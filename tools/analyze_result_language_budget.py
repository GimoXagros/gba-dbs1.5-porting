#!/usr/bin/env python3
"""Read-only mode8 OAM proof and lossless result-label packing experiment.

No ROM is written. The inputs are the frozen result-pose candidate, retail
GBA/WSC1.5, licensed Korean font and the reviewed 98-cell Digicode catalog.
The complete native task population and correlated pose timing are counted;
offscreen parts and the renderer's overflow guard are never used as savings.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from build_options_korean_poc import font_glyphs as korean_font, text_pixels as korean_pixels
from digicode_glyphs import font_glyphs as digicode_font, text_pixels as digicode_pixels
from encode_digicode_reading import encode
from convert_wsc_palette_block import convert_block

BASE = 0x08000000
PINNED = {
    "current": "DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C",
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
    "font": "4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED",
    "license": "76B3F3DD55B1F37C31E440E7224EF732F8D1D0DB23CA9C4A610F575261C49A4C",
}
DG_ROWS = "E2704D551B94B4657BC93976A4DB93810ED30BA8BF6736B1FC61535D75F19195"
CODE = (
    (0x893A4, 0x89774, "6BEDE4B7F48FF7B1181ED6FC31C5CCA669E12CC58399303931FCE8EF4EE9DF3D"),
    (0x897AC, 0x8A354, "C707D97FBE3F7CDDE6F36A99B08C37AA6D5DBFE4D582D2A15AB4BA7B87790F27"),
    (0x8A4AC, 0x8B334, "372D7F3C1A83D86F04F794A57C99449B388D20A13BAAB94A99B46E18932BC4FE"),
    (0x12874, 0x12C28, "6A63C22471C3CF2DB8860BC2BEBCBC17BA9754525E31D86E3E3DC496937CAB5F"),
    (0x117B0, 0x11810, "1DB2A6237E90AD2B718E785E688309619283964924564859F2A1B2C0C50100D8"),
    (0x11D70, 0x11E0C, "34C1EDB66BD6E6E881D2796C11C84026E4812B16D8CB5E33B02EC56C7C6ABFE8"),
    (0x35227C, 0x352374, "654E9281B5B2D3AC98650EF7F95AC1F7C688A6FC35886DCC49684801E1A9387F"),
    (0xD1B0C, 0xD1C68, "9F3426DFE4F64ECEFE93BCE7B7D4B2C56A6BDF14FCFAF225B1B0131E685AD44C"),
    (0x340C54, 0x340CB0, "A2C3AB78C4A1ADC8B98AB9FEA683645B839BB88D68189F146A88864614AE3C1C"),
    (0x340F04, 0x340F90, "2C67A21B0D5D7025A3C67B398DFEA20A3BC9386CFFF8B44D7653B078C6FF94AD"),
    (0x340470, 0x34059C, "9F5676B4B7FCC894C41B9419C5BED2198FB42D74ACC9D6F3681D0BB5BAEBF94B"),
    (0x1E8C4, 0x1E9BC, "9084B52299757D7E94E54F44186973DD2628ABF97739B06D44E9597D5A4AD201"),
    (0x33FE94, 0x33FF5C, "4DC40C8BE91B8231421B10C0D4C0C27DBF22F294D6E104A238AC547BE7FC570F"),
    (0x83070, 0x830DC, "45486E7E84370D52CD1BFBABBBFBFD4EC07E4A98316E8BF5E594A990F7363060"),
    (0x1F51C, 0x1F590, "9D07B7360BEA0A1BC54202B4FD6FF3E755DFFD5FFE8F18561042ADCA01EB861D"),
    (0x17758, 0x177B0, "77EE72EC762AB9DC9294E8611F89D952686BD903828C6C240182BCD205794DFE"),
    (0xC9000, 0xC9074, "F164E7B89DC35D5913D4F9EA1F589B58291AA6DBCB8857FF307E4AF81C2D557C"),
    (0x159B4, 0x15B70, "EACE6D1A791C9BA7A4EED828E345BE5C59C9F72035DD0ACA53028690BAA604C8"),
    (0xD15F0, 0xD1B0C, "49AE7DD99553EABD4738F8FF03CB97A86A7EFE95158949AB9C7A583CE099039A"),
)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded input read")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def pointer(data, at, size=1):
    result = u(data, at) - BASE
    cut(data, result, size)
    return result


def literal(data, at, register=8):
    word = u(data, at)
    need(word & 0x0F7FF000 == (0x051F0000 | register << 12), f"r{register} PC-relative load at {at:X}")
    return u(data, at + 8 + (word & 4095) * (1 if word & 0x800000 else -1))


def branch_target(word, at):
    displacement = word & 0xFFFFFF
    if displacement & 0x800000:
        displacement -= 0x1000000
    return at + 8 + displacement * 4


def calls(data, lo, hi, target=None):
    out = []
    for at in range(lo, hi, 4):
        word = u(data, at)
        if word & 0x0F000000 == 0x0B000000:
            dest = branch_target(word, at)
            if target is None or dest == target:
                out.append((at, dest))
    return out


def native_parts(data, p0, layout):
    table = pointer(data, p0)
    count = u(data, table + layout * 8)
    need(0 < count <= 127, "native layout bounded part count")
    raw = pointer(data, table + layout * 8 + 4, count * 4)
    return [struct.unpack("<Hbb", cut(data, raw + i * 4, 4)) for i in range(count)]


def native_event(data, p0, p1, event):
    table = pointer(data, p1)
    count = u(data, table + event * 16)
    need(0 < count <= 255, "complete native P1 frame count")
    raw = pointer(data, table + event * 16 + 4, count * 16)
    frames = []
    for i in range(count):
        at = raw + i * 16
        duration, flags, layout = data[at], h(data, at + 6), h(data, at + 2)
        need(duration < 128, "signed native duration domain")
        frames.append(dict(duration=duration, flags=flags, layout=layout,
                           parts=len(native_parts(data, p0, layout)), command_raw=at))
    return frames


def native_population(data, gba):
    for lo, hi, digest in CODE:
        need(sha(cut(data, lo, hi - lo)) == digest, f"complete code dependency {lo:X}")
        need(cut(data, lo, hi - lo) == cut(gba, lo, hi - lo), "unchanged retail callback/driver")
    need(struct.unpack("<3I", cut(data, 0x15BD0, 12)) ==
         (BASE + 0x893A4, BASE + 0x897AC, BASE + 0x159B0), "mode8 init/constructor/common binding")
    need(u(data, 0x159B0) == 0xE12FFF1E, "empty mode common callback")
    need(literal(data, 0x1F3B0) == BASE + 0x4A80F8 and u(data,0x1F3B4) == 0xE0881281,
         "base fighter group indexed ID*32 without evolution switch")
    need(sha(cut(data,0x1F3A8,0xF8)) == "0732867DA2D3D2BE7CB8D1D317B1498C93A8C74E5005317478015865397352BC",
         "complete unchanged base presentation loader")
    expected = ((0x1000, 0x8A4AC), (0xF000, 0x8B200), (0x1500, 0x8B024),
                (0x1600, 0x8AC34), (0x1700, 0x8AC34), (0x2000, 0x8A7C0), (0x3000, 0x8A7C0))
    allocations = calls(data, 0x897AC, 0x8A354, 0x11AC4)
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    rows = []
    for (at, _), (priority, callback) in zip(allocations, expected):
        ins = list(decoder.disasm(cut(data, at - 8, 4), BASE + at - 8))[0]
        need(ins.mnemonic == "mov" and ins.op_str == f"r8, #{hex(priority)}", "native task priority")
        need(literal(data, at - 20) == BASE + callback, "native task callback literal")
        rows.append(dict(allocator_call_raw=at, priority=priority, callback_raw=callback))
    need(len(rows) == len(allocations) == 7, "exact seven constructor-created tasks")
    draws = [at for at, _ in calls(data, 0x8A4AC, 0x8B334, 0x12C28)]
    need(draws == [0x8A858, 0x8A930, 0x8AA18, 0x8AAB0,
                   0x8AC6C, 0x8AC8C, 0x8ACAC, 0x8AD70, 0x8AD84, 0x8AD98,
                   0x8AEF4, 0x8AF24, 0x8AF54, 0x8AF88, 0x8AF9C, 0x8AFB0,
                   0x8B0AC, 0x8B170, 0x8B19C], "complete result callback draw sites")
    need(not calls(data, 0x8A4AC, 0x8B334, 0x11AC4) and
         not calls(data, 0x8A4AC, 0x8B334, 0x127E4), "callbacks allocate no extra presentation/task")
    guards = {0x11DCC: 0xE5958000, 0x11DD4: 0xE12FFF18, 0x11DF0: 0xE595500C,
              0x117C8: 0xE3A07000, 0x117CC: 0xE5C87000, 0x352298: 0xE3A0201A,
              0x3522BC: 0xE3A0201A, 0x352348: 0xE3A0201A, 0x8A6A8: 0xE3A01C3F,
              0x8A8BC: 0xE3A09030, 0x8A9D0: 0xE3A090DE, 0x12BB8: 0x101}
    for at, word in guards.items():
        need(u(data, at) == word, f"scheduler/lifecycle/phase guard {at:X}")
    need(literal(data, 0x352280, 4) == literal(data, 0x352344, 4) == 0x030047A8,
         "same complete 26-slot battle task array created/deleted")
    need([at for at, _ in calls(data, 0xD1B0C, 0xD1B80, 0x352340)] == [0xD1B24] and
         [at for at, _ in calls(data, 0xD1B0C, 0xD1B80, 0xD1C24)] == [0xD1B28], "battle teardown covers object and service tasks")
    return dict(total_tasks=8, constructor_tasks=rows, mode_controller_tasks=1,
                presentations=dict(heading=1, name_or_last_chance=1, digits=6, fighters=2),
                total_presentations=10, draw_sites_raw=draws, service_oam_parts=0,
                callback_dependencies=[dict(raw=[a, b], sha256=s) for a, b, s in CODE],
                entry="Battle teardown080D1B0C deletes26 renderer tasks, two service tasks and03004518 before setting the mode-change flag; priority0 mode dispatch follows on a later scheduler traversal.",
                exit="0808A698 waits for all six completion bits3F00; every result drawing task deletes itself before the next mode is requested.",
                overlap=False, queue_reset_raw=0x117C8,
                services="83070/1F51C scroll and palette counters; 33FE94/33FF00 blending; 17758/C9000 LCD scanline state; 1E8C4 SCORE writes BG tilemap only.")


def pose_frames(data, source):
    need(cut(data, 0x629480, 64) == cut(source, 0x7771C0, 64), "corrected source-exact result-pose views")
    for at, expected in ((0x8A418, 0x629480), (0x8A41C, 0x629481), (0x8A420, 0x6294A0), (0x8A424, 0x6294A1),
                         (0x8A43C, 0x629480), (0x8A440, 0x629481), (0x8A444, 0x6294A0), (0x8A448, 0x6294A1),
                         (0x8A44C, 0x629480), (0x8A450, 0x629481), (0x8A454, 0x6294A0), (0x8A458, 0x6294A1)):
        need(u(data, at) == BASE + expected, "all six actual result-pair reader routes")
    actors, names = [], []
    for ident in range(15):
        p0, p1 = (pointer(data, 0x4A80F8 + ident * 32 + off) for off in (0, 4))
        pairs = [tuple(cut(data, table + ident * 2, 2)) for table in (0x629480, 0x6294A0)]
        events = {0, 1, 0x51, 0x56, *pairs[0], *pairs[1]}
        fs = {e: native_event(data, p0, p1, e) for e in sorted(events)}
        for first in (pairs[0][0], pairs[1][0]):
            need(all(f["flags"] == 0 for f in fs[first]), "first poses are finite sequential events")
        actors.append(dict(id=ident, p0_raw=p0, p1_raw=p1, pairs=pairs, events=fs))
        name = native_event(data, 0xB799C, 0xB77EC, ident)
        need(len(name) == 1, "one stable winner-name frame")
        names.append(name[0]["parts"])
    need(names == [16,22,16,16,20,14,16,14,14,16,14,16,16,16,16], "all fifteen native winner names")
    need(sum(len(a["events"]) for a in actors) == 120 and
         sum(len(fs) for a in actors for fs in a["events"].values()) == 1252, "complete repaired pose/event population")
    return actors, names


@dataclass
class Actor:
    events: dict
    pair: tuple
    phase: int = 0
    frame: int = 0
    left: int = 0
    flags: int = 0

    def __post_init__(self):
        self.select()

    def select(self):
        self.frame = 0
        f = self.events[self.pair[self.phase]][0]
        self.left, self.flags = f["duration"], f["flags"]

    def state(self):
        return self.phase, self.frame, self.left, self.flags

    def step(self):
        frames = self.events[self.pair[self.phase]]
        if not self.flags & 0x2000:
            remaining = (self.left - 256 if self.left & 128 else self.left) - 1
            self.left = remaining & 255
            # BPL tests the signed32-bit subtraction, not the truncated byte.
            if remaining < 0:
                self.frame += 1
                if self.frame == len(frames):
                    if self.flags & 1:
                        self.frame = 0
                    else:
                        self.frame -= 1
                        self.flags |= 0x2000
                if not self.flags & 0x2000:
                    f = frames[self.frame]
                    self.left = (self.left + f["duration"]) & 255
                    self.flags = (self.flags & 0x101) | f["flags"]
        if self.phase == 0 and self.flags & 0x2000:
            self.phase = 1
            self.select()
        return self.events[self.pair[self.phase]][self.frame]["parts"]


def paired_bounds(actors, names):
    rows, witness, max_total, completion = [], None, -1, []
    for actor in actors:
        for side, pair in zip(("win","lose"), actor["pairs"]):
            state = Actor(actor["events"],pair)
            ticks = 0
            while state.phase == 0:
                need(ticks < 222, "every first pose completes before the native result countdown")
                state.step(); ticks += 1
            completion.append(dict(id=actor["id"],kind=side,first_event=pair[0],calls=ticks))
    need(min(r["calls"] for r in completion)==5 and max(r["calls"] for r in completion)==140,
         "all thirty actual first-pose completion intervals")
    for winner in actors:
        for loser in actors:
            win = Actor(winner["events"], winner["pairs"][0])
            lose = Actor(loser["events"], loser["pairs"][1])
            seen, pair_max, step = {}, 0, 0
            while (key := (win.state(), lose.state())) not in seen:
                need(step < 100000, "finite pair-state closure must be established, never truncated")
                seen[key] = step
                a, b = win.step(), lose.step()
                total = names[winner["id"]] + a + b
                pair_max = max(pair_max, total)
                if total > max_total:
                    max_total = total
                    witness = dict(winner=winner["id"], loser=loser["id"], step=step,
                                   name=names[winner["id"]], winner_parts=a, loser_parts=b,
                                   winner_state=win.state(), loser_state=lose.state())
                step += 1
            rows.append(dict(winner=winner["id"], loser=loser["id"], states=step,
                             tail_start=seen[key], period=step-seen[key], name_plus_poses_max=pair_max))
    return dict(pairs=len(rows), states=sum(r["states"] for r in rows),
                longest=max(r["states"] for r in rows), name_plus_poses_max=max_total,
                witness=witness, first_pose_completion=completion, rows=rows,
                domain="Both first poses start on the same traversal after the shared48-countdown; each then advances delta1. The finite graph includes indefinite phase2 loops and holds, beyond the normal222-countdown.")


def bounds(pixels):
    return [min(x for x,y in pixels), min(y for x,y in pixels), max(x for x,y in pixels), max(y for x,y in pixels)]


def tile_pixels(tile):
    need(len(tile) == 32, "complete native tile")
    return {(x,y): (tile[y*4+x//2] >> (4*(x&1))) & 15 for y in range(8) for x in range(8)}


def compose(parts, tiles):
    pixels = {}
    for flags, y, x in parts:
        need(flags & 0xE00 == 0x400, "one exact source result text palette bank")
        need((flags & 255) < len(tiles), "native low-byte tile index")
        for (xx, yy), value in tile_pixels(tiles[flags & 255]).items():
            if value:
                point = (x + (7-xx if flags & 0x4000 else xx), y + (7-yy if flags & 0x8000 else yy))
                pixels.setdefault(point, value)
    return pixels


def pack_exact(pixels, grid):
    tiles, lookup, parts = [], {}, []
    cells = sorted({((x-grid[0])//8*8+grid[0], (y-grid[1])//8*8+grid[1]) for x,y in pixels}, key=lambda p:(p[1],p[0]))
    for x, y in cells:
        tile = bytes(pixels.get((x+xx,y+yy),0) | pixels.get((x+xx+1,y+yy),0)<<4
                     for yy in range(8) for xx in range(0,8,2))
        need(any(tile), "no blank padding part")
        if tile not in lookup:
            lookup[tile] = len(tiles)
            tiles.append(tile)
        parts.append((0x400 | lookup[tile], y, x))
    need(len(tiles) <= 256 and all(-128 <= q <= 127 for _, y, x in parts for q in (x,y)), "native packing domain")
    need(compose(parts, tiles) == pixels, "complete palette-index pixel roundtrip")
    return parts, tiles


def pixel_sha(pixels):
    return sha(b"".join(struct.pack("<hhB", x, y, pixels[x,y]) for x,y in sorted(pixels)))


def source_labels(source, native):
    p0, p1, p2 = 0x3CB870, 0x3D29E0, 0x3D7EB0
    need(sha(cut(source,0x777465,0x71)) == "3D13705D83F5829CCF7E1E6F007DC259AC364B51495AE0E15D8ACF960AF02C4C",
         "actual zeroed Japanese branch and exact P0/P1/P2 constructor arguments")
    need(u(source, p0) == 16 and u(source, p1) == 4, "source P0/P1 headers")
    seg, bank = struct.unpack("<2H", cut(source, p0+4, 4))
    descriptor = (bank & 127)*0x10000 + (seg-0x2000)*16
    size, off, seg, bank = struct.unpack("<4H", cut(source, descriptor, 8))
    atlas = (bank & 127)*0x10000 + seg*16 + off - 0x20000
    need((descriptor, atlas, size) == (0x3D8E80, 0x3A0000, 0xCC0), "actual source atlas descriptor")
    tiles = []
    for at in range(atlas, atlas+size, 32):
        planar = cut(source, at, 32)
        values = [sum(((planar[y*4+b] >> (7-x)) & 1) << b for b in range(4)) for y in range(8) for x in range(8)]
        tiles.append(bytes(values[i] | values[i+1]<<4 for i in range(0,64,2)))
    frames, counts = [], []
    for index in range(16):
        count, rel = struct.unpack("<2H", cut(source, p0+16+index*4, 4))
        parts = [struct.unpack("<Hbb", cut(source, p0+rel+i*4, 4)) for i in range(count)]
        frames.append(compose(parts, tiles)); counts.append(count)
    need(counts == [38,20,4,2,4,4,5,4,4,3,4,4,4,4,28,17], "full actual Japanese source layout population")
    need(convert_block(cut(source,p2,38)) == cut(native,0xB9144,40), "same complete Japanese/native result palette")
    need([h(source,p1+4+i*8) for i in range(5)] == [1,1,12,1,1], "source five events; source-only LOSE excluded")
    repacked, repacked_tiles = pack_exact(frames[0], (0,5))
    need(len(repacked) == 30 and bounds(frames[0]) == [-39,-11,39,12], "lossless Japanese WIN30-part packing")
    punctuation = {xy:v for xy,v in frames[14].items() if 42 <= xy[0] <= 50}
    need(bounds(punctuation) == [42,-8,50,6] and not any(x == 41 for x,y in frames[14]), "isolated complete source exclamation after blank column41")
    return frames, punctuation, dict(p0_raw=p0,p1_raw=p1,p2_raw=p2,atlas_raw=atlas,
        source_parts=counts, included_events=[0,1,2,3], excluded_event=4,
        japanese_win=dict(before=38,after=30,grid=[0,5],bounds=bounds(frames[0]),
                          pixels=len(frames[0]),pixel_sha256=pixel_sha(frames[0]),
                          exact_pack_roundtrip=True,unique_tiles=len(repacked_tiles)),
        exclamation=dict(bounds=bounds(punctuation),pixels=len(punctuation),pixel_sha256=pixel_sha(punctuation)))


def draft_labels(font, catalog, reference, punctuation):
    need(bounds(punctuation) == [42,-8,50,6] and len(punctuation) == 65 and
         set(punctuation.values()) <= {6,7,8,9,10,12}, "complete native punctuation input")
    mappings = dict(reference["mapping"])
    need(mappings["ゃャ"] == mappings["やヤ"] == "/jp/ya.svg", "documented local small-YA identity")
    try:
        encode("ラストチャンス", catalog)
    except ValueError:
        pass
    else:
        raise ValueError("frozen strict encoder unexpectedly broadened")
    dg = digicode_font(catalog)
    need(len(catalog["glyphs"])+len(catalog["latin_glyphs"]) == 98 and
         sha(b"".join(dg[g["id"]] for g in catalog["glyphs"]+catalog["latin_glyphs"])) == DG_ROWS,
         "exact unchanged reviewed98-cell font")
    texts = ("승리", "무승부", "마지막 기회")
    kg = korean_font(font, set("".join(texts)))
    reports, counts = {}, {}
    for language, labels in (("ko", texts), ("digicode", ("WIN", "DRAW", "ラストチヤンス"))):
        output = []
        for index, text in enumerate(labels):
            px, width = (korean_pixels(text,kg) if language == "ko" else digicode_pixels(text,catalog,dg))
            # This is a geometry/budget draft. Keep all outline pixels and the
            # complete actual native exclamation; a future resource review owns
            # the final ink palette/style, which does not change this bound.
            shift = 5 if language == "ko" else 7
            px = {(x,y+shift):(10 if value == 1 else 12) for (x,y),value in px.items()}
            if index == 2:
                start = width+2
                shifted = {(start+x-42,y):v for (x,y),v in punctuation.items()}
                need(not px.keys() & shifted.keys(), "native punctuation remains distinct and complete")
                px.update(shifted)
                width = start+9
            left = -(width//2)
            px = {(x+left,y):v for (x,y),v in px.items()}
            parts, _ = pack_exact(px, (left,min(y for x,y in px)))
            output.append(dict(reading=text,parts=len(parts),width=width,bounds=bounds(px),pixels=len(px),pixel_sha256=pixel_sha(px),exact_pack_roundtrip=True))
        reports[language] = output
        counts[language] = [row["parts"] for row in output]
    return counts, dict(frames=reports,
        japanese_metadata=["WIN","DRAW","ラストチャンス！"],
        digicode_policy="WIN/DRAW use Latin only because the actual Japanese resource contains Latin; only the exact ラストチャンス reading applies localャ→ヤ. Native exclamation is preserved. Strict encoder/catalog/font are unchanged.",
        alias=dict(source="ャ",target="ヤ",glyph_id=encode("ヤ",catalog)[0],reference_image="/jp/ya.svg"),
        status="Geometry and complete-pixel packing feasibility; not installed assets or final visual approval.")


def approved_labels(art, source_frames, punctuation):
    """Count the QA-approved native parts, without redrawing any language."""
    frames = [*art["japanese_common"], art["korean"], art["digicode"]]
    reports = []
    for frame in frames:
        pixels = {(x, y): value for x, y, value in frame["pixels"]}
        tiles = [bytes.fromhex(tile) for tile in frame["tiles_4bpp_hex"]]
        need(compose(frame["parts"], tiles) == pixels, "approved art complete native inverse")
        need(pixel_sha(pixels) == frame["palette_pixel_sha256"], "approved palette pixel identity")
        reports.append(dict(parts=len(frame["parts"]), pixels=len(pixels), bounds=bounds(pixels), pixel_sha256=pixel_sha(pixels)))
    need([{(x,y):v for x,y,v in f["pixels"]} for f in frames[:2]] == source_frames[:2], "shared Japanese WIN/DRAW exact source")
    for frame in frames[2:]:
        need({(x,y):v for x,y,v in frame["pixels"] if x>=42} == punctuation, "approved exact native punctuation")
    need([r["parts"] for r in reports] == [30,20,26,27], "approved art population")
    need([r["pixel_sha256"] for r in reports] == [
        "8ECA7847B508136FCB6CF9A6B3613778E95CD6932995D6810117D4A6CB622499",
        "D47B0B69E6AA2E5FBE3AA8228EA6F3F272DBF90400BFB55C9FE79A68EE366F22",
        "124F00001D3C12A36C3336049D28BAFEE6EC3321C975ADAE0D072C15D9946917",
        "4F9B02D9BC03779DCB14B62B0D0EB0F5755BC0DD48B3006669E5631F4BAAC924"], "independently approved complete indexed pixel commitments")
    return {"ko":[30,20,26], "digicode":[30,20,27]}, dict(status="Independent-QA-approved native indexed art", frames=reports,
        digicode_policy="Japanese source WIN/DRAW graphics reused exactly; last-chance seven Japanese-reading glyphs only.")


def analyze(data, gba, source, font=None, catalog=None, reference=None, *, art=None):
    population = native_population(data,gba)
    actors, names = pose_frames(data,source)
    pair = paired_bounds(actors,names)
    labels = [native_event(data,0xB8210,0xB9004,event) for event in range(4)]
    digits = [f["parts"] for f in labels[2]]
    need(digits == [4,2,4,4,5,4,4,3,4,4,4,4], "all native digit/symbol frames retained")
    values = [sum(digits[int(c)] for c in f"{score:03d}") for score in range(256)]
    final_max = max(values[a]+values[b] for a in range(256) for b in range(a))
    need(final_max == 28 and max(values) == 14, "byte-score decimal final digits")
    initial_left = max(f["parts"] for a in actors for e in (0,1,0x56) for f in a["events"][e])
    initial_right = max(f["parts"] for a in actors for e in (0,0x51,0x56) for f in a["events"][e])
    prephase = initial_left+initial_right+6*max(digits)
    independent = max(names[a["id"]]+max(f["parts"] for e in a["pairs"][0] for f in a["events"][e]) for a in actors)
    lose_max = max(f["parts"] for a in actors for e in a["pairs"][1] for f in a["events"][e])
    pose_any = max(f["parts"] for a in actors for fs in a["events"].values() for f in fs)
    draw_pose = max(f["parts"] for a in actors for e in (0,1) for f in a["events"][e])
    source_frames, punctuation, source_report = source_labels(source,data)
    draft_counts, draft_report = (approved_labels(art,source_frames,punctuation) if art is not None
                                  else draft_labels(font,catalog,reference,punctuation))
    counts = {"en":[labels[0][0]["parts"],labels[1][0]["parts"],labels[3][0]["parts"]],
              "ja":[30,20,28], **draft_counts}
    outcomes = []
    for language,(win,draw,last) in counts.items():
        normal = win+pair["name_plus_poses_max"]+final_max
        # This intentionally permits DRAW and LAST CHANCE simultaneously,
        # although the native callback chooses one interval or the other.
        ordinary_draw = draw+last+2*draw_pose+final_max
        linked_draw = draw+2*pose_any+final_max  # flag1000 suppresses second label
        maximum = max(prephase,normal,ordinary_draw,linked_draw)
        need(maximum <= 127 and maximum*32 <= 4096, f"complete {language} OAM/staging upper bound")
        outcomes.append(dict(language=language,label_parts=[win,draw,last],prelabel=prephase,
            normal_win=normal,normal_independent_overestimate=win+independent+lose_max+final_max,
            ordinary_draw=ordinary_draw,repeated_or_linked_draw=linked_draw,
            skipped_constructor=0,services=0,transition_extra=0,maximum=maximum,tile_bytes=maximum*32))
    return dict(schema=1,kind="read-only-result-language-budget",status="BOUNDED_PACKING_PROPOSAL",
        population=population,poses=dict(ids=15,selected_events=120,selected_frames=1252,
            base_resources_only=True,names=names,independent_winner_plus_name=independent,
            independent_loser=lose_max,largest_any_pose=pose_any,draw_pose_max=draw_pose,correlated=pair),
        digits=dict(parts=digits,score_domain=[0,255],per_side_final=max(values),both_final=final_max,
            maximizing_unequal_scores=[244,44],both_rolling=6*max(digits),
            correlation="The two digit tasks have identical16/59/118 phase counters and priorities1600/1700 before both fighters2000/3000. Each freezes all3 actual decimal frames before flag1 starts both pose48-countdowns; heading/name require later flag2."),
        phases=[
            dict(name="initial slide and rolling score",headings=False,pose_events_left=[0,1,0x56],pose_events_right=[0,0x51,0x56],bound=prephase,
                 evidence="Both fighter slide counters16 finish before digit finalization, even in accelerated draw mode. The source-selected result poses have not started; text gate8B040..8B054 excludes both text objects."),
            dict(name="frozen score and shared pose delay",headings=False,pose_event=0x56,
                 evidence="AE5C/AE80/AEA4 set all three actual digits beforeAEB4 setsflag1; both A870 callbacks see it after both digit tasks and set the identical48 countdown. A94C holds event56 until reachingzero."),
            dict(name="normal result and indefinite wait",headings=True,
                 evidence="Both A94C callbacks select first pair events and advance1 on the same traversal; all future AA30 callbacks advance1 once. The name follows the winner ID; 389162 joint states close before any cutoff. Text is conservatively counted throughout."),
            dict(name="draw and last chance",headings=True,
                 evidence="Ordinary draw sets4000, substitutes event0, disables phase2 pair handoff and later chooses walkingevent1. Repeated/linked draw sets1000, suppresses lastchance, and is bounded with both unrestricted selected-pose maxima."),
            dict(name="fade and exit",headings=True,extra_parts=0,
                 evidence="The drawing callbacks retain their same presentations until deletion; fade/scroll/palette/scanline/BG text services add no OAM. All six completion flags precede next-mode dispatch."),
        ],
        source=source_report,drafts=draft_report,budgets=outcomes,
        unrepacked_japanese_upper_bound=38+pair["name_plus_poses_max"]+final_max,
        assumptions=["All15 playable IDs and all byte scores are included, including same-character matches; no gameplay score attainability restriction is used.",
            "Every layout part counts even when offscreen, transparent or overlapping. No renderer clamp, dropped glyph, missing fighter, shortened phrase or changed timing is a budget remedy.",
            "Final whole-ROM integration must revalidate the unchanged native dependencies against the future Waterfall-repaired predecessor."],
        limitations=["No language ROM is built; this is a read-only prebuild gate with in-memory exact tile roundtrips.",
            "Approved native art is used when supplied; the legacy font-draft path is not production artwork.",
            "Root's actual ID14 result-pose consumer probe is distinct from this static aggregate proof; no normal result-screen runtime pass is claimed."])


def self_checks(data, gba, source, font, catalog, reference):
    rejected=[]
    def reject(label, fn):
        try: fn()
        except (ValueError,KeyError,IndexError,struct.error): rejected.append(label)
        else: raise ValueError("negative accepted: "+label)
    bad=bytearray(data);struct.pack_into("<I",bad,0x8A418,BASE+0x89774)
    reject("old-truncated-pose-route",lambda:pose_frames(bad,source))
    for offset,value in ((0x62949C,0x73),(0x6294BC,0x75)):
        bad2=bytearray(data);bad2[offset]=value
        reject(f"wrong-added-ID14-pose-{offset:X}",lambda d=bad2:pose_frames(d,source))
    p1=pointer(data,0x4A80F8+14*32+4);table=pointer(data,p1);command=pointer(data,table+0x74*16+4)
    for label,offset,replacement in (("missing-pose-frame",table+0x74*16,b"\0"*4),
                                    ("signed-duration-overflow",command,b"\x80"),
                                    ("first-pose-never-completes",command+6,b"\x01\x00"),
                                    ("invalid-layout",command+2,b"\xff\xff")):
        changed=bytearray(data);changed[offset:offset+len(replacement)]=replacement
        reject(label,lambda d=changed:pose_frames(d,source))
    reject("unreviewed-small-YA-direct-encoding",lambda:encode("ラストチャンス",catalog))
    reject("unknown-punctuation-has-no-font-fallback",lambda:encode("！",catalog))
    changed_ref=json.loads(json.dumps(reference));changed_ref["mapping"]=[(a,"/wrong.svg" if a=="ゃャ" else b) for a,b in changed_ref["mapping"]]
    _,punct,_=source_labels(source,data)
    reject("different-small-YA-reference",lambda:draft_labels(font,catalog,changed_ref,punct))
    reject("cropped-exclamation",lambda:draft_labels(font,catalog,reference,{(0,0):16}))
    for label,at in (("missing-task-population",0x898D8),("unsynchronized-pose-delay",0x8A8BC),
                     ("missing-battle-task-teardown",0x352348),("premature-mode-transition",0x8A6A8),
                     ("missing-frame-queue-reset",0x117C8),("rolling-digits-after-finalize",0x8AEBC)):
        changed=bytearray(data);changed[at:at+4]=b"\0"*4
        reject(label,lambda d=changed:native_population(d,gba))
    # Exact packing must preserve sparse edges and source colors, including
    # negative positions and tiles which straddle the chosen grid origin.
    sparse={(-9,-9):12,(-1,-1):6,(0,0):10,(8,8):7}
    parts,tiles=pack_exact(sparse,(0,5))
    reject("missing-packed-edge-pixel",lambda:need(compose(parts[1:],tiles)==sparse,"complete pixels"))
    actors,names=pose_frames(data,source)
    joint=paired_bounds(actors,names)["name_plus_poses_max"]
    reject("unrepacked-Japanese-WIN-overflow",lambda:need(38+joint+28<=127,"native full-population capacity"))
    return dict(count=len(rejected),all_rejected=True,cases=rejected)


def main():
    if len(sys.argv)>1 and sys.argv[1]=="--approved-art":
        need(len(sys.argv)==7,"--approved-art CURRENT GBA WSC15 ART OUTPUT")
        current,gba_path,source_path,art_path,output=map(Path,sys.argv[2:])
        paths=(current,gba_path,source_path,art_path)
        need(all(p.suffix.lower()!=".sav" for p in (*paths,output)),"save paths forbidden")
        need(output.suffix.lower()==".json" and output.resolve() not in {p.resolve() for p in paths},"distinct report output")
        data,gba,source,art_bytes=(p.read_bytes() for p in paths)
        need(sha(data)=="494D14A2D4661FEA5DF36A9D12D57D31B2204924702CAB95DB3CE12A857F58B6","exact source-title result predecessor")
        need(sha(gba)==PINNED["gba"] and sha(source)==PINNED["wsc15"],"pinned originals")
        report=analyze(data,gba,source,art=json.loads(art_bytes))
        report["hashes"]={k:sha(v) for k,v in zip(("current","gba","wsc15","art"),(data,gba,source,art_bytes))}
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        print("[approved-result-budget] "+str([(r["language"],r["maximum"]) for r in report["budgets"]]))
        return
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("current","gba","wsc15","font","license","output"):
        p.add_argument(name,type=Path)
    root=Path(__file__).resolve().parents[1]
    p.add_argument("--catalog",type=Path,default=root/"localization/digicode-reference.json")
    p.add_argument("--reference",type=Path,default=root/"local/digimoji-reference-20261021/reference.json")
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    paths={name:getattr(args,name) for name in (*PINNED,"catalog","reference")}
    need(all(path.suffix.lower()!=".sav" for path in [*paths.values(),args.output]),"save paths forbidden")
    need(args.output.suffix.lower()==".json" and args.output.resolve() not in {x.resolve() for x in paths.values()},"report-only distinct output")
    data={name:path.read_bytes() for name,path in paths.items()}
    for name,digest in PINNED.items():need(sha(data[name])==digest,"pinned input "+name)
    catalog=json.loads(data["catalog"]);reference=json.loads(data["reference"])
    report=analyze(data["current"],data["gba"],data["wsc15"],data["font"],catalog,reference)
    report["hashes"]={name:sha(value) for name,value in data.items()}
    if args.self_test:report["negative_checks"]=self_checks(data["current"],data["gba"],data["wsc15"],data["font"],catalog,reference)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("[result-language-budget] "+report["status"]+" "+str([(r["language"],r["maximum"]) for r in report["budgets"]])+" "+sha(args.output.read_bytes()))


if __name__=="__main__":
    main()
