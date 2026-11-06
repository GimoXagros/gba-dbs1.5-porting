#!/usr/bin/env python3
"""Independent source partition and actual ARM verification of the 28-byte subset repair."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_ARCH_X86,CS_MODE_16
BASE=0x08000000
BEFORE='B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B'
AFTER='8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOK,FIRST,LIMIT=0x5CC0F0,0x6FE000,0x6FE020
SPANS=((FIRST,LIMIT),)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)
def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def signed(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def rotate(v,n):return ((v>>n)|(v<<((32-n)&31)))&0xFFFFFFFF

def inbound(data, origin=0):
    """Independent conservative references: no data/interior exemptions."""
    matches = []

    def consider(kind, at, value):
        if 0x08000000 <= value < 0x0E000000:
            raw = value & 0x01FFFFFF
            if any(start <= raw < end for start, end in SPANS):
                matches.append((kind, origin + at, value))

    for alignment in range(4):
        stop = len(data) - (len(data) - alignment) % 4
        for i, (word,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            consider("pointer", alignment + 4 * i, word)
    for i, (word,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at = 4 * i
        pc = BASE + origin + at + 8
        if word & 0x0E000000 == 0x0A000000:
            consider("ARM branch", at, pc + signed(word & 0xFFFFFF, 24) * 4)
        if (word >> 16) & 15 == 15 and word & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            consider("ARM literal", at, pc + (1 if word & 0x800000 else -1) * (word & 0xFFF))
        if word & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            immediate = rotate(word & 255, ((word >> 8) & 15) * 2)
            consider("ARM ADR", at, pc + (immediate if (word >> 21) & 15 == 4 else -immediate))
    for at in range(0, len(data) - 1, 2):
        half = int.from_bytes(data[at:at + 2], "little")
        pc = BASE + origin + at + 4
        if half & 0xF800 in (0x4800, 0xA000):
            consider("Thumb literal/ADR", at, (pc & ~3) + (half & 255) * 4)
        if half & 0xF800 == 0xE000:
            consider("Thumb B", at, pc + signed(half & 0x7FF, 11) * 2)
        if half & 0xF000 == 0xD000 and (half >> 8) & 15 < 14:
            consider("Thumb conditional", at, pc + signed(half & 255, 8) * 2)
        if half & 0xF800 == 0xF000 and at + 4 <= len(data):
            tail = int.from_bytes(data[at + 2:at + 4], "little")
            if tail & 0xF800 in (0xF800, 0xE800):
                destination = pc + (signed(half & 0x7FF, 11) << 12) + ((tail & 0x7FF) << 1)
                consider("Thumb BL/BLX", at, destination & ~3 if tail & 0xF800 == 0xE800 else destination)
    return matches

class Arm:
    """Small strict interpreter, limited to instructions actually under review."""

    def __init__(self, rom, seed=0, flags=0x10, rng=0):
        self.rom, self.mem, self.writes, self.reads, self.calls = rom, {}, [], [], []
        self.r = [((0x13579BDF * (i + 1)) ^ (seed * 0x2468ACE1)) & 0xFFFFFFFF for i in range(16)]
        self.r[13], self.r[14] = 0x03007C00 - 4 * (seed % 32), 0x08001234
        self.cpsr, self.rng, self.rng_calls = flags, rng, 0

    def put(self, address, value, size=4, log=False):
        for i in range(size):
            self.mem[address + i] = (value >> (8 * i)) & 255
        if log:
            self.writes.append((address, value & ((1 << (8 * size)) - 1), size))

    def get(self, address, size=4):
        if BASE <= address and address + size <= BASE + len(self.rom):
            return int.from_bytes(self.rom[address - BASE:address - BASE + size], "little")
        need(all(address + i in self.mem for i in range(size)), f"uninitialized read {address:08X}/{size}")
        self.reads.append((address, size))
        return sum(self.mem[address + i] << (8 * i) for i in range(size))

    def operand(self, word):
        if word & 0x02000000:
            return rotate(word & 255, ((word >> 8) & 15) * 2)
        need(not word & 0x10, "register shift by immediate only")
        kind, count = (word >> 5) & 3, (word >> 7) & 31
        value = self.r[word & 15]
        need(kind == 0, "reviewed LSL operand only")
        return (value << count) & 0xFFFFFFFF

    def condition(self, cond):
        n, z, c, v = ((self.cpsr >> i) & 1 for i in (31, 30, 29, 28))
        return (z, not z, c, not c, n, not n, v, not v, c and not z,
                not c or z, n == v, n != v, not z and n == v, z or n != v, True, False)[cond]

    def run(self, start, stops):
        pc = start
        for _ in range(160):
            if pc in stops:
                return pc
            w = self.get(pc)
            self.r[15] = pc + 8
            nxt = pc + 4
            if not self.condition(w >> 28):
                pc = nxt
                continue
            if w & 0x0FFFFFF0 == 0x012FFF10:
                nxt = self.r[w & 15]
            elif w & 0x0FFF0FFF == 0x010F0000:
                self.r[(w >> 12) & 15] = self.cpsr
            elif w & 0x0FFFFFF0 == 0x0128F000:
                self.cpsr = (self.cpsr & 0x00FFFFFF) | (self.r[w & 15] & 0xFF000000)
            elif w & 0x0E000000 == 0x08000000:
                need(w & 0x0FFF0000 in (0x092D0000, 0x08BD0000), "reviewed PUSH/POP only")
                regs = [i for i in range(16) if w & (1 << i)]
                load = bool(w & 0x00100000)
                address = self.r[13] if load else self.r[13] - 4 * len(regs)
                for i, reg in enumerate(regs):
                    if load:
                        self.r[reg] = self.get(address + i * 4)
                    else:
                        self.put(address + i * 4, self.r[reg], log=True)
                self.r[13] += (1 if load else -1) * 4 * len(regs)
            elif w & 0x0E000000 == 0x0A000000:
                nxt = pc + 8 + signed(w & 0xFFFFFF, 24) * 4
                if w & 0x01000000:
                    self.r[14] = pc + 4
                    self.calls.append((pc, nxt, tuple(self.r[:5])))
                    if nxt == 0x08012600:
                        self.rng_calls += 1
                        self.r[0], self.r[8], self.r[9] = self.rng, 0xDEADBEEF, 0xBAD0CAFE
                        nxt = pc + 4
            elif w & 0x0C000000 == 0x04000000:
                need(w & 0x01000000 and not w & 0x00200000, "preindexed no-writeback transfer")
                offset = self.r[w & 15] if w & 0x02000000 else w & 0xFFF
                address = self.r[(w >> 16) & 15] + (offset if w & 0x00800000 else -offset)
                reg, size = (w >> 12) & 15, 1 if w & 0x00400000 else 4
                if w & 0x00100000:
                    self.r[reg] = self.get(address, size)
                else:
                    self.put(address, self.r[reg], size, True)
            elif w & 0x0E000090 == 0x00000090:
                need(w & 0x01400000 == 0x01400000 and not w & 0x00200000, "immediate halfword transfer")
                offset = ((w >> 4) & 0xF0) | (w & 15)
                address = self.r[(w >> 16) & 15] + (offset if w & 0x00800000 else -offset)
                reg, kind = (w >> 12) & 15, (w >> 5) & 3
                if w & 0x00100000:
                    value = self.get(address, 1 if kind == 2 else 2)
                    self.r[reg] = (signed(value, 8) if kind == 2 else signed(value,16) if kind == 3 else value) & 0xFFFFFFFF
                else:
                    need(kind == 1, "STRH only")
                    self.put(address, self.r[reg], 2, True)
            elif w & 0x0C000000 == 0:
                op, dest = (w >> 21) & 15, (w >> 12) & 15
                left, right = self.r[(w >> 16) & 15], self.operand(w)
                if op in (8, 10):
                    result = (left & right) if op == 8 else (left - right) & 0xFFFFFFFF
                    flags = (result & 0x80000000) | (0x40000000 if result == 0 else 0)
                    if op == 10:
                        flags |= (0x20000000 if left >= right else 0) | (((left ^ right) & (left ^ result) & 0x80000000) >> 3)
                        self.cpsr = (self.cpsr & 0x0FFFFFFF) | flags
                    else:
                        self.cpsr = (self.cpsr & 0x3FFFFFFF) | flags
                else:
                    need(op in (0,2,4,13), "reviewed AND/SUB/ADD/MOV only")
                    result=((left & right) if op==0 else left-right if op==2 else left+right if op==4 else right)&0xFFFFFFFF
                    self.r[dest]=result
                    if w&0x00100000:
                        need(op==2,'only reviewed SUBS')
                        self.cpsr=(self.cpsr&0x0FFFFFFF)|(result&0x80000000)|(0x40000000 if result==0 else 0)|(0x20000000 if left>=right else 0)|(((left^right)&(left^result)&0x80000000)>>3)
            else:
                raise ValueError(f"unsupported ARM instruction {pc:08X}:{w:08X}")
            pc = nxt
        raise ValueError("bounded ARM execution did not return/tail-call")


def source_partition(source):
    def word(off):return struct.unpack_from('<H',source,0x740900+(off&65535))[0]
    ins=[(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(source[0x7497F3:0x749829],0x7497F3)]
    need(ins==[('mov','cx, 5'),('mov','bx, 0x8fef'),('mov','ax, word ptr [si + 0x8c]'),
        ('cmp','ax, word ptr cs:[bx]'),('jle','0x749807'),('add','bx, 8'),('loop','0x7497fd'),
        ('mov','cx, word ptr cs:[bx + 2]'),('mov','bx, word ptr cs:[bx + 4]'),
        ('mov','ax, word ptr [si + 0x26]'),('cmp','ax, word ptr cs:[bx]'),('jl','0x74981c'),
        ('add','bx, 4'),('loop','0x749812'),('mov','bx, word ptr cs:[bx + 2]'),
        ('mov','ax, bx'),('add','bx, bx'),('jmp','word ptr cs:[bx - 0x7025]')],
        'complete actual source loops and exhausted fallthrough')
    # Derive disjoint signed-coordinate rectangles algebraically, not by the
    # producer's per-coordinate enumeration or claimed accepted predicate.
    limits=[signed(word(0x8FEF+8*k),16) for k in range(5)]
    need(limits==sorted(set(limits)),'strict Y thresholds')
    rectangles=[];ylow=-32768
    for index,yhigh in enumerate(limits+[32767]):
        row=0x8FEF+8*index
        count,pointer=word(row+2),word(row+4)
        need(1<=count<=9,'bounded actual exhausted X count')
        xlimits=[signed(word(pointer+4*k),16) for k in range(count)]
        need(xlimits==sorted(set(xlimits)),'strict X thresholds')
        xlow=-32768
        for k,xhigh in enumerate([v-1 for v in xlimits]+[32767]):
            token=word(pointer+4*k+2)
            destination=word(0x8FDB+2*token)
            normal=(token==0 and destination==0x8F29) or (1<=token<=9 and destination==0x8F65)
            rectangles.append(dict(x=[xlow,xhigh],y=[ylow,yhigh],token=token,destination=destination,normal=normal,
                pairs=(xhigh-xlow+1)*(yhigh-ylow+1)))
            xlow=xhigh+1
        ylow=yhigh+1
    need(sum(r['pairs'] for r in rectangles)==2**32,'exact disjoint exhaustive signed-word plane')
    counts={name:sum(r['pairs'] for r in rectangles if predicate(r)) for name,predicate in {
        'normal':lambda r:r['normal'], 'nonpattern':lambda r:not r['normal'],
        'new':lambda r:r['normal'] and r['x'][0]>=0x1E00}.items()}
    need(counts==dict(normal=2568421376,nonpattern=1726545920,new=963404288),'independent weighted partition')
    need({r['destination'] for r in rectangles if not r['normal']}=={0xA80,0xE59A,0xEB4C},'three actual unrelated transfers stay open')
    return rectangles,counts


def execute_one(data,source,r,x,y,rng,seed):
    cpu=Arm(data,seed,flags=((seed&15)<<28)|0xD3,rng=rng)
    actor=0x02011000;cpu.r[4]=actor
    for k in range(0xB0):cpu.put(actor+k,(k*13+0x51)&255,1)
    cpu.put(actor+0x34,x&65535,2);cpu.put(actor+0xA2,y&65535,2)
    initial=cpu.r[:15];saved={off:cpu.get(actor+off,2) for off in (0xA4,0xA6,0xA8,0xAA)}
    expected=dict(saved)
    if r['normal']:
        if r['token']==0:
            expected.update({0xA4:3,0xAA:0x1900,0xA8:min(0x1680,max(0x580,x&65535))})
        else:
            raw=0x749893+8*(r['token']-1)
            vx,vy,count=struct.unpack_from('<3H',source,raw)
            expected.update({0xA8:vx,0xAA:vy,0xA4:count})
        expected[0xA6]=rng&3
    cpu.run(0x085CC0D0,{initial[14]})
    need(cpu.r[0]==int(r['normal']),'actual acceptance/return')
    need(cpu.r[1:15]==initial[1:15],'all saved registers/SP/LR restored')
    need(cpu.rng_calls==int(r['normal']),'exactly one RNG call only for normal output')
    need({off:cpu.get(actor+off,2) for off in expected}==expected,'actual actor fields equal source normal pattern')
    actor_writes=[(at-actor,size) for at,_,size in cpu.writes if actor<=at<actor+0xB0]
    need(sorted(actor_writes)==([(0xA4,2),(0xA6,2),(0xA8,2),(0xAA,2)] if r['normal'] else []),'exact actor write set')
    need(all(actor+0xA4<=at<actor+0xAC or initial[13]-52<=at<initial[13] for at,_,_ in cpu.writes),'only exact result fields and bounded original stack')
    need(len(cpu.calls)==int(r['normal']) and all(c[1]==0x08012600 for c in cpu.calls),'only retained RNG service')


def semantics(data,source,rectangles):
    count=0
    for r in rectangles:
        for x,y,rng in itertools.product(set(r['x']),set(r['y']),range(4)):
            execute_one(data,source,r,x,y,rng,count)
            count+=1
    return count


def structure(before,after):
    need(len(before)==len(after)==0x800000,'unchanged extent')
    need(before[FIRST:LIMIT]==b'\xFF'*(LIMIT-FIRST),'full reservation FF')
    need(u32(before,HOOK)==0xAA000032,'exact old BGE done')
    word=u32(after,HOOK)
    need(word>>24==0xAA and BASE+HOOK+8+signed(word&0xFFFFFF,24)*4==BASE+FIRST,'conditional BGE tail target and no BL')
    ins=[i.mnemonic+' '+i.op_str for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(after[FIRST:FIRST+24],BASE+FIRST)]
    need(ins==['cmp r1, #0x1600','bgt #0x85cc1c0','cmp r1, #0x1500','bgt #0x85cc188','mov r1, #1','b #0x85cc150'],'actual complete stub')
    inverse=bytearray(after)
    for at,size in ((HOOK,4),(FIRST,24)):inverse[at:at+size]=before[at:at+size]
    need(inverse==before and sha(inverse)==BEFORE,'whole inverse includes every outside byte')
    need(before[0x5C9900:0x5C9B00]==after[0x5C9900:0x5C9B00]==b'\xFF'*512,'external selector remains absent')
    return ins


def verify(before,after,source,manifest):
    need(tuple(map(sha,(before,after,source)))==(BEFORE,AFTER,SOURCE),'actual immutable artifact identities')
    decoded=structure(before,after)
    fixtures=[('mirrored pointer',struct.pack('<I',0x0A000000+FIRST),0),
        ('ARM ADR',struct.pack('<I',0xE28F0000),FIRST-8),
        ('Thumb literal',struct.pack('<H',0x4800),FIRST-4),
        ('Thumb B',struct.pack('<H',0xE000),FIRST-4)]
    for label,blob,origin in fixtures:need(inbound(blob,origin),'scanner fixture: '+label)
    refs=inbound(before);need(not refs,'full strict reservation reference scan')
    need(manifest['input_sha256']==BEFORE and manifest['output_sha256']==AFTER and
        manifest['complete_controller_input_domain'] is False and manifest['external_scene_entry_authorized'] is False,'honest manifest scope')
    rectangles,counts=source_partition(source)
    # The existing native tables are independently read from the actual code.
    ytable=u32(after,0x5CC1C8)-BASE;vectors=u32(after,0x5CC1CC)-BASE
    need(after[vectors:vectors+72]==source[0x749893:0x7498DB],'all actual native vector rows match source')
    for k in range(5):
        y,n,p=struct.unpack_from('<HHI',after,ytable+k*8)
        sy,sn,sp=struct.unpack_from('<3H',source,0x7498EF+k*8)
        need((y,n)==(sy,sn) and after[p-BASE:p-BASE+n*4]==source[0x740900+sp:0x740900+sp+n*4],'actual native Y/X tables')
    cases=semantics(after,source,rectangles)
    mutations=[]
    for label,at,value in (
        ('upper boundary opens unrelated branch',FIRST,0xE3510C17),
        ('selector boundary shifted',FIRST+8,0xE3510C14),
        ('wrong vector',FIRST+16,0xE3A01002),
        ('new path removed',HOOK,0xAA000032),
        ('signed branch changed',FIRST+4,u32(after,FIRST+4)^0x80000000),
        ('zero path redirected',FIRST+12,u32(after,FIRST+20))):
        bad=bytearray(after);struct.pack_into('<I',bad,at,value)
        try:semantics(bytes(bad),source,rectangles)
        except (ValueError,IndexError):mutations.append(label)
        else:raise ValueError('semantic mutation accepted: '+label)
    bad=bytearray(after);bad[FIRST+31]=0
    try:structure(before,bytes(bad))
    except ValueError:mutations.append('outside declared write')
    else:raise ValueError('outside mutation accepted')
    return dict(status='PASS',input_sha256=BEFORE,output_sha256=AFTER,source_sha256=SOURCE,
        decoded_stub=decoded,source_rectangles=rectangles,partition_counts=counts,
        weighted_source_pairs=2**32,actual_ARM_cases=cases,negative_controls_rejected=mutations,
        actual_native_table_identity=True,register_stack_RNG_write_contract=True,
        whole_inverse=True,reservation_references=refs,scanner_fixtures=[x[0] for x in fixtures],complete_controller_input_domain=False,
        external_scene_entry_authorized=False,runtime_executed=False,
        scope='All source normal patterns, including exhausted-loop cases; unrelated source control transfers remain unresolved.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','source'):p.add_argument(key,type=Path)
    p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=verify(a.before.read_bytes(),a.after.read_bytes(),a.source.read_bytes(),json.loads(a.manifest.read_text()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('PASS',result['actual_ARM_cases'],'actual ARM cases; independent2^32 partition;',len(result['negative_controls_rejected']),'mutations')
if __name__=='__main__':main()
