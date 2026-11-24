"""Exercise all five installed VS RECORD pages at the portrait/digit-render boundaries."""
import argparse
import json
import struct
from pathlib import Path

from verify_mode22_stats_bridge import Device, encode_snapshot, event_list, TAIL, snapshot
from verify_mode23_completion_save import BUFFER, CONFIG, fill, dump, sha

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
IMAGE = 'F824434CBEE46F3BBFE59DF95038B618C2F534274CC44A59B0FB0B9C477E599B'
TASK = 0x02010000
STATE = TASK+0x18
ACTIVE = 0x0300133c
KEY = 0x03001306
PORTRAITS = 0x084a80f8
ROWS = (0,1,2,3,4,5,6,7,8,9,10,13,14,11,12)


class Scene(Device):
    def __init__(self,image,record,**args):
        super().__init__(image,record,**args)
        fill(self,TASK-16,b'\x5a'*(0x118+32))
        self.put(ACTIVE,TASK)
        self.put(KEY,0,2)
        self.r[4] = STATE
        self.r[8] = 0
        self.portraits = []
        self.digits = []
        self.masks = []
        self.services.update({0x080127e4:self.portrait,0x080132ec:lambda _:None,
            0x08012874:lambda _:None,0x0833fc0c:lambda _:self.masks.append(self.r[8]),
            0x0833f9f8:self.digit,0x0801e8c4:lambda _:None,0x0837db3c:self.divide})

    def portrait(self, _):
        sp = self.r[13]
        triple = tuple(self.get(sp+n) for n in (28,40,16))
        for offset,val in zip((28,40,16),triple):
            assert self.get(sp+offset+4)==self.get(sp+offset+8)==val
        assert self.get(sp+52)==self.get(sp+56)
        self.portraits.append((self.get(sp+52),triple))

    def digit(self, _):
        sp = self.r[13]
        self.digits.append(tuple(self.get(sp+i) for i in (0,4,8,12)))

    def divide(self, _):
        assert self.r[1] > 0
        self.r[0] //= self.r[1]

    def run(self, start, stops, max_steps=22000):
        multiply={0x0833f448,0x0833f59c,0x0833f6f0}
        pc=start
        while True:
            pc=super().run(pc,set(stops)|multiply,max_steps)
            if pc in stops:
                return pc
            assert self.get(pc)==0xe0000093
            self.r[0]=(self.r[3]*self.r[0])&0xffffffff
            pc+=4

    def capture(self):
        old = dump(self,TASK-16,0x118+32)
        regs=self.r[:15]
        self.drive(0x0833ec90,{0x0833ec94})
        assert self.r[:15]==regs
        after=dump(self,TASK-16,0x118+32)
        for index,(a,b) in enumerate(zip(old,after)):
            if index not in {0x10+0x1a,0x10+0x1b} and not 0x10+0x10c<=index<0x10+0x118:
                assert a==b
        return dump(self,STATE+0xf4,12)


def record_data():
    payload = snapshot()
    for fighter in (12,13,14):
        struct.pack_into('<HH',payload,4*(fighter-12),fighter+1,fighter+30)
    return encode_snapshot(payload)


def page(image,start,unlocked):
    vm=Scene(image,record_data())
    expected_cache=vm.blocks[224:236]
    assert vm.capture()==expected_cache and vm.events==event_list('read',TAIL)
    for fighter in range(12):
        fill(vm,BUFFER+0x8e+4*fighter,struct.pack('<HH',fighter+1,fighter+30))
    vm.put(STATE,start,2)
    vm.put(CONFIG+0x19,unlocked,1)
    ids=ROWS[start:start+3]
    vm.drive(0x0833ee30,{vm.r[14]})
    assert vm.portraits==[(STATE+4+0x50*i,tuple(vm.get(PORTRAITS+32*f+j) for j in (0,4,8))) for i,f in enumerate(ids)]
    assert vm.masks==[0x05000200+32*i for i,f in enumerate(ids) if f in (11,12) and not unlocked&(1<<(f-7))]
    vm.drive(0x0833f31c,{0x0833f764})
    expected=[]
    for i,f in enumerate(ids):
        y=5+i*5
        expected.extend(((3,f+1,y,14),(3,f+30,y,20),(2,(f+1)*100//(f+30),y,8)))
    assert vm.digits==expected
    assert vm.events==event_list('read',TAIL)
    assert dump(vm,STATE+0xf4,12)==expected_cache
    assert dump(vm,TASK+0x118,16)==b'\x5a'*16
    vm.drive(0x0833f904,{0x0833f918,0x0833f930})
    assert vm.get(STATE,2)==start+3
    target=0x0833f930 if start==12 else 0x0833f918
    assert vm.r[15]==(0x0833f914+8)
    # Consume the actual bound comparison a second time with fresh flags.
    assert vm.drive(0x0833f910,{0x0833f918,0x0833f930})==target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','image','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    source,image=args.source.read_bytes(),args.image.read_bytes()
    assert sha(source)==SOURCE and sha(image)==IMAGE
    assert struct.unpack_from('<16H',source,0x76cf4e)==(*ROWS,0xffff)
    assert source[0x76cef6:0x76cefc]==bytes.fromhex('bbae1a2e8b07')
    assert source[0x76d35f:0x76d362]==bytes.fromhex('bbba39')
    for start in (0,3,6,9,12):
        for flags in (0,0x10,0x20,0x30):
            page(image,start,flags)
    bad=bytearray(record_data());bad[22]^=1
    failures=[(bytes(56),()),(b'\xff'*56,()),(bad,())]
    failures += [(record_data(),[('read',block,1)]) for block in TAIL]
    for record,faults in failures:
        vm=Scene(image,record,faults=faults)
        before=bytes(vm.blocks)
        assert vm.capture()==bytes(12)
        assert bytes(vm.blocks)==before
    report=dict(status='VS_RECORD_FIVE_SOURCE_PAGES_ARM_PASS',source_sha256=SOURCE,image_sha256=IMAGE,
                checker_sha256=sha(Path(__file__).read_bytes()),source_order=ROWS,page_and_mask_cases=20,
                safe_empty_or_io_cases=len(failures),private_task_range=[0x10c,0x118],
                evidence='Installed source page IDs, constructor parameter triples, lock palette calls, nine numeric arguments per page, page end and no EEPROM writes.',
                limits='Digit/portrait and hardware services intercepted at native call boundaries. Visual/timing qualification is separate.')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(args.report.read_bytes()))


if __name__=='__main__':
    main()
