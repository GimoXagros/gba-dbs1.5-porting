"""Bind capture evidence to the launched Windows process and sampled ROM bytes.

This module never starts an emulator or changes guest memory.  TCP ownership is
checked through the Windows IP Helper API, rather than inferred from a listening
port or from the private desktop used by the frontend.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import hashlib
from pathlib import Path
import socket
import struct
import sys
import time


def tcp_owner_rows() -> list[dict[str, object]]:
    if sys.platform != "win32":
        raise RuntimeError("TCP process ownership verification is Windows-only")
    get_table = ctypes.WinDLL("iphlpapi", use_last_error=True).GetExtendedTcpTable
    get_table.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.ULONG),
                         wintypes.BOOL, wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
    get_table.restype = wintypes.DWORD
    rows: list[dict[str, object]] = []
    for family, row_format in ((2, "<6I"), (23, "<16sII16sIIII")):
        size = wintypes.ULONG()
        result = get_table(None, ctypes.byref(size), False, family, 5, 0)
        if result not in (0, 122):
            raise ctypes.WinError(result)
        for _ in range(4):
            buffer = ctypes.create_string_buffer(size.value)
            result = get_table(buffer, ctypes.byref(size), False, family, 5, 0)
            if result != 122:
                break
        if result:
            raise ctypes.WinError(result)
        data = buffer.raw[:size.value]
        count = struct.unpack_from("<I", data)[0]
        row_size = struct.calcsize(row_format)
        if 4 + count * row_size > len(data):
            raise RuntimeError("truncated Windows TCP owner table")
        for index in range(count):
            values = struct.unpack_from(row_format, data, 4 + index * row_size)
            if family == 2:
                state, local, local_port, peer, peer_port, pid = values
                local_address = socket.inet_ntoa(struct.pack("<I", local))
                peer_address = socket.inet_ntoa(struct.pack("<I", peer))
            else:
                local, local_scope, local_port, peer, peer_scope, peer_port, state, pid = values
                local_address = socket.inet_ntop(socket.AF_INET6, local)
                peer_address = socket.inet_ntop(socket.AF_INET6, peer)
                if local_scope:
                    local_address += f"%{local_scope}"
                if peer_scope:
                    peer_address += f"%{peer_scope}"
            rows.append({"family": family, "state": state, "pid": pid,
                         "local_address": local_address,
                         "local_port": socket.ntohs(local_port & 0xFFFF),
                         "peer_address": peer_address,
                         "peer_port": socket.ntohs(peer_port & 0xFFFF)})
    return rows


def assert_gdb_port_free(port: int) -> None:
    occupied = [row for row in tcp_owner_rows()
                if row["local_port"] == port and row["state"] in (2, 5)]
    if occupied:
        raise RuntimeError(f"GDB port {port} already belongs to a listener/connection: {occupied}")


def verify_gdb_owner(connection: socket.socket, expected_pid: int) -> dict[str, object]:
    client_address, client_port = connection.getsockname()
    server_address, server_port = connection.getpeername()
    deadline = time.monotonic() + 1.0
    while True:
        matches = [row for row in tcp_owner_rows()
                   if row["family"] == 2 and row["state"] == 5
                   and row["local_address"] == server_address
                   and row["local_port"] == server_port
                   and row["peer_address"] == client_address
                   and row["peer_port"] == client_port]
        if matches:
            if len(matches) != 1 or matches[0]["pid"] != expected_pid:
                raise RuntimeError(f"GDB endpoint is not owned by launched PID {expected_pid}: {matches}")
            return {"expected_pid": expected_pid, "verified": True, **matches[0]}
        if time.monotonic() >= deadline:
            raise RuntimeError("connected GDB endpoint has no verifiable Windows TCP owner")
        time.sleep(0.01)


def verify_loaded_rom_samples(remote, rom: Path) -> dict[str, object]:
    """Read-only identity samples, explicitly not a full loaded-ROM hash.

    Include the complete expanded physics blob and adjacent presentation tables
    in addition to a header and evenly spaced blocks.  All expected bytes come
    directly from the already hash-guarded requested ROM.
    """
    data = rom.read_bytes()
    if not 0 < len(data) <= 0x2000000:
        raise ValueError("GBA ROM identity samples require a file of 1..32 MiB")
    block_size = min(0x100, len(data))
    windows = {(index * (len(data) - block_size) // 15, block_size)
               for index in range(16)}
    for offset, size in ((0x0D3FB8, 0x400), (0x3530BC, 0x248),
                         (0x485000, 0x21C), (0x5C1500, 0x114)):
        if offset + size <= len(data):
            windows.add((offset, size))
    verified = []
    for offset, size in sorted(windows):
        expected = data[offset:offset + size]
        actual = remote.read_memory(0x08000000 + offset, size)
        if actual != expected:
            raise RuntimeError(f"loaded ROM differs from requested file at sample raw 0x{offset:X} size 0x{size:X}")
        verified.append({"offset": f"0x{offset:06X}", "size": size,
                         "sha256": hashlib.sha256(actual).hexdigest().upper()})
    return {"method": "read-only ROM samples; not a full loaded-ROM hash",
            "verified": True, "samples": verified}
