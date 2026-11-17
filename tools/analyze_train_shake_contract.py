"""Read-only, bounded source contract for the previously named Train hazard.

Does not establish dynamic reachability, reserve RAM, build a ROM, or launch a core.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    data = args.source.read_bytes()
    sha = hashlib.sha256(data).hexdigest().upper()
    assert sha == "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
    base, entry, end = 0x768F70, 0x76B3D2, 0x76B477
    # Far initializer is called by the actual stage-8 initializer.
    assert data[0x77DAA0:0x77DAA5] == bytes.fromhex("9a0725f768")
    assert data[end:0x76B49B] == bytes.fromhex(
        "501eb800108ed833c0a37603a37803a16000251f00a37a03"
        "a16200252f00a37c031f58cb")
    assert data[entry:end] == bytes.fromhex(
        "535606f70676030100752fff0e78037803e98d00810e7603010033c0a37803"
        "bea22303367a0303367a03ff067a0381267a031f002e8b04a37e03bece01"
        "a17e03bb0400f706780302007403bb0100c7441c000089441e531e569a6733ff4f"
        "83c406b800038ec0bb3c008a441a2688078a441b26884701ff067803833e780304"
        "7220bee223a17c0303f003f02e8b04a37803ff067c0381267c032f0081267603"
        "feff075e5bc3")
    dispatch = [base + struct.unpack_from("<H", data, 0x7693AC + i * 2)[0]
                for i in range(12)]
    assert dispatch[8] == 0x76A8CC and entry not in dispatch
    assert data[0x7693FD:0x769402] == bytes.fromhex("2eff973c04")
    # Train's complete epilogue: scroll and palette, then return.
    assert data[0x76A918:0x76A922] == bytes.fromhex("e8a100e834008be55dc3")
    # No direct call/jump to this entry, including alternative 16-bit CS aliases.
    near = []
    for at in range(entry - 0x10000, entry + 0x10000):
        if data[at] in (0xE8, 0xE9):
            target = at + 3 + struct.unpack_from("<h", data, at + 1)[0]
            if (target - entry) & 0xFFFF == 0:
                near.append(at)
    far = []
    for at in range(0x700000, len(data) - 5):
        if data[at] in (0x9A, 0xEA):
            offset, segment = struct.unpack_from("<HH", data, at + 1)
            if ((segment * 16 + offset) & 0xFFFFF) == (entry & 0xFFFFF):
                far.append(at)
    pointer = struct.pack("<H", entry - base)
    pointer_locations = [at for at in range(base, base + 0x10000 - 1)
                         if data[at:at + 2] == pointer]
    assert near == far == pointer_locations == []
    amplitude = list(struct.unpack_from("<32H", data, 0x76B312))
    delay = list(struct.unpack_from("<64H", data, 0x76B352))
    assert set(amplitude) == {0x100, 0x200, 0x300}
    assert set(delay) == {10, 15, 20, 30}
    assert len(data[0x76B312:entry]) == 192  # 32 amplitude + 64 delay words
    assert data[0x76B311] == 0xC3  # preceding routine returns before table data
    report = {
        "status": "source-contract-proved; update-reachability-unproved",
        "source_sha256": sha,
        "initializer": "77DAA0 -> 68F7:2507 / raw76B477",
        "stage8_update": "7693FD -> table7693BC -> 76A8CC -> 76A9BC,76A952",
        "consumer_entry": "68F7:2462 / raw76B3D2",
        "direct_near_entry_candidates": near,
        "direct_far_entry_candidates": far,
        "entry_word_candidates_in_CS_window": pointer_locations,
        "source_state": {
            "1000:0376": "bit0 active shake; initializer clears whole word",
            "1000:0378": "inactive countdown / active phase0..3; initializer zero",
            "1000:037A": "amplitude index: config0060 & 001F; increment &001F",
            "1000:037C": "delay index: config0062 & 002F; increment &002F (not modulo48)",
            "1000:037E": "selected amplitude; written before first active read",
        },
        "amplitude_words": amplitude,
        "delay_words": delay,
        "reachable_delay_indices": [i for i in range(64) if i & 0x2F == i],
        "effect": "BG0 owner01CE: Xdelta0,Ydelta amplitude; movement modes4,4,1,1; copy scroll bytes to0300:003C/003D",
        "missing_witness": "An actual source execution entering 68F7:2462, with predecessor/call site, CS/DS, stage, and five fields; do not manufacture a callback edge.",
        "limitations": "No exhaustive computed-control-flow proof, native private-state owner, runtime observation, damage effect, or port correctness claim.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.output)}))


if __name__ == "__main__":
    main()
