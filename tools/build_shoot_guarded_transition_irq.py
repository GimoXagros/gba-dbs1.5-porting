#!/usr/bin/env python3
"""Bounded stationary Shoot transition IRQ; no general low-Y entry claim."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
import verify_shoot_caller_resident as resident
from verify_shoot_static_companion_clear import Machine

BASE = 0x08000000
INPUT = '025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
START, IRQ, LIMIT = 0x6FF9C0, 0x6FFE10, 0x6FFED0
ADAPTER, ADAPTER_LIMIT, SITE = 0x6FF600, 0x6FF800, 0xD0BE8
STATE, SLOT = 0x03004710, 0x030012E0
OFFSETS = bytes((0, 2, 4, 7, 10, 13, 17, 21))


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def asm(source, raw):
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE + raw)[0])


def irq_code():
    # C4C returns DISPSTAT, whose compare byte is source OUT03 +8. Read it
    # again after F44 exactly as the original does; preserve all live registers.
    return asm(f'''
        push {{r0-r12, lr}}
        mrs r12, cpsr
        push {{r12}}
        ldr r4, state
        ldrh r5, [r4, #6]
        adr r6, offsets
        ldrb r6, [r6, r5]
        bl 0x08000C4C
        lsr r0, r0, #8
        sub r0, r0, #8
        and r0, r0, #255
        ldrb r1, [r4, #4]
        add r1, r1, r6
        and r1, r1, #255
        cmp r0, r1
        bne mismatch
        ldrb r0, [r4, #8]
        sub r0, r0, r6
        and r0, r0, #255
        bl 0x08000F44
        ldrh r0, [r4, #4]
        add r0, r0, #1
        strh r0, [r4, #4]
        add r5, r5, #1
        strh r5, [r4, #6]
        cmp r5, #8
        bne schedule
        ldr r0, slot
        adr r1, final
        str r1, [r0]
        b schedule
    mismatch:
        ldrb r0, [r4, #10]
        bl 0x08000F44
    schedule:
        bl 0x08000C4C
        lsr r0, r0, #8
        sub r0, r0, #7
        and r0, r0, #255
        add r0, r0, #8
        bl 0x08000C10
        pop {{r12}}
        msr cpsr_f, r12
        pop {{r0-r12, lr}}
        bx lr
    final:
        bx lr
    state: .word {STATE:#x}
    slot: .word {SLOT:#x}
    offsets: .byte {','.join(str(x) for x in OFFSETS)}
    ''', IRQ)


def irq_selfcheck(data, final):
    """Execute only new actual ARM logic; retained port helpers are ABI models."""
    count = 0
    for index in range(8):
        for counter in (0, 1, 127, 255, 256, 65535):
            for base in (0, 7, 21, 128, 255):
                for match in (False, True):
                    m = Machine(data, count, ((count % 16) << 28) | 0x10)
                    old = list(m.r)
                    m.r[14] = 0x09000000
                    old[14] = m.r[14]
                    cpsr = m.cpsr
                    compare = ((counter + OFFSETS[index]) + (0 if match else 1)) & 255
                    m.put(STATE + 4, counter, 2)
                    m.put(STATE + 6, index, 2)
                    m.put(STATE + 8, base, 2)
                    m.put(STATE + 10, 0xA65B, 2)
                    m.put(SLOT, BASE + IRQ)
                    calls = []
                    def read(mm):
                        mm.r[0] = (((compare + 8) & 255) << 8) | 0x27
                        mm.r[8] = 0x04000000
                    def vertical(mm):
                        calls.append(('vertical', mm.r[0]))
                        mm.r[8:11] = [0x030012B9, 0x04000000, (mm.r[0]-8)&0xFFFFFFFF]
                    def schedule(mm):
                        calls.append(('schedule', mm.r[0]))
                        mm.r[8:10] = [0x04000000, 0x12345678]
                    m.services.update({0x08000C4C:read, 0x08000F44:vertical, 0x08000C10:schedule})
                    m.run(BASE + IRQ, {0x09000000})
                    need(m.r[:15] == old[:15] and m.cpsr == cpsr, 'IRQ live register/flag preservation')
                    need(calls == [('vertical', (base-OFFSETS[index])&255 if match else 0x5B),
                                   ('schedule', ((compare+1)&255)+8)], 'source per-step port semantics')
                    need(m.get(STATE+4,2) == (counter+int(match))&65535 and
                         m.get(STATE+6,2) == index+int(match), 'full16bit source counters')
                    need(m.get(SLOT) == (final if match and index==7 else BASE+IRQ), 'eighth-match callback replacement')
                    count += 1
    m=Machine(data, 1, 0xA0000010);before=list(m.r);flags=m.cpsr
    m.r[14]=0x09000000;before[14]=m.r[14]
    m.run(final,{0x09000000})
    need(m.r[:15]==before[:15] and m.cpsr==flags and not m.writes, 'observational final has no writes or clobbers')
    return {'actual_ARM_step_cases':count, 'final_callback_cases':1}


def guard_code():
    literals = []
    def load(reg, value):
        label='lit'+str(len(literals));literals.append((label,value))
        return f'ldr {reg}, {label}\n'
    def expect(reg, offset, value, size=''):
        return f'ldr{size} r0, [{reg}, #{offset}]\n'+load('r1',value)+'cmp r0, r1\nbne reject\n'
    text='push {lr}\n'
    text+=load('r0',0x0300231E)+'ldrb r0, [r0]\ncmp r0, #11\nbne reject\n'
    # The actual terminal input/battle tasks exclude normal input and collisions.
    for address,callback in ((0x03004510,0x08374FAC),(0x03004514,0x0837354C)):
        text+=load('r0',address)+'ldr r7, [r0]\nadd r0, r7, #0x18\nbl active\ncmp r0, #0\nbeq reject\n'
        text+=expect('r7',0,callback)
    for reg,address in (('r4',0x0300489C),('r5',0x030048A0),('r6',0x03004D3C)):
        text+=load('r0',address)+f'ldr {reg}, [r0]\nmov r0, {reg}\nbl active\ncmp r0, #0\nbeq reject\n'
    text+='cmp r4, r5\nbeq reject\ncmp r4, r6\nbeq reject\ncmp r5, r6\nbeq reject\n'
    text+=expect('r4',0,0x0835620C)+expect('r5',0,0x085BF200)+expect('r6',0,0x085BF600)
    text+='ldrh r0, [r4, #4]\nands r0, r0, #15\nbne reject\nldrb r0, [r4, #0x11]\ncmp r0, #0\nbne reject\n'
    text+='ldrh r0, [r4, #6]\ntst r0, #3\nbne reject\nldrh r0, [r4, #8]\ntst r0, #0x100\nbne reject\n'
    for offset in (0x2C,0x2E,0x42,0x44,0x46,0x48,0x4A,0x4C):
        text+=f'ldrh r0, [r4, #{offset}]\ncmp r0, #0\nbne reject\n'
    for offset in (0x34,0x36):
        text+=f'ldrh r0, [r4, #{offset}]\nldrh r1, [r4, #{offset+4}]\ncmp r0, r1\nbne reject\n'
    # Positive presentation resources and event identities bound upload owners.
    for reg,p0,p1,event in (('r4',0x080D7A58,0x080D45B8,0),
                           ('r5',0x085D1000,0x085D0000,1),
                           ('r6',0x085D1100,0x085D029C,0)):
        text+=expect(reg,0xF4,p0)+expect(reg,0xF0,p1)+expect(reg,0xBA,event,'h')
    text+='ldr r0, [r5, #0x28]\ncmp r0, r6\nbne reject\nldr r0, [r6, #0x18]\ncmp r0, r5\nbne reject\n'
    text+=load('r0',0x0300482A)+'ldrh r0, [r0]\ncmp r0, #1\nbne reject\n'
    text+=load('r0',0x03004830)+'ldr r0, [r0]\nadd r1, r4, #0xAC\ncmp r0, r1\nbne reject\n'
    for address in (0x03002354,0x03002356,0x030023A4,0x030023A6):
        text+=load('r0',address)+'ldrh r0, [r0]\ncmp r0, #0\nbne reject\n'
    # Native hardware mapping is checked, not inferred from the source map name.
    text+=load('r0',0x04000000)+'ldrh r0, [r0]\nands r0, r0, #7\nbne reject\n'
    text+=load('r0',0x0400000A)+'ldrh r0, [r0]\n'+load('r1',0xDFCC)+'and r0, r0, r1\n'+load('r1',0x1E00)+'cmp r0, r1\nbne reject\n'
    text+=load('r0',0x06000000)+'mov r1, #8\nblank:\nldr r2, [r0], #4\ncmp r2, #0\nbne reject\nsubs r1, r1, #1\nbne blank\n'
    text+=load('r0',0x0300450A)+'ldrh r0, [r0]\ntst r0, #0x800\nbne accept\n'
    text+=load('r4',STATE)+'ldrh r0, [r4, #2]\ncmp r0, #1\nblo reject\ncmp r0, #143\nbhi reject\n'
    # All native lines, including the eight lines below the WSC144-line window.
    text+='add r6, r0, #37\nldrb r5, [r4, #8]\nsub r5, r5, #29\n'
    text+='line:\ncmp r6, #160\nbhs accept\nadd r0, r5, r6\nand r0, r0, #255\nand r7, r0, #7\nrsb r7, r7, #8\nlsr r0, r0, #3\n'
    text+=load('r1',0x0600F000)+'add r0, r1, r0, lsl #6\nmov r1, #16\nrow:\nldr r2, [r0], #4\ncmp r2, #0\nbne reject\nsubs r1, r1, #1\nbne row\nadd r6, r6, r7\nb line\n'
    text+='accept:\nmov r0, #1\npop {lr}\nbx lr\n'
    text+='reject:\nmov r0, #0\npop {lr}\nbx lr\n'
    # Match the actual52-slot physical pool before reading an activity field.
    text+='active:\n'+load('r1',0x02010018)+'mov r2, #52\nactive_loop:\ncmp r0, r1\nbeq active_found\nadd r1, r1, #0x118\nsubs r2, r2, #1\nbne active_loop\nmov r0, #0\nbx lr\nactive_found:\nldrh r0, [r1, #-8]\nand r0, r0, #2\nbx lr\n'
    text+=''.join(f'{label}: .word {value:#x}\n' for label,value in literals)
    return asm(text,START)


def active_entry(guard):
    marker=asm('mov r2, #52',0)
    at=guard.find(marker)
    need(at>=4 and guard.find(marker,at+1)<0,'one positively located52-slot activity helper')
    return BASE+START+at-4


def adapter_code(guard):
    return asm(f'''
        push {{lr}}
        bl 0x08017758
        pop {{lr}}
        push {{r0-r12, lr}}
        ldr r0, current
        ldr r7, [r0]
        ldr r0, display_task
        ldr r0, [r0]
        cmp r0, r7
        bne done
        ldr r0, last_task
        ldr r0, [r0]
        cmp r0, r7
        bne done
        add r0, r7, #0x18
        bl {active_entry(guard):#x}
        cmp r0, #0
        beq done
        ldr r0, [r7]
        ldr r1, display_callback
        cmp r0, r1
        bne done
        ldr r0, [r7, #4]
        cmn r0, #0x1000
        bne done
        ldr r0, queue
        ldr r1, [r0]
        cmp r1, #1
        bne done
        ldr r1, [r0, #4]
        ldr r2, old_display
        cmp r1, r2
        bne done
        ldr r0, flags
        ldrh r0, [r0]
        tst r0, #0x400
        beq done
        bl {BASE+START:#x}
        cmp r0, #0
        beq done
        ldr r0, queue
        adr r1, display
        str r1, [r0, #4]
    done:
        pop {{r0-r12, lr}}
        bx lr
    display:
        push {{r0, r1, lr}}
        ldr r0, mode
        ldrh r1, [r0]
        cmp r1, #7
        bne stale
        ldrb r0, [r0, #14]
        cmp r0, #11
        bne stale
        ldr r0, flags
        ldrh r0, [r0]
        tst r0, #0x400
        beq stale
        ldr r0, irq
        bl 0x085E7400
        pop {{r0, r1, lr}}
        bx lr
    stale:
        pop {{r0, r1, lr}}
        b 0x08587200
    current: .word 0x0300133C
    display_task: .word 0x03004518
    display_callback: .word 0x08352268
    queue: .word 0x03004574
    old_display: .word 0x08587200
    irq: .word {BASE+IRQ:#x}
    last_task: .word 0x03001344
    flags: .word 0x0300450A
    mode: .word 0x03002310
    ''',ADAPTER)


def guard_fixture(data):
    m=Machine(data,17,0x60000010)
    for address,size in ((0x02010000,0x600),(0x03002338,0xA0),
                         (0x06000000,32),(0x0600F000,0x800)):
        for i in range(0,size,4):m.put(address+i,0)
    first,upper,aux=0x02010248,0x02010360,0x02010478
    for header in (0x02010000,0x02010118,first-24,upper-24,aux-24):
        m.put(header+0x10,2,2)
    for address,value in ((0x03004510,0x02010000),(0x03004514,0x02010118),
                          (0x02010000,0x08374FAC),(0x02010118,0x0837354C),
                          (0x0300489C,first),(0x030048A0,upper),(0x03004D3C,aux),
                          (first,0x0835620C),(upper,0x085BF200),(aux,0x085BF600),
                          (upper+0x28,aux),(aux+0x18,upper),(0x03004830,first+0xAC)):
        m.put(address,value)
    for actor,p0,p1,event in ((first,0x080D7A58,0x080D45B8,0),
                              (upper,0x085D1000,0x085D0000,1),
                              (aux,0x085D1100,0x085D029C,0)):
        m.put(actor+0xF4,p0);m.put(actor+0xF0,p1);m.put(actor+0xBA,event,2)
    for offset,value in ((0x34,0xE00),(0x38,0xE00),(0x36,0x1500),(0x3A,0x1500)):
        m.put(first+offset,value,2)
    m.put(0x03002310,7,2);m.put(0x0300231E,11,1);m.put(0x0300482A,1,2)
    m.put(0x03004574,0)
    m.put(0x04000000,0,2)
    m.put(0x0400000A,0x1E00,2);m.put(0x0300450A,0x400,2)
    m.put(STATE+2,40,2);m.put(STATE+8,0xB8,2)
    m.r[14]=0x09000000
    return m,first,upper,aux


def guard_selfcheck(data):
    changes=[('stage',0x0300231E,7,1),('wrong input',0x02010000,0x08374FF4,4),
             ('wrong battle',0x02010118,0x083735BC,4),
             ('unowned FIRST',0x0300489C,0x02010249,4),
             ('inactive FIRST',0x02010240,0,2),('moving callback',0x02010248,0x083562B4,4),
             ('held',0x02010274,0x40,2),('edge',0x02010276,0x80,2),
             ('drop through',0x0201024E,2,2),('evolved',0x02010250,0x100,2),
             ('x displacement',0x02010292,1,2),('previous Y',0x02010282,0x1400,2),
             ('upper callback',0x02010360,0x085BEA00,4),('aux callback',0x02010478,0x085BF800,4),
             ('upload owner',0x03004830,0x02010478+0xAC,4),
             ('blank tile',0x0600001C,1,4),('hardware map',0x0400000A,0x1F00,2),
             ('mosaic',0x0400000A,0x1E40,2),('bitmap mode',0x04000000,3,2),
             ('first BG velocity',0x03002354,1,2),('second BG velocity',0x030023A6,1,2),
             ('bad visible counter',STATE+2,0,2)]
    cases=0
    for change in [None]+changes:
        m,_,_,_=guard_fixture(data)
        if change:m.put(change[1],change[2],change[3])
        sp=m.r[13]
        target=m.run(BASE+START,{0x09000000},max_steps=40000)
        need(m.r[0]==int(change is None),'guard predicate '+str(change))
        need(m.r[13]==sp and m.r[14]==0x09000000,'checker stack ABI')
        cases+=1
    # Independently mutate each current sampled row, including the native-only
    # bottom8 lines; one nonzero cell in any horizontal column must reject.
    for k in (1,40,114,115,122,123,143):
        for base in (0,7,0xB8,255):
            rows={((base-29+y)&255)//8 for y in range(k+37,160)}
            for row in rows:
                m,_,_,_=guard_fixture(data);m.put(STATE+2,k,2);m.put(STATE+8,base,2)
                m.put(0x0600F000+row*64+62,1,2)
                m.run(BASE+START,{0x09000000},max_steps=40000)
                need(m.r[0]==0,'actual160-line sampled row rejection')
                cases+=1
    return {'actual_ARM_guard_cases':cases,'negative_field_cases':len(changes),
            'native_visible_lines':160,'history_assumption':False}


def build(before, gba, source):
    need(sha(before)==INPUT and sha(gba)==GBA and sha(source)==SOURCE, 'fixed native/source identities')
    import analyze_shoot_guarded_transition_irq as contract
    source_contract=contract.proof(before,gba,source,START,LIMIT)
    adapter_layout=contract.layout_proof(before,ADAPTER,ADAPTER_LIMIT)
    guard,irq=guard_code(),irq_code()
    adapter=adapter_code(guard)
    need(START+len(guard)<=IRQ and IRQ+len(irq)==LIMIT and
         ADAPTER+len(adapter)<=ADAPTER_LIMIT,'bounded separate reservations')
    spans=((ADAPTER,ADAPTER_LIMIT),(START,LIMIT))
    for a,z in spans:need(before[a:z]==b'\xFF'*(z-a),'complete erased reservation')
    scanner=types.FunctionType(resident.inbound.__code__,dict(resident.__dict__,SPANS=spans),
                               argdefs=resident.inbound.__defaults__)
    incoming=scanner(before)
    need(not incoming,'strict whole-ROM inbound census without exemptions')
    need(before[SITE:SITE+4]==asm('bl 0x08017758',SITE),'exact displaced queue-copy call')
    writes=[('late_queue_copy_hook',SITE,asm(f'bl {BASE+ADAPTER:#x}',SITE)),
            ('postcopy_adapter_and_tiny_display',ADAPTER,adapter),
            ('readonly_stationary_and_current_pixels_guard',START,guard),
            ('source_irq_and_observational_final',IRQ,irq)]
    after=bytearray(before)
    for _,at,blob in writes:after[at:at+len(blob)]=blob
    def validate(candidate):
        need(len(candidate)==len(before),'exact output length')
        inverse=bytearray(candidate)
        for name,at,blob in writes:
            need(candidate[at:at+len(blob)]==blob,'exact emitted '+name)
            inverse[at:at+len(blob)]=before[at:at+len(blob)]
        need(inverse==before,'whole-ROM inverse and all prior components retained')
    validate(after)
    final=BASE+IRQ+irq.index(asm('bx lr',0))+4
    need(after[final-BASE:final-BASE+4]==asm('bx lr',0),'exact final return-only entry')
    display=BASE+ADAPTER+adapter.index(asm('push {r0,r1,lr}',0))
    semantics=dict(guard=guard_selfcheck(after),irq=irq_selfcheck(after,final),
                   adapter=adapter_selfcheck(after,display))
    rejected=[]
    for name,at in [(n,a) for n,a,_ in writes]+[('undeclared gap',IRQ-4),('frozen router',0x5E7A0C)]:
        bad=bytearray(after);bad[at]^=1
        try:validate(bad)
        except ValueError:rejected.append(name)
        else:raise ValueError('accepted output corruption '+name)
    return bytes(after),dict(schema=1,status='BOUNDED_STATIONARY_TRANSITION_COMPONENT_PASS',
        input_sha256=INPUT,retail_sha256=GBA,source_sha256=SOURCE,output_sha256=sha(after),
        source_contract=source_contract,adapter_layout=adapter_layout,
        reservations=[list(s) for s in spans],incoming_references=incoming,
        entries=dict(adapter=BASE+ADAPTER,display=display,guard=BASE+START,irq=BASE+IRQ,final=final),
        writes=[dict(name=n,raw=a,bytes=len(b),sha256=sha(b)) for n,a,b in writes],
        changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_ROM_inverse=True,
        semantics=semantics,negative_controls_rejected=rejected,
        new_RAM_or_task=False,source_DI_value_emulated=False,external_entry_authorized=False,
        complete_Shoot=False,low_Y_moving_family_closed=False,
        scope='Late prepared-queue resident stationary base0 family with current blank sampled rows; all rejected queues unchanged',
        dependencies={n:sha((ROOT/'tools'/n).read_bytes()) for n in
                      ('build_shoot_guarded_transition_irq.py','analyze_shoot_guarded_transition_irq.py')})


def adapter_selfcheck(data,display):
    """Compare with actual17758, including its clobbered output registers."""
    mutations=[None,('other current',0x0300133C,0x02010000,4),
        ('not last',0x03001344,0x02010000,4),('bad display callback',0x02010578,0,4),
        ('unsigned priority',0x0201057C,0xF000,4),
        ('wrong priority',0x0201057C,0xE000,4),('inactive display task',0x02010588,0,2),
        ('empty queue',0x03002474,0,2),('multiple queue',0x03002474,2,2),
        ('other callback',0x03002478,0x080C97B8,4),('not transition',0x0300450A,0,2),
        ('moving FIRST',0x0201028C,1,2)]
    for change in mutations:
        pair=[]
        for start in (0x08017758,BASE+ADAPTER):
            m,_,_,_=guard_fixture(data)
            for address,value in ((0x0300133C,0x02010578),(0x03001344,0x02010578),
                                  (0x03004518,0x02010578),(0x02010578,0x08352268),
                                  (0x0201057C,0xFFFFF000)):
                m.put(address,value)
            m.put(0x02010588,2,2);m.put(0x03002474,1,2)
            for i in range(100):m.put(0x03002478+4*i,0x08587200 if i==0 else i)
            if change:m.put(change[1],change[2],change[3])
            m.run(start,{0x09000000},max_steps=40000);pair.append(m)
        old,new=pair
        need(old.r[:15]==new.r[:15],'post17758 register outputs preserved '+str(change))
        old_effect=[x for x in old.writes if not 0x03007000<=x[0]<0x03008000]
        new_effect=[x for x in new.writes if not 0x03007000<=x[0]<0x03008000]
        need(new_effect==old_effect+([] if change else [(0x03004578,display,4)]),
             'only eligible sole queued callback substituted '+str(change))
    for mode,stage,flags in ((7,11,0x400),(7,7,0x400),(7,11,0),(8,11,0xD86)):
        m,_,_,_=guard_fixture(data);m.put(0x03002310,mode,2)
        m.put(0x0300231E,stage,1);m.put(0x0300450A,flags,2)
        old=list(m.r);seen=[]
        m.services[0x085E7400]=lambda mm:seen.append(mm.r[0])
        stop=m.run(display,{0x09000000,0x08587200},max_steps=100)
        need(m.r[:15]==old[:15],'tiny wrapper restores incoming registers')
        eligible=mode==7 and stage==11 and bool(flags&0x400)
        need(stop==(0x09000000 if eligible else 0x08587200) and
             seen==([BASE+IRQ] if eligible else []),'live callback stale-stage/phase gate')
    return dict(actual_copy_join_cases=len(mutations),live_wrapper_cases=4,
                original17758_executed=True,postcopy_registers_preserved=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('input',type=Path);p.add_argument('gba',type=Path)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--manifest',type=Path,required=True)
    a=p.parse_args()
    need(len({p.resolve() for p in (a.input,a.gba,a.source,a.output,a.manifest)})==5,'distinct input/output paths')
    need(not a.output.exists() and not a.manifest.exists(),'fresh outputs required')
    data,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(data)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('[shoot-guarded-transition] '+report['output_sha256'])


if __name__=='__main__':main()
