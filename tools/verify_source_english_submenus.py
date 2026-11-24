"""Independently compare the source English title banks with the packaged GBA atlas."""
import argparse
import json
import struct
from pathlib import Path
from verify_character_select_name_scene import sha

SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
USA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
PREVIOUS='F61053394798E4529F45A75E8363791EC8777774681F0B7354A69966EF780E3B'
OUTPUT='8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
P0=0xE9A820
BASE=0x08000000


def decode(data,root,n,source=False):
    if source:
        assert root==0x3C43D0
        table=root+struct.unpack_from('<I',data,root)[0]
        first=struct.unpack_from('<H',data,table+2)[0]
        assert (root+first-table)==4*n
        pixels,end=0x3974C0,0x398640
    else:
        table,desc=struct.unpack_from('<II',data,root)
        table-=BASE
        length,ptr=struct.unpack_from('<II',data,desc-BASE)
        pixels,end=ptr-BASE,ptr-BASE+length
    frames=[]
    for i in range(n):
        if source:
            count,rel=struct.unpack_from('<HH',data,table+4*i);address=root+rel
        else:
            count,ptr=struct.unpack_from('<II',data,table+8*i);address=ptr-BASE
        img={}
        for j in range(count):
            tile,y,x=struct.unpack_from('<Hbb',data,address+4*j)
            raw=pixels+32*(tile&0x3fff)
            assert raw+32<=end
            for ty in range(8):
                for tx in range(8):
                    pos=(x+(7-tx if tile&0x4000 else tx),y+(7-ty if tile&0x8000 else ty))
                    a=raw+4*ty
                    if source:
                        c=sum(((data[a+plane]>>(7-tx))&1)<<plane for plane in range(4))
                    else:
                        c=data[a+tx//2]>>(4*(tx%2))&15
                    if c:img[pos]=c
        frames.append(img)
    return frames


def verify(usa,source,before,rom):
    assert tuple(map(sha,(usa,source,before,rom)))==(USA,SOURCE,PREVIOUS,OUTPUT)
    assert rom[:P0]==before[:P0] and rom[P0+5472:]==before[P0+5472:]
    expected=decode(usa,0x8fd08,5)+decode(source,0x3c43d0,11,True)[5:]
    frames=decode(rom,P0,11)
    assert frames==expected
    rows=[]
    for i,g in enumerate(frames):
        bounds=[min(x for x,y in g),min(y for x,y in g),max(x for x,y in g),max(y for x,y in g)]
        entry=dict(event=i,pixels=len(g),bounds=bounds)
        if i:
            assert bounds==[-44,-8,43,7]
            ink=[(x,y)for (x,y),c in g.items() if -28<=x<=42 and -5<=y<=5 and c in (13,14)]
            entry['ink_bounds']=[min(x for x,y in ink),min(y for x,y in ink),max(x for x,y in ink),max(y for x,y in ink)]
            entry['clear_right_columns']=42-max(x for x,y in ink)
            assert entry['clear_right_columns']>=1
        rows.append(entry)
    return dict(status='PASS',before=PREVIOUS,after=OUTPUT,usa_events=[0,1,2,3,4],
                wonder_swan_events=[5,6,7,8,9,10],events=rows,checker_sha256=sha(Path(__file__).read_bytes()))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ('usa','source','before','after','report'):
        parser.add_argument('--'+k,type=Path,required=True)
    a=parser.parse_args()
    result=verify(*(getattr(a,k).read_bytes() for k in ('usa','source','before','after')))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS',sha(a.report.read_bytes()))


if __name__=='__main__':
    main()
