#!/usr/bin/env python3
"""Independently check the finite Shoot scene translation without execution.

No builder/converter is imported.  Fixed complete code profiles are combined
with source receiver/control-flow checks, native instruction contracts, full
resource consumer inverses, algebraic specifications and semantic mutations.
This does not emulate either CPU or assert runtime behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16, Cs
from keystone import KS_ARCH_ARM, KS_MODE_ARM, Ks

BASE, START, END = 0x08000000, 0x5C8000, 0x5CA000
INPUTS = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
# Each fixed profile covers the complete reviewed instruction population and
# its literal pool. Code bytes exclude the two-word boundary marker/pool.
PROFILES = (
    (0x5C8000,196,160,"D9CBC71370F621498AD634FE38DFA4DD29C10F5E1E3DE16D4671B50F7BCCC686"),
    (0x5C8100,124,104,"EE1D26D50125D01D66C1174F614181D8B0393829BE809765CDC27BFEEEB0BD0E"),
    (0x5C8200,152,132,"CE73ACC6BB363A34843C5DDF81E607F26CC5230E2C80E95E72B5882D6AF19759"),
    (0x5C8300,180,152,"3BBBF7026929487760B5E5DC1CC23F3AE008767D64B9B55B56C4A5EF09B6E154"),
    (0x5C8400,164,140,"757C06D0B0C2A21EB23EEE6500FA1D3E939695E311D05862C33989DA82EE8084"),
    (0x5C8500,104,88,"5AD77BF0BD7A7547AA8ACAD60547278FC0F1A75EFF94BE5D27783C68DCFA178F"),
    (0x5C8600,76,64,"50C980B05082B107E5738AE8AB3C1D339FB77E937E454EF18D9E335C6D7DD718"),
    (0x5C8700,96,84,"8DF4642497AE74D3EDAC506BA0D52E6BAF7411E358F3323F179180811369FEB9"),
    (0x5C8800,92,76,"F7C84B452EED7896EC81FCA32744F3EACE97F2E9ABD0D39FC69EA8931EF802A4"),
    (0x5C8900,124,100,"0F939FB0CB1A5A4FF912FD1553DFC093D88513BEF50DF54744C92DC6784FFCE2"),
    (0x5C8A00,80,64,"830BBEAADD2785DF7959D1855785D75B607BFFF406B222CD21B8863DBDEAED5E"),
    (0x5C8B00,96,76,"C51F22CEBDB3C9AC11C0B5CE2F77285160DE27FE1C5C4955D9B48E2D24841B82"),
    (0x5C8C00,188,168,"3B315CEA4FB906F87E5FEFD1F6A811BA3CFBFE1AC2ED551F827A1C93C8DB04E6"),
    (0x5C8D00,120,92,"4C91AB3F6E57DAD3D532B3EA4153D1B8E4A2A8CF761061FBA7925F35E02CF4DD"),
    (0x5C8E00,348,312,"7FC2F3805AD02AC1F48F5E6980F8C6DF31EB83AF09973A255133046958AF0A6D"),
    (0x5C9000,60,48,"567A10A59F5F58C16C3968556A3AEF2C0504EBB9F872B0CE9CC6E8A959390671"),
    (0x5C9100,264,252,"A150F3C5A715F6131D6DB358676C75E011482B14C6BF331E807076CF2395CB0D"),
    (0x5C9300,228,216,"F8ADB5316CF6F645400F3560BE907770ACACBCF730DCBFA9E2778A24ED45CECB"),
    (0x5C9500,108,92,"1320CF1203697259E1D0CD806E350401D2752F482DCB8B636EB1B9C998E4C856"),
    (0x5C9600,96,76,"BD8AFE1232EFCB33A4433E4CA6F6F5F56C8C3659A07A441061F18D1344F75E7E"),
    (0x5C9700,32,0,"589AABB3C3F042B7035E4599DE2D2EE924E8E7D63C8AB7D10A854A0D48C35FFB"),
    (0x5C9800,104,96,"F8186AAE065A42C76D9AE74799396717BB4C57791087E82B7D9414EEBC444AA0"),
)
EXTERNALS = {0x0801201C,0x08012008,0x08012030,0x083524C4,0x08352374,
             0x080127E4,0x08012874,0x08012560,0x0801233C,0x08012348,
             0x080D15C0,0x085C1900,0x085C1D00,0x085C1F00,0x0801565C,
             0x080158C8,0x085C7800}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def instructions(data: bytes, raw: int, count: int, arm: bool = True, address: int | None = None) -> list:
    decoder = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    result = list(decoder.disasm(data[raw:raw + count], BASE + raw if address is None else address))
    need(sum(i.size for i in result) == count, f"incomplete decode at {raw:X}")
    return result


def at(data: bytes, raw: int, expected: list[str]) -> None:
    actual = [f"{i.mnemonic} {i.op_str}".strip() for i in instructions(data, raw, len(expected) * 4)]
    need(actual == expected, f"native semantic contract differs at {raw:X}: {actual}")


def literal(data: bytes, raw: int) -> int:
    instruction = struct.unpack_from("<I", data, raw)[0]
    need(instruction & 0x0FFF0000 == 0x059F0000, f"not positive ARM PC literal at {raw:X}")
    return struct.unpack_from("<I", data, raw + 8 + (instruction & 4095))[0]


def source_contract(wsc: bytes) -> dict:
    source = {i.address: (i.mnemonic, i.op_str) for i in
              instructions(wsc, 0x772DEA, 0x6BF, False, 0xEEA)}
    expected = {
        0xF03:("mov","word ptr [si + 0x42], 0x97"),
        0xF3F:("mov","word ptr [si + 0x46], ax"),
        0xF80:("dec","word ptr [si + 0x42]"),
        0xF98:("mov","word ptr [si + 0x42], 0xc8"),
        0xFBD:("mov","word ptr [si + 0x50], 1"),
        0xFE1:("mov","si, word ptr es:[0x65c]"),
        0xFF5:("cmp","word ptr [si + 0x26], 0xe40"),
        0xFFA:("jl","0x1002"),0x1002:("cmp","word ptr [si + 0x26], 0xdc0"),
        0x1007:("jg","0x100f"),0x1020:("mov","word ptr [si + 0x42], 5"),
        0x1053:("mov","ax, word ptr [8]"),0x1056:("add","ax, 0x10"),
        0x105A:("mov","si, ax"),0x105C:("dec","word ptr [si + 0x42]"),
        0x106E:("mov","word ptr [si + 0x1e], 0"),
        0x1073:("lcall","0x71f0, 0x161"),0x10B1:("mov","word ptr [si + 0x42], 6"),
        0x1107:("mov","ax, word ptr [si + 0x42]"),0x110A:("cmp","ax, 0"),
        0x110D:("jl","0x1124"),0x110F:("dec","word ptr [si + 0x42]"),
        0x11D9:("mov","word ptr [si + 0x42], 0x20"),
        0x123E:("lcall","0x4fff, 0x50f2"),0x1243:("lcall","0x4090, 0x7168"),
        0x1248:("mov","word ptr [si + 0x42], 0x20"),
        0x12A7:("mov","word ptr [si + 0x42], 0x96"),
        0x12DF:("dec","word ptr [si + 0x42]"),0x12E4:("cmp","word ptr [si + 0x42], 0x82"),
        0x12FB:("mov","word ptr [si + 2], 0xd2"),
        0x13BA:("xor","byte ptr es:[0x3cd], 7"),
        0x13C0:("test","word ptr [di + 6], 0x800"),
        0x1457:("mov","ax, word ptr [si + 0x46]"),
        0x145F:("mov","word ptr [di + 0x50], ax"),
        0x14C0:("mov","word ptr [si + 2], 0x9a"),
        0x14D6:("inc","word ptr [si + 0x42]"),
        0x14D9:("mov","word ptr [si + 0x44], 0x1e"),
        0x14E1:("cmp","ax, word ptr [si + 0x42]"),0x14E4:("ja","0x150e"),
        0x150E:("dec","word ptr [si + 0x44]"),
        0x1559:("dec","word ptr [si + 0x42]"),0x15A0:("lcall","0x4fff, 0xa32"),
    }
    for point, wanted in expected.items():
        need(source.get(point) == wanted, f"source scene receiver/condition changed at {point:X}")
    # Explicitly retain FC3's player timer write, not an invented task timer5.
    # After1043 rebinds SI to current task, no source read consumes its +1E.
    source_1e = [(p,m,o) for p,(m,o) in source.items() if "[si + 0x1e]" in o]
    need(source_1e == [(0xFEB,"mov","word ptr [si + 0x1e], 0"),
                       (0xFFC,"mov","word ptr [si + 0x1e], 8"),
                       (0x1009,"mov","word ptr [si + 0x1e], 2"),
                       (0x1025,"mov","word ptr [si + 0x1e], 0"),
                       (0x106E,"mov","word ptr [si + 0x1e], 0")],
         "bounded scene input-field access set changed")
    presentation = {i.address:(i.mnemonic,i.op_str) for i in
                    instructions(wsc,0x7734C9,0x187,False,0x15C9)}
    for point,wanted in {
        0x15ED:("or","ax, 0x100"),0x1625:("mov","bx, word ptr [bp + 4]"),
        0x169C:("push","5"),0x16A2:("lcall","0x4fff, 0x24cb"),
        0x16C0:("cmp","ax, word ptr [si + 0x26]"),0x16C3:("jl","0x16cb"),
        0x16C5:("mov","word ptr [si + 0x8a], 0xffe4"),
        0x16E5:("lcall","0x4fff, 0x1bd9"),0x16F4:("lcall","0x4fff, 0x19bf"),
        0x1703:("lcall","0x4fff, 0x19a8"),0x1747:("lcall","0x4090, 0x181e"),
    }.items():
        need(presentation.get(point)==wanted,f"source presentation contract differs at {point:X}")
    return {"source_scene_instructions":len(source),"source_presentation_instructions":len(presentation),
            "receiver_condition_anchors":len(expected),
            "current_task_1e_store_has_no_scene_reader":True,
            "fc3_timer5_receiver":"first player+42, translated player+52",
            "task_timers":"151 then200; FC3 fallthrough consumes199, not4",
            "same_invocation_fallthrough":["EEA->F67","FC3->1043","10DD->11F7","16BA->16D4"]}


def semantic_contract(data: bytes) -> dict:
    # These checks run before complete-profile hashes, including in mutations.
    at(data,0x5C8010,["mov r0, #0x97","strh r0, [r4, #0x50]"])
    at(data,0x5C8064,["ldr r1, [pc, #0x4c]","ldr r5, [r1]","ldrh r0, [r5, #0x64]",
                         "strh r0, [r4, #0x54]","mov r0, #1","strh r0, [r5, #0x64]"])
    at(data,0x5C8110,["ldrh r0, [r4, #0x50]","subs r0, r0, #1","strh r0, [r4, #0x50]","bne #0x85c8148"])
    at(data,0x5C8224,["ldrsh r0, [r5, #0x34]","cmp r0, #0xe40","movge r0, #8",
                         "strhge r0, [r5, #0x2c]","bge #0x85c827c","cmp r0, #0xdc0",
                         "movle r0, #2","strhle r0, [r5, #0x2c]","ble #0x85c827c"])
    at(data,0x5C8260,["mov r0, #5","strh r0, [r5, #0x52]","mov r0, #0","strh r0, [r5, #0x2c]"])
    at(data,0x5C8330,["mov r0, #0x64","strh r0, [r4, #0x50]","mov r0, #0",
                         "strh r0, [r4, #0x2c]","bl #0x85c9500"])
    at(data,0x5C8428,["ldrsh r0, [r4, #0x50]","cmp r0, #0","blt #0x85c844c",
                         "sub r2, r0, #1","strh r2, [r4, #0x50]"])
    at(data,0x5C845C,["mov r8, #0","mov sb, #2","mov sl, #0","bl #0x80d15c0",
                         "bl #0x85c9800","mov r0, #0x20","strh r0, [r4, #0x50]"])
    at(data,0x5C8510,["ldrh r0, [r4, #0x50]","bl #0x85c9300","ldrh r0, [r4, #0x50]",
                         "subs r0, r0, #1","strh r0, [r4, #0x50]","bne #0x85c8550"])
    at(data,0x5C8538,["bl #0x801565c","bl #0x85c7800","mov r0, #0x20","strh r0, [r4, #0x50]"])
    at(data,0x5C8610,["ldrh r0, [r4, #0x50]","bl #0x85c1d00"])
    at(data,0x5C8710,["ldrh r0, [r4, #0x50]","subs r0, r0, #1","strh r0, [r4, #0x50]",
                         "beq #0x85c873c","cmp r0, #0x82","bne #0x85c874c",
                         "mov r8, #0x5c","mov sb, #2","mov sl, #0","bl #0x80d15c0"])
    at(data,0x5C8810,["ldrh r0, [r4, #0x50]","bl #0x85c1f00"])
    at(data,0x5C8928,["ldrh r2, [r5, #6]","tst r2, #0x800","beq #0x85c895c",
                         "bic r0, r0, #7","strb r0, [r1]","mov r0, #0x1e","strh r0, [r4, #0x50]"])
    at(data,0x5C8B20,["ldrh r0, [r4, #0x54]","ldr r1, [pc, #0x2c]","ldr r5, [r1]",
                         "strh r0, [r5, #0x64]","mov r0, #0","strh r0, [r4, #0x50]","strh r0, [r4, #0x52]"])
    at(data,0x5C8C30,["mov r8, #0x5a","mov sb, #1","mov sl, #0","bl #0x80d15c0",
                         "ldrh r0, [r4, #0x50]","add r0, r0, #1","strh r0, [r4, #0x50]",
                         "ldrh r0, [r4, #0x50]","mov r1, #0x1e","strh r1, [r4, #0x52]",
                         "ldrh r1, [r5, #0x64]","cmp r1, r0","bhi #0x85c8c88"])
    at(data,0x5C8C88,["ldrh r0, [r4, #0x52]","sub r0, r0, #1","strh r0, [r4, #0x52]",
                         "ldrh r0, [r4, #0x50]","cmp r0, #0","blne #0x85c9600"])
    need([literal(data,p) for p in (0x5C8D30,0x5C8D38,0x5C8D40,0x5C8D48)] ==
         [0x03004510,0x08374FF4,0x03004514,0x083735BC],"exit task destinations differ")
    at(data,0x5C8D4C,["str r2, [r1]","bl #0x8012030"])
    at(data,0x5C8E24,["mov r8, #0x100","orr r8, r8, #0xb"])
    at(data,0x5C8E48,["ldr ip, [sp]"])
    need([literal(data,p) for p in (0x5C8E98,0x5C8EA8,0x5C8EB8)]==
         [0x08350248,0x083505E8,0x08352240],"constructor P1/P0/P2 order changed")
    at(data,0x5C8F18,["mov r8, #5","str r8, [sp, #-4]!","bl #0x8012874"])
    at(data,0x5C9010,["cmp r0, r2","mvnge r0, #0x1b","strhge r0, [r4, #0xa0]"])
    at(data,0x5C9174,["ldrsh r0, [r1, #0x34]","sub r0, r0, #0x100","lsl r0, r0, #0x10",
                         "asr r0, r0, #0x10","ldrsh r2, [r4, #0x34]","cmp r0, r2","bgt #0x85c91f4"])
    at(data,0x5C932C,["cmp r5, #0","moveq r5, #3","addne r5, r5, #2","cmp r5, #0x1f","movhi r5, #0x1f"])
    at(data,0x5C9508,["mov r0, #0","strh r0, [r1]","bl #0x85c1900"])
    need(literal(data,0x5C9504)==0x0203F000,"source03E8 counter binding differs")
    at(data,0x5C9618,["mov r7, #0xb","mov r6, #0x14"])
    need(literal(data,0x5C9620)==0x67FC,"native HUD tile/palette differs")
    at(data,0x5C9804,["mov fp, #0","mov r6, #0","mov r7, #0x20"])
    at(data,0x5C984C,["add r6, r6, #1","cmp r6, #4","bne #0x85c9810"])
    return {"semantic_instruction_blocks":29,"native_entry":0x085C8000,
            "full_initializer_call":0x085C7800,"all_scene_callbacks_preserve":"r0-r12,LR,SP",
            "root_allocations_added":0,"new_ram_globals":0}


def resource_contract(wsc: bytes, old: bytes, gba: bytes) -> dict:
    p1=0x3CAD70
    need(wsc[p1:p1+0x2BA]==old[0x2AE180:0x2AE43A],"P1 source ancestor differs")
    commands=[struct.unpack_from("<4H",wsc,p1+4+j*8) for j in range(7)]
    need([a[0] for a in commands]==[5,3,1,5,10,8,10],"P1 command counts differ")
    items=tails=0
    for j,(count,payload,a,b) in enumerate(commands):
        nc,np,na,nb=struct.unpack_from("<4I",gba,0x350250+j*16)
        need(count==nc and b==nb==0,"native P1 population/B pointer differs")
        need(wsc[p1+a:p1+a+8]==gba[na-BASE:na-BASE+8],"P1 A-record differs")
        for k in range(count):
            sw=list(struct.unpack_from("<6H",wsc,p1+payload+k*12))
            nw=struct.unpack_from("<6HI",gba,np-BASE+k*16)
            if sw[0]&0xFF00==0xFF00:
                sw[0]=0xFF00|(((sw[0]&255)*4+2)//5)
            tail=sw.pop()
            need(tuple(sw)==nw[:5] and nw[5]==0,"native P1 command payload differs")
            if tail:
                need(wsc[p1+tail:p1+tail+10]==gba[nw[6]-BASE:nw[6]-BASE+10],"P1 ten-byte target differs")
                tails+=1
            else:
                need(nw[6]==0,"P1 spurious tail")
            items+=1
    p0=0x3CA7D0
    table,desc=struct.unpack_from("<2I",gba,0x3505E8)
    need(wsc[p0+8:p0+16]==gba[0x3505F0:0x3505F8],"P0 constants differ")
    layout_bytes=0
    for j in range(15):
        count,relative=struct.unpack_from("<2H",wsc,p0+16+j*4)
        nc,np=struct.unpack_from("<2I",gba,table-BASE+j*8)
        need(count==nc and wsc[p0+relative:p0+relative+count*4]==gba[np-BASE:np-BASE+nc*4],"P0 layout differs")
        layout_bytes+=count*4
    pixels=0
    for j in range(21):
        count,offset,segment,bank=struct.unpack_from("<4H",wsc,0x3D4710+j*8)
        raw=(bank&127)*65536+segment*16+offset-0x20000
        nc,np=struct.unpack_from("<2I",gba,desc-BASE+j*8)
        need(nc==count,"P0 tile byte count differs")
        for tile in range(count//32):
            for y in range(8):
                planes=wsc[raw+tile*32+y*4:raw+tile*32+y*4+4]
                for x in range(8):
                    expected=sum(((planes[k]>>(7-x))&1)<<k for k in range(4))
                    packed=gba[np-BASE+tile*32+y*4+x//2]
                    need(expected==(packed>>(4*(x&1)))&15,"native P0 pixel differs")
                    pixels+=1
    need(wsc[0x3D47B8:0x3D47C0]==b"\xff"*8,"P0 descriptor terminator differs")
    need(wsc[0x3D7A60:0x3D7A66]==gba[0x352240:0x352246] and gba[0x352266:0x352268]==b"\0\0","P2 framing differs")
    for j in range(16):
        word=struct.unpack_from("<H",wsc,0x3D7A66+j*2)[0]
        channels=[(word>>shift)&15 for shift in (8,4,0)]
        native=sum((v*2+bool(v))<<(5*k) for k,v in enumerate(channels))
        need(native==struct.unpack_from("<H",gba,0x352246+j*2)[0],"native P2 channel differs")
    return {"commands":7,"payload_items":items,"nonzero_per_item_tails":tails,
            "layouts":15,"layout_bytes":layout_bytes,"descriptors":21,"pixels":pixels,"palette_colors":16}


def algebra_contract() -> dict:
    # Finite mathematical specifications; these do not execute generated code.
    expand=lambda n:0 if n==0 else 2*n+1
    native_up=lambda n:min(31,3 if n==0 else n+2)
    for n in range(16):
        need(native_up(expand(n))==expand(min(15,n+1)),"white source-lattice step differs")
    for n in range(32):
        current=n
        for _ in range(16):current=native_up(current)
        need(current==31,"white native endpoint differs")
    for counter in range(65536):
        after=(counter-1)&65535
        need((counter==1)==(after==0),"16-bit decrement zero event differs")
    # All signed source X values: boundary values DC0/E40 move, only the open
    # interval can advance. This catches <= versus < at both source edges.
    populations={"left":0,"right":0,"wait":0}
    for raw in range(65536):
        x=raw if raw<32768 else raw-65536
        choice="left" if x>=0xE40 else "right" if x<=0xDC0 else "wait"
        populations[choice]+=1
    need(populations["wait"]==127,"FC3 open interval differs")
    # Source10DD emits indices7 then6..0 after events; the eighth event starts
    # the white transition in the same invocation and consumes32->31.
    sequence=[7]+list(range(6,-1,-1))
    need(sequence==[7,6,5,4,3,2,1,0],"source eight-object sequence differs")
    hold_events=[150-k for k in range(1,151)]
    need(hold_events.index(130)==19 and hold_events[-1]==0,"hold event ordinal differs")
    channels=[(channel,side,0,32,0) for channel in range(4) for side in (1,0)]
    need(len(channels)==8,"source audio prelude request population differs")
    return {"counter_cases":65536,"signed_position_cases":65536,"position_populations":populations,
            "source_white_channels":16,"native_white_endpoints":32,
            "spawn_indices":sequence,"D2_attempt_on_hold_invocation":20,
            "audio_requests":channels,"CPU_execution":False}


def negative_contract(after: bytes, wsc: bytes) -> list[str]:
    semantic_contract(after)
    source_contract(wsc)
    mutations=[
        (0x5C8264,0xE1C505B2,0xE1C505B0,"FC3 player timer52 changed to50"),
        (0x5C8234,0xAA000010,0xCA000010,"FC3 upper equality no longer moves"),
        (0x5C8428,0xE1D405F0,0xE1D405B0,"signed spawn counter becomes unsigned"),
        (0x5C8720,0xE3500082,0xE3500081,"D2 event130 becomes129"),
        (0x5C8C60,0x8A000008,0xCA000008,"HP unsigned comparison becomes signed"),
        (0x5C8E24,0xE3A08C01,0xE3A08C41,"source010B gains unrelated4000 flag"),
        (0x5C8F18,0xE3A08005,0xE3A08000,"presentation event5 becomes0"),
        (0x5C9018,0xA1C40AB0,0xE1C40AB0,"retained angle becomes unconditional overwrite"),
        (0x5C9178,0xE2400C01,0xE2400C02,"arrival radius100 becomes200"),
        (0x5C9330,0x03A05003,0x03A05002,"white zero channel grows to2"),
        (0x5C9850,0xE3560004,0xE3560003,"audio channel3 omitted"),
    ]
    caught=[]
    for offset,old,new,label in mutations:
        need(struct.unpack_from("<I",after,offset)[0]==old,f"mutation baseline differs: {label}")
        changed=bytearray(after);struct.pack_into("<I",changed,offset,new)
        try:semantic_contract(changed)
        except ValueError:caught.append(label)
        else:raise ValueError(f"semantic negative survived: {label}")
    changed=bytearray(wsc)
    need(changed[0x772F22]==0x42,"source timer mutation baseline differs")
    changed[0x772F22]=0x44
    try:source_contract(changed)
    except ValueError:caught.append("source FC3 timer field changed")
    else:raise ValueError("source receiver mutation survived")
    return caught


def verify(before: bytes, after: bytes, sources: dict, dependencies: dict) -> dict:
    for key,expected in INPUTS.items():need(digest(sources[key])==expected,f"wrong source {key}")
    need(len(before)==len(after)==0x800000,"candidate size differs")
    need(set(dependencies)=={"input_sha256","initializer"},"dependency schema differs")
    need(digest(before)==dependencies["input_sha256"],"exact predecessor differs")
    init=dependencies["initializer"]
    need(init["entry"]==0x085C7800 and init["bytes"]>=8,"real initializer boundary differs")
    need(digest(before[0x5C7800:0x5C7800+init["bytes"]])==init["sha256"],"initializer bytes differ")
    need(before[0x5C7800:0x5C7804] not in (b"\xff"*4,bytes.fromhex("1EFF2FE1")),"initializer is still a placeholder")
    need(before[START:END]==b"\xff"*(END-START),"scene window is not owned")
    inbound=[]
    for site in range(0,len(before)-3,4):
        value=struct.unpack_from("<I",before,site)[0]
        if BASE+START<=value<BASE+END:inbound.append(site)
        if value&0x0E000000==0x0A000000:
            delta=value&0xFFFFFF
            if delta&0x800000:delta-=0x1000000
            if START<=site+8+delta*4<END:inbound.append(site)
    need(not inbound,"predecessor reaches scene window")
    source=source_contract(sources["wsc15"])
    native=semantic_contract(after)
    resources=resource_contract(sources["wsc15"],sources["wsc10"],sources["gba"])
    algebra=algebra_contract()
    all_sites={BASE+start+i for start,_,count,_ in PROFILES for i in range(0,count,4)}
    allowed=set();decoded=0;branches=[]
    encoder=Ks(KS_ARCH_ARM,KS_MODE_ARM)
    for start,total,count,expected in PROFILES:
        need(digest(after[start:start+total])==expected,f"complete scene profile changed at {start:X}")
        allowed.update(range(start,start+total))
        if not count:continue
        population=instructions(after,start,count)
        need(len(population)*4==count,"non-ARM instruction in scene")
        need(struct.unpack_from("<I",after,start)[0]==0xE92D5FFF,"whole caller register preservation changed")
        need(after[start+count-8:start+count]==bytes.fromhex("FF5FBDE81EFF2FE1"),"return register preservation changed")
        for i in population:
            encoded,_=encoder.asm(f"{i.mnemonic} {i.op_str}",i.address)
            need(bytes(encoded)==i.bytes,f"ARM encoding round trip differs at {i.address:X}")
            word=int.from_bytes(i.bytes,"little")
            need(i.mnemonic not in {"blx","bkpt","clz","movw","movt","swi","svc"},"non-ARM7/profile instruction")
            if word&0x0E000000==0x0A000000:
                delta=word&0xFFFFFF
                if delta&0x800000:delta-=0x1000000
                target=i.address+8+delta*4
                need(target in all_sites|EXTERNALS,"scene branch escapes declared graph")
                branches.append((i.address,target))
            if word&0x0FFF0000==0x059F0000:
                target=i.address+8+(word&4095)
                need(BASE+start+count<=target<=BASE+start+total-4,"PC literal escapes declared data")
        decoded+=len(population)
    changed={i for i,(a,b) in enumerate(zip(before,after,strict=True)) if a!=b}
    need(changed and changed<=allowed,"external hook or unexplained bytes changed")
    expected_changed={i for i in allowed if after[i]!=255}
    need(changed==expected_changed,"Expected Write population differs")
    for a,z in ((0x350248,0x352268),(0x127E4,0x12DB8),(0x1233C,0x126F8),
                (0x352374,0x352AC8),(0x12008,0x12058),(0xD15C0,0xD15F0),
                (0x370124,0x37016C),(0x1565C,0x15810),(0x158C8,0x158CC)):
        need(after[a:z]==sources["gba"][a:z],f"native service/resource changed at {a:X}")
    negatives=negative_contract(after,sources["wsc15"])
    return {"schema":1,"status":"PASS","kind":"independent-shoot-scene-static-verification",
            "before_sha256":digest(before),"after_sha256":digest(after),
            "source_contract":source,"native_contract":native,"resources":resources,"algebra":algebra,
            "complete_profiles":len(PROFILES),"ARM_instructions":decoded,"branch_edges":branches,
            "expected_write_bytes":len(allowed),"changed_bytes":len(changed),"semantic_negatives":negatives,
            "initializer_dependency":init,"no_external_hook":True,"no_game_execution":True,
            "limitation":"unhooked resident scene; real entry invariants and complete downstream rules remain integration gates; retail channel fade backend is a no-op"}


def main() -> int:
    parser=argparse.ArgumentParser()
    for name in ("before","after","gba","wsc10","wsc15","dependencies"):
        parser.add_argument(name,type=pathlib.Path)
    parser.add_argument("--output",required=True,type=pathlib.Path)
    args=parser.parse_args()
    sources={key:getattr(args,key).read_bytes() for key in INPUTS}
    report=verify(args.before.read_bytes(),args.after.read_bytes(),sources,
                  json.loads(args.dependencies.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"[shoot-scene-verifier] PASS: {report['ARM_instructions']} ARM instructions, {len(report['semantic_negatives'])} semantic negatives")
    return 0


if __name__=="__main__":raise SystemExit(main())
