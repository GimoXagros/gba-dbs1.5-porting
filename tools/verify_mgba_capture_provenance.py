"""Exercise capture identity failures without starting an emulator."""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import tempfile

from mgba_capture_provenance import (
    assert_gdb_port_free, verify_gdb_owner, verify_loaded_rom_samples,
)


def rejects(call, fragment: str) -> None:
    try:
        call()
    except RuntimeError as error:
        if fragment not in str(error):
            raise
    else:
        raise AssertionError(f"expected rejection containing {fragment!r}")


def main() -> None:
    checks = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
        listener.listen(1)
        rejects(lambda: assert_gdb_port_free(port), "already belongs")
        checks.append("pre-existing listener rejected")
        with socket.create_connection(("127.0.0.1", port)) as client:
            server, _ = listener.accept()
            with server:
                identity = verify_gdb_owner(client, os.getpid())
                assert identity["pid"] == os.getpid()
                checks.append("connected server endpoint belongs to exact expected PID")
                rejects(lambda: verify_gdb_owner(client, os.getpid() + 0x100000),
                        "not owned by launched PID")
                checks.append("different process rejected")
    assert_gdb_port_free(port)
    checks.append("closed listener no longer occupies port")

    # Deterministic synthetic bytes: no source ROM or save file is read here.
    payload = bytes(range(256)) * 0x8000
    class ReadOnlyRemote:
        def __init__(self, mutation=None):
            self.mutation = mutation
        def read_memory(self, address, size):
            offset = address - 0x08000000
            result = bytearray(payload[offset:offset + size])
            if self.mutation is not None and offset <= self.mutation < offset + size:
                result[self.mutation - offset] ^= 1
            return bytes(result)

    with tempfile.TemporaryDirectory(prefix="mgba-provenance-") as directory:
        rom = Path(directory) / "synthetic.gba"
        rom.write_bytes(payload)
        report = verify_loaded_rom_samples(ReadOnlyRemote(), rom)
        assert report["verified"]
        checks.append("loaded ROM samples match expected requested bytes")
        for offset in (0, 0x485030, 0x485034, 0x485038, 0x4851A4, 0x5C1500):
            rejects(lambda: verify_loaded_rom_samples(ReadOnlyRemote(offset), rom),
                    "loaded ROM differs")
        checks.append("header, three physics pointers, physics record, resident code mismatches rejected")
    print(json.dumps({"status": "PASS", "emulator_started": False,
                      "guest_writes": [], "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
