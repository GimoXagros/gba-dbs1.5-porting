#!/usr/bin/env python3
"""Connect the existing stage11 fatal adapter with one ARM branch word."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

import analyze_shoot_fatal_callback_contract as contract
from verify_shoot_static_companion_clear import Machine

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
INPUT='18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1'
HOOK, ADAPTER, TAIL = contract.HOOK,contract.ADAPTER,contract.TAIL
SIMULATOR='CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943'


def need(ok,label):
    if not ok:raise ValueError(label)


def sha(data):return hashlib.sha256(data).hexdigest().upper()


def branch():
    delta=ADAPTER-HOOK-8
    need(delta%4==0 and -(1<<25)<=delta<(1<<25),'ARM branch range')
    return struct.pack('<I',0xEA000000|((delta>>2)&0xFFFFFF))


def fixture(data,stage,seed=0,flags=0x10,hp=1,damage=1,evolved=False):
    m=Machine(data,seed,flags=flags)
    attacker,victim,aux,parent=0x02010018,0x02010248,0x02010478,0x020106A8
    m.r[4],m.r[5]=attacker,victim
    for address,value,size in ((attacker+8,0x4000 if evolved else 0,2),
        (victim+0x64,hp&0xFFFF,2),(victim+0x28,aux,4),(victim+0x20,parent,4),
        (victim,0x08045678,4),(aux,0x08056788,4),
        (victim+0x76,0x1234,2),(aux+0x76,0x5678,2),(parent+0x94,0x3456,2),
        (0x03004D40,0x789A,2),(0x03004D24,damage,1),
        (0x0300231E,stage,1),(0x0300231F,(seed*53)&255,1),
        (0x0300232A,(seed*0x1357)&0xFFFF,2)):
        m.put(address,value,size)
    return m,attacker,victim,aux,parent


def author_selfcheck(before,after):
    joins=0
    for stage in range(256):
        for seed,flags in ((0,0x10),(1,0xA0000010),(2,0x50000010)):
            old,*_=fixture(before,stage,seed,flags)
            new,attacker,victim,aux,parent=fixture(after,stage,seed,flags)
            old.run(BASE+HOOK,{BASE+TAIL});new.run(BASE+HOOK,{BASE+TAIL})
            expected=list(old.r[:15])
            if stage==11:expected[8]=0x085BF204
            need(new.r[:15]==expected,'actual displaced-operation register join')
            wanted=[(victim,0x085BDD00,4),(aux,0x085BF204,4)] if stage==11 else old.writes
            need(new.writes==wanted,'only exact callback pair differs at adapter join')
            need(new.r[0]==victim and new.r[5]==aux,'real lethal live-ins/displaced MOV')
            joins+=1
    hp_cases=0
    for stage in (0,7,11,255):
        for hp in (-1,0,1,2,8):
            for damage in (0,1,2,255):
                for evolved in (False,True):
                    old,*_=fixture(before,stage,1,hp=hp,damage=damage,evolved=evolved)
                    new,_,victim,aux,_=fixture(after,stage,1,hp=hp,damage=damage,evolved=evolved)
                    stops={0x0836E438,0x0836E634}
                    a=old.run(0x0836E5C8,stops);b=new.run(0x0836E5C8,stops)
                    need(a==b and old.r[:15]==new.r[:15],'HP arithmetic and complete common-tail registers')
                    expected=list(old.writes)
                    if stage==11 and a==0x0836E438:
                        expected=[(p,0x085BDD00 if p==victim and n==4 else
                                   0x085BF204 if p==aux and n==4 else v,n)
                                  for p,v,n in expected]
                    need(new.writes==expected,'HP/common-tail write order unchanged except selected callbacks')
                    hp_cases+=1
    return dict(actual_adapter_join_cases=joins,actual_HP_and_common_tail_cases=hp_cases,
                full_register_join=True,source_flags_scope='Incoming differences dead under separate per-flag native-consumer proof',
                no_imported_service_models=True)


def build(before,gba,source):
    need(sha(before)==INPUT,'exact accepted IRQ predecessor')
    need(sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes())==SIMULATOR,
         'frozen actual ARM interpreter')
    source_contract=contract.proof(before,gba,source)
    expected=branch();after=bytearray(before);after[HOOK:HOOK+4]=expected
    def validate(candidate):
        need(len(candidate)==len(before),'unchanged ROM size')
        need(candidate[HOOK:HOOK+4]==expected,'exact sole branch word')
        inverse=bytearray(candidate);inverse[HOOK:HOOK+4]=before[HOOK:HOOK+4]
        need(inverse==before,'whole-ROM inverse; every resident and external entry retained')
    validate(after)
    semantics=author_selfcheck(before,after)
    negatives=[]
    for label,at in (('branch corruption',HOOK),('resident adapter changed',ADAPTER),
                     ('HP math changed',0x36E5E0),('common tail changed',TAIL),
                     ('external scene hook changed',0x33FD04)):
        bad=bytearray(after);bad[at]^=1
        try:validate(bad)
        except ValueError:negatives.append(label)
        else:raise ValueError('ineffective inverse mutation '+label)
    for label,at,word in (('flags used before common-tail kill',TAIL,0x03A09000),
                          ('caller does not overwrite flags',0x353FF4,0xE2422001),
                          ('freeze prefix does not kill flags',0x36A6A8,0xE1A09009)):
        bad=bytearray(before);struct.pack_into('<I',bad,at,word)
        try:contract.flags_dead(bad)
        except ValueError:negatives.append(label)
        else:raise ValueError('ineffective flag lifetime mutation '+label)
    return bytes(after),dict(schema=1,status='EXISTING_STAGE11_FATAL_CALLBACK_ROUTE_PASS',
        input_sha256=INPUT,retail_sha256=contract.GBA,source_sha256=contract.SOURCE,
        output_sha256=sha(after),source_contract=source_contract,semantics=semantics,
        writes=[dict(name='connect_existing_fatal_adapter',raw=HOOK,bytes=4,
                     before=before[HOOK:HOOK+4].hex().upper(),after=expected.hex().upper())],
        changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_ROM_inverse=True,
        new_code_bytes=0,new_reservation=False,new_RAM_or_task=False,
        existing_adapter_unchanged=True,non11_retail_behavior_retained=True,
        non11_source_difficulty_table_newly_implemented=False,
        external_scene_entry_opened=False,E5_cause_or_repair_claim=False,
        negative_controls_rejected=negatives,
        dependencies={n:sha((ROOT/'tools'/n).read_bytes()) for n in
                      ('build_shoot_fatal_callback_route.py','analyze_shoot_fatal_callback_contract.py',
                       'verify_shoot_static_companion_clear.py')})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','gba','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    paths=(a.input,a.gba,a.source,a.output,a.manifest)
    need(len({x.resolve()for x in paths})==len(paths),'distinct input/output paths')
    need(not a.output.exists()and not a.manifest.exists(),'fresh outputs required')
    result,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'))
    print('[shoot-fatal-callback-route] '+report['output_sha256'])


if __name__=='__main__':main()
