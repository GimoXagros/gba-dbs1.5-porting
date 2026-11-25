"""Select the common WSC roster and the retail evolution/serial rules only in legacy cable play."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose

PARENT = 'EF8BBC67DB243A8CCAFA25744EFB371CC097C323F45D25060419B33B577B75BA'
FINAL = 'AA6BB1EB93027464F842D6EB0CC69A68959F26B38460FAF1B0C63BDD5FFA4BB1'
OWNER = 'CD910DA852DF621FED7362EFB1C7D83CF8F62DEC6AC6B58F2669ED3A4D60B8A0'
SITES = {
    0x8170c: ('mixed_count', 0x85b0000),
    0x81d04: ('mixed_palette', 0x8628080),
    0x81ff4: ('mixed_confirm', 0x86280c0),
    0x83238: ('mixed_portrait', 0x8628100),
    0x354700: ('mixed_calumon', 0x8354738),
    0x81e60: ('mixed_handshake', None),
}
SYMBOLS = tuple(name for name, _ in SITES.values()) + ('common_roster',)

def cartridge_code():
    lookups = ''
    for start, register in ((0x81d04,4), (0x81ff4,4), (0x83238,8)):
        lookups += f"""
{SITES[start][0]}:
    push {{r0, lr}}
    bl mixed_table
    mov r{register}, r0
    pop {{r0, lr}}
    b 0x{BASE+start+4:x}
"""
    return lookups + """
mixed_table:
    push {r1, r2, lr}
    mrs r2, cpsr
    bl mixed_profile
    adrne r0, common_roster
    beq mixed_full_table
    b mixed_table_done
mixed_full_table:
    ldrb r1, [r0,#0x19]
    and r1, r1, #0x30
    ldr r0, =0x08628000
    add r0,r0,r1,lsl #1
mixed_table_done:
    msr cpsr_f,r2
    pop {r1,r2,pc}

mixed_profile:
    ldr r0, =0x03002310
    ldrh r1,[r0,#0x1a]
    tst r1,#1
    ldrbne r1,[r0,#0x25]
    tstne r1,#1
    bx lr

mixed_count:
    push {r0,r1,lr}
    bl mixed_profile
    pop {r0,r1,lr}
    beq 0x085b0000
    ldrb r0,[r5,#0x19]
    tst r0,#0x10
    mov r2,#11
    addne r2,r2,#1
    pop {r4}
    b 0x08081710

mixed_calumon:
    bne 0x08354738
    push {r0,r1,r2,lr}
    mrs r2,cpsr
    bl mixed_profile
    beq mixed_evolve
    msr cpsr_f,r2
    pop {r0,r1,r2,lr}
    b 0x08354704
mixed_evolve:
    msr cpsr_f,r2
    pop {r0,r1,r2,lr}
    b 0x08354738

mixed_handshake:
    push {r0,r1,r2,lr}
    mrs r2,cpsr
    bl mixed_profile
    orrne r3,r3,#0x0f
    orreq r3,r3,#0x4f
    msr cpsr_f,r2
    pop {r0,r1,r2,lr}
    b 0x08081e64
.ltorg
common_roster:
    .hword 0,1,2,3,4,5,6,7,8,9,10,11
"""


def install(before, owner):
    assert sha(before)==PARENT and sha(owner)==OWNER
    meta=json.loads(owner)
    assert meta['output_sha256']==PARENT and len(before)==0x1000000
    occupied=meta['prior_excluded_extents']+[[a['start'],a['end']] for a in meta['allocations']]
    allocator=Allocator(before)
    exclude(allocator,occupied)
    asm=cartridge_code()
    size=len(compose((asm,),BASE,SYMBOLS)[0])
    pos=allocator.allocate(size,'mixed cable profile',4)
    code, symbols, linkage=compose((asm,),BASE+pos,SYMBOLS)
    assert len(code)==size and before[pos:pos+size]==b'\xff'*size
    writes=[(pos,code)]
    for off,(symbol,previous) in SITES.items():
        expected=branch(BASE+off,previous) if previous else struct.pack('<I',0xe383300f)
        assert before[off:off+4]==expected,(symbol,hex(off))
        writes.append((off,branch(BASE+off,symbols[symbol])))
    image=bytearray(before)
    rows=[]
    for off,data in sorted(writes):
        rows.append(dict(offset=off,size=len(data),before_sha256=sha(before[off:off+len(data)]),after_sha256=sha(data)))
        image[off:off+len(data)]=data
    return image,dict(input_sha256=PARENT,prior_owner_sha256=OWNER,output_sha256=sha(image),
                      source_sha256=meta['source_sha256'],symbols=symbols,linkage=linkage,
                      prior_excluded_extents=occupied,allocations=allocator.allocations,
                      storage_exports=meta['storage_exports'],writes=rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','owner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    image,manifest=install(args.input.read_bytes(),args.owner.read_bytes())
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'component.gba').write_bytes(image)
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
    print(manifest['output_sha256'])

if __name__=='__main__':
    main()
