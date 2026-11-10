#!/usr/bin/env python3
"""Independent bounded ARM owner-link QA, no production builder import."""
import argparse
import json
from pathlib import Path
from verify_shoot_stage11_runtime_probe import Machine, listing
from verify_shoot_terminal_owner_link_production import audit, need, sha

FIRST, SECOND, AUX = 0x02011710, 0x02011828, 0x02011940
RETURN = 0x09000000

def run_guard(rom, snapshot, changes=()):
    m = Machine(rom, 3, 0x10, snapshot=snapshot)
    m.r[14] = RETURN
    for address,value,size in changes:
        m.put(address,value,size)
    m.writes.clear()
    stop = m.run(0x086FF9C0, {0x086FFD34,0x086FFD3C})
    need(all(0x03007000 <= a < 0x03008000 for a,_,_ in m.writes), 'guard stack writes only')
    return stop,m

def lifetimes(rom):
    m = Machine(rom, 2, 0x10)
    m.r[4],m.r[6],m.r[7] = AUX,SECOND,FIRST
    for at,reg,owner in ((0x5BC29C,6,SECOND),(0x5BC2A8,7,FIRST),(0x5BC380,4,AUX)):
        m.run(0x08000000+at, {0x08000000+at+4})
    need((m.get(AUX+0x28),m.get(AUX+0x18),m.get(SECOND+0x28)) == (SECOND,FIRST,AUX), 'actual constructor stores')
    m.r[5]=SECOND
    m.put(0x0300231E,11,1)
    m.writes.clear()
    m.run(0x085CD960, {0x0836E604})
    need([(a,v,n) for a,v,n in m.writes] == [(SECOND,0x085BDD00,4),(AUX,0x085BF204,4)], 'fatal route changes callbacks only')
    m.r[4],m.r[14]=AUX,RETURN
    m.put(AUX+4,0,2)
    m.writes.clear()
    m.run(0x085BF204,{RETURN})
    need(m.get(AUX)==0x085BF400 and m.get(AUX+0x94,2)==59, 'actual initial auxiliary death update')
    for _ in range(59):
        m.r[14]=RETURN
        m.run(0x085BF400,{RETURN})
    need(m.get(AUX)==0x085BF600, 'actual auxiliary death reaches final callback')
    need(not any(a in (AUX+0x18,AUX+0x28,SECOND+0x28) for a,_,_ in m.writes), 'death never relinks')
    need((m.get(AUX+0x28),m.get(AUX+0x18),m.get(SECOND+0x28)) == (SECOND,FIRST,AUX), 'owner/opponent survive fatal and death')
    return dict(constructor_store_addresses=[0x5BC29C,0x5BC2A8,0x5BC380], fatal_callback_only=True, auxiliary_updates=60, no_relink=True)

def semantic(before,after,capture):
    snapshot = {base:(capture/('18-bounded-no-completion-'+name+'.bin')).read_bytes()
                for name,base in (('ewram',0x02000000),('iwram',0x03000000),('vram',0x06000000),('display',0x04000000))}
    need(listing(after,0x6FFC00,12)==['ldr r0, [r6, #0x28]','cmp r0, r5','bne #0x86ffd3c'], 'load/compare/refusal actual ARM')
    old,m=run_guard(before,snapshot)
    need(old==0x086FFD3C and m.r[0]==FIRST, 'old captured reciprocal-owner refusal')
    new,m=run_guard(after,snapshot)
    need(new==0x086FFD3C and (m.r[0],m.r[1])==(0x1F00,0x1E00), 'actual final outer IO refusal remains')
    model=((0x0400000A,0x1E03,2),)
    stop,m=run_guard(after,snapshot,model)
    need(stop==0x086FFD34, 'mixed-epoch hook IO model only reaches accept')
    rejected=[]
    for label,a,v,n in (
        ('reverse owner',AUX+0x28,FIRST,4),('forward owner',SECOND+0x28,FIRST,4),
        ('inactive auxiliary',AUX-8,0,4),('aux resource',AUX+0xF0,0,4),
        ('moving FIRST',FIRST+0x42,1,2),('BG velocity',0x03002354,1,2),
        ('extra renderer',0x0300482A,2,2),('aux nonfinal callback',AUX,0x085BF400,4)):
        stop,_=run_guard(after,snapshot,model+((a,v,n),))
        need(stop==0x086FFD3C,label+' rejected'); rejected.append(label)
    return dict(status='INDEPENDENT_TERMINAL_OWNER_LINK_ARM_PASS', lifetimes=lifetimes(after),
                native_guard_negative_controls=rejected, actual_old_owner_refusal=True,
                actual_repaired_outer_IO_refusal=True, modeled_guard_acceptance=True,
                model_limitation='Final outer RAM/VRAM plus earlier hook BG1CNT: mixed epochs, not actual acceptance',
                runtime_acceptance=False, service_models=[], capture_hashes={hex(a):sha(b) for a,b in snapshot.items()})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','source','manifest','capture','report'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args(); need(not args.report.exists(),'fresh report')
    before,after,source,manifest=(getattr(args,k).read_bytes() for k in ('before','after','source','manifest'))
    structure=audit(before,after,source,manifest)
    result=semantic(before,after,args.capture); result['structure']=structure
    result['verifier_sha256']=sha(Path(__file__).read_bytes())
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result['status'],sha(args.report.read_bytes()))

if __name__=='__main__':
    main()
