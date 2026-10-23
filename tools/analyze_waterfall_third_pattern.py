#!/usr/bin/env python3
"""Read-only proof of Waterfall's omitted third configuration and callback.

Expected values come from source/commercial ROMs, not a build manifest.
No emulator, save, or unbounded service execution is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

BASE = 0x08000000
PARENT = "DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
CS = 0x740900
RECORD, ENTRY, SLOT = 0x584CE8, 0x629600, 0x62967C
RESERVATIONS = ((RECORD, RECORD + 20), (ENTRY, SLOT + 4))
PHASE2 = ((0x5846F4, 0xE2451001, 0xE1A01005),
          (0x584704, 0xE2471001, 0xE1A01007))
WRITE_SPANS = RESERVATIONS + tuple((at, at+4) for at, _, _ in PHASE2)
SOURCE_GUARDS = (
    (0x7442A9, 0x744357, "0E33FE33C1AA31B29E583A28B1B8A01534717193EB48C73560F711A82824D428", "configuration consumer"),
    (0x7446FB, 0x7447E0, "426AC033F0303F6EDEF7CF08DBC571DB4E050E19DF8AACD051195B29882E3FAC", "mode1 family"),
    (0x7448CA, 0x7449AF, "47D69D4A0C0E60C0B0F8C862EF5027D56854887454E49D3F8D82ACCD00317226", "mode3 family"),
    (0x7450A1, 0x7450D1, "52910441C612BCE1FC38719B3B9F33F5E61BAA8570C8D87A5A56B69685DFEC13", "three source records"),
    (0x74527D, 0x74529D, "ED6F243B4AEFFD1B043EEA154ABF864673FC7B1BC4B8F401BEC1D962CAAC6633", "pattern payload"),
    (0x751998, 0x7519C9, "51A08E5CD08209B9E95D7D90C228A8DADE6E79769F30468F5521DF743529D4A5", "source sine consumer"),
    (0x76ABCF, 0x76ACF6, "F67A930A50A5B19F33D4673242FD1DC5AC23E8299A41FA7E8C236BEFD1FCD8D0", "hazard consumer"),
)
NATIVE_GUARDS = (
    (0x36D77C, 0x36D8B4, "79F89EC8AADF076AEE76631372824913ADB1EDE38FC92E54775E0AB8BB53C335", "native selector2 consumer"),
    (0x585200, 0x585390, "0E1DA4E47BBA90A2711BCE9F022A65FBBAA58A5DBBABE67D5B3B0B80AB733FCA", "retained mode1 constructor and continuation"),
    (0x36D8B4, 0x36D9C8, "FBB854E117095D1F1E0394F5A664603B641596246031863E549FD3B27A23A289", "commercial service oracle"),
    (0x36D750, 0x36D77C, "5982EEBEF11CCCEC5D15E37E436DE6F1F127CD3532082FA40251A4B3E3CECACD", "native destruction service"),
    (0x12348, 0x12360, "BD7BCA6B2C465574E8D102A5A6E22C8AFB0F1C22F947C2622664C1A2F8ECA8CF", "native sine consumer"),
    (0x584600, 0x584754, "3CA75DB08CC5763E96F8ECEDDE5E149A84F523E00707CDC78C39E3EDE7AA29B5", "existing hazard consumer"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u16(data, at):
    return struct.unpack_from("<H", data, at)[0]


def u32(data, at):
    return struct.unpack_from("<I", data, at)[0]


def occurrences(data, value):
    result, at = [], data.find(value)
    while at >= 0:
        result.append(at)
        at = data.find(value, at + 1)
    return result


def branch_target(at, word):
    delta = word & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return BASE + at + 8 + 4 * delta


def no_inbound(data, spans=RESERVATIONS):
    """Conservative whole-ROM static reservation ownership, including mirrors."""
    ranges = [(base + a, base + b) for base in (BASE, 0x0A000000, 0x0C000000)
              for a, b in spans]
    def inside(v):
        return any(a <= v < b for a, b in ranges)
    matches = []
    for shift in range(4):
        stop = len(data) - ((len(data) - shift) % 4)
        for n, (word,) in enumerate(struct.iter_unpack("<I", data[shift:stop])):
            if inside(word):
                matches.append(("pointer", shift + n * 4, word))
    for n, (word,) in enumerate(struct.iter_unpack("<I", data)):
        at, pc = n * 4, BASE + n * 4 + 8
        if word & 0x0E000000 == 0x0A000000:
            target = branch_target(at, word)
            if inside(target):
                matches.append(("ARM branch", at, target))
        if word & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            target = pc + (word & 0xFFF) * (1 if word & 0x800000 else -1)
            if inside(target):
                matches.append(("ARM literal", at, target))
        if word & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            value, rotate = word & 255, ((word >> 8) & 15) * 2
            if rotate:
                value = ((value >> rotate) | (value << (32 - rotate))) & 0xFFFFFFFF
            target = pc + (value if word & 0x01E00000 == 0x00800000 else -value)
            if inside(target):
                matches.append(("ARM ADR", at, target))
    for n, (word,) in enumerate(struct.iter_unpack("<H", data)):
        at, pc = n * 2, BASE + n * 2 + 4
        if word & 0xF800 in (0x4800, 0xA000):
            target = (pc & ~3) + (word & 255) * 4
            if inside(target):
                matches.append(("Thumb literal/ADR", at, target))
        if word & 0xF800 == 0xE000:
            imm = word & 0x7FF
            target = pc + 2 * (imm - (0x800 if imm & 0x400 else 0))
            if inside(target):
                matches.append(("Thumb B", at, target))
        if word & 0xF000 == 0xD000 and word & 0x0F00 < 0x0E00:
            imm = word & 255
            target = pc + 2 * (imm - (256 if imm & 128 else 0))
            if inside(target):
                matches.append(("Thumb conditional B", at, target))
        if word & 0xF800 == 0xF000 and at + 4 <= len(data):
            tail = u16(data, at + 2)
            if tail & 0xF800 in (0xF800, 0xE800):
                imm = word & 0x7FF
                target = pc + ((imm - (0x800 if imm & 0x400 else 0)) << 12) + ((tail & 0x7FF) << 1)
                if tail & 0xF800 == 0xE800:
                    target &= ~3
                if inside(target):
                    matches.append(("Thumb BL/BLX", at, target))
    # E310 is the upper halfword of guarded ARM TST r0,#0x200 at5846D0.
    # Decoding that interior halfword as Thumb B spuriously targets584CF6.
    # The whole surrounding ARM routine is separately hash-guarded by proof().
    classified=[]
    false_thumb=("Thumb B",0x5846D2,0x08584CF6)
    if false_thumb in matches:
        need(u32(data,0x5846D0)==0xE3100C02,"classified ARM instruction containing Thumb-like halfword")
        matches.remove(false_thumb)
        classified.append(dict(kind="Thumb-looking ARM interior",site="085846D2",
                               actual_instruction="085846D0: TST r0,#0x200",word="E3100C02"))
    need(not matches, f"pre-existing ownership of proposed writes: {matches[:12]}")
    return {"all_alignment_mirrored_pointers": True, "arm_thumb_code_references": True,
            "inbound_matches": [], "classified_instruction_interiors":classified,
            "ranges": [[f"{a:06X}", f"{b:06X}"] for a, b in spans]}


def proof(current, gba, old, source):
    guards = []
    for label, data, specs in (("source", source, SOURCE_GUARDS), ("native", current, NATIVE_GUARDS)):
        for start, end, expected, purpose in specs:
            need(sha(data[start:end]) == expected, f"{label} {purpose} exact instructions")
            guards.append(dict(rom=label, start=f"{start:06X}", end=f"{end:06X}", sha256=expected, purpose=purpose))
    need(current[0x36D77C:0x36D9C8] == gba[0x36D77C:0x36D9C8], "commercial native consumers retained")
    # Commercial metadata conversion, all eight retail stage pairs.
    oracle = []
    for stage in range(8):
        sh, sp = struct.unpack_from("<HH", source, 0x744F2D + 4 * stage)
        nh, np = struct.unpack_from("<II", gba, 0x36D38C + 8 * stage)
        need(sh == nh, "retail stage table header")
        for index in range(2):
            s, n = CS + sp + index * 16, np - BASE + index * 20
            need(gba[n:n+14] == source[s:s+14] and gba[n+14:n+16] == bytes(2), "sixteen retail record conversion oracle")
            need(BASE <= u32(gba, n+16) < BASE + len(gba), "retail callback-slot pointer")
            oracle.append(dict(stage=stage, index=index, source=f"{s:06X}", native=f"{n+BASE:08X}"))
    need(struct.unpack_from("<HH", source, 0x744F51) == (3, 0x47A1), "source Waterfall config row")
    need(struct.unpack_from("<HH", source, 0x744F55) == (2, 0x47D1), "next config fixes three-record boundary")
    need(struct.unpack_from("<BBH", source, 0x745151) == (3, 4, 0x497D), "source pattern initial modulus and cycle length")
    need(struct.unpack_from("<HHI", current, 0x584B48) == (3, 4, 0x08584B80), "native Waterfall pattern row")
    need(current[0x584B80:0x584BA0] == source[0x74527D:0x74529D], "all eight retained pattern pairs")
    patterns = list(struct.iter_unpack("<HH", source[0x74527D:0x74529D]))
    need(patterns == [(1,10),(0,10),(2,10),(1,10),(0,10),(2,10),(1,10),(2,10)], "source selectors and timing values")
    need(struct.unpack_from("<II", current, 0x584C48) == (3, 0x08584CC0), "current config owner")
    records = []
    for index, (slot, callback) in enumerate(((0x481F,0x3DFB),(0x4821,0x3EE0),(0x4823,0x3FCA))):
        s, n = 0x7450A1 + index * 16, 0x584CC0 + index * 20
        need(u16(source, s+14) == slot and u16(source, CS+slot) == callback, "source callback graph")
        if index < 2:
            need(current[n:n+14] == source[s:s+14] and current[n+14:n+16] == bytes(2), "existing two records preserved")
            need(u32(current,n+16) == 0x08584D88 + index*4, "existing callback slots")
            need(u32(current,0x584D88+index*4) == (0x08585200,0x08585500)[index], "existing callback constructors")
        else:
            need(current[n:n+20] == b"\xff"*20, "actual missing third config is erased")
        records.append(dict(index=index, source=f"{s:06X}", native=f"{n+BASE:08X}", source_hex=source[s:s+16].hex(), callback=f"4090:{callback:04X}", missing=index==2))
    # Exact source mode1 -> mode3 correspondence, no unrelated differences.
    mode1, mode3 = source[0x7446FB:0x7447E0], source[0x7448CA:0x7449AF]
    changes = ((0x10,1,3),(0x3A,0x40,0xC0),(0x48,0x4A,0x19),(0x49,0x3E,0x40),(0x62,0x9E,0x6D),(0x63,0x3E,0x40))
    normalized = bytearray(mode1)
    for off, before, after in changes:
        need(normalized[off] == before and mode3[off] == after, "specific source mode/phase/continuation change")
        normalized[off] = after
    need(bytes(normalized) == mode3, "entire229-byte source family equivalence")
    # Old/new commercial callback proves all four service correspondence routes.
    old_code, new_code = old[0x393F11:0x393FB6], source[0x744357:0x7443FC]
    need(sha(old_code) == "408297B5D22E7FF2EB837ABB950E13816C9BB10DACD7E61B85606940BD5376E3", "old commercial source oracle")
    need(sha(new_code) == "38B8678F82F13BF5DD5C5D95E93C8491E7E587153ECFD2127D63093F26B45CEB", "new commercial source oracle")
    relocations = [(7,bytes.fromhex('eb24b296'),bytes.fromhex('cb24ff4f')),
                   (0x3A,bytes.fromhex('5238'),bytes.fromhex('983a')),
                   (0x3F,bytes.fromhex('7090'),bytes.fromhex('9040')),
                   (0x45,bytes.fromhex('3c1ab296'),bytes.fromhex('a819ff4f')),
                   (0x66,bytes.fromhex('8228b296'),bytes.fromhex('6228ff4f')),
                   (0x7B,bytes.fromhex('8406'),bytes.fromhex('0007')),
                   (0x80,bytes.fromhex('8406'),bytes.fromhex('0007')),
                   (0x85,bytes.fromhex('8606'),bytes.fromhex('0207')),
                   (0x8A,bytes.fromhex('48377090'),bytes.fromhex('8e399040')),
                   (0x9A,bytes.fromhex('8206'),bytes.fromhex('fe06'))]
    normalized = bytearray(old_code)
    for at, before, after in relocations:
        need(normalized[at:at+len(before)] == before, "old service/global relocation")
        normalized[at:at+len(after)] = after
    need(bytes(normalized) == new_code, "commercial callback equality after ten explicit relocations")
    sine = source[0x7519C9:0x751BC9]
    need(sine == gba[0x12360:0x12560] == current[0x12360:0x12560], "all256 signed sine values")
    need(sha(sine) == "9287394FA9384EEAAA175244A8CB0A9AF4B0FF78D0BB0F58869173D342410D30", "sine identity")
    pairs = struct.unpack_from("<6H", source, 0x76ABC3)
    need(pairs == (5,7,1,7,1,3) and current[0x584800:0x58480C] == source[0x76ABC3:0x76ABCF], "all three hazard pairs")
    need(u32(current,0x584744) == 0x0300256A and u32(current,0x58538C) == 0x0300256A, "hazard owner distinct from phase/palette")
    need(u32(current,0x584750) == 0x08584800, "hazard selected-data base")
    need(current[0x1369C:0x137AC] == gba[0x1369C:0x137AC], "commercial entity allocation and ID service retained")
    need(u32(current,0x136E8)==0x03001C68 and u32(current,0x136E4)==0x03001D68,
         "entity allocation base and next live owner")
    need(u32(current,0x136AC)==0xE3A09010 and
         tuple(u32(current,at) for at in range(0x136B0,0x136C0,4))==(0xE488A004,)*4,
         "16 iterations of four-word clearing equals32 eight-byte records")
    need(u32(current,0x58467C)==0xE2451001,"phase1 correctly retains ID-minus-one read")
    for at, expected, _ in PHASE2:
        need(u32(current,at)==expected,"existing phase2 subtract-one discrepancy")
    bounds=[]
    for mode,(left,right) in enumerate(zip(pairs[::2],pairs[1::2]),1):
        rows=(left,right)
        remaining=[8+k for k in range(1,4) if k!=mode]
        need(all(0<=row<32 for row in rows) and all(1<=entity<=32 for entity in remaining),
             "all-mode successor clear and remaining entity bounds")
        bounds.append(dict(mode=mode,first_ids=[left,right],successor_ids=[left+1,right+1],
                           phase2_row_indices=list(rows),remaining_ids=remaining))
    # References to this source family's entry/slot are bounded to its bank.
    need(occurrences(source[CS:CS+0x10000],bytes.fromhex('ca3f')) == [0x4823], "sole same-bank mode3 near pointer")
    need(occurrences(source[CS:CS+0x10000],bytes.fromhex('2348')) == [0x47CF], "sole same-bank third callback-slot pointer")
    need(not occurrences(source,bytes.fromhex('ca3f9040')), "no direct source far-pointer/call aliases")
    native_calls = {}
    for target in (0x08585200,0x08585274,0x08585310):
        native_calls[f"{target:08X}"] = [f"{BASE+at:08X}" for at in range(0,len(current)-3,4)
            if u32(current,at)&0x0E000000 == 0x0A000000 and branch_target(at,u32(current,at)) == target]
    need(native_calls == {'08585200':[], '08585274':['08585268'], '08585310':[]}, "retained direct continuation callers")
    x86, arm = Cs(CS_ARCH_X86,CS_MODE_16), Cs(CS_ARCH_ARM,CS_MODE_ARM)
    def decoded(decoder,data,start,end,base=0):
        rows=list(decoder.disasm(data[start:end],base+start))
        need(sum(i.size for i in rows)==end-start,"complete bounded instruction decoding")
        return [dict(address=f"{i.address:08X}",op=i.mnemonic,args=i.op_str)for i in rows]
    return dict(schema=1, status="PASS", scope="Third-pattern route and bounded native continuation reuse; no whole-hazard/service/runtime claim",
                guards=guards, retail_records=oracle, records=records, patterns=patterns,
                reachable_pattern_indices=[0,1,2,3], reachable_selectors=[1,0,2,1],
                source_changes=[dict(offset=f"{o:02X}",before=a,after=b)for o,a,b in changes],
                source_mode3=decoded(x86,source,0x7448CA,0x7449AF),
                native_common=decoded(arm,current,0x585274,0x58538C,BASE),
                service_mapping={"4FFF:24CB":"08012874","4FFF:2862":"08012A84","4FFF:19A8":"08012348","4090:398E":"0836D750"},
                sine_entries=256, sine_sha256=sha(sine), native_direct_calls=native_calls,
                mode3_downstream=dict(owner="0300256A",admitted=[1,2,3],pair=[1,3],successors=[2,4],remaining=[9,10],palette_owner="03003D30",display_phase_owner="03002568",
                    existing_phase2_difference="Source clears ID-indexed successor rows; existing native subtracts1. Two flags-neutral MOV corrections restore all3 source row selections.",
                    all_mode_bounds=bounds,entity_owner=["03001C68","03001D68"],entity_rows=32),
                proposed_writes=[[f"{s:06X}",f"{e:06X}"]for s,e in WRITE_SPANS])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("current","gba","old","source","output"):
        parser.add_argument(name,type=Path)
    args=parser.parse_args()
    need(args.current.suffix.lower()=='.gba' and args.gba.suffix.lower()=='.gba' and
         args.old.suffix.lower()=='.wsc' and args.source.suffix.lower()=='.wsc',
         "ROM-only input extensions checked before reading")
    need(args.output.suffix.lower()=='.json' and args.output.resolve() not in
         {getattr(args,k).resolve() for k in ('current','gba','old','source')},"distinct JSON report output")
    data=[getattr(args,k).read_bytes() for k in ("current","gba","old","source")]
    need(tuple(map(sha,data))==(PARENT,GBA,OLD,NEW),"four exact input ROM identities")
    report=proof(*data)
    report["input_sha256"]=list(map(sha,data))
    for s,e in RESERVATIONS:
        need(data[0][s:e]==b'\xff'*(e-s),"two exact FF reservations")
    report["reservation"]=no_inbound(data[0],WRITE_SPANS)
    cases=[]
    for which,at,label in [(3,0x7450CF,"third slot"),(3,0x745123,"third callback"),
                         (3,0x745285,"selector2"),(3,0x7448DA,"mode3 immediate"),
                         (3,0x744904,"phaseC0"),(3,0x74492C,"exit continuation"),
                         (3,0x74496E,"signed exit boundary"),(3,0x7519C9,"source sine"),
                         (3,0x76ABCB,"mode3 hazard pair"),(2,0x393F17,"old service oracle"),
                         (0,0x36D7CC,"native record stride"),(0,0x36D85C,"actual callback store"),
                         (0,0x5852FC,"shared decrement"),(0,0x58531C,"shared signed exit"),
                         (0,0x12360,"native sine"),(0,0x584CE8,"missing record ownership"),
                         (0,0x5846F4,"phase2 first row"),(0,0x584704,"phase2 second row"),
                         (0,0x136AC,"entity allocation count")]:
        changed=bytearray(data[which]);changed[at]^=1;inputs=list(data);inputs[which]=bytes(changed)
        try:
            proof(*inputs)
        except ValueError as exc:
            cases.append(dict(name=label,rejected=True,reason=str(exc)))
        else:
            raise ValueError(f"negative was accepted: {label}")
    report["negative_controls"]=cases
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="PASS",report_sha256=sha(args.output.read_bytes()),negative_controls=len(cases))))


if __name__=="__main__":
    main()
