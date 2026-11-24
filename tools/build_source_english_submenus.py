"""Install WSC 1.5's alternate English submenu graphics in the owned USA title atlas."""
import argparse
import json
import struct
from pathlib import Path

from build_mode23_title_assets_r4 import BASE, native_frames, native_pixels, pack, tile_layouts
from build_title_language import parse_wsc_far_descriptor
from build_full_asset_poc import convert_tile
from render_wsc_asset_frames import layout_frames
from verify_character_select_name_scene import sha

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = 'F61053394798E4529F45A75E8363791EC8777774681F0B7354A69966EF780E3B'
TITLE_OWNER = '91618BDC7A28BB36A829AABDD19271CDCB66747B305917E5174968AC38D9F412'


def english_source(source):
    assert sha(source) == SOURCE
    # Japan 1.5 fixes the language to zero, but the alternate branch retains its
    # own complete eleven-event bank. Follow that branch's P0/P1/P2 arguments.
    assert source[0x780148:0x780151] == bytes.fromhex('33c033c03d00007551')
    assert source[0x7801C1:0x7801DC] == bytes.fromhex(
        '68bd0068f12768000068bc00683d2468000068bd0068b723680000')
    layouts = layout_frames(source,0x3C43D0)
    segment,bank = struct.unpack_from('<HH',source,0x3C43D4)
    descriptor = ((bank&127)<<16)+(segment-0x2000)*16
    size,start = parse_wsc_far_descriptor(source,descriptor)
    assert (descriptor,size,start,len(layouts)) == (0x3D8EA0,0x1180,0x3974C0,11)
    tiles = [convert_tile(source[i:i+32]) for i in range(start,start+size,32)]
    return [native_pixels([(tile,y,x) for tile,x,y in parts],tiles) for parts in layouts]


def build(before,source,owner_raw):
    assert sha(before)==BEFORE and sha(owner_raw)==TITLE_OWNER
    title=json.loads(owner_raw)
    bank=title['asset_pointers']['english_p0']
    raw=bank-BASE
    span=next(r for r in title['writes'] if r['label']=='title-english_p0')
    assert span['offset']==raw and sha(before[raw:raw+span['size']])==span['after_sha256']
    retained=native_frames(before,0x8FD08)
    source_frames=english_source(source)
    frames=retained+source_frames[5:]
    for frame in frames[1:]:
        assert all(frame.get((x,y))==retained[1].get((x,y)) for x in range(-44,-27) for y in range(-8,8))
    layouts,tiles=tile_layouts(frames)
    atlas=pack(layouts,tiles,bank)
    assert len(atlas)<=span['size'] and [len(p) for p in layouts]==[8]+[22]*10
    # Keep both the existing entry point and the complete reserved extent.
    after=before[:raw]+atlas+before[raw+len(atlas):]
    assert len(after)==len(before) and after[:raw]+before[raw:raw+len(atlas)]+after[raw+len(atlas):]==before
    return after, dict(input_sha256=BEFORE,source_sha256=SOURCE,output_sha256=sha(after),
        builder_sha256=sha(Path(__file__).read_bytes()),existing_owner_sha256=TITLE_OWNER,
        title_p0=bank,source_p0=0x3C43D0,source_tile_start=0x3974C0,
        retained_events=list(range(5)),source_events=list(range(5,11)),
        write=[raw,len(atlas)],owned_extent=[raw,span['size']],parts=[len(p)for p in layouts],
        changed_bytes=sum(a!=b for a,b in zip(before[raw:raw+len(atlas)],atlas)),whole_image_inverse=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','source','title-owner','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    after,meta=build(a.input.read_bytes(),a.source.read_bytes(),a.title_owner.read_bytes())
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(after)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(meta['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':
    main()
