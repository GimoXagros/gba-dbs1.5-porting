"""Restore the link Master's name-entry sound schedule after the ordinary card scene."""
import argparse
import json
from pathlib import Path
import struct

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose

PARENT='249FB4C337964F72005233FD8F68E1A1A19D74171AC35BEA8E4ED932A74B086B'
OWNER='AF825A36A60DACAD6FC792D90D55C2DD9EB999FFBA9177E373C1C16E94BB1D6C'
PRESENTATION='876C1468C10DCDD66520D65E673D4D0C1ABDC3F3DF27B6E9C0BFFF7F7F5A91A9'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CARD_CALL,INPUT_CMP=0x08ecab10,0x08ecab2c


def build(before,source,raw_owner,raw_presentation):
    assert [sha(v) for v in (before,source,raw_owner,raw_presentation)]==[PARENT,SOURCE,OWNER,PRESENTATION]
    parent,pres=map(json.loads,(raw_owner,raw_presentation))
    assert parent['output_sha256']==PARENT
    assert source[0x774917:0x77491b]==bytes.fromhex('c6450c41')
    assert source[0x774a29:0x774a2c]==bytes.fromhex('803f28')
    symbols=pres['symbols']
    assert before[CARD_CALL-BASE:CARD_CALL-BASE+8]==branch(CARD_CALL,0x08eca8a8,True)+bytes.fromhex('100084e2')
    assert before[INPUT_CMP-BASE:INPUT_CMP-BASE+4]==bytes.fromhex('020050e3')
    body=f"""
m24_special_name_prepare:
    push {{r0-r4,lr}}
    ldr r0,=0x{symbols['m11_card_asset_table']:08x}
    ldr r0,[r0,#40]
    bl 0x{symbols['m11_transfers']:08x}
    mov r0,#0xb8
    ldr r1,=0x030012ba
    strb r0,[r1]
    mov r1,#0x04000000
    sub r0,r0,#8
    strh r0,[r1,#0x10]
    ldr r2,=0x030012b9
    mov r0,#246
    strb r0,[r2]
    sub r0,r0,#8
    strh r0,[r1,#0x16]
    pop {{r0-r4,pc}}
m24_special_input_sfx:
    cmp r1,#0
    beq m24_special_compare
    push {{r0-r12,lr}}
    cmp r1,#0x78
    moveq r8,#0x1e
    cmp r1,#0x79
    moveq r8,#0x1f
    cmp r1,#0x7a
    moveq r8,#0x20
    cmp r1,#6
    moveq r8,#0x21
    mov r9,#1
    moveq r9,#2
    mov r10,#0
    mov r11,#0
    bl 0x080d15c0
    pop {{r0-r12,lr}}
m24_special_compare:
    cmp r0,#2
    b 0x{INPUT_CMP+4:08x}
.ltorg
"""
    p=parent['prior_excluded_extents']+[[a['start'],a['end']] for a in parent['allocations']]
    allocate=Allocator(before);exclude(allocate,p)
    names=('m24_special_name_prepare','m24_special_input_sfx')
    trial=compose((body,),BASE,names)[0]
    offset=allocate.allocate(len(trial),'mode24 Master name and keypad feedback',4)
    code,exports,linkage=compose((body,),BASE+offset,names);assert len(code)==len(trial)
    writes=[(offset,code),(CARD_CALL-BASE,branch(CARD_CALL,exports[names[0]],True)),(INPUT_CMP-BASE,branch(INPUT_CMP,exports[names[1]]))]
    after=bytearray(before)
    for at,data in writes:after[at:at+len(data)]=data
    inverse=after[:]
    for at,data in writes:inverse[at:at+len(data)]=before[at:at+len(data)]
    assert inverse==before
    return after,dict(input_sha256=PARENT,output_sha256=sha(after),source_sha256=SOURCE,prior_owner_sha256=OWNER,
                      presentation_owner_sha256=PRESENTATION,storage_exports=parent['storage_exports'],
                      prior_excluded_extents=p,allocations=allocate.allocations,whole_image_inverse=True,
                      symbols=exports,linkage=linkage,builder_sha256=sha(Path(__file__).read_bytes()),
                      writes=[dict(offset=at,size=len(data),before_sha256=sha(before[at:at+len(data)]),after_sha256=sha(data)) for at,data in sorted(writes)])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','source','owner','presentation-owner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    rom,report=build(a.input.read_bytes(),a.source.read_bytes(),a.owner.read_bytes(),a.presentation_owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(rom)
    path=a.output/'manifest.json'
    path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(report['output_sha256'],sha(path.read_bytes()))


if __name__=='__main__':
    main()
