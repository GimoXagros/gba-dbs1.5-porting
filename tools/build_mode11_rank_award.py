"""Bind the mode 11 positive-clear score to the save-backed WSC rank-award primitive."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode22_source_scene import EXPORTS, SOURCE, assembly as primitives
from mode23_linker import compose

BEFORE = '476E753BC09D8EB3B39F2CB0F6734241233EE7080B4E901AB57C20B603327D08'
OWNER = '27AF52D2CBBD96AF21A2B98D71E28C6762B5FB807D121AB005BEC0E1643333C7'
HOOK = 0xc0d14


def assemble(at, read, write, award):
    body = f"""
m11_award_at_fade:
    push {{r0-r12,lr}}
    mrs r6,cpsr
    bl m11_award_persist
m11_award_result:
    msr cpsr_f,r6
    pop {{r0-r12,lr}}
    ldr r8,m11_side
    b 0x080c0d18

m11_award_persist:
    push {{r1-r12,lr}}
    sub sp,sp,#44
    ldr r1,m11_config
    ldrb r4,[r1,#15]
    cmp r4,#3
    bhi m11_no_award
    mov r0,sp
    bl 0x{read:08x}
    cmp r0,#0
    cmpne r0,#2
    bne m11_no_award
    mov r0,sp
    mov r1,r4
    ldr r2,m11_score
    ldrh r2,[r2]
    bl 0x{award:08x}
    mov r4,r0
    ldr r5,m11_refused
    cmp r4,r5
    beq m11_no_award
    mov r0,sp
    bl 0x{write:08x}
    cmp r0,#0
    bne m11_no_award
    mov r0,r4
    b m11_award_return
m11_no_award:
    ldr r0,m11_refused
m11_award_return:
    add sp,sp,#44
    pop {{r1-r12,lr}}
    bx lr
.align 2
m11_side: .word 0x03004528
m11_config: .word 0x03002310
m11_score: .word 0x03003d02
m11_refused: .word 0xffff
"""
    return compose((body,),at,('m11_award_at_fade','m11_award_result','m11_award_persist'))


def build(source,before,owner):
    if (sha(source),sha(before),sha(owner)) != (SOURCE,BEFORE,OWNER):
        raise ValueError('mode11 rank award source, ancestor or ownership')
    meta=json.loads(owner)
    assert meta['output_sha256']==BEFORE and struct.unpack_from('<I',before,HOOK)[0]==0xe59f81d4
    pure,exports,_=compose((primitives(source),),BASE,EXPORTS)
    placed=before.find(pure)
    assert placed==before.rfind(pure)==0xf7a3e8
    rank=placed+exports['m22_source_score_award']
    storage=meta['storage_exports']
    imports=(storage['m22_read_snapshot'],storage['m22_write_snapshot'],rank)
    extents=meta['prior_excluded_extents']+[[r['start'],r['end']] for r in meta['allocations']]
    allocator=Allocator(before)
    exclude(allocator,extents)
    size=len(assemble(BASE,*imports)[0])
    off=allocator.allocate(size,'mode11 earned tag storage',4)
    assert before[off:off+size]==bytes([255])*size and all(off+size<=a or b<=off for a,b in extents)
    code,symbols,link=assemble(BASE+off,*imports)
    assert len(code)==size
    delta=symbols['m11_award_at_fade']-(BASE+HOOK+8)
    assert delta%4==0 and -(1<<25)<=delta<1<<25
    writes={HOOK:struct.pack('<I',0xea000000|((delta//4)&0xffffff)),off:code}
    image=bytearray(before)
    for at,data in writes.items():image[at:at+len(data)]=data
    inverse=image[:]
    for at,data in writes.items():inverse[at:at+len(data)]=before[at:at+len(data)]
    assert inverse==before
    return image,dict(input_sha256=BEFORE,output_sha256=sha(image),prior_owner_sha256=OWNER,
        source_sha256=SOURCE,builder_sha256=sha(Path(__file__).read_bytes()),source_award_entry=rank,
        prior_excluded_extents=extents,allocations=allocator.allocations,storage_exports=storage,
        symbols=symbols,linkage=link,writes=[dict(offset=a,size=len(d),before_sha256=sha(before[a:a+len(d)]),after_sha256=sha(d))
        for a,d in sorted(writes.items())],whole_image_inverse=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','input','owner','output'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    image,result=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(result['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':main()
