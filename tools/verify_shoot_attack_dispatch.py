#!/usr/bin/env python3
"""Independent source and actual-ARM verification of Shoot attack consumers.

No production builder imports, emulator, save or guest-state writes.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_ARCH_ARM, CS_MODE_ARM
import verify_shoot_caller_resident as resident
from verify_shoot_caller_resident import Arm, signed, rotate

BASE = 0x08000000
INPUT = '72A03EA9267A35E8B9CCECC110D2BA3F7E9DF99422480E3CCE08C18AE3B5F4BC'
ORIGINALS = ('996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED',
 '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735',
 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7')
FIRST, END, LIMIT = 0x6FD000, 0x6FD720, 0x6FD800
HOOK=0x36EB9C
TABLES=tuple(0x6FD480+60*k for k in range(5))
RECORDS=(0x6FD5C0,0x6FD640,0x6FD6C0)
WRAPPERS=(0x6FD280,0x6FD300,0x6FD380)
CONTINUATIONS=(0x0836A8AC,0x0836AB18,0x0836AF64)
INTERPRETER='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def need(value, label):
    if not value: raise ValueError(label)


def sha(blob): return hashlib.sha256(blob).hexdigest().upper()
def h(blob, at): return struct.unpack_from('<H',blob,at)[0]
def u32(blob, at): return struct.unpack_from('<I',blob,at)[0]


def source_contract(gba, old, new, before):
    need(gba[0x36EB30:0x36EC14] == before[0x36EB30:0x36EC14], 'retained actual retail dispatch')
    need(struct.unpack_from('<2I',gba,0x36EBF0)==(0x03004D28,0x03004D20), 'typed source additions overread retail literals')
    old_table=struct.unpack_from('<18H',old,0x3A4AC3)
    new_table=struct.unpack_from('<20H',new,0x76059F)
    need(old_table[-1]==0xAAA and new_table[-2:]==(0xB89,0xC01), 'exact18 versus20 source attack dispatch population')
    for at,target in ((0x30F2,0x3688),(0x3110,0x3708),(0x303E,0x3388),(0x305C,0x3408),(0x312E,0x3788)):
        need(struct.unpack_from('<15H',new,0x75FFD0+at)==(target,)*15,'complete actual source fifteen-fighter view')
    native_table=struct.unpack_from('<18I',gba,0x36EBA8)
    need(all(0x0836EC14<=x<=0x0836F37C for x in native_table) and native_table[-1]==0x0836F37C,
         'eighteen native executable destinations before literal pool')
    record_sets=[]
    for name,src,ancestor,native,count,old_cb,new_cb,native_cb in (
        ('1A-ground',0x763658,0x3A6FCE,0x36C12C,4,0xE46,0x17DF,0x0836A834),
        ('1A-air',0x7636D8,0x3A704E,0x36C1AC,4,0xFAA,0x1905,0x0836AAC0),
        ('1B-air',0x763758,0x3A724E,0x36C3AC,3,0x11EF,0x19B6,0x0836AE94),
        ('1A-evolved-ground-retained',0x763358,0x3A70CE,0x36C22C,4,0xE46,0xFE2,0x0836A834),
        ('1A-evolved-air-retained',0x7633D8,0x3A714E,0x36C2AC,4,0xFAA,0x1146,0x0836AAC0)):
        for k in range(count):
            a=new[src+k*32:src+(k+1)*32];b=old[ancestor+k*32:ancestor+(k+1)*32]
            need(a[:4]==b[:4] and a[8:]==b[8:], 'all source attack reaction metadata and event identical '+name)
            need(struct.unpack_from('<2H',a,4)==(new_cb,0x5FFD) and
                 struct.unpack_from('<2H',b,4)==(old_cb,0xA45B), 'source constructor lineage '+name)
            need(u32(gba,native+k*32+4)==native_cb,'commercial native constructor oracle '+name)
        record_sets.append(dict(name=name,source=src,ancestor=ancestor,native=native,count=count))
    c=Cs(CS_ARCH_X86,CS_MODE_16)
    copies=[]
    for normal,start,end,delta in ((0x760FF1,0x7617E7,0x7618D5,0x7F6),
            (0x761143,0x7618FB,0x761986,0x7B8),(0x7613CF,0x7619F3,0x761DD3,0x624)):
        a=list(c.disasm(new[normal:normal+end-start],normal))
        b=list(c.disasm(new[start:end],start))
        need(len(a)==len(b) and sum(i.size for i in b)==end-start,'complete continuation decode')
        for x,y in zip(a,b,strict=True):
            need(x.mnemonic==y.mnemonic, 'continuation operation identity')
            if x.op_str==y.op_str: continue
            if x.mnemonic.startswith('j'):
                need(int(y.op_str,0)-int(x.op_str,0)==delta,'continuation direct branch relocation')
            elif x.mnemonic=='mov' and x.op_str.startswith('word ptr [si], 0x') and y.op_str.startswith('word ptr [si], 0x'):
                need(int(y.op_str.split(', ')[1],0)-int(x.op_str.split(', ')[1],0)==delta,
                     'continuation callback relocation')
            else: raise ValueError('unmapped continuation difference')
        copies.append(dict(normal=normal,new=start,end=end,instructions=len(b)))
    need([p['instructions'] for p in copies]==[71,43,336],'complete three continuation populations')
    for normal,start,end in ((0x760FB2,0x7617B4,0x7617DD),
                            (0x761116,0x7618DA,0x7618F1),
                            (0x76135B,0x76198B,0x7619E9)):
        need(new[normal:normal+end-start]==new[start:end], 'constructor common byte identity')
        need(new[start-5:start]==bytes.fromhex('9A30309040'),'each new constructor invokes actual HP/orb service')
    need(new[0x76129C:0x7612A1]==bytes.fromhex('9A30309040'),'source paired HP/orb call')
    need(u32(gba,0x36AD68)==0xEBFF58B1,'actual commercial paired native HP/orb call')
    # Actual child commands and pointers, read without any converter import.
    populations=[]
    for raw in (0x3D23B0,0x0DFEC0,0x3CF410,0x3BD730,0x3D1E30):
        count=(h(new,raw+6)-4)//8; refs=set()
        for e in range(count):
            n,p,_,_=struct.unpack_from('<4H',new,raw+4+e*8)
            refs.update(h(new,raw+p+j*12+10) for j in range(n))
        refs.discard(0)
        populations.append(dict(resource=raw,events=count,attacks=[(raw+p,h(new,raw+p)) for p in sorted(refs)]))
    need(sorted({t for p in populations for _,t in p['attacks']})==[25,26,27],'whole five-resource typed attack population')
    for raw,commands,expected in ((0x5C4800,1,27),(0x5C4C00,3,26)):
        found=0
        for e in range(commands):
            n,p,_,_=struct.unpack_from('<4I',before,raw+8+e*16)
            for j in range(n):
                tail=u32(before,p-BASE+j*16+12)
                if tail:
                    need(h(before,tail-BASE)==expected,'actual converted attack type retained')
                    found+=1
        need(found==(5 if expected==27 else 8),'actual converted attack frame population')
    return dict(native_attack_types=[8,25],added_source_types=[26,27],
        record_oracles=record_sets,normalized_continuations=copies,resource_populations=populations)


class Machine(Arm):
    """Strict independent ARM interpreter, with explicit imported-call contracts."""
    def __init__(self, rom, seed=0, flags=0x10):
        super().__init__(rom,seed,flags)
        self.services={}

    def shifted(self,w):
        if w&0x02000000: return rotate(w&255,((w>>8)&15)*2)
        need(not w&16,'only immediate register shift')
        value=self.r[w&15];n=(w>>7)&31;k=(w>>5)&3
        if k==0:return (value<<n)&0xFFFFFFFF
        if k==1:return value>>(n or 32)
        if k==2:return (signed(value,32)>>(n or 32))&0xFFFFFFFF
        return rotate(value,n)

    def run(self,start,stops,max_steps=4096):
        pc=start
        for _ in range(max_steps):
            if pc in stops:return pc
            w=self.get(pc);self.r[15]=pc+8;nxt=pc+4
            if not self.condition(w>>28):pc=nxt;continue
            if w&0x0FFFFFF0==0x012FFF10:nxt=self.r[w&15]
            elif w&0x0FFF0FFF==0x010F0000:self.r[(w>>12)&15]=self.cpsr
            elif w&0x0FFFFFF0==0x0128F000:self.cpsr=(self.cpsr&0x00FFFFFF)|(self.r[w&15]&0xFF000000)
            elif w&0x0E000000==0x08000000:
                need(w&0x0FFF0000 in (0x092D0000,0x08BD0000),'reviewed PUSH/POP only')
                regs=[i for i in range(16) if w&(1<<i)];load=bool(w&0x100000)
                address=self.r[13] if load else self.r[13]-4*len(regs)
                for i,reg in enumerate(regs):
                    if load:self.r[reg]=self.get(address+4*i)
                    else:self.put(address+4*i,self.r[reg],log=True)
                self.r[13]+=(1 if load else -1)*4*len(regs)
                if load and 15 in regs:nxt=self.r[15]
            elif w&0x0E000000==0x0A000000:
                nxt=pc+8+signed(w&0xFFFFFF,24)*4
                if w&0x1000000:
                    self.r[14]=pc+4;self.calls.append((pc,nxt,tuple(self.r[:5])))
                    if nxt in self.services:self.services[nxt](self);nxt=pc+4
            elif w&0x0C000000==0x04000000:
                need((w&0x1000000 and not w&0x200000) or (w>>16)&15==13,'writeback only stack base')
                offset=self.shifted(w&~0x02000000) if w&0x02000000 else w&0xFFF
                base=(w>>16)&15;updated=(self.r[base]+(offset if w&0x800000 else -offset))&0xFFFFFFFF
                address=updated if w&0x1000000 else self.r[base]
                reg=(w>>12)&15;size=1 if w&0x400000 else 4
                if w&0x100000:self.r[reg]=self.get(address,size)
                else:self.put(address,self.r[reg],size,True)
                if w&0x200000 or not w&0x1000000:self.r[base]=updated
                if reg==15 and w&0x100000:nxt=self.r[15]
            elif w&0x0E000090==0x00000090:
                need(w&0x1400000==0x1400000 and not w&0x200000,'immediate halfword transfer')
                offset=((w>>4)&0xF0)|(w&15);address=self.r[(w>>16)&15]+(offset if w&0x800000 else -offset)
                reg=(w>>12)&15;kind=(w>>5)&3
                if w&0x100000:
                    value=self.get(address,1 if kind==2 else 2)
                    self.r[reg]=(signed(value,8 if kind==2 else 16) if kind in (2,3) else value)&0xFFFFFFFF
                else:need(kind==1,'only STRH');self.put(address,self.r[reg],2,True)
            elif w&0x0C000000==0:
                op=(w>>21)&15;dest=(w>>12)&15;l=self.r[(w>>16)&15];r=self.shifted(w)
                if op in (2,10):value=(l-r)&0xFFFFFFFF
                elif op==3:value=(r-l)&0xFFFFFFFF
                elif op==4:value=(l+r)&0xFFFFFFFF
                elif op in (0,8):value=l&r
                elif op==1:value=l^r
                elif op==12:value=l|r
                elif op==13:value=r
                elif op==14:value=l&~r
                elif op==15:value=~r&0xFFFFFFFF
                else:raise ValueError('unreviewed ARM operation')
                if op in (8,10) or w&0x100000:
                    flags=(value&0x80000000)|(0x40000000 if value==0 else 0)
                    if op in (2,10):
                        flags|=(0x20000000 if l>=r else 0)|(((l^r)&(l^value)&0x80000000)>>3)
                        self.cpsr=(self.cpsr&0x0FFFFFFF)|flags
                    else:self.cpsr=(self.cpsr&0x3FFFFFFF)|flags
                if op not in (8,10):self.r[dest]=value&0xFFFFFFFF
            else:raise ValueError(f'unreviewed ARM instruction {pc:08X}:{w:08X}')
            pc=nxt
        raise ValueError('bounded actual ARM execution did not return')


def structural(before,after,gba):
    need(len(before)==len(after)==0x800000,'whole ROM extent')
    inverse=bytearray(after)
    inverse[HOOK:HOOK+4]=before[HOOK:HOOK+4]
    inverse[FIRST:END]=before[FIRST:END]
    need(inverse==before,'whole two-span inverse including all padding')
    need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'whole unused reservation FF')
    need(u32(before,HOOK)==0xE28F8004,'original ADD dispatch boundary')
    hook=u32(after,HOOK)
    need(hook>>24==0xEA and BASE+HOOK+8+signed(hook&0xFFFFFF,24)*4==BASE+FIRST,'actual unlinked dispatch tail hook')
    need(after[END:LIMIT]==b'\xff'*(LIMIT-END),'reservation tail unchanged')
    for a,z in ((0x341034,0x34136C),(0x3555D0,0x35568C),
            (0x36EBA0,0x36EC14),(0x36EC14,0x36ED40),
            (0x36A8AC,0x36AAC0),(0x36AB18,0x36AC20),
            (0x36AF64,0x36BA90)):
        need(after[a:z]==before[a:z],f'exact retained consumer {a:X}')
        if a==0x341034:
            need(before[a:z]==gba[a:z] and sha(gba[a:z])=='9B16BDE5A4397680DD768E19C3634DBBF37A30BB3A05F9D80DEEDC0FD4AEDB37',
                 'commercial HP/orb imported helper full code+literal pool')
    need(after[0x33FCCC:0x33FDC0]==gba[0x33FCCC:0x33FDC0] and
         after[0x34059C:0x3407F4]==gba[0x34059C:0x3407F4] and
         after[0x5C9900:0x5C9B00]==b'\xff'*0x200,'retail external scene route remains closed')
    for k,(native,count) in enumerate(((0x36C12C,4),(0x36C1AC,4),(0x36C3AC,3))):
        expected=bytearray(gba[native:native+count*32])
        for row in range(count):struct.pack_into('<I',expected,row*32+4,BASE+WRAPPERS[k])
        need(after[RECORDS[k]:RECORDS[k]+count*32]==expected,'complete retail record inverse except typed constructor')
    for at,target in zip(TABLES,(*RECORDS[:2],0x36C22C,0x36C2AC,RECORDS[2])):
        need(struct.unpack_from('<15I',after,at)==(BASE+target,)*15,'actual complete15row source-prescribed view')
    for a,z in ((0x6FD044,0x6FD080),(0x6FD13C,0x6FD180),(0x6FD1F8,0x6FD280),
            (0x6FD2E4,0x6FD300),(0x6FD344,0x6FD380),(0x6FD43C,0x6FD480),(0x6FD5AC,0x6FD5C0)):
        need(after[a:z]==b'\xff'*(z-a),'complete declared unused padding FF')
    for start,body,end,continuation in zip(WRAPPERS,(0x36A838,0x36AAC4,0x36AE98),
             (0x36A880,0x36AAEC,0x36AF38),CONTINUATIONS):
        need(u32(after,start)==0xE52DE004,'single balanced LR save')
        call=u32(after,start+4)
        need(call>>24==0xEB and BASE+start+12+signed(call&0xFFFFFF,24)*4==0x08341034,'direct actual HP/orb helper call')
        need(after[start+8:start+8+end-body]==gba[body:end],'entire constructor motion body retail oracle')
        tail=start+8+end-body
        need(struct.unpack_from('<5I',after,tail)==(0xE59F8008,0xE5848000,0xE49DE004,0xE12FFF1E,continuation),
             'exact direct continuation and balanced return, no freeze')


def setup(rom,seed=0):
    m=Machine(rom,seed,0xA0000010)
    m.r[4],m.r[5],m.r[11]=0x03003000,0x03005000,0
    for base,size in ((0x03003000,0x200),(0x03005000,0x200),(0x03004D20,0x20)):
        for off in range(size):m.put(base+off,(off*13+seed)&255,1)
    return m


def dispatch_cases(rom):
    count=0
    for typ,nzcv,control in itertools.product((*range(8,28),0,1,7,28,255,65535),range(16),(0x10,0xD3)):
        m=Machine(rom,typ+nzcv,(nzcv<<28)|control)
        m.r[1]=((typ-8)*2)&0xFFFFFFFF
        initial=m.r[:15];flags=m.cpsr
        expected=0x086FD080 if typ==26 else 0x086FD180 if typ==27 else 0x0836EBA0
        end=m.run(BASE+HOOK,{0x086FD080,0x086FD180,0x0836EBA0})
        need(end==expected,'actual type discrimination')
        if typ not in (26,27):initial[8]=0x0836EBA8
        need(m.r[:15]==initial and m.cpsr==flags,'dispatch exact live ABI and flags')
        need(all(initial[13]-8<=a<initial[13] for a,_,_ in m.writes),'dispatch stack-only ownership')
        count+=1
    return count


def handler_case(rom,typ,hp=100,air=0,evolved=0,identity=14,variant=2,run_reader=False):
    m=setup(rom,identity+variant)
    victim=m.r[5];attacker=m.r[4];sp=m.r[13]
    m.put(victim+0x64,hp,2);m.put(victim+6,air,2)
    old_flags=0x20E4|evolved;m.put(victim+8,old_flags,2)
    m.put(victim+0x11,identity,1)
    m.put(0x03004D26,variant,1)
    m.put(0x030048C0,0x1234,2);m.put(0x030048C2,0x5678,2)
    effect=[];sound=[];events=[]
    def visual(cpu):
        args=[cpu.get(cpu.r[13]+i*4) for i in range(5)]
        need(args==[0x8002,0x5678,0x1234,0,victim],'actual effect call stack and point owner')
        effect.append(args)
        for r in (0,1,2,3,8,9,10):cpu.r[r]=0xBAD00000+r
        cpu.cpsr=0x50000010
    def audio(cpu):
        need(cpu.r[8:11]==[0x33,1,0],'source-common sound import arguments')
        sound.append(True)
        for r in (0,1,2,3,8,9,10):cpu.r[r]=0xCAFE0000+r
        cpu.cpsr=0x60000010
    def event(cpu):
        need([cpu.get(cpu.r[13]+i*4) for i in range(3)]==[h(rom,cpu.r[1]-BASE+2),0,victim+0xAC],
             'actual common reader event argument ABI')
        events.append(True)
        for r in (0,2,3,8,9,10):cpu.r[r]=0xABCD0000+r
    m.services={0x0835972C:visual,0x080D15C0:audio,0x08012874:event}
    end=m.run(0x086FD080 if typ==26 else 0x086FD180,{0x0836ECF4,0x0836F3B8})
    need(m.r[4]==attacker and m.r[5]==victim and m.r[13]==sp,'handler actor and stack ownership')
    if hp<=0:
        need(end==0x0836ECF4 and m.get(0x03004D26,1)==0,'dead-victim ordinary fallback and variant reset')
        need(not effect and not sound,'dead-victim has no living effect or sound')
        return
    need(end==0x0836F3B8 and len(effect)==1 and len(sound)==(typ==26),'living source path imports')
    table_index=4 if typ==27 else (2 if evolved else 0)+(1 if air else 0)
    need(m.r[1]==BASE+TABLES[table_index],'actual living conditional reaction table selection')
    need(m.get(victim+8,2)==((old_flags|0x8000)&~0xE0),'actual damage flags')
    if run_reader:
        expected_record=u32(rom,TABLES[table_index])+variant*32
        end=m.run(end,{0x0836F414})
        need(end==0x0836F414 and m.r[4]==attacker and m.r[5]==victim and m.r[13]==sp,'retained full metadata reader balances and restores actors')
        record=rom[expected_record-BASE:expected_record-BASE+32]
        need(m.get(victim)==u32(record,4),'retained common reader binds exact typed constructor')
        fields=[(0x94,int.from_bytes(record[8:10],'little',signed=True),2),
            (0x96,int.from_bytes(record[10:11],'little',signed=True),2),
            (0x98,int.from_bytes(record[11:12],'little',signed=True),2),
            (0x9C,u32(record,12),4),(0x9A,record[16],1),(0x9B,record[17],1)]
        fields += [(offset,h(record,source),2) for offset,source in zip(range(0xA0,0xAC,2),range(18,30,2))]
        for at,value,size in fields:need(m.get(victim+at,size)==value&((1<<(size*8))-1),'all retained source-mapped metadata fields')
        need(len(events)==1,'actual common reader event import once')


def handlers(rom):
    count=0
    for typ,hp in itertools.product((26,27),(-32768,-1,0)):
        handler_case(rom,typ,hp=hp);count+=1
    for typ,air,evolved,identity,variant in itertools.product((26,27),(0,1),(0,0x4000),range(15),range(3)):
        handler_case(rom,typ,air=air,evolved=evolved,identity=identity,variant=variant,run_reader=True);count+=1
    return count


def wrapper_case(rom,kind,row,facing,immunity=True):
    m=setup(rom,row+facing)
    actor=m.r[4];m.r[5]=actor+0xAC;render=m.r[5]
    record=rom[RECORDS[kind]+row*32:RECORDS[kind]+(row+1)*32]
    m.put(actor+0x94,h(record,8),2)
    m.put(actor+0x96,record[10] if immunity else 0,2)
    m.put(actor+0x98,record[11],2);m.put(actor+0x9C,u32(record,12))
    for dst,src in zip(range(0xA0,0xAC,2),range(18,30,2)):m.put(actor+dst,h(record,src),2)
    m.put(actor+6,0x3020,2);m.put(actor+8,0x2204,2);m.put(render+8,0xABCD,2)
    m.put(actor+0x64,100,2);m.put(actor+0x6C,7,1);m.put(actor+0xBC,0 if facing else 0x4000,2)
    helper=[]
    def hp_effect(cpu):
        need(cpu.r[4]==actor and cpu.r[5]==render,'retained HP helper live actor/renderer ABI')
        damage=min(cpu.get(actor+0x6C,1),cpu.get(actor+0x64,2))
        cpu.put(actor+0x64,cpu.get(actor+0x64,2)-damage,2,True)
        cpu.put(actor+0xC,(cpu.get(actor+0xC,2)&~0x4000)|(0x4000 if facing else 0),2,True)
        cpu.r[8],cpu.r[9]=0xBAD8,0xBAD9;cpu.cpsr=0x30000010
        helper.append(True)
    m.services={0x08341034:hp_effect}
    initial=m.r[:15];end=m.run(BASE+WRAPPERS[kind],{initial[14]})
    need(end==initial[14] and len(helper)==1,'typed constructor invokes actual HP helper exactly once')
    need(m.r[13]==initial[13] and m.r[14]==initial[14] and
         all(m.r[r]==initial[r] for r in (*range(2,8),11,12)),'constructor preserved ABI')
    need(m.get(actor)==CONTINUATIONS[kind],'direct no-freeze actual native continuation')
    need(m.get(actor+0x64,2)==93,'retained helper HP effect retained')
    need(m.get(actor+0x6E,1)==(9 if kind==2 else 8),'source reaction phase')
    if immunity and record[10]:
        need(m.get(actor+8,2)==0x2205 and m.get(actor+0x6F,1)==record[10],'source immunity bit and converted timer')
    else:need(m.get(actor+8,2)==0x2204,'zero immunity keeps flag')
    if kind==0:
        need(m.get(actor+6,2)==0x3060 and m.get(actor+0x73,1)==(h(record,8)+u32(record,12)+10)&255,'source ground reaction status/timer')
    if kind==2:
        factor=1 if facing else -1
        need(m.get(actor+0x42,2)==(int.from_bytes(record[20:22],'little',signed=True)*factor)&65535 and
             m.get(actor+0x46,2)==(int.from_bytes(record[22:24],'little',signed=True)*factor)&65535,
             'source horizontal reaction facing')
        need(m.get(actor+0x44,2)==h(record,24) and m.get(actor+0x48,2)==h(record,26),'actual converted upward motion and acceleration')
        need(m.get(actor+6,2)==0x3021,'airborne reaction status')
    allowed={actor,actor+6,actor+8,actor+0xC,actor+0x64,actor+0x6E,actor+0x6F,actor+0x73,
             actor+0x42,actor+0x44,actor+0x46,actor+0x48,render+8}
    need(all(a in allowed or initial[13]-4<=a<initial[13] for a,_,_ in m.writes),'constructor owned actor/renderer/stack stores only')


def wrappers(rom):
    count=0
    for kind,n in enumerate((4,4,3)):
        for row,facing,immunity in itertools.product(range(n),(0,1),(False,True)):
            wrapper_case(rom,kind,row,facing,immunity);count+=1
    return count


def negative_controls(before,after,gba,old,new):
    out=[]
    def reject(label,fn):
        try:fn()
        except (ValueError,KeyError,IndexError):out.append(label)
        else:raise ValueError('accepted direct negative: '+label)
    nop=0xE1A00000
    for at,word,label,test in (
        (0x6FD008,0xE3510022,'wrong new attack discriminator',dispatch_cases),
        (0x6FD018,nop,'legacy flags lost',dispatch_cases),
        (0x6FD040,0x0836EBAC,'legacy table shifted',dispatch_cases),
        (0x6FD094,nop,'dead variant reset absent',lambda r:handler_case(r,26,hp=0)),
        (0x6FD188,0xDA000003,'living HP branch reversed',lambda r:handler_case(r,27)),
        (0x6FD0A8,nop,'type1A sound absent',lambda r:handler_case(r,26)),
        (0x6FD1CC,nop,'living contact effect absent',lambda r:handler_case(r,27)),
        (0x6FD1D0,0xE28DD010,'contact argument stack unbalanced',lambda r:handler_case(r,27)),
        (0x6FD134,0x030048C2,'wrong contact point owner',lambda r:handler_case(r,26)),
        (0x6FD120,BASE+TABLES[1],'ground and air reaction swapped',lambda r:handler_case(r,26)),
        (0x6FD128,BASE+TABLES[0],'evolved table lost',lambda r:handler_case(r,26,evolved=0x4000)),
        (0x6FD1E8,BASE+TABLES[0],'type1B uses ground reaction',lambda r:handler_case(r,27)),
        (0x6FD384,nop,'typed HP/orb call absent',lambda r:wrapper_case(r,2,2,1)),
        (0x6FD3A0,nop,'immunity flag absent',lambda r:wrapper_case(r,2,2,1)),
        (0x6FD418,nop,'upward velocity store absent',lambda r:wrapper_case(r,2,2,1)),
        (0x6FD2E0,0x0836A880,'freeze continuation substituted',lambda r:wrapper_case(r,0,0,1))):
        changed=bytearray(after);struct.pack_into('<I',changed,at,word)
        reject(label,lambda changed=changed,test=test:test(changed))
    for at,label in ((0x6FD4B8,'last fighter table row'),(0x6FD6D8,'converted record motion'),
                     (0x1234,'outside both spans'),(0x6FD060,'declared padding ownership'),(0x341368,'last helper literal retained')):
        changed=bytearray(after);changed[at]^=1
        reject(label,lambda changed=changed:structural(before,changed,gba))
    changed=bytearray(new);changed[0x7605C5]^=1
    reject('source added type1B table target',lambda:source_contract(gba,old,changed,before))
    return out


def verify(before,after,gba,old,new,manifest):
    need(sha(Path(resident.__file__).read_bytes())==INTERPRETER,'frozen independent interpreter/census dependency')
    need(tuple(map(sha,(gba,old,new)))==ORIGINALS and sha(before)==INPUT,'exact immutable inputs')
    source=source_contract(gba,old,new,before)
    structural(before,after,gba)
    scan=types.FunctionType(resident.inbound.__code__,dict(resident.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=resident.inbound.__defaults__)
    inbound=scan(before)
    need(not inbound,'no incoming references to complete reserved free region')
    counts=dict(dispatch=dispatch_cases(after),living_dead_and_full_metadata=handlers(after),constructors=wrappers(after))
    negatives=negative_controls(before,after,gba,old,new)
    need(manifest['kind']=='shoot-attack-dispatch' and manifest['input_sha256']==sha(before)
         and manifest['output_sha256']==sha(after),'manifest actual identities')
    need(manifest['declared_write_bytes']==1828 and manifest['new_RAM_bytes']==0 and
         manifest['external_scene_entry_authorized'] is False and manifest['complete_controller_input_domain'] is False and
         manifest['historical_E5_root_cause_claim'] is False and manifest['runtime_claim'] is False,'honest manifest scope')
    need([(int(x['raw'],16),x['bytes']) for x in manifest['expected_writes']]==[(HOOK,4),(FIRST,END-FIRST)],'manifest exact declared spans')
    for item in manifest['expected_writes']:
        at=int(item['raw'],16);size=item['bytes']
        need(item['before_sha256']==sha(before[at:at+size]) and item['after_sha256']==sha(after[at:at+size]),'actual declared span hashes')
    for item in manifest['components']:
        at=int(item['raw'],16);size=item['bytes']
        need(item['sha256']==sha(after[at:at+size]),'actual every component hash')
    need(any(int(x['raw'],16)==0x341034 and int(x['end'],16)==0x34136C and x['sha256']==sha(gba[0x341034:0x34136C])
             for x in manifest['dependencies']),'manifest owns complete imported helper literal pool')
    return dict(status='PASS',input_sha256=sha(before),output_sha256=sha(after),source_contract=source,
        actual_ARM_cases=counts,negative_controls=negatives,declared_write_bytes=1828,
        changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        reservation_bytes=LIMIT-FIRST,incoming_references=len(inbound),new_RAM_bytes=0,
        independent_interpreter_census_sha256=INTERPRETER,
        imported_HP_orb_helper_sha256=sha(gba[0x341034:0x34136C]),
        source_import_pair=['76129C:4090:3030','0836AD68:BL08341034'],
        imported_services=['08341034 complete retained code+literal pool; ABI/HP-facing contract at constructor call boundary',
                           '0835972C contact effect and080D15C0 audio use checked ABI boundaries',
                           '083555D0 actual full metadata reader executed;08012874 event boundary checked'],
        external_scene_entry_authorized=False,complete_controller_input_domain=False,historical_E5_root_cause_claim=False,
        limitations=['No emulator, guest-state writes, save access or actual Shoot gameplay in this proof.',
            'Native imported helper/effect/event functions are retained retail dependencies; their complete service graphs are not emulated here.',
            'Handler direct-entry evolved cases are conditional branch tests; existing evolved pre-dispatch override remains unchanged.',
            'Global movement/camera lifetime and external Shoot route remain OPEN; historical ordinary-battle E5 is separate.'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','gba','old','source','manifest'):p.add_argument(name,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    need(all(getattr(a,n).suffix.lower() in ('.gba','.wsc') for n in ('before','after','gba','old','source')),'explicit ROM inputs only')
    need(a.manifest.suffix.lower()=='.json' and a.output.suffix.lower()=='.json','explicit report inputs/outputs')
    need(a.output.resolve() not in [getattr(a,n).resolve() for n in ('before','after','gba','old','source','manifest')],'do not overwrite inputs')
    report=verify(*(getattr(a,n).read_bytes() for n in ('before','after','gba','old','source')),json.loads(a.manifest.read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status=report['status'],sha256=sha(a.output.read_bytes()),cases=report['actual_ARM_cases'])))


if __name__=='__main__':main()
