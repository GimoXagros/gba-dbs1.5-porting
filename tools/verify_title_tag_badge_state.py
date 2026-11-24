"""Exercise the actual title constructor and both badge retirement hooks across saved states."""
import argparse
import json
import struct
from pathlib import Path
from verify_mode22_stats_bridge import Device,encode_snapshot,event_list,TAIL
from verify_mode23_completion_save import dump,fill,sha

PAYLOAD=0x02011900
PALETTES=0x050003a0
BACKUP=bytes((i*31+7)&255 for i in range(64))


def check(image):
    cases=0
    tests=[(r,n) for r in range(-1,11) for n in (0,9,10,99,100,998,999,1000,65535)]
    for rank,count in tests+[(None,0),(None,255),('corrupt',0),('fault',0)]:
        raw=bytearray(42)
        if isinstance(rank,int):
            for i in range(rank+1):
                struct.pack_into('<H',raw,18+i*2,i+1)
            struct.pack_into('<H',raw,40,count)
        record=encode_snapshot(raw)
        if rank is None:
            record=bytes([count])*56
        if rank=='corrupt':
            record=record[:-1]+bytes([record[-1]^0x40])
        m=Device(image,record,faults=[('read',30,1)] if rank=='fault' else [])
        fill(m,PAYLOAD,b'\xa5'*0x100)
        m.r[4]=PAYLOAD
        m.r[0]=0
        before=m.r[:15]
        m.drive(0x08090C30,{0x08090C34})
        assert m.r[:15]==before and m.get(PAYLOAD,2)==0
        assert m.events==event_list('read',range(27,31) if rank=='fault' else TAIL)
        active=rank not in ('fault','corrupt')
        assert m.get(PAYLOAD+0x28,1)==active and m.get(PAYLOAD+0x2a,1)==0
        if active:
            high=255 if rank is None or rank==-1 else rank
            assert m.get(PAYLOAD+0x29,1)==high
            assert dump(m,PAYLOAD+0x2c,3)==f'{min(count,999) if rank is not None else 0:03}'.encode()
        assert dump(m,PAYLOAD+2,0x26)==bytes([0xa5])*0x26 and dump(m,PAYLOAD+0x30,0xd0)==bytes([0xa5])*0xd0
        cases+=1
    for addr in (0x08090DB0,0x08090D34):
        for acquired in (0,1):
            fill(m,PALETTES,bytes(64))
            fill(m,PAYLOAD+0x30,BACKUP)
            m.put(PAYLOAD+0x2a,acquired,1)
            m.r[5]=PAYLOAD
            saved=m.r[:15]
            m.drive(addr,{0x08090df8})
            assert m.r[:15]==saved and m.get(PAYLOAD+0x2a,1)==0
            assert dump(m,PALETTES,64)==(BACKUP if acquired else bytes(64))
            cases+=1
    return cases


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image',type=Path)
    parser.add_argument('manifest',type=Path)
    args=parser.parse_args()
    image=args.image.read_bytes()
    meta=json.loads(args.manifest.read_bytes())
    assert sha(image)==meta['output_sha256'] and meta['whole_image_inverse']
    for row in meta['writes']:
        assert sha(image[row['offset']:row['offset']+row['size']])==row['after_sha256']
    print('PASS',check(image),'title initialization, numeric limits, bad storage and exit cases')
