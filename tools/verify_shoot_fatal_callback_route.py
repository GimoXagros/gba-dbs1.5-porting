#!/usr/bin/env python3
"""Independent actual-ARM verification of the single fatal-route branch.

No production imports, emulator, saves, or old callee verification reruns.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from verify_shoot_static_companion_clear import Machine

BASE=0x08000000
BEFORE='18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1'
RETAIL='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ADAPTER_SHA='49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246'
MACHINE_SHA='CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943'
SITE,ADAPTER,JOIN,STOP=0x36E5EC,0x5CD960,0x36E604,0x0836E438
UPPER,AUX,PARENT,ATTACKER=0x02010248,0x02010478,0x020106A8,0x02010018
TARGETS=(0x0836F558,)*3+(0x0836F648,0x0836F64C,0x0836F6C4,0x0836F6C8,
    0x0836F72C,0x0836F730,0x0836F734,0x0836F738,0x0836F74C,0x0836F7A0,0x0836E484)


def need(ok,label):
    if not ok:raise ValueError(label)


def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,p):return struct.unpack_from('<I',b,p)[0]


def target(at,w):
    delta=w&0xFFFFFF
    if delta&0x800000:delta-=0x1000000
    return BASE+at+8+4*delta


def exact_change(before,after):
    need(len(after)==len(before)==0x800000,'unchanged complete ROM extent')
    word=u(after,SITE)
    need(word>>24==0xEA and target(SITE,word)==BASE+ADAPTER,'sole unconditional non-link branch to resident adapter')
    need(u(before,SITE)==0xE1A00005,'actual displaced MOV r0,r5')
    restored=bytearray(after);restored[SITE:SITE+4]=before[SITE:SITE+4]
    need(restored==before,'entire four-byte inverse')
    need(sha(after[ADAPTER:ADAPTER+64])==ADAPTER_SHA,'frozen resident adapter reused exactly')


def fixture(data,stage,nzcv):
    m=Machine(data,stage,flags=(nzcv<<28)|0x10)
    m.r[4],m.r[5]=ATTACKER,UPPER
    for address,value,size in ((UPPER+0x28,AUX,4),(UPPER+0x20,PARENT,4),
        (UPPER,0x085BE000,4),(AUX,0x085BE100,4),(UPPER+0x76,0xA55A,2),
        (AUX+0x76,0x5AA5,2),(PARENT+0x94,0xFFFF,2),(0x03004D40,0x9234,2),
        (0x0300231E,stage,1),(ATTACKER+8,0,2),(UPPER+0x64,1,2),
        (0x03004D24,1,1)):
        m.put(address,value,size)
    return m


def joins(before,after):
    count=0
    for stage in range(256):
        for flags in range(16):
            old,new=fixture(before,stage,flags),fixture(after,stage,flags)
            old.run(BASE+SITE,{STOP});new.run(BASE+SITE,{STOP})
            need(old.r[:15]==new.r[:15],'complete common-tail register parity')
            expected=list(old.writes)
            if stage==11:
                expected=[(a,0x085BDD00 if a==UPPER and n==4 else
                    0x085BF204 if a==AUX and n==4 else value,n) for a,value,n in expected]
            need(new.writes==expected,'ordered callback/reset writes and exact non11 behavior')
            need(new.r[0]==new.r[5]==UPPER and new.get(AUX+0x76,2)==0 and
                new.get(UPPER+0x76,2)==0 and new.get(PARENT+0x94,2)==1 and
                new.get(0x03004D40,2)==0,'displaced MOV and retained complete tail')
            count+=1
    # Only the native HP decision prefix newly joined to this selector.
    hp_count=0
    for stage in (7,11):
        for hp,damage,evolve in ((1,1,0),(1,255,0),(2,1,0),(1,1,0x4000),(1,2,0x4000)):
            old,new=fixture(before,stage,15),fixture(after,stage,15)
            for m in (old,new):
                m.put(UPPER+0x64,hp,2);m.put(0x03004D24,damage,1);m.put(ATTACKER+8,evolve,2)
            a=old.run(0x0836E5C8,{STOP,0x0836E634})
            b=new.run(0x0836E5C8,{STOP,0x0836E634})
            need(a==b and old.r[:15]==new.r[:15],'HP decision/registers unchanged')
            need(new.get(UPPER+0x64,2)==(hp-(damage>>bool(evolve)))&65535,'real zeroextended/halved damage')
            if a==0x0836E634:need(old.writes==new.writes and old.cpsr==new.cpsr,'nonfatal branch unchanged')
            hp_count+=1
    return dict(all_stage_all_NZCV_cases=count,actual_HP_prefix_cases=hp_count,service_models=0,
                new_callbacks_only_at_stage11=True,common_tail_registers_and_resets_exact=True)


def flags_lifetime(data):
    """Independent restricted CFG: EQ/NE may use freshly defined Z only.

    TST/ORRS are not treated as full NZCV kills. Stop at CMP/SUBS; follow
    direct returns to the real caller's SUBS and the one typed freeze prefix.
    """
    decoder=Cs(CS_ARCH_ARM,CS_MODE_ARM)
    need(struct.unpack_from('<14I',data,0x36E44C)==TARGETS,'actual attacker table')
    todo=[(BASE+JOIN,False)];seen=set();kills=set();returns=0
    safe={'ldr','ldrb','ldrh','ldrsh','str','strh','strb','mov','add','and','orr','push','pop','stmdb','ldm'}
    while todo:
        address,z_defined=todo.pop()
        if (address,z_defined) in seen:continue
        seen.add((address,z_defined));need(len(seen)<150,'bounded new flag-lifetime join')
        at=address-BASE;w=u(data,at)
        ins=next(decoder.disasm(data[at:at+4],address),None)
        need(ins is not None,'actual instruction decode')
        need('rrx' not in ins.op_str,'no hidden incoming carry in operand shift')
        cond=w>>28
        need(cond==14 or cond in (0,1) and z_defined,'incoming NZCV conditional consumer')
        if ins.mnemonic in ('cmp','subs'):
            kills.add(address);continue
        if ins.mnemonic in ('tst','orrs'):z_defined=True
        elif address==0x0836E448:
            need(w==0xE12FFF19,'only typed attacker dispatch')
            todo.extend((t,z_defined) for t in TARGETS);continue
        elif ins.mnemonic=='bx':
            need(address==0x0836E488 and ins.op_str=='lr','only shared collision return')
            todo.append((0x08353FF0,z_defined));returns+=1;continue
        elif ins.mnemonic in ('b','beq','bne','bl'):
            dest=target(at,w)
            if ins.mnemonic=='bl':need(address==0x0836F6FC and dest==0x0836A69C,'only freeze prefix before flag death')
            todo.append((dest,z_defined))
            if cond!=14:todo.append((address+4,z_defined))
            continue
        else:need(ins.mnemonic in safe,'no hidden carry arithmetic/CPSR use '+ins.mnemonic)
        todo.append((address+4,z_defined))
    need({0x08353FF4,0x0836A6A8}<=kills and returns>0,'real caller and freeze-prefix full NZCV kills')
    return dict(states=len(seen),full_NZCV_kill_sites=sorted(kills),
        logical_tests_only_define_Z=True,caller_return=0x08353FF0,intermediate_CPSR_equality_claim=False)


def source_binding(source,retail,before):
    need(source[0x760197:0x76019F]==bytes.fromhex('26803E5C000B744D'),'source stage11 first fatal-selection branch')
    for raw,value in ((0x7601EE,0x7AB1),(0x7601FA,0x7D8D)):
        need(source[raw:raw+9]==b'\xC7\x05'+struct.pack('<H',value)+bytes.fromhex('C745029040'),'exact source fatal target pair')
    need(struct.unpack_from('<3I',before,ADAPTER+52)==(0x03002310,0x085BDD00,0x085BF204),'retained positive native mapping')
    for a,z in ((0x36E5C8,0x36E69C),(0x353FEC,0x353FFC),(0x36F558,0x36F7A4),(0x36A69C,0x36A6AC)):
        need(before[a:z]==retail[a:z],'retained real native arithmetic/tail/flag consumer')
    need(u(before,0x353FEC)>>24==0xEB and target(0x353FEC,u(before,0x353FEC))==0x0836E348,'actual collision caller')


def verify(after,before,retail,source,manifest):
    need((sha(before),sha(retail),sha(source))==(BEFORE,RETAIL,SOURCE),'immutable inputs')
    need(sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes())==MACHINE_SHA,'frozen machine')
    exact_change(before,after);source_binding(source,retail,before)
    effects=joins(before,after);flags=flags_lifetime(after)
    need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==sha(after),'component identities')
    need(len(manifest['writes'])==1 and manifest['writes'][0]['raw']==SITE and
         manifest['writes'][0]['bytes']==4,'exact single manifest write')
    need(all(manifest[k] is False for k in ('new_reservation','new_RAM_or_task','external_scene_entry_opened','E5_cause_or_repair_claim')),'scope limits retained')
    negatives=[]
    def rejects(label,fn):
        try:fn()
        except (ValueError,AssertionError):negatives.append(label)
        else:raise ValueError('accepted negative '+label)
    for label,at,word in (('linked instead of tail branch',SITE,u(after,SITE)|0x01000000),
        ('wrong adapter target',SITE,u(after,SITE)+1),('outside single write',SITE+4,u(after,SITE+4)^1),
        ('resident target changed',ADAPTER+56,0x085BDD04)):
        bad=bytearray(after);struct.pack_into('<I',bad,at,word)
        rejects(label,lambda b=bad:exact_change(before,b))
    bad=bytearray(after);struct.pack_into('<I',bad,ADAPTER+56,0x085BDD04)
    rejects('actual wrong selected callback',lambda:joins(before,bad))
    for label,at,word in (('conditional tail consumer',JOIN,0x03A09000),
        ('caller flags not overwritten',0x353FF4,0xE2422001),
        ('freeze flags not overwritten',0x36A6A8,0xE1A09009)):
        bad=bytearray(after);struct.pack_into('<I',bad,at,word)
        rejects(label,lambda b=bad:flags_lifetime(b))
    return dict(schema=1,status='FATAL_CALLBACK_ROUTE_INDEPENDENT_QA_PASS',before_sha256=BEFORE,
        after_sha256=sha(after),source_sha256=SOURCE,retail_sha256=RETAIL,
        resident_adapter_sha256=ADAPTER_SHA,verifier_sha256=sha(Path(__file__).read_bytes()),
        exact_four_byte_inverse=True,new_declared_bytes=4,
        new_changed_bytes=sum(a!=b for a,b in zip(before,after)),
        actual_ARM=effects,flags_lifetime=flags,negative_controls_rejected=negatives,
        external_scene_entry_opened=False,E5_cause_or_repair_claim=False,
        whole_Shoot_completion=False,old_callee_suites_rerun=False,
        dependencies={'verify_shoot_static_companion_clear.py':MACHINE_SHA})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('candidate','predecessor','retail','source'):p.add_argument(n,type=Path)
    p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();need(not a.output.exists(),'fresh report output')
    result=verify(a.candidate.read_bytes(),a.predecessor.read_bytes(),a.retail.read_bytes(),
                  a.source.read_bytes(),json.loads(a.manifest.read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
    print(json.dumps({'status':result['status'],'report_sha256':sha(a.output.read_bytes())}))


if __name__=='__main__':main()
