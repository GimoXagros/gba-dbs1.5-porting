"""Independent byte ownership and linked native consumer gate for child contact.

No production-builder import, emulator, checkpoint dependency, or ROM mutation.
Native event/update/audio code executes; effect creation and retirement are
explicit ABI summaries whose unchanged code/resource lineage is checked.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import struct
import types
import textwrap

import verify_shoot_static_companion_clear as arm
import verify_shoot_caller_resident as scan

BEFORE = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
AFTER = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST, END, LIMIT, HOOK = 0xD8C800, 0xD8CA68, 0xD8CE00, 0x36F77C
PAYLOAD = '789CF70A0047AFF843313FB266891DAFDE1D79F894F549A9AC29A7DCF5D5E795'
BASE = 0x08000000
CHILD, PARENT, TARGET, OWNER = 0x020112B0, 0x02011940, 0x02011710, 0x02011828
PRESENT = CHILD + 0xAC
ENTRY = (BASE+FIRST, BASE+FIRST+0x64, BASE+FIRST+0x110, BASE+FIRST+0x180)

# Keep the frozen interpreter unchanged. This native consumer additionally
# executes ordinary non-S MUL at 08012B34, which the earlier checker did not
# need. Insert only that ISA case before the halfword-transfer classifier.
class Machine(arm.Machine):
    pass

_run = textwrap.dedent(inspect.getsource(arm.Machine.run))
_anchor = 'elif w & 0x0E000090 == 0x00000090:'
assert _run.count(_anchor) == 1
_run = _run.replace(_anchor, '''elif w & 0x0FC000F0 == 0x00000090:
            need(not w & 0x00300000, 'reviewed MUL without accumulate or flags')
            self.r[(w >> 16) & 15] = (self.r[w & 15] * self.r[(w >> 8) & 15]) & 0xFFFFFFFF
        ''' + _anchor)
_namespace = dict(arm.__dict__)
exec(compile(_run, __file__ + ':MUL-extension', 'exec'), _namespace)
Machine.run = _namespace['run']

def need(ok, label):
    if not ok:
        raise ValueError(label)

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

def u(b, p):
    return struct.unpack_from('<I', b, p)[0]

def ownership(before, after):
    need(len(before) == len(after) == 0x1000000, 'ROM extent')
    need(before[FIRST:LIMIT] == b'\xff'*(LIMIT-FIRST), 'whole reserved interval vacant')
    need(after[END:LIMIT] == before[END:LIMIT], 'unused reservation remains FF')
    need(sha(after[FIRST:END]) == PAYLOAD, 'independently reviewed exact executable image')
    need(before[HOOK:HOOK+4] == bytes.fromhex('08819fe5'), 'original callback producer')
    need(after[HOOK:HOOK+4] == bytes.fromhex('1f7428ea'), 'branch targets reviewed router')
    inverse = bytearray(after)
    inverse[HOOK:HOOK+4] = before[HOOK:HOOK+4]
    inverse[FIRST:END] = before[FIRST:END]
    need(inverse == before, 'entire image inverse; no other instructions/data/owners changed')
    need(struct.unpack_from('<4I', after, END-16) == ENTRY, 'all four public entries')
    return sum(a != b for a,b in zip(before,after))

def source_contract(source, before, after):
    need(sha(source) == SOURCE, 'immutable source')
    need(sha(source[0x760E4B:0x760E95]) ==
         'BC0EB46ABB9510987E1543E7F4472337ACCE2D706202F0581FCF910599E30582', 'source typed route')
    need(sha(source[0x749F6A:0x74A098]) ==
         'B4C4442E444473974F3B77F0366C1B88F73D40F80F4EEED54077897FF60389E4', 'all callback and follow bodies')
    need(source[0x760E5C:0x760E60] == bytes.fromhex('3c0b7419'), 'source stage11 branch')
    need(source[0x760E79:0x760E80] == bytes.fromhex('c7046a96c74402'), 'source callback966A assignment')
    # Source P1 is precisely three commands. The new path uses events1 and2;
    # it does not enlarge the P0/P1 population or suppress the native consumer.
    need((struct.unpack_from('<H',source,0x3D1E36)[0]-12)//8+1 == 3, 'source child three events')
    need(after[0x5B9000:0x5B9400] == before[0x5B9000:0x5B9400], 'child resources retained')
    for at,size in ((0x12874,0x150),(0x12A84,0x130),(0xD15C0,0x30),
                    (0x3524C4,0xA0),(0x35972C,0x49C),(0x6FEA00,0x180),
                    (0x627D00,0x100)):
        need(after[at:at+size] == before[at:at+size], 'native import retained '+hex(at))
    need(sha(after[0x35972C:0x3598FC]) ==
         '90BB8FA03BA903135924DA0419BEAA90FF5EE987DE870E63996E365F2892EEF1', 'effect constructor lineage')
    need(sha(after[0x3598FC:0x359BC8]) ==
         'CA2EDEBE37A1F30314683B0F4CBA7BB23846976B20C8B04860F4E4702E968F8D', 'effect callback lifetime')
    need(u(after,0x36E694) == 0x03004D40, 'existing damage scroll consumer owner')
    need(after[0x36E624:0x36E630] == bytes.fromhex('68809fe50090a0e3b090c8e1'),
         'positive damage callback load/zero/store to scroll owner')
    need(u(after,0xD15EC) == 0x030022F0, 'native audio request owner')
    imports = {0xD8C8A8:0x0835972C, 0xD8C8C8:0x080D15C0,
               0xD8C9A4:0x083524C4, 0xD8CA20:0x08012874, 0xD8CA48:0x08012A84}
    for at,target in imports.items():
        word=u(after,at)
        need(word>>24 == 0xEB and BASE+at+8+scan.signed(word&0xFFFFFF,24)*4 == target,
             'actual external BL target '+hex(at))

def setup(rom, stage=11, flags=0):
    m = Machine(rom, seed=9, flags=(flags<<28)|0x1F)
    for base,size in ((CHILD,0x100),(PARENT,0x100),(TARGET,0x100),(OWNER,0x100),
                      (0x030022F0,0x20),(0x0300450A,2),(0x03004D40,2)):
        for i in range(size): m.put(base+i,0,1)
    m.r[4],m.r[5],m.r[11] = CHILD,PRESENT,0
    m.put(CHILD+4,0xC10B,2)
    m.put(CHILD+0x14,PARENT)
    m.put(CHILD+0x18,TARGET)
    m.put(PARENT+0x20,OWNER)
    m.put(PARENT+0x76,0x1234,2)
    m.put(OWNER+0x76,0x5678,2)
    m.put(0x0300231E,stage,1)
    m.put(PRESENT+8,0x200A,2)
    m.put(PRESENT+0x30,0xFFFF,2)
    m.put(PRESENT+0x44,0x085B9000)
    m.put(TARGET+0x34,0x710,2)
    m.put(TARGET+0x36,0x520,2)
    return m

def routes(before,after):
    count = 0
    for stage in (0,1,7,9,10,11,12,20,23,255):
        for flags in range(16):
            m = setup(after,stage,flags)
            sp = m.r[13]
            # The original collision function has a live six-word return frame.
            saved = [0xABC00000+i for i in range(5)] + [0x08001234]
            for i,v in enumerate(saved): m.put(sp+i*4,v)
            m.run(BASE+HOOK,{saved[-1]})
            need(m.r[13] == sp+24 and m.r[1:6] == saved[:5], 'actual outer pop/return and live frame')
            if stage == 11:
                need(m.get(CHILD) == ENTRY[1] and m.get(CHILD+4,2) == 0xB, 'source callback and flags')
                need(m.get(OWNER+0x76,2) == 0x465 and m.get(PARENT+0x76,2) == 0x1234, 'typed nested cooldown')
            else:
                old = setup(before,stage,flags)
                for i,v in enumerate(saved): old.put(sp+i*4,v)
                old.run(BASE+HOOK,{saved[-1]})
                need(old.r[:15] == m.r[:15] and old.cpsr == m.cpsr, 'retail register/flag parity')
                # Added stack stores are dead below incomingSP; every live byte
                # including the caller return frame must still agree.
                need({a:v for a,v in old.mem.items() if not sp-20 <= a < sp} ==
                     {a:v for a,v in m.mem.items() if not sp-20 <= a < sp}, 'retail live RAM parity')
            need(all(sp-20 <= a < sp or CHILD <= a < CHILD+6 or
                     a in (OWNER+0x76,PARENT+0x76) for a,v,n in m.writes), 'route write ownership')
            count += 1
    return count

def linked(rom):
    results=[]
    for busy in (0,1):
        m=setup(rom)
        m.put(0x030022F6,busy,2)
        m.put(0x030022F2,0x7777,2)
        m.put(0x0300450A,0x40,2)
        sp,regs=m.r[13],m.r[:15]
        effects=[];retired=[]
        def effect(x):
            args=[x.get(x.r[13]+4*i) for i in range(5)]
            need(args == [3,0,0,0,TARGET] and x.r[5] == TARGET and x.r[11] == 0, 'real constructor ABI')
            effects.append(args)
            # Commercial constructor restores r0/r1/r3/r4/r5; other scratch
            # registers are deliberately poisoned to prove caller ownership.
            for reg in (2,6,7,8,9,10,11,12): x.r[reg]=0xBAD00000+reg
        def retire(x):
            need([x.get(x.r[13]+4*i) for i in range(2)] == [0,CHILD], 'native deferred-retirement ABI')
            retired.append(CHILD)
        m.services={0x0835972C:effect,0x083524C4:retire}
        m.run(ENTRY[1],{regs[14]})
        need(m.r[:15] == regs and m.r[13] == sp, 'first callback all registers and stack returned')
        need(m.get(CHILD) == ENTRY[2] and m.get(PRESENT+0xE,2) == 1, 'actual native event1')
        need(m.get(0x030022F2,2) == (0x4A if busy==0 else 0x7777), 'actual native sound gate')
        need(m.get(0x03004D40,2) == 0xFFFF and m.get(0x0300450A,2) == 0x50, 'owned source globals')
        need(effects == [[3,0,0,0,TARGET]], 'one visual effect allocation request')
        m.put(TARGET+8,m.get(TARGET+8,2)|0x4000,2)
        m.run(ENTRY[2],{regs[14]})
        need(m.get(CHILD) == ENTRY[3] and m.get(PRESENT+0xE,2) == 2, 'native event2 after target hit')
        frames=0; layouts=set()
        while not retired and frames < 256:
            m.run(ENTRY[3],{regs[14]})
            need(m.r[:15] == regs and m.r[13] == sp, 'linked callback preserves ABI')
            layout=m.get(PRESENT+0x18,2)
            need(layout < 15, 'actual native event2 layout remains within15')
            layouts.add(layout); frames+=1
        need(retired == [CHILD] and not m.get(0x0300450A,2)&0x50, 'real native completion to deferred release and flags')
        results.append(dict(sound_busy=busy,event2_calls=frames,layouts=sorted(layouts),effect_ABI=effects[0]))
    return results

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','source','report'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); before=a.before.read_bytes(); after=a.after.read_bytes(); source=a.source.read_bytes()
    need(sha(before)==BEFORE and sha(after)==AFTER,'frozen complete images')
    changed=ownership(before,after); source_contract(source,before,after)
    scanner=types.FunctionType(scan.inbound.__code__,dict(scan.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scan.inbound.__defaults__)
    need(not scanner(before),'strict all-encoding inbound census without exemptions')
    count=routes(before,after); consumers=linked(after)
    rejected=[]
    for at,label in ((HOOK,'hook'),(FIRST+0x2C,'callback assignment'),(FIRST+0x48,'cooldown'),
                     (FIRST+0xA8,'effect import'),(FIRST+0x220,'event import'),(0x5B9000,'resource outside layer')):
        bad=bytearray(after);bad[at]^=1
        try: ownership(before,bad)
        except ValueError: rejected.append(label)
        else: raise ValueError('mutation accepted '+label)
    result=dict(status='PASS',before_sha256=BEFORE,after_sha256=AFTER,source_sha256=SOURCE,
                reservations=[[FIRST,LIMIT]],declared_bytes=620,changed_bytes=changed,new_RAM_bytes=0,
                whole_image_inverse=True,strict_inbound_hits=0,route_cases=count,
                linked_native_consumers=consumers,mutation_rejections=rejected,
                limits=['Effect allocation and deferred retirement are explicit ABI summaries; their retained native code and source lineage are pinned.',
                        'Native event/update/audio instructions execute directly. No actual emulator or complete gameplay claim.',
                        'New route scratch stores occur only below incoming SP; live caller frame and non11 RAM remain identical.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result))

if __name__=='__main__': main()
