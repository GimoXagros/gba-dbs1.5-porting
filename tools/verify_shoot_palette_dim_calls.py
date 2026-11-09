#!/usr/bin/env python3
"""Independent actual captured palette-call/scheduler diagnosis and repair QA."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

from verify_gba_shoot_entry_capture_v2 import checkpoint_core
from verify_shoot_stage11_runtime_probe import Machine

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
BEFORE='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
AFTER='FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR='66E70D72AB1401A526ADB16A560FB0EFB18E42BE2F56B3A411358DEB1FB6BE91'
SITES=(0x5C6F4C,0x5C6F5C,0x5C6F88,0x5C6FBC)
WORDS=(0x1B000020,0x1B00001C,0x1B000011,0x1B000004)
DEPS={
 'verify_gba_shoot_entry_capture_v2.py':'4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68',
 'verify_shoot_stage11_runtime_probe.py':'259061E232A4B3C2462112711B48196EEFF736194C35E904EB1803E5B3B885E7',
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
 'verify_shoot_graphics_initializer.py':'AB0B78C1CBFA82407A6A204A1EF518C02CB671D709B11B70B5B11F4E7A5D7EA2'}

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a,n=4):return int.from_bytes(b[a:a+n],'little')
def inverse(before,after):
    need(len(before)==len(after)==0x800000,'eight MiB extent')
    out=bytearray(after)
    for at,value in zip(SITES,WORDS):
        need(u(before,at)==0x1BFFFFFE and u(after,at)==value,'exact NE+link branch word')
        need(BASE+at+8+(value&0xFFFFFF)*4==0x085C6FD4,'all four direct calls target existing local dim helper')
        out[at:at+4]=(0x1BFFFFFE).to_bytes(4,'little')
    need(bytes(out)==before,'four-word whole-ROM inverse')
def convert(v):return sum(((v>>s&15)*2+bool(v>>s&15))<<t for s,t in((8,0),(4,5),(0,10)))
def fixture(rom,snapshot,regs,flags=0):
    m=Machine(rom,0,(flags<<28)|0x10,snapshot=snapshot)
    m.r[:13]=regs[:13];m.r[13]=0x03007ECC;m.r[14]=regs[13]
    return m
def palette_plan(rom,source,iw,blink):
    groups=((u(iw,0x3D38),6),(u(iw,0x3D3C),8),(u(iw,0x3D40),5));colors=[]
    for pointer,count in groups:
        values=[]
        for j in range(count):
            offset=pointer-0x08586800+2*j
            need(0<=offset<404 and offset%2==0,'actual selected source table domain')
            color=u(source,0x76B03B+offset,2)
            need(u(rom,pointer-BASE+2*j,2)==convert(color),'actual source/native selected color')
            values.append(convert((color&0xEEE)>>1)if blink else convert(color))
        colors.append(values)
    writes=[]
    for j in range(3):writes.extend(((0x05000010+32*j,colors[0][2*j]),(0x05000012+32*j,colors[0][2*j+1])))
    for j in range(8):writes.extend((0x05000064+32*k+2*j,colors[1][j])for k in range(3))
    writes.extend((0x050000C4+2*j,colors[2][j])for j in range(5))
    return writes

def audit(before,after,source,capture):
    need(tuple(map(sha,(before,after,source)))==(BEFORE,AFTER,SOURCE),'frozen predecessor/repaired/source identities')
    need(sha((ROOT/'tools/build_shoot_palette_dim_calls.py').read_bytes())==AUTHOR,'frozen author')
    for name,digest in DEPS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen independent helper '+name)
    inverse(before,after)
    need(sha(source[0x783C9E:0x783EAF])=='BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1','source nineteen-color normal/half-nibble projection')
    serialize=ROOT/'build/gba-shoot-entry-capture-v2-qa-20261109/source/serialize.h'
    need(sha(serialize.read_bytes())=='B7437677E104AF90838FC0D54530779CE0063B9EA6EA91130192A3F716D2EAFF','CPU serialized GPR/prefetch ABI')
    names=['04-bounded-no-completion.State','04-bounded-no-completion-iwram.bin','04-bounded-no-completion-ewram.bin','04-bounded-no-completion-palette.bin']
    evidence={name:sha((capture/name).read_bytes())for name in names}
    core,_=checkpoint_core((capture/names[0]).read_bytes());length=u(core,0);native=core[4:4+length]
    iw,ew,pal=((capture/name).read_bytes()for name in names[1:])
    need(native[0x19000:0x21000]==iw and native[0x21000:0x61000]==ew and native[0x800:0xC00]==pal,'actual genuine State/RAM fixture equality')
    actual=list(struct.unpack_from('<16I',native,0x20))
    need((actual[15],actual[14],actual[13],actual[4],actual[5],actual[6],actual[7],actual[8])==
         (0x085C6F50,0x085C6F50,0x03007E94,0x08586812,0x03003D30,0x739C,7,0x05000010),'actual self-call PC LR SP and palette live-ins')
    regs=list(struct.unpack_from('<14I',iw,0x7E94))
    need(regs[13]==0x080D1224 and u(before,0xD1220)==0xEBFFCEA7,'actual saved caller BL080C4CC4 atD1220')
    need(u(iw,0x4506,2)==0x80 and iw[0x4529]==7 and iw[0x260B]==0,'first actual blink enables projector dim path')
    snapshot={0x03000000:iw,0x02000000:ew,0x05000000:pal}
    cases=0;dim_calls=set()
    for blink,flags in [(b,0)for b in range(256)]+[(b,f)for b in(0,7)for f in range(1,16)]:
        m=fixture(after,snapshot,regs,flags);m.put(0x03004529,blink,1)
        initial=m.r[:15];sp=m.r[13]
        m.run(0x085C6F00,{regs[13]})
        need(m.r[:15]==initial,'actual full projector returns saved caller with all r0-r12/SP/LR preserved')
        want=palette_plan(after,source,iw,blink)
        observed=[(a,v)for a,v,n in m.writes if 0x05000000<=a<0x05000400]
        need(observed==want and len(observed)==35,'source-correct nineteen colors and exact35 ordered halfword stores')
        expected=bytearray(pal)
        for at,value in want:expected[at-0x05000000:at-0x05000000+2]=value.to_bytes(2,'little')
        need(bytes(m.get(0x05000000+i,1)for i in range(0x400))==expected,'entire protected palette exact')
        need(bytes(m.get(0x03003D30+i,1)for i in range(32))==iw[0x3D30:0x3D50],'compact state32 bytes not rewritten')
        need(all((sp-56<=a and a+n<=sp)or(0x05000000<=a and a+n<=0x05000400)for a,v,n in m.writes),'only saved frame and approved palette output writes')
        callsites={a-BASE for a,to,_ in m.calls if to==0x085C6FD4}
        need(callsites==(set(SITES)if blink else set()),'all four retained conditional calls taken iff nonzero control')
        dim_calls|=callsites;cases+=1
    for common,disabled in((0x10,0),(0x90,0),(0x80,1),(0x80,255)):
        m=fixture(after,snapshot,regs);m.put(0x03004506,common,2);m.put(0x0300260B,disabled,1)
        initial=m.r[:15];m.run(0x085C6F00,{regs[13]})
        need(m.r[:15]==initial and not any(0x05000000<=a<0x05000400 for a,v,n in m.writes),'retained common10/disabled gates')
    corners=0
    for color in(0x000,0x001,0x111,0x123,0x777,0x888,0xEEE,0xFFF):
        for flags in range(16):
            m=fixture(after,snapshot,regs,flags);m.r[0]=convert(color);m.r[6]=0x739C;m.r[14]=0x09000000
            old=m.r[:15];m.run(0x085C6FD4,{0x09000000});expected=old[:];expected[0]=convert((color&0xEEE)>>1)
            need(m.r[:15]==expected and not m.writes,'actual local dim helper RGB corners and register contract');corners+=1
    old=fixture(before,snapshot,regs)
    try:old.run(0x085C6F00,{regs[13]},max_steps=96)
    except ValueError:need(old.r[14]==0x085C6F50 and old.r[15]in(0x085C6F54,0x085C6F50)and len(old.calls)>1,'old real self-branch counterexample')
    else:raise ValueError('old dimmed projector unexpectedly returned')
    # The normal task scheduler has no new predicate to repair. Its linked scene
    # remains present; ordinary actor-control7 is an intended pre-callback gate.
    need(u(ew,0x121E8)==0x085CD0A0 and u(ew,0x121EC)==0xFF0 and u(ew,0x121F0)==0x02011D88 and
         u(ew,0x121F4)==0x02011FB8 and u(ew,0x121F8,2)&2,'actual active normally linked terminal owner')
    m=fixture(after,snapshot,regs);m.put(0x0300133C,0x020121E8);m.r[14]=0x09000000
    m.run(0x085CD0A0,{0x09000000})
    need(m.get(0x02012250,2)==119 and m.get(0x03004529,1)==0,'real scene decrements120→119 and blink7→0 if CPU returns to scheduler')
    rejected=[]
    for at in SITES+(0x5C6FD4,0x5C7100,0x352B10,0x5BDD00,0x6FF600,0x7FFFFF):
        bad=bytearray(after);bad[at]^=1
        try:inverse(before,bytes(bad))
        except ValueError:rejected.append(at)
        else:raise ValueError('inverse mutation accepted')
    need(all(sha((capture/name).read_bytes())==digest for name,digest in evidence.items()),'frozen capture not rewritten')
    return dict(status='INDEPENDENT_PALETTE_DIM_CALL_REPAIR_PASS',before_sha256=BEFORE,after_sha256=AFTER,source_sha256=SOURCE,
        author_sha256=AUTHOR,writes=[dict(raw=a,before='1BFFFFFE',after=f'{v:08X}',target='085C6FD4')for a,v in zip(SITES,WORDS)],
        declared_bytes=16,changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        actual_capture_hashes=evidence,actual_CPU=dict(PC=actual[15],LR=actual[14],SP=actual[13],control=7),
        saved_caller_return=regs[13],incoming_SP=0x03007ECC,full_projector_cases=cases,all256_blink_values=True,
        all_four_conditional_calls_executed=sorted(dim_calls),RGB_corner_actual_helper_cases=corners,retained_gate_cases=4,
        source_colors_each=19,palette_halfword_stores_each=35,full_palette_and_state_protection=True,
        scene_actual_counter_progress=dict(before=120,after=119,control_before=7,control_after=0),
        inverse_controls_rejected=rejected,dependencies={**DEPS,Path(__file__).name:sha(Path(__file__).read_bytes())},
        qualification='Offline real ARM fragments and exact captured call frame; no emulator/state load/repair, scheduler patch, runtime completion, original full-Core equality or historical E5 claim. Prior4096 source-color math suite not rerun.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('before','after','source','capture','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    result=audit(a.before.read_bytes(),a.after.read_bytes(),a.source.read_bytes(),a.capture)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
    print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
