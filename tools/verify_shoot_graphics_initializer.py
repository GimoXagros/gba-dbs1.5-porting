#!/usr/bin/env python3
"""Independent ROM-bound checks for the dedicated Shoot graphics layer.

This verifier imports no builder/converter and does not execute machine code.
It decodes final placements, checks reviewed instruction/data hashes, reverses
the retail font/color encoding, and compares source buffered-color semantics
against the compact representation over every update state and flag choice.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs

PREDECESSOR = "223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E"
OUTPUT = "6F02E33A164D764BFC5BC071CA5522339032B089D9BF9A3702F5EF9551603C29"
SOURCE_HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
# Final reviewed boundaries.  Hashes cover instruction bytes AND local literals.
CODE = (
    ("graphics", 0x5C6800, 236, 292, "41DE52839852A31A6B16C6381E1A052C565D69775C7DA2DB93B5EAA199FFB8B1"),
    ("stage_resources", 0x5C6A00, 40, 56, "527363F6AAE9E1EAD456C5759A15D7F9A1B2C4B77074E88AF3E13EE8689B6487"),
    ("bounds", 0x5C6B00, 96, 104, "78E7906270982D80C9F07DEB65FF9C46F3B4FBE31A876E11C8A3A56F6F9D000B"),
    ("bounds_hook", 0x5C6C00, 32, 36, "92075B4259741E39A6DE474D52B8DF67BC0B1370AB4403B63A4533C257F5CB79"),
    ("palette_init", 0x5C6D00, 64, 72, "048AD412FD77E7EF4E42D153C6296BCA56427C75C56F05FA3AE29A8F420F8B6D"),
    ("palette_update", 0x5C6E00, 160, 176, "48653752705684E5239945FCF13641E4071F2D4C56D249214161F63944AC428B"),
    ("palette_project", 0x5C6F00, 248, 268, "A5BF5D31A6DD7679945E0EBAB3059B09FC2A91F16422C5C8BC3AE9B6FA47E6E3"),
    ("palette_hook", 0x5C7100, 32, 36, "EC3FB9FA565C924CCDEA3323EB1F831085D2ADD60FDC4539BA3C4C2A1C864A40"),
    ("irq_preamble", 0x5C7200, 56, 68, "D194F1448221ABECBC38E1270967664521585A6A62627DEBD64B5EDB2575D4AD"),
    ("palette_init_hook", 0x5C7380, 32, 36, "7E3901FCD6DF01953D62B8339DEC12C7B058181FAC5F579877659178C653EC64"),
)
ORACLES = (
    ("wsc15", 0x77DCB4, 0x77DE62, "F43D8674B2C9CC396250727CD2987FBBC0E5015348839F1771234F0D80A3D2E4"),
    ("wsc15", 0x77DF30, 0x77DFDF, "1F46DA4A8030853300FFC722520BAAE40DDCBE10DFB4E6A27361D238FC55751D"),
    ("wsc15", 0x77E0C5, 0x77E1A4, "D27C5D44BA4721DC3688F7ACCEC47C34AA16D511A2B7E1E653728B52FA751C28"),
    ("wsc15", 0x77E29F, 0x77E2B2, "F15F20236340E27DD574CD358E993B7AB98BEC57670478585E9A2C692E7BA8F6"),
    ("wsc15", 0x747A76, 0x747A9F, "F3B6F1EE3AC4EC6503CD224D713500400755080C2DD2148A187AB6928DD20AC1"),
    ("wsc15", 0x783470, 0x78370E, "088D5A83DFD61B3C65BAB860DE97BC3260CBE8123D305DA4BC0223E6F56E46EF"),
    ("wsc15", 0x78370E, 0x78378C, "230C505415173C2958B4FCED9551AEA4D19DFC686CB85EB5495995C3632440B9"),
    ("wsc15", 0x783C9E, 0x783EAF, "BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1"),
    ("wsc15", 0x76B1CF, 0x76B312, "7533706F4580DBFB23A17911443B9999D44E777591CD551F544FC28E5349D71D"),
    ("wsc15", 0x7693AC, 0x769410, "8C2E97BB8E1DC088B6A9CD164621148D4618C8BFDC5DB4FDB434EBA07FBFF48A"),
    ("wsc10", 0x3BC801, 0x3BC898, "5A35E1EE297FFB43480DA8B49182B1779CA29D1C7F8B0DCA3272773ADE69FB45"),
    ("gba", 0xD0B24, 0xD0BC0, "BEB7F435B56D93A439220C563B84C8F268D5EBCC3BC9C49E3600F05EDBBB8463"),
    ("gba", 0xC4BC0, 0xC4C38, "3E76211444CD5DF2FEFA5A32E4DCE0E5FB169F79FC41DF01EE1366C78D900521"),
    ("gba", 0x11440, 0x11520, "3E496ACAB31BD31527E36B9C160397DEF80E6D94CA0624C425C25622B002013B"),
    ("gba", 0x7FEB0, 0x80040, "DDFCB9DCF874762346481181CC5C82DBCED6936BE0B71735F726CA3919F9AF9A"),
    ("gba", 0x80040, 0x80140, "83EFD251CE309B96D3B5DE6CD60CC011DAFAECA3943BEE20E799DC20FB5B1115"),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def native_color(source: int) -> int:
    """Commercial oracle: zero maps to zero, nonzero n maps to 2*n+1."""
    red, green, blue = (source >> 8) & 15, (source >> 4) & 15, source & 15
    return sum((2*c + (c != 0)) << shift for c, shift in ((red,0),(green,5),(blue,10)))


def inverse_color(color: int) -> int:
    channels = tuple((color >> shift) & 31 for shift in (0,5,10))
    require(all(c == 0 or c & 1 for c in channels), "non-oracle 5-bit color")
    return (channels[0] // 2 << 8) | (channels[1] // 2 << 4) | channels[2] // 2


def dim_native(color: int) -> int:
    result = (color & 0x739C) >> 1
    return result | (bool(result & 0x1E)) | (bool(result & 0x3C0) << 5) | (bool(result & 0x7800) << 10)


def arm_shape(word: int) -> bool:
    """Exact instruction classes used here; no ARMv5+ or coprocessor forms."""
    if word >> 28 == 15:
        return False
    body = word & 0x0FFFFFFF
    if body == 0x012FFF1E:  # BX LR only
        return True
    if body & 0x0E000000 == 0x0A000000:  # B/BL
        return True
    if body & 0x0FFF0000 in (0x092D0000, 0x08BD0000):  # stack STM/LDM
        return body & 0x8000 == 0 and body & 0xFFFF != 0
    if body & 0x0E000000 == 0x04000000:  # immediate single transfer
        return body & 0x00200000 == 0 or (body >> 16) & 15 == 13
    if body & 0x0E000090 == 0x00000090:  # immediate halfword transfer
        return body & 0x00400060 == 0x00400020
    if body & 0x0C000000 == 0:  # selected data-processing, no status/multiply
        op = (body >> 21) & 15
        if op not in (0, 2, 4, 8, 10, 12, 13, 14):
            return False
        if op in (8,10) and not body & 0x00100000:
            return False
        return bool(body & 0x02000000) or body & 0x10 == 0
    return False


def branch_target(word: int, raw: int) -> int:
    offset = word & 0xFFFFFF
    if offset & 0x800000:
        offset -= 0x1000000
    return 0x08000000 + raw + 8 + 4*offset


def decode_and_check(candidate: bytes) -> dict:
    dis = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    rows, count = [], 0
    for label, start, code_size, size, expected in CODE:
        blob = candidate[start:start+size]
        require(digest(blob) == expected, f"reviewed instruction/literal shape changed: {label}")
        instructions = list(dis.disasm(blob[:code_size], 0x08000000+start))
        require(len(instructions)*4 == code_size, f"incomplete instruction decode: {label}")
        literals = []
        for i in instructions:
            word = int.from_bytes(i.bytes, "little")
            require(arm_shape(word), f"instruction outside reviewed ARM7TDMI forms: {i.address:X} {i.mnemonic}")
            # Every immediate PC load must point inside this function's literal tail.
            if word & 0x0F7F0000 == 0x051F0000:
                offset = word & 0xFFF
                address = i.address+8+(offset if word & 0x00800000 else -offset)-0x08000000
                require(start+code_size <= address <= start+size-4 and address % 4 == 0, "literal outside owning pool")
                literals.append(struct.unpack_from("<I",candidate,address)[0])
        rows.append({"name": label, "entry": 0x08000000+start, "instructions": len(instructions), "literal_values": literals})
        count += len(instructions)
    return {"instructions": count, "functions": rows}


def verify_sources(sources: dict, candidate: bytes) -> dict:
    for key, expected in SOURCE_HASHES.items():
        require(digest(sources[key]) == expected, f"wrong original {key}")
    for key,start,end,expected in ORACLES:
        require(digest(sources[key][start:end]) == expected, f"source oracle changed {key}:{start:X}")
    s, g = sources["wsc15"], sources["gba"]
    # Source initializer seeds are immediate stores, parsed independently.
    x86 = Cs(CS_ARCH_X86, CS_MODE_16)
    stores = [i for i in x86.disasm(s[0x78368D:0x783707],0x78368D)
              if i.mnemonic == "mov" and i.op_str.startswith("word ptr [si],")]
    seeds = [int(i.op_str.split(", ")[1],0) for i in stores]
    require(len(seeds) == 19, "source seed population")
    target_seeds = list(struct.unpack_from("<19H",candidate,0x5C7300))
    require([inverse_color(c) for c in target_seeds] == seeds, "seed inverse mismatch")
    # Prove exact retail HUD assets without calling the converter.
    source_colors = struct.unpack_from("<16H",s,0x42FD60)
    native_colors = struct.unpack_from("<16H",g,0x1FD30)
    require(tuple(inverse_color(c) for c in native_colors) == source_colors, "HUD palette inverse mismatch")
    font_a, font_b = s[0x42FD80:0x42FFA0], g[0x1FD50:0x1FF70]
    for tile in range(17):
        for row in range(8):
            for column in range(8):
                packed = font_b[tile*32+row*4+column//2]
                pixel = (packed >> (4*(column%2))) & 15
                planes = font_a[tile*32+row*4:tile*32+row*4+4]
                require(pixel == sum(((v >> (7-column)) & 1) << p for p,v in enumerate(planes)), "HUD pixel inverse mismatch")
    require(font_b[-32:] == b"\xFF"*32, "HUD tile3FF must be solid color15")
    require(struct.unpack_from("<2H",s,0x77CD1C) == (448,432), "source Shoot dimensions")
    require(struct.unpack_from("<H",s,0x77DE94+22)[0] == 0x15AF, "Shoot bounds dispatch")
    require(struct.unpack_from("<H",s,0x783470+22)[0] == 0x21D, "Shoot palette initializer dispatch")
    require(struct.unpack_from("<H",s,0x78370E+22)[0] == 0x82E, "Shoot palette projector dispatch")
    require(struct.unpack_from("<H",s,0x7693AC+22)[0] == 0x2067, "Shoot stage-update dispatch")
    update_call = list(x86.disasm(s[0x76B034:0x76B037],0x76B034))
    require([(i.mnemonic,i.op_str) for i in update_call] == [("call","0x76b1db")], "Shoot-only palette-update callee")
    # Six source tables are contiguous but their logical widths differ.
    source_tables = list(struct.unpack_from("<202H",s,0x76B03B))
    native_tables = list(struct.unpack_from("<202H",candidate,0x586800))
    require([inverse_color(c) for c in native_tables] == source_tables, "palette table inverse mismatch")
    # Every valid four-counter state and either selection flag gets the same
    # new counters and selected source slice. Unchanged groups are retained.
    cases = 0
    for tick, a, b, c, alternate in itertools.product(range(8),range(10),range(8),range(7),range(2)):
        current = [tick,a,b,c]
        expected_counters = current.copy()
        expected_counters[0] = (tick+1) % 8
        selected = [None,None,None]
        base = 101*alternate
        if expected_counters[0] == 0:
            selected[0] = source_tables[base+2*a:base+2*a+6]
            expected_counters[1] = (a+1)%10
        elif expected_counters[0] & 1:
            selected[1] = source_tables[base+30+b:base+30+b+8]
            selected[2] = source_tables[base+45+8*c:base+45+8*c+5]
            expected_counters[2] = (b+1)%8
            expected_counters[3] = (c+1)%7
        # Separate native pointer arithmetic, read back through candidate ROM.
        native_counters = [(tick+1)&7,a,b,c]
        pointers = [None,None,None]
        table = 0x586800 + 0xCA*alternate
        if native_counters[0] == 0:
            pointers[0] = (table+4*a,6)
            native_counters[1] = a+1 if a<9 else 0
        elif native_counters[0]&1:
            pointers[1] = (table+0x3C+2*b,8)
            pointers[2] = (table+0x5A+16*c,5)
            native_counters[2] = (b+1)&7
            native_counters[3] = c+1 if c<6 else 0
        require(native_counters == expected_counters, "counter mismatch")
        for group, ref in zip(selected,pointers,strict=True):
            if ref is None:
                require(group is None, "changed group retention")
            else:
                pos,n = ref
                colors = struct.unpack_from(f"<{n}H",candidate,pos)
                require([inverse_color(v) for v in colors] == group, "selected pointer fails source slice")
        cases += 1
    # Dim happens after selecting the stored group: flag changes between update
    # and projection cannot redirect a pointer. Check all 4096 source colors.
    for value in range(4096):
        source_half = ((value & 0xEEE) >> 1)
        require(dim_native(native_color(value)) == native_color(source_half), "dim color mismatch")
    # All source stores of row11 cover these 35 palette cells, never row0/7/OBJ.
    destinations = [x for row in (0x10,0x30,0x50) for x in (row,row+2)]
    destinations += [row+2*k for row in (0x64,0x84,0xA4) for k in range(8)]
    destinations += list(range(0xC4,0xCE,2))
    return {"HUD_tiles":17, "HUD_pixels":1088, "HUD_font_sha256":digest(font_b),
            "HUD_color_words":16, "HUD_map_cells":[0x73FF]*4,
            "dimensions":[448,432], "initial_scroll":[112,0], "source_seed_colors":seeds,
            "palette_transition_cases":cases, "dim_color_cases":4096,
            "palette_write_offsets":destinations,
            "state_owner":[0x03003D30,0x03003D50],
            "irq_commercial_pair":[0x3BC801,0x080D0B24]}


def verify(before: bytes, candidate: bytes, sources: dict) -> dict:
    require(digest(before) == PREDECESSOR, "wrong lower-rules predecessor")
    require(digest(candidate) == OUTPUT and len(candidate) == len(before) == 0x800000, "wrong graphics artifact")
    code_report = decode_and_check(candidate)
    proof = verify_sources(sources,candidate)
    ranges = [(start,start+size) for _,start,_,size,_ in CODE] + [(0x5C7300,0x5C7326)]
    hooks = ((0x7FC34,0x5C6C00,0xE92D403F),(0xC4CC4,0x5C7100,0xE92D403F),
             (0x586400,0x5C6E00,0xE92D41FF),(0xC4BC0,0x5C7380,0xE92D4037))
    expected = bytearray(before)
    for start,end in ranges:
        require(before[start:end] == b"\xFF"*(end-start), "dirty expansion")
        expected[start:end] = candidate[start:end]
    for site,target,old in hooks:
        require(struct.unpack_from("<I",before,site)[0] == old, "wrong hook predecessor")
        word = struct.unpack_from("<I",candidate,site)[0]
        require(word >> 24 == 0xEA and branch_target(word,site) == 0x08000000+target, "wrong hook target")
        expected[site:site+4] = candidate[site:site+4]
    require(bytes(expected) == candidate, "full ROM diff outside approved spans")
    callers = {0x0803EE08:[],0x080C4BC0:[],0x080C4CC4:[],0x08586400:[]}
    pointer_refs = {target:[] for target in callers}
    for site in range(0,len(before)-3,4):
        word = struct.unpack_from("<I",before,site)[0]
        require(not 0x085C6800 <= word < 0x085C7800, "preexisting pointer to reserved range")
        if word in pointer_refs:
            pointer_refs[word].append(site+0x08000000)
        if word & 0x0E000000 == 0x0A000000:
            target = branch_target(word,site)
            require(not 0x085C6800 <= target < 0x085C7800, "preexisting branch to reserved range")
            if target in callers:
                callers[target].append(site+0x08000000)
    require(callers == {0x0803EE08:[0x080D1A2C],0x080C4BC0:[0x0803EE6C],
                        0x080C4CC4:[0x080D0C74,0x080D0EA0,0x080D11F4,0x080D120C,0x080D1220],
                        0x08586400:[0x08586248]}, "palette/graphics direct caller population changed")
    require(not any(pointer_refs.values()), "new palette/graphics function-pointer consumer")
    return {"schema":1, "output_sha256":OUTPUT, "machine_code":code_report,
            "source_contract":proof, "actual_changed_bytes":sum(a!=b for a,b in zip(before,candidate,strict=True)),
            "full_ROM_expected_writes_exact":True, "preexisting_inbound_scan_pass":True,
            "palette_lifetime_direct_callers":{f"{key:08X}":value for key,value in callers.items()},
            "claim_scope":"static graphics/palette/IRQ proof only; no emulator, save, or runtime acceptance"}


def main() -> int:
    p=argparse.ArgumentParser()
    for key in ("before","candidate","gba","wsc10","wsc15"):
        p.add_argument(key,type=pathlib.Path)
    p.add_argument("--report",type=pathlib.Path)
    a=p.parse_args()
    report=verify(a.before.read_bytes(),a.candidate.read_bytes(),{k:getattr(a,k).read_bytes() for k in SOURCE_HASHES})
    if a.report:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"[shoot-graphics-verify] PASS {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
