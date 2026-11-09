#!/usr/bin/env python3
"""Isolated common-tile clear projection for static player companions.

The external Shoot route and primary-fighter parity machinery remain closed.
The retained actor tasks enqueue presentations; battle priority6000 draws them
after form-completion preloads, so expiration precedes the actual tile copy.
"""
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
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
import verify_shoot_caller_resident as resident
from analyze_shoot_companion_draw_order import contracts as order_contracts

BASE = 0x08000000
INPUT = '8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'
FIRST, LIMIT = 0x6FE800, 0x6FF000
OWNER, CAPTURE, RENDER, EXPIRE = FIRST, FIRST+0x100, FIRST+0x200, FIRST+0x600
GROUPS = (0x4A82D8, 0x60B1E0)
PHASES = (0x085CD340, 0x085CD3A0, 0x085CD420, 0x085CD4B0,
          0x085CD510, 0x085CD550, 0x085CD5E0, 0x085CD640,
          0x085CD6A0, 0x085CD710, 0x085CD740)

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest().upper()

def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]

def asm(source, raw):
    return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, BASE+raw)[0])

def owner():
    """Return a positively identified active terminal payload or zero.

    No new persistent pointer is introduced. The physical52-slot bound and
    statusbit2 come from11AC4/11BE4; callback identity is the resident graph.
    All registers exceptR0 and flags survive.
    """
    return asm(f'''
      push {{r1-r4, r8-r9, lr}}
      ldr r0, pool
      mov r1, #52
    slot:
      ldrh r2, [r0, #0x10]
      tst r2, #2
      beq next
      ldr r2, [r0]
      adr r3, phases
      mov r4, #{len(PHASES)}
    phase:
      ldr r8, [r3], #4
      cmp r2, r8
      beq found
      subs r4, r4, #1
      bne phase
    next:
      add r0, r0, #0x118
      subs r1, r1, #1
      bne slot
      mov r0, #0
      b done
    found:
      add r0, r0, #0x18
    done:
      pop {{r1-r4, r8-r9, lr}}
      bx lr
    pool: .word 0x02010000
    phases:
      {''.join(f'.word {p:#x};' for p in PHASES)}
    ''', OWNER)

def capture():
    # The hook replaces only the actual197A BL clear_rows at085CD314.
    # Original clear_rows remains the tail callee, preserving its ABI/behavior.
    return asm('''
      push {r0-r3}
      ldr r0, current
      ldr r0, [r0]
      add r0, r0, #0x18
      mov r2, #0
      cmp r1, #260
      bls save
      cmp r1, #288
      bhi save
      lsl r2, r1, #1
      sub r2, r2, #448
      orr r2, r2, #0xF00
    save:
      strh r2, [r0, #0x52]
      pop {r0-r3}
      b 0x085CD920
    current: .word 0x0300133C
    ''', CAPTURE)

def companion_p0s(data):
    return tuple(u32(data, group+32*i) for group in GROUPS for i in range(15))

def renderer(data):
    """Relocate the actual dynamic renderer, adding only logical blanking.

    The12C28 dispatcher already pushedR0-R5/LR. Its table points to this entry,
    so the original12C58 PUSH must not be cloned. R9 is kept on an extra stack
    word and carries the mask; every original pixel/OAM/index instruction stays.
    """
    texts = [f'''
      push {{r9}}
      mov r9, #0
      ldrh r0, [r5, #0x14]
      cmp r0, #0x49
      bne original
      ldrh r0, [r5, #8]
      tst r0, #2
      bne original
      ldr r0, [r5, #0x48]
      adr r1, companion_p0s
      mov r2, #30
    match_p0:
      ldr r3, [r1], #4
      cmp r0, r3
      beq recognized
      subs r2, r2, #1
      bne match_p0
      b original
    recognized:
      bl {BASE+OWNER:#x}
      cmp r0, #0
      ldrhne r9, [r0, #0x52]
    original:
    ''']
    cs = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    ins = list(cs.disasm(data[0x12C5C:0x12DBC], BASE+0x12C5C))
    need(len(ins)*4 == 0x160, 'whole retained native renderer decode')
    for i in ins:
        texts.append(f'n{i.address:x}:')
        if i.address == 0x08012D54:
            # R4 is dead after native attr2 construction; R8 is already the
            # original copy scratch. No sprite position/index changes occur.
            texts.append('''
              cmp r9, #0
              beq normal_pixels
              and r4, r9, #255
              add r8, r3, #0x49
              sub r4, r8, r4
              cmp r4, #3
              bhi normal_pixels
              mov r8, #0x100
              lsl r8, r8, r4
              tst r9, r8
              beq normal_pixels
              adr r3, zero_tile
              b n8012d58
            normal_pixels:
              add r3, r11, r3, lsl #5
            ''')
        elif i.address == 0x08012DB4:
            texts.extend(['pop {r9}', 'pop {r0-r5, lr}'])
        elif i.address in (0x08012C5C, 0x08012C60, 0x08012DAC):
            texts.append({0x08012C5C:'ldr r12, oam',
                          0x08012C60:'ldr r0, count',
                          0x08012DAC:'ldr r2, count'}[i.address])
        elif i.mnemonic.startswith('b') and i.op_str.startswith('#'):
            target = int(i.op_str[1:], 16)
            need(BASE+0x12C5C <= target < BASE+0x12DBC, 'internal clone branch')
            texts.append(f'{i.mnemonic} n{target:x}')
        else:
            texts.append(f'{i.mnemonic} {i.op_str}')
    texts.extend(['.align 2', 'oam: .word 0x03001428',
                  'count: .word 0x030012CA', 'zero_tile: .space 32, 0',
                  'companion_p0s:'])
    texts.extend(f'.word {x:#x}' for x in companion_p0s(data))
    return asm('\n'.join(texts), RENDER)

def expiration():
    """Expire the physical overlap at the omitted2E74 companion preload.

    At35346C R5 is the selected resource byte offset, including the form delta.
    The retained349C..34A4 adds companion table084A82D8 only after this hook.
    R3 is the positively retained fixed tile base49/6D. All original registers
    and flags are restored, then the displacedLDRR0 is executed exactly.
    The priority6000 list consumer runs after the fighter's preload.
    """
    return asm(f'''
      push {{r0-r12, lr}}
      mrs r12, cpsr
      push {{r12}}
      bl {BASE+OWNER:#x}
      cmp r0, #0
      beq done
      ldr r4, companion_table
      ldr r4, [r4, r5]
      ldr r4, [r4, #4]
      ldr r4, [r4]
      lsr r4, r4, #5
      add r4, r4, r3
      ldrh r1, [r0, #0x52]
      and r2, r1, #255
      mov r6, #0x100
      mov r7, #4
    tile:
      cmp r2, r3
      blo next
      cmp r2, r4
      biclo r1, r1, r6
    next:
      add r2, r2, #1
      lsl r6, r6, #1
      subs r7, r7, #1
      bne tile
      strh r1, [r0, #0x52]
    done:
      pop {{r12}}
      msr cpsr_f, r12
      pop {{r0-r12, lr}}
      ldr r0, [sp, #0x20]
      b 0x08353470
    companion_table: .word 0x084A82D8
    ''', EXPIRE)

def pieces(data):
    blobs = [('owner', OWNER, owner()), ('capture', CAPTURE, capture()),
             ('renderer', RENDER, renderer(data)), ('expiration', EXPIRE, expiration())]
    for n, (_, start, blob) in enumerate(blobs):
        end = blobs[n+1][1] if n+1 < len(blobs) else LIMIT
        need(start+len(blob) <= end, 'resident functions do not overlap')
    return blobs


def writes(data):
    return pieces(data)+[
        ('capture_hook',0x5CD314,asm(f'bl {BASE+CAPTURE:#x}',0x5CD314)),
        ('renderer_pointer',0x12C50,struct.pack('<I',BASE+RENDER)),
        ('preload_hook',0x35346C,asm(f'b {BASE+EXPIRE:#x}',0x35346C))]


def validate(before, after):
    need(len(before)==len(after), 'unchanged ROM size')
    inverse=bytearray(after)
    for name, at, blob in writes(before):
        need(after[at:at+len(blob)]==blob, 'exact '+name)
        inverse[at:at+len(blob)]=before[at:at+len(blob)]
    need(bytes(inverse)==before and sha(inverse)==INPUT,
         'whole-ROM inverse; no undeclared write')


def build(before, source):
    need(sha(before)==INPUT and sha(source)==SOURCE, 'exact v70/source inputs')
    need(before[FIRST:LIMIT]==b'\xFF'*(LIMIT-FIRST), 'entire reservation is erased')
    need(sha(Path(resident.__file__).read_bytes())==SCANNER, 'frozen inbound scanner')
    scan=types.FunctionType(resident.inbound.__code__,
        dict(resident.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=resident.inbound.__defaults__)
    incoming=scan(before)
    need(not incoming, 'no existing inbound reference to resident reservation')
    order=order_contracts(source,before)
    need(u32(before,0x5CD314)==0xEB000181 and u32(before,0x35346C)==0xE59D0020,
         'exact displaced capture and preload instructions')
    after=bytearray(before)
    blobs=writes(before)
    for _,at,blob in blobs:after[at:at+len(blob)]=blob
    validate(before,after)
    negatives=[]
    for name,at,_ in blobs:
        bad=bytearray(after);bad[at]^=1
        try:validate(before,bad)
        except ValueError:negatives.append(name)
        else:raise ValueError('accepted output mutation '+name)
    bad=bytearray(after);bad[LIMIT]^=1
    try:validate(before,bad)
    except ValueError:negatives.append('outside reservation')
    else:raise ValueError('accepted outside write')
    for name,at,is_source in [('source append',0x742420,True),
        ('native actual draw',0x373570,False),('battle priority',0xD1BF0,False),
        ('preload side base',0x353464,False),
        ('preload resource offset',0x353350,False),
        ('preload form delta',0x353380,False),
        ('preload companion table',0x3534D4,False)]:
        bad=bytearray(source if is_source else before);bad[at]^=1
        try:order_contracts(bad if is_source else source,before if is_source else bad)
        except (ValueError,AssertionError):negatives.append(name)
        else:raise ValueError('accepted order mutation '+name)
    return bytes(after),dict(schema=2,status='STATIC_COMPANION_COMPONENT_PASS',
        input_sha256=INPUT,source_sha256=SOURCE,output_sha256=sha(after),rom_emitted=True,
        external_entry_authorized=False,complete_terminal_clear=False,
        scope='30 exact static companion P0 owners; fixed base49; indexed flag clear; BX261..288',
        draw_order=order,source_correct_upload_expiration=True,
        existing_native_dynamic_OAM_indices_preserved=True,
        new_task_or_persistent_RAM=False,storage='existing terminal payload+52 dead case argument',
        reservation=[FIRST,LIMIT],incoming_references=incoming,
        conservative_census_dependency_sha256=SCANNER,whole_ROM_inverse=True,
        changed_bytes=sum(a!=b for a,b in zip(before,after)),
        negative_controls_rejected=negatives,
        writes=[dict(name=name,raw=at,bytes=len(blob),sha256=sha(blob)) for name,at,blob in blobs],
        remaining=['Lower common tiles/primary fighter parity and queues are not projected.',
            'Other common/fixed-tile owners, non-common clear destinations and IRQ/external-entry contracts remain separate.',
            'Record21 retains the retail nine-layout adaptation; source1.0 and1.5 content match and no asset repair is included.',
            'No emulator/runtime entry or arbitrary corrupted/foreign scheduler state was tested.'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',required=True,type=Path)
    a=p.parse_args()
    paths=[p.resolve() for p in (a.candidate,a.source,a.output,a.manifest)]
    need(len(set(paths))==4,'distinct input and output paths')
    need(a.source.suffix.lower()=='.wsc' and a.output.suffix.lower()=='.gba', 'explicit ROM types')
    need(not a.output.exists() and not a.manifest.exists(),'fresh outputs required')
    after,report=build(a.candidate.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('status','rom_emitted','scope')}))

if __name__=='__main__':
    main()
