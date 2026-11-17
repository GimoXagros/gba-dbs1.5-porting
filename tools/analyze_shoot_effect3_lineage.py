"""Bound source 86BF:0000 effect3 to the retained native visual child service."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from build_shoot_initializer import parse_p1
from build_full_asset_poc import convert_tile, parse_wsc_far_descriptor
from convert_wsc_palette_block import convert_block

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

def analyze(source, old, gba, current):
    pins = (
        (source, "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"),
        (old, "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"),
        (gba, "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"),
        (current, "574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"),
    )
    assert all(sha(b) == pin for b, pin in pins)
    assert source[0x786BF0:0x786BFD] == old[0x3C6970:0x3C697D]
    assert source[0x786C0B:0x786C19] == old[0x3C698B:0x3C6999]
    assert struct.unpack_from("<4I", gba, 0x3598D0) == (0x083598FC, 0x080D1C88, 0x080D20D8, 0x080D2ED0)
    assert current[0x35972C:0x3597D0] == gba[0x35972C:0x3597D0]
    assert current[0x3597D4:0x359BC8] == gba[0x3597D4:0x359BC8]
    # ABI witnesses: eventID at originalSP+0, Y+4, X+8, target+16; R5
    # supplies the initial parent coordinates even though target is also saved.
    anchors = {0x35972C: 0xE92D403B, 0x3597B0: 0xE59D0018,
               0x359838: 0xE59D0020, 0x359850: 0xE59D001C,
               0x35988C: 0xE1D503F4, 0x3598A4: 0xE1D503F6,
               0x3598BC: 0xE59D0028, 0x3598C4: 0xE7840008,
               0x359974: 0xE3580003, 0x359B5C: 0xE3500003,
               0x359B88: 0xE3180B02}
    for p, word in anchors.items():
        assert struct.unpack_from("<I", current, p)[0] == word, hex(p)
    parsed = parse_p1(source, 0x3C8CF0, 0x318)
    assert parsed["data"] == old[0x2AC750:0x2AC750 + len(parsed["data"])]
    n, p, a, b = struct.unpack_from("<4I", current, 0xD1C88 + 8 + 3 * 16)
    assert n == 4 and b == 0
    payload = bytearray()
    for row in parsed["payloads"][3]:
        words = list(row)
        assert words[0] == 0xFF04 and words[5] == 0
        words[0] = 0xFF03
        payload.extend(struct.pack("<6HI", *words, 0))
    assert bytes(payload) == current[p - 0x08000000:p - 0x08000000 + 64]
    ar = parsed["commands"][3][2]
    assert parsed["data"][ar:ar + 8] == current[a - 0x08000000:a - 0x08000000 + 8]
    table, descriptors, c0, c1 = struct.unpack_from("<4I", current, 0xD20D8)
    assert (c0, c1) == struct.unpack_from("<2I", source, 0x3BDCC8)
    layouts = (struct.unpack_from("<H", source, 0x3BDCD2)[0] - 16) // 4
    total = 0
    for i in range(layouts):
        n, rel = struct.unpack_from("<2H", source, 0x3BDCD0 + i * 4)
        nn, ptr = struct.unpack_from("<2I", current, table - 0x08000000 + i * 8)
        assert n == nn
        assert source[0x3BDCC0 + rel:0x3BDCC0 + rel + n * 4] == current[ptr - 0x08000000:ptr - 0x08000000 + n * 4]
        total += n * 4
    length, physical = parse_wsc_far_descriptor(source, 0x3D8E00)
    n, ptr = struct.unpack_from("<2I", current, descriptors - 0x08000000)
    pixels = b"".join(convert_tile(source[x:x + 32]) for x in range(physical, physical + length, 32))
    assert length == n == 2016 and pixels == current[ptr - 0x08000000:ptr - 0x08000000 + n]
    assert convert_block(source[0x3D7D60:0x3D7D86]) == current[0xD2ED0:0xD2EF8]
    return {"status": "PASS", "source_constructor": "786BF0", "old_constructor": "3C6970",
            "native_constructor": "0835972C", "native_child": "083598FC",
            "stack_at_entry": ["effect=3", "y=0", "x=0", "ignored=0", "parent payload"],
            "additional_required_registers": {"R5": "parent payload", "R11": 0},
            "caller_preserves": "R4..R12 and LR", "allocation_priority": 4096,
            "native_resources": ["080D1C88", "080D20D8", "080D2ED0"],
            "event_items": 4, "layouts": layouts, "layout_bytes": total,
            "tile_bytes": n, "palette_bytes": 40,
            "event3_parent_retirement_mask": "0800", "event_done_mask": "2000",
            "existing_constructor_priority_hook": "083597D0",
            "native_constructor_sha256": sha(current[0x35972C:0x3598FC]),
            "native_child_sha256": sha(current[0x3598FC:0x359BC8]),
            "runtime_claim": False, "ROM_modified": False}

def main():
    p = argparse.ArgumentParser()
    for name in ("source", "old", "gba", "current", "report"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.source.read_bytes(), a.old.read_bytes(), a.gba.read_bytes(), a.current.read_bytes())
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
