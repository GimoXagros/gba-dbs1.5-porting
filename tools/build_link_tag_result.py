"""Port the accepted cable result's tag exchange and the source mode24 streak producer."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode22_source_scene import assembly as primitives, EXPORTS, SOURCE
from mode23_linker import compose

PARENT='78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
OWNER='0D06FCB9A11A53629FB75B11495043D4A22499E4100153E2FC7EE6B6CDDC4278'
HOOKS=((0x37AB18,0xE3A08082,'link_tag_send'),(0x37AB8C,0xE3A00000,'link_tag_accept'),
       (0x15B24,0x03A00004,'link_streak_dispatch'))


def module(address,reader,writer,highest,carry):
    # The GBA uses six control/data bytes in a fixed 16-byte slot for WSC's
    # four-byte legacy result. Put its source rank after those six. Two more
    # spare bytes identify this extension so retail padding cannot award rank0.
    code=f"""
link_tag_send:
push {{r0-r12,lr}}
mrs r11,cpsr
ldr r4,=0x03002310
ldrb r0,[r4,#0x25]
tst r0,#1
bne link_tag_send_done
sub sp,sp,#44
mov r0,sp
bl 0x{reader:x}
cmp r0,#0
cmpne r0,#2
mvnne r0,#0
bne link_tag_send_store
mov r0,sp
bl 0x{highest:x}
link_tag_send_store:
ldr r1,=0x03002168
strh r0,[r1,#6]
ldr r2,=0xd675
strh r2,[r1,#8]
add sp,sp,#44
link_tag_send_done:
msr cpsr_f,r11
pop {{r0-r12,lr}}
mov r8,#0x82
b 0x0837ab1c
.ltorg

link_tag_accept:
push {{r0-r12,lr}}
mrs r11,cpsr
ldr r4,=0x03002310
ldrb r0,[r4,#0x25]
tst r0,#1
bne link_tag_accept_done
ldr r5,=0x03002178
ldr r6,=0x03001f00
ldrb r0,[r6]
cmp r0,#8
addeq r5,r5,#16
ldrh r0,[r5,#8]
ldr r1,=0xd675
cmp r0,r1
bne link_tag_accept_done
ldrh r7,[r5,#6]
bl link_local_scores
cmp r8,r9
beq link_tag_accept_done
sub sp,sp,#44
mov r0,sp
bl 0x{reader:x}
cmp r0,#0
cmpne r0,#2
bne link_tag_accept_pop
cmp r8,r9
blo link_tag_lose
cmp r7,#10
bhs link_tag_accept_pop
mov r0,sp
mov r1,r7
bl 0x{carry:x}
cmp r0,#0
beq link_tag_accept_pop
b link_tag_write
link_tag_lose:
mov r0,sp
bl 0x{highest:x}
cmp r0,#10
bhs link_tag_accept_pop
add r2,sp,#18
add r2,r2,r0,lsl #1
ldrh r1,[r2]
sub r1,r1,#1
strh r1,[r2]
link_tag_write:
mov r0,sp
bl 0x{writer:x}
link_tag_accept_pop:
add sp,sp,#44
link_tag_accept_done:
msr cpsr_f,r11
pop {{r0-r12,lr}}
mov r0,#0
b 0x0837ab90
.ltorg

link_streak_dispatch:
push {{r0-r12,lr}}
mrs r11,cpsr
ldrb r0,[r5,#0x25]
tst r0,#1
bne link_streak_done
sub sp,sp,#44
mov r0,sp
bl 0x{reader:x}
cmp r0,#0
cmpne r0,#2
bne link_streak_pop
bl link_local_scores
cmp r8,r9
movls r0,#0
bls link_streak_store
ldrh r0,[sp,#40]
add r0,r0,#1
mov r0,r0,lsl #16
mov r0,r0,lsr #16
ldr r1,=999
cmp r0,r1
movhi r0,r1
link_streak_store:
strh r0,[sp,#40]
mov r0,sp
bl 0x{writer:x}
link_streak_pop:
add sp,sp,#44
link_streak_done:
msr cpsr_f,r11
pop {{r0-r12,lr}}
mov r0,#4
b 0x08015b28
.ltorg

link_local_scores:
ldr r2,=0x0300475e
ldrb r8,[r2]
ldrb r9,[r2,#1]
ldr r2,=0x03004528
ldrb r0,[r2]
tst r0,#1
movne r1,r8
movne r8,r9
movne r9,r1
bx lr
.ltorg
"""
    return compose((code,),address,[label for _,_,label in HOOKS])


def build(src,before,owner_bytes,pinned_parent=PARENT,pinned_owner=OWNER):
    assert sha(src)==SOURCE and sha(before)==pinned_parent and sha(owner_bytes)==pinned_owner
    owner=json.loads(owner_bytes)
    assert owner['output_sha256']==pinned_parent
    assert src[0x741E40:0x741E4F]==bytes.fromhex('9afa078f84a378376a069a0211ff4f')
    assert src[0x77560B:0x775613]==bytes.fromhex('3bc27615ff84e600')
    assert src[0x74FE50:0x74FE5D]==bytes.fromhex('a8017506b81800e90300b80400')
    storage=owner['storage_exports']
    pure,exports,_=compose((primitives(src),),BASE,EXPORTS)
    at=before.find(pure)
    assert at==before.rfind(pure)==0xF7A3E8
    services=(storage['m22_read_snapshot'],storage['m22_write_snapshot'],at+exports['m22_source_highest'],at+exports['m22_source_carry'])
    prior=owner['prior_excluded_extents']+[[row['start'],row['end']] for row in owner['allocations']]
    alloc=Allocator(before)
    exclude(alloc,prior)
    size=len(module(BASE,*services)[0])
    off=alloc.allocate(size,'native cable tag and source result streak',4)
    code,symbols,link=module(BASE+off,*services)
    assert len(code)==size
    changes={off:code}
    for site,expected,name in HOOKS:
        assert struct.unpack_from('<I',before,site)[0]==expected
        delta = symbols[name]-(BASE+site+8)
        assert delta%4==0 and -(1<<25)<=delta<(1<<25)
        changes[site]=struct.pack('<I',(expected&0xF0000000)|0x0A000000|((delta//4)&0xFFFFFF))
    image=bytearray(before)
    for site,data in changes.items():image[site:site+len(data)]=data
    inverse=image[:]
    for site,data in changes.items():inverse[site:site+len(data)]=before[site:site+len(data)]
    assert inverse==before
    manifest=dict(input_sha256=pinned_parent,output_sha256=sha(image),prior_owner_sha256=pinned_owner,source_sha256=SOURCE,
                  builder_sha256=sha(Path(__file__).read_bytes()),symbols=symbols,storage_exports=storage,
                  prior_excluded_extents=prior,allocations=alloc.allocations,linkage=link,whole_image_inverse=True,
                  writes=[dict(offset=site,size=len(data),before_sha256=sha(before[site:site+len(data)]),after_sha256=sha(data)) for site,data in sorted(changes.items())],
                  note='E6 save is executed at the source mode24 decision. The GBA currently resumes at native character selection after it.')
    return image,manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','input','owner','output'):
        p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--input-sha256')
    p.add_argument('--owner-sha256')
    a=p.parse_args()
    if bool(a.input_sha256)!=bool(a.owner_sha256):
        p.error('the pinned parent image and owner must be supplied together')
    im,meta=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes(),
                  a.input_sha256 or PARENT,a.owner_sha256 or OWNER)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(im)
    m=a.output/'manifest.json';m.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8',newline='\n')
    print(meta['output_sha256'],sha(m.read_bytes()),meta['symbols'])


if __name__=='__main__':main()

