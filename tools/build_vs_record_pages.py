"""Restore the five source VS RECORD pages and bind each portrait/stat pair to the same ID."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode23_linker import compose

BEFORE = '3CB82DEC80C68FF85199A5BD264D78F3C794A6C522539731550B1A797A06A74C'
OWNER = '0CFB507D336D886D0BC137DFD41D7DE2CC913F3FD0D1A22050F3C1B0D46F7F0D'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOKS = (
    (0x33ec90, 0xe1c480b2, 'vs_capture'), (0x33ee68, 0xe1d430b0, 'vs_first_portrait'),
    (0x33ef74, 0xe2855020, 'vs_second_portrait'), (0x33f07c, 0xe2855020, 'vs_third_portrait'),
    (0x33ef10, 0xe3520007, 'vs_first_lock'), (0x33f018, 0xe3520007, 'vs_second_lock'),
    (0x33f120, 0xe3520007, 'vs_third_lock'), (0x33f35c, 0xe59f14b4, 'vs_first_row'),
    (0x33f4bc, 0xe2811004, 'vs_second_row'), (0x33f610, 0xe2811004, 'vs_third_row'),
)


def code_at(address, roster, reader):
    code = f"""
vs_capture:
    strh r8,[r4,#2]
    push {{r0-r5,lr}}
    sub sp,sp,#44
    mov r0,sp
    bl 0x{reader:08x}
    cmp r0,#0
    moveq r1,sp
    add r2,r4,#244
    mov r3,#0
    ldreq r3,[r1]
    str r3,[r2]
    ldreq r3,[r1,#4]
    str r3,[r2,#4]
    ldreq r3,[r1,#8]
    str r3,[r2,#8]
    add sp,sp,#44
    pop {{r0-r5,lr}}
    b 0x0833ec94
"""
    for i, (label, pointer_offset, resume) in enumerate((
            ('first', 0, 0x833ee78), ('second', -4, 0x833ef80), ('third', -84, 0x833f088))):
        code += f"""
vs_{label}_portrait:
    ldrh r3,[r4,#{pointer_offset}]
    add r3,r3,#{i}
    adr r8,vs_roster
    ldrb r2,[r8,r3]
    mov r5,r2,lsl #5
"""
        if i:
            code += '    add r4,r4,#80\n'
        else:
            code += '    mov r3,r5\n'
        code += f'    b 0x{resume:08x}\n'
    for label, original, skip in (('first',0x833ef18,0x833ef40), ('second',0x833f020,0x833f048),
                                   ('third',0x833f128,0x833f150)):
        code += f"""
vs_{label}_lock:
    cmp r2,#11
    blo 0x{skip:08x}
    cmp r2,#12
    bhi 0x{skip:08x}
    b 0x{original:08x}
"""
    for index,(label,resume) in enumerate((('first',0x833f36c),('second',0x833f4c0),('third',0x833f614))):
        code += f"""
vs_{label}_row:
    ldrh r8,[r4]
    add r8,r8,#{index}
    adr r1,vs_roster
    ldrb r8,[r1,r8]
    cmp r8,#12
    ldrlo r1,vs_native_rows
    addhs r1,r4,#244
    subhs r8,r8,#12
    add r1,r1,r8,lsl #2
    b 0x{resume:08x}
"""
    code += '\nvs_native_rows: .word 0x030011ae\nvs_roster: .byte '+','.join(map(str,roster))+',255\n'
    return compose((code,),address,[name for _,_,name in HOOKS])


def build(source, before, owner_bytes):
    if (sha(source),sha(before),sha(owner_bytes)) != (SOURCE,BEFORE,OWNER):
        raise ValueError('VS RECORD source, prior layer or owner identity')
    parent = json.loads(owner_bytes)
    assert parent['output_sha256'] == BEFORE
    source_words = struct.unpack_from('<16H',source,0x76cf4e)
    assert source_words == (0,1,2,3,4,5,6,7,8,9,10,13,14,11,12,65535)
    reader = parent['storage_exports']['m22_read_snapshot']
    extents = parent['prior_excluded_extents'] + [[r['start'],r['end']] for r in parent['allocations']]
    allocator = Allocator(before)
    exclude(allocator,extents)
    size = len(code_at(0x08f00000,source_words[:-1],reader)[0])
    off = allocator.allocate(size,'VS RECORD source identity and three private stat pairs',4)
    assert before[off:off+size] == b'\xff'*size and all(off+size<=a or b<=off for a,b in extents)
    code,symbols,link = code_at(BASE+off,source_words[:-1],reader)
    assert len(code)==size
    writes={off:code}
    for at,expected,name in HOOKS:
        assert struct.unpack_from('<I',before,at)[0] == expected
        delta = symbols[name]-(BASE+at+8)
        assert not delta%4 and -(1<<25)<=delta<(1<<25)
        writes[at]=struct.pack('<I',0xea000000|((delta//4)&0xffffff))
    assert struct.unpack_from('<I',before,0x33f910)[0]==0xe358000c
    writes[0x33f910]=struct.pack('<I',0xe358000f)
    image = bytearray(before)
    for at,data in writes.items():
        image[at:at+len(data)] = data
    inverse = image[:]
    for at,data in writes.items():
        inverse[at:at+len(data)] = before[at:at+len(data)]
    assert inverse == before
    report = dict(input_sha256=BEFORE,output_sha256=sha(image),source_sha256=SOURCE,prior_owner_sha256=OWNER,
        builder_sha256=sha(Path(__file__).read_bytes()),linkage=link,symbols=symbols,storage_exports=parent['storage_exports'],
        prior_excluded_extents=extents,allocations=allocator.allocations,source_roster=list(source_words[:-1]),
        current_task_scratch=[0x10c,0x118],writes=[dict(offset=at,size=len(data),before_sha256=sha(before[at:at+len(data)]),
        after_sha256=sha(data)) for at,data in sorted(writes.items())],whole_image_inverse=True)
    return image,report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','input','owner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args()
    image,report=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':
    main()
