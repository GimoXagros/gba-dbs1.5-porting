"""Verify original campaign particle quanta and all native tile submissions on the installed ROM."""
import argparse
import json
import struct
from pathlib import Path

from verify_mode23_scene_component import POOL, empty, fill, memory, sha
from verify_mode24_special_particles import model

BASE=0x08000000
PARTICLES=0x03003048
SIBLING=POOL+0x230
STOP=0x0b000000
RESUME=0x08EA4BD4
PARENT='2922F5865C962A4AFA148DC80736ADBA96FDFE5786DAFB7F008845C7B529CFE7'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'


class RetailRng:
    """08012600, including the byte exchange before consumers mask the result."""
    def __init__(self,a,b):
        self.a,self.b=a,b
        self.calls=0

    def getrandbits(self,bits):
        assert bits==16
        total=self.a+self.b+0x3711
        self.a,self.b=self.b,total&0xffff
        self.calls+=1
        return (total>>8)+((total&255)<<8)


def run(source,prior,image,raw_owner):
    meta=json.loads(raw_owner)
    assert (sha(source),sha(prior),sha(image))==(SOURCE,PARENT,meta['output_sha256'])
    assert meta['input_sha256']==PARENT
    assert len(meta['writes'])==2 and meta['writes'][0]['offset']==0xea4bc0 and meta['writes'][0]['size']==4
    inverse=bytearray(image)
    for row in meta['writes']:
        at,n=row['offset'],row['size']
        assert sha(image[at:at+n])==row['after_sha256'] and sha(prior[at:at+n])==row['before_sha256']
        inverse[at:at+n]=prior[at:at+n]
    assert inverse==prior
    vm=empty(image)
    sentinel=bytes((k*197+29)%256 for k in range(0xbe0))
    fill(vm,PARTICLES,sentinel)
    vm.put(0x03003cf8,SIBLING)
    vm.put(SIBLING,0x08ea473c)
    rngptr=struct.unpack_from('<I',image,0x12630)[0]
    rng=RetailRng(0xba55,0xb00b)
    vm.put(rngptr,rng.a|(rng.b<<16))
    vm.r[14]=STOP
    regs=vm.r[:15].copy()
    assert vm.run(0x08ea4bc0,{RESUME},max_steps=30000)==RESUME
    assert vm.r[:15]==regs and vm.get(SIBLING)==meta['symbols']['m11p_tick']
    assert memory(vm,0x05000260,32)==image[0x194ee:0x1950e]
    rows=[list(struct.unpack_from('<hh',source,0x774ca8+4*i))+[0]*5 for i in range(30)]
    model(source,rows,rng)
    assert rng.calls==34 and vm.get(rngptr)==rng.a|(rng.b<<16)
    assert vm.get(0x030012ca,1)==0
    def slot(i):
        return PARTICLES+10*i+(2 if i>=15 else 0)
    visible=0
    respawns=0
    forced={4:(0,14),70:(15,29)}
    for tick in range(1,181):
        for i in forced.get(tick,()):
            rows[i][1]=0x980
            vm.put(slot(i)+2,0x980,2)
        vm.put(0x030012ca,0,1)
        vm.r[14]=STOP
        assert vm.run(vm.get(SIBLING),{STOP},max_steps=50000)==STOP and vm.r[:14]==regs[:14]
        respawns+=model(source,rows,rng)
        assert vm.get(rngptr)==rng.a|(rng.b<<16)
        assert vm.get(PARTICLES+340)==tick%30
        onscreen=[]
        for index,(x,y,*_) in enumerate(rows):
            assert struct.unpack('<hh',memory(vm,slot(index),4))==(x,y)
            dx,dy=(x>>4)-4,(y>>4)-4
            phase=2*((index+1)//6)
            tile=(0,9,6,3,12,15)[index%6]+((tick+phase)%30)//10
            if -15<=dx<232 and -15<=dy<152:
                onscreen.append((dx,dy,tile))
        assert vm.get(0x030012ca,1)==len(onscreen)
        for n,(dx,dy,tile) in enumerate(onscreen):
            assert struct.unpack('<4H',memory(vm,0x03001428+8*n,8))==((dy+8)&255,(dx+8)&511,0x3400+n,0)
            assert memory(vm,0x02000000+n*32,32)==image[0x192a8+tile*32:0x192c8+tile*32]
        visible+=len(onscreen)
    assert respawns>=4
    for lo,hi in ((150,152),(302,340),(344,len(sentinel))):
        assert memory(vm,PARTICLES+lo,hi-lo)==sentinel[lo:hi]
    return dict(status='CAMPAIGN_MASTER_SOURCE_PARTICLES_PASS',source_sha256=SOURCE,input_sha256=PARENT,
                rom_sha256=sha(image),owner_sha256=sha(raw_owner),whole_image_inverse=True,
                source_initial_draws=34,identical_native_random_draws=rng.calls,matched_positions=5400,
                matched_visible_object_tiles=visible,respawns=respawns,
                unchanged_original_particle_area_bytes=len(sentinel)-304,
                limits='Fixed shared random draws for source-vs-native differential. Four boundary placements exercise respawn. Genuine earned gameplay is a separate replay.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('source','prior','image','owner','report'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    result=run(*(getattr(a,k).read_bytes() for k in ('source','prior','image','owner')))
    result['checker_sha256']=sha(Path(__file__).read_bytes())
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()

