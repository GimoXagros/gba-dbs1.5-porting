"""Execute the cable award latch, normal/rematch dispatcher, empty constructor and retirement."""
import argparse
import json
import struct
from pathlib import Path

from verify_link_tag_result import (Device, CONFIG, IN, OUT, ROLE, SIDE, SCORE, ACCEPT, DISPATCH,
                                    READS, WRITES, encode_snapshot, sample, dump, fill, highest)
from verify_mode23_completion_save import sha

BASE=0x08000000
PTRS=(0x15B70,0x15B74,0x15B78,0x15C6C,0x15CC8)


def latch(image,rows,peer,local_score,remote_score,side,*,old=False,marker=0xD675,fault=()):
    record=encode_snapshot(sample(rows))
    m=Device(image,record,faults=fault)
    role=0 if side else 8
    m.put(CONFIG+0x25,int(old),1);m.put(ROLE,role,1);m.put(SIDE,side,1)
    fill(m,SCORE,bytes((remote_score,local_score) if side else (local_score,remote_score)))
    m.put(OUT+6,highest(rows),2);m.put(OUT+8,0xD675,2);m.put(OUT+10,0xEEE1,2)
    selected=IN+(0 if side else 16)
    m.put(selected+6,peer,2);m.put(selected+8,marker,2)
    regs=m.r[:15];regs[0]=0;flags=m.cpsr=0xb000001f
    m.drive(ACCEPT,{ACCEPT+4})
    assert m.r[:15]==regs and m.cpsr==flags
    return m.get(OUT+10,2),bytes(m.blocks[216:272]),m.events


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','image','owner','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    before,image,raw=[f.read_bytes()for f in (a.before,a.image,a.owner)]
    info=json.loads(raw);assert sha(image)==info['output_sha256'] and sha(before)==info['input_sha256']
    at=info['table']-BASE
    previous=before[0xdb4400:0xdb4400+528]
    assert image[at:at+288]==previous[:288] and image[at+300:at+396]==previous[288:384]
    assert image[at+400:at+544]==previous[384:] and image[at+544:at+550]==bytes((4,0,0,0,0,0))
    assert struct.unpack_from('<3I',image,at+288)==(info['symbols']['m24_init'],info['symbols']['m24_create'],0x080159b0)
    assert struct.unpack_from('<I',image,at+396)[0]==0x08015b40
    assert [struct.unpack_from('<I',image,t)[0] for t in PTRS]==[BASE+at+i for i in (0,4,8,300,400)]
    rows=[0]*11;rows[2]=3
    tests=0
    for side in (0,1):
        for counts in (rows,[0]*11,[9]*10+[0],[0]*10+[1]):
            for peer in (0,4,9,10,65535):
                for local,remote in ((0,255),(0,0),(128,127)):
                    rank=highest(counts)
                    token,new,events=latch(image,counts,peer,local,remote,side)
                    if local>remote and peer<10 and not counts[10]:
                        want=0x8000|peer
                    elif local<remote and rank<10:
                        want=rank
                    else:
                        want=65535
                    assert token==want and events==([] if local==remote else READS+(WRITES if want!=65535 else []))
                    assert (new!=encode_snapshot(sample(counts)))==(want!=65535)
                    tests+=1
        for marker in (0,0xD674):
            assert latch(image,rows,0,1,0,side,marker=marker)==(65535,encode_snapshot(sample(rows)),[])
        assert latch(image,rows,0,1,0,side,old=True)==(0xeee1,encode_snapshot(sample(rows)),[])
        for kind,blocks in (('read',range(27,34)),('write',(28,29,30,31,32,33,27))):
            for n in blocks:
                v,_,ops=latch(image,rows,0,1,0,side,fault=[(kind,n,1)])
                assert v==65535 and ops[-1]==(kind,n)
    record=encode_snapshot(sample(rows))
    transitions=0
    for version in (1,2,3):
        for selection in (0,1):
            for flags in (0,0x1000):
                m=Device(image,record);m.r[5]=CONFIG
                m.put(SIDE,0,1);fill(m,SCORE,bytes((1,0)))
                m.put(CONFIG+0x25,version,1);m.put(CONFIG+2,selection,2);m.put(CONFIG+26,flags,2)
                pc=m.drive(0x08015b08,{0x08015b28,0x08015b40})
                if not selection:assert pc==0x08015b40
                else:assert pc==0x08015b28 and m.r[0]==(6 if flags else 4 if version&1 else 24)
                assert bool(m.events)==bool(selection and not flags and not (version&1))
                transitions+=1
    for token,marker in ((0xffff,0xD675),(11,0xD675),(0x800a,0)):
        m=Device(image,record);m.put(OUT+10,token,2);m.put(OUT+8,marker,2)
        regs=m.r[:15];m.drive(info['symbols']['m24_init'],{regs[14]})
        assert m.r[:3]==[0,regs[1],1] and m.r[3:15]==regs[3:15]
        m.drive(info['symbols']['m24_create'],{regs[14]})
        assert m.get(CONFIG+4,2)==1 and m.get(CONFIG+6,4)==0 and not m.events
    report=dict(status='NATIVE_MODE24_TABLE_LATCH_CARRY_PASS',image_sha256=sha(image),input_sha256=sha(before),
                checker_sha256=sha(Path(__file__).read_bytes()),accepted_exchange_cases=tests,original_tables=24,
                transition_cases=transitions,empty_constructor_cases=3,legacy_and_marker_cases=6,device_errors=28)
    with a.report.open('x',encoding='utf8',newline='\n') as dest:dest.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
