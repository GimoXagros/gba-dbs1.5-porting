#!/usr/bin/env python3
"""Add source Shoot attack types 1A/1B without changing existing typed paths.

This internal consumer repair does not install the external Shoot scene route.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
BASE=0x08000000
INPUT='72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
OLD='58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOK=0x36EB9C
FIRST,LIMIT,END=0x6FD000,0x6FD800,0x6FD720
SPANS=((FIRST,LIMIT),)
DISPATCH,A,B=FIRST,0x6FD080,0x6FD180
CONSTRUCTORS=(0x6FD280,0x6FD300,0x6FD380)
TABLES=tuple(0x6FD480+60*k for k in range(5))
RECORDS=(0x6FD5C0,0x6FD640,0x6FD6C0)
# (new source, old source, retail native, count, native body, end, continuation)
ROWS=((0x763658,0x3A6FCE,0x36C12C,4,0x36A838,0x36A880,0x0836A8AC),
      (0x7636D8,0x3A704E,0x36C1AC,4,0x36AAC4,0x36AAEC,0x0836AB18),
      (0x763758,0x3A724E,0x36C3AC,3,0x36AE98,0x36AF38,0x0836AF64))
PINS=((0x341034,0x34136C,'9B16BDE5A4397680DD768E19C3634DBBF37A30BB3A05F9D80DEEDC0FD4AEDB37'),
 (0x36EB30,0x36EBF8,'E0629303ACE62375B1EE4EC26F5213122EB96D6EA6004C3BC0FEAC3A172367D8'),
 (0x36EC14,0x36ED40,'9804A65427C40F6BC5183BB2287F63638FFBE08F78A7A40F0AB579287DBCCA61'),
 (0x36F3B8,0x36F890,'F376F8A3180D3536444094D73B0805307B4D585F8AD418E4F444316F069928F4'),
 (0x36A8AC,0x36AAC0,'F3D187FCB59C1B0CC5C58B814E028146D8FD7942B095505A996B2D91A03D5F14'),
 (0x36AB18,0x36AC20,'D7B15F612FD66D00CE05A0C379016D0FF3FD2CCEF8C5CC5615ECB4A62EA5A9FE'),
 (0x36AF64,0x36BA90,'CB84EB5167F445EEE254EC7CF4CA7B87FD951B5FBFFBEC46EE78FA7D4B404B17'))
def need(ok,message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest().upper()
def u32(data,at): return struct.unpack_from('<I',data,at)[0]
def signed(value,bits): return value-(1<<bits) if value&(1<<(bits-1)) else value
def rotate(value,bits): return ((value>>bits)|(value<<(32-bits)))&0xFFFFFFFF if bits else value
def asm(text,raw): return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(text,BASE+raw)[0])

def inbound(data, origin=0):
    """Independent conservative references: no data/interior exemptions."""
    matches = []

    def consider(kind, at, value):
        if 0x08000000 <= value < 0x0E000000:
            raw = value & 0x01FFFFFF
            if any(start <= raw < end for start, end in SPANS):
                matches.append((kind, origin + at, value))

    for alignment in range(4):
        stop = len(data) - (len(data) - alignment) % 4
        for i, (word,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            consider("pointer", alignment + 4 * i, word)
    for i, (word,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at = 4 * i
        pc = BASE + origin + at + 8
        if word & 0x0E000000 == 0x0A000000:
            consider("ARM branch", at, pc + signed(word & 0xFFFFFF, 24) * 4)
        if (word >> 16) & 15 == 15 and word & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            consider("ARM literal", at, pc + (1 if word & 0x800000 else -1) * (word & 0xFFF))
        if word & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            immediate = rotate(word & 255, ((word >> 8) & 15) * 2)
            consider("ARM ADR", at, pc + (immediate if (word >> 21) & 15 == 4 else -immediate))
    for at in range(0, len(data) - 1, 2):
        half = int.from_bytes(data[at:at + 2], "little")
        pc = BASE + origin + at + 4
        if half & 0xF800 in (0x4800, 0xA000):
            consider("Thumb literal/ADR", at, (pc & ~3) + (half & 255) * 4)
        if half & 0xF800 == 0xE000:
            consider("Thumb B", at, pc + signed(half & 0x7FF, 11) * 2)
        if half & 0xF000 == 0xD000 and (half >> 8) & 15 < 14:
            consider("Thumb conditional", at, pc + signed(half & 255, 8) * 2)
        if half & 0xF800 == 0xF000 and at + 4 <= len(data):
            tail = int.from_bytes(data[at + 2:at + 4], "little")
            if tail & 0xF800 in (0xF800, 0xE800):
                destination = pc + (signed(half & 0x7FF, 11) << 12) + ((tail & 0x7FF) << 1)
                consider("Thumb BL/BLX", at, destination & ~3 if tail & 0xF800 == 0xE800 else destination)
    return matches


def dispatch():
    return asm(f"""
    push {{r0, ip}}
    mrs ip, cpsr
    cmp r1, #0x24
    beq type_a
    cmp r1, #0x26
    beq type_b
    msr cpsr_f, ip
    pop {{r0, ip}}
    ldr r8, old_table
    b 0x0836EBA0
 type_a:
    msr cpsr_f, ip
    pop {{r0, ip}}
    b {BASE+A:#x}
 type_b:
    msr cpsr_f, ip
    pop {{r0, ip}}
    b {BASE+B:#x}
 old_table: .word 0x0836EBA8
 """,DISPATCH)


def handler(kind):
    raw=A if kind==0x1A else B
    sound="mov r8,#0x33; mov r9,#1; mov r10,#0; bl 0x080D15C0" if kind==0x1A else ''
    select=f"""
    ldrh r8,[r5,#6]
    tst r8,#1
    ldreq r1, ground
    ldrne r1, air
    ldrh r8,[r5,#8]
    tst r8,#0x4000
    beq selected
    ldrh r8,[r5,#6]
    tst r8,#1
    ldreq r1, evolved_ground
    ldrne r1, evolved_air
 selected:
    b 0x0836F3B8
 ground: .word {BASE+TABLES[0]:#x}
 air: .word {BASE+TABLES[1]:#x}
 evolved_ground: .word {BASE+TABLES[2]:#x}
 evolved_air: .word {BASE+TABLES[3]:#x}
 """ if kind==0x1A else f"ldr r1, records; b 0x0836F3B8; records: .word {BASE+TABLES[4]:#x}"
    return asm(f"""
    ldrsh r8,[r5,#0x64]
    cmp r8,#0
    bgt alive
    ldr r8, metadata
    mov r9,#0
    strb r9,[r8,#6]
    b 0x0836ECF4
 alive:
    {sound}
    ldrh r8,[r5,#8]
    orr r8,r8,#0x8000
    strh r8,[r5,#8]
    ldr r9, point
    push {{r5}}
    push {{fp}}
    ldrh r8,[r9]
    push {{r8}}
    ldrh r8,[r9,#2]
    push {{r8}}
    ldr r8, effect_flags
    push {{r8}}
    bl 0x0835972C
    add sp,sp,#20
    ldrh r8,[r5,#8]
    bic r8,r8,#0xE0
    strh r8,[r5,#8]
    {select}
 metadata: .word 0x03004D20
 point: .word 0x030048C0
 effect_flags: .word 0x8002
 """,raw)


def constructor(gba,index):
    raw=CONSTRUCTORS[index]
    start,end,continuation=ROWS[index][4:]
    body=gba[start:end]
    ins=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,BASE+start))
    need(len(ins)*4==len(body),'complete shared native body')
    for i in ins:
        # Only local immediate branches are PC-sensitive in these exact bodies.
        if i.mnemonic.startswith('b') and i.mnemonic!='bic':
            need(i.mnemonic in ('beq','bne') and BASE+start<=int(i.op_str[1:],16)<=BASE+end,
                 'shared body has only relocation-invariant local branches')
        else:
            need('pc' not in i.op_str,'no PC-dependent shared body instruction')
    prefix=asm('push {lr}; bl 0x08341034',raw)
    tail=asm(f'ldr r8, next; str r8,[r4]; pop {{lr}}; bx lr; next: .word {continuation:#x}',raw+len(prefix)+len(body))
    return prefix+body+tail


def source_contract(source,old,gba,before):
    table_tokens=(0x30F2,0x3110,0x303E,0x305C,0x312E)
    targets=(0x3688,0x3708,0x3388,0x3408,0x3788)
    for table,target in zip(table_tokens,targets):
        need(struct.unpack_from('<15H',source,0x75FFD0+table)==(target,)*15,'exact source fifteen-row population')
    rows=[]
    for index,(new,previous,native,count,start,end,continuation) in enumerate(ROWS):
        for row in range(count):
            a=source[new+row*32:new+(row+1)*32]
            b=old[previous+row*32:previous+(row+1)*32]
            need(a[:4]==b[:4] and a[8:]==b[8:],'all source event and metadata fields match retail lineage')
            need(struct.unpack_from('<HH',a,4)==((0x17DF,0x1905,0x19B6)[index],0x5FFD),'new source callback identity')
            need(u32(gba,native+row*32+4)==(0x0836A834,0x0836AAC0,0x0836AE94)[index], 'retail constructor record oracle')
        need(before[native:native+count*32]==gba[native:native+count*32],'retained exact retail native records')
        need(before[start:end]==gba[start:end],'retained shared native constructor body')
        rows.append(dict(source=f'{new:06X}',old=f'{previous:06X}',native=f'{BASE+native:08X}',rows=count,
                         exact_metadata_bytes_per_row=24,continuation=f'{continuation:08X}'))
    # Each new source constructor prepends the same actual HP/orb helper.
    for new,common,size in ((0x7617AF,0x760FB2,41),(0x7618D5,0x761116,23),(0x761986,0x76135B,94)):
        need(source[new:new+5]==bytes.fromhex('9A30309040'),'new constructor calls4090:3030')
        need(source[new+5:new+5+size]==source[common:common+size],'source shared constructor body')
    for start,end,digest in PINS:
        need(sha(before[start:end])==digest,f'actual retained dependency{start:X}')
    need(u32(before,HOOK)==0xE28F8004,'exact old ADD r8,pc,#4 boundary')
    need(struct.unpack_from('<2I',before,0x36EBF0)==(0x03004D28,0x03004D20),'actual uncovered1A/1B RAM literals')
    need(before[0x341034:0x34136C]==gba[0x341034:0x34136C],'retained native HP/orb helper')
    return rows


def build(before,gba,old,source):
    need(tuple(map(sha,(before,gba,old,source)))==(INPUT,GBA,OLD,SOURCE),'exact predecessor and three originals')
    need(len(before)==0x800000,'candidate extent')
    rows=source_contract(source,old,gba,before)
    need(before[FIRST:LIMIT]==b'\xFF'*(LIMIT-FIRST),'whole prospective reservation is FF')
    references=inbound(before)
    need(not references,'no conservative inbound references to full reservation: '+repr(references[:4]))
    payload=bytearray(b'\xFF'*(END-FIRST))
    components=[]
    def put(at,data,label,limit):
        need(at>=FIRST and at+len(data)<=limit<=END,'component owns exact bounded slot')
        need(payload[at-FIRST:at-FIRST+len(data)]==b'\xFF'*len(data),'component slots do not overlap')
        payload[at-FIRST:at-FIRST+len(data)]=data
        components.append(dict(name=label,raw=f'{at:06X}',bytes=len(data),sha256=sha(data)))
    put(DISPATCH,dispatch(),'typed dispatch with exact legacy fallback',A)
    put(A,handler(0x1A),'source type1A',B)
    put(B,handler(0x1B),'source type1B',CONSTRUCTORS[0])
    for k,(at,limit) in enumerate(zip(CONSTRUCTORS,(*CONSTRUCTORS[1:],TABLES[0]))):
        put(at,constructor(gba,k),'no-freeze constructor'+str(k),limit)
    targets=(*RECORDS[:2],0x36C22C,0x36C2AC,RECORDS[2])
    for k,(at,target) in enumerate(zip(TABLES,targets)):
        put(at,struct.pack('<15I',*([BASE+target]*15)),'fifteen-row view'+str(k),at+60)
    for k,(at,spec) in enumerate(zip(RECORDS,ROWS)):
        native,count=spec[2:4]
        data=bytearray(gba[native:native+count*32])
        for row in range(count):struct.pack_into('<I',data,row*32+4,BASE+CONSTRUCTORS[k])
        put(at,data,'retail converted records'+str(k),at+count*32)
    after=bytearray(before)
    hook=asm(f'b {BASE+DISPATCH:#x}',HOOK)
    need(len(hook)==4,'one ARM tail branch')
    after[HOOK:HOOK+4]=hook
    after[FIRST:END]=payload
    writes=[(HOOK,4),(FIRST,len(payload))]
    inverse=bytearray(after)
    for at,size in writes:inverse[at:at+size]=before[at:at+size]
    need(inverse==before,'whole-ROM inverse contains only declared hook and payload')
    need(after[0x36EBA0:0x36EC14]==before[0x36EBA0:0x36EC14],'entire old table, dispatch load and literals retained')
    need(after[0x33FCCC:0x33FDC0]==before[0x33FCCC:0x33FDC0] and
         after[0x5C9900:0x5C9B00]==b'\xFF'*0x200,'external Shoot entry remains closed')
    report=dict(schema=1,kind='shoot-attack-dispatch',input_sha256=INPUT,output_sha256=sha(after),
        original_sha256=dict(gba=GBA,old=OLD,source=SOURCE),source_records=rows,components=components,
        expected_writes=[dict(raw=f'{at:06X}',bytes=size,before_sha256=sha(before[at:at+size]),
                             after_sha256=sha(after[at:at+size])) for at,size in writes],
        declared_write_bytes=sum(size for _,size in writes),changed_bytes=sum(a!=b for a,b in zip(before,after)),
        full_inverse=True,reservation=dict(start=f'{FIRST:06X}',limit=f'{LIMIT:06X}',FF=True,inbound_references=references,
        scans=['all-byte pointers and ROM mirrors','ARM branch/literal/ADR','Thumb branch/conditional/BL/BLX/literal/ADR']),
        dependencies=[dict(raw=f'{a:06X}',end=f'{b:06X}',sha256=h) for a,b,h in PINS],
        new_types=['1A','1B'],native_HP_orb_helper='08341034',new_RAM_bytes=0,
        old_type_dispatch_preserved=True,evolved_pre_dispatch_preserved=True,
        external_scene_entry_authorized=False,complete_controller_input_domain=False,
        runtime_claim=False,historical_E5_root_cause_claim=False)
    return bytes(after),report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ('before','gba','old','source','output'):parser.add_argument(field,type=Path)
    parser.add_argument('--manifest',required=True,type=Path)
    args=parser.parse_args()
    inputs=[args.before,args.gba,args.old,args.source]
    need(all(p.suffix.lower() in ('.gba','.wsc') for p in inputs),'explicit ROM inputs only')
    need(args.output.suffix.lower()=='.gba' and args.manifest.suffix.lower()=='.json','explicit artifact formats')
    need(args.output.resolve() not in [p.resolve() for p in inputs],'never overwrite source inputs')
    after,report=build(*(p.read_bytes() for p in inputs))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(after)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('[shoot-attack-dispatch]',sha(after),report['declared_write_bytes'],'declared bytes')
if __name__=='__main__':main()
