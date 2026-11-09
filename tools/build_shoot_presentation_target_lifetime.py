#!/usr/bin/env python3
"""Isolated five-word fix for the presentation target across native angle calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_shoot_static_companion_clear import Machine as OriginalMachine, signed
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16

ROOT = Path(__file__).resolve().parents[1]
BASE, ENTRY, RETURN = 0x08000000, 0x085C9100, 0x09000000
INPUT = 'D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CAPTURE = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-b'
RAM_PINS = {'ewram.bin': '64F86BFA9A8EE96086998E2FF7294BDB1D4212457E2F7263EBAE3674B8EF5ACB',
            'iwram.bin': 'BC10319BFC772FCE8D379D02E78061B9D2C00E21116EA19A47EBE9DCA3929B12'}
OBJECT, TARGET = 0x020112B0, 0x02011828
WRITES = ((0x5C9108, 0xE5941014, 0xE5946014),
          (0x5C910C, 0xE1D103F4, 0xE1D603F4),
          (0x5C9120, 0xE1D133F6, 0xE1D633F6),
          (0x5C9174, 0xE1D103F4, 0xE1D603F4),
          (0x5C91A4, 0xE1D103F6, 0xE1D603F6))
PINS = ((0x5C9100, 0x5C9208, 'A150F3C5A715F6131D6DB358676C75E011482B14C6BF331E807076CF2395CB0D'),
        (0x12560, 0x125FC, '2861671771BD772F199B1CDC6C9FFDFB2C5C909F8ACFD67E081704267B156FFA'),
        (0x12650, 0x12710, '1BCC645673A5922816FC034CA0BD693675D8FBD35833361DCAD235573FF2640C'),
        (0x1233C, 0x12560, '4A17D49503101E0A84B5E167B2D851704BB3F00F0495E5F7F7AF8F827EC18523'),
        (0x3524C4, 0x352570, '0855FA3FFA0344F386DE208941FAC054CD6F33A5A88F40F49B91EEC88DD6C14B'),
        (0x352AF8, 0x352B10, '69FBE2499D05F07ED8C1F4DFFA9FF721FE6DC89B2EE6E7B1A0C6CAE8832689DA'),
        (0x11E7C, 0x11E8C, '203A3CFD02495B3D7C2C7BF387D28A63CF4D9410C598F643147894B2D71CEE32'))


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data): return hashlib.sha256(data).hexdigest().upper()
def u(data, at): return struct.unpack_from('<I', data, at)[0]


class Machine(OriginalMachine):
    """Existing strict ARM runner plus the three actual missing instructions.

    Only MUL at126D8/126FC and register-offset LDRSH at12358 are added.
    The actual ARM division thunk runs; its Thumb SWI6 boundary is modeled.
    No angle, trig, event, task release or callback service is mocked.
    """
    SPECIAL = {0x080126D8, 0x080126FC, 0x08012358, 0x0837D5E9}

    def __init__(self, rom, seed=0, flags=0x10):
        super().__init__(rom, seed, flags)
        self.bios_calls = []
        self.extra_executed = []

    def run(self, start, stops, max_steps=16000):
        pc = start
        for _ in range(512):
            pc = super().run(pc, set(stops) | self.SPECIAL, max_steps)
            if pc in stops:
                return pc
            self.extra_executed.append(pc)
            if pc == 0x0837D5E9:
                # Explicit ABI boundary: BIOS code/hardware is not executed.
                left, right = signed(self.r[0], 32), signed(self.r[1], 32)
                need(right != 0, 'nonzero divisor in executed BIOS boundary')
                keep = self.r[4:12]
                q = abs(left) // abs(right)
                if (left < 0) != (right < 0): q = -q
                rem = left - q * right
                self.bios_calls.append(dict(numerator=left, denominator=right,
                                            target_r6=self.r[6], quotient=q, remainder=rem))
                self.r[0], self.r[1], self.r[3] = q & 0xFFFFFFFF, rem & 0xFFFFFFFF, abs(q)
                self.cpsr = (self.cpsr & 0x0FFFFFFF) | 0xA0000000
                need(self.r[4:12] == keep, 'modeled SWI6 callee-preserved register ABI')
                pc = self.r[14]
                continue
            word = self.get(pc)
            self.r[15] = pc + 8
            need(word >> 28 == 14, 'reviewed unconditional added instruction')
            if pc in (0x080126D8, 0x080126FC):
                need(word == 0xE0000093, 'exact native MUL r0,r3,r0')
                self.r[0] = (self.r[3] * self.r[0]) & 0xFFFFFFFF
            else:
                need(word == 0xE19800F9, 'exact native register-offset LDRSH r0,[r8,r9]')
                self.r[0] = signed(self.get(self.r[8] + self.r[9], 2), 16) & 0xFFFFFFFF
            pc += 4
        raise ValueError('bounded native helper transitions did not return')


def contract(before, gba, source):
    need((sha(before), sha(gba), sha(source)) == (INPUT, GBA, SOURCE), 'exact D0 and immutable originals')
    need(sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes()) ==
         'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943', 'frozen strict ARM dependency')
    for lo, hi, digest in PINS:
        need(sha(before[lo:hi]) == digest, f'exact reviewed code {lo:X}')
        if lo < 0x400000:
            need(before[lo:hi] == gba[lo:hi], 'native imported body remains retail')
    need(sha(source[0x7735D4:0x773650]) ==
         '99C91CB79EC99AE4893FB8D4A5984348F797E5D88B7F9EC1E7D41859840D820F', 'source homing and completion body')
    x86 = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[0x7735D4:0x773650], 0x7735D4))
    need([(x.address, x.op_str) for x in x86 if x.address in (0x7735D4,0x773611,0x773624)] ==
         [(0x7735D4,'bx, word ptr [si + 0x12]'), (0x773611,'ax, word ptr [bx + 0x26]'),
          (0x773624,'ax, word ptr [bx + 0x28]')], 'source receiver lifetime across angle/trig')
    arm = Cs(CS_ARCH_ARM, CS_MODE_ARM); arm.detail = True
    body = list(arm.disasm(before[0x5C9100:0x5C91FC], ENTRY))
    target_uses = [x.address for x in body if '[r1,' in x.op_str]
    need(target_uses == [0x085C910C,0x085C9120,0x085C9174,0x085C91A4], 'all four original target dereferences')
    need(u(before,0x5C9100)==0xE92D5FFF and u(before,0x5C91F4)==0xE8BD5FFF,
         'complete r0-r12/LR outer save and restore')
    checked = []
    for lo, hi in ((0x12560,0x125FC),(0x12650,0x12710),(0x1233C,0x12360)):
        ins = list(arm.disasm(before[lo:hi], BASE+lo))
        need(sum(x.size for x in ins)==hi-lo, 'complete native helper decode')
        for x in ins:
            _, writes = x.regs_access()
            need('r6' not in [x.reg_name(r) for r in writes], f'callee does not overwrite r6 {x.address:X}')
            if x.mnemonic == 'bl':
                target = int(x.op_str[1:],16)
                need(target in (0x08012650,0x080126A4,0x0837DB3C), 'closed actual helper call graph')
        checked.append([lo,hi])
    need(before[0x37DB3C:0x37DB48] == bytes.fromhex('00C09FE51CFF2FE1E9D53708') and
         before[0x37D5E8:0x37D5EC] == bytes.fromhex('06DF7047'), 'actual ARM thunk to Thumb SWI6/BX LR')
    need(u(before,0x126DC)==0xE1A01009 and u(before,0x12700)==0xE1A01009,
         'both native divide branches overwrite original receiver r1')
    return dict(target_uses=target_uses, native_helper_no_r6_writes=checked,
                BIOS_boundary='SWI6 quotient/remainder and r4-r11 preservation explicitly modeled; BIOS not executed',
                helper_graph='12560 ->12650 ->126A4 ->37DB3C/37D5E9; trig1233C/12348 ->1234C',
                source_receiver='BX retained from7735D4 through773611/773624')


def capture_memory():
    mem = {}
    for name, address in (('ewram.bin',0x02000000),('iwram.bin',0x03000000)):
        blob = (CAPTURE/name).read_bytes()
        need(sha(blob)==RAM_PINS[name], 'frozen completed actual RAM '+name)
        mem.update((address+i, value) for i,value in enumerate(blob))
    return mem


def fixture(rom, mem, seed=0, nzcv=0, dx=None, dy=None, offset=0):
    m = Machine(rom,seed,(nzcv<<28)|0x10); m.mem = mem.copy()
    m.r[4],m.r[14] = OBJECT,RETURN
    if dx is not None:
        m.put(OBJECT+0x34,(m.get(TARGET+0x34,2)-dx)&65535,2)
        m.put(OBJECT+0x36,(m.get(TARGET+0x36,2)-dy)&65535,2)
    if offset:
        m.put(OBJECT+0xA0,offset&65535,2)
    m.reads.clear()
    return m


def effects(m):
    return [(a,v,n) for a,v,n in m.writes if not 0x03007000<=a<0x03008000]


def semantics(before, after, mem):
    old,new = fixture(before,mem),fixture(after,mem)
    need(new.get(OBJECT,4)==ENTRY and new.get(OBJECT+0x14,4)==TARGET and
         new.get(0x020121E8,4)==0x085C8400 and new.get(0x03004508,2)==2,
         'actual stalled presentation, target, waiting scene and absent event')
    actual_positions = [new.get(a,2) for a in (OBJECT+0x34,OBJECT+0x36,TARGET+0x34,TARGET+0x36)]
    need(actual_positions == [0x13A1,0x0CFB,0x13A1,0x0D2B], 'exact actual inside-box positions')
    old.run(ENTRY,{0x085C9174}); new.run(ENTRY,{0x085C9174})
    need(old.r[1]==new.r[1]==0 and new.r[6]==TARGET, 'actual native divide loses r1, repaired r6 retains target')
    need(effects(old)==effects(new), 'repair leaves real angle/trig and velocity writes identical')
    initial = fixture(after,mem).r[:15]
    new.run(0x085C9174,{RETURN})
    need(new.r[:15]==initial, 'actual complete repaired callback restores all saved registers and frame')
    need(new.get(0x03004508,2)==0x12, 'natural real completion event write')
    need(new.get(OBJECT+0xA,2)&0x8000 and new.get(OBJECT+4,2)&0x20,
         'real native release marks correct presentation')
    need(new.get(OBJECT-0x18,4)==u(after,0x352560), 'real release replaces owning task callback')
    need(any(target==0x083524C4 for _,target,_ in new.calls), 'actual release routine executed')
    actual = dict(positions=actual_positions, original_target_register_after_angle=old.r[1],
                  fixed_target_register_before_completion=TARGET, event_before=2,event_after=0x12,
                  native_release_callback=new.get(OBJECT-0x18,4), writes=effects(new),
                  BIOS_calls=new.bios_calls, full_outer_registers_restored=True,
                  old_run_boundary='Stopped immediately before wrong receiver read at5C9174; BIOS memory not invented')
    count=0; divide_sites=set(); helper_cases=0
    for dx in (-257,-256,-1,0,1,256,257):
        for dy in (-257,-256,-1,0,1,256,257):
            if dx==dy==0: continue  # divide-by-zero is not needed for this repair
            for offset in (0,-28):
                for flags in (0,5,10,15):
                    m=fixture(after,mem,count%3,flags,dx,dy,offset); original=m.r[:15]
                    m.run(ENTRY,{RETURN})
                    inside=abs(dx)<=256 and abs(dy)<=256
                    need(m.get(0x03004508,2)==(0x12 if inside else 2), 'exact inclusive source completion box')
                    need(bool(m.get(OBJECT+0xA,2)&0x8000)==inside, 'release only inside actual target box')
                    need(m.r[:15]==original, 'every tested branch restores complete outer frame')
                    need(all(x['target_r6']==TARGET for x in m.bios_calls), 'r6 survives every executed divide boundary')
                    divide_sites.update(pc for pc,target,_ in m.calls if target==0x0837DB3C)
                    count+=1
    # Full NZCV domain for the unmodified captured runtime positions.
    for flags in range(16):
        m=fixture(after,mem,flags%3,flags); original=m.r[:15]
        m.run(ENTRY,{RETURN});need(m.r[:15]==original and m.get(0x03004508,2)==0x12,'captured pose all NZCV')
        helper_cases+=1
    need(divide_sites=={0x080126E0,0x08012704}, 'both native arithmetic/division branches executed')
    return dict(actual_capture=actual, boundary_cases=count,captured_pose_NZCV_cases=helper_cases,
                actual_native_division_branch_sites=sorted(divide_sites),
                modeled_services=['BIOS SWI6 only; native thunk, angle, trig and release execute actual ARM'],
                excluded_case='atan(0,0) division-by-zero output is unchanged and not modeled')


def validate(before, candidate):
    need(len(candidate)==len(before),'unchanged ROM size')
    inverse=bytearray(candidate)
    for at,old,new in WRITES:
        need(u(before,at)==old and u(candidate,at)==new,'exact ExpectedWrite at '+hex(at))
        struct.pack_into('<I',inverse,at,old)
    need(inverse==before,'whole-ROM inverse and off-target preservation')


def build(before,gba,source):
    proof=contract(before,gba,source)
    after=bytearray(before)
    for at,old,new in WRITES:
        need(u(before,at)==old,'original instruction expected');struct.pack_into('<I',after,at,new)
    validate(before,after); mem=capture_memory()
    checks=semantics(before,after,mem)
    negatives=[]
    for label,at in [('target load',0x5C9108),('pre-angle X',0x5C910C),('pre-angle Y',0x5C9120),
                     ('completion X',0x5C9174),('completion Y',0x5C91A4),('outside word',0x5C91DC),
                     ('entry selector preserved',0x33FD04),('unopened normal-hit hook',0x36E634)]:
        bad=bytearray(after);bad[at]^=1
        try:validate(before,bad)
        except ValueError:negatives.append(label)
        else:raise ValueError('ineffective exact inverse control')
    for at,label in ((0x5C9174,'lost completion X receiver'),(0x5C91A4,'lost completion Y receiver')):
        bad=bytearray(after);struct.pack_into('<I',bad,at,u(before,at))
        m=fixture(bad,mem)
        try:m.run(ENTRY,{RETURN})
        except ValueError as error:
            need('uninitialized read' in str(error),'semantic control rejects wrong receiver read')
            negatives.append(label)
        else:raise ValueError('ineffective receiver mutation')
    return bytes(after),dict(schema=1,status='PRESENTATION_TARGET_LIFETIME_AUTHOR_PASS',
        input_sha256=INPUT,output_sha256=sha(after),retail_sha256=GBA,source_sha256=SOURCE,
        source_contract=proof,semantics=checks,capture_sha256=RAM_PINS,
        writes=[dict(raw=at,bytes=4,before=struct.pack('<I',old).hex().upper(),
                     after=struct.pack('<I',new).hex().upper()) for at,old,new in WRITES],
        declared_bytes=20,changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        new_code_or_RAM_or_cave=False,forced_flags_coordinates_or_HP=False,actual_runtime_repair_observed=False,
        negative_controls_rejected=negatives,
        builder_sha256=sha(Path(__file__).read_bytes()),
        interpreter_sha256=sha((ROOT/'tools/verify_shoot_static_companion_clear.py').read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','gba','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    need(len({x.resolve() for x in (a.input,a.gba,a.source,a.output,a.manifest)})==5,'distinct paths')
    need(not a.output.exists() and not a.manifest.exists(),'fresh outputs only')
    result,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:report[k] for k in ('status','output_sha256','builder_sha256','changed_bytes')}))


if __name__=='__main__':main()
