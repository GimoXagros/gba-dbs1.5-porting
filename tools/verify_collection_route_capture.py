"""Bind the ordinary stage 11 clear, saved unlock and observed Collection route."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def verify(directory):
    launch = json.loads((directory / "launch.json").read_bytes())
    for field in ("completed", "loaded_rom_exact", "scripts_unchanged", "checkpoint_copies_unchanged"):
        assert launch[field], field
    assert not launch["visible"] and not launch["supplied_save_used"]
    assert launch["outcome"] == "collection-shoot-returned"
    assert sha(directory / "loaded-rom.bin") == launch["rom_sha256"] == "9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5"
    for name, digest in launch["files"].items():
        assert sha(directory / name) == digest, name
    trace = (directory / "collection-trace.txt").read_text().splitlines()
    milestones = ["eligible-clear-writer mode=8", "mode=3", "mode=4", "mode=23",
                  "scene-create mode=23", "scene-playing mode=23", "failure-exit mode=23",
                  "mode=20", "mode=3"]
    events = [line.split(" ", 1) for line in trace if "callbacks=" not in line]
    assert [event for frame, event in events] == milestones
    assert [int(frame) for frame, event in events] == sorted(int(frame) for frame, event in events)
    writes = (directory / "wholeplay-stage11-writes.txt").read_text().splitlines()
    assert len(writes) == 1 and "address=0201188C bytes=2 before=37 requested=1" in writes[0]
    tail = (directory / "wholeplay-trace.txt").read_text()
    assert re.search(r"event=hit-post core=89483", tail) and "event=title-ready" in tail
    def read(prefix, domain):
        return (directory / f"{prefix}-{domain}.bin").read_bytes()
    def word(data, offset):
        return struct.unpack_from("<H", data, offset)[0]
    def longword(data, offset):
        return struct.unpack_from("<I", data, offset)[0]
    def tasks(ewram):
        return [h for h in range(0x10000, 0x10000 + 52 * 0x118, 0x118) if word(ewram, h+16) & 2]
    menu = read("collection-eligible", "IWRAM")
    e = read("collection-eligible", "EWRAM")
    owner, = [h for h in tasks(e) if longword(e, h) == 0x08DFE048]
    assert word(menu, 0x2310) == 3 and e[owner+28] == 2 and longword(e, owner+52) == 1
    assert word(menu, 0x2A78+14) == 10 and word(menu, 0x2AC8+14) == 9
    e = read("shoot-playing", "EWRAM")
    assert word(read("shoot-playing", "IWRAM"), 0x2310) == 23
    h, = [at for at in tasks(e) if longword(e, at) == 0x08DB2994]
    assert longword(e,h+24+0xFC) == 0x02000000+h+24 and e[h+24+43] == 3
    assert word(read("shoot-exit","IWRAM"),0x2310) == 20
    e = read("collection-return","EWRAM")
    assert word(read("collection-return","IWRAM"),0x2310) == 3
    assert any(longword(e, h) == 0x08090C7C for h in tasks(e))
    assert all(not 0x08DB0404 <= longword(e, h) < 0x08DB5C04 for h in tasks(e))
    return dict(status="PASS", launch_sha256=sha(directory/"launch.json"), capture_files=len(launch["files"]),
                events=events, sole_stage11_hp1_write=True, observed_playing_participants=3,
                earned_saved_unlock=True, defeat_exit=True, no_scene_tasks_at_title=True,
                scope="One private run from the genuine stage 11 checkpoint through ordinary Shoot defeat and title return.")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    report=verify(args.capture)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(report["status"],sha(args.output))
