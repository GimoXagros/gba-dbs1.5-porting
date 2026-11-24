"""Connect the saved win counter and highest-rank emblem to the pre-Start title screen."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color
from mode23_linker import compose
from title_tag_badge import assembly

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
HOOKS = ((0x90C30,0xE1C400B0,'title_badge_init'),(0x90DB4,0xE59F8090,'title_badge_draw'),
         (0x90DB0,0xEA000010,'title_badge_exit'),(0x90D34,0xEA00002F,'title_badge_exit'))


def build(before, source, parent):
    assert sha(source)==SOURCE and sha(before)==parent['output_sha256']
    assert source[0x7803F5:0x7803FC]==b'WIN[S]\0'
    assert source[0x780326:0x780333]==bytes.fromhex('268b85e6003de7037603b8e703')
    offset=0x2D9360
    tile_refs=struct.unpack_from('<11H',source,0x780288)
    pal_refs=struct.unpack_from('<11H',source,0x78029E)
    assert tile_refs==tuple(i*896 for i in range(11)) and pal_refs==tuple(0x3680+i*32 for i in range(11))
    prior=parent['prior_excluded_extents']+[[r['start'],r['end']] for r in parent['allocations']]
    allocator=Allocator(before)
    exclude(allocator,prior)
    reader=parent['storage_exports']['m22_read_snapshot']
    spans=[]
    references={}
    def asset(label,data):
        # Existing translated viewer assets are safe to share only within an explicitly owned extent.
        for start,end in prior:
            at=before.find(data,start,end)
            if at!=-1 and at%4==0:
                references[label]=BASE+at
                return BASE+at
        at=allocator.allocate(len(data),label,4)
        spans.append((at,data,label))
        references[label]=BASE+at
        return BASE+at
    def tiles(raw,size):
        return b''.join(convert_tile(source[i:i+32]) for i in range(raw,raw+size,32))
    def pal(raw):
        values=struct.unpack_from('<16H',source,raw)
        assert max(values)<4096
        return struct.pack('<16H',*(convert_color(v) for v in values))
    badges=[asset('badge-tiles-'+str(i),tiles(offset+p,896)) for i,p in enumerate(tile_refs)]
    colors=[asset('badge-palette-'+str(i),pal(offset+p)) for i,p in enumerate(pal_refs)]
    font=asset('counter-font',tiles(0x43E9C0,0x800))
    palette=asset('counter-palette',pal(0x43F1C0))
    body=assembly(reader,badges,colors,font,palette)
    names=('title_badge_init','title_badge_draw','title_badge_exit')
    trial=compose([body],0x08F00000,names)[0]
    code_at=allocator.allocate(len(trial),'title pre-Start badge',4)
    code,symbols,_=compose([body],BASE+code_at,names)
    assert len(code)==len(trial)
    spans.append((code_at,code,'badge-controller'))
    for at,old,label in HOOKS:
        assert struct.unpack_from('<I',before,at)[0]==old
        displacement=symbols[label]-BASE-at-8
        assert displacement%4==0 and -0x2000000<=displacement<0x2000000
        spans.append((at,struct.pack('<I',0xea000000|(displacement//4&0xffffff)),label))
    out=bytearray(before)
    entries=[]
    for at,data,label in spans:
        entries.append(dict(offset=at,size=len(data),purpose=label,before_sha256=sha(before[at:at+len(data)]),after_sha256=sha(data)))
        out[at:at+len(data)]=data
    inverse=out[:]
    for at,data,_ in spans: inverse[at:at+len(data)]=before[at:at+len(data)]
    assert inverse==before and all(before[r['start']:r['end']]==b'\xff'*(r['end']-r['start']) for r in allocator.allocations)
    return out,dict(input_sha256=sha(before),output_sha256=sha(out),source_sha256=SOURCE,storage_exports=parent['storage_exports'],
                    symbols=symbols,assets=references,writes=entries,allocations=allocator.allocations,prior_excluded_extents=prior,whole_image_inverse=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','source','owner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    owner=args.owner.read_bytes()
    image,manifest=build(args.input.read_bytes(),args.source.read_bytes(),json.loads(owner))
    manifest.update(prior_owner_sha256=sha(owner),builder_sha256=sha(Path(__file__).read_bytes()),
                    controller_sha256=sha(Path(__file__).with_name('title_tag_badge.py').read_bytes()))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'component.gba').write_bytes(image)
    path=args.output/'manifest.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(manifest['output_sha256'],sha(path.read_bytes()))
