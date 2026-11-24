"""Compare the installed linked Master's 30 particles to the original WSC state updates."""
import argparse
import json
import random
import struct
from pathlib import Path

from verify_mode23_scene_component import POOL, empty, fill, memory, sha

BASE=0x08000000
STOP=0x0b000000
RNG=0x08012600
RENDER=POOL+0x118
CONTROL=POOL+0x230
BANK=0x76d7f0
PARENT='505DCE0601EA9ACCB7D27D9AE410132D27933E733580574F4B177541B05DA96D'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'


def signed(v):
    return (v+0x8000)%0x10000-0x8000


def model(source, particles, rng):
    gate=rng.getrandbits(16)&15
    rng.getrandbits(16)
    choice=rng.getrandbits(16)&15
    respawn=rng.getrandbits(16)&31
    cursor=0x1b59
    respawns=0
    for index,row in enumerate(particles):
        x,y,vx,vy,ax,ay,when=row
        vx=max(-7,min(7,signed(vx+ax)))
        vy=max(-7,min(7,signed(vy+ay)))
        x,y=signed(x+vx),signed(y+vy)
        if y>=0x980:
            cursor=0x5c7+4*respawn
            x,y=struct.unpack_from('<hh',source,BANK+cursor)
            respawns+=1
        if when<=gate:
            when=rng.getrandbits(16)&15
            p=BANK+cursor+(index%4)*128+choice*8
            vx,vy,ax,ay=struct.unpack_from('<4h',source,p)
        row[:]=[x,y,vx,vy,ax,ay,when]
    return respawns


def invoke(vm,address,rng):
    vm.r[14]=STOP
    while True:
        pc=vm.run(address,{RNG,STOP},max_steps=250000)
        if pc==STOP:return
        vm.r[0]=rng.getrandbits(16)
        address=vm.r[14]


def run(source,prior,rom,raw_owner):
    assert sha(prior)==PARENT and sha(source)==SOURCE
    meta=json.loads(raw_owner)
    assert meta['output_sha256']==sha(rom)
    sym=meta['symbols']
    vm=empty(rom)
    vm.r[9:11]=RENDER,CONTROL
    within=0x03003048
    pattern=bytes((i*131+219)%256 for i in range(0xbe0))
    fill(vm,within,pattern)
    before_r=memory(vm,RENDER,0x118)
    before_c=memory(vm,CONTROL,0x118)
    gr=random.Random(0x736d24)
    sr=random.Random(0x736d24)
    invoke(vm,sym['m24s_party_init'],gr)
    assert memory(vm,0x05000260,32)==rom[0x194ee:0x1950e]
    def slot(n):
        return (RENDER+120+10*n) if n<15 else (CONTROL+24+10*(n-15))
    particles=[]
    for i in range(30):
        x,y=struct.unpack_from('<hh',source,0x774ca8+i*4)
        assert memory(vm,slot(i),10)==struct.pack('<hh6x',x,y)
        particles.append([x,y,0,0,0,0,0])
    forced=(0,14,15,29)
    for n in forced:
        # Boundary fixture only: start four original slots at the offscreen edge.
        vm.put(slot(n)+2,0x980,2)
        particles[n][1]=0x980
    # Four screen snapshots near guard tiles also cover negative X/Y handling.
    emitted=respawns=0
    for tick in range(1,161):
        vm.put(CONTROL+212,tick)
        vm.put(0x030012ca,0,1)
        invoke(vm,sym['m24s_particles'],gr)
        respawns+=model(source,particles,sr)
        objects=[]
        for i,(x,y,*_) in enumerate(particles):
            assert struct.unpack('<hh',memory(vm,slot(i),4))==(x,y)
            dx,dy=(x>>4)-4,(y>>4)-4
            if -15<=dx<232 and -15<=dy<152:
                phase=2*((i+1)//6)
                tile=(0,9,6,3,12,15)[i%6]+((tick+phase)%30)//10
                objects.append((dx,dy,tile))
        assert vm.get(0x030012ca,1)==len(objects)
        for j,(dx,dy,tile) in enumerate(objects):
            attrs=struct.unpack('<4H',memory(vm,0x03001428+8*j,8))
            assert attrs==((dy+8)&255,(dx+8)&511,0x3400+j,0)
            at=0x192a8+tile*32
            assert memory(vm,0x02000000+32*j,32)==rom[at:at+32]
            emitted+=1
    assert gr.getstate()==sr.getstate() and respawns>=4
    assert memory(vm,within,len(pattern))==pattern
    after_r=memory(vm,RENDER,0x118)
    after_c=memory(vm,CONTROL,0x118)
    assert before_r[:120]==after_r[:120] and before_r[270:]==after_r[270:]
    assert before_c[:24]==after_c[:24] and before_c[174:212]==after_c[174:212] and before_c[216:]==after_c[216:]
    return dict(status='MODE24_ORIGINAL_PARTICLE_PHYSICS_AND_OWNERSHIP_PASS',rom_sha256=sha(rom),
                source_sha256=SOURCE,owner_sha256=sha(raw_owner),particles=30,frames=160,
                matched_positions=4800,matched_visible_tiles=emitted,respawns=respawns,
                original_mode11_global_particle_bytes_preserved=len(pattern),
                limits='Seeded identical random draws and four synthetic offscreen positions exercise signed source math. Live paired Master acquisition is a separate probe.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('source','prior','image','owner','report'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();result=run(*(getattr(a,k).read_bytes() for k in ('source','prior','image','owner')))
    result['checker_sha256']=sha(Path(__file__).read_bytes())
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

