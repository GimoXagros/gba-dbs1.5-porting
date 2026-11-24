"""Exercise the executed ARM display guard for hidden and visible auxiliary actors."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_shoot_guarded_transition_irq import Machine


START = 0x086FFBE4
ACCEPT = 0x086FFBF4
REJECT = 0x086FFD3C
AUX = 0x02011940


def verify(before, after, source):
    sha = lambda data: hashlib.sha256(data).hexdigest().upper()
    old, new, wsc = before.read_bytes(), after.read_bytes(), source.read_bytes()
    assert sha(wsc) == "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
    assert wsc[0x7486AF:0x7486BE] == bytes.fromhex("814C042000C704D87DC744029040CB") and wsc[0x7486D8] == 0xCB
    assert struct.unpack_from("<6I", old, 0x5BF414) == (0xE1D480B4, 0xE3888020, 0xE1C480B4, 0xE59F8004, 0xE5848000, 0xE12FFF1E)
    assert struct.unpack_from("<I", old, 0x5BF42C)[0] == 0x085BF600
    assert struct.unpack_from("<I", old, 0x5BF600)[0] == 0xE12FFF1E
    assert len(old) == len(new) and old[:0x6FFBE4] == new[:0x6FFBE4] and old[0x6FFBF0:] == new[0x6FFBF0:]
    assert struct.unpack_from("<4I", old, 0x6FFBE4) == (0xE1D60BBA, 0xE59F11D4, 0xE1500001, 0x1A000051)
    assert struct.unpack_from("<4I", new, 0x6FFBE4) == (0xE1D600B4, 0xE2000020, 0xE3500020, 0x1A000051)
    cases = 0
    for flags in range(16):
        prior = Machine(old, seed=flags, flags=0x10 | flags << 28)
        fixed = Machine(new, seed=flags, flags=0x10 | flags << 28)
        for event in (*range(256), 0x8000, 0xFFFF):
            for kind in (0x306, 0x326):
                for m, allow in ((prior, event == 0), (fixed, bool(kind & 0x20))):
                    m.r[6] = AUX
                    m.put(AUX + 4, kind, 2)
                    m.put(AUX + 0xBA, event, 2)
                    snapshot = m.r[2:15]
                    writes = len(m.writes)
                    m.cpsr = 0x10 | flags << 28
                    assert m.run(START, {ACCEPT, REJECT}) == (ACCEPT if allow else REJECT)
                    assert m.r[2:15] == snapshot and len(m.writes) == writes
                    cases += 1
    return dict(status="PASS", input=sha(old), output=sha(new), source=sha(wsc), executed_predicate_cases=cases,
                in_place_bytes=12, effective_byte_changes=sum(a != b for a, b in zip(old, new)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "source", "report"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = verify(args.before, args.after, args.source)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(report["executed_predicate_cases"], hashlib.sha256(args.report.read_bytes()).hexdigest().upper())
