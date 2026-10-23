#!/usr/bin/env python3
"""Independent result-pose routing proof from five explicit ROM inputs.

No producer, analyzer, generated manifest, target execution or save supplies
expected data. Source pair tables, actual native consumers, selected animation
graphs and exact data-only ownership are checked separately.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

BEFORE = "A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61"
AFTER = "DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, TABLE, END = 0x08000000, 0x629480, 0x6294C0
ORIGINAL = (0x89774, 0x89790)
SOURCE_OLD, SOURCE_NEW = (0x3B5D7C, 0x3B5D96), (0x7771C0, 0x7771E0)
OLD_CS, NEW_CS = 0x3B5AD0, 0x776F10
# Each pair is (low-byte literal, actual reader); the high-byte pair is +4/+8.
PAIRS = ((0, 0x8A418, 0x8A014), (1, 0x8A420, 0x8A030),
         (0, 0x8A43C, 0x8A12C), (1, 0x8A444, 0x8A148),
         (0, 0x8A44C, 0x8A174), (1, 0x8A454, 0x8A190))
SOURCE_READERS = ((0x3B6281, 0x7776B4), (0x3B628E, 0x7776C1),
                  (0x3B6316, 0x777749), (0x3B6323, 0x777756),
                  (0x3B6345, 0x777778), (0x3B6352, 0x777785))
EVENT_COUNTS = (115, 134, 105, 119, 132, 112, 121, 112, 134, 120, 112, 114, 131, 115, 120)
FRAME_COUNTS = (104, 53, 56, 77, 133, 98, 62, 90, 69, 66, 98, 72, 168, 48, 58)
MAX_PARTS = (22, 26, 26, 17, 26, 26, 20, 26, 26, 23, 26, 22, 19, 26, 18)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data) - at, "bounded ROM extent")
    return bytes(data[at:at + size])


def u(data, at):
    return struct.unpack("<I", cut(data, at, 4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data, at, 2))[0]


def ptr(data, at, size=1):
    raw = u(data, at) - BASE
    cut(data, raw, size)
    return raw


def banked(data, offset, segment, bank):
    address = segment * 16 + offset
    need(0x20000 <= address < 0x30000 and 0x80 <= bank <= 255, "source resource window")
    return (bank & (len(data) // 65536 - 1)) * 65536 + address - 0x20000


def far(data, at):
    return banked(data, *struct.unpack("<3H", cut(data, at, 6)))


def sequence(data, at, expected, arm=True, size=None):
    size = len(expected) * 4 if size is None else size
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    rows = list(decoder.disasm(cut(data, at, size), at + (BASE if arm else 0)))
    need(sum(row.size for row in rows) == size and
         [f"{row.mnemonic} {row.op_str}".strip() for row in rows] == expected,
         f"actual {'ARM' if arm else 'x86'} instruction contract {at:X}")


def source_tables(gba, old, new):
    need(len(gba) == len(old) == 0x400000 and len(new) == 0x800000, "original input extents")
    result = []
    added = (bytes.fromhex("6F706E6F7475"), bytes.fromhex("717270717677"))
    for kind in range(2):
        a, b, native = cut(old, SOURCE_OLD[kind], 26), cut(new, SOURCE_NEW[kind], 32), cut(gba, ORIGINAL[kind], 28)
        need(a[:24] == b[:24] == native[:24], "all twelve paired retail/source row identities")
        need(a[24:] == native[24:26] == b[30:] == bytes(2), "explicit terminal zero pair retained")
        need(native[26:] == bytes(2), "native table alignment padding")
        need(b[24:30] == added[kind], "three explicit added-character source pairs")
        result.append(b)
    for data, end in ((old, 0x3B5DB0), (new, 0x777200)):
        sequence(data, end, ["push bp", "mov bp, sp", "add sp, -0xa"], False, 6)
    for (kind, _, _), (oa, na) in zip(PAIRS, SOURCE_READERS):
        for data, at, table, cs in ((old, oa, SOURCE_OLD[kind], OLD_CS), (new, na, SOURCE_NEW[kind], NEW_CS)):
            displacement = table - cs
            sequence(data, at, [f"mov cl, byte ptr cs:[bx + 0x{displacement:x}]",
                               f"mov ch, byte ptr cs:[bx + 0x{displacement + 1:x}]"], False, 10)
    for data, at in ((old, 0x3B6275), (new, 0x7776A8)):
        sequence(data, at, ["mov bx, word ptr [bp - 6]", "add bx, bx", "test word ptr [bp - 0xa], 0x60"], False, 10)
    for data, at in ((old, 0x3B6303), (new, 0x777736)):
        sequence(data, at, ["mov bx, word ptr [bp - 8]", "add bx, bx", "test word ptr [bp - 0xa], 0x40"], False, 10)
    return result


def literal_site(data, at):
    word = u(data, at)
    need(word >> 28 != 15 and word & 0x0F7F0000 == 0x051F0000, "ARM word literal reader")
    return at + 8 + (1 if word & 0x800000 else -1) * (word & 4095)


def consumers(before, after, gba):
    # Complete original constructor/callback region, including both participant
    # branches. The only differences permitted here are twelve literal words.
    need(cut(before, 0x897AC, 0x8AD00 - 0x897AC) == cut(gba, 0x897AC, 0x8AD00 - 0x897AC), "complete original result constructor and callbacks")
    spans = ((0x127B4, 0x12874), (0x12874, 0x12BBC), (0x12C58, 0x12DBC), (0x1F3A8, 0x1F4A0))
    for start, end in spans:
        need(cut(before, start, end-start) == cut(after, start, end-start) == cut(gba, start, end-start), "retained native initializer/setter/animation/renderer/loader")
    for kind, site, reader in PAIRS:
        for high in range(2):
            at, address = reader + high * 8, site + high * 4
            need(literal_site(after, at) == address and (u(after, at) >> 12 & 15) == 8, "actual r8 literal consumer")
            need(u(before, address) == BASE + ORIGINAL[kind] + high and u(after, address) == BASE + TABLE + kind * 32 + high, "actual byte-selector alias redirect")
        sequence(after, reader + 4, ["ldrb r2, [r1, r8]"])
        sequence(after, reader + 12, ["ldrb sb, [r1, r8]", "lsls sb, sb, #8", "orrs r2, r2, sb"])
    for at in (0x89FFC, 0x8A104):
        sequence(after, at, ["ldrh r1, [r8]", "adds r1, r1, r1"])
    for at in (0x8A048, 0x8A1AC):
        sequence(after, at, ["subs r1, r1, r1", "strh r1, [r5, #8]", "mov r1, r2", "ands r1, r1, #0xff",
            "strh r1, [r5, #4]", "mov r1, r2", "lsrs r1, r1, #8", "ands r1, r1, #0xff", "strh r1, [r5, #6]"])
    sequence(after, 0x1F3B0, ["ldr r8, [pc, #0xe8]", "add r1, r8, r1, lsl #5"])
    need(u(before, 0x1F4A0) == u(after, 0x1F4A0) == BASE + 0x4A80F8 and
         u(gba, 0x1F4A0) == BASE + 0xD3FB8, "existing base-only fifteen-character resource group relocation retained")
    sequence(after, 0x8A0A8, ["bl #0x801f3a8"])
    sequence(after, 0x8A20C, ["bl #0x801f3a8"])
    sequence(after, 0x12828, ["ldrh r8, [r4, #0xe]", "orr r3, r3, r8", "strh r3, [r5, #8]"])
    sequence(after, 0x12C7C, ["ldr r4, [r5, #0x20]", "ldrh sl, [r5, #0x1a]", "add r4, r4, sl, lsl #4",
        "ldrh r3, [r4, #4]", "ldr r4, [r5, #0x48]", "ldr fp, [r4, #4]", "ldrh r1, [r5, #8]",
        "tst r1, #2", "addne fp, fp, r3, lsl #3", "ldr fp, [fp, #4]"])
    sequence(after, 0x12D50, ["ldrb r3, [sl]", "add r3, fp, r3, lsl #5"])
    return dict(pair_reads=6, literal_reads=12, id_stride=2, resource_group=BASE+0x4A80F8,
        resource_variant="base only", pair_state_offsets=[4,6], handoff_latch_offset=8,
        terminal_pair="Stored 00/00 is copied arithmetically; no sentinel comparison or ID15 resource meaning is inferred.",
        preserved_services=[dict(start=a,end=b,sha256=sha(after[a:b])) for a,b in spans])


def phase_contract(after, gba):
    need(cut(after, 0x8A94C, 0x8ABE8-0x8A94C) == cut(gba, 0x8A94C, 0x8ABE8-0x8A94C), "complete original result pose callback chain")
    sequence(after, 0x8A998, ["ldrh r8, [r1]", "tst r8, #0x4000", "beq #0x808a9b4", "mov r2, #5", "mov r3, #4",
        "mov r1, #0", "b #0x808a9b8", "ldrh r1, [r4, #4]", "stmdb sp!, {r5}", "stmdb sp!, {fp}", "stmdb sp!, {r1}",
        "bl #0x8012874", "add sp, sp, #0xc", "mov r4, r0", "mov sb, #0xde", "strh sb, [r4, #2]",
        "ldr r8, [pc, #0x4c]", "bl #0x8012008"])
    need(u(after, 0x8AA28) == u(after, 0x8ABE4) == 0x03004738 and u(after, 0x8AA2C) == BASE+0x8AA30, "draw state owner and installed continuation")
    sequence(after, 0x8AA44, ["mov r0, #1", "stmdb sp!, {r1}", "stmdb sp!, {fp}", "stmdb sp!, {r0}",
        "bl #0x8012a84", "add sp, sp, #0xc", "ldr r4, [pc, #0x180]", "ldrh r8, [r4]", "tst r8, #0x4000",
        "bne #0x808aaa8", "ldrh r2, [r5, #8]", "orrs r2, r2, r2", "bne #0x808aaa8", "ldrh r8, [r1, #0xa]",
        "tst r8, #0x2000", "beq #0x808aaa8", "ldrh r8, [r5, #8]", "adds r8, r8, #1", "strh r8, [r5, #8]",
        "ldrh r2, [r5, #6]", "stmdb sp!, {r1}", "stmdb sp!, {fp}", "stmdb sp!, {r2}", "bl #0x8012874", "add sp, sp, #0xc"])
    sequence(after, 0x128A0, ["ldr r2, [r1]", "ldr r1, [r1, #4]", "strh r2, [r5, #0x1c]", "str r1, [r5, #0x20]",
        "str r1, [r5, #0x24]", "mov r0, #0", "strh r0, [r5, #0x1a]", "ldrb r0, [r1]", "strb r0, [r5, #0x17]",
        "ldrh r0, [r1, #6]", "strh r0, [r5, #0xa]"])
    sequence(after, 0x12A90, ["ldrh r0, [r5, #0xa]", "ands r0, r0, #0x2000", "bne #0x8012bb0", "ldr r0, [sp, #0x1c]",
        "ldrsb r8, [r5, #0x17]", "subs r8, r8, r0", "strb r8, [r5, #0x17]", "bpl #0x8012bb0",
        "ldrsh r3, [r5, #0x1c]", "ldrh r8, [r5, #0x1a]", "add r8, r8, #1", "strh r8, [r5, #0x1a]", "cmp r8, r3",
        "bmi #0x8012b08", "ldrh r8, [r5, #0xa]", "tst r8, #1", "bne #0x8012af0", "ldrh r8, [r5, #0x1a]",
        "sub r8, r8, #1", "strh r8, [r5, #0x1a]", "ldrh r8, [r5, #0xa]", "orr r8, r8, #0x2000", "strh r8, [r5, #0xa]"])
    sequence(after, 0x12B3C, ["ldrb r0, [r1]", "ldrb r8, [r5, #0x17]", "add r8, r8, r0", "strb r8, [r5, #0x17]"])
    sequence(after, 0x12B6C, ["ldrh r8, [r5, #0xa]", "ldr sb, [pc, #0x40]", "and r8, r8, sb", "orr r8, r8, r0", "strh r8, [r5, #0xa]"])
    need(u(after, 0x12BB8) == 0x101, "retained animation flag mask")
    return dict(first_callback=BASE+0x8A94C, continuation=BASE+0x8AA30, event_setter=BASE+0x12874,
        timer=222, completion_flag=0x2000, draw_flag=0x4000, draw_owner=0x03004738,
        first_argument="task+4 unless draw bit4000, when event0 is passed at [sp] to0808A9C4",
        handoff="After delta1 animation update, iff no draw4000, latch task+8==0 and completion2000; increment latch and pass task+6 at0808AAA0.",
        zero_pair="No special zero check in loading, storing, or event setter.")


def packed(data):
    result = bytearray()
    for at in range(0, len(data), 4):
        row = [sum(((data[at+p] >> (7-x)) & 1) << p for p in range(4)) for x in range(8)]
        result.extend(row[x] | row[x+1] << 4 for x in range(0,8,2))
    return bytes(result)


def animation(durations, flags):
    """Bounded static state recurrence derived from012A84; not target execution."""
    need(len(durations) == len(flags) > 0 and all(0 <= d <= 127 for d in durations), "bounded signed-byte animation durations")
    frame, timer, state_flags, steps = 0, durations[0], flags[0], 0
    seen, visited = set(), {0}
    while steps < 65536:
        state = (frame,timer,state_flags)
        if state_flags & 0x2000:
            return dict(kind="complete",steps=steps,visited=len(visited),frames=len(flags))
        if state in seen:
            return dict(kind="cycle",steps=steps,visited=len(visited),frames=len(flags))
        seen.add(state); steps += 1
        signed = timer if timer < 128 else timer - 256
        remainder = signed - 1
        timer = remainder & 255
        if remainder >= 0:
            continue
        frame += 1
        if frame == len(flags):
            if not state_flags & 1:
                frame -= 1; state_flags |= 0x2000
                continue
            frame = 0
        timer = (timer + durations[frame]) & 255
        state_flags = (state_flags & 0x101) | flags[frame]
        visited.add(frame)
    raise ValueError("animation recurrence bound exceeded")


def population(after, new, tables, only_id=None):
    resources, atlases, events_total, frame_total = [], {}, 0, 0
    for ident in (range(15) if only_id is None else [only_id]):
        source_p0, source_p1 = far(new,0x740000+32*ident), far(new,0x740006+32*ident)
        p0, p1 = ptr(after,0x4A80F8+32*ident), ptr(after,0x4A80FC+32*ident)
        need(u(new,source_p1)==4 and u(new,source_p0)==16, "direct source resource headers")
        first = h(new,source_p1+6)
        need(first>4 and (first-4)%8==0, "source P1 exact event boundary")
        count=(first-4)//8
        need(count==EVENT_COUNTS[ident], "complete source event population")
        et=ptr(after,p1,count*16)
        need(et==p1+8 and u(after,p1+4)==0 and ptr(after,et+4)==et+count*16, "same complete native event boundary")
        lt=ptr(after,p0); first_parts=ptr(after,lt+4)
        need(lt==p0+16 and (first_parts-lt)%8==0, "native P0 layout boundary")
        layouts=(first_parts-lt)//8
        need(0<layouts<1024 and h(new,source_p0+18)==16+4*layouts, "same exact source/native P0 layout population")
        need(h(after,p0+14)==h(new,source_p0+14), "source/native P0 rendering flags")
        nd=ptr(after,p0+4)
        sd=banked(new,0,h(new,source_p0+4),h(new,source_p0+6))
        selected=[0,1,0x51,0x56,*tables[0][2*ident:2*ident+2],*tables[1][2*ident:2*ident+2]]
        need(len(set(selected))==8, "eight distinct selected events")
        result=[]; local_frames=maximum=0
        for event in selected:
            need(event<count, "selected event inside complete native/source population")
            source_row=source_p1+4+8*event; native_row=et+16*event
            frames=h(new,source_row); sc=source_p1+h(new,source_row+2)
            need(0<frames<=255 and u(after,native_row)==frames, "selected complete frame count")
            nc=ptr(after,native_row+4,frames*16)
            cut(new,sc,frames*12)
            row=dict(event=event,frames=frames,native_commands=nc,source_commands=sc,layouts=[],atlas_indices=[],durations=[],flags=[],part_counts=[])
            for j in range(frames):
                a,b=nc+16*j,sc+12*j
                need(cut(after,a+2,6)==cut(new,b+2,6), "source/native layout, atlas index and animation flags")
                layout,atlas_index,flags=struct.unpack("<3H",cut(after,a+2,6))
                need(layout<layouts, "selected layout is inside real P0 table")
                np=ptr(after,lt+layout*8+4); parts=u(after,lt+layout*8)
                source_layout=source_p0+16+4*layout
                need(0<parts<=127 and h(new,source_layout)==parts, "bounded source/native part count")
                sp=source_p0+h(new,source_layout+2)
                need(cut(after,np,4*parts)==cut(new,sp,4*parts), "complete native/source selected part array")
                index=atlas_index if h(after,p0+14)&2 else 0
                nda,sda=nd+8*index,sd+8*index
                size=u(after,nda); na=ptr(after,nda+4,size)
                need(size==h(new,sda) and 0<size<=8192 and size%32==0, "complete selected source/native atlas size")
                sa=far(new,sda+2); source_pixels=cut(new,sa,size)
                key=(nda,sda)
                if key not in atlases:
                    need(cut(after,na,size)==packed(source_pixels), "entire selected atlas equals source planar-to-packed pixels")
                    atlases[key]=dict(native_descriptor=nda,source_descriptor=sda,native_pixels=na,source_pixels=sa,bytes=size,sha256=sha(after[na:na+size]))
                for part in range(parts):
                    need(after[np+4*part]*32+32<=size, "every actual native low-byte tile read fits selected atlas")
                row["layouts"].append(layout);row["atlas_indices"].append(index);row["durations"].append(after[a]);row["flags"].append(flags);row["part_counts"].append(parts)
                maximum=max(maximum,parts)
            row["progress"]=animation(row["durations"],row["flags"])
            need(row["progress"]["visited"]==frames, "all selected frames reachable in retained animation graph")
            result.append(row);local_frames+=frames
        need(local_frames==FRAME_COUNTS[ident] and maximum==MAX_PARTS[ident], "independent per-character selected-frame census")
        for index in (4,6):
            first_pose=result[index]
            need(all(flag==0 for flag in first_pose["flags"]) and first_pose["progress"]["kind"]=="complete" and first_pose["progress"]["steps"]<222, "every first pose completes before native handoff countdown")
        resources.append(dict(id=ident,native_p0=p0,native_p1=p1,source_p0=source_p0,source_p1=source_p1,
            all_events=count,all_layouts=layouts,selected_frames=local_frames,max_parts=maximum,events=result))
        events_total+=len(result);frame_total+=local_frames
    if only_id is None:
        need((events_total,frame_total,len(atlases))==(120,1252,701), "complete fifteen-character selected graph and atlas census")
    return dict(resources=resources,events=events_total,frames=frame_total,atlases=[atlases[k] for k in sorted(atlases)],
        unique_atlases=len(atlases),timing="Existing native duration bytes are retained; source timing conversion is not redefined by this table layer.")


def pointer_aliases(data, start, end):
    result=[]
    for alignment in range(4):
        stop=len(data)-((len(data)-alignment)%4)
        for index,(value,) in enumerate(struct.iter_unpack("<I",memoryview(data)[alignment:stop])):
            if value>>24 in (8,10,12) and start<=value&0x1FFFFFF<end:
                result.append((alignment+4*index,value))
    return sorted(result)


def aliases(data, installed):
    start,end=(TABLE,END) if installed else (ORIGINAL[0],ORIGINAL[1]+28)
    expected=sorted((site+4*high,BASE+(TABLE+32*kind if installed else ORIGINAL[kind])+high)
                    for kind,site,_ in PAIRS for high in range(2))
    need(pointer_aliases(data,start,end)==expected, "exact twelve all-alignment aliases in all three ROM mirrors")
    if installed:
        need(not pointer_aliases(data,ORIGINAL[0],ORIGINAL[1]+28), "no original-table interior or mirror aliases remain")
    for _,site,reader in PAIRS:
        for high in range(2):
            address=site+4*high; readers=[]
            for at in range((address-4104)&~3,address+4096,4):
                word=u(data,at)
                if word>>28!=15 and word&0x0F7F0000==0x051F0000 and literal_site(data,at)==address:
                    readers.append((at,word>>12&15))
            need(readers==[(reader+high*8,8)], "exact actual reader of every literal")
    return [dict(site=s,pointer=p) for s,p in expected]


def reservation(before):
    need(cut(before,TABLE,END-TABLE)==b"\xff"*(END-TABLE), "whole sixty-four-byte allocation is unused")
    need(not pointer_aliases(before,TABLE,END), "no all-alignment inbound ROM-mirror pointer")
    for index,(word,) in enumerate(struct.iter_unpack("<I",before)):
        if word==0xFFFFFFFF:continue
        at,target=index*4,None
        if word&0x0E000000==0x0A000000:
            d=word&0xFFFFFF;d-=0x1000000 if d&0x800000 else 0;target=at+8+4*d
        elif word&0x0F7F0000==0x051F0000:
            target=at+8+(1 if word&0x800000 else -1)*(word&4095)
        elif word&0x0E1F0000==0x020F0000 and (word>>21)&15 in (2,4):
            rotate,value=((word>>8)&15)*2,word&255
            immediate=((value>>rotate)|(value<<(32-rotate)))&0xFFFFFFFF if rotate else value
            target=at+8+(immediate if (word>>21)&15==4 else -immediate)
        need(target is None or not TABLE<=target<END, "no ARM branch/literal/ADR allocation owner")
    for index,(word,) in enumerate(struct.iter_unpack("<H",before)):
        if word&0xF800 in (0x4800,0xA000):
            target=((index*2+4)&~3)+(word&255)*4
            need(not TABLE<=target<END, "no Thumb PC-relative literal/ADR allocation owner")


def candidate(before, after, gba, tables):
    need(len(before)==len(after)==0x800000, "candidate extents")
    expected=bytearray(before);expected[TABLE:END]=tables[0]+tables[1]
    for kind,site,_ in PAIRS:
        for high in range(2):struct.pack_into("<I",expected,site+4*high,BASE+TABLE+kind*32+high)
    need(after==expected, "exact source-derived sixty-four bytes and twelve redirects; no other writes")
    need(cut(after,ORIGINAL[0],56)==cut(gba,ORIGINAL[0],56), "all original pair bytes and alignment padding retained")
    inverse=bytearray(after);inverse[TABLE:END]=before[TABLE:END]
    for _,site,_ in PAIRS:inverse[site:site+8]=before[site:site+8]
    need(inverse==before, "full-image inverse")
    rows=[]
    for ident in range(15):
        for kind in range(2):
            expected_pair=h(tables[kind],2*ident)
            for selected_kind,site,_ in PAIRS:
                if selected_kind==kind:
                    low=after[ptr(after,site)+2*ident];high=after[ptr(after,site+4)+2*ident]
                    need(low|(high<<8)==expected_pair, "all ninety actual installed pair consumer routes")
            rows.append(dict(id=ident,outcome="win" if kind==0 else "lose",first=expected_pair&255,second=expected_pair>>8))
    return rows


def negatives(before,after,gba,old,new,tables,graph):
    rejected=[]
    def reject(label,check):
        try:check()
        except (ValueError,IndexError,KeyError,struct.error):rejected.append(label)
        else:raise ValueError("negative accepted: "+label)
    def changed(data,at,mask=1):
        result=bytearray(data);result[at]^=mask;return result
    for byte in range(64):
        reject(f"installed pair byte {byte}",lambda byte=byte:candidate(before,changed(after,TABLE+byte),gba,tables))
    for _,site,_ in PAIRS:
        for high in range(2):
            at=site+4*high
            reject(f"redirect {at:X}",lambda at=at:candidate(before,changed(after,at),gba,tables))
    for at in (TABLE-1,END,ORIGINAL[0],ORIGINAL[1]+26,0x629350,0x629000,0x90A18,0x8A048,0x12AE4):
        reject(f"outside-layer byte {at:X}",lambda at=at:candidate(before,changed(after,at),gba,tables))
    reject("truncated candidate",lambda:candidate(before,after[:-1],gba,tables))
    for kind in range(2):
        for ident in range(16):
            at=SOURCE_NEW[kind]+2*ident
            reject(f"source pair {kind}/{ident}",lambda at=at:source_tables(gba,old,changed(new,at)))
    for at in (0x777200,0x7776AB,0x7776B4,0x7776C6,0x777739,0x77778A):
        reject(f"source boundary/reader {at:X}",lambda at=at:source_tables(gba,old,changed(new,at)))
    for at in (0x8A99C,0x8A9B4,0x8A9D0,0x8AA64,0x8AA6C,0x8AA7C,0x8AA8C,0x8AA90,0x12AA0,0x12ACC,0x12AE4,0x12B78,0x12BB8):
        reject(f"native phase contract {at:X}",lambda at=at:phase_contract(changed(after,at),gba))
    for resource in graph["resources"]:
        ident=resource["id"]
        for event in resource["events"]:
            at=event["native_commands"]+2
            reject(f"selected frame layout {ident}/{event['event']}",lambda at=at,ident=ident:population(changed(after,at),new,tables,ident))
        event=resource["events"][4]
        at=event["source_commands"]+6
        reject(f"source first-pose flags {ident}",lambda at=at,ident=ident:population(after,changed(new,at),tables,ident))
    # These do not rely on the whole-image identity check: wrong graph structure,
    # atlas payloads and signed timing must fail their own semantic contracts.
    for resource in graph["resources"]:
        ident=resource["id"];event=resource["events"][4]
        bad=bytearray(after);bad[event["native_commands"]]=255
        reject(f"invalid signed frame duration {ident}",lambda bad=bad,ident=ident:population(bad,new,tables,ident))
    atlas=graph["atlases"][0]
    reject("native atlas pixel",lambda:population(changed(after,atlas["native_pixels"]),new,tables))
    reject("source atlas pixel",lambda:population(after,changed(new,atlas["source_pixels"]),tables))
    for installed,data,target in ((False,before,ORIGINAL[0]+1),(True,after,TABLE+1)):
        for mirror in (8,10,12):
            bad=bytearray(data);struct.pack_into("<I",bad,0x101,(mirror<<24)+target)
            reject(f"unaligned interior alias {installed}/{mirror:X}",lambda bad=bad,installed=installed:aliases(bad,installed))
    reject("occupied allocation",lambda:reservation(changed(before,TABLE)))
    for mirror in (8,10,12):
        bad=bytearray(before);struct.pack_into("<I",bad,0x101,(mirror<<24)+TABLE+1)
        reject(f"allocation mirror {mirror:X}",lambda bad=bad:reservation(bad))
    for label,word,half in (("ARM branch",0xEA00003E,False),("ARM literal",0xE59F00F8,False),("ARM ADR",0xE28F00F8,False),
                            ("Thumb literal",0x483F,True),("Thumb ADR",0xA03F,True)):
        bad=bytearray(before);struct.pack_into("<H" if half else "<I",bad,TABLE-0x100,word)
        reject(label+" owner",lambda bad=bad:reservation(bad))
    return rejected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("before","after","gba","old","new","output"):parser.add_argument(key,type=Path)
    args=parser.parse_args()
    paths=[args.before,args.after,args.gba,args.old,args.new]
    need(all(p.suffix.lower() in (".gba",".wsc") for p in paths), "explicit ROM inputs only")
    need(args.output.suffix.lower()==".json", "JSON report output only")
    before,after,gba,old,new=[p.read_bytes() for p in paths]
    need(tuple(map(sha,(before,after,gba,old,new)))==(BEFORE,AFTER,GBA,OLD,NEW), "five pinned input identities")
    tables=source_tables(gba,old,new)
    code=consumers(before,after,gba)
    phases=phase_contract(after,gba)
    graph=population(after,new,tables)
    reservation(before)
    original_aliases=aliases(before,False);installed_aliases=aliases(after,True)
    rows=candidate(before,after,gba,tables)
    rejected=negatives(before,after,gba,old,new,tables,graph)
    spans=sorted([(site+4*high,site+4*high+4) for _,site,_ in PAIRS for high in range(2)]+[(TABLE,END)])
    report=dict(status="PASS",kind="independent-result-pose-routing",inputs=dict(zip(("before","after","gba","old","new"),map(sha,(before,after,gba,old,new)))),
        source_tables=[dict(kind="win" if i==0 else "lose",old=SOURCE_OLD[i],source=SOURCE_NEW[i],native_original=ORIGINAL[i],installed=TABLE+32*i,
            old_storage_bytes=26,source_storage_bytes=32,native_original_storage_bytes=28,source_sha256=sha(tables[i])) for i in range(2)],
        routes=rows,actual_consumer_routes=90,consumers=code,phase_handoff=phases,presentation_graph=graph,
        aliases_before=original_aliases,aliases_after=installed_aliases,
        writes=[dict(start=a,end=b,bytes=b-a,before_sha256=sha(before[a:b]),after_sha256=sha(after[a:b])) for a,b in spans],
        declared_bytes=sum(b-a for a,b in spans),changed_bytes=sum(a!=b for a,b in zip(before,after)),full_inverse=True,
        reservation=dict(start=TABLE,end=END,ff=True,all_alignment_rom_mirrors=[8,10,12],arm_branch_literal_adr=True,thumb_literal_adr=True),
        negative_count=len(rejected),negative_cases=rejected,
        limits=["The stored terminal00/00 pair is preserved without assigning a character or sentinel meaning; no ID15 resource validity is claimed.",
            "Per-character part maxima are not a whole-mode OAM budget. Other result objects and their aggregate emissions are a separate proof.",
            "All selected frames are internally reachable; second-pose cycles may extend past the existing222-tick result countdown or other mode exit.",
            "Native timing, audio and service behavior are retained. This layer does not establish universal WSC/native timing or downstream behavior equivalence.",
            "No emulator, target execution or save access; runtime observations are separate."])
    need(report["declared_bytes"]==112 and report["changed_bytes"]==100,"exact write census")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="PASS",report_sha256=sha(args.output.read_bytes()),events=graph["events"],frames=graph["frames"],atlases=graph["unique_atlases"],negatives=len(rejected))))


if __name__=="__main__":
    main()
