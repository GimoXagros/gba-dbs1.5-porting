"""Exercise the installed cable hooks against two independent cartridge and score models."""
import argparse
import json
import struct
from pathlib import Path

from verify_mode22_stats_bridge import Device, TAIL, COMMIT, encode_snapshot, event_list
from verify_mode23_completion_save import CONFIG, dump, fill, sha

OUT, IN, ROLE, SIDE, SCORE = 0x03002168, 0x03002178, 0x03001F00, 0x03004528, 0x0300475E
SEND, ACCEPT, DISPATCH = 0x0837AB18, 0x0837AB8C, 0x08015B24
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
READS, WRITES = event_list('read', TAIL), event_list('write', COMMIT)


def sample(rows, streak=321):
    data=bytearray((n*23+9)&255 for n in range(42))
    data[12]=0
    struct.pack_into('<11HH',data,18,*rows,streak)
    return data


def highest(rows):
    return next((i for i in range(10,-1,-1) if rows[i]),65535)


def expected_trade(rows, peer, delta):
    result=rows.copy()
    if delta<0:
        rank=highest(rows)
        if rank<10:
            result[rank]-=1
    elif delta>0 and peer<10 and not rows[10] and not all(v>=9 for v in rows[peer:]):
        for i in range(peer,11):
            if result[i]<9:
                result[i]+=1
                break
            result[i]=0
    return result


def hook(image, site, record, *, side=0, role=8, peer=2, version=2, marker=0xD675,
         scores=(5,3),flags=6,faults=()):
    machine=Device(image,record,faults=faults)
    machine.r[5]=CONFIG
    machine.cpsr=flags<<28|31
    fill(machine,CONFIG,bytes(range(64)))
    machine.put(CONFIG+0x25,version,1)
    machine.put(ROLE,role,1)
    machine.put(SIDE,side,1)
    fill(machine,SCORE,bytes(scores))
    fill(machine,OUT,bytes(range(48)))
    selected=IN+(16 if role==8 else 0)
    machine.put(selected+6,peer,2)
    machine.put(selected+8,marker,2)
    comm=dump(machine,OUT,48)
    before=bytes(machine.blocks)
    registers=machine.r[:15]
    machine.drive(site,{site+4})
    if site==SEND:
        registers[8]=0x82
    elif site==ACCEPT:
        registers[0]=0
    elif flags&4:
        registers[0]=4
    assert machine.r[:15]==registers and machine.cpsr==(flags<<28|31)
    assert bytes(machine.blocks[:216])==before[:216] and bytes(machine.blocks[272:])==before[272:]
    after=dump(machine,OUT,48)
    if site==SEND and not version&1:
        assert after[:6]==comm[:6] and after[10:]==comm[10:]
    else:
        assert after==comm
    return bytes(machine.blocks[216:272]),machine.events,struct.unpack_from('<HH',after,6)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','prior','image','owner','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    source,prior,image,raw=[p.read_bytes() for p in (args.source,args.prior,args.image,args.owner)]
    manifest=json.loads(raw)
    assert sha(source)==SOURCE and sha(prior)==manifest['input_sha256'] and sha(image)==manifest['output_sha256']
    assert source[0x785136:0x785144]==bytes.fromhex('3ac2723e7708c74423ffffe96300')
    assert prior[0x37ab1c:0x37ab8c]==image[0x37ab1c:0x37ab8c] and prior[0x15b08:0x15b24]==image[0x15b08:0x15b24]
    shapes=[[0]*11,[9]*10+[0],[0]*10+[1],[1,0,9,9,9,9,0,0,0,0,0]]
    shapes += [[int(i==rank) for i in range(11)] for rank in range(10)]
    send=accept=dispatch=0
    for i,rows in enumerate(shapes):
        orig=encode_snapshot(sample(rows))
        for flags in range(16):
            after,events,packet=hook(image,SEND,orig,flags=flags)
            assert (after,events,packet)==(orig,READS,(highest(rows),0xD675))
            send+=1
        for side,role in ((0,8),(1,0)):
            for left,right in ((0,255),(128,127),(200,200)):
                local,remote=(left,right) if not side else (right,left)
                for peer in (0,2,5,9,10,65535):
                    target=expected_trade(rows,peer,local-remote)
                    final,events,_=hook(image,ACCEPT,orig,side=side,role=role,peer=peer,scores=(left,right),flags=accept%16)
                    wanted=encode_snapshot(sample(target))
                    assert final==wanted and events==([] if left==right else READS+(WRITES if wanted!=orig else []))
                    accept+=1
    rows=shapes[-1]
    for side in (0,1):
        for left,right in ((0,255),(128,127),(7,7)):
            local,remote=(left,right) if not side else (right,left)
            for n in (0,1,998,999,1000,65535):
                current=encode_snapshot(sample(rows,n))
                wanted=min(999,(n+1)&65535) if local>remote else 0
                after,events,_=hook(image,DISPATCH,current,side=side,scores=(left,right),flags=(dispatch%16)|4)
                assert after==encode_snapshot(sample(rows,wanted)) and events==READS+WRITES
                dispatch+=1
    current=encode_snapshot(sample(rows))
    for version in (1,3,255):
        for site in (SEND,ACCEPT,DISPATCH):
            data,events,_=hook(image,site,current,version=version)
            assert data==current and not events
    for marker in (0,0xFFFF,0xD674):
        data,events,_=hook(image,ACCEPT,current,marker=marker)
        assert data==current and not events
    for blank in (0,255):
        record=bytes([blank])*56
        assert hook(image,SEND,record)[:2]==(record,READS)
        assert hook(image,SEND,record)[2]==(65535,0xD675)
        expected=bytearray(42);expected[22]=1
        assert hook(image,ACCEPT,record)[:2]==(encode_snapshot(expected),READS+WRITES)
    corrupt=bytearray(current);corrupt[-1]^=1
    for site in (SEND,ACCEPT,DISPATCH):
        assert hook(image,site,corrupt)[:2]==(corrupt,READS)
        for i,block in enumerate(TAIL):
            after,ops,_=hook(image,site,current,faults=[('read',block,1)])
            assert after==current and ops==READS[:i+1]
    for site in (ACCEPT,DISPATCH):
        expected=hook(image,site,current)[0]
        for i,block in enumerate(COMMIT):
            partial=bytearray(current)
            for blk in COMMIT[:i]:
                start=(blk-27)*8
                partial[start:start+8]=expected[start:start+8]
            after,events,_=hook(image,site,current,faults=[('write',block,1)])
            assert after==partial and events==READS+WRITES[:i+1]
    for mode,rematch,stop,mode_after in ((0,0,0x08015B40,None),(1,0x1000,0x08015B28,6)):
        vm=Device(image,current);vm.r[5]=CONFIG
        vm.put(CONFIG+2,mode,2);vm.put(CONFIG+26,rematch,2)
        vm.drive(0x08015B08,{stop})
        assert vm.events==[] and (mode_after is None or vm.r[0]==mode_after)
    for role in (0,8):
        vm=Device(image,current);vm.put(ROLE,role,1)
        vm.r[0]=0
        at=IN+(16 if role==8 else 0)
        fill(vm,at,struct.pack('<HBBHHH',0x82,1,3,999,2,0xD675))
        vm.drive(0x0837AB34,{0x0837AB98})
        assert not vm.events
    report=dict(status='NATIVE_LINK_TAG_AND_STREAK_PASS',input_sha256=sha(prior),image_sha256=sha(image),
                source_sha256=SOURCE,checker_sha256=sha(Path(__file__).read_bytes()),send=send,receive=accept,
                streak=dispatch,blank=2,legacy=9,unmarked=3,failed_reads=21,failed_writes=14,corrupted=3,
                original_singleplayer_and_rematch=2,bad_peer_score_sum=2)
    with args.report.open('x',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(args.report.read_bytes()))


if __name__=='__main__':
    main()
