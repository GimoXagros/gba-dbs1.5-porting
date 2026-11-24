"""Prove phase equivalence and bounded work of the installed cable name-editor clock."""
import argparse
import json
import random
import struct
from pathlib import Path

from verify_mode23_scene_component import empty, sha


def run(prior,rom,owner_raw):
    meta=json.loads(owner_raw)
    assert sha(prior)==meta['input_sha256'] and sha(rom)==meta['output_sha256']
    inverse=bytearray(rom)
    for row in meta['writes']:
        lo=row['offset'];hi=lo+row['size']
        assert sha(prior[lo:hi])==row['before_sha256'] and sha(rom[lo:hi])==row['after_sha256']
        inverse[lo:hi]=prior[lo:hi]
    assert inverse==prior
    add=0x08f15440
    assert prior[add-0x08000000:add-0x08000000+4]==bytes.fromhex('010080e2')
    vm=empty(rom)
    old_regs=vm.r[:15]
    count=0
    def next_tick(old,flags):
        nonlocal count
        vm.r[:15]=old_regs;vm.r[0]=old;vm.cpsr=31|flags<<28
        # An arbitrarily old clock from a previous running scene must also assign
        # a bounded amount of work independent of the magnitude of that clock.
        vm.run(add,{add+4},max_steps=20 if old<=180 else 170)
        assert vm.r[1:15]==old_regs[1:15] and vm.cpsr==31|flags<<28
        n=vm.r[0];count+=1
        assert n==(old+1 if old<180 else 151+(old-150)%30)
        assert (n>=151)==(old+1>=151) and n%30==(old+1)%30
        return n
    # Execute all native conditions through the borrow boundaries and six wrap edges.
    rng=random.Random(151)
    clocks=list(range(361))+[v+d for v in (1<<16,1<<24,1<<31) for d in (-1,0,1)]
    clocks+=list(range(0xfffffff0,0x100000000))+[rng.getrandbits(32) for _ in range(150)]
    for i,t in enumerate(clocks):next_tick(t,i%16)
    clock=0
    for tick in range(1,7201):
        clock=next_tick(clock,tick%16)
        assert clock%30==tick%30 and (clock>=151)==(tick>=151)
        if tick<151:assert tick==clock
        else:assert 151<=clock<=180
    # The installed inner per-particle loop subtracts thirty while its unsigned clock
    # remains at least thirty. Every runtime tile offset is read from the actual table.
    pattern=bytes.fromhex('1e0050e31e004022fcffff2a')
    assert rom.count(pattern)>=1
    symbol=meta['reused_symbols']['m24s_animate']-0x08000000
    unique=rom.find(pattern,symbol,symbol+1500)
    assert unique>=0 and rom.find(pattern,unique+1,symbol+1500)<0
    table=bytes(2*((i+1)//6) for i in range(30))
    assert rom.find(table,symbol,symbol+2408)>=0
    ceiling=max((180+offset)//30 for offset in table)
    assert ceiling==6
    return dict(status='CABLE_NAME_IDLE_PHASE_AND_COST_PASS',image_sha256=sha(rom),prior_sha256=sha(prior),
                full_image_inverse=True,arm_invocations=count,continuous_name_ticks=7200,clock_after_7200=clock,
                maximum_particle_subtractions=ceiling,fast_clock_instruction_limit=20,old_state_instruction_limit=170)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('prior','image','owner','report'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();r=run(a.prior.read_bytes(),a.image.read_bytes(),a.owner.read_bytes())
    r['checker_sha256']=sha(Path(__file__).read_bytes())
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(r['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
