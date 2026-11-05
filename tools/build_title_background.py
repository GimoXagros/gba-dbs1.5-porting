"""Isolated WSC1.5 Japanese title BG layer; retain shared native artwork owners."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from analyze_waterfall_third_pattern import no_inbound
from build_poc import convert_planar_tile
from build_stage_assets import convert_map
from convert_wsc_palette_block import convert_color

BASE = 0x08000000
INPUT = "428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
TILES1, TILES2, MAP, PALETTE, CODE = 0x712680, 0x717F40, 0x6FBDA8, 0x6FC198, 0x6FC298
RESERVATIONS = ((TILES1, TILES1 + 0x2000), (TILES2, TILES2 + 0x1300), (MAP, CODE + 48))


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, address):
    return struct.unpack_from("<I", data, address)[0]


def branch(address, target):
    delta = target - (BASE + address + 8)
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), "ARM B range")
    return struct.pack("<I", 0xEA000000 | (delta // 4 & 0xFFFFFF))


def helper():
    text = f"""
        ldr r5, destination
        ldr r4, first
        mov r2, #0x800
        bl 0x08000B84
        ldr r4, second
        mov r2, #0x4C0
        ldr lr, continuation
        b 0x08000B84
    destination: .word 0x06003200
    first: .word 0x{BASE + TILES1:08X}
    second: .word 0x{BASE + TILES2:08X}
    continuation: .word 0x08090938
    """
    result = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(text, BASE + CODE)[0])
    need(len(result) == 48, "exact eight instructions/four literals")
    instructions = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(result[:32], BASE + CODE))
    need(len(instructions) == 8 and all(not i.update_flags for i in detail_instructions(result[:32])), "helper preserves flags")
    need([(i.mnemonic, i.op_str) for i in instructions] == [
        ("ldr", "r5, [pc, #0x18]"), ("ldr", "r4, [pc, #0x18]"), ("mov", "r2, #0x800"),
        ("bl", "#0x8000b84"), ("ldr", "r4, [pc, #0x10]"), ("mov", "r2, #0x4c0"),
        ("ldr", "lr, [pc, #0xc]"), ("b", "#0x8000b84")], "complete DMA helper register/continuation contract")
    need(result[32:] == struct.pack("<4I", 0x06003200, BASE + TILES1, BASE + TILES2, 0x08090938), "complete helper literals")
    for item in instructions:
        assembled = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(item.mnemonic + " " + item.op_str, item.address)[0])
        need(assembled == item.bytes, "placed instruction roundtrip")
    return result, [{"address": i.address, "mnemonic": i.mnemonic, "operands": i.op_str} for i in instructions]


def detail_instructions(data):
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    decoder.detail = True
    return list(decoder.disasm(data, BASE + CODE))


def source_assets(source):
    # C3 maps physical30000..3FFFF; segment380C gives offset80C0.
    need(source[0x780039:0x780043] == bytes.fromhex("B80C388ED8B8CA00E6C3"), "actual source C3/DS producer")
    base = (struct.unpack_from("<H", source, 0x78003F)[0] & 127) * 0x10000 + ((struct.unpack_from("<H", source, 0x78003A)[0] << 4) & 0xFFFF)
    need(base == 0x4A80C0, "banked source graphics base")
    for start, expected in [
        (0x780043, "BF20FE33C033C03D00007506BEF035E90300BE606D56B96000F3A5"),
        (0x780070, "BF007233C033C03D00007506BEF003E90300BEE03AB98019F3A5"),
        (0x78008A, "BF000833C033C03D00007506BE0000E90300BEF036B9120051B91C00F3A583C70859E2F4"),
    ]:
        need(source[start:start + len(bytes.fromhex(expected))] == bytes.fromhex(expected), f"source title copy producer {start:X}")
    palette_words = struct.unpack_from("<96H", source, base + 0x35F0)
    need(all(v <= 0xFFF for v in palette_words), "source title BGR444 colors")
    palette = struct.pack("<96H", *(convert_color(v) for v in palette_words))
    planar = source[base + 0x3F0:base + 0x36F0]
    need(len(planar) == 0x3300, "source408 tiles")
    tiles = b"".join(convert_planar_tile(planar[i:i + 32]) for i in range(0, len(planar), 32))
    raw_map = source[base:base + 0x3F0]
    translated_map = convert_map(raw_map)
    cells = struct.unpack("<504H", translated_map)
    need(all(0x190 <= v & 1023 < 0x328 and 1 <= v >> 12 <= 6 for v in cells), "all map cells owned by loaded tile/palette extents")
    # Check every converted tile pixel against its actual source plane bit.
    for tile in range(408):
        for y in range(8):
            for x in range(8):
                value = tiles[tile * 32 + y * 4 + x // 2] >> (4 * (x % 2)) & 15
                expected = sum(((planar[tile * 32 + y * 4 + plane] >> (7 - x)) & 1) << plane for plane in range(4))
                need(value == expected, "complete tile bitplane inverse")
    return palette, tiles, translated_map, {"bank": 0xCA, "segment": 0x380C, "map_raw": base,
        "tiles_raw": base + 0x3F0, "palette_raw": base + 0x35F0, "map_cells": 504,
        "loaded_tiles": 408, "map_used_tiles": len({v & 1023 for v in cells}),
        "map_combined_tile_range": [min(v & 1023 for v in cells), max(v & 1023 for v in cells)],
        "map_palettes": sorted({v >> 12 for v in cells}), "tile_pixels_inverted": 408 * 64}


def build(before, source):
    need(sha(before) == INPUT and sha(source) == SOURCE, "exact v66 scene/source inputs")
    need(len(before) == 0x800000, "native8MB extent unchanged")
    expected_words = {0x90924: 0xE59F5258, 0x90928: 0xE59F4258, 0x9092C: 0xE3A02D36,
        0x90930: 0xE2822008, 0x90934: 0xEBFDC092, 0x90B7C: 0x0808FB58, 0x90B88: 0x0808BB58, 0x90B90: 0x0808B768}
    for at, value in expected_words.items():
        need(word(before, at) == value, f"native title consumer {at:X}")
    need(before[0xB84:0xBA8] == bytes.fromhex("0183A0E3D44088E5D85088E5BC2DC8E121CBA0E3BECDC8E1024184E0025185E01EFF2FE1"), "complete32-bit DMA consumer")
    for lo, hi in RESERVATIONS:
        need(before[lo:hi] == b"\xFF" * (hi - lo), "complete new allocation is FF")
    ownership = no_inbound(before, RESERVATIONS)
    palette, tiles, tilemap, source_report = source_assets(source)
    secondary = struct.pack("<16H", *(convert_color(v) for v in struct.unpack_from("<16H", source, 0x4AB790)))
    need(secondary == before[0x8B748:0x8B768], "source secondary palette already exact native")
    # Keep rows7/8 for the native shared resources and the existing128-halfword fade.
    palette += before[0x8FB58 + 0xC0:0x8FC58]
    code, instructions = helper()
    writes = [(TILES1, tiles[:0x2000], "source title tile chunk0"), (TILES2, tiles[0x2000:], "source title tile chunk1"),
        (MAP, tilemap, "source28x18 title map"), (PALETTE, palette, "six source palette rows plus two retained native rows"),
        (CODE, code, "two-chunk DMA with native continuation"),
        (0x90924, branch(0x90924, BASE + CODE), "title-only tile transfer"),
        (0x90B7C, struct.pack("<I", BASE + PALETTE), "title physical/fade-staging palette pointer"),
        (0x90B90, struct.pack("<I", BASE + MAP), "title map pointer")]
    after = bytearray(before)
    reports = []
    inverse = bytearray(before)
    for at, data, label in writes:
        need(len(data) % 4 == 0, "aligned native DMA/code data")
        after[at:at + len(data)] = data
        reports.append({"offset": at, "bytes": len(data), "label": label, "before_sha256": sha(before[at:at + len(data)]), "after_sha256": sha(data)})
    expected = {at + i for at, data, _ in writes for i, value in enumerate(data) if value != before[at + i]}
    actual = {i for i, (a, b) in enumerate(zip(before, after, strict=True)) if a != b}
    need(actual == expected, "complete expected-write population")
    inverse[:] = after
    for at, data, _ in writes:
        inverse[at:at + len(data)] = before[at:at + len(data)]
    need(inverse == before, "full-ROM inverse")
    need(after[0x8B748:0x90924] == before[0x8B748:0x90924], "all original shared artwork and title labels retained")
    report = {"schema": 1, "kind": "source15-title-background-isolated", "input_sha256": INPUT, "source_sha256": SOURCE,
        "output_sha256": sha(after), "source": source_report, "ownership": ownership, "expected_writes": reports,
        "changed_bytes": len(actual), "instructions": instructions, "tile_destination": [0x06003200, 0x06006500],
        "map_destination": {"start": 0x0600F000, "rows": 18, "row_bytes": 56, "stride": 64},
        "palette_destination": [0x05000020, 0x05000120], "fade_staging": [0x0201E400, 0x0201E500],
        "register_contract": "Same native r4/r5/r2/r8/r12/LR clobbers; r0/r1/r3/r6/r7/r9/r10/r11 and flags preserved; no stack use; LR08090938.",
        "limits": ["Static isolated component, independent verification pending; no emulator or live title claim.", "Menu tree and six extra title events remain separate."]}
    return bytes(after), report, (palette, tiles, tilemap)


def preview(directory, assets):
    from PIL import Image
    palette, tiles, tilemap = assets
    colors = struct.unpack("<128H", palette)
    cells = struct.unpack("<504H", tilemap)
    image = Image.new("RGB", (224, 144))
    zeros = 0
    for row in range(18):
        for column in range(28):
            cell = cells[row * 28 + column]
            tile, pal = (cell & 1023) - 0x190, (cell >> 12) - 1
            for y in range(8):
                for x in range(8):
                    sx, sy = (7 - x if cell & 0x400 else x), (7 - y if cell & 0x800 else y)
                    index = tiles[tile * 32 + sy * 4 + sx // 2] >> (4 * (sx % 2)) & 15
                    zeros += index == 0
                    color = colors[pal * 16 + index]
                    image.putpixel((column * 8 + x, row * 8 + y), tuple(((color >> shift) & 31) * 255 // 31 for shift in (0, 5, 10)))
    need(zeros == 0, "source BG has no mapped color-zero transparency discrepancy")
    image.save(directory / "title-source-background-1x.png")
    image.resize((448, 288), Image.Resampling.NEAREST).save(directory / "title-source-background-2x.png")
    return {"pixels": 224 * 144, "mapped_zero_index_pixels": zeros, "kind": "static reconstructed native BG, without sprite labels"}


def main():
    parser = argparse.ArgumentParser()
    for name in ("input", "wsc15", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    output, report, assets = build(args.input.read_bytes(), args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    report["preview"] = preview(args.output.parent, assets)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[source-title-background] " + report["output_sha256"])


if __name__ == "__main__":
    main()
