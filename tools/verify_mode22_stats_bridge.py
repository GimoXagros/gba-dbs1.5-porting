"""Execute the installed stat/reset hooks and native EEPROM serializer against a block fixture."""
import argparse
import json
import struct
import zlib
from pathlib import Path

from verify_mode23_completion_save import BUFFER, CONFIG, dump, fill, need, sha
from verify_mode23_eligibility_storage import EEPROMFixture, MARKER, READ, WRITE, RECORD_INIT

BASE = 0x08000000
PRIOR = '63D7B68138CF7C1EBD96CEE168E1AFCD414A7591EDD9FBD8329A7E64C96F6248'
INSTALLED = '3CB82DEC80C68FF85199A5BD264D78F3C794A6C522539731550B1A797A06A74C'
PREVIOUS_ROM = '8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
PREFIX = list(range(25))
TAIL = list(range(27, 34))
COMMIT = [28, 29, 30, 31, 32, 33, 27]
SCORES, SIDE = 0x0300475E, 0x03004528
STATS_CALL, STATS_RETURN = 0x0808B3E0, 0x0808B3E4


def encode_snapshot(data):
    assert len(data) == 42 and data[12] == 0
    body = data + bytes(2)
    return b'BS15TAG\1' + body + struct.pack('<I', zlib.crc32(body))


def snapshot(fighter=12, wins=1, total=7):
    data = bytearray((index*29+5)&255 for index in range(42))
    data[12] = 0
    struct.pack_into('<HH', data, 4*(fighter-12), wins, total)
    return data


class Device(EEPROMFixture):
    # Indexed halfword operations used in the unchanged USA stat path.
    indexed = {0x0833ed98: (True, 0xe19490b8), 0x0833edac: (False, 0xe18490b8),
               0x0833ede8: (True, 0xe19490b8), 0x0833edf0: (False, 0xe18490b8)}

    def __init__(self, image, record, *, faults=()):
        super().__init__(image, MARKER)
        self.blocks[216:272] = record
        self.faults = set(faults)
        self.counts = {}
        self.events = []
        self.services = {}
        fill(self, BUFFER+200, bytes(range(24)))  # detect overflow into native checksum/trailer
        self.start_sp = self.r[13]

    def device(self, direction):
        block, ptr = self.r[:2]
        assert block in (*PREFIX,26,*TAIL) and ptr % 2 == 0
        in_stack = self.start_sp - 512 <= ptr <= self.start_sp - 8
        if block < 25:
            assert ptr == BUFFER+block*8 or (direction == 'read' and in_stack)
        elif block == 26:
            assert direction == 'write' and dump(self,ptr,8) == bytes(8)
        elif block == 27 and direction == 'write':
            assert BASE <= ptr < 0x09000000 and dump(self,ptr,8) == b'BS15TAG\1'
        else:
            assert in_stack
        event = (direction,block)
        self.counts[event] = self.counts.get(event,0) + 1
        failed = (*event, self.counts[event]) in self.faults
        self.events.append(event)
        lo = block*8
        if not failed:
            if direction == 'read':
                fill(self,ptr,self.blocks[lo:lo+8])
            else:
                self.blocks[lo:lo+8] = dump(self,ptr,8)
        self.r[0] = 0x8000 if failed else 0
        for reg in (1,2,3,12):
            self.r[reg] = 0x7c00+reg

    def run(self, start, stops, max_steps=22000):
        pc = start
        while True:
            pc = super().run(pc, set(stops)|self.indexed.keys(), max_steps)
            if pc in stops:
                return pc
            load, word = self.indexed[pc]
            assert self.get(pc) == word
            address = self.r[4] + self.r[8]
            if load:
                self.r[9] = self.get(address,2)
            else:
                self.put(address,self.r[9],2,True)
            pc += 4


def event_list(direction, blocks):
    return [(direction,n) for n in blocks]


def play(device, fighter, side, score, *, prefix_stats=(0,7)):
    put = device.put
    put(CONFIG+0xa, fighter if not side else 14, 1)
    put(CONFIG+0xc, fighter if side else 14, 1)
    put(SIDE,side,1)
    fill(device,SCORES,bytes(score))
    if fighter < 12:
        fill(device, BUFFER+0x8e+fighter*4, struct.pack('<HH',*prefix_stats))
    regs = device.r[:]
    device.drive(STATS_CALL, {STATS_RETURN})
    assert device.r[:6] == regs[:6] and device.r[13:15] == [regs[13],STATS_RETURN]
    return bytes(device.blocks)


def native_rows(prior, image):
    record = encode_snapshot(snapshot())
    tested = 0
    for fighter in range(12):
        for side,score,pair in ((0,(3,1),(1,5)),(1,(1,3),(1,998)),(0,(1,2),(3,21)),
                                (1,(2,2),(7,999))):
            original, changed = Device(prior, record), Device(image, record)
            old = play(original,fighter,side,score,prefix_stats=pair)
            new = play(changed,fighter,side,score,prefix_stats=pair)
            assert new == old and changed.events == original.events
            assert dump(original,BUFFER,224) == dump(changed,BUFFER,224)
            assert all(b<25 for _,b in changed.events)
            tested += 1
    return tested


def extended_rows(image):
    tested = 0
    reads = event_list('read',TAIL)
    writes = event_list('write',COMMIT+PREFIX)
    for fighter in (12,13,14):
        for side in (0,1):
            for left,right in ((3,0),(0,3),(2,2)):
                for total in (0,998,999,65535):
                    wins = 65535 if total == 998 else 1
                    row = snapshot(fighter,wins,total)
                    device = Device(image, encode_snapshot(row))
                    before = bytes(device.blocks)
                    local = (left,right) if not side else (right,left)
                    actual = play(device,fighter,side,(left,right))
                    if total < 999:
                        struct.pack_into('<HH', row, (fighter-12)*4, (wins+(local[0]>local[1]))&65535,total+1)
                    assert device.events == reads+(writes if total<999 else [])
                    assert actual[216:272] == encode_snapshot(row)
                    assert actual[200:216] == before[200:216] and actual[272:] == before[272:]
                    assert actual[0x8e:0xc0] == before[0x8e:0xc0]
                    assert dump(device,BUFFER+200,24) == bytes(range(24))
                    tested += 1
    for blank in (0,255):
        device = Device(image,bytes([blank])*56)
        actual = play(device,14,1,(0,1))
        data = bytearray(42)
        struct.pack_into('<HH',data,8,1,1)
        assert actual[216:272] == encode_snapshot(data)
    return tested+2


def failures(image):
    row = snapshot()
    tag = encode_snapshot(row)
    tests = 0
    for at in (0,7,8,20,49,51,52,55):
        record = bytearray(tag)
        record[at] ^= 1
        device = Device(image,record)
        before = bytes(device.blocks)
        assert play(device,12,0,(2,1)) == before and device.events == event_list('read',TAIL)
        tests += 1
    for block in TAIL:
        device = Device(image,tag,faults=[('read',block,1)])
        before = bytes(device.blocks)
        assert play(device,12,0,(2,1)) == before
        assert device.events == event_list('read',list(range(27,block+1)))
        tests += 1
    changed_body = bytearray(row)
    struct.pack_into('<HH',changed_body,0,2,8)
    changed_tag = encode_snapshot(changed_body)
    for i,block in enumerate(COMMIT):
        device = Device(image,tag,faults=[('write',block,1)])
        expected = bytearray(device.blocks)
        for b in COMMIT[:i]:
            o = (b-27)*8
            expected[b*8:b*8+8] = changed_tag[o:o+8]
        assert play(device,12,0,(2,1)) == expected
        assert device.events == event_list('read',TAIL)+event_list('write',COMMIT[:i+1])
        tests += 1
    for invalid in (15,127,128,255):
        for side in (0,1):
            device = Device(image,tag)
            before = bytes(device.blocks)
            assert play(device,invalid,side,(2,1)) == before and not device.events
            tests += 1
    return tests


def resets(prior, image):
    record = encode_snapshot(snapshot())
    tested = 0
    scenarios = [
        ('load',0,(),False), ('explicit',1,(),True), ('bad-signature',0,(),True),
        ('bad-checksum',0,(),True), ('transient-io',0,(('read',0,1),),False),
        ('recheck-io',0,(('read',0,2),),False),
        ('corrupt-tail-no-reset',0,(),False), ('explicit-corrupt-tail',1,(),True),
    ]
    for label, arg, faults, reset in scenarios:
        m = Device(image,record,faults=faults)
        control = Device(prior,record)
        for vm in (m,control):
            vm.put(vm.r[13],arg)
            if label == 'bad-signature':
                vm.blocks[0] ^= 1
                struct.pack_into('<I',vm.blocks,0xc0,sum(vm.blocks[:0xc0]))
            if label in ('bad-checksum','recheck-io'):
                vm.blocks[0xc0] ^= 1
            if 'corrupt-tail' in label:
                vm.blocks[217] ^= 1
            if label == 'transient-io':
                fill(vm,BUFFER,bytes(200))
        before = bytes(m.blocks)
        m.drive(RECORD_INIT,{m.r[14]})
        assert m.r[13] == m.start_sp
        if reset:
            control.drive(RECORD_INIT,{control.r[14]})
            assert bytes(m.blocks[:200]) == bytes(control.blocks[:200])
            assert m.blocks[208:272] == bytes(8)+encode_snapshot(bytes(42))
            assert [b for d,b in m.events if d=='write'] == COMMIT+[26]+PREFIX
        else:
            assert bytes(m.blocks) == before
            assert all(d=='read' for d,b in m.events)
        assert before[200:208] == m.blocks[200:208] and before[272:] == m.blocks[272:]
        tested += 1
    for i,block in enumerate(COMMIT+[26]+PREFIX):
        m = Device(image,record,faults=[('write',block,1)])
        before = bytes(m.blocks)
        m.put(m.r[13],1)
        m.drive(RECORD_INIT,{m.r[14]})
        assert [b for d,b in m.events if d=='write'] == (COMMIT+[26]+PREFIX)[:i+1]
        assert before[200:208] == m.blocks[200:208] and before[272:] == m.blocks[272:]
        if block >= 26:
            assert before[:200] == m.blocks[:200]
        tested += 1
    return tested


def census(image):
    targets = {0x0801F894:[0x15940,0xc35d4],0x0801fca8:[0x1fc08],0x0837db60:[0x1fcc0,0x629828,0x629850],
               0x0837db54:[0x1fc7c,0x629844,0x62986c],0x0833ed64:[0x8b3e0],0x08d8d290:[0x1f9c4]}
    arm = {t:[] for t in targets}
    thumb = {t:[] for t in (0x0837D7E4,0x0837D894,0x0837D970,0x0837D9C8)}
    for index,(word,) in enumerate(struct.iter_unpack('<I',image)):
        if word & 0x0e000000 == 0x0a000000:
            dest = BASE+index*4+8+4*((word&0x7fffff)-(word&0x800000))
            if dest in arm:
                arm[dest].append(index*4)
    halves = memoryview(image).cast('H')
    for i,first in enumerate(halves[:-1]):
        second = halves[i+1]
        if first&0xf800 == 0xf000 and second&0xf800 == 0xf800:
            dest = BASE+i*2+4+4096*((first&0x3ff)-(first&0x400))+2*(second&0x7ff)
            if dest in thumb:
                thumb[dest].append(i*2)
    assert arm == targets and list(thumb.values()) == [[0x37d998],[0x37d9e2],[0x37d9f2],[]]
    literals = {0x0837DB60:0xd8d2e4,0x0837DB54:0xd8d2dc,0x0837d7e5:0x37db68,0x0837d9c9:0x37db5c}
    for target in set(targets)|set(thumb)|{t+1 for t in set(targets)|set(thumb)}:
        n = struct.pack('<I',target)
        assert image.find(n) == image.rfind(n) == literals.get(target,-1)
    assert struct.unpack_from('<IHHB',image,0x3877d0) == (512,64,0x300,6)
    return dict(ARM=arm, Thumb=thumb, literals=literals, EEPROM_blocks=64)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','prior','image','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    baseline, prior, image = a.baseline.read_bytes(), a.prior.read_bytes(), a.image.read_bytes()
    assert sha(baseline)==PREVIOUS_ROM and sha(prior)==PRIOR and sha(image)==INSTALLED
    owners = census(baseline)
    counts = dict(native_rows=native_rows(prior,image), extended_rows=extended_rows(image),
                  bad_data_and_io=failures(image), reset=resets(prior,image))
    report = dict(status='MODE22_NATIVE_STAT_RESET_BRIDGE_PASS', sha256=sha(image), baseline=sha(baseline),
                  prior=sha(prior), checker_sha256=sha(Path(__file__).read_bytes()), census=owners, cases=counts,
                  limitations=['Direct encoded control flow and address literal census only.',
                  'Actual installed ARM from 0808B3E0 and 0801F894, block device and sorter DMA modeled.',
                  'Multi-block updates and prefix commits are not power-loss atomic; device writes include readback.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()),counts)


if __name__ == '__main__':
    main()
