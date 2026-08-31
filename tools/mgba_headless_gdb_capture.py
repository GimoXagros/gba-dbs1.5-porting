#!/usr/bin/env python3
"""Capture an mGBA runtime state without showing a window on the user desktop.

The Windows Qt frontend is launched on a private desktop, then observed through
its GDB remote stub. Runtime dumps are evidence artifacts and must stay under
an ignored output directory.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid


DESKTOP_ALL_ACCESS = 0x01FF
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_F12 = 0x7B
VK_RETURN = 0x0D
VK_X = 0x58
MGBA_GDB_PORT = 2345


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


class PrivateDesktopProcess:
    def __init__(self, executable: Path, arguments: list[str], cwd: Path) -> None:
        if sys.platform != "win32":
            raise RuntimeError("private-desktop capture is Windows-only")

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self._close_desktop = user32.CloseDesktop
        self._close_desktop.argtypes = [wintypes.HANDLE]
        self._close_desktop.restype = wintypes.BOOL
        self._close_handle = kernel32.CloseHandle
        self._close_handle.argtypes = [wintypes.HANDLE]
        self._close_handle.restype = wintypes.BOOL
        self._terminate_process = kernel32.TerminateProcess
        self._terminate_process.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._terminate_process.restype = wintypes.BOOL
        self._post_message = user32.PostMessageW
        self._post_message.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._post_message.restype = wintypes.BOOL
        self._get_window_pid = user32.GetWindowThreadProcessId
        self._get_window_pid.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self._get_window_pid.restype = wintypes.DWORD
        self._enum_desktop_windows = user32.EnumDesktopWindows
        self._enum_desktop_windows.restype = wintypes.BOOL

        create_desktop = user32.CreateDesktopW
        create_desktop.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            ctypes.c_void_p,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        create_desktop.restype = wintypes.HANDLE

        create_process = kernel32.CreateProcessW
        create_process.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.BOOL,
            wintypes.DWORD,
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.POINTER(STARTUPINFOW),
            ctypes.POINTER(PROCESS_INFORMATION),
        ]
        create_process.restype = wintypes.BOOL

        self.desktop_name = f"CodexMGBACapture_{uuid.uuid4().hex}"
        self.desktop = create_desktop(
            self.desktop_name, None, None, 0, DESKTOP_ALL_ACCESS, None
        )
        if not self.desktop:
            raise ctypes.WinError(ctypes.get_last_error())

        command_line = subprocess.list2cmdline([str(executable), *arguments])
        command_buffer = ctypes.create_unicode_buffer(command_line)
        startup = STARTUPINFOW()
        startup.cb = ctypes.sizeof(startup)
        startup.lpDesktop = self.desktop_name
        self.process = PROCESS_INFORMATION()
        if not create_process(
            str(executable),
            command_buffer,
            None,
            None,
            False,
            0,
            None,
            str(cwd),
            ctypes.byref(startup),
            ctypes.byref(self.process),
        ):
            error = ctypes.get_last_error()
            self._close_desktop(self.desktop)
            self.desktop = None
            raise ctypes.WinError(error)

    @property
    def pid(self) -> int:
        return int(self.process.dwProcessId)

    def post_key_state(self, virtual_key: int, pressed: bool) -> int:
        windows: list[int] = []
        callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self._enum_desktop_windows.argtypes = [
            wintypes.HANDLE,
            callback_type,
            wintypes.LPARAM,
        ]

        @callback_type
        def collect(window: int, _parameter: int) -> bool:
            owner = wintypes.DWORD()
            self._get_window_pid(window, ctypes.byref(owner))
            if owner.value == self.pid:
                windows.append(window)
            return True

        if not self._enum_desktop_windows(self.desktop, collect, 0):
            raise ctypes.WinError(ctypes.get_last_error())
        message = WM_KEYDOWN if pressed else WM_KEYUP
        parameter = 1 if pressed else 0xC0000001
        for window in windows:
            self._post_message(window, message, virtual_key, parameter)
        return len(windows)

    def post_key(self, virtual_key: int) -> int:
        windows = self.post_key_state(virtual_key, True)
        self.post_key_state(virtual_key, False)
        return windows

    def close(self) -> None:
        if getattr(self, "process", None):
            if self.process.hProcess:
                self._terminate_process(self.process.hProcess, 0)
            if self.process.hThread:
                self._close_handle(self.process.hThread)
            if self.process.hProcess:
                self._close_handle(self.process.hProcess)
            self.process = None
        if getattr(self, "desktop", None):
            self._close_desktop(self.desktop)
            self.desktop = None

    def __enter__(self) -> "PrivateDesktopProcess":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class GdbRemote:
    def __init__(self, connection: socket.socket) -> None:
        self.connection = connection
        self.connection.settimeout(10.0)

    @staticmethod
    def _packet(payload: bytes) -> bytes:
        checksum = sum(payload) & 0xFF
        return b"$" + payload + b"#" + f"{checksum:02x}".encode("ascii")

    def _read_byte(self) -> bytes:
        value = self.connection.recv(1)
        if not value:
            raise ConnectionError("mGBA GDB connection closed")
        return value

    def receive_packet(self) -> bytes:
        while True:
            value = self._read_byte()
            if value == b"$":
                break
        payload = bytearray()
        while True:
            value = self._read_byte()
            if value == b"#":
                break
            payload.extend(value)
        received_checksum = int(self.connection.recv(2), 16)
        if (sum(payload) & 0xFF) != received_checksum:
            self.connection.sendall(b"-")
            raise RuntimeError("bad checksum in GDB response")
        self.connection.sendall(b"+")
        return bytes(payload)

    def command(self, payload: str) -> bytes:
        self.connection.sendall(self._packet(payload.encode("ascii")))
        acknowledgement = self._read_byte()
        if acknowledgement != b"+":
            raise RuntimeError(f"GDB command was not acknowledged: {acknowledgement!r}")
        response = self.receive_packet()
        if response.startswith(b"E"):
            raise RuntimeError(f"GDB command {payload!r} failed: {response!r}")
        return response

    def continue_for(self, seconds: float) -> bytes:
        self.start_continue()
        time.sleep(seconds)
        return self.interrupt()

    def start_continue(self) -> None:
        self.connection.sendall(self._packet(b"c"))
        acknowledgement = self._read_byte()
        if acknowledgement != b"+":
            raise RuntimeError(f"GDB continue was not acknowledged: {acknowledgement!r}")

    def interrupt(self) -> bytes:
        self.connection.sendall(b"\x03")
        return self.receive_packet()

    def read_memory(self, address: int, size: int) -> bytes:
        output = bytearray()
        for offset in range(0, size, 0x100):
            chunk_size = min(0x100, size - offset)
            encoded = self.command(f"m{address + offset:x},{chunk_size:x}")
            chunk = bytes.fromhex(encoded.decode("ascii"))
            if len(chunk) != chunk_size:
                raise RuntimeError(
                    f"short GDB read at 0x{address + offset:08X}: "
                    f"expected {chunk_size}, got {len(chunk)}"
                )
            output.extend(chunk)
        return bytes(output)


def connect_gdb(port: int, timeout: float) -> socket.socket:
    deadline = time.monotonic() + timeout
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connection.connect(("127.0.0.1", port))
            return connection
        except OSError as error:
            last_error = error
            connection.close()
            time.sleep(0.1)
    raise TimeoutError(f"mGBA GDB port {port} did not open: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mgba", required=True, type=Path)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seconds", type=float, default=45.0)
    parser.add_argument(
        "--press-start-at",
        type=float,
        help="press the default mGBA Start key (Enter) at this runtime second",
    )
    parser.add_argument(
        "--press-a-at",
        type=float,
        action="append",
        help="press the default mGBA A key (X) at this runtime second",
    )
    parser.add_argument("--key-hold-seconds", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mgba = args.mgba.resolve(strict=True)
    rom = args.rom.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise RuntimeError(f"refusing to replace evidence directory: {output_dir}")

    rom_hash = sha256(rom)
    expected_hash = args.expected_sha256.upper()
    if rom_hash != expected_hash:
        raise RuntimeError(
            f"unexpected ROM SHA-256: expected {expected_hash}, got {rom_hash}"
        )
    if args.seconds <= 0:
        raise ValueError("--seconds must be positive")
    scheduled_inputs = []
    if args.press_start_at is not None:
        scheduled_inputs.append((args.press_start_at, "Start", VK_RETURN))
    scheduled_inputs.extend(
        (at_seconds, "A", VK_X) for at_seconds in (args.press_a_at or [])
    )
    scheduled_inputs.sort()
    if scheduled_inputs:
        if scheduled_inputs[0][0] < 0 or args.key_hold_seconds <= 0:
            raise ValueError("input timing must be positive")
        for (first_at, _, _), (second_at, _, _) in zip(
            scheduled_inputs, scheduled_inputs[1:]
        ):
            if first_at + args.key_hold_seconds > second_at:
                raise ValueError("scheduled key presses must not overlap")
        if scheduled_inputs[-1][0] + args.key_hold_seconds >= args.seconds:
            raise ValueError("all key presses must end before capture")
    output_dir.mkdir(parents=True)

    arguments = [
        "-g",
        "-C",
        "pauseOnMinimize=0",
        "-C",
        "pauseOnFocusLost=0",
        "-C",
        f"screenshotPath={output_dir}",
        str(rom),
    ]
    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with PrivateDesktopProcess(mgba, arguments, Path.cwd()) as process:
        with connect_gdb(MGBA_GDB_PORT, 10.0) as connection:
            remote = GdbRemote(connection)
            supported = remote.command("qSupported").decode("ascii", errors="replace")
            initial_stop = remote.command("?").decode("ascii", errors="replace")
            input_events = []
            if not scheduled_inputs:
                final_stop_bytes = remote.continue_for(args.seconds)
            else:
                remote.start_continue()
                elapsed = 0.0
                for at_seconds, key, virtual_key in scheduled_inputs:
                    time.sleep(at_seconds - elapsed)
                    key_down_windows = process.post_key_state(virtual_key, True)
                    time.sleep(args.key_hold_seconds)
                    key_up_windows = process.post_key_state(virtual_key, False)
                    elapsed = at_seconds + args.key_hold_seconds
                    input_events.append(
                        {
                            "key": key,
                            "host_virtual_key": (
                                "VK_RETURN" if virtual_key == VK_RETURN else "VK_X"
                            ),
                            "at_seconds": at_seconds,
                            "hold_seconds": args.key_hold_seconds,
                            "key_down_windows": key_down_windows,
                            "key_up_windows": key_up_windows,
                        }
                    )
                time.sleep(args.seconds - elapsed)
                final_stop_bytes = remote.interrupt()
            final_stop = final_stop_bytes.decode("ascii", errors="replace")
            screenshot_windows = process.post_key(VK_F12)
            time.sleep(2.0)
            screenshots = sorted(output_dir.glob("*.png"))
            registers = remote.command("g").decode("ascii")
            regions = {
                "io.bin": remote.read_memory(0x04000000, 0x400),
                "palette.bin": remote.read_memory(0x05000000, 0x400),
                "vram.bin": remote.read_memory(0x06000000, 0x18000),
                "oam.bin": remote.read_memory(0x07000000, 0x400),
                "ewram.bin": remote.read_memory(0x02000000, 0x40000),
                "iwram.bin": remote.read_memory(0x03000000, 0x8000),
            }
            for filename, data in regions.items():
                (output_dir / filename).write_bytes(data)

            display_control = int.from_bytes(regions["io.bin"][0:2], "little")
            manifest = {
                "schema": "mgba-headless-gdb-capture-v1",
                "started_utc": started_utc,
                "capture_seconds": args.seconds,
                "rom": {
                    "filename": rom.name,
                    "size": rom.stat().st_size,
                    "sha256": rom_hash,
                },
                "emulator": {
                    "filename": mgba.name,
                    "sha256": sha256(mgba),
                    "gdb_supported": supported,
                },
                "process": {
                    "pid": process.pid,
                    "private_desktop": True,
                    "monitor_visible": False,
                    "screenshot_windows": screenshot_windows,
                },
                "input_events": input_events,
                "gdb": {
                    "initial_stop": initial_stop,
                    "final_stop": final_stop,
                    "registers_hex": registers,
                },
                "display": {
                    "dispcnt": f"0x{display_control:04X}",
                    "mode": display_control & 0x7,
                    "screenshots": [
                        {
                            "filename": screenshot.name,
                            "size": screenshot.stat().st_size,
                            "sha256": sha256(screenshot),
                        }
                        for screenshot in screenshots
                    ],
                },
                "regions": {
                    filename: {
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest().upper(),
                    }
                    for filename, data in regions.items()
                },
            }
            (output_dir / "capture.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
