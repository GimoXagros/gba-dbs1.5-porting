"""Verify every score tick and the retained native song-specific stop contract."""
import argparse
import json
import struct
from pathlib import Path

from verify_mode23_scene_component import empty,sha

BASE=0x08000000
HOOK=0x08ea4840
ORIGINAL='9A8D51B08310376C093013D952FC7A02973134F3FE338C1718AF009B4B692B2D'
IMAGE='39D0EEBF4793CAB110DCF51D6C5F29C076039EEC9D78F95BE16096AC5A32D979'
OWNER='A41428915AC1241000B31176086FB0A20B647B9216749BBB7DEF184E2889F116'


def check(before,after,manifest):
    assert (sha(before),sha(after),sha(manifest))==(ORIGINAL,IMAGE,OWNER)
    owner=json.loads(manifest)
    inverse=bytearray(after)
    for x in owner['writes']:
        at,n=x['offset'],x['size']
        assert sha(before[at:at+n])==x['before_sha256'] and sha(after[at:at+n])==x['after_sha256']
        if at!=HOOK-BASE:
            assert before[at:at+n]==b'\xff'*n and all(at+n<=a or b<=at for a,b in owner['prior_excluded_extents'])
        inverse[at:at+n]=before[at:at+n]
    assert inverse==before
    vm=empty(after)
    sym=owner['symbols']
    bx=sym['m11_reel_stopped']-4
    assert vm.get(bx)==0xe12fff13
    ops=[]
    for tick in range(1,711):
        vm.r[5]=tick
        original=vm.r[:15]
        pc=HOOK
        while True:
            pc=vm.run(pc,{HOOK+4,0x080d15c0,bx},max_steps=300)
            if pc==HOOK+4:break
            if pc==bx:
                assert vm.r[0]==127 and vm.r[3]==0x0837c349 and vm.r[14]==sym['m11_reel_stopped']
                ops.append((tick,'stop',127))
            else:ops.append((tick,'start',*vm.r[8:11]))
            pc=vm.r[14]
        assert vm.r[0]==710 and vm.r[1:15]==original[1:]
    assert ops==[(61,'start',3,4,0),(92,'start',127,1,0),(318,'stop',127)]
    # The immutable Thumb function loads the requested song header and player.
    # Its actual CMP BNE comparison guards the call to MPlayStop.
    assert after[0x37c360:0x37c370]==bytes.fromhex('11680068814202d1101c00f02dfb01bc')
    table=struct.unpack_from('<I',after,0x37c378)[0]-BASE
    head,player,again=struct.unpack_from('<IHH',after,table+127*8)
    assert (head,player,again)==(owner['reel_header'],3,3)
    assert struct.unpack_from('<I',after,0x37fbb4+12*3)[0]==0x03006c90
    cases={}
    for other in (0x03,0x3d,0x55,0x5a,0x7f):
        h,p,_=struct.unpack_from('<IHH',after,table+other*8)
        same=h==head
        assert same==(other==0x7f)
        cases[f'{other:02X}']=dict(player=p,header=h,passes_native_header_equality=same)
    return dict(status='MODE11_SCORE_AUDIO_ALL_710_FRAMES_PASS',image_sha256=sha(after),
                owner_sha256=sha(manifest),tested_score_frames=710,requests=ops,
                retail_song_specific_stop_samples=cases,whole_image_inverse=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('prior','image','owner','report'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();result=check(*(getattr(a,k).read_bytes() for k in ('prior','image','owner')))
    result['checker_sha256']=sha(Path(__file__).read_bytes())
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

