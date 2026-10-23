#!/usr/bin/env python3
"""Independent proof of the bounded Waterfall third-pattern/phase2 repair.

The five ROMs are explicit inputs. No builder, analyzer, generated manifest,
runtime fixture, emulator or save determines expected data or code.
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

BEFORE = "DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C"
AFTER = "B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8"
GBA = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BASE, CODE, SLOT, END = 0x08000000, 0x629600, 0x62967C, 0x629680
RECORD, RECORD_END = 0x584CE8, 0x584CFC
SOURCE_CS, SOURCE_RECORD = 0x740900, 0x7450A1
MODE1, MODE3, SOURCE_END = 0x7446FB, 0x7448CA, 0x7449AF
WAIT, EXIT = 0x585274, 0x585310
PHASE_EDITS = ((0x5846F4, 0xE2451001, 0xE1A01005), (0x584704, 0xE2471001, 0xE1A01007))
WRITES = ((0x5846F4,0x5846F8),(0x584704,0x584708),(RECORD,RECORD_END),(CODE,END))
NATIVE_PINS = (
    (0x36D28C,0x36D354,"3AF7186D3894C0B036B8DAA97E6FA450AB7D58BD69A55D4D18C317B70358F7DF"),
    (0x36D77C,0x36D8B4,"79F89EC8AADF076AEE76631372824913ADB1EDE38FC92E54775E0AB8BB53C335"),
    (0x585200,0x585390,"0E1DA4E47BBA90A2711BCE9F022A65FBBAA58A5DBBABE67D5B3B0B80AB733FCA"),
    (0x1369C,0x136F0,"A1436B6A7F40C6019E0A27B4A3A636C8819D05E5B0391914FA85FF2DA9236026"),
    (0x13764,0x137AC,"0B756AB86846DFF0E92AD9AA172F3A594BBAE3640D6F9448C830E361C3F6366A"),
    (0x36D750,0x36D77C,"5982EEBEF11CCCEC5D15E37E436DE6F1F127CD3532082FA40251A4B3E3CECACD"),
    (0x583900,0x58394C,"FFD67C3A8732D9576388DCFB633FA44E23B1F90CCB8A56F2CD77CDE313875692"),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def cut(data, at, size):
    need(0 <= at <= len(data) and 0 <= size <= len(data)-at, "bounded ROM extent")
    return bytes(data[at:at+size])


def u(data, at):
    return struct.unpack("<I", cut(data,at,4))[0]


def h(data, at):
    return struct.unpack("<H", cut(data,at,2))[0]


def signed(data, at):
    return struct.unpack("<h", cut(data,at,2))[0]


def ptr(data, at, size=1):
    raw=u(data,at)-BASE;cut(data,raw,size);return raw


def sequence(data, at, rows, arm=True, size=None):
    size=len(rows)*4 if size is None else size
    decoder=Cs(CS_ARCH_ARM if arm else CS_ARCH_X86,CS_MODE_ARM if arm else CS_MODE_16)
    ins=list(decoder.disasm(cut(data,at,size),at+(BASE if arm else 0)))
    need(sum(row.size for row in ins)==size and [f"{row.mnemonic} {row.op_str}".strip() for row in ins]==rows,
         f"actual {'ARM' if arm else 'x86'} contract {at:X}")


def branch_word(at, target, link=False):
    offset=target-at-8
    need(offset%4==0 and -(1<<25)<=offset<(1<<25),"bounded ARM branch relocation")
    return (0xEB000000 if link else 0xEA000000)|((offset//4)&0xFFFFFF)


def branch_target(data, at):
    word=u(data,at);need(word&0x0E000000==0x0A000000,"ARM branch")
    value=word&0xFFFFFF;value-=0x1000000 if value&0x800000 else 0
    return at+8+value*4


def literal(data, at):
    word=u(data,at);need(word&0x0F7F0000==0x051F0000,"ARM word literal")
    return u(data,at+8+(1 if word&0x800000 else -1)*(word&4095))


def source_proof(new):
    # Neighboring configuration row and callback slots establish actual extents;
    # the leading configuration value3 is NOT assumed to be a record count.
    need(struct.unpack("<4H",cut(new,0x744F51,8))==(3,0x47A1,2,0x47D1),"adjacent source configuration boundaries")
    need(SOURCE_CS+0x47A1==SOURCE_RECORD and SOURCE_CS+0x47D1==SOURCE_RECORD+48,"three complete source records before next configuration")
    record_rows=[]
    for index,callback in enumerate((0x3DFB,0x3EE0,0x3FCA)):
        at=SOURCE_RECORD+16*index;data=cut(new,at,16)
        fields=struct.unpack("<6hHH",data)
        need(fields[6]==1 and fields[7]==0x481F+2*index,"one consumed callback slot per source record")
        slot=SOURCE_CS+fields[7]
        need(h(new,slot)==callback,"actual source callback indirection")
        need(fields[:6]==((0xF00,0x600,128,0,0x380,-1),(0xFF00-65536,0xF80,128,0,0x380,-1),(0xF00,0x1300,128,0,0x380,-1))[index],"all six source motion/state fields")
        record_rows.append(dict(index=index,source=at,fields=list(fields[:6]),callback_count=fields[6],source_slot=slot,source_callback=SOURCE_CS+callback))
    need(h(new,0x745125)==0x40AF,"next callback anchors full mode3 boundary including final RETF")
    need(struct.unpack("<BBH",cut(new,0x745151,4))==(3,4,0x497D),"source seed divisor, cycle length and sequence pointer")
    payload=cut(new,0x74527D,32)
    pairs=list(struct.iter_unpack("<HH",payload))
    need(pairs==[(1,10),(0,10),(2,10),(1,10),(0,10),(2,10),(1,10),(2,10)],"entire stored selector payload")
    mode1,mode3=cut(new,MODE1,229),cut(new,MODE3,229)
    need(sha(mode1)=="426AC033F0303F6EDEF7CF08DBC571DB4E050E19DF8AACD051195B29882E3FAC","complete mode1 source oracle")
    changes={0x10:(1,3),0x3A:(0x40,0xC0),0x48:(0x4A,0x19),0x49:(0x3E,0x40),0x62:(0x9E,0x6D),0x63:(0x3E,0x40)}
    need([(i,a,b) for i,(a,b) in enumerate(zip(mode1,mode3)) if a!=b]==[(i,*ab) for i,ab in changes.items()],"only mode, initial phase and two continuation relocations differ")
    need(mode3[-1]==0xCB and new[SOURCE_END]==0x6A,"complete mode3 RETF then next constructor")
    need(h(new,MODE3+0x48)==0x4019 and h(new,MODE3+0x4D)==0x4090 and h(new,MODE3+0x62)==0x406D and h(new,MODE3+0x67)==0x4090,"both source callback continuations resolve internally")
    sequence(new,MODE3,["push es","push bx","mov bx, 0x1000","mov es, bx","mov bx, 0x382","add bx, 2","mov word ptr es:[bx], 3","pop bx","pop es"],False,20)
    ins=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(mode3,MODE3))
    need(sum(i.size for i in ins)==229,"complete source callback-family decoding")
    need([i.op_str for i in ins if i.mnemonic=="lcall"]==["0x4fff, 0x24cb","0x4fff, 0x2862","0x4fff, 0x19a8","0x4090, 0x398e","0x4fff, 0x2862","0x4fff, 0x19a8"],"all required source services")
    sequence(new,0x744919,["cmp word ptr [si + 0x82], 0","jne 0x744936","or word ptr [di + 8], 0x4000","mov word ptr [si + 0x32], 0x70","mov word ptr [si], 0x406d","mov word ptr [si + 2], 0x4090","jmp 0x74496c"],False,29)
    sequence(new,0x74494F,["sar ax, 1","mov word ptr [si + 0x34], ax","inc word ptr [si + 0x80]","and word ptr [si + 0x80], 1","jne 0x74496c","inc word ptr [si + 0x7e]","and word ptr [si + 0x7e], 0xff","dec word ptr [si + 0x82]","retf"],False,30)
    sequence(new,0x74496D,["cmp word ptr [si + 0x26], 0xf00","jl 0x74497c","lcall 0x4090, 0x398e","jmp 0x74496c"],False,15)
    return dict(records=record_rows,stored_selector_pairs=[list(p) for p in pairs],active_selectors=[p[0] for p in pairs[:4]],
        source_mode1=MODE1,source_mode3=MODE3,source_end=SOURCE_END,source_family_bytes=229,source_mode3_sha256=sha(mode3),
        only_source_differences=[dict(offset=i,before=a,after=b) for i,(a,b) in changes.items()],
        source_wait=0x744919,source_exit=0x74496D,initial_phase=0xC0,initial_counter=256)


def selector_consumers(before, after, new):
    need(cut(after,0x584C48,8)==struct.pack("<II",3,BASE+0x584CC0),"native stage9 configuration row")
    need(cut(after,0x584B48,8)==struct.pack("<HHI",3,4,BASE+0x584B80),"native stage9 pattern header")
    need(cut(after,0x584B80,32)==cut(new,0x74527D,32),"all stored source/native selector pairs")
    sequence(new,0x74403A,["shl bx, 2","add bx, 0x462d","mov ax, word ptr cs:[bx]","mov word ptr [0x706], ax","mov ax, word ptr cs:[bx + 2]","mov word ptr [0x708], ax","mov word ptr [0x70a], 0x4761"],False,26)
    sequence(new,0x74406D,["shl bx, 2","add bx, 0x482d","mov dl, byte ptr cs:[bx]","xor di, di","mov di, dx","xor dx, dx","mov ax, word ptr [0x6fc]","div di","mov al, byte ptr cs:[bx + 1]","mov byte ptr [0x70c], al","mov ax, word ptr cs:[bx + 2]","mov word ptr [0x70d], ax","xor dh, dh","mov word ptr [0x704], dx"],False,41)
    need(SOURCE_CS+0x462D+9*4==0x744F51 and SOURCE_CS+0x482D+9*4==0x745151,"source stage9 producer indices")
    need(branch_target(after,0x36D2C0)==0x584D40 and literal(after,0x584D40)==BASE+0x584C00 and branch_target(after,0x584D48)==0x36D2C8,"retained native configuration-table route")
    sequence(after,0x584D44,["add r1, sb, r1, lsl #3"])
    sequence(after,0x36D2C8,["ldr r0, [r1]","ldr r8, [pc, #0x128]","strh r0, [r8]","ldr r0, [r1, #4]","ldr r8, [pc, #0x120]","str r0, [r8]"])
    need(literal(after,0x36D2CC)==0x03004CFA and literal(after,0x36D2D8)==0x03004CFC,"configuration globals")
    sequence(after,0x36D300,["ldr sb, [pc, #0x104]","adds r1, sb, r1, lsl #3","ldrsh r5, [r1]","ldr r8, [pc, #0xfc]","ldrh r0, [r8]","stmdb sp!, {r1}","mov r1, r5","bl #0x837db3c","mov r3, r1","ldm sp!, {r1}","ldrsh r0, [r1, #2]","ldr r8, [pc, #0xe0]","strb r0, [r8]","ldr r0, [r1, #4]","ldr r8, [pc, #0xd8]","str r0, [r8]","and r3, r3, #0xff","ldr r8, [pc, #0xd0]","strh r3, [r8]"])
    need(literal(after,0x36D300)==BASE+0x584B00 and literal(after,0x36D32C)==0x03004D04 and literal(after,0x36D338)==0x03004D08 and literal(after,0x36D344)==0x03004CF8,"seed/cycle/sequence native owners")
    sequence(new,0x7442B4,["mov bx, word ptr es:[0x70d]","mov ax, word ptr es:[0x704]","shl ax, 2","add bx, ax","mov ax, word ptr es:[0x704]","inc ax","cmp al, byte ptr es:[0x70c]","jb 0x7442d0","xor ax, ax","mov word ptr es:[0x704], ax"],False,32)
    sequence(new,0x7442DA,["mov ax, word ptr cs:[bx]","shl ax, 4","test word ptr es:[0x713], 1","je 0x7442f1","add ax, word ptr es:[0x70a]","jmp 0x7442f6","add ax, word ptr es:[0x708]","mov bx, ax"],False,30)
    sequence(new,0x7442F8,["mov ax, word ptr cs:[bx]","mov word ptr [si + 0x26], ax","mov word ptr [si + 0x2a], ax",
        "mov ax, word ptr cs:[bx + 2]","mov word ptr [si + 0x28], ax","mov word ptr [si + 0x2c], ax",
        "mov ax, word ptr cs:[bx + 4]","mov word ptr [si + 0x32], ax","mov ax, word ptr cs:[bx + 6]","mov word ptr [si + 0x34], ax",
        "mov ax, word ptr cs:[bx + 8]","mov word ptr [si + 0x82], ax","mov ax, word ptr cs:[bx + 0xa]","mov word ptr [si + 0x84], ax",
        "mov ax, word ptr cs:[bx + 0xc]","mov word ptr es:[0x702], ax","mov ax, word ptr cs:[bx + 0xe]","mov word ptr es:[0x6fe], ax",
        "mov bx, ax","mov ax, word ptr cs:[bx]","mov word ptr [si], ax","mov word ptr [si + 2], cs"],False,75)
    sequence(after,0x36D78C,["ldr r8, [pc, #0xfc]","ldr r1, [r8]","ldr r8, [pc, #0xf8]","ldrh r0, [r8]","add r1, r1, r0, lsl #2","ldr r8, [pc, #0xf0]","ldrh r0, [r8]","add r0, r0, #1","ldr sb, [pc, #0xe8]","ldrb sb, [sb]","cmp r0, sb","movhs r0, #0","strh r0, [r8]"])
    sequence(after,0x36D7C8,["ldrh r0, [r1]","mov r8, #0x14","mul r0, r8, r0"])
    sequence(after,0x36D800,["mov r1, r0","ldrsh r0, [r1]","strh r0, [r4, #0x34]","strh r0, [r4, #0x38]","ldrsh r0, [r1, #2]","strh r0, [r4, #0x36]","strh r0, [r4, #0x3a]","ldrsh r0, [r1, #4]","strh r0, [r4, #0x42]","ldrsh r0, [r1, #6]","strh r0, [r4, #0x44]","ldrsh r0, [r1, #8]","strh r0, [r4, #0x98]","ldrsh r0, [r1, #0xa]","str r0, [r4, #0x9c]","ldr r0, [r1, #0xc]","ldr r8, [pc, #0x64]","strh r0, [r8]","ldr r0, [r1, #0x10]","ldr r8, [pc, #0x5c]","str r0, [r8]","mov r1, r0","ldr r0, [r1]","str r0, [r4]"])
    need(literal(after,0x36D78C)==0x03004D08 and literal(after,0x36D794)==0x03004CF8 and literal(after,0x36D7AC)==0x03004D04 and literal(after,0x36D7F4)==0x03004CFC,"actual selector and config readers use producer globals")
    routes=[]
    for seed in range(3):
        for step in range(4):
            cycle=(seed+step)%4;selector=h(after,0x584B80+cycle*4)
            need(selector in (0,1,2),"all active selector indices fit complete three-record source extent")
            native=0x584CC0+20*selector;source=SOURCE_RECORD+16*selector
            routes.append(dict(seed=seed,step=step,cycle=cycle,selector=selector,native=native,source=source))
    return dict(configuration=0x584C48,pattern_header=0x584B48,pattern_payload=0x584B80,
        seed_divisor=3,active_cycle=4,active_selectors=[1,0,2,1],routes=routes,
        source_stride=16,native_stride=20,callback_writer=BASE+0x36D85C,
        limit="Proves the existing logical-stage9 route. Earlier stage getter/priority behavior is unchanged and belongs to a separate layer.")


def core_services(before, after, gba, old, new):
    kept=[]
    for start,end,digest in NATIVE_PINS:
        need(sha(cut(before,start,end-start))==digest and cut(after,start,end-start)==cut(before,start,end-start),"complete retained native consumer/service span")
        kept.append(dict(start=start,end=end,sha256=digest))
    for start,end in ((0x12874,0x12BBC),(0x12348,0x12560),(0x1369C,0x136F0),(0x13764,0x137AC),(0x3524C4,0x3524F0)):
        need(cut(after,start,end-start)==cut(gba,start,end-start),"retained retail native service oracle")
    source_sine=cut(new,0x7519C9,512)
    need(source_sine==cut(old,0x39858D,512)==cut(after,0x12360,512),"all256 source-old/source-new/native signed sine entries identical")
    for data,at,table in ((new,0x751998,0x19D9),(old,0x39855C,0x1A6D)):
        sequence(data,at,["push bp","mov bp, sp","push bx","mov bx, word ptr [bp + 6]","and bx, 0xff","add bx, bx",f"mov ax, word ptr cs:[bx + 0x{table:x}]","pop bx","mov sp, bp","pop bp","retf"],False,23)
    sequence(after,0x12348,["ldr sb, [sp]","and sb, sb, #0xff","add sb, sb, sb","add r8, pc, #4","ldrsh r0, [r8, sb]","bx lr"])
    sequence(new,0x74428E,["push bx","push es","mov ax, 0x1000","mov es, ax","mov word ptr es:[0x6f8], 0","push ds","push si","lcall 0x4090, 0x181e","add sp, 4","pop es","pop bx","retf"],False,27)
    sequence(after,0x36D750,["stmdb sp!, {lr}","ldr r8, [pc, #0x1c]","mov sb, #0","strh sb, [r8]","stmdb sp!, {r4}","stmdb sp!, {fp}","bl #0x83524c4","add sp, sp, #8","ldm sp!, {lr}","bx lr"])
    need(literal(after,0x36D754)==0x03004CEC,"existing reset/hazard owner")
    return dict(retained_spans=kept,sine_entries=256,sine_sha256=sha(source_sine),
        source_services={"event":"4FFF:24CB","animation":"4FFF:2862","sine":"4FFF:19A8","reset":"4090:398E"},
        native_services={"event":BASE+0x12874,"animation":BASE+0x12A84,"sine":BASE+0x12348,"reset":BASE+0x36D750},
        owner=0x0300256A,reset_owner=0x03004CEC)


def helper_expected(before):
    code=bytearray(cut(before,0x585200,116))
    for at,value in ((4,0xE59F8068),(8,0xE3A00003),(0x20,branch_word(CODE+0x20,0x12874,True)),
                     (0x4C,0xE3A080C0),(0x60,0xE59F8010),(0x68,branch_word(CODE+0x68,WAIT,True))):
        struct.pack_into("<I",code,at,value)
    code.extend(struct.pack("<III",0x0300256A,BASE+WAIT,BASE+CODE))
    need(len(code)==128,"116-byte entry, two literals and one callback slot")
    return bytes(code)


def helper_contract(before,after):
    need(cut(after,CODE,128)==helper_expected(before),"independently relocated complete entry and callback slot")
    sequence(after,CODE,["str lr, [sp, #-4]!","ldr r8, [pc, #0x68]","mov r0, #3","strh r0, [r8]",
        "str r5, [sp, #-4]!","str fp, [sp, #-4]!","mov r8, #0","str r8, [sp, #-4]!","bl #0x8012874","add sp, sp, #0xc",
        "ldrh r8, [r5, #8]","bic r8, r8, #0x6000","strh r8, [r5, #8]","mov r0, #0","mvn r8, #0x6f",
        "strh r8, [r4, #0x42]","strh r0, [r4, #0x44]","strh r0, [r4, #0x46]","strh r0, [r4, #0x48]",
        "mov r8, #0xc0","strh r8, [r4, #0x94]","strh r0, [r4, #0x96]","mov r8, #0x100","strh r8, [r4, #0x98]",
        "ldr r8, [pc, #0x10]","str r8, [r4]","bl #0x8585274","pop {lr}","bx lr"])
    need(literal(after,CODE+4)==0x0300256A and literal(after,CODE+0x60)==BASE+WAIT and u(after,SLOT)==BASE+CODE,"actual relocated owner and wait indirection")
    sequence(after,WAIT,["str lr, [sp, #-4]!","ldrh r8, [r4, #0x98]","cmp r8, #0","bne #0x85852a4","ldrh r8, [r5, #8]",
        "orr r8, r8, #0x4000","strh r8, [r5, #8]","mov r8, #0x70","strh r8, [r4, #0x42]","add r8, pc, #0x70","str r8, [r4]","b #0x8585308"])
    sequence(after,0x5852A4,["str r5, [sp, #-4]!","str fp, [sp, #-4]!","mov r8, #1","str r8, [sp, #-4]!","bl #0x8012a84","add sp, sp, #0xc",
        "ldrh r8, [r4, #0x94]","str r8, [sp, #-4]!","bl #0x8012348","add sp, sp, #4","asr r0, r0, #1","strh r0, [r4, #0x44]",
        "ldrh r8, [r4, #0x96]","add r8, r8, #1","and r8, r8, #1","strh r8, [r4, #0x96]","cmp r8, #0","bne #0x8585308",
        "ldrh r8, [r4, #0x94]","add r8, r8, #1","and r8, r8, #0xff","strh r8, [r4, #0x94]","ldrh r8, [r4, #0x98]",
        "sub r8, r8, #1","strh r8, [r4, #0x98]","pop {lr}","bx lr"])
    sequence(after,EXIT,["str lr, [sp, #-4]!","ldrsh r8, [r4, #0x34]","cmp r8, #0xf00","blt #0x858532c","bl #0x836d750","pop {lr}","bx lr"])
    sequence(after,0x58532C,["str r5, [sp, #-4]!","str fp, [sp, #-4]!","mov r8, #1","str r8, [sp, #-4]!","bl #0x8012a84","add sp, sp, #0xc",
        "ldrh r8, [r4, #0x94]","str r8, [sp, #-4]!","bl #0x8012348","add sp, sp, #4","asr r0, r0, #1","strh r0, [r4, #0x44]",
        "ldrh r8, [r4, #0x96]","add r8, r8, #1","and r8, r8, #1","strh r8, [r4, #0x96]","cmp r8, #0","bne #0x8585384",
        "ldrh r8, [r4, #0x94]","add r8, r8, #1","and r8, r8, #0xff","strh r8, [r4, #0x94]","pop {lr}","bx lr"])
    need(0x585298+8+0x70==EXIT,"shared wait installs retained exit callback")
    # Both entry and common wait retain LR in distinct words. The maximum
    # before entering retained services is8 bytes of LR plus12 argument bytes.
    return dict(entry=BASE+CODE,entry_code_bytes=116,entry_literals=[0x0300256A,BASE+WAIT],slot=BASE+SLOT,
        wait=BASE+WAIT,exit=BASE+EXIT,mode=3,phase=192,counter=256,
        actor_field_mapping={"source32":"native42","source34":"native44","source36":"native46","source38":"native48","source7E":"native94","source80":"native96","source82":"native98"},
        abi="Existing r4 actor, r5 presentation, fp placeholder; no new RAM. Entry and shared wait save/restore their own LR, unwind all arguments, and return with original SP.",
        maximum_local_stack_bytes=20,common_sha256=sha(cut(after,WAIT,0x58538C-WAIT)))


def phase_contract(before,after,new):
    need(sha(cut(before,0x584600,0x154))=="3CA75DB08CC5763E96F8ECEDDE5E149A84F523E00707CDC78C39E3EDE7AA29B5","whole original mode handler")
    expected=bytearray(cut(before,0x584600,0x154))
    for at,old,word in PHASE_EDITS:
        need(u(before,at)==old and u(after,at)==word,"only exact two phase2 register moves")
        need(not(old|word)&0x00100000,"both original SUB and replacement MOV preserve CPSR flags")
        struct.pack_into("<I",expected,at-0x584600,word)
    need(cut(after,0x584600,0x154)==expected,"whole mode handler retained except two phase2 words")
    need(u(after,0x58467C)==u(before,0x58467C)==0xE2451001,"phase1 ID-minus-one remains unchanged")
    sequence(after,0x584600,["push {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}","ldr r4, [pc, #0x138]","ldrh r0, [r4]","and r2, r0, #3",
        "cmp r2, #1","blo #0x858473c","cmp r2, #3","bhi #0x858473c","sub r1, r2, #1","ldr r6, [pc, #0x124]","add r6, r6, r1, lsl #2","ldrh r5, [r6]","ldrh r7, [r6, #2]"])
    need(literal(after,0x584604)==0x0300256A and literal(after,0x584624)==BASE+0x584800,"mode and pair owners")
    pairs=list(struct.iter_unpack("<HH",cut(new,0x76ABC3,12)))
    need(pairs==[(5,7),(1,7),(1,3)] and cut(after,0x584800,12)==cut(new,0x76ABC3,12),"all three source/native mode pairs")
    for at in (0x76ACA9,0x76ACC3):
        sequence(new,at,["mov ax, word ptr cs:[bx]","mov di, ax","shl di, 2","shl ax, 1","add di, ax","add di, 0","xor ax, ax","mov word ptr [di + 2], ax","mov word ptr [di], ax"],False,23)
    sequence(new,0x76AC37,["dec ax","mov bx, ax","mov ax, 0x1073","mov ds, ax","mov ax, bx","shl bx, 2","shl ax, 1","add bx, ax","add bx, 0","mov ax, word ptr [bx]"],False,23)
    sequence(after,0x5846E8,["mov r0, #0","strh r0, [r4]","ldr r6, [pc, #0x50]","mov r1, r5","add r1, r6, r1, lsl #3","strh r0, [r1]","strh r0, [r1, #2]","mov r1, r7","add r1, r6, r1, lsl #3","strh r0, [r1]","strh r0, [r1, #2]"])
    sequence(after,0x1369C,["mov sl, #0","ldr r8, [pc, #0x3c]","strh sl, [r8]","ldr r8, [pc, #0x38]","mov sb, #0x10","str sl, [r8], #4","str sl, [r8], #4","str sl, [r8], #4","str sl, [r8], #4","subs sb, sb, #1","bgt #0x80136b0"])
    need(literal(after,0x136A8)==literal(after,0x13780)==literal(after,0x5846F0)==0x03001C68 and literal(after,0x136A0)==0x03001D68,"32-record allocation and separate next live halfword")
    sequence(after,0x13768,["ldr r2, [sp, #0x14]","movs r2, r2","beq #0x80137a0","sub r2, r2, #1","mov r0, #8","mul r2, r0, r2","ldr r5, [pc, #0x20]","add r5, r5, r2","mov r0, #0","strh r0, [r5, #2]","mov r0, #1","strh r0, [r5]","ldr r0, [sp, #0x10]","strh r0, [r5, #4]"])
    rows=[]
    for mode,pair in enumerate(pairs,1):
        successors=[ident+1 for ident in pair]
        remaining=[ident for ident in range(9,12) if ident!=mode+8]
        all_indices=[ident-1 for ident in pair]+list(pair)+[ident-1 for ident in remaining]
        need(all(0<=index<32 for index in all_indices),"every phase0/phase1/phase2/remaining-ID record is inside actual owner")
        need(all(0x03001C68+index*8+4<=0x03001D68 for index in pair),"two-word phase2 writes preserve next owner")
        rows.append(dict(mode=mode,phase0_ids=list(pair),phase1_read_index=pair[0]-1,phase1_successor_ids=successors,
            source_phase2_byte_offsets=[ident*6 for ident in pair],native_phase2_indices=list(pair),
            native_phase2_addresses=[0x03001C68+ident*8 for ident in pair],remaining_ids=remaining))
    return dict(owner_start=0x03001C68,owner_end=0x03001D68,records=32,record_bytes=8,modes=rows,
        phase1_preserved=True,phase2_flags_preserved=True,phase2_write_offsets=[0,2],
        reason="The callback reloads pair IDs each time; phase1's temporary increment does not persist. Source phase2 clears ID*6, so native must clear ID*8, the successors activated by phase1.")


def aliases(data,start,end):
    found=[]
    for align in range(4):
        stop=len(data)-((len(data)-align)%4)
        for index,(value,) in enumerate(struct.iter_unpack("<I",memoryview(data)[align:stop])):
            if value>>24 in (8,10,12) and start<=(value&0x1FFFFFF)<end:
                found.append((align+4*index,value))
    return sorted(found)


def reservation(before):
    ranges=((RECORD,RECORD_END),(CODE,END))
    for start,end in ranges:
        need(cut(before,start,end-start)==b"\xff"*(end-start),"complete empty record/helper reservation")
        need(not aliases(before,start,end),"no encoded inbound pointer in any ROM mirror/alignment")
    def inside(target):return any(a<=target<b for a,b in ranges)
    for index,(word,) in enumerate(struct.iter_unpack("<I",before)):
        if word==0xFFFFFFFF:continue
        at,target=index*4,None
        if word&0x0E000000==0x0A000000:
            d=word&0xFFFFFF;d-=0x1000000 if d&0x800000 else 0;target=at+8+d*4
        elif word&0x0F7F0000==0x051F0000:
            target=at+8+(1 if word&0x800000 else -1)*(word&4095)
        elif word&0x0E1F0000==0x020F0000 and (word>>21)&15 in (2,4):
            rot,value=((word>>8)&15)*2,word&255
            imm=((value>>rot)|(value<<(32-rot)))&0xFFFFFFFF if rot else value
            target=at+8+(imm if (word>>21)&15==4 else -imm)
        need(target is None or not inside(target),"no ARM branch/literal/ADR allocation owner")
    classified=[]
    for index,(word,) in enumerate(struct.iter_unpack("<H",before)):
        at,target,kind=index*2,None,None
        if word&0xF800 in (0x4800,0xA000):
            target=((at+4)&~3)+(word&255)*4;kind="literal/ADR"
        elif word&0xF800==0xE000:
            d=word&0x7FF;d-=0x800 if d&0x400 else 0;target=at+4+d*2;kind="B"
        elif word&0xF000==0xD000 and word&0x0F00<0x0E00:
            d=word&255;d-=256 if d&128 else 0;target=at+4+d*2;kind="conditional B"
        elif word&0xF800==0xF000 and at+4<=len(before):
            low=h(before,at+2)
            if low&0xF800==0xF800:
                d=word&0x7FF;d-=0x800 if d&0x400 else 0
                target=at+4+(d<<12)+((low&0x7FF)<<1);kind="BL pair"
        if target is not None and inside(target):
            need((at,word,target,kind)==(0x5846D2,0xE310,0x584CF6,"B"),"no unclassified Thumb allocation owner")
            need(u(before,0x5846D0)==0xE3100C02 and branch_target(before,0x583934)==0x584600,"Thumb-like halfword belongs to reached ARM handler")
            sequence(before,0x5846D0,["tst r0, #0x200","beq #0x858473c"])
            sequence(before,0x584600,["push {r0, r1, r2, r3, r4, r5, r6, r7, r8, lr}"])
            need(sha(cut(before,0x584600,0x154))=="3CA75DB08CC5763E96F8ECEDDE5E149A84F523E00707CDC78C39E3EDE7AA29B5","complete ARM owner from called entry through epilogue")
            classified.append(dict(halfword=at,word=word,apparent_target=target,arm_instruction=0x5846D0,arm_entry=0x584600,arm_caller=0x583934,
                reason="Upper half of reachable ARM E3100C02 TST r0,#200; not a separate Thumb entry."))
    need(len(classified)==1,"explicitly report the one classified mixed-ISA false positive")
    return classified


def candidate(before,after,new):
    need(len(before)==len(after)==0x800000,"candidate extent")
    record=cut(new,SOURCE_RECORD+32,14)+bytes(2)+struct.pack("<I",BASE+SLOT)
    expected=bytearray(before);expected[RECORD:RECORD_END]=record;expected[CODE:END]=helper_expected(before)
    for at,old,word in PHASE_EDITS:struct.pack_into("<I",expected,at,word)
    need(after==expected,"exact source-derived156-byte layer; no additional writes")
    inverse=bytearray(after)
    for start,end in WRITES:inverse[start:end]=before[start:end]
    need(inverse==before,"full-image inverse")
    rows=[]
    for index,callback in enumerate((0x585200,0x585500,CODE)):
        native=0x584CC0+20*index;source=SOURCE_RECORD+16*index
        need(cut(after,native,12)==cut(new,source,12) and u(after,native+12)==h(new,source+12),"all three complete consumed native records preserve six typed fields and count")
        slot=ptr(after,native+16,4)
        need(slot==(0x584D88,0x584D8C,SLOT)[index] and ptr(after,slot)==callback,"every native callback slot resolves its exact source mode representative")
        need(u(after,callback+8)==0xE3A00000+index+1,"all three entry modes match source1/2/3")
        if index<2:need(cut(after,native,20)==cut(before,native,20),"first two records remain byte-identical")
        rows.append(dict(index=index,native=native,source=source,fields=list(struct.unpack("<6h",cut(after,native,12))),callback_count=u(after,native+12),slot=BASE+slot,callback=BASE+callback))
    need(cut(after,RECORD_END,4)==cut(before,RECORD_END,4)==b"\xff"*4,"four-byte guard before next record family retained")
    need(cut(after,0x629500,32)==cut(before,0x629500,32),"separate stage-priority layer excluded")
    need(aliases(after,CODE,END)==[(RECORD+16,BASE+SLOT),(SLOT,BASE+CODE)],"exact new callback-slot and entry aliases; no hidden interior or mirror aliases")
    need(not aliases(after,RECORD,RECORD_END),"third record reached by proven table indexing, not an unaccounted literal")
    return rows


def negatives(before,after,gba,old,new):
    rejected=[]
    def reject(label,check):
        try:check()
        except (ValueError,IndexError,KeyError,struct.error):rejected.append(label)
        else:raise ValueError("negative accepted: "+label)
    def changed(data,at,mask=1):
        out=bytearray(data);out[at]^=mask;return out
    # Call the bounded expected-image check without re-running large alias scans.
    def exact(data):
        expected=bytearray(before)
        expected[RECORD:RECORD_END]=cut(new,SOURCE_RECORD+32,14)+bytes(2)+struct.pack("<I",BASE+SLOT)
        expected[CODE:END]=helper_expected(before)
        for at,_,word in PHASE_EDITS:struct.pack_into("<I",expected,at,word)
        need(data==expected,"independent expected image")
    for start,end in WRITES:
        for at in range(start,end):reject(f"declared byte {at:X}",lambda at=at:exact(changed(after,at)))
    for at in (RECORD-1,RECORD_END,CODE-1,END,0x584CC0,0x584D00,0x58467C,0x585274,0x585310,0x629500,0x629480,0x628300):
        reject(f"outside-layer byte {at:X}",lambda at=at:exact(changed(after,at)))
    reject("truncated candidate",lambda:exact(after[:-1]))
    for at in range(MODE3,SOURCE_END):reject(f"source family byte {at:X}",lambda at=at:source_proof(changed(new,at)))
    for at in (0x744F51,0x744F55,0x745151,0x745153,0x74527D,0x745285,0x74529B,0x745125):
        reject(f"source boundary/selector {at:X}",lambda at=at:source_proof(changed(new,at)))
    for index in range(3):
        for offset in range(0,16,2):
            at=SOURCE_RECORD+index*16+offset
            reject(f"source record{index} field{offset}",lambda at=at:source_proof(changed(new,at)))
    for offset in range(0,128,4):
        reject(f"relocated helper word {offset:X}",lambda offset=offset:helper_contract(before,changed(after,CODE+offset)))
    for at in (0x585278,0x585298,0x5852C4,0x5852CC,0x5852F4,0x585304,0x585314,0x585320,0x58534C,0x58537C):
        reject(f"shared wait/exit {at:X}",lambda at=at:helper_contract(before,changed(after,at)))
    for at in (0x58467C,0x5846F4,0x584704,0x58462C,0x584630,0x584800,0x136AC,0x136E4,0x13774):
        reject(f"phase/owner contract {at:X}",lambda at=at:phase_contract(before,changed(after,at),new))
    for at in (0x76AC37,0x76ACAC,0x76ACC6,0x76ABC3,0x76ABCB):
        reject(f"source phase contract {at:X}",lambda at=at:phase_contract(before,after,changed(new,at)))
    for at in (0x36D304,0x36D330,0x36D79C,0x36D7CC,0x36D83C,0x36D848,0x36D85C):
        reject(f"actual native selector/field consumer {at:X}",lambda at=at:selector_consumers(before,changed(after,at),new))
    for at in (0x74403A,0x744070,0x7442DD,0x7442F8,0x744319,0x744331,0x74433E):
        reject(f"actual source selector/field consumer {at:X}",lambda at=at:selector_consumers(before,after,changed(new,at)))
    reject("source sine value",lambda:core_services(before,after,gba,old,changed(new,0x7519C9)))
    reject("old sine value",lambda:core_services(before,after,gba,changed(old,0x39858D),new))
    reject("native sine value",lambda:core_services(before,changed(after,0x12360),gba,old,new))
    for start,end in ((RECORD,RECORD_END),(CODE,END)):
        reject(f"occupied allocation {start:X}",lambda start=start:reservation(changed(before,start)))
        for mirror in (8,10,12):
            bad=bytearray(before);struct.pack_into("<I",bad,0x101,(mirror<<24)+start+1)
            reject(f"unaligned mirror{mirror:X} pointer {start:X}",lambda bad=bad:reservation(bad))
    for label,word,half in (("ARM branch",0xEA00003E,False),("ARM literal",0xE59F00F8,False),("ARM ADR",0xE28F00F8,False),
                            ("Thumb literal",0x483F,True),("Thumb ADR",0xA03F,True),("Thumb B",0xE07E,True),("Thumb conditional B",0xD07E,True)):
        bad=bytearray(before);struct.pack_into("<H" if half else "<I",bad,CODE-0x100,word)
        reject(label+" inbound owner",lambda bad=bad:reservation(bad))
    bad=bytearray(before);struct.pack_into("<HH",bad,CODE-0x100,0xF000,0xF87E)
    reject("Thumb BL inbound owner",lambda:reservation(bad))
    for at in (0x5846D0,0x583934,0x584600):
        reject(f"false-positive classification prerequisite {at:X}",lambda at=at:reservation(changed(before,at)))
    return rejected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("before","after","gba","old","new","output"):parser.add_argument(key,type=Path)
    args=parser.parse_args();paths=[args.before,args.after,args.gba,args.old,args.new]
    need(all(p.suffix.lower() in (".gba",".wsc") for p in paths),"explicit ROM inputs only")
    need(args.output.suffix.lower()==".json","JSON report output only")
    before,after,gba,old,new=[p.read_bytes() for p in paths]
    need(tuple(map(sha,(before,after,gba,old,new)))==(BEFORE,AFTER,GBA,OLD,NEW),"five pinned input identities")
    source=source_proof(new);selectors=selector_consumers(before,after,new)
    services=core_services(before,after,gba,old,new);helper=helper_contract(before,after)
    phases=phase_contract(before,after,new);classified=reservation(before);rows=candidate(before,after,new)
    rejected=negatives(before,after,gba,old,new)
    report=dict(status="PASS",kind="independent-waterfall-third-pattern",inputs=dict(zip(("before","after","gba","old","new"),map(sha,(before,after,gba,old,new)))),
        source=source,selector_consumers=selectors,installed_records=rows,services=services,helper=helper,phase2=phases,
        writes=[dict(start=a,end=b,bytes=b-a,before_sha256=sha(before[a:b]),after_sha256=sha(after[a:b])) for a,b in WRITES],
        declared_bytes=sum(b-a for a,b in WRITES),changed_bytes=sum(a!=b for a,b in zip(before,after)),full_inverse=True,
        allocation=dict(ranges=[[RECORD,RECORD_END],[CODE,END]],empty=True,all_alignment_rom_mirrors=[8,10,12],arm_branch_literal_adr=True,
            thumb_literal_adr_conditional_branch_unconditional_branch_bl=True,classified_thumb_candidates=classified),
        negative_count=len(rejected),negative_cases=rejected,
        limits=["This is the156-byte third-pattern and phase2 successor-clear layer; separate stage-priority/getter changes are excluded.",
            "All three mode record/owner paths are bounded, but full Waterfall mechanics, camera, physics and whole-campaign stability are separate validation.",
            "Existing native setter, animation, reset and scheduling conventions are retained; no universal source/native timing or full downstream service parity is claimed.",
            "Runtime open-bus values are not used as a portable oracle. No emulator, target execution or save access is performed."])
    need((report["declared_bytes"],report["changed_bytes"])==(156,151),"exact declared/changed byte census")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(dict(status="PASS",report_sha256=sha(args.output.read_bytes()),negatives=len(rejected),declared_bytes=156,source_family_bytes=229)))


if __name__=="__main__":
    main()
