"""Check native score/card selection, source artwork, safe exits and the audio guard."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_mode23_scene_component import POOL, empty, fill, memory

BASE=0x08000000
STOP=0x0b000000
END=0x080c0d18
HOOK=0x08dd0c24
TASK=POOL+3*0x118
DATA=TASK+24
SOUND=0x080d15c0
READER=0x08fb6130
OWNER='876C1468C10DCDD66520D65E673D4D0C1ABDC3F3DF27B6E9C0BFFF7F7F5A91A9'
TARGET='54B3033E182431DA168452CF78C73C7A39352D31396E94C4ABF60B011C6AED70'
PRIOR='78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def pack_tile(data):
    out=bytearray()
    for y in range(8):
        planes=data[y*4:y*4+4]
        pixels=[sum(((b>>(7-x))&1)<<i for i,b in enumerate(planes)) for x in range(8)]
        out.extend(pixels[x]|(pixels[x+1]<<4) for x in range(0,8,2))
    return bytes(out)


def mapword(w):
    return (w&0x1ff)|((w>>13&1)<<9)|((w>>14&3)<<10)|((w>>9&15)<<12)


def palette(data):
    colors=[]
    for i in range(16):
        w=int.from_bytes(data[i*2:i*2+2],'little')
        b,g,r=w&15,(w>>4)&15,(w>>8)&15
        c=lambda v:2*v+bool(v)
        colors.append(c(r)|(c(g)<<5)|(c(b)<<10))
    return struct.pack('<16H',*colors)


def invoke(vm,symbols,entry,stop=STOP,*,read=None,sound=None):
    vm.r[14]=STOP
    address=entry
    ldm=symbols['m11_transfers']+20
    assert vm.get(ldm)==0xe8b4000e
    for _ in range(1100):
        pc=vm.run(address,{stop,ldm,READER,SOUND},max_steps=300000)
        if pc==stop:return
        if pc==ldm:
            # ARM7 LDMIA R4!,{R1,R2,R3}, in the generic stride-aware transfer.
            base=vm.r[4]
            vm.r[1:4]=[vm.get(base+i) for i in (0,4,8)]
            vm.r[4]=base+12
            address=pc+4
        else:
            if pc==SOUND:
                assert sound is not None
                sound.append(tuple(vm.r[8:11]))
            elif pc==READER:
                assert read is not None
                status,highest=read
                if status==0:vm.put(vm.r[0]+38,highest,2)
                vm.r[0]=status
            address=vm.r[14]
    raise AssertionError('unexpected service loop')


def fixture(rom,age,phase,token):
    vm=empty(rom)
    vm.put(0x0300133c,TASK)
    vm.put(0x03003040,POOL+0x118)
    vm.put(0x03003cf8,POOL+0x230)
    fill(vm,DATA,bytes(256))
    vm.put(DATA,age,2)
    vm.put(DATA+2,phase,2)
    vm.put(DATA+4,token,2)
    vm.put(DATA+24,0x080c12dc)
    vm.put(DATA+28,0x080c07f4)
    vm.put(DATA+32,0x080cb9e8)
    vm.put(DATA+48,0x0f06,2)
    vm.put(DATA+52,0x01020304)
    vm.put(DATA+56,0x12345678)
    vm.r[14]=STOP
    return vm


def check(source,prior,image,owner):
    assert (sha(source),sha(prior),sha(image),sha(owner))==(SOURCE,PRIOR,TARGET,OWNER)
    report=json.loads(owner)
    symbols=report['symbols']
    inverse=bytearray(image)
    spans=[]
    for row in report['writes']:
        lo,n=row['offset'],row['size']
        hi=lo+n
        assert sha(image[lo:hi])==row['after_sha256'] and sha(prior[lo:hi])==row['before_sha256']
        if lo!=HOOK-BASE:
            assert prior[lo:hi]==b'\xff'*n
            assert all(hi<=a or b<=lo for a,b in report['prior_excluded_extents'])
        inverse[lo:hi]=prior[lo:hi]
        spans.append((lo,hi))
    spans.sort()
    assert inverse==prior and all(a[1]<=b[0] for a,b in zip(spans,spans[1:]))
    source_bank=0x2d9360
    converted_frames=0
    for rank in range(11):
        vm=fixture(image,709,0,0x8000+rank)
        invoke(vm,symbols,symbols['m11_controller'])
        assert vm.get(DATA,2)==0 and vm.get(DATA+2,2)==1 and vm.get(0x030012b6,2)==7
        art,pal=struct.unpack_from('<2H',source,0x77407c+4*rank)
        w,h,y,table=(10,6,2,0x6242) if rank==10 else (7,4,5,0x620a)
        lo=source_bank+art
        tiles=b''.join(pack_tile(source[q:q+32]) for q in range(lo,lo+w*h*32,32))
        assert memory(vm,0x06006540,len(tiles))==tiles
        assert memory(vm,0x050001e0,32)==palette(source[source_bank+pal:source_bank+pal+32])
        assert vm.get(0x05000000,2)==0
        for j in range(h):
            for i in range(w):
                entry=struct.unpack_from('<H',source,source_bank+table+2*(j*w+i))[0]
                assert vm.get(0x0600f800+(j+y)*64+2*i,2)==mapword(entry)
        for incoming,expected_count in ((rank,17),(0x8000+rank,33)):
            vm.put(DATA,(114 if rank==10 else 112)-1,2)
            vm.put(DATA+4,incoming,2)
            vm.put(0x030012ca,0,1)
            invoke(vm,symbols,symbols['m11_controller'])
            assert vm.get(0x030012ca,1)==expected_count
            assert vm.get(0x030012ba,1)==(0xb8 if rank==10 else 0xac)
            converted_frames+=1
    for status,highest,expected in ((0,0,END),(2,0,END),(3,0,END),(1,0,END),(0,1,STOP)):
        vm=fixture(image,397,1,0x8007)
        invoke(vm,symbols,symbols['m11_controller'],expected,read=(status,highest))
        if expected==STOP:
            assert vm.get(DATA+4,2)==0x800a and vm.get(DATA,2)==0 and vm.get(DATA+2,2)==1
        else:
            assert vm.get(0x030012e0)==0x080cb9e8 and vm.get(0x030012b6,2)==0x0f06
            assert vm.get(POOL+0x118)==0x080c12dc and vm.get(POOL+0x230)==0x080c07f4
            assert vm.get(POOL+0x118+0x110)==0x12345678 and vm.get(0x030012b8)==0x01020304
    vm=fixture(image,709,0,0xffff)
    invoke(vm,symbols,symbols['m11_controller'],END)
    score_cases=0
    for id in range(15):
        for side in (0,1):
            vm=fixture(image,390,0,0x8000)
            vm.put(0x03004528,side,1)
            vm.put(0x0300231a+2*side,id,1)
            vm.put(0x0300231b+2*side,side,1)
            vm.put(0x0300231f,id%4,1)
            fill(vm,DATA+40,b'2310\0')
            invoke(vm,symbols,symbols['m11_controller'])
            row=0x4a80f8+32*id
            raw=struct.unpack_from('<I',image,row+8+4*side)[0]-BASE+6
            assert memory(vm,0x05000280,32)==image[raw:raw+32]
            assert 37<=vm.get(0x030012ca,1)<128
            score_cases+=1
    for enabled in (0,1):
        local=bytearray(image)
        struct.pack_into('<I',local,symbols['m11_tag_audio_ready']-BASE,enabled)
        vm=fixture(local,0,0,0)
        for index in range(0x7a,0x80):
            calls=[]
            priority=1 if index==0x7b else 4
            vm.r[:2]=index,priority
            regs=vm.r[:14]
            invoke(vm,symbols,symbols['m11_tag_audio'],sound=calls)
            assert vm.r[:14]==regs and calls==([(index,priority,0)] if enabled and 0x7b<=index<=0x7e else [])
    return dict(status='MODE11_PRESENTATION_ARM_PASS',rom_sha256=sha(image),owner_sha256=sha(owner),
                source_sha256=sha(source),source_badge_maps_palettes_and_tiles=11,
                new_and_repeat_tag_actor_cases=converted_frames,selected_score_actor_cases=score_cases,
                carry_and_error_cases=5,no_award_skip_cases=1,audio_guard_cases=12,
                whole_image_inverse=True,
                limits='The audio driver and EEPROM transport are boundaries in this fixture. Real BCD entry, card/exit and a second-process physical EEPROM read have their own capture report.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','prior','image','owner','report'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    result=check(*(getattr(a,name).read_bytes() for name in ('source','prior','image','owner')))
    result['checker_sha256']=sha(Path(__file__).read_bytes())
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

