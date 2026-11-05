#!/usr/bin/env python3
"""Independently check the bounded four-language result-label artifact.

No producer/analyzer imports, target execution or save access. Expected text
comes from commercial source pixels and independently reviewed native artwork.
All input paths are explicit or pinned documented local development assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

BASE = 0x08000000
P0, P1, P2 = 0xB8210, 0xB9004, 0xB9144
JA, KO, DG, CODE = 0x651AE0, 0x6DA640, 0x7DFC20, 0x652FA0
GETTER = 0x633400
ALLOCATIONS = ((JA, JA+5280), (KO, KO+5272), (DG, DG+5276), (CODE, CODE+52))
HOOKS = (0x89988, 0x899EC, 0x89BFC, 0x89C60, 0x89D9C, 0x89F34)
OLD_WORDS = (0xEBFE2395, 0xEBFE237C, 0xEBFE22F8, 0xEBFE22DF, 0xEBFE2290, 0xEBFE222A)
P0_ALIASES = (0x8A388, 0x8A394, 0x8A3C8, 0x8A3D4, 0x8A3E8, 0x8A400, 0xBBA64)
TEXT_LAYOUTS = (0, 1, 14)
COUNTS = ((35, 20, 28), (30, 20, 28), (30, 20, 26), (30, 20, 27))
PINS = dict(
    before="494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6",
    after="A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F",
    gba="996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    old="58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    new="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
    catalog="9A3E279DDB68AF381818D191132A48DF351BCBA9D21938D7AD51A4B62E4E80F7",
)
GETTER_SHA = "5F72868A07F73A7FC2892A38BB9902BB8986B2FFB9460F454F8A41E4AC7FCFD7"
WRITES = tuple(sorted((*ALLOCATIONS, *((at, at + 4) for at in HOOKS))))


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded input read")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def ptr(data, at, size=1):
    address = u(data, at) - BASE
    cut(data, address, size)
    return address


def literal(data, at, register=8):
    word = u(data, at)
    need(word & 0x0F7FF000 == 0x051F0000 | register << 12, "actual ARM PC-relative load")
    return u(data, at + 8 + (1 if word & 0x800000 else -1) * (word & 4095))


def target(data, at, link=None):
    word = u(data, at)
    need(word & 0xFE000000 == 0xEA000000, "unconditional ARM B/BL")
    if link is not None:
        need(bool(word & 0x1000000) == link, "correct B versus BL contract")
    delta = word & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return at + 8 + delta * 4


def calls(data, lo, hi, destination=None):
    result = []
    for at in range(lo, hi, 4):
        if u(data, at) & 0xFF000000 == 0xEB000000:
            to = target(data, at, True)
            if destination is None or destination == to:
                result.append((at, to))
    return result


def sequence(data, at, expected):
    decoded = list(Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(cut(data, at, 4 * len(expected)), BASE + at))
    need([i.mnemonic + " " + i.op_str for i in decoded] == expected, f"placed ARM sequence {at:X}")


def digest_pixels(pixels):
    return sha(b"".join(struct.pack("<hhB", x, y, pixels[x, y]) for x, y in sorted(pixels)))


def bounds(pixels):
    need(bool(pixels), "nonempty image")
    return [min(x for x, y in pixels), min(y for x, y in pixels),
            max(x for x, y in pixels), max(y for x, y in pixels)]


def packed(planar):
    need(len(planar) % 32 == 0, "complete source tile rows")
    result = bytearray()
    for at in range(0, len(planar), 4):
        row = [sum(((planar[at + plane] >> (7 - x)) & 1) << plane for plane in range(4)) for x in range(8)]
        result.extend(row[x] | row[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(result)


def compose(parts, atlas):
    output = {}
    for flags, top, left in parts:
        need(flags & 0x3F00 == 0x400, "complete result part uses only the native palette bank2 and flip bits")
        tile = flags & 255
        need((tile + 1) * 32 <= len(atlas), "native low-byte tile index is owned")
        for y in range(8):
            sy = 7 - y if flags & 0x8000 else y
            for x in range(8):
                sx = 7 - x if flags & 0x4000 else x
                value = atlas[tile * 32 + sy * 4 + sx // 2] >> (4 * (sx & 1)) & 15
                if value:
                    # Earlier OAM entries have priority; do not erase hidden
                    # source pixels by reversing the actual composition order.
                    output.setdefault((left + x, top + y), value)
    return output


def native(data, p0, extent=None):
    table, descriptor = ptr(data, p0), ptr(data, p0 + 4)
    size, start = u(data, descriptor), ptr(data, descriptor + 4)
    need(size % 32 == 0 and 91 * 32 <= size <= 256 * 32, "complete bounded result atlas")
    need(struct.unpack("<4H", cut(data, p0 + 8, 8)) == (5, size // 32 - 1, size - 32, 8), "all native P0 header fields")
    need(table == p0 + 16, "fifteen-layout table immediately follows P0")
    atlas = cut(data, start, size)
    layouts, addresses, frames = [], [], []
    cursor = table + 15 * 8
    for i in range(15):
        count, address = u(data, table + i * 8), ptr(data, table + i * 8 + 4)
        need(0 < count <= 127 and address == cursor, "complete contiguous result part arrays")
        parts = [struct.unpack("<Hbb", cut(data, address + j * 4, 4)) for j in range(count)]
        layouts.append(parts); addresses.append(address); frames.append(compose(parts, atlas))
        cursor += count * 4
    need(descriptor == cursor and start == descriptor + 8, "no gaps or hidden descriptors in result resource")
    if extent is not None:
        need((p0, start + size) == extent, "entire resource exactly owns its allocation")
    return dict(p0=p0, layouts=layouts, atlas=atlas, atlas_start=start, descriptor=descriptor,
                part_addresses=addresses, frames=frames, end=start + size)


def banked(data, bank, segment, offset=0):
    physical = 16 * segment + offset
    need(0x20000 <= physical < 0x30000, "explicit source C2 window")
    result = (bank & (len(data) // 65536 - 1)) * 65536 + physical - 0x20000
    cut(data, result, 1)
    return result


def source_resource(data, p0, count):
    need(u(data, p0) == 16 and h(data, p0 + 18) == 16 + count * 4, "source layout extent")
    descriptor = banked(data, h(data, p0 + 6), h(data, p0 + 4))
    size, off, seg, bank = struct.unpack("<4H", cut(data, descriptor, 8))
    start = banked(data, bank, seg, off)
    atlas = packed(cut(data, start, size))
    layouts = []
    for i in range(count):
        number, offset = struct.unpack("<2H", cut(data, p0 + 16 + i * 4, 4))
        need(0 < number <= 127, "source complete part count")
        layouts.append([struct.unpack("<Hbb", cut(data, p0 + offset + k * 4, 4)) for k in range(number)])
    return dict(p0=p0, layouts=layouts, atlas=atlas, descriptor=descriptor, atlas_start=start,
                frames=[compose(parts, atlas) for parts in layouts])


def source_contract(gba, old, new):
    need(cut(old, 0x3B6030, 11) == bytes.fromhex("33c0e4cd24013d00007533"), "old actual language input branch")
    need(cut(new, 0x777465, 9) == bytes.fromhex("33c033c03d00007533"), "new actual zero-Japanese branch")
    for at, expected in ((0x777479, 0x3D7EB0), (0x777482, 0x3CB870), (0x77748B, 0x3D29E0)):
        need([new[at + d] for d in (0, 3, 6)] == [0x68] * 3, "source far resource argument pushes")
        bank, segment, offset = (h(new, at + d) for d in (1, 4, 7))
        need(banked(new, bank, segment, offset) == expected, "actual Japanese result constructor binding")
    need(cut(new, 0x777496, 5) == bytes.fromhex("9af423ff4f"), "actual source presentation constructor")
    variants = ((old, 0x2AF360, 0x2B3580, 0x2B5F90, 15),
                (old, 0x2AF5C0, 0x2B3660, 0x2B6080, 15),
                (new, 0x3CB870, 0x3D29E0, 0x3D7EB0, 16),
                (new, 0x3CBB20, 0x3D2AE0, 0x3D7FA0, 16))
    resources, metadata = [], []
    need(ptr(gba, P1) == P1 + 8 and u(gba, P1 + 4) == 0, "native four-event P1")
    for data, p0, p1, p2, count in variants:
        resources.append(source_resource(data, p0, count))
        events = 4 if count == 15 else 5
        need(u(data, p1) == 4 and h(data, p1 + 6) == 4 + events * 8, "source event table extent")
        colors = bytearray(cut(data, p2, 6))
        for value in struct.unpack("<16H", cut(data, p2 + 6, 32)):
            channels = [(value >> bit) & 15 for bit in (8, 4, 0)]
            colors.extend(struct.pack("<H", sum((2 * v + bool(v)) << (5 * j) for j, v in enumerate(channels))))
        need(bytes(colors) + bytes(2) == cut(gba, P2, 40), "every source palette equals retained native P2")
        differences = []
        for event in range(4):
            n, commands, meta, tail = struct.unpack("<4H", cut(data, p1 + 4 + event * 8, 8))
            at = P1 + 8 + event * 16
            need(n == u(gba, at) == (12 if event == 2 else 1) and tail == u(gba, at + 12) == 0, "native/source complete command population")
            need(cut(data, p1 + meta, 8) == cut(gba, ptr(gba, at + 8), 8), "source A metadata retained")
            for frame in range(n):
                source = bytearray(cut(data, p1 + commands + frame * 12, 12))
                native_cmd = cut(gba, ptr(gba, at + 4) + frame * 16, 16)
                if event == 2 and (1 <= frame <= 10 or p1 == 0x2B3660):
                    need(h(source, 6) == 0 and h(native_cmd, 6) == 1, "intentional native digit control flag")
                    struct.pack_into("<H", source, 6, 1); differences.append(frame)
                need(bytes(source) + bytes(4) == native_cmd, "every other source command field and native widening")
        metadata.append(dict(p0=p0, p1=p1, p2=p2, layouts=count, events=events,
                             native_digit_flags_preserved_for_frames=differences))
    ja = resources[2]
    need((ja["descriptor"], ja["atlas_start"], len(ja["atlas"])) == (0x3D8E80, 0x3A0000, 0xCC0), "full Japanese source atlas")
    need([len(p) for p in ja["layouts"]] == [38, 20, 4, 2, 4, 4, 5, 4, 4, 3, 4, 4, 4, 4, 28, 17], "all source parts including excluded LOSE")
    need(resources[0]["frames"] == ja["frames"][:15], "old/new Japanese complete visible pixel lineage")
    retail = native(gba, P0)
    need(retail["frames"][2:14] == ja["frames"][2:14], "all twelve native digit/symbol pixel maps match source")
    for index, expected in ((0, "8ECA7847B508136FCB6CF9A6B3613778E95CD6932995D6810117D4A6CB622499"),
                            (1, "D47B0B69E6AA2E5FBE3AA8228EA6F3F272DBF90400BFB55C9FE79A68EE366F22"),
                            (14, "8918B8FA7A18880FFC280922271B493BCD699B776C74874E826CEFDE4B316DC3")):
        need(digest_pixels(ja["frames"][index]) == expected, "complete reviewed Japanese text image")
    punctuation = {point: color for point, color in ja["frames"][14].items() if 42 <= point[0] <= 50}
    need(not any(x == 41 for x, y in ja["frames"][14]) and bounds(punctuation) == [42, -8, 50, 6] and len(punctuation) == 65,
         "isolated full native exclamation after blank column")
    need(digest_pixels(punctuation) == "26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8", "all punctuation colors and edge pixels")
    return ja, retail, punctuation, dict(variants=metadata, japanese15_pixels_equal_japanese10=True,
        japanese_source_last_chance_parts=[len(resources[0]["layouts"][14]), len(ja["layouts"][14])],
        source_only_event4_lose_excluded=True, native_digit_commands_retained=True)


def check_policy(config, catalog):
    need(config.get("schema") == 2 and config.get("status") == "approved-native-result-component", "approved native artwork catalog")
    need(config['approved_art_sha256']=='875700A7C5C0281E46651AF09E31E30BB846D1C44675172391D323D3450B03B3','reviewed native artwork provenance')
    need(config['last_chance_part_counts']==[28,26,27],'approved last-chance populations')
    need(config['shared_headings']=='Exact Japanese-source WIN/DRAW for Japanese, Korean and Digicode; English retains native WINS/DRAW.','source WIN/DRAW reuse policy')
    row=config['last_chance']
    need(tuple(row[k] for k in ('japanese','korean','digicode_source_reading','digicode_render_reading'))==
         ('ラストチャンス！','마지막 기회!','ラストチャンス','ラストチヤンス'),'complete wording and exact local small-YA rendering policy')
    need(config['excluded_source_event']['event']==4 and config['excluded_source_event']['text']=='LOSE','source-only LOSE remains excluded')
    identities=[g['id'] for g in catalog['glyphs']+catalog['latin_glyphs']]
    need(len(identities)==len(set(identities))==98,'complete strict catalog identities')
    lookup={g[k]:g['id'] for g in catalog['glyphs'] for k in ('hiragana','katakana')}
    need('ャ' not in lookup and lookup['ヤ']=='jp-3084','small YA remains explicit local alias')
    need([lookup[c] for c in row['digicode_render_reading']]==['jp-3089','jp-3059','jp-3068','jp-3061','jp-3084','jp-3093','jp-3059'],'all seven approved glyph identities/order')


def expected_images(ja, punctuation, art):
    output={language:{i:ja['frames'][i] for i in TEXT_LAYOUTS} for language in ('ja','ko','digicode')}
    for language,key,pin,parts in (
        ('ko','korean','124F00001D3C12A36C3336049D28BAFEE6EC3321C975ADAE0D072C15D9946917',26),
        ('digicode','digicode','4F9B02D9BC03779DCB14B62B0D0EB0F5755BC0DD48B3006669E5631F4BAAC924',27)):
        frame=art[key];pixels={(x,y):c for x,y,c in frame['pixels']}
        need(len(pixels)==len(frame['pixels']) and digest_pixels(pixels)==pin,'independently approved native palette pixels '+language)
        need(bounds(pixels)==[-51,-8,50,7] and set(pixels.values())<={6,7,8,9,10,12},'native102x16 color population')
        need({p:c for p,c in pixels.items() if p[0]>=42}==punctuation and not any(x in (40,41) for x,y in pixels),'exact65source punctuation and separation')
        atlas=b''.join(bytes.fromhex(tile) for tile in frame['tiles_4bpp_hex'])
        need(len(frame['parts'])==parts and compose(frame['parts'],atlas)==pixels,'approved native parts and4bpp inverse')
        need(frame['palette_pixel_sha256']==pin,'art metadata pixel digest truthful')
        output[language][14]=pixels
    for frame,index in zip(art['japanese_common'],(0,1)):
        pixels={(x,y):c for x,y,c in frame['pixels']}
        need(pixels==ja['frames'][index],'reused WIN/DRAW exactly Japanese source')
    return output


def grid_reference(pixels, origin):
    ox, oy = origin
    cells = sorted({((x - ox) // 8 * 8 + ox, (y - oy) // 8 * 8 + oy) for x, y in pixels}, key=lambda p: (p[1], p[0]))
    result = []
    for left, top in cells:
        tile = bytes(pixels.get((left + x, top + y), 0) | pixels.get((left + x + 1, top + y), 0) << 4
                     for y in range(8) for x in range(0, 8, 2))
        need(any(tile), "no invented transparent grid part")
        result.append((0x400, top, left, tile))
    return result


def verify_resources(after, retail, ja, expected):
    resources = [native(after, P0)]
    need(resources[0] == retail, "complete original English resource unchanged")
    reports = []
    for language, extent, expected_counts in zip(("ja", "ko", "digicode"), ALLOCATIONS[:3], COUNTS[1:]):
        result = native(after, extent[0], extent)
        need(result["layouts"][2:14] == retail["layouts"][2:14], "all twelve native digit arrays byte-identical")
        need(result["atlas"][:91 * 32] == retail["atlas"], "complete91-tile native prefix retained")
        tiles = [retail["atlas"][k:k + 32] for k in range(0, len(retail["atlas"]), 32)]
        known = {tile: i for i, tile in enumerate(tiles)}
        for layout in TEXT_LAYOUTS:
            wanted = expected[language][layout]
            need(result["frames"][layout] == wanted, f"every {language} layout{layout} pixel, color and coordinate")
            if language == "ja" and layout == 14:
                reference = [(flags & 0xFF00, y, x, ja["atlas"][(flags & 255) * 32:((flags & 255) + 1) * 32])
                             for flags, y, x in ja["layouts"][layout]]
            else:
                reference = grid_reference(wanted, (0, 5) if layout == 0 else (0, 0))
            need(len(reference) == len(result["layouts"][layout]), "all canonical nonempty native parts retained")
            for (high, y, x, tile), actual in zip(reference, result["layouts"][layout]):
                if tile not in known:
                    known[tile] = len(tiles); tiles.append(tile)
                need(actual == (high | known[tile], y, x), "actual per-part tile contents, palette/flip bits and geometry")
        need(result["atlas"] == b"".join(tiles), "entire atlas contains only exact retained/needed canonical tiles")
        need(tuple(len(result["layouts"][i]) for i in TEXT_LAYOUTS) == expected_counts, "exact localized label part counts")
        need(all(len(a) <= len(b) for a, b in zip(result["layouts"], retail["layouts"])), "pointwise all15 layouts do not increase OAM")
        reports.append(dict(language=language, p0=extent[0], extent=list(extent), tiles=len(tiles),
            layout_parts=[len(p) for p in result["layouts"]], original_digits_and91tiles_exact=True,
            text=[dict(layout=i, parts=len(result["layouts"][i]), pixels=len(result["frames"][i]),
                       bounds=bounds(result["frames"][i]), pixel_sha256=digest_pixels(result["frames"][i])) for i in TEXT_LAYOUTS]))
        resources.append(result)
    need([len(r["atlas"]) // 32 for r in resources] == [91, 145, 145, 145], "complete four-resource atlas population")
    return resources, reports


def abi(before, after):
    need(sha(cut(before, GETTER, 28)) == GETTER_SHA and cut(before, GETTER, 28) == cut(after, GETTER, 28), "unchanged shared tag getter")
    sequence(after, GETTER, ["ldr r0, [pc, #0x10]", "ldrb r0, [r0]", "sub r0, r0, #0xa0", "cmp r0, #3", "movhi r0, #0", "bx lr"])
    need(u(after, GETTER + 24) == 0x0300112F, "shared initialized language tag owner")
    sequence(after, CODE, ["push {r0, r1, r2, lr}", "mrs r1, apsr", "bl #0x8633400", "add r2, pc, #0x10",
                          "ldr r0, [r2, r0, lsl #2]", "str r0, [sp, #0x34]", "msr apsr_nzcvq, r1",
                          "pop {r0, r1, r2, lr}", "b #0x80127e4"])
    table = struct.unpack("<4I", cut(after, CODE + 36, 16))
    for delta,word in ((0,0xE92D4007),(4,0xE10F1000),(12,0xE28F2010),(16,0xE7920100),(20,0xE58D0034),(24,0xE128F001),(28,0xE8BD4007)):
        need(u(after,CODE+delta)==word,'exact ARM7 helper instruction including reserved bits')
    need(table == tuple(BASE + p for p in (P0, JA, KO, DG)), "exact four-way P0 table")
    need(u(after, CODE) == 0xE92D4007 and u(after, CODE + 28) == 0xE8BD4007, "only four native scratch-stack words")
    need(target(after, CODE + 8, True) == GETTER and target(after, CODE + 32, False) == 0x127E4, "getter link followed by native tail-call")
    sequence(after, 0x127E4, ["push {r0, r3, r4, r5}", "ldr r5, [sp, #0x48]", "ldr r0, [sp, #0x40]", "str r0, [r5, #0x44]",
                            "ldr r0, [sp, #0x34]", "str r0, [r5, #0x48]"])
    sequence(after, 0x12854, ["pop {r0, r3, r4, r5}", "bx lr"])
    for at, old in zip(HOOKS, OLD_WORDS):
        need(u(before, at) == old and target(before, at, True) == 0x127E4 and target(after, at, True) == CODE, "all six actual BL redirects")
        need(u(after, at + 4) == 0xE28DD03C, "original caller discards fifteen argument slots")
        need(literal(after, at - 0x40) == BASE + P0, "caller still supplies its original P0 argument")
    need(target(after, 0xBB0F4, True) == 0x127E4, "mode12 init call retains direct native target")
    count = 0
    for tag in range(256):
        unsigned = (tag - 0xA0) & 0xFFFFFFFF
        index = unsigned if unsigned <= 3 else 0
        need(index == (tag - 0xA0 if 0xA0 <= tag <= 0xA3 else 0), "all invalid tags select English")
        for flag_bits in range(32):
            for control in (0x10, 0xD3, 0x1F):
                cpsr = flag_bits << 27 | control
                # A static transfer proof over arbitrary register/argument
                # symbols. This is not target execution or a CPU emulator.
                regs = [("arbitrary", n) for n in range(15)]
                initial = list(regs); stack = list(range(15)); initial_args = list(stack)
                saved = [regs[i] for i in (0, 1, 2, 14)]
                regs[1] = cpsr; regs[14] = BASE + CODE + 12
                regs[0] = index
                compared = (cpsr & 0x0FFFFFFF) | (((unsigned - 3) & 0x80000000)) | (int(unsigned == 3) << 30) | (int(unsigned >= 3) << 29)
                regs[2] = BASE + CODE + 36; regs[0] = table[index]
                need(-16 + 0x34 == 0x24, "wrapper stack P0 offset matches native entry argument")
                stack[9] = regs[0]
                restored_flags = (compared & 0x00FFFFFF) | (regs[1] & 0xFF000000)
                for i, value in zip((0, 1, 2, 14), saved):
                    regs[i] = value
                need(regs == initial and restored_flags == cpsr and stack[9] == table[index]
                     and all(stack[j] == initial_args[j] for j in range(15) if j != 9), "registers/LR/CPSR and all other arguments preserved")
                count += 1
    return dict(helper=CODE, bytes=52, cases=count, tag_values=256, status_patterns=32, control_patterns=3,
        stack_bytes=16, entry_argument_offset=0x24, wrapper_argument_offset=0x34,
        preserved="r0-r12, original BL return LR, SP and CPSR at native tail entry; only P0 argument changes",
        stack_ownership="Exactly the sixteen descending bytes already used by the native constructor push. Getter has no stack use; wrapper pops before tail B, so existing minimum SP is unchanged.",
        p0_table=list(table), mode12_direct_native=True)


def inverse(before, after):
    need(len(before) == len(after) == 0x800000, "fixed full ROM extent")
    restored = bytearray(after)
    for start, end in WRITES:
        restored[start:end] = before[start:end]
    need(bytes(restored) == before, "complete ten-span inverse; no out-of-scope byte changes")
    need(sum(end - start for start, end in WRITES) == 15904, "declared write count")
    need(cut(before, P0, 0xF5C) == cut(after, P0, 0xF5C), "entire original result resource/P1/palette family unchanged")
    need(cut(before, 0xBB0B4, 0xA0) == cut(after, 0xBB0B4, 0xA0) and u(after, 0xBBA64) == BASE + P0, "separate mode12 body and original P0 alias unchanged")


def ownership(before):
    for lo, hi in ALLOCATIONS:
        need(cut(before, lo, hi - lo) == b"\xff" * (hi - lo), "complete allocation is unused FF")
    def inside(value):
        return any(lo <= value < hi for lo, hi in ALLOCATIONS)
    for alignment in range(4):
        stop = len(before) - ((len(before) - alignment) % 4)
        for _, (value,) in enumerate(struct.iter_unpack("<I", memoryview(before)[alignment:stop])):
            need(not (value >> 24 in (8, 10, 12) and inside(value & 0x1FFFFFF)), "no all-alignment interior pointer in any ROM mirror")
    for index, (word,) in enumerate(struct.iter_unpack("<I", before)):
        if word == 0xFFFFFFFF:
            continue
        at, destination = index * 4, None
        if word & 0x0E000000 == 0x0A000000:
            d = word & 0xFFFFFF; d -= 0x1000000 if d & 0x800000 else 0
            destination = at + 8 + d * 4
        elif word & 0x0F7F0000 in (0x051F0000,0x055F0000):
            destination = at + 8 + (1 if word & 0x800000 else -1) * (word & 4095)
        elif word & 0x0E1F0000 == 0x020F0000 and (word >> 21) & 15 in (2, 4):
            rotate, value = ((word >> 8) & 15) * 2, word & 255
            immediate = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF if rotate else value
            destination = at + 8 + (immediate if (word >> 21) & 15 == 4 else -immediate)
        need(destination is None or not inside(destination), "no ARM branch/literal/ADR owner")
    for index, (word,) in enumerate(struct.iter_unpack("<H", before)):
        at, destination = index * 2, None
        if word & 0xF800 in (0x4800, 0xA000):
            destination = ((at + 4) & ~3) + (word & 255) * 4
        elif word & 0xF800 == 0xE000:
            d = word & 2047; d -= 2048 if d & 1024 else 0
            destination = at + 4 + d * 2
        elif word & 0xF000 == 0xD000 and word & 0x0F00 < 0x0E00:
            d = word & 255; d -= 256 if d & 128 else 0
            destination = at + 4 + d * 2
        elif word & 0xF800 == 0xF000 and at + 4 <= len(before):
            low = h(before, at + 2)
            if low & 0xF800 in (0xF800,0xE800):
                d = word & 2047; d -= 2048 if d & 1024 else 0
                destination = at + 4 + (d << 12) + ((low & 2047) << 1)
                if low & 0xF800 == 0xE800:destination &= ~3
        need(destination is None or not inside(destination), "no Thumb branch/literal/ADR/BL owner")


def original_aliases(data):
    hits = []
    for alignment in range(4):
        stop = len(data) - ((len(data) - alignment) % 4)
        for n, (value,) in enumerate(struct.iter_unpack("<I", memoryview(data)[alignment:stop])):
            if value >> 24 in (8, 10, 12) and value & 0x1FFFFFF == P0:
                hits.append((alignment + n * 4, value))
    return sorted(hits)


def event(data, p0, p1, index):
    at = ptr(data, p1) + index * 16
    n, address = u(data, at), ptr(data, at + 4)
    need(0 < n <= 255, "complete selected event")
    result = []
    for j in range(n):
        command = address + j * 16
        duration, flags, layout = data[command], h(data, command + 6), h(data, command + 2)
        need(duration < 128, "native signed counter input domain")
        row = ptr(data, p0) + layout * 8
        parts, start = u(data, row), ptr(data, row + 4)
        need(0 < parts <= 127, "selected P0 part count")
        cut(data, start, parts * 4)
        result.append((duration, flags, parts))
    return tuple(result)


def next_pose(events, pair, state):
    phase, frame, remaining, flags = state
    frames = events[pair[phase]]
    if not flags & 0x2000:
        signed = (remaining - 256 if remaining & 128 else remaining) - 1
        remaining = signed & 255
        if signed < 0:
            frame += 1
            if frame == len(frames):
                if flags & 1:
                    frame = 0
                else:
                    frame -= 1; flags |= 0x2000
            if not flags & 0x2000:
                duration, new_flags, _ = frames[frame]
                remaining = (remaining + duration) & 255
                flags = (flags & 0x101) | new_flags
    if phase == 0 and flags & 0x2000:
        phase, frame = 1, 0
        remaining, flags, _ = events[pair[1]][0]
    return phase, frame, remaining, flags


def population(after, gba, source, resources):
    # Actual native producer/callback and lifecycle bytes establish the
    # population; the only six constructor changes were independently checked.
    original_constructor = bytearray(cut(after, 0x897AC, 0x8A354 - 0x897AC))
    for at, word in zip(HOOKS, OLD_WORDS):
        struct.pack_into("<I", original_constructor, at - 0x897AC, word)
    need(bytes(original_constructor) == cut(gba, 0x897AC, len(original_constructor)), "otherwise unchanged retail result constructor")
    dependencies = ((0x893A4, 0x89774), (0x8A4AC, 0x8B334), (0x12874, 0x12C28),
                    (0x117B0, 0x11810), (0x11D70, 0x11E0C), (0x35227C, 0x352374),
                    (0xD1B0C, 0xD1C68), (0x1E8C4, 0x1E9BC), (0x33FE94, 0x33FF5C),
                    (0x83070, 0x830DC), (0x1F51C, 0x1F590), (0x17758, 0x177B0), (0xC9000, 0xC9074),
                    (0x159B4, 0x15B70), (0xD15F0, 0xD1B0C))
    for lo, hi in dependencies:
        need(cut(after, lo, hi - lo) == cut(gba, lo, hi - lo), "complete unchanged callback/scheduler/service dependency")
    need(struct.unpack("<3I", cut(after, 0x15BD0, 12)) == (BASE + 0x893A4, BASE + 0x897AC, BASE + 0x159B0)
         and u(after, 0x159B0) == 0xE12FFF1E, "mode8 binding and empty common callback")
    allocation_calls = calls(after, 0x897AC, 0x8A354, 0x11AC4)
    expected = ((0x1000, 0x8A4AC), (0xF000, 0x8B200), (0x1500, 0x8B024),
                (0x1600, 0x8AC34), (0x1700, 0x8AC34), (0x2000, 0x8A7C0), (0x3000, 0x8A7C0))
    need(len(allocation_calls) == len(expected), "exact seven native result task allocations")
    for (at, _), (priority, callback) in zip(allocation_calls, expected):
        sequence(after, at - 8, [f"mov r8, #{priority:#x}"])
        need(literal(after, at - 20) == BASE + callback, "actual task priority/callback ownership")
    draw_sites = [at for at, _ in calls(after, 0x8A4AC, 0x8B334, 0x12C28)]
    need(draw_sites == [0x8A858, 0x8A930, 0x8AA18, 0x8AAB0, 0x8AC6C, 0x8AC8C, 0x8ACAC,
                       0x8AD70, 0x8AD84, 0x8AD98, 0x8AEF4, 0x8AF24, 0x8AF54, 0x8AF88, 0x8AF9C, 0x8AFB0,
                       0x8B0AC, 0x8B170, 0x8B19C], "all nineteen actual native draw sites")
    need(not calls(after, 0x8A4AC, 0x8B334, 0x11AC4) and not calls(after, 0x8A4AC, 0x8B334, 0x127E4), "callbacks create no additional result task/presentation")
    for at, word in ((0x11DCC, 0xE5958000), (0x11DD4, 0xE12FFF18), (0x11DF0, 0xE595500C),
                     (0x117C8, 0xE3A07000), (0x117CC, 0xE5C87000), (0x8A6A8, 0xE3A01C3F),
                     (0x8A8BC, 0xE3A09030), (0x8A9D0, 0xE3A090DE), (0x12BB8, 0x101)):
        need(u(after, at) == word, "scheduler/text phase/transition/animation control")
    need(literal(after, 0x1F3B0) == BASE + 0x4A80F8 and u(after, 0x1F3B4) == 0xE0881281, "base-only fighter loader ID*32")
    need(cut(after, 0x629480, 64) == cut(source, 0x7771C0, 64), "all15 corrected source pose pairs")
    actors, names = [], []
    for identity in range(15):
        p0, p1 = ptr(after, 0x4A80F8 + identity * 32), ptr(after, 0x4A80F8 + identity * 32 + 4)
        pairs = tuple(tuple(cut(after, table + identity * 2, 2)) for table in (0x629480, 0x6294A0))
        events = {i: event(after, p0, p1, i) for i in {0, 1, 0x51, 0x56, *pairs[0], *pairs[1]}}
        need(all(flags == 0 for pair in pairs for _, flags, _ in events[pair[0]]), "every first pose is finite sequential")
        actors.append((events, pairs))
        name = event(after, 0xB799C, 0xB77EC, identity)
        need(len(name) == 1, "one stable name frame")
        names.append(name[0][2])
    need(names == [16, 22, 16, 16, 20, 14, 16, 14, 14, 16, 14, 16, 16, 16, 16], "all fifteen winner-name populations")
    need(sum(len(events) for events, _ in actors) == 120 and sum(len(v) for e, _ in actors for v in e.values()) == 1252,
         "complete120event1252frame installed pose population")
    trajectories, completion = [], []
    for identity, (events, pairs) in enumerate(actors):
        both = []
        for side, pair in enumerate(pairs):
            state = (0, 0, events[pair[0]][0][0], events[pair[0]][0][1])
            states, seen, outputs = [], {}, []
            while state not in seen:
                need(len(states) < 100000, "complete individual state closure")
                seen[state] = len(states); states.append(state)
                following = next_pose(events, pair, state)
                outputs.append(events[pair[following[0]]][following[1]][2])
                if state[0] == 0 and following[0] == 1:
                    completion.append((identity, side, len(states)))
                state = following
            both.append((outputs, seen[state]))
        trajectories.append(both)
    need(len(completion) == 30 and min(v[2] for v in completion) == 5 and max(v[2] for v in completion) == 140, "all first poses complete before222-countdown")
    total_states, longest, maximum, witness = 0, 0, -1, None
    for winner in range(15):
        for loser in range(15):
            (a, loop_a), (b, loop_b) = trajectories[winner][0], trajectories[loser][1]
            i = j = tick = 0; seen = set()
            while (i, j) not in seen:
                seen.add((i, j))
                value = names[winner] + a[i] + b[j]
                if value > maximum:
                    maximum = value; witness = dict(winner=winner, loser=loser, tick=tick, name=names[winner], winner_parts=a[i], loser_parts=b[j])
                i = i + 1 if i + 1 < len(a) else loop_a
                j = j + 1 if j + 1 < len(b) else loop_b
                tick += 1
            total_states += tick; longest = max(longest, tick)
    need((total_states, longest, maximum) == (389162, 18852, 64), "all225 synchronized finite pose-pair graphs close without cutoff")
    digits = [len(p) for p in resources[0]["layouts"][2:14]]
    scores = [sum(digits[int(ch)] for ch in f"{score:03d}") for score in range(256)]
    need(max(scores) == 14, "entire byte-score decimal domain")
    frozen_digits = max(scores[a] + scores[b] for a in range(256) for b in range(a))
    left = max(parts for events, _ in actors for i in (0, 1, 0x56) for _, _, parts in events[i])
    right = max(parts for events, _ in actors for i in (0, 0x51, 0x56) for _, _, parts in events[i])
    draw_pose = max(parts for events, _ in actors for i in (0, 1) for _, _, parts in events[i])
    any_pose = max(parts for events, _ in actors for rows in events.values() for _, _, parts in rows)
    need((frozen_digits, left, right, draw_pose, any_pose) == (28, 20, 26, 20, 26), "all simultaneous component populations")
    budgets = []
    for language, resource in zip(("en", "ja", "ko", "digicode"), resources):
        win, draw, last = (len(resource["layouts"][i]) for i in TEXT_LAYOUTS)
        bounds_ = dict(prelabel=left + right + 6 * max(digits), normal=win + maximum + frozen_digits,
                       ordinary_draw=draw + last + 2 * draw_pose + frozen_digits,
                       repeated_or_linked_draw=draw + 2 * any_pose + frozen_digits)
        cap = max(bounds_.values())
        need(cap <= 127 and cap * 32 <= 4096, "complete mode8 native OAM/staging capacity")
        budgets.append(dict(language=language, **bounds_, maximum=cap, staging_bytes=cap * 32))
    need([b["maximum"] for b in budgets] == [127, 122, 122, 122], "four exact conservative aggregate bounds")
    return dict(tasks=8, constructor_tasks=7, presentations=10, components=dict(heading=1, name_or_last_chance=1, digits=6, fighters=2),
        draws=draw_sites, callback_dependencies=[dict(start=a, end=b, sha256=sha(after[a:b])) for a, b in dependencies],
        selected_events=120, selected_frames=1252, ids=15, pairs=225, closed_joint_states=total_states,
        longest_trajectory=longest, name_plus_poses_maximum=maximum, witness=witness, budgets=budgets,
        first_pose_completion=completion, score_domain=[0, 255], offscreen_parts_counted=True,
        phase_contract="Native16-step slides precede finalized digits. Priorities1600/1700 finish all three decimal digits before flag1; both fighter tasks then share the48-countdown. Flag2 gates both text objects. Normal poses advance once per traversal. Draw4000 uses0/1;1000 suppresses last-chance. All periodic/held tails are included beyond222 ticks.",
        lifecycle="Native teardown removes the26 battle renderer tasks and service handles. Frame queues reset before result tasks. Result controller waits3F00 completion bits before next mode. Mode/fade/scroll/palette/scanline/BG SCORE services emit no additional OBJ parts.")


def manifest_contract(manifest, before, after, resources):
    need(manifest.get("kind") == "bounded-four-language-result-labels" and manifest.get("input_sha256") == sha(before)
         and manifest.get("output_sha256") == sha(after), "manifest identifies actual independently checked artifacts")
    need(manifest.get("declared_bytes") == 15904 and manifest.get("spans") == 10 and manifest.get("full_inverse") is True, "manifest bounded write scope")
    actual = [(lo, hi - lo, sha(after[lo:hi])) for lo, hi in WRITES]
    need([(r["raw"], r["bytes"], r["sha256"]) for r in manifest["writes"]] == actual, "manifest writes match actual full bytes")
    need([r["p0_raw"] for r in manifest["resources"]] == [P0, JA, KO, DG], "manifest language resource identity")
    need([r["layout_parts"] for r in manifest["resources"]] == [[len(p) for p in resource["layouts"]] for resource in resources], "manifest counts checked against actual decoded arrays")


def negative_cases(before, after, gba, old, new, ja, retail, expected, resources, config, catalog, art):
    rejected = []
    def reject(label, check):
        try:
            check()
        except (ValueError, IndexError, KeyError, TypeError, struct.error):
            rejected.append(label)
        else:
            raise ValueError("negative accepted: " + label)
    def altered(data, at, mask=1):
        result = bytearray(data); result[at] ^= mask
        return result
    for at in (*HOOKS, *(CODE + i for i in range(0, 52, 4)), GETTER, GETTER + 12, GETTER + 24, 0x127F4, 0x12854, 0xBB0F4):
        reject(f"actual ABI word {at:X}", lambda at=at: abi(before, altered(after, at)))
    for resource in resources[1:]:
        raw = resource["p0"]
        for at in (raw, raw + 4, raw + 8, raw + 10, raw + 12, raw + 14, resource["descriptor"], resource["descriptor"] + 4):
            reject(f"resource header/descriptor {at:X}", lambda at=at: verify_resources(altered(after, at), retail, ja, expected))
        for layout in range(15):
            at = resource["part_addresses"][layout]
            for delta in (0, 1, 2, 3):
                reject(f"actual part{layout} field{delta} at{at:X}", lambda at=at, delta=delta: verify_resources(altered(after, at + delta), retail, ja, expected))
        for tile in range(len(resource["atlas"]) // 32):
            at = resource["atlas_start"] + tile * 32
            reject(f"complete atlas tile at{at:X}", lambda at=at: verify_resources(altered(after, at), retail, ja, expected))
    for at in (P0, P1, P2, 0xBBA64, 0x8A858, 0x629480, 0x629700, 0x640000, 0x652F80, 0x652FD4, 0x6DE2F0):
        reject(f"out-of-scope byte {at:X}", lambda at=at: inverse(before, altered(after, at)))
    reject("truncated image", lambda: inverse(before, after[:-1]))
    for at in (0x777465, 0x777482, 0x77748B, 0x777496, 0x3CB870, 0x3CB882, 0x3D29E6, 0x3D7EB6, 0x3D8E80, 0x3A0000 + 36 * 32):
        reject(f"source producer/resource byte {at:X}", lambda at=at: source_contract(gba, old, altered(new, at)))
    for field, value in (("digicode_source_reading", "LAST CHANCE"), ("digicode_render_reading", "ラストチャンス"), ("korean", "마지막")):
        bad = json.loads(json.dumps(config)); bad["last_chance"][field] = value
        reject("unsupported language policy " + field, lambda bad=bad: check_policy(bad, catalog))
    bad=json.loads(json.dumps(catalog));bad['glyphs'][0]['id']='jp-3084'
    reject('duplicate strict catalog identity',lambda:check_policy(config,bad))
    for key in ('korean','digicode'):
        bad=json.loads(json.dumps(art));bad[key]['pixels'][0][2]^=1
        reject('approved palette pixel '+key,lambda bad=bad:expected_images(ja,{p:c for p,c in ja['frames'][14].items() if p[0]>=42},bad))
    # Ownership negatives deliberately target each scanner class at an early
    # offset, so each must reject without relying on a full-ROM hash mismatch.
    for mirror in (8, 10, 12):
        bad = bytearray(before); struct.pack_into("<I", bad, 5, mirror << 24 | JA + 1)
        reject(f"unaligned mirror{mirror:X} interior owner", lambda bad=bad: ownership(bad))
    bad = bytearray(before); struct.pack_into("<I", bad, 0, 0xEA000000 | ((JA - 8) // 4))
    reject("ARM inbound branch", lambda: ownership(bad))
    for opcode, label in ((0xE59F0000, "ARM literal"), (0xE28F0000, "ARM ADR")):
        bad = bytearray(before); struct.pack_into("<I", bad, JA - 12, opcode | 4)
        reject(label, lambda bad=bad: ownership(bad))
    for opcode, label in ((0x4800, "Thumb literal"), (0xA000, "Thumb ADR"), (0xE000, "Thumb B"), (0xD000, "Thumb conditional B")):
        bad = bytearray(before); struct.pack_into("<H", bad, JA - 4, opcode)
        reject(label, lambda bad=bad: ownership(bad))
    bad = bytearray(before); struct.pack_into("<HH", bad, JA - 4, 0xF000, 0xF800)
    reject("Thumb BL pair", lambda: ownership(bad))
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "new", "art", "manifest", "output"):
        parser.add_argument(name, type=Path)
    root = Path(__file__).resolve().parents[1]
    for name, relative in (("config", "localization/result-labels.json"), ("catalog", "localization/digicode-reference.json")):
        parser.add_argument("--" + name, type=Path, default=root / relative)
    args = parser.parse_args()
    names = ("before", "after", "gba", "old", "new", "art", "config", "catalog")
    paths = {name: getattr(args, name) for name in names}
    need(all(path.suffix.lower() != ".sav" for path in [*paths.values(), args.manifest, args.output]), "save paths forbidden")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in {p.resolve() for p in [*paths.values(), args.manifest]}, "distinct JSON report output")
    need(not args.output.exists(),'preserve existing independent reports')
    data = {name: path.read_bytes() for name, path in paths.items()}
    need(all(sha(data[name]) == PINS[name] for name in names if name in PINS), "pinned independent inputs")
    before, after, gba, old, new = (data[name] for name in ("before", "after", "gba", "old", "new"))
    config, catalog, art = (json.loads(data[name]) for name in ("config", "catalog", "art"))
    ja, retail, punctuation, source_report = source_contract(gba, old, new)
    check_policy(config, catalog)
    wanted = expected_images(ja, punctuation, json.loads(data['art']))
    resources, resource_report = verify_resources(after, retail, ja, wanted)
    abi_report = abi(before, after)
    inverse(before, after); ownership(before)
    aliases_before, aliases_after = original_aliases(before), original_aliases(after)
    need(aliases_before == [(at, BASE + P0) for at in P0_ALIASES], "all seven original mirrored/all-alignment P0 aliases")
    need(aliases_after == sorted(aliases_before + [(CODE + 36, BASE + P0)]), "only additional English P0 alias is private selector table")
    population_report = population(after, gba, new, resources)
    manifest = json.loads(args.manifest.read_bytes())
    manifest_contract(manifest, before, after, resources)
    negatives = negative_cases(before, after, gba, old, new, ja, retail, wanted, resources, config, catalog, art)
    changed = sum(a != b for a, b in zip(before, after))
    need(changed == manifest["changed_bytes"], "actual changed-byte census")
    report = dict(status="PASS", kind="independent-four-language-result-labels", inputs={name: sha(data[name]) for name in names},
        source=source_report, resource_frames=60, localized_text_frames=9, retained_digit_frames=48,
        resources=resource_report, abi=abi_report, population=population_report,
        original_p0_aliases_before=aliases_before, original_p0_aliases_after=aliases_after,
        ownership=dict(ranges=[list(pair) for pair in ALLOCATIONS], empty_ff=True, all_alignments=True,
                       rom_mirrors=[8, 10, 12], arm_branch_literal_adr=True, thumb_branch_literal_adr_bl=True, exceptions=[]),
        writes=[dict(start=a, end=b, bytes=b-a, before_sha256=sha(before[a:b]), after_sha256=sha(after[a:b])) for a, b in WRITES],
        spans=10, declared_bytes=15904, changed_bytes=changed, full_inverse=True,
        reviewed_digicode_pixel_sha256="4F9B02D9BC03779DCB14B62B0D0EB0F5755BC0DD48B3006669E5631F4BAAC924",
        language_policy="Exact Japanese-source WIN/DRAW is shared by Japanese/Korean/Digicode. English retains WINS/DRAW. Korean/Digicode LAST CHANCE uses independently reviewed native art, with explicit localャ→ヤ identity. Exact source punctuation/digits retained.",
        negative_count=len(negatives), negative_cases=negatives,
        limits=["Four existing mode8 events only; source-only LOSE and mode12 behavior are unchanged.",
                "Approved Korean/Digicode artwork is checked against frozen palette-index pixel identities; external chart authentication is not claimed.",
                "Offscreen, transparent and overlapping parts all count; no clipping or renderer limit is used as a remedy.",
                "Static state closure includes indefinite second-pose tails; whole-game timing, other language consumers and campaign completion are separate.",
                "No emulator, target execution or save access; actual result-screen observations belong to separate runtime reports."])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status="PASS", report_sha256=sha(args.output.read_bytes()), frames=60, joint_states=389162,
                          declared_bytes=15904, changed_bytes=changed, negatives=len(negatives))))


if __name__ == "__main__":
    main()
