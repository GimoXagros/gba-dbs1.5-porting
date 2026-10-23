#!/usr/bin/env python3
"""Independent final-byte verification of the private stage-manager getter.

No builder/analyzer imports or manifests. Restricted instruction evaluation
is a static proof for the exact decoded routines, not native-service or game
execution. No emulator or save access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct

BASE=0x08000000
BEFORE="B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8"
GBA="996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
OLD="58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
NEW="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
HELPER=0x629500
SITES=(0x36D28C,0x36D2F8)
SPANS=((0x36D28C,0x36D290),(0x36D2F8,0x36D2FC),(HELPER,HELPER+24))
GETTER_CALLS=(0x3EE5C,0xC8264,0xC829C,0xC86CC,0xC87CC,0x35B384,
              *SITES,0x627904,0x627D14,0x627D94,0x628694,0x6286D4,
              0x6EEF94,0x6EEFD4,0x6EF14C)
SHARED=(0xE59F802C,0xE5D8000A,0xE350000B,0x03A0000A,0x012FFF1E,
        0xE350000D,0x03A00008,0x012FFF1E,0xE350000E,0x03A00009,
        0x012FFF1E,0xE5D8000E,0xE12FFF1E,0x03002310)


def need(ok,message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data,at):
    return struct.unpack_from('<I',data,at)[0]


def target(at,w):
    imm=w&0xFFFFFF
    if imm&0x800000:
        imm-=0x1000000
    return BASE+at+8+4*imm


def core(before,after,gba,source):
    need(len(before)==len(after)==0x800000,'unchanged eight-MiB ROM size')
    need(before[HELPER:HELPER+24]==b'\xff'*24,'new helper exact FF ownership')
    need(struct.unpack_from('<4I',gba,0xD1C78)==(0xE59F8004,0xE5D8000E,0xE12FFF1E,0x03002310),
         'commercial unsigned-byte getter ABI')
    for data in (before,after):
        need(struct.unpack_from('<14I',data,0x582C40)==SHARED,'retained shared character-routing getter')
        need(word(data,0xD1C78)&0xFF000000==0xEA000000 and target(0xD1C78,word(data,0xD1C78))==0x08582C40,
             'public getter tail-branches without modifying LR')
    need(sha(source[0x743FC0:0x7440C7])=='A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6',
         'complete source manager including both actual-stage reads')
    need(sha(source[0x747A68:0x747AC7])=='1A1B4E6046E15687E8087FF14AF909546AF8F41AE3BC95964C16FB2D992CF447',
         'source Shoot writes stage11 before manager call')
    need(sha(before[0x36D224:0x36D38C])=='BAD85987BF89590DF2DE5BB72B3CECAB5DDB2118531ED25AF847FE132418F471',
         'complete predecessor manager with flag and live-register continuations')
    # First CMP overwrites flags; second continuation has AND without S, LDR,
    # then ADDS, with no conditional use of helper flags.
    need(word(after,0x36D290)==0xE3500005,'first caller overwrites flags immediately')
    need(struct.unpack_from('<3I',after,0x36D2FC)==(0xE20010FF,0xE59F9104,0xE0991181),
         'second caller overwrite of flags after unchanged unsigned index mask')
    need(word(after,0x36D2BC)==0xE20010FF and word(after,0x36D2F4)==0xE0533003,
         'first unsigned index and second live r3=0 producer')
    for at in SITES:
        old,new=word(before,at),word(after,at)
        need(old&0xFF000000==0xEB000000 and target(at,old)==0x080D1C78,'original direct BL')
        need(new&0xFF000000==0xEB000000 and target(at,new)==BASE+HELPER,'new private BL preserving link ABI')
    expected=(0xE59F800C,0xE5D8000E,0xE350000B,0x012FFF1E)
    need(struct.unpack_from('<4I',after,HELPER)==expected,'private unsigned actual-stage-first instructions')
    tail=word(after,HELPER+16)
    need(tail&0xFF000000==0xEA000000 and target(HELPER+16,tail)==0x080D1C78,'tail-B existing getter, not BL')
    need(word(after,HELPER+20)==0x03002310,'exact stage-byte owner literal')
    inverse=bytearray(after)
    for a,b in SPANS:
        inverse[a:b]=before[a:b]
    need(bytes(inverse)==before,'whole-ROM inverse including all other stage/Waterfall users')


def run_exact(data,entry,character,stage,flags=0,return_to=0x0836D290):
    """Evaluate only the exact whitelist checked by core, with immutable reads."""
    regs=[0xA1000000+0x10101*n for n in range(15)]
    regs[13]=0x03007EE4;regs[14]=return_to
    initial=tuple(regs);pc=BASE+entry;reads=[]
    for steps in range(32):
        if pc==return_to:
            need(all(regs[n]==initial[n]for n in (*range(1,8),*range(9,15))),
                 'r1-r7,r9-r12,SP,LR preserved')
            need(regs[8]==0x03002310,'r8 retains existing owner ABI')
            return regs[0],flags,tuple(reads),steps
        need(pc in (0x080D1C78,) or 0x08582C40<=pc<0x08582C74 or
             BASE+HELPER<=pc<BASE+HELPER+20,'restricted exact code path')
        w=word(data,pc-BASE);condition=w>>28;following=pc+4
        need(condition in (0,14),'only documented AL/EQ conditions')
        if condition==0 and not flags&4:
            pc=following;continue
        op=w&0x0FFFFFFF
        if op in (0x059F800C,0x059F802C):
            regs[8]=word(data,pc-BASE+8+(w&0xFFF))
        elif op in (0x05D8000A,0x05D8000E):
            offset=w&0xFFF
            need(regs[8]==0x03002310,'unsigned byte owner during actual instruction evaluation')
            regs[0]=character if offset==10 else stage
            reads.append(0x03002310+offset)
        elif op in (0x0350000B,0x0350000D,0x0350000E):
            left,right=regs[0],w&255;result=(left-right)&0xFFFFFFFF
            n=(result>>31)&1;z=int(result==0);c=int(left>=right)
            v=int(bool(((left^right)&(left^result))&0x80000000))
            flags=(n<<3)|(z<<2)|(c<<1)|v
        elif op in (0x03A0000A,0x03A00008,0x03A00009):
            regs[0]=w&255
        elif op==0x012FFF1E:
            following=regs[14]
        elif w&0xFF000000==0xEA000000:
            following=target(pc-BASE,w)
        else:
            raise ValueError(f'unexpected instruction {pc:08X}/{w:08X}')
        pc=following
    raise ValueError('restricted program did not return within32 instructions')


def routing(before,after):
    differences=[];max_steps=0
    for character in range(256):
        for stage in range(256):
            old,_,_,_ = run_exact(before,0xD1C78,character,stage)
            new,_,reads,steps = run_exact(after,HELPER,character,stage)
            expected_old={11:10,13:8,14:9}.get(character,stage)
            expected_new=11 if stage==11 else expected_old
            need((old,new)==(expected_old,expected_new),'actual instruction/source-priority truth table')
            need(reads[0]==0x0300231E,'stage owner read first')
            need(stage!=11 or reads==(0x0300231E,),'Shoot does not consult character override')
            max_steps=max(max_steps,steps)
            if new!=old:
                differences.append([character,stage,old,new])
    need(differences==[[11,11,10,11],[13,11,8,11],[14,11,9,11]],'only three byte-domain cases differ')
    cases=0
    for at in SITES:
        for flags in range(16):
            for character,stage in ((0,0),(0,5),(0,11),(11,0),(11,11),(13,8),(13,11),(14,9),(14,11),(255,255)):
                result,_,_,_=run_exact(after,HELPER,character,stage,flags,BASE+at+4)
                need(result==(11 if stage==11 else {11:10,13:8,14:9}.get(character,stage)),
                     'all incoming NZCV and both BL continuations')
                cases+=1
    return dict(byte_domain_cases=65536,differences=differences,unchanged_supported_cases=3069,
                supported_cases=3072,initial_flags_and_callers=cases,max_instruction_steps=max_steps,
                preserved_registers=['r1-r7','r9-r12','sp','lr'],result_registers=['r0','r8'],
                memory_writes=0,flags='clobbered; both actual caller continuations overwrite before use')


def scan(data,origin=0):
    """All byte alignments/mirrors; ARM and Thumb code-like ownership."""
    hits=[]
    def inside(value):
        return any(base+HELPER<=value<base+HELPER+24 for base in (BASE,0x0A000000,0x0C000000))
    for shift in range(4):
        end=len(data)-((len(data)-shift)%4)
        for n,(w,)in enumerate(struct.iter_unpack('<I',data[shift:end])):
            if inside(w):hits.append(('pointer',origin+shift+n*4,w))
    for n,(w,)in enumerate(struct.iter_unpack('<I',data[:len(data)//4*4])):
        at=origin+n*4;pc=BASE+at+8
        if w&0x0E000000==0x0A000000:
            dst=target(at,w)
            if inside(dst):hits.append(('ARM branch',at,dst))
        if w&0x0F7F0000 in (0x051F0000,0x055F0000):
            dst=pc+(w&0xFFF)*(1 if w&0x800000 else -1)
            if inside(dst):hits.append(('ARM literal',at,dst))
        if w&0x0FFF0000 in (0x028F0000,0x024F0000):
            imm,rot=w&255,((w>>8)&15)*2
            if rot:imm=((imm>>rot)|(imm<<(32-rot)))&0xFFFFFFFF
            dst=pc+(imm if w&0x01E00000==0x00800000 else -imm)
            if inside(dst):hits.append(('ARM ADR',at,dst))
    for n,(w,)in enumerate(struct.iter_unpack('<H',data[:len(data)//2*2])):
        at=origin+n*2;pc=BASE+at+4
        if w&0xF800 in (0x4800,0xA000):
            dst=(pc&~3)+(w&255)*4
            if inside(dst):hits.append(('Thumb literal/ADR',at,dst))
        if w&0xF800==0xE000:
            imm=w&0x7FF;dst=pc+2*(imm-(0x800 if imm&0x400 else 0))
            if inside(dst):hits.append(('Thumb B',at,dst))
        if w&0xF000==0xD000 and w&0x0F00<0x0E00:
            imm=w&255;dst=pc+2*(imm-(256 if imm&128 else 0))
            if inside(dst):hits.append(('Thumb conditional B',at,dst))
        if w&0xF800==0xF000 and n*2+4<=len(data):
            tail=struct.unpack_from('<H',data,n*2+2)[0]
            if tail&0xF800 in (0xF800,0xE800):
                imm=w&0x7FF
                dst=pc+((imm-(0x800 if imm&0x400 else 0))<<12)+((tail&0x7FF)<<1)
                if tail&0xF800==0xE800:dst&=~3
                if inside(dst):hits.append(('Thumb BL/BLX',at,dst))
    return hits


def callers(data,destination):
    return [at for at in range(0,len(data)-3,4)if word(data,at)&0x0E000000==0x0A000000
            and target(at,word(data,at))==destination]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('before','after','gba','old','source','output'):
        p.add_argument(n,type=Path)
    a=p.parse_args()
    need(all(getattr(a,n).suffix.lower()=='.gba'for n in ('before','after','gba'))and
         all(getattr(a,n).suffix.lower()=='.wsc'for n in ('old','source')),'ROM-only extensions before reads')
    need(a.output.suffix.lower()=='.json' and a.output.resolve()not in
         {getattr(a,n).resolve()for n in ('before','after','gba','old','source')},'distinct JSON report output')
    before,after,gba,old,source=[getattr(a,n).read_bytes()for n in ('before','after','gba','old','source')]
    need(tuple(map(sha,(before,gba,old,source)))==(BEFORE,GBA,OLD,NEW),'exact predecessor and originals')
    core(before,after,gba,source)
    semantics=routing(before,after)
    need(not scan(before),'no predecessor helper ownership')
    expected_refs=[('ARM branch',at,BASE+HELPER)for at in SITES]+[
        ('ARM literal',HELPER,BASE+HELPER+20)]
    need(scan(after)==expected_refs, 'only two intended calls and the private owner literal reference')
    need(callers(before,0x080D1C78)==list(GETTER_CALLS),'all original shared getter callers')
    need(callers(after,0x080D1C78)==sorted([at for at in GETTER_CALLS if at not in SITES]+[HELPER+16]),
         'all remaining shared getter users unchanged; new tail call accounted')
    need(callers(after,0x08582C40)==[0xD1C78],'one unchanged public implementation branch')
    negative=[]
    for start,end in SPANS:
        for at in range(start,end):
            changed=bytearray(after);changed[at]^=1
            try:core(before,bytes(changed),gba,source)
            except ValueError as e:negative.append(dict(kind='output-byte',offset=f'{at:06X}',reason=str(e)))
            else:raise ValueError(f'accepted output mutation{at:06X}')
    for at in (0x629518,0x629600,0x5846F4,0x36D2BC,0x36D304,0x582C48):
        changed=bytearray(after);changed[at]^=1
        try:core(before,bytes(changed),gba,source)
        except ValueError as e:negative.append(dict(kind='outside-write',offset=f'{at:06X}',reason=str(e)))
        else:raise ValueError('accepted unowned change')
    for at in (0x74401B,0x74401D,0x74401F,0x744025,0x744064,0x744066,0x747A95,0x747A99):
        changed=bytearray(source);changed[at]^=1
        try:core(before,after,gba,bytes(changed))
        except ValueError as e:negative.append(dict(kind='source',offset=f'{at:06X}',reason=str(e)))
        else:raise ValueError('accepted source condition mutation')
    # Independent scanner controls include all mirrors and instruction modes.
    scanner_cases=[]
    for mirror in (BASE,0x0A000000,0x0C000000):
        for interior in (0,1,20,23):
            for alignment in range(4):
                sample=bytearray(b'\xff'*64)
                struct.pack_into('<I',sample,alignment,mirror+HELPER+interior)
                need(any(h[0]=='pointer'for h in scan(sample)),'scanner rejects mirrored/interior/unaligned alias')
                scanner_cases.append('pointer')
    origin=HELPER-0x100
    arm_words=(0xEA00003E,0xEB00003E,0xE59F80F8,0xE28F00F8)
    for w in arm_words:
        sample=struct.pack('<I',w)+b'\xff'*60
        need(scan(sample,origin),'ARM branch/literal/ADR scanner control')
        scanner_cases.append('ARM')
    for h in (0x483F,0xA03F,0xE07E,0xD07E):
        sample=struct.pack('<H',h)+b'\xff'*62
        need(scan(sample,origin),'Thumb branch/literal/ADR scanner control')
        scanner_cases.append('Thumb')
    sample=struct.pack('<HH',0xF000,0xF87E)+b'\xff'*60
    need(scan(sample,origin),'Thumb BL scanner control');scanner_cases.append('Thumb BL')
    report=dict(schema=1,kind='independent-stage-priority-artifact-verification',status='PASS',
        input_sha256=sha(before),output_sha256=sha(after),original_sha256=[sha(gba),sha(old),sha(source)],
        writes=[[f'{s:06X}',f'{e:06X}']for s,e in SPANS],declared_bytes=32,
        changed_bytes=sum(a!=b for a,b in zip(before,after)),full_inverse=True,
        instruction_semantics=semantics,shared_getter_callers=[f'{BASE+x:08X}'for x in GETTER_CALLS],
        allocation=dict(predecessor_FF=True,mirrors=['08','0A','0C'],all_alignments=True,
                        arm_thumb_branches_literals_adr=True,unexpected_references=[]),
        negative_controls=negative,scanner_negative_controls=len(scanner_cases),
        negative_control_count=len(negative)+len(scanner_cases),
        limits=['Old WSC identity is checked; direct condition proof uses Ver1.5 source and USA native getter.',
                'Exact bounded instruction evaluation only; no emulator or service execution.',
                'No full Shoot entry, campaign routing, or runtime claim.'])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',report_sha256=sha(a.output.read_bytes()),
                         negative_controls=report['negative_control_count'],changed_bytes=report['changed_bytes'])))


if __name__=='__main__':
    main()
