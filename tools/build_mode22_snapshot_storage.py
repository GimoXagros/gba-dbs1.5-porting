"""Allocate the typed Tamer Tag save services on the source-ending development image."""
import argparse
import json
import struct
from pathlib import Path
from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode22_snapshot_storage import assemble

BEFORE='2A7E8296DDD1DB3898CF3484E5849E623066A6249D3F70B090374956213CD083'
OWNER='29B914EF1CD8403C70B5C92A8CF9478E40B0014DAC41CD8FCB9F7F181AC11505'

def check_device(image):
    assert struct.unpack_from('<IHHB',image,0x3877D0)==(512,64,0x300,6)
    callers={0x0837DB60:[],0x0837DB54:[]}
    for i,(word,) in enumerate(struct.iter_unpack('<I',image)):
        if word & 0x0E000000==0x0A000000:
            target=BASE+8+i*4+4*((word&0x7FFFFF)-(word&0x800000))
            if target in callers:callers[target].append(i*4)
    assert callers=={0x0837DB60:[0x1FCC0,0x629828,0x629850],0x0837DB54:[0x1FC7C,0x629844,0x62986C]}
    for target,at in [(0x0837DB60,0xD8D2E4),(0x0837DB54,0xD8D2DC),(0x0837D7E5,0x37DB68),(0x0837D9C9,0x37DB5C)]:
        needle=struct.pack('<I',target)
        assert image.find(needle)==image.rfind(needle)==at

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('before','owner','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    image=args.before.read_bytes();owner=args.owner.read_bytes()
    assert sha(image)==BEFORE and sha(owner)==OWNER
    check_device(image)
    meta=json.loads(owner)
    prior=meta['prior_excluded_extents']+[[r['start'],r['end']]for r in meta['allocations']]
    allocator=Allocator(image)
    exclude(allocator,prior)
    size=len(assemble(0x08f00000)[0])
    offset=allocator.allocate(size,'mode22 EEPROM record reader and writer',4)
    code,symbols,_=assemble(BASE+offset)
    assert len(code)==size and image[offset:offset+size]==bytes([255])*size
    assert all(offset+size<=a or b<=offset for a,b in prior)
    after=image[:offset]+code+image[offset+size:]
    record=dict(input_sha256=BEFORE,output_sha256=sha(after),builder_sha256=sha(Path(__file__).read_bytes()),
        module_sha256=sha(Path(__file__).with_name('mode22_snapshot_storage.py').read_bytes()),
        prior_owner_sha256=OWNER,prior_excluded_extents=prior,allocations=allocator.allocations,
        exports=symbols,blocks=list(range(27,34)),writes=[[offset,size]],new_global_RAM_bytes=0,
        invoked_in_game=False,limits=['Read and verified write services only. Consumers and reset need separate hooks.'])
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'component.gba').write_bytes(after)
    path=args.output/'manifest.json'
    path.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(record['output_sha256'],sha(path.read_bytes()),{k:hex(v)for k,v in symbols.items()})
if __name__=='__main__':main()
