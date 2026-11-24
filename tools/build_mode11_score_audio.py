"""Restore the three WSC score-reel requests, preserving independent MP2K players."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode23_linker import compose

PRIOR='9A8D51B08310376C093013D952FC7A02973134F3FE338C1718AF009B4B692B2D'
OWNER='8B483AEFD27C4F87438B60155417A306E84602209C7035F0AC4EEC21D25B6DA3'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOK=0xea4840
LOADERS=(0x37c2a4,0x37c2d8,0x37c324,0x37c378,0x37c3ac)


def assembly(address):
    body="""
@ Native score controller r5 = elapsed source score frames from 73D3:1562.
m11_score_audio:
    cmp r5,#61
    beq m11_score_music
    cmp r5,#92
    beq m11_reel_start
    ldr r0,=318
    cmp r5,r0
    beq m11_reel_stop
m11_score_continue:
    ldr r0,=710
    b 0x08ea4844
m11_score_music:
    push {r0-r12,lr}
    mov r8,#3
    mov r9,#4
    b m11_score_request
m11_reel_start:
    push {r0-r12,lr}
    mov r8,#0x7f
    mov r9,#1
m11_score_request:
    mov r10,#0
    mov r11,#0
    bl 0x080d15c0
    pop {r0-r12,lr}
    b m11_score_continue
m11_reel_stop:
    push {r0-r12,lr}
    mov r0,#0x7f
    ldr r3,=0x0837c349
    mov lr,pc
    bx r3
m11_reel_stopped:
    pop {r0-r12,lr}
    b m11_score_continue
.ltorg
"""
    return compose((body,),address,('m11_score_audio','m11_score_music','m11_reel_start','m11_reel_stop','m11_reel_stopped'))


def build(source,image,raw_owner):
    assert (sha(source),sha(image),sha(raw_owner))==(SOURCE,PRIOR,OWNER)
    prior=json.loads(raw_owner)
    assert prior['output_sha256']==PRIOR and prior['song_count']==128
    assert image[HOOK:HOOK+4]==bytes.fromhex('a4059fe5')
    assert struct.unpack_from('<I',image,HOOK+8+0x5a4)[0]==710
    assert source[0x7752e6:0x7752f1]==bytes.fromhex('6a006a046a149a b8011987')
    assert source[0x77533c:0x775348]==bytes.fromhex('6a006a0168b6009ab8011987')
    assert source[0x7753bf:0x7753ca]==bytes.fromhex('6a006a016a069ab8011987')
    table=prior['table']
    assert all(struct.unpack_from('<I',image,off)[0]==BASE+table for off in LOADERS)
    rows={x['source']:x for x in prior['sounds']}
    assert (rows[0xb6]['native'],rows[0xb6]['player'])==(127,3)
    assert struct.unpack_from('<IHH',image,table+127*8)==(BASE+rows[0xb6]['header_raw'],3,3)
    music,channel,duplicate=struct.unpack_from('<IHH',image,table+3*8)
    assert image[music-BASE]>0 and channel==duplicate==0
    expected=bytes.fromhex('00b50004094a0a49400b401883885900c918890089180a6811680068814202d1101c00f02dfb01bc')
    assert image[0x37c348:0x37c348+len(expected)]==expected
    extents=prior['prior_excluded_extents']+[[r['start'],r['end']] for r in prior['allocations']]
    alloc=Allocator(image)
    exclude(alloc,extents)
    size=len(assembly(BASE)[0])
    at=alloc.allocate(size,'ending score music and guarded reel release',4)
    assert image[at:at+size]==b'\xff'*size
    code,symbols,link=assembly(BASE+at)
    delta=(BASE+at)-(BASE+HOOK+8)
    assert len(code)==size and delta%4==0 and -(1<<25)<=delta<1<<25
    writes={HOOK:struct.pack('<I',0xea000000|((delta//4)&0xffffff)),at:code}
    output=bytearray(image)
    report=[]
    for off,raw in sorted(writes.items()):
        output[off:off+len(raw)]=raw
        old=image[off:off+len(raw)]
        report.append(dict(offset=off,size=len(raw),before_sha256=sha(old),after_sha256=sha(raw)))
    inverse=output[:]
    for off,raw in writes.items():inverse[off:off+len(raw)]=image[off:off+len(raw)]
    assert inverse==image
    return output,dict(input_sha256=PRIOR,output_sha256=sha(output),prior_owner_sha256=OWNER,source_sha256=SOURCE,
             builder_sha256=sha(Path(__file__).read_bytes()),prior_excluded_extents=extents,
             allocations=alloc.allocations,storage_exports=prior['storage_exports'],symbols=symbols,
             linkage=link,writes=report,whole_image_inverse=True,
             score_music_header=music,reel_header=rows[0xb6]['header_raw']+BASE)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','input','owner','output'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    image,report=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    dest=a.output/'manifest.json'
    dest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['output_sha256'],sha(dest.read_bytes()))


if __name__=='__main__':main()

