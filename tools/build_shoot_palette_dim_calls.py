#!/usr/bin/env python3
"""Repair four local BLNE relocations; preserve the frozen graphics generator."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_shoot_graphics_initializer import palette_project
from verify_shoot_graphics_initializer import CODE, dim_native
from verify_shoot_stage11_runtime_probe import Machine

ROOT = Path(__file__).resolve().parents[1]
INPUT = '1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
OUTPUT = 'FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SITES = (0x5C6F4C, 0x5C6F5C, 0x5C6F88, 0x5C6FBC)
HELPER, BASE = 0x5C6FD4, 0x08000000
DEPS = {
 'build_shoot_graphics_initializer.py':'4CDCF5DB76E7029066E051FB5343A41DE6069F57BA6D6C84A2FC7580A223CB80',
 'build_shoot_player_binding.py':'34A3BED066AD527A65BBC328F6FD3168B978D7EA5E3BA56CC35A8198CB7A1C53',
 'verify_shoot_graphics_initializer.py':'AB0B78C1CBFA82407A6A204A1EF518C02CB671D709B11B70B5B11F4E7A5D7EA2',
 'verify_shoot_stage11_runtime_probe.py':'259061E232A4B3C2462112711B48196EEFF736194C35E904EB1803E5B3B885E7',
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
}
# The exact project/helper, its stage dispatch, and the terminal blink producer.
PINS = (
 (0x5C6F00,0x5C700C,'A5BF5D31A6DD7679945E0EBAB3059B09FC2A91F16422C5C8BC3AE9B6FA47E6E3'),
 (0x5C7100,0x5C7124,'EC3FB9FA565C924CCDEA3323EB1F831085D2ADD60FDC4539BA3C4C2A1C864A40'),
 (0xC4CC4,0xC4CCC,'4100B3560C896034CE1EED3B4605C4ED70EB20D52F3B9F086C40082394AC1A5C'),
 (0x5CD0D8,0x5CD104,'179211AF41993C0C9264A68105DA6110849009DD6751316EF48801606ABC4600'),
)


def need(ok, label):
    if not ok: raise ValueError(label)


def sha(b): return hashlib.sha256(b).hexdigest().upper()
def u(b, a): return struct.unpack_from('<I', b, a)[0]


def target(w, a):
    displacement = w & 0xFFFFFF
    if displacement & 0x800000: displacement -= 0x1000000
    return a + 8 + 4 * displacement


def writes():
    # Explicit PC+8 arithmetic avoids the reproduced conditional-label defect.
    return [(a, struct.pack('<I',0x1BFFFFFE),
             struct.pack('<I',0x1B000000 | ((HELPER-a-8)//4))) for a in SITES]


def apply(before, rows):
    result = bytearray(before)
    for a, old, new in rows:
        need(len(old)==len(new)==4 and result[a:a+4]==old, 'ExpectedWrite '+hex(a))
        result[a:a+4] = new
    return bytes(result)


def validate(before, after):
    need(len(before)==len(after)==0x800000, 'unchanged complete ROM extent')
    need(apply(after, [(a,new,old) for a,old,new in writes()])==before, 'whole-ROM inverse')
    for a in SITES:
        need(u(after,a)>>24==0x1B and target(u(after,a),a)==HELPER, 'BLNE helper binding')


def build(before, source):
    need(sha(before)==INPUT and sha(source)==SOURCE, 'exact predecessor and source')
    for name, digest in DEPS.items():
        need(sha((ROOT/'tools'/name).read_bytes())==digest, 'dependency '+name)
    for a,z,digest in PINS:
        need(sha(before[a:z])==digest, 'native owner '+hex(a))
    need(sha(source[0x783C9E:0x783EAF])=='BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1', 'source normal/dim projection')
    old, code_size = palette_project()
    need(old==before[0x5C6F00:0x5C700C] and code_size==248, 'reproduce historical generator exactly')
    # Bound the sibling inquiry to the ten published graphics function bodies.
    self_calls=[]; projector_calls=[]
    for name,a,n,_,_ in CODE:
        for at in range(a,a+n,4):
            w=u(before,at)
            if w & 0x0F000000 == 0x0B000000:
                if target(w,at)==at: self_calls.append(at)
                if name=='palette_project': projector_calls.append(at)
    need(tuple(self_calls)==SITES and tuple(projector_calls)==SITES, 'complete affected BL and sibling self-call population')
    result=apply(before,writes()); validate(before,result)
    need(sha(result)==OUTPUT, 'frozen repaired output')
    return result, dict(input_sha256=INPUT,output_sha256=OUTPUT,source_sha256=SOURCE,
        expected_writes=[dict(offset=a,before=old.hex(),after=new.hex())for a,old,new in writes()],
        whole_ROM_inverse=True,declared_bytes=16,changed_bytes=sum(a!=b for a,b in zip(before,result)),
        new_storage=False,new_RAM_owner=False,source_range=[0x783C9E,0x783EAF],
        helper=BASE+HELPER,affected_BL_population=list(SITES),sibling_functions=len(CODE),
        dependency_hashes=DEPS,native_pins=PINS,
        limits='Local call repair only. No actual repaired terminal runtime or subsequent IRQ acceptance claimed.')


def fixture(rom, flags, blink, common=0, disabled=0, snapshot=None):
    m=Machine(rom,3,(flags<<28)|0x10,snapshot=snapshot)
    m.r[14]=0x09000000
    m.put(0x0300231E,11,1);m.put(0x03004506,common,2)
    m.put(0x0300260B,disabled,1);m.put(0x03004529,blink,1)
    if not snapshot:
        for i in range(32):m.put(0x03003D30+i,(i*3+5)&255,1)
        for at,pointer in ((8,0x08586810),(12,0x08586844),(16,0x0858688A)):
            m.put(0x03003D30+at,pointer)
        for i in range(0x400):m.put(0x05000000+i,(i*7+3)&255,1)
    return m


def execute(rom, flags, blink, common=0, disabled=0, snapshot=None):
    m=fixture(rom,flags,blink,common,disabled,snapshot)
    registers=m.r[:15]; state=bytes(m.get(0x03003D30+i,1)for i in range(32))
    palette=bytearray(m.get(0x05000000+i,1)for i in range(0x400))
    expected=palette[:]; stores=[]
    if not(common&16 or disabled):
        groups=((8,6),(12,8),(16,5))
        for slot,count in groups:
            pointer=m.get(0x03003D30+slot)
            for j in range(count):
                color=m.get(pointer+2*j,2)
                if blink:color=dim_native(color)
                offsets=([0x10+(j//2)*0x20+(j%2)*2] if slot==8 else
                         [0x64+2*j+k*0x20 for k in range(3)] if slot==12 else [0xC4+2*j])
                for offset in offsets:
                    expected[offset:offset+2]=struct.pack('<H',color)
                    stores.append((0x05000000+offset,color,2))
    m.writes.clear();m.calls.clear()
    m.run(0x085C7100,{0x09000000})
    need(m.r[:15]==registers,'full caller registers and SP/LR restored')
    need(bytes(m.get(0x03003D30+i,1)for i in range(32))==state,'32-byte palette state unchanged')
    need(bytes(m.get(0x05000000+i,1)for i in range(0x400))==expected,'exact colors and protected palette cells')
    palette_writes=[w for w in m.writes if 0x05000000<=w[0]<0x05000400]
    need(palette_writes==stores,'ordered source-equivalent 35 stores')
    need(len(m.calls)==(19 if stores and blink else 0),'all four static calls, 19 selected colors')
    need(all(t==BASE+HELPER for _,t,_ in m.calls),'all calls enter local dim helper')
    need(all(0x03007000<=a<0x03008000 or 0x05000000<=a<0x05000400 for a,_,_ in m.writes),'only stack and palette writes')
    return m


def checks(before,after,capture):
    cases=0
    for flags in range(16):
        for blink in (0,1,7):
            execute(after,flags,blink);cases+=1
        for common,disabled in ((16,0),(0,1)):
            execute(after,flags,7,common,disabled);cases+=1
    # Retained non-Shoot dispatch stops at the exact original displaced prologue join.
    for stage in range(11):
        m=fixture(after,0,7);m.put(0x0300231E,stage,1)
        m.run(0x085C7100,{0x080C4CC8});need(not m.calls,'non11 retained join')
    snapshot={}
    for domain,base in (('iwram',0x03000000),('ewram',0x02000000),('palette',0x05000000)):
        snapshot[base]=(capture/('04-bounded-no-completion-'+domain+'.bin')).read_bytes()
    captured=execute(after,2,7,snapshot=snapshot)
    original=fixture(before,2,7,snapshot=snapshot)
    original.run(0x085C7100,{0x085C6F4C})
    need(original.r[0]==0x1B and original.r[7]==7 and original.r[6]==0x739C and
         original.r[4]==0x08586812 and original.r[5]==0x03003D30 and original.r[8]==0x05000010 and original.r[2]==3,
         'actual captured first dim-call register tuple')
    try:original.run(0x085C6F4C,{0x085C6F50},max_steps=8)
    except ValueError as e:need(str(e)=='bounded actual ARM execution did not return','exact original loop refusal')
    else:raise ValueError('old self call unexpectedly returned')
    need(original.r[14]==0x085C6F50,'actual captured LR witness')
    controls=0
    for at,_,_ in writes():
        bad=bytearray(after);bad[at]^=1
        try:validate(before,bytes(bad))
        except ValueError:controls+=1
        else:raise ValueError('mutation accepted')
    return dict(status='PASS',actual_ARM_projector_cases=cases,captured_RAM_case=True,
        non11_retained_joins=11,source_colors=19,palette_stores=35,mutation_controls=controls,
        old_self_loop_reproduced=True,service_models=[],BIOS_executed=False,
        capture_sha256={hex(a):sha(b)for a,b in snapshot.items()},
        qualification='Actual ROM instructions in the existing strict ARM interpreter; no emulator replay. Prior complete 4096-color source proof reused.')


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--capture-dir',type=Path)
    p.add_argument('--author-report',type=Path);a=p.parse_args()
    before=a.input.read_bytes();after,manifest=build(before,a.source.read_bytes())
    if a.author_report:
        need(a.capture_dir is not None,'author checks require explicit completed capture')
        report=checks(before,after,a.capture_dir)
        a.author_report.parent.mkdir(parents=True,exist_ok=True);a.author_report.write_text(json.dumps(report,indent=2)+'\n')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(manifest,indent=2)+'\n')
    print(OUTPUT)


if __name__=='__main__':main()
