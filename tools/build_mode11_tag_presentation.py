"""Install source-earned score, printable tag and name callbacks into native mode 11."""
import argparse
import json
import struct
from pathlib import Path

import mode11_special_name
import mode11_tag_actors
import mode11_tag_controller
import mode11_tag_graphics
import mode11_tag_resources
from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode23_linker import compose

BEFORE = '78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
OWNER = '0D06FCB9A11A53629FB75B11495043D4A22499E4100153E2FC7EE6B6CDDC4278'
EXPORTS = ('m11_present','m11_controller','m11_begin_card','m11_editor','m11_name_draw',
           'm11_native_exit','m11_irq_off','m11_graphics_clear','m11_transfers',
           'm11_card_asset_table','m11_layout','m11_digits_frame_table','m11_digits_ptr',
           'm11_get_frame0_ptr','m11_get_ptr','m11_name_assets','m11_text','m11_name_text',
           'm11_underscore','m11_retry','m11_tag_audio','m11_tag_audio_ready',
           *mode11_special_name.EXPORTS)


def build(source, before, owner):
    if (sha(source),sha(before),sha(owner)) != (mode11_special_name.SOURCE,BEFORE,OWNER):
        raise ValueError('mode11 tag presentation requires its authenticated rank producer')
    meta=json.loads(owner)
    assert meta['output_sha256']==BEFORE
    start=meta['symbols']['m11_award_result']-BASE
    assert before[start:start+4]==bytes.fromhex('06f028e1')
    extents=meta['prior_excluded_extents']+[[r['start'],r['end']] for r in meta['allocations']]
    allocator=Allocator(before)
    exclude(allocator,extents)
    writes={}
    def place(label, data):
        at=allocator.allocate(len(data),label,4)
        assert before[at:at+len(data)]==b'\xff'*len(data)
        assert all(at+len(data)<=lo or hi<=at for lo,hi in extents)
        writes[at]=data
        return BASE+at
    resources=mode11_tag_resources.resources(source)
    pointers={key:place('mode11 '+key,raw) for key,raw in resources.items()}
    storage=meta['storage_exports']
    bodies=(mode11_tag_controller.assembly(storage['m22_read_snapshot']),mode11_tag_graphics.assembly(pointers),
            mode11_tag_actors.assembly(before,source),
            mode11_special_name.assembly(source,storage['m22_read_snapshot'],storage['m22_write_snapshot']))
    provisional=compose(bodies,BASE,EXPORTS)[0]
    target=place('mode11 score/card/name native callbacks',provisional)
    code,symbols,link=compose(bodies,target,EXPORTS)
    assert len(code)==len(provisional)
    writes[target-BASE]=code
    delta=symbols['m11_present']-(BASE+start+8)
    assert delta%4==0 and -(1<<25)<=delta<1<<25
    writes[start]=struct.pack('<I',0xea000000|((delta//4)&0xffffff))
    image=bytearray(before)
    for offset,raw in writes.items():image[offset:offset+len(raw)]=raw
    inverse=image[:]
    for offset,raw in writes.items():inverse[offset:offset+len(raw)]=before[offset:offset+len(raw)]
    assert inverse==before
    return image,dict(input_sha256=BEFORE,output_sha256=sha(image),prior_owner_sha256=OWNER,
        source_sha256=sha(source),symbols=symbols,linkage=link,storage_exports=storage,
        resource_addresses=pointers,source_resources={k:sha(v) for k,v in resources.items()},
        prior_excluded_extents=extents,allocations=allocator.allocations,
        module_sha256={Path(m.__file__).name:sha(Path(m.__file__).read_bytes()) for m in
                       (mode11_tag_controller,mode11_tag_graphics,mode11_tag_resources,mode11_tag_actors,mode11_special_name)},
        writes=[dict(offset=at,size=len(raw),before_sha256=sha(before[at:at+len(raw)]),after_sha256=sha(raw)) for at,raw in sorted(writes.items())],
        whole_image_inverse=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','input','owner','output'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    image,report=build(a.source.read_bytes(),a.input.read_bytes(),a.owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':main()

