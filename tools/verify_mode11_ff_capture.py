"""Verify the live source-FF mode 11 exit on the exact isolated candidate."""
import argparse
import json
import re
import struct
from pathlib import Path

from verify_collection_route_capture import sha


def verify(capture):
    launch = json.loads((capture / "launch.json").read_bytes())
    assert launch["outcome"] == "shoot-checkpoint-aim-terminal-results-title"
    assert all(launch[key] for key in ("completed", "loaded_rom_exact", "scripts_unchanged",
                                       "checkpoint_copies_unchanged", "CPU_bank_equal",
                                       "native_extensions_equal", "managed_suffix_equal"))
    assert not any(launch[key] for key in ("visible", "physical_background_input", "supplied_save_used"))
    rom = capture / "loaded-rom.bin"
    assert sha(rom) == launch["rom_sha256"] == "2A7E8296DDD1DB3898CF3484E5849E623066A6249D3F70B090374956213CD083"
    assert struct.unpack_from("<I", rom.read_bytes(), 0xC0D28)[0] == 0xE3A000FF
    for name, expected in launch["files"].items():
        assert sha(capture / name) == expected, name
    trace = (capture / "wholeplay-trace.txt").read_text().splitlines()
    events = {}
    for line in trace:
        match = re.match(r"event=([\w-]+) core=(\d+).+? pc=([0-9A-F]+)", line)
        if match:
            events[match[1]] = (int(match[2]), match[3], line)
    path = [
        ("ending-entry", "080BF1D4"), ("ending-ready", "080C0054"),
        ("ending-selector-entry", "080C0D2C"), ("ending-source-bypass", "080C0E08"),
        ("ending-source-request", "080C0E20"), ("mode20-entry", "0804044C"),
        ("mode20-art", "08040720"), ("mode20-return-request", "0804060C"),
        ("title-ready", "08090C80")
    ]
    assert all(events[name][1] == pc for name, pc in path)
    frames = [events[name][0] for name, _ in path]
    assert frames == sorted(frames)
    assert frames[0] < frames[1] < frames[2] == frames[3] == frames[4] < frames[5] < frames[-1]
    assert "R0=FF ordinary path" in events["ending-source-bypass"][2]
    assert "request=1,0,0" in events["ending-source-request"][2]
    assert not any("forbidden-card-init" in line or "violation=" in line for line in trace)
    writes = (capture / "wholeplay-stage11-writes.txt").read_text().splitlines()
    assert len(writes) == 1 and "address=0201188C bytes=2 before=37 requested=1" in writes[0]
    snapshots = (("18-wholeplay-ending-source-request", 11), ("19-wholeplay-mode20-entry", 20),
                 ("22-wholeplay-title-ready", 3))
    for prefix, mode in snapshots:
        iw = (capture / (prefix + "-iwram.bin")).read_bytes()
        assert struct.unpack_from("<H", iw, 0x2310)[0] == mode
    return dict(status="PASS", rom=sha(rom), capture=sha(capture / "launch.json"),
                frames={name: events[name][0] for name, _ in path},
                all_indexed_files=len(launch["files"]), optional_card_initialized=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = verify(args.capture)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS", sha(args.report))
