"""Bound the active link-name animation clock while preserving every particle's 30-tick phase."""
import argparse
import json
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose

PARENT='6AE6D4AFD5AB82C6933F2A73F327F3FA67978CB7AC81A079538B03939ACCE68B'
OWNER='07A7EA616C71FE39DB3EE8B7235D32C577253DE88EDD9FEF5C94EB54D8A608B4'
CELEBRATION='74AF7A5614AE9923EF81CC16B2657EE097046C81209766F2331DC2A755BB3F39'
CLOCK_ADD=0x08F15440
ENTRY='m24_next_particle_tick'


def build(image,owner_raw,celebration_raw):
    assert (sha(image),sha(owner_raw),sha(celebration_raw))==(PARENT,OWNER,CELEBRATION)
    owner,celebration=map(json.loads,(owner_raw,celebration_raw))
    symbols=celebration['symbols']
    assert owner['output_sha256']==PARENT and owner['prior_owner_sha256']==CELEBRATION
    assert symbols['m24s_animate']+12==CLOCK_ADD
    clock=next(row for row in celebration['writes'] if row['offset']==symbols['m24s_sprite']-BASE)
    assert sha(image[clock['offset']:clock['offset']+clock['size']])==clock['after_sha256']
    assert image[CLOCK_ADD-BASE-4:CLOCK_ADD-BASE+8]==bytes.fromhex('580094e5010080e2580084e5')
    body=f"""
{ENTRY}:
    push {{r1,r2}}
    mrs r2,cpsr
    cmp r0,#180
    addlo r0,r0,#1
    movhs r1,#150
    moveq r0,#151
    bls m24_tick_done
    @ A normal task starts at zero and wraps at 180. An older live clock
    @ also retains its phase, including values near the 32-bit limit.
    sub r0,r0,r1
    mov r1,#0xf0000000
m24_tick_reduce:
    cmp r0,r1
    subhs r0,r0,r1
    mov r1,r1,lsr #1
    cmp r1,#30
    bhs m24_tick_reduce
    add r0,r0,#151
m24_tick_done:
    msr cpsr_f,r2
    pop {{r1,r2}}
    b 0x{CLOCK_ADD+4:08x}
.ltorg
"""
    prior=owner['prior_excluded_extents']+[[a['start'],a['end']] for a in owner['allocations']]
    allocator=Allocator(image);exclude(allocator,prior)
    trial=compose((body,),BASE,(ENTRY,))[0]
    offset=allocator.allocate(len(trial),'bounded 30-tick link name animation',4)
    code,exports,linkage=compose((body,),BASE+offset,(ENTRY,))
    assert len(code)==len(trial)
    patches=[(offset,code),(CLOCK_ADD-BASE,branch(CLOCK_ADD,exports[ENTRY]))]
    result=bytearray(image)
    for at,data in patches:result[at:at+len(data)]=data
    inv=result[:]
    for at,data in patches:inv[at:at+len(data)]=image[at:at+len(data)]
    assert inv==image
    return result,dict(input_sha256=PARENT,prior_owner_sha256=OWNER,source_sha256=owner['source_sha256'],
                       celebration_owner_sha256=CELEBRATION,output_sha256=sha(result),symbols=exports,
                       reused_symbols={k:symbols[k] for k in ('m24s_party_init','m24s_animate','m24s_editor')},
                       linkage=linkage,storage_exports=owner['storage_exports'],prior_excluded_extents=prior,
                       allocations=allocator.allocations,whole_image_inverse=True,builder_sha256=sha(Path(__file__).read_bytes()),
                       writes=[dict(offset=at,size=len(data),before_sha256=sha(image[at:at+len(data)]),
                                    after_sha256=sha(data)) for at,data in sorted(patches)])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('input','owner','celebration-owner','output'):
        p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args()
    image,meta=build(a.input.read_bytes(),a.owner.read_bytes(),a.celebration_owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    dst=a.output/'manifest.json';dst.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8',newline='\n')
    print(meta['output_sha256'],sha(dst.read_bytes()))


if __name__=='__main__':
    main()
