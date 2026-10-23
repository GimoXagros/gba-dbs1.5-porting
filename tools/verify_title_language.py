#!/usr/bin/env python3
"""Independent five-event title-language ROM/source verification.

No producer/analyzer is imported and no target, emulator or save is executed.
Pixels are reconstructed from the two source ROMs, licensed BDF and reviewed
Digicode row bytes. The manifest is checked only after deriving the contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unicodedata

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BEFORE = "A18B0EDA679D381BF143C49438459ABC7F02F0871D10FE347C79C5582CF62F71"
AFTER = "143ECA1C15D495E59D52252C7BB046217FEDD462772CC887A4D2D4C9830F4A80"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
FONT = "4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED"
LICENSE = "76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C"
DG_JSON = "ABDFB29C40C3C8F38BB64214B1F3695FED4774C32362A6ACC1F4EE5D90029EEA"
DG_ROWS = "E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195"
BASE, HOOK, HELPER = 0x08000000, 0x090A18, 0x63FB00
P0, P1, P2 = 0x08FD08, 0x08FC58, 0x090878
ALLOCATIONS = ((0x63A800, 0x63BBA4), (0x63D000, 0x63DB60),
               (0x63E000, 0x63ED64), (HELPER, HELPER + 68))
WRITES = ((HOOK, HOOK + 4),) + ALLOCATIONS
SOURCE_JA = ("スタートボタンをおしてね！", "ひとりでバトル", "ともだちとバトル", "オプション", "D-ARK")
KOREAN = ("시작 버튼을 눌러 주세요", "혼자 대전", "친구와 대전", "설정", "D-ARK")
READINGS = ("スタートボタンをおしてね", "ひとりでバトル", "ともだちとバトル", "おぷしよん")


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded input extent")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def ptr(data, at):
    value = u(data, at) - BASE
    need(0 <= value < len(data), "native pointer extent")
    return value


def branch(data, at):
    word = u(data, at)
    need(word & 0x0E000000 == 0x0A000000, "ARM branch instruction")
    displacement = word & 0xFFFFFF
    displacement -= 0x1000000 if displacement & 0x800000 else 0
    return at + 8 + 4 * displacement


def literal(data, at):
    word = u(data, at)
    need(word & 0x0F7F0000 == 0x051F0000, "ARM PC-relative word load")
    return u(data, at + 8 + (1 if word & 0x800000 else -1) * (word & 0xFFF))


def sequence(data, at, rows):
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(cut(data, at, 4 * len(rows)), BASE + at))
    need([f"{row.mnemonic} {row.op_str}" for row in decoded] == rows, f"decoded ARM contract {at:X}")


def pixels(parts, atlas, planar=False):
    result = {}
    for flags, top, left in parts:
        tile = flags & 0x3FFF
        need(tile < 256 and tile * 32 + 32 <= len(atlas), "native low-byte tile identity")
        for y in range(8):
            sy = 7 - y if flags & 0x8000 else y
            for x in range(8):
                sx = 7 - x if flags & 0x4000 else x
                if planar:
                    value = sum(((atlas[tile * 32 + sy * 4 + plane] >> (7 - sx)) & 1) << plane for plane in range(4))
                else:
                    value = atlas[tile * 32 + sy * 4 + sx // 2] >> (4 * (sx % 2)) & 15
                if value:
                    point = left + x, top + y
                    # Earlier OAM entries win when opaque pixels overlap.
                    result.setdefault(point, value)
    return result


def native(data, p0, allocation=None):
    table, descriptor = ptr(data, p0), ptr(data, p0 + 4)
    size, start = u(data, descriptor), ptr(data, descriptor + 4)
    need(0 < size <= 256 * 32 and size % 32 == 0, "complete bounded native atlas")
    need(struct.unpack("<4H", cut(data, p0 + 8, 8)) == (5, size // 32 - 1, size - 32, 8), "native P0 header")
    atlas = cut(data, start, size)
    frames, part_positions, cursor = [], [], table + 40
    need(table == p0 + 16, "five-layout table begins after P0")
    for i in range(5):
        count, address = u(data, table + i * 8), ptr(data, table + i * 8 + 4)
        need(0 < count <= 127 and address == cursor, "complete contiguous title part array")
        parts = [struct.unpack("<Hbb", cut(data, address + j * 4, 4)) for j in range(count)]
        frames.append((parts, pixels(parts, atlas)))
        part_positions.append(address)
        cursor += count * 4
    need(descriptor == cursor and start == descriptor + 8, "no hidden resource bytes")
    if allocation:
        need((p0, start + size) == allocation, "resource wholly owns its declared allocation")
    return dict(frames=frames, atlas=atlas, atlas_start=start, part_positions=part_positions, tiles=size // 32)


def banked(data, bank, segment, offset=0):
    physical = segment * 16 + offset
    need(0x20000 <= physical < 0x30000, "source C2 address window")
    return (bank & (len(data) // 65536 - 1)) * 65536 + physical - 0x20000


def source_resource(data, p0, count):
    need(u(data, p0) == 16 and h(data, p0 + 18) == 16 + count * 4, "source layout extent")
    descriptor = banked(data, h(data, p0 + 6), h(data, p0 + 4))
    size, offset, segment, bank = struct.unpack("<4H", cut(data, descriptor, 8))
    start = banked(data, bank, segment, offset)
    atlas = cut(data, start, size)
    need(size % 32 == 0 and 0 < size <= 8192, "complete source four-plane atlas")
    frames = []
    for index in range(count):
        total, offset = struct.unpack("<2H", cut(data, p0 + 16 + 4 * index, 4))
        need(0 < total <= 127, "bounded source layout")
        parts = [struct.unpack("<Hbb", cut(data, p0 + offset + 4 * j, 4)) for j in range(total)]
        frames.append((parts, pixels(parts, atlas, True)))
    return dict(frames=frames, atlas=atlas, atlas_start=start, descriptor=descriptor)


def packed(planar):
    out = bytearray()
    for at in range(0, len(planar), 4):
        row = [sum(((planar[at + p] >> (7 - x)) & 1) << p for p in range(4)) for x in range(8)]
        out.extend(row[x] | row[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(out)


def source_contract(gba, old, new):
    need(cut(new, 0x780148, 9) == bytes.fromhex("33c033c03d00007551"), "fixed Japanese title branch")
    for at, expected in ((0x780179, (0xBC, 0x23FE, 0, 0x3C3FE0)),
                         (0x780182, (0xBD, 0x23A8, 0, 0x3D3A80)),
                         (0x780170, (0xBD, 0x27EE, 0, 0x3D7EE0))):
        need([new[at + d] for d in (0, 3, 6)] == [0x68] * 3, "source resource pushes")
        bank, segment, offset = (h(new, at + d) for d in (1, 4, 7))
        need((bank, segment, offset, banked(new, bank, segment, offset)) == expected, "source branch binds correct resource")
    variants = ((old, 0x2B0BA0, 0x22FF80, 0x2B5FC0, 5),
                (old, 0x2B14B0, 0x2B4F60, 0x2B5FF0, 5),
                (new, 0x3C3FE0, 0x3D3A80, 0x3D7EE0, 11),
                (new, 0x3C43D0, 0x3D3B70, 0x3D7F10, 11))
    resources, event_report = [], []
    native_table = ptr(gba, P1)
    need(native_table == P1 + 8 and u(gba, P1 + 4) == 0, "native P1 flags")
    for data, p0, p1, p2, count in variants:
        resources.append(source_resource(data, p0, count))
        need(u(data, p1) == 4 and h(data, p1 + 6) == 4 + count * 8, "source P1 event count")
        converted = cut(data, p2, 6)
        for color in struct.unpack("<16H", cut(data, p2 + 6, 32)):
            channels = [(color >> shift) & 15 for shift in (8, 4, 0)]
            value = sum(((v * 2 + 1) if v else 0) << (i * 5) for i, v in enumerate(channels))
            converted += struct.pack("<H", value)
        need(converted == cut(gba, P2, 38), "all four source palettes equal the unchanged native palette")
        for event in range(5):
            number, commands, metadata, tail = struct.unpack("<4H", cut(data, p1 + 4 + event * 8, 8))
            nt = native_table + event * 16
            need(number == u(gba, nt) == 1 and tail == u(gba, nt + 12) == 0, "native/source event counts")
            command = cut(data, p1 + commands, 12)
            need(command == cut(gba, ptr(gba, nt + 4), 12) and cut(gba, ptr(gba, nt + 4) + 12, 4) == bytes(4), "all command fields and native widening")
            need(h(data, p1 + commands + 2) == event, "event directly selects its source layout")
            need(cut(data, p1 + metadata, 8) == cut(gba, ptr(gba, nt + 8), 8), "complete source A metadata")
        event_report.append(dict(p0=p0, p1=p1, p2=p2, source_event_count=count, checked_events=5))
    retail = native(gba, P0)
    # Native English has its own prompt/Options drawing. Do not pretend those
    # five localized bitmaps are identical across source versions/platforms.
    english_equal = [retail["frames"][i][1] == resources[1]["frames"][i][1] for i in range(5)]
    need(english_equal == [False, True, True, False, True], "bounded English retail pixel oracle and known localized differences")
    need([len(f[0]) for f in resources[2]["frames"][:5]] == [17, 22, 22, 22, 22], "complete Japanese layouts")
    return resources[2], retail, dict(variants=event_report, source_atlas_sha256=sha(resources[2]["atlas"]),
                                    source_atlas_raw=resources[2]["atlas_start"], source_atlas_bytes=len(resources[2]["atlas"]),
                                    english_retail_equal_source10_by_event=english_equal,
                                    japanese10_equal_japanese15_by_event=[resources[0]["frames"][i][1] == resources[2]["frames"][i][1] for i in range(5)])


def bdf_text(font, text):
    cursor, ink = 0, set()
    for ch in text:
        match = re.search(r"^ENCODING " + str(ord(ch)) + r"\n(.*?)^ENDCHAR$", font, re.M | re.S)
        need(match is not None, f"licensed BDF contains {ch!r}")
        block = match.group(1)
        advance = int(re.search(r"^DWIDTH (\d+) 0$", block, re.M).group(1))
        width, height, left, bottom = map(int, re.search(r"^BBX (\d+) (\d+) (-?\d+) (-?\d+)$", block, re.M).groups())
        bitmap = block.split("BITMAP\n")[1].splitlines()
        need(len(bitmap) == height, "full BDF glyph height")
        for y, row in enumerate(bitmap):
            bits = f"{int(row, 16):0{((width + 7) // 8) * 8}b}"
            for x in range(width):
                if bits[x] == "1":
                    ink.add((cursor + left + x + 1, y - height - bottom))
        cursor += advance
    out = {(x + dx, y + dy): 15 for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    out.update({point: 13 for point in ink})
    return out, max(x for x, _ in out) + 1


def dg_font(font_bytes, catalog_bytes):
    need(sha(font_bytes) == DG_JSON, "frozen reviewed Digicode JSON")
    catalog, font = json.loads(catalog_bytes), json.loads(font_bytes)
    rows = {key: bytes.fromhex(value) for key, value in font["glyphs"].items()}
    ids = [g["id"] for g in catalog["glyphs"] + catalog["latin_glyphs"]]
    need(len(ids) == len(set(ids)) == len(rows) == 98 and set(ids) == set(rows), "all98 canonical glyph identities")
    need(sha(b"".join(rows[key] for key in ids)) == DG_ROWS, "canonical Japanese-then-Latin row digest")
    lookup = {g[key]: g["id"] for group, keys in (("glyphs", ("hiragana", "katakana")),
                                                ("latin_glyphs", ("uppercase", "lowercase")))
              for g in catalog[group] for key in keys}
    def render(text):
        chars = unicodedata.normalize("NFC", text)
        need(chars and all(ch in lookup for ch in chars), "strict Digicode input; no implicit small kana/kanji/punctuation")
        images = []
        for ch in chars:
            bitmap = Image.frombytes("1", (8, 16), rows[lookup[ch]]).convert("L")
            left, top, right, bottom = bitmap.getbbox()
            need(top >= 1 and bottom <= 15, "full glyph edge fits sixteen rows")
            images.append(bitmap.crop((left, 0, right, 16)))
        width = 1 + sum(image.width + 1 for image in images)
        ink, cursor = Image.new("L", (width, 16)), 1
        for image in images:
            ink.paste(image, (cursor, 0)); cursor += image.width + 1
        edge = ink.filter(ImageFilter.MaxFilter(3))
        return ({(x, y - 15): 13 if ink.getpixel((x, y)) else 15
                 for y in range(16) for x in range(width) if edge.getpixel((x, y))}, width)
    return render, lookup


def shift(pix, dx, dy):
    return {(x + dx, y + dy): color for (x, y), color in pix.items()}


def expected_images(source, retail, font_bytes, dg_bytes, catalog_bytes):
    render, lookup = dg_font(dg_bytes, catalog_bytes)
    source_frames, original = source["frames"], retail["frames"]
    exclamation = {p: c for p, c in source_frames[0][1].items() if 48 <= p[0] <= 50}
    hyphen = {p: c for p, c in source_frames[4][1].items() if -7 <= p[0] <= -2 and p[1] == -1}
    marker = {p: c for p, c in original[1][1].items() if -43 <= p[0] <= -30 and -7 <= p[1] <= 6}
    need(len(exclamation) == 22 and min(y for x, y in exclamation) == -4 and max(y for x, y in exclamation) == 3, "complete native exclamation")
    need([hyphen[x, -1] for x in range(-7, -1)] == [14, 13, 13, 13, 13, 14], "complete source hyphen, not English separator/long-vowel symbol")
    need(len(marker) == 196, "complete original marker rectangle")
    def prompt(text, width):
        width += 2 + 3
        image = dict(text)
        image.update(shift(exclamation, width - 3 - 48, 0))
        return shift(image, -(width // 2), 0)
    korean = []
    font = font_bytes.decode("utf-8").replace("\r\n", "\n")
    for event, text in enumerate(KOREAN[:4]):
        glyphs, width = bdf_text(font, text)
        if not event:
            korean.append(prompt(shift(glyphs, 0, 5), width))
        else:
            image = dict(original[event][1])
            image.update({(x, y): 15 for y in range(-7, 7) for x in range(-28, 43)})
            image.update(shift(glyphs, 8 - width // 2, 5))
            korean.append(image)
    korean.append(source_frames[4][1])
    digicode, width_report = [], []
    glyphs, width = render(READINGS[0])
    digicode.append(prompt(shift(glyphs, 0, 7), width))
    for event, width in enumerate((80, 88, 64, 64), 1):
        left = -(width // 2)
        image = {(x, y): 13 if y in (-9, 8) or x in (left, left + width - 1) else 15
                 for y in range(-9, 9) for x in range(left, left + width)}
        image.update(shift(marker, left + 44, 0))
        if event < 4:
            glyphs, text_width = render(READINGS[event]); dy = 7
        else:
            a, aw = render("D"); b, bw = render("ARK")
            glyphs = dict(a)
            glyphs.update(shift(hyphen, aw + 2 + 7, -5))
            glyphs.update(shift(b, aw + 10, 0))
            text_width, dy = aw + 10 + bw, 5
        dx = left + 16 + (width - 17 - text_width) // 2
        need(dx >= left + 15 and max(x for x, _ in glyphs) + dx < left + width - 1, "all Digicode text fits its button")
        image.update(shift(glyphs, dx, dy))
        digicode.append(image); width_report.append(dict(event=event, width=width, text_width=text_width))
    return korean, digicode, render, dict(source_ja=list(SOURCE_JA), korean=list(KOREAN),
        digicode_readings=list(READINGS) + ["D + native Japanese hyphen + ARK"],
        reading_ids=[[lookup[ch] for ch in text] for text in READINGS] + [[lookup[ch] for ch in "DARK"]],
        small_kana_policy="Only source オプション has explicit title reading おぷしよん; strict encoder remains unchanged.",
        source_wording_evidence="Visually reviewed Japanese source bitmap; binding, every pixel and palette independently checked.",
        exclamation_pixels=22, hyphen_pixels=6, marker_pixels=196, buttons=width_report)


def verify_resources(after, source, retail, korean, digicode):
    result = [native(after, P0)] + [native(after, start, (start, end)) for start, end in ALLOCATIONS[:3]]
    need(result[0]["frames"] == retail["frames"] and result[0]["atlas"] == retail["atlas"], "English native resource intact")
    need(result[1]["frames"] == source["frames"][:5] and result[1]["atlas"] == packed(source["atlas"]), "complete Japanese source parts and four-plane conversion")
    for label, decoded, images in (("Korean", result[2], korean), ("Digicode", result[3], digicode)):
        for event, image in enumerate(images):
            need(decoded["frames"][event][1] == image, f"every {label} event{event} pixel, full ink/edge/decoration")
    need([len(f[0]) for f in result[0]["frames"]] == [8, 22, 22, 26, 22], "English parts")
    need([len(f[0]) for f in result[1]["frames"]] == [17, 22, 22, 22, 22], "Japanese parts")
    need([len(f[0]) for f in result[2]["frames"]] == [24, 22, 22, 22, 22], "Korean parts")
    need([len(f[0]) for f in result[3]["frames"]] == [26, 30, 33, 24, 24], "Digicode parts")
    return result


def verify_helper(before, after):
    need(u(before, HOOK) == 0xE59F81A0 and literal(before, HOOK) == BASE + P0, "original r8-only LDR")
    need(u(after, HOOK) >> 24 == 0xEA and branch(after, HOOK) == HELPER, "B preserves caller LR; not BL")
    sequence(after, HELPER, ["push {r0, r1}", "mrs r1, apsr", "ldr r0, [pc, #0x20]", "ldrb r0, [r0]",
        "sub r0, r0, #0xa0", "cmp r0, #3", "movhi r0, #0", "add r8, pc, #0x10",
        "ldr r8, [r8, r0, lsl #2]", "msr apsr_nzcvq, r1", "pop {r0, r1}", "b #0x8090a1c"])
    need(u(after, HELPER + 4) == 0xE10F1000 and u(after, HELPER + 36) == 0xE128F001, "CPSR saved/restored using flags-only mask")
    table = struct.unpack("<5I", cut(after, HELPER + 48, 20))
    need(table == (0x0300112F, BASE + P0, BASE + ALLOCATIONS[0][0], BASE + ALLOCATIONS[1][0], BASE + ALLOCATIONS[2][0]), "one existing tag byte and exact four resources")
    need(branch(after, HELPER + 44) == HOOK + 4, "fixed original continuation")
    cases = 0
    # A static transfer calculation, not target execution. Exact decoded words
    # above constrain all reads/writes. Unsigned HI is (C && !Z) after CMP.
    for tag in range(256):
        index = (tag - 0xA0) & 0xFFFFFFFF
        carry, zero = index >= 3, index == 3
        if carry and not zero:
            index = 0
        need(index == (tag - 0xA0 if 0xA0 <= tag <= 0xA3 else 0), "all invalid tags safely default English")
        for flags in range(32):
            cpsr = (flags << 27) | 0x10
            # Opaque register identities make this preservation proof apply
            # to arbitrary entry values, rather than one numeric test seed.
            original = [("entry-register", i) for i in range(15)]
            registers = original.copy()
            stack = registers[0:2]
            sp_delta = -8
            registers[1] = cpsr
            registers[0] = index
            registers[8] = table[1 + index]
            raw = (tag - 0xA0) & 0xFFFFFFFF
            difference = (raw - 3) & 0xFFFFFFFF
            overflow = bool((raw ^ 3) & (raw ^ difference) & 0x80000000)
            compared = ((cpsr & 0x0FFFFFFF) | ((difference >> 31) << 31) |
                        (int(difference == 0) << 30) | (int(raw >= 3) << 29) | (int(overflow) << 28))
            restored = (compared & 0x00FFFFFF) | (registers[1] & 0xFF000000)
            registers[0:2] = stack
            sp_delta += 8
            need(restored == cpsr and sp_delta == 0 and
                 all(registers[i] == original[i] for i in range(15) if i != 8) and
                 registers[8] == table[1 + index], "all arbitrary registers except r8, LR, SP and CPSR restored")
            cases += 1
    sequence(before, 0x90A00, ["stmdb sp!, {r4}", "stmdb sp!, {fp}", "ldr r8, [pc, #0x1ac]",
        "stmdb sp!, {r8}", "stmdb sp!, {r8}", "stmdb sp!, {r8}"])
    sequence(before, HOOK + 4, ["stmdb sp!, {r8}", "stmdb sp!, {r8}", "stmdb sp!, {r8}"])
    need(u(before, 0x908A0) == 0xE92D4033 and u(before, 0x909CC) == 0xE92D0008 and u(before, 0x127E4) == 0xE92D0039, "native stack frames")
    return dict(static_transfer_cases=cases, tags=256, high_flag_patterns=32,
        preserved_registers="r0-r7,r9-r14 and CPSR; r8 is original LDR destination; PC rejoins090A1C",
        helper_stack_bytes=8, caller_depth_at_hook=44, depth_with_helper=52, original_argument_and_callee_depth=100,
        scratch_proof="The helper uses the two descending outgoing slots subsequently written by the first two unchanged P0 pushes; its minimum SP is above the original callee minimum.",
        writes="Only two private stack words, restored SP; tag read-only; no new persistent RAM")


def calls(data, start, end):
    return [(at, branch(data, at)) for at in range(start, end, 4) if u(data, at) & 0x0F000000 == 0x0B000000]


def population(after, gba, resources):
    # Actual native constructor, event selection and object coordinates, not
    # a sum of producer-declared frame costs.
    need(literal(after, 0x909D4) == literal(after, 0x90A90) == 0x03002A78, "five presentation base")
    sequence(after, 0x909CC, ["stmdb sp!, {r3}", "mov r2, #5", "ldr r4, [pc, #0x1d8]", "mov r0, #0"])
    sequence(after, 0x90A5C, ["add r0, r0, #1", "add r4, r4, #0x50", "subs r2, r2, #1", "bgt #0x80909dc"])
    need(branch(after, 0x90A54) == 0x127E4 and branch(after, 0x90AD8) == 0x12874, "native creation and event dispatcher")
    need(u(after, 0x90A94) == 0xE3A02005 and u(after, 0x90A98) == 0xE3A00000 and u(after, 0x90AE0) == 0xE2844050, "five event IDs in constructor order")
    coords = struct.unpack("<10h", cut(after, 0x90B54, 20))
    need(coords == (112, 104, -48, 36, -48, 72, -48, 108, -48, 200), "all five native coordinates, including offscreen event4")
    need(literal(after, 0x90A08) == BASE + P1 and literal(after, 0x90A28) == BASE + P2, "unchanged P1 and P2 ABI arguments")
    need(cut(after, 0x127E4, 0x74) == cut(gba, 0x127E4, 0x74), "native resource-field constructor unchanged")
    callbacks = (("prompt", 0x90C7C, 0x90E00, [0x90DD0]),
                 ("menu_slide", 0x90E58, 0x90F5C, [0x90F30]),
                 ("menu", 0x90FA0, 0x9126C, [0x91240]),
                 ("menu_exit", 0x91310, 0x914A8, [0x91414]),
                 ("fade", 0x914E4, 0x91578, []),
                 ("timeout", 0x91598, 0x91668, []),
                 ("mode_controller", 0x15AB4, 0x15B70, []))
    rows = []
    for name, start, end, expected_draws in callbacks:
        need(cut(after, start, end - start) == cut(gba, start, end - start), "original complete callback retained")
        found = calls(after, start, end)
        need([at for at, target in found if target == 0x12C28] == expected_draws, f"all direct draw sites {name}")
        need(all(target not in (0x11AC4, 0x127E4) for _, target in found), "callbacks create no hidden tasks/presentations")
        rows.append(dict(name=name, start=start, end=end, draw_sites=expected_draws, calls=found, sha256=sha(cut(after, start, end - start))))
    need(literal(after, 0x90DC4) == 0x03002A78 and literal(after, 0x90EB8) == literal(after, 0x911EC) == literal(after, 0x913C8) == 0x03002AC8, "prompt or four menu object bases")
    need(u(after, 0x90A70) == 0xE3A08004 and literal(after, 0x90A6C) == literal(after, 0x90EB4) == 0x03002A64, "menu slide count initialized to four")
    sequence(after, 0x90F38, ["add r1, r1, #0x50", "ldr r8, [pc, #0x48]", "ldrh sb, [r8]", "add sb, sb, #1", "strh sb, [r8]", "subs r2, r2, #1", "bgt #0x8090ed4"])
    need(u(after, 0x911FC) == u(after, 0x913CC) == 0xE3A02004, "steady and exiting menus draw four presentations")
    sequence(after, 0x91258, ["add r3, r3, #0x50", "subs r2, r2, #1", "bgt #0x8091200"])
    sequence(after, 0x9141C, ["add r1, r1, #0x50", "add r0, r0, #1", "subs r2, r2, #1", "bgt #0x80913d4"])
    need(u(after, 0x90C70) == BASE + 0x90C7C and u(after, 0x90C74) == BASE + 0x914E4, "two title task callbacks")
    need([at for at, target in calls(after, 0x90BF4, 0x90C70) if target == 0x11AC4] == [0x90C18, 0x90C54], "exactly two title task creations")
    need(u(after, 0x90E34) == BASE + 0x90E58 and u(after, 0x90E18) == BASE + 0x91598, "prompt replaces itself with menu/timeout callback")
    need(u(after, 0x159B0) == 0xE12FFF1E and struct.unpack("<3I", cut(after, 0x15B94, 12)) == (BASE + 0x908A0, BASE + 0x90BF4, BASE + 0x159B0), "mode3 init/task/common callback table; common is BX LR")
    sequence(after, 0x11DC8, ["push {r2, r5, lr}", "ldr r8, [r5]", "mov lr, pc", "bx r8", "pop {r2, r5, lr}"])
    need(u(after, 0x11DF0) == 0xE595500C, "scheduler advances to next task after one callback invocation")
    need(calls(after, 0x914E4, 0x91578) == [(0x91568, 0x1207C)] and calls(after, 0x1207C, 0x12138) == [(0x120B4, 0x37DB3C), (0x120E8, 0x37DB3C), (0x12114, 0x37DB3C)], "fade only blends palette channels via division")
    need(literal(after, 0x9152C) == 0x05000020 and literal(after, 0x91538) == 0x0201E800 and literal(after, 0x91544) == 0x0201E400, "fade buffers are palette destinations, not OAM")
    need(sha(cut(after, 0x12C58, 0x180)) == "D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685", "actual low-byte tile renderer remains intact")
    # No title-Y clipping precedes these calls: Y200 still contributes parts.
    totals = []
    for language, resource in zip(("en", "ja", "ko", "digicode"), resources):
        counts = [len(frame[0]) for frame in resource["frames"]]
        prompt, menu = counts[0], sum(counts[1:])
        need(max(prompt, menu) <= 127 and max(prompt, menu) * 32 <= 4096, "complete active OAM and per-part tile staging capacity")
        totals.append(dict(language=language, counts=counts, prompt_max=prompt, menu_max=menu,
                           maximum=max(prompt, menu), maximum_tile_bytes=max(prompt, menu) * 32))
    need([row["maximum"] for row in totals] == [92, 88, 88, 111], "exact independently reconstructed title population")
    # Existing native loader runs before priority-zero mode task creation and
    # before the first scheduler invocation, so the tag is never uninitialized.
    need(branch(after, 0x29C) == 0x420 and branch(after, 0x2B4) == 0x11D78 and branch(after, 0x424) == 0x158D4 and branch(after, 0x43C) == 0x11AC4, "record init precedes mode task and scheduler")
    need(branch(after, 0x15940) == 0x1F894 and literal(after, 0x15948) == 0x03001120, "native read/reset path initializes existing record")
    need(branch(after, 0x1F8A8) == 0x1FBD0 and literal(after, 0x1F8B0) == literal(after, 0x1F8E8) == 0x03001120, "existing load/check/default record paths")
    need(cut(after, 0x1F9D4, 16) == b"DIMPS Ver0.72   " and u(after, 0x1F904) == 0xE3A02010, "legacy defaults write entire sixteen-byte header, including tag20")
    return dict(callbacks=rows, object_base=0x03002A78, stride=0x50, coordinates=list(zip(coords[::2], coords[1::2])),
        budgets=totals, original_title_tasks=2, mode_controller_tasks=1, new_tasks=0,
        phase_exclusion="One title callback per scheduler visit; callback replacements take effect next visit. Prompt and menu draw sites do not run together. Fade/controller emit no OAM.",
        initialization="Boot029C ->0420 ->0158D4 ->01F894 initializes03001120 before mode task creation043C and scheduler02B4. Existing native valid/default record path retained.")


def inverse(before, after):
    restored = bytearray(after)
    for start, end in WRITES:
        restored[start:end] = before[start:end]
    need(restored == before, "all writes confined to the five independent spans; complete inverse")
    for start, end in ALLOCATIONS:
        need(cut(before, start, end - start) == b"\xff" * (end - start), "allocation originally empty")
        need(cut(before, start - 16, 16) == cut(after, start - 16, 16) and cut(before, end, 16) == cut(after, end, 16), "allocation adjacent bytes preserved")


def reservation(data):
    spans = ALLOCATIONS
    def owned(raw):
        return any(start <= raw < end for start, end in spans)
    encoded = []
    for alignment in range(4):
        end = len(data) - ((len(data) - alignment) % 4)
        for index, (word,) in enumerate(struct.iter_unpack("<I", memoryview(data)[alignment:end])):
            if BASE + spans[0][0] <= word < BASE + spans[-1][1] and owned(word - BASE):
                encoded.append(alignment + index * 4)
    need(not encoded, "no existing encoded pointer into new allocation at any byte alignment")
    arm, thumb = [], []
    for at, (word,) in enumerate(struct.iter_unpack("<I", data)):
        at *= 4
        if word == 0xFFFFFFFF:
            continue
        target = None
        if word & 0x0E000000 == 0x0A000000:
            delta = word & 0xFFFFFF; delta -= 0x1000000 if delta & 0x800000 else 0
            target = at + 8 + 4 * delta
        elif word & 0x0F7F0000 == 0x051F0000:
            target = at + 8 + (1 if word & 0x800000 else -1) * (word & 0xFFF)
        elif word & 0x0E1F0000 == 0x020F0000 and (word >> 21) & 15 in (2, 4):
            rotate = ((word >> 8) & 15) * 2
            value = word & 255
            immediate = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF if rotate else value
            target = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
        if target is not None and owned(target):
            arm.append((at, target))
    for index, (word,) in enumerate(struct.iter_unpack("<H", data)):
        at = index * 2
        if word & 0xF800 == 0x4800 or word & 0xF800 == 0xA000:
            target = ((at + 4) & ~3) + (word & 255) * 4
            if owned(target):
                thumb.append((at, target))
    need(not arm and not thumb, "no existing ARM branch/literal/ADR or Thumb PC-relative/ADR into allocation")
    return dict(encoded_pointer_alignments=4, arm_branch_literal_adr_hits=arm, thumb_literal_adr_hits=thumb,
                allocations=[list(s) for s in spans], unused_before=True)


def negative_cases(before, after, source, retail, korean, digicode, renderer):
    rejected = []
    def reject(label, action):
        try:
            action()
        except (ValueError, KeyError, IndexError, struct.error):
            rejected.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    def altered(at, mask=1):
        data = bytearray(after); data[at] ^= mask; return data
    for offset in range(0, 68, 4):
        reject(f"helper word {offset // 4}", lambda offset=offset: verify_helper(before, altered(HELPER + offset)))
    reject("BL would overwrite live LR", lambda: verify_helper(before, altered(HOOK + 3, 1)))
    reject("wrong hook target", lambda: verify_helper(before, altered(HOOK)))
    resources = verify_resources(after, source, retail, korean, digicode)
    for lang, resource in enumerate(resources[1:], 1):
        p0 = ALLOCATIONS[lang - 1][0]
        for offset in (0, 4, 8, 10, 12, 14, 16, 20):
            reject(f"language{lang} header/table {offset}", lambda at=p0 + offset: verify_resources(altered(at), source, retail, korean, digicode))
        for event, part_start in enumerate(resource["part_positions"]):
            for field in (0, 2, 3):
                reject(f"language{lang} event{event} tile/y/x {field}", lambda at=part_start + field: verify_resources(altered(at), source, retail, korean, digicode))
        # Mutate an actually visible source tile, not a known-unused byte.
        flags = resource["frames"][0][0][0][0]
        at = resource["atlas_start"] + (flags & 255) * 32
        reject(f"language{lang} actual atlas pixel", lambda at=at: verify_resources(altered(at), source, retail, korean, digicode))
    for at, label in ((P1 + 8, "native P1"), (P2 + 6, "native palette"), (0x90B66, "offscreen D-ARK coordinate"),
                      (0x12C68, "renderer cap"), (0x633400, "frozen Options code"), (0x629350, "recovery layer")):
        reject(label, lambda at=at: inverse(before, altered(at)))
    for start, end in ALLOCATIONS:
        reject(f"before allocation guard {start:X}", lambda at=start - 1: inverse(before, altered(at)))
        reject(f"after allocation guard {end:X}", lambda at=end: inverse(before, altered(at)))
    for text in ("オプション", "ょ", "っ", "漢字", "!", "-", "1"):
        reject("strict unapproved input " + text, lambda text=text: renderer(text))
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "wsc10", "wsc15", "font", "license", "manifest", "output"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--digicode-font", type=Path, default=ROOT / "build/digicode-glyphs-20261023/font-8x16.json")
    args = parser.parse_args()
    before, after, gba, old, new, font, license_bytes = (getattr(args, key).read_bytes() for key in ("before", "after", "gba", "wsc10", "wsc15", "font", "license"))
    for label, data, digest in (("before", before, BEFORE), ("after", after, AFTER), ("gba", gba, GBA), ("wsc10", old, OLD), ("wsc15", new, NEW), ("font", font, FONT), ("license", license_bytes, LICENSE)):
        need(sha(data) == digest, "exact independent input identity " + label)
    need(len(before) == len(after) == len(new) == 0x800000 and len(gba) == len(old) == 0x400000, "fixed ROM extents")
    source, retail, source_report = source_contract(gba, old, new)
    korean, digicode, renderer, text_report = expected_images(source, retail, font, args.digicode_font.read_bytes(), (ROOT / "localization/digicode-reference.json").read_bytes())
    resources = verify_resources(after, source, retail, korean, digicode)
    helper_report = verify_helper(before, after)
    native_report = population(after, gba, resources)
    inverse(before, after)
    allocation_report = reservation(before)
    negatives = negative_cases(before, after, source, retail, korean, digicode, renderer)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    need(manifest["input_sha256"] == BEFORE and manifest["output_sha256"] == AFTER, "manifest identities agree with independent inputs")
    need([(row["raw"], row["raw"] + row["bytes"]) for row in manifest["expected_writes"]] == list(WRITES), "manifest five spans agree with independent contract")
    for row, (start, end) in zip(manifest["expected_writes"], WRITES):
        need(row["before_sha256"] == sha(cut(before, start, end - start)) and row["after_sha256"] == sha(cut(after, start, end - start)), "manifest span digests")
    report = dict(status="PASS", kind="independent-five-event-title-language", input_sha256=BEFORE, output_sha256=AFTER,
        inputs=dict(gba=GBA, wsc10=OLD, wsc15=NEW, bdf=FONT, font_license=LICENSE, digicode_json=DG_JSON, digicode_rows=DG_ROWS),
        source=source_report, text=text_report, helper=helper_report, native_population=native_report,
        allocation=allocation_report, exact_writes=[dict(start=a, end=b, bytes=b-a, before_sha256=sha(before[a:b]), after_sha256=sha(after[a:b])) for a, b in WRITES],
        declared_bytes=sum(b-a for a,b in WRITES), changed_bytes=sum(a != b for a,b in zip(before, after)), full_inverse=True,
        negative_count=len(negatives), negative_cases=negatives,
        limits=["Only the five existing native title events; later Ver1.5 entries and whole-game localization remain open.",
                "Digicode is the reviewed bounded pixel approximation; no external SVG/font adoption or formal font certification.",
                "Static verification does not execute the ROM or establish runtime/save persistence; separate root-owned captures cover those."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", report_sha256=sha(args.output.read_bytes()), negatives=len(negatives), maximum_oam=[92,88,88,111])))


if __name__ == "__main__":
    main()
