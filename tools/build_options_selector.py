#!/usr/bin/env python3
"""Build the guarded development four-language Options selector, not a release."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

from analyze_language_consumers import ASSETS, decode_asset, render_asset
from build_options_korean_poc import (BASE, RAW, GBA_SHA, FONT_SHA, LICENSE_SHA,
    EVENTS, need, sha, word, pack_tile, text_pixels, resource as korean_resource)
from options_selector_arm import SLOTS, source
from digicode_glyphs import font_glyphs as digicode_glyphs, text_pixels as digicode_pixels
from encode_digicode_reading import CATALOG

INPUTS = ("AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF",
          "F1BC5A96024E7035AFF2F6653C2C56258E52C5D13E556B2E950B234E55895D0E")
SELECTOR_RAW = 0x637000
DIGICODE_RAW = 0x639000
ROW_Y = {36:36, 56:54, 76:72, 96:90, 116:126}
COORDINATES = {0xC1A08:56, 0xC1AC0:76, 0xC1BAC:96, 0xC1C64:116,
               0xC1EF8:56, 0xC2090:76, 0xC22C8:96}
DEPENDENCIES = ((0x9F980, 0xA1060), (0xC15C4, 0xC4018),
    (0x11A84, 0x12058), (0x127E4, 0x12DD8), (0x11708, 0x11854),
    (0x1F894, 0x1FD30), (0x104C, 0x10E0))


def selector_glyphs(font, characters):
    """The same exact BDF pixels, including the kana's one-pixel left bearing."""
    result = {}
    for block in font.decode("utf-8").split("STARTCHAR ")[1:]:
        lines = block.splitlines()
        fields = {line.split()[0]: line.split()[1:] for line in lines if line.split()}
        code = int(fields["ENCODING"][0])
        if code < 0 or chr(code) not in characters:
            continue
        ch = chr(code)
        advance, dy = map(int, fields["DWIDTH"])
        width, height, left, bottom = map(int, fields["BBX"])
        need(ch not in result and dy == 0 and 0 < advance <= 8 and
             0 <= width <= 7 and 0 <= left <= 1 and left + width <= advance and
             0 <= height <= 11 and 0 <= bottom and height + bottom <= 11,
             f"complete bounded selector BDF glyph {ch!r}")
        rows = lines[lines.index("BITMAP") + 1:lines.index("ENDCHAR")]
        need(len(rows) == height and all(len(row) == (width + 7)//8*2 for row in rows),
             f"complete selector BDF rows {ch!r}")
        ink = {(x + left, y - height - bottom) for y, row in enumerate(rows)
               for x in range(width) if int(row, 16) & (1 << ((width + 7)//8*8 - x - 1))}
        need(ink or ch == " ", f"nonempty selector glyph {ch!r}")
        result[ch] = (advance, ink)
    need(set(result) == set(characters), "every selector character has an exact glyph")
    return result


def pack_p0(layouts, tiles, raw):
    need(len(tiles) <= 256 and all(0 < len(parts) <= 20 for parts in layouts),
         "native eight-bit tile lookup and bounded layouts")
    out = bytearray(16 + len(layouts)*8)
    for index, parts in enumerate(layouts):
        struct.pack_into("<II", out, 16 + index*8, len(parts), BASE + raw + len(out))
        for part in parts:
            out.extend(struct.pack("<Hbb", *part))
    descriptor = len(out)
    out.extend(struct.pack("<II", len(tiles)*32, BASE + raw + descriptor + 8))
    out.extend(b"".join(tiles))
    struct.pack_into("<IIHHHH", out, 0, BASE + raw + 16, BASE + raw + descriptor,
                     5, len(tiles) - 1, (len(tiles) - 1)*32, 8)
    return out


def digicode_resource(gba, draft, catalog, glyphs):
    native = decode_asset(gba, ASSETS[0])
    layouts = [[(p["tile_flags"],p["y"],p["x"]) for p in row["entries"]] for row in native["layouts"]]
    at=native["atlas_pixels_raw"]
    tiles=[gba[i:i+32] for i in range(at,at+native["atlas_bytes"],32)]
    indices={tile:i for i,tile in enumerate(tiles)}
    frames=[]
    for row in draft["entries"]:
        event,frame=row["event"],row.get("frame",0)
        pixels,width=digicode_pixels(row["ja_reading"],catalog,glyphs)
        is_label=event in (0,2,4,6,7)
        need(width <= (72 if is_label else 40),"Digicode text fits the native column")
        left=8 if is_label else ((24 if event==11 else 40)-width)//2
        parts=[(27,-8,0)] if is_label else []
        for y in (-15,-7):
            for x in range(0,width,8):
                tile=pack_tile(pixels,x,y)
                if not any(tile):
                    continue
                if tile not in indices:
                    indices[tile]=len(tiles)
                    tiles.append(tile)
                parts.append((indices[tile],y,left+x))
        layout=native["events"][event]["layouts"][frame]
        layouts[layout]=parts
        frames.append(dict(event=event,frame=frame,layout=layout,reading=row["ja_reading"],
                           width=width,left=left,parts=len(parts)))
    counts=[max(len(layouts[i]) for i in native["events"][e]["layouts"]) for e in EVENTS]
    return bytes(pack_p0(layouts,tiles,DIGICODE_RAW)),dict(p0_raw=DIGICODE_RAW,p1_raw=0xA02E8,
        p2_raw=0xA05B8,atlas_tiles=len(tiles),frames=frames,
        maximum_parts_by_object=counts,maximum_oam_parts=sum(counts),
        glyph_status="development pixel transcription; final supplied-chart review pending")


def selector_resource(gba, font, config, catalog, digicode_font):
    need(set(config) == {"schema", "status", "languages", "labels", "names", "save_errors",
                        "commit", "scope", "digicode"}, "known selector input fields")
    need(config["schema"] == 1 and config["status"] == "development-options-component" and
         config["languages"] == ["en", "ja", "ko", "digicode"], "explicit four-language development scope")
    need(all(len(config[key]) == 4 for key in ("labels", "names", "save_errors")),
         "one label, name and error per supported language")
    glyphs = selector_glyphs(font, set("".join(config["labels"][:3] + config["names"][:3] + config["save_errors"][:3])))
    native = decode_asset(gba, ASSETS[0])
    at = native["atlas_pixels_raw"]
    tiles = [gba[i:i + 32] for i in range(at, at + native["atlas_bytes"], 32)]
    indices = {tile: i for i, tile in enumerate(tiles)}
    layouts, frames = [], []
    for event, key in enumerate(("labels", "names", "save_errors")):
        for frame, text in enumerate(config[key]):
            pixels, width = (digicode_pixels(text,catalog,digicode_font) if frame==3 else text_pixels(text,glyphs))
            need(width <= (72 if event == 0 else 64), "selector horizontal text capacity")
            left = 8 if event == 0 else (56 - width)//2
            parts = []
            for y in ((-15,-7) if frame==3 else (-12,-4)):
                for x in range(0, width, 8):
                    tile = pack_tile(pixels, x, y)
                    if not any(tile):
                        continue
                    if tile not in indices:
                        indices[tile] = len(tiles)
                        tiles.append(tile)
                    parts.append((indices[tile], y, left + x))
            layouts.append(parts)
            frames.append(dict(event=event, frame=frame, text=text, width=width, left=left,
                               parts=len(parts)))
    layouts += [[(26,-8,72)],[(26,-8,72),(0x401A,-8,0)],
                [(26,-8,72),(0x401A,-8,0)],[(0x401A,-8,0)]]
    out=pack_p0(layouts,tiles,SELECTOR_RAW)
    p1 = SELECTOR_RAW + len(out)
    out.extend(struct.pack("<II", BASE + p1 + 8, 0))
    commands = p1 + 8 + 4*16
    for event in range(4):
        out.extend(struct.pack("<IIII", 4, BASE + commands + event*64, 0, 0))
    for layout in range(16):
        out.extend(struct.pack("<BBHHHII", 1, 255, layout, 0, 0, 0, 0))
    return bytes(out), dict(p0_raw=SELECTOR_RAW, p1_raw=p1, p2_raw=0xA05B8,
        atlas_tiles=len(tiles), frames=frames, parts=[len(parts) for parts in layouts],
        event_layouts=[list(range(e*4, e*4 + 4)) for e in range(4)])


def assemble(text, at, literals):
    assembler = Ks(KS_ARCH_ARM, KS_MODE_ARM)
    payload = bytes(assembler.asm(text, BASE + at)[0])
    end = len(payload) - literals
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(payload[:end], BASE + at))
    need(sum(row.size for row in decoded) == end, "complete final-placement ARM decode")
    for row in decoded:
        need(bytes(assembler.asm(row.mnemonic + " " + row.op_str, row.address)[0]) == row.bytes,
             "every installed ARM instruction independently decodes/reassembles")
    return payload, dict(raw=at, code_bytes=end, literal_bytes=literals,
        instructions=[dict(address=row.address, mnemonic=row.mnemonic, operands=row.op_str) for row in decoded])


def branch(at, destination):
    delta = destination - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < 1 << 25, "ARM BL extent")
    return struct.pack("<I", 0xEB000000 | ((delta//4) & 0xFFFFFF))


def check_ownership(before, spans):
    for lo, hi in spans:
        need(before[lo:hi] == b"\xff"*(hi - lo), "entire exact allocation is unused FF")
    for at in range(len(before) - 3):
        pointer = word(before, at) - BASE
        need(not any(lo <= pointer < hi for lo, hi in spans), f"encoded inbound reference {at:X}")
    for at in range(0, len(before) - 3, 4):
        value = word(before, at)
        if value >> 28 == 15:
            continue
        targets = []
        if value & 0x0E000000 == 0x0A000000:
            delta = (value & 0xFFFFFF) - (0x1000000 if value & 0x800000 else 0)
            targets.append(at + 8 + delta*4)
        if value & 0x0E1F0000 == 0x041F0000:
            targets.append(at + 8 + (value & 4095)*(1 if value & 0x800000 else -1))
        need(not any(lo <= target < hi for target in targets for lo, hi in spans),
             f"aligned ARM inbound reference {at:X}")


def build(before, gba, font, license_data, draft, config, catalog):
    need(sha(before) in INPUTS and len(before) == 0x800000 and sha(gba) == GBA_SHA,
         "exact supported predecessor and original USA image")
    need(sha(font) == FONT_SHA and sha(license_data) == LICENSE_SHA, "exact licensed BDF input")
    for lo, hi in DEPENDENCIES:
        need(before[lo:hi] == gba[lo:hi], f"unchanged native dependency {lo:X}..{hi:X}")
    korean, korean_info = korean_resource(gba, font, draft)
    glyphs=digicode_glyphs(catalog)
    digi,digicode_info=digicode_resource(gba,draft,catalog,glyphs)
    selector, selector_info = selector_resource(gba, font, config, catalog, glyphs)
    writes = [(RAW, korean, "Korean Options atlas; original resources retained"),
              (SELECTOR_RAW, selector, "new native sixth-row P0/P1 resource"),
              (DIGICODE_RAW,digi,"Japanese-reading Digicode Options resource")]
    machine = []
    for name, (text, literals) in source(*(BASE + selector_info[key] for key in
                                        ("p0_raw", "p1_raw", "p2_raw")),BASE+DIGICODE_RAW).items():
        at, capacity = SLOTS[name]
        payload, decoded = assemble(text, at, literals)
        need(len(payload) <= capacity, "bounded ARM routine: " + name)
        writes.append((at, payload, name))
        machine.append(dict(name=name, **decoded))
    spans = [(RAW, RAW + len(korean)), (min(x[0] for x in SLOTS.values()),
             max(at + count for at, count in SLOTS.values())),
             (SELECTOR_RAW, SELECTOR_RAW + len(selector)),(DIGICODE_RAW,DIGICODE_RAW+len(digi))]
    check_ownership(before, spans)

    hooks = {0xC15F4: (0xE3B00001, "palette_choice"), 0xC1824: (0xE3B00001, "constructor_choice"),
             0xC184C: (0xE59F803C, "create_task"), 0xC328C: (0xE3100080, "input_guard"),
             0xC32FC: (0xE3580004, "confirm")}
    for at, (old, name) in hooks.items():
        need(word(before, at) == old, "exact native selector hook")
        writes.append((at, branch(at, SLOTS[name][0]), name + " native hook"))
    creations = []
    for at in range(0xC2564, 0xC315C, 4):
        if before[at:at + 4] == branch(at, 0x127E4):
            creations.append(at)
            writes.append((at, branch(at, SLOTS["route_object"][0]), "route English/Korean presentation tuple"))
    need(len(creations) == 15, "all fifteen actual English constructor calls")
    replacements = {0xC32B8: (0xE3A02004, 0xE3A02005), 0xC32C4: (0xE3520004, 0xE3520005),
        0xC33F4: (0x1FB, 0x3FB), 0xC1BE4: (0xE3A08004, 0xE3A08005),
        0xC28B4: (0xE3A08004, 0xE3A08005)}
    # Constructor input is explicitly zero at C17BC; these are its reachable
    # full-height coordinates, including the r0 shared by values and arrows.
    need(word(before, 0xC17BC) == 0xE3A02000, "fixed full-height constructor input")
    for at, y in COORDINATES.items():
        for offset in (0, 0xCD0):
            replacements[at + offset] = (0xE3A00000 | y, 0xE3A00000 | ROW_Y[y])
    for at, register, y in ((0xC34E0,9,96),(0xC34EC,9,96),(0xC36E0,9,56),
            (0xC36EC,9,76),(0xC36F8,9,96),(0xC3704,9,116),(0xC39C8,2,56),(0xC3BA8,2,76)):
        opcode = 0xE3A00000 | register << 12
        replacements[at] = (opcode | y, opcode | ROW_Y[y])
    for at, (old, new) in replacements.items():
        need(word(before, at) == old, f"exact row/reflow/retirement word {at:X}")
        writes.append((at, struct.pack("<I", new), "six-row cursor, Return coordinate or retirement"))

    budgets = []
    for language, original in zip(("en", "ja"), (ASSETS[1], ASSETS[0])):
        asset = decode_asset(gba, original)
        sizes = {row["layout"]: len(row["entries"]) for row in asset["layouts"]}
        budgets.append((language, sum(max(sizes[i] for i in asset["events"][e]["layouts"]) for e in EVENTS)))
    budgets.append(("ko", korean_info["active_budget"]["maximum_oam_parts"]))
    budgets.append(("digicode",digicode_info["maximum_oam_parts"]))
    counts = selector_info["parts"]
    for language_index, (language, base_parts) in enumerate(budgets):
        normal = counts[language_index]+max(counts[4+selected]+counts[12+selected] for selected in range(4))
        total = base_parts+max(normal,counts[8+language_index])
        need(total <= 127 and total*32 <= 4096, "aggregate whole-screen native OAM/tile budget")
        budgets[language_index] = dict(language=language, existing=base_parts,
            selector=total - base_parts, maximum_oam=total, maximum_tile_bytes=total*32)

    manifest_writes, end = [], 0
    for at, value, purpose in sorted(writes):
        need(end <= at and at + len(value) <= len(before), "disjoint bounded Expected Writes")
        end = at + len(value)
        manifest_writes.append(dict(raw=at, bytes=len(value), purpose=purpose,
            before_sha256=sha(before[at:end]), after_sha256=sha(value)))
    after = bytearray(before)
    for at, value, _ in writes:
        after[at:at + len(value)] = value
    inverse = bytearray(after)
    for at, value, _ in writes:
        inverse[at:at + len(value)] = before[at:at + len(value)]
    need(inverse == before, "whole-image final diff explained by single writers")
    for info, name, events in ((korean_info, "korean-options", 12), (selector_info, "selector", 4),
                              (digicode_info,"digicode-options",12)):
        decode_asset(after, (name, info["p0_raw"], info["p1_raw"], info["p2_raw"], events, info["atlas_tiles"]))
    return bytes(after), dict(schema=1, kind="development-four-language-options-selector",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=sha(gba),
        font_sha256=sha(font), font_license_sha256=sha(license_data),
        korean_resource=korean_info, selector_resource=selector_info, digicode_resource=digicode_info,budgets=budgets,
        digicode_catalog_sha256=sha(json.dumps(catalog,ensure_ascii=False,sort_keys=True).encode("utf-8")),
        digicode_glyph_rows={name:rows.hex() for name,rows in glyphs.items()},
        dependencies=[dict(start=lo, end=hi, sha256=sha(gba[lo:hi])) for lo, hi in DEPENDENCIES],
        expected_writes=manifest_writes, allocation_spans=spans, machine_code=machine,
        isa="ARM7TDMI ARMv4T, little-endian ARM32; Keystone 0.9.2 / Capstone 5.0.6",
        task=dict(priority=0x1500, header_bytes=0x18, allocation_stride=0x118,
                  payload_capacity=0x100, payload_used=0xF8, presentation_offsets=[8, 0x58, 0xA8],
                  retirement_bit=0x200, complete_retirement_mask=0x3FB),
        language_tags={"en":0xA0, "ja":0xA1, "ko":0xA2,"digicode":0xA3},
        default="legacy and invalid tags read as English without rewriting",
        save_contract="A commits/exits; failed writes retain menu; A retries; B repairs old record before exit",
        row_baselines=[36,54,72,90,108,126], logical_window=[16,128],
        normal_cancel="B/Return before an attempted write discards staged selection without EEPROM write",
        supported_scope="Options only; new selection appears on re-entry",
        original_assets_preserved=True, supplied_save_accessed=False, runtime_claim=False,
        power_failure_atomic=False, four_language_feature_complete=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "gba", "font", "license", "output"):
        parser.add_argument(name, type=Path)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--draft", type=Path, default=root/"localization/options-draft.json")
    parser.add_argument("--selector", type=Path, default=root/"localization/options-selector.json")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--render-directory", type=Path)
    args = parser.parse_args()
    need(all(p is None or p.suffix.lower() != ".sav" for p in vars(args).values()), "save paths forbidden")
    need(args.output.resolve() not in {args.before.resolve(), args.gba.resolve()}, "never overwrite source")
    result, report = build(*(getattr(args, key).read_bytes() for key in ("before", "gba", "font", "license")),
        *(json.loads(getattr(args, key).read_text(encoding="utf-8")) for key in ("draft", "selector")),
        json.loads(CATALOG.read_text(encoding="utf-8")))
    if args.render_directory:
        info = report["selector_resource"]
        asset = decode_asset(result, ("selector", info["p0_raw"], info["p1_raw"], info["p2_raw"], 4, info["atlas_tiles"]))
        report["preview"] = render_asset(result, asset, args.render_directory, True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[Options selector] " + report["output_sha256"])


if __name__ == "__main__":
    main()
