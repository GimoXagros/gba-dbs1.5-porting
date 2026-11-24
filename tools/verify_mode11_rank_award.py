"""Independent installed ARM, native score consumer, physical layout and 1.5 branch tests."""
import argparse
import bisect
import json
import struct
from pathlib import Path

from verify_mode22_stats_bridge import Device, encode_snapshot, event_list, TAIL, COMMIT
from verify_mode23_completion_save import CONFIG, dump, fill, sha

PRIOR='476E753BC09D8EB3B39F2CB0F6734241233EE7080B4E901AB57C20B603327D08'
IMAGE='78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOK, AFTER, SCORE=0x080c0d14,0x080c0d18,0x03003d02
TOKEN=0x8dd0c24


def as_record(rows,seed=7):
    data=bytearray((n*31+seed)&255 for n in range(42))
    data[12]=0
    struct.pack_into('<11H',data,18,*rows)
    return data


def result_model(rows,rank):
    v=rows.copy()
    if rows[10] or all(n>=9 for n in rows[rank:]):
        return 0xffff,v
    for index in range(rank,11):
        v[index]=(v[index]+1)&0xffff
        if v[index]<10:break
        v[index]=0 if index<10 else 9
    return 0x8000|rank,v


def execute(image, difficulty, score, record, fault=(), flags=0):
    vm=Device(image,record,faults=fault)
    fill(vm,CONFIG,bytes(range(64)))
    vm.put(CONFIG+15,difficulty,1)
    vm.put(SCORE,score,2)
    before=bytes(vm.blocks)
    config=dump(vm,CONFIG,64)
    regs=vm.r[:15]
    vm.cpsr=flags<<28|0x1f
    vm.drive(HOOK,{TOKEN})
    result=vm.r[0]
    vm.drive(TOKEN,{AFTER})
    regs[8]=0x03004528
    assert vm.r[:15]==regs and vm.cpsr==flags<<28|0x1f
    assert dump(vm,CONFIG,64)==config
    assert vm.blocks[:216]==before[:216] and vm.blocks[272:]==before[272:]
    return result,bytes(vm.blocks[216:272]),vm.events


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('source','prior','image','report'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    s,b,rom=(f.read_bytes()for f in (a.source,a.prior,a.image))
    assert (sha(s),sha(b),sha(rom))==(SOURCE,PRIOR,IMAGE)
    assert s[0x77b106:0x77b110]==bytes.fromhex('9a28078f849af80fd373')
    assert s[0x77a5d3:0x77a5e3]==bytes.fromhex('268b57212bd133c02689472126895726')
    assert struct.unpack_from('<6I',b,0xbfdbc)==(0xe1d132b2,0xe0533002,0xe0500000,0xe1c102b2,0xe59f40b8,0xe1c430b0)
    assert b[0xc0c70:0xc0d14]==rom[0xc0c70:0xc0d14] and b[0xc0d18:0xc0ee0]==rom[0xc0d18:0xc0ee0]
    assert b[0xc05e4:0xc0678]==rom[0xc05e4:0xc0678] and b[0xc06a8:0xc07f4]==rom[0xc06a8:0xc07f4]
    limits=struct.unpack_from('<44H',s,0x785092)
    reads=event_list('read',TAIL);writes=event_list('write',COMMIT);cases=0
    for difficulty in range(4):
        cuts=limits[difficulty*11:difficulty*11+11]
        for score in sorted({0,2310,65535}|{v for t in cuts for v in (t-1,t,t+1)if 0<=v<=65535}):
            for rows in ([0]*11,[9]*10+[0],[0]*10+[1]):
                old=as_record(rows)
                expected,new=result_model(rows,bisect.bisect_left(cuts,score))
                actual,after,ops=execute(rom,difficulty,score,encode_snapshot(old),flags=cases%16)
                assert actual==expected and after==encode_snapshot(as_record(new))
                assert ops==reads+(writes if expected!=65535 else [])
                cases+=1
    for blank in (0,255):
        token,record,ops=execute(rom,2,2310,bytes([blank])*56)
        new=bytearray(42);new[38]=1
        assert token==0x800a and record==encode_snapshot(new) and ops==reads+writes
    for difficulty in (4,127,255):
        old=encode_snapshot(as_record([0]*11))
        assert execute(rom,difficulty,4,old)==(0xffff,old,[])
    baseline=encode_snapshot(as_record([0]*11))
    for offset in (0,12,19,51,54):
        corrupt=bytearray(baseline);corrupt[offset]^=1
        assert execute(rom,0,3,corrupt)==(0xffff,corrupt,reads)
    for block in TAIL:
        assert execute(rom,2,2310,baseline,[('read',block,1)])==(0xffff,baseline,reads[:block-26])
    desired=encode_snapshot(as_record([0]*10+[1]))
    for i,block in enumerate(COMMIT):
        incomplete=bytearray(baseline)
        for blk in COMMIT[:i]:
            o=8*(blk-27);incomplete[o:o+8]=desired[o:o+8]
        assert execute(rom,2,2310,baseline,[('write',block,1)])==(0xffff,incomplete,reads+writes[:i+1])
    report=dict(status='MODE11_SOURCE_TAG_AWARD_PERSIST_PASS',image_sha256=IMAGE,source_sha256=SOURCE,prior_sha256=PRIOR,
        checker_sha256=sha(Path(__file__).read_bytes()),rank_and_carry_cases=cases,
        blank_cases=2,outside_difficulty=3,corruption_cases=5,device_failures=14,source_issuer=0x77b106,
        native_positive_countdown=HOOK,corrected_score_native=SCORE,
        limits='EEPROM read/write modeled here. Native restored sibling path CC7/C06A8 does not award. Score-card and optional rank-card UI require a separate layer.')
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()),cases)


if __name__=='__main__':main()
