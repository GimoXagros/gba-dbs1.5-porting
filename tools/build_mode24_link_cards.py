"""Register the 1.5 cable tag result screen and preserve each previous mode row."""
import argparse
import json
import struct
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode23_linker import compose
from mode24_link_cards import assembly

SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ENTRIES=('m24_accept_init','m24_write_result','m24_dispatch','m24_init','m24_create','m24_render','m24_controller','m24_exit')
TABLE=0xDB4400
TABLE_POINTERS=(0x15B70,0x15B74,0x15B78,0x15C6C,0x15CC8)
WORD=struct.Struct('<I')


def branch(pc, dest, link=False):
    delta=dest-pc-8
    assert delta%4==0 and -(1<<25)<=delta<(1<<25)
    return WORD.pack(0xea000000|(int(link)<<24)|(delta//4&0xffffff))


def build(before,source,parent_bytes,link_bytes,presentation_bytes,expected):
    parent,link,pres=map(json.loads,(parent_bytes,link_bytes,presentation_bytes))
    assert sha(source)==SOURCE and sha(before)==parent['output_sha256']==expected[0]
    assert [sha(b) for b in (parent_bytes,link_bytes,presentation_bytes)]==expected[1:]
    assert source[0x74FAC0:0x74FAC6]==bytes.fromhex('040000000000')
    assert source[0x785138:0x78513c]==bytes.fromhex('723e7708')
    assert source[0x774036:0x77403f]==bytes.fromhex('c7057000c745025a00')
    data=bytearray(before)
    imports=dict(pres['symbols'])
    imports.update(pres['resource_addresses'])
    imports['reader']=link['storage_exports']['m22_read_snapshot']
    writer=link['storage_exports']['m22_write_snapshot']
    # The component may be installed after user-facing graphics. Confirm that
    # both original executable resource owners still match their actual bytes.
    for ancestor in (link,pres):
        for row in ancestor['allocations']:
            lo,hi=row['start'],row['end']
            approved=[w for w in ancestor['writes'] if w['offset']==lo and w['size']==hi-lo]
            assert len(approved)==1
            span=bytearray(before[lo:hi])
            if ancestor is pres:
                gate=pres['symbols']['m11_tag_audio_ready']-BASE
                if lo<=gate<hi and WORD.unpack_from(span,gate-lo)[0]==1:
                    table_at=WORD.unpack_from(before,0x37c2a4)[0]-BASE
                    assert all(WORD.unpack_from(before,t)[0]-BASE==table_at for t in (0x37c2d8,0x37c324,0x37c378,0x37c3ac))
                    assert all(BASE<=WORD.unpack_from(before,table_at+i*8)[0]<BASE+len(before) for i in range(123,127))
                    WORD.pack_into(span,gate-lo,0)
            if ancestor is pres and 'm11_score_audio' in parent.get('symbols',{}):
                # The immediate score-audio owner replaces this one LDR by
                # a direct branch; its target is itself in the typed parent.
                hook=0xea4840
                if lo<=hook<hi:
                    entry=parent['symbols']['m11_score_audio']
                    assert before[hook:hook+4]==branch(BASE+hook,entry)
                    fix=next(w for w in parent['writes'] if w['offset']==hook and w['size']==4)
                    original=bytes.fromhex('a4059fe5')
                    assert sha(original)==fix['before_sha256'] and sha(before[hook:hook+4])==fix['after_sha256']
                    span[hook-lo:hook-lo+4]=original
            assert sha(span)==approved[0]['after_sha256']
    sym=link['symbols']
    accept=sym['link_tag_accept']+4
    start=sym['link_streak_dispatch']
    assert before[accept-BASE:accept-BASE+4]==WORD.pack(0xe10fb000)
    veneer=next(row['address'] for row in link['linkage']['native_veneers'].values() if row['target']==writer)
    writesites=[at for at in range(accept,start,4) if before[at-BASE:at-BASE+4]==branch(at,veneer,True)]
    assert len(writesites)==1
    writer_call=writesites[0]
    end=next(x for x in link['allocations'] if x['start']<=start-BASE<x['end'])['end']+BASE
    fallback=[at for at in range(start,end,4) if before[at-BASE:at-BASE+4]==WORD.pack(0xe3a00004)]
    assert len(fallback)==1
    fallback=fallback[0]
    body=assembly(imports,dict(accept_resume=accept+4,write_resume=writer_call+4),writer)
    prior=parent['prior_excluded_extents']+[[r['start'],r['end']] for r in parent['allocations']]
    allocator=Allocator(before);exclude(allocator,prior)
    trial=compose((body,),BASE,ENTRIES)[0]
    at=allocator.allocate(len(trial),'mode24 result latch and native card scene',4)
    code,symbols,relocations=compose((body,),BASE+at,ENTRIES)
    assert len(code)==len(trial)
    patches=[(at,code,'mode24 callbacks')]
    patches += [(pc-BASE,branch(pc,symbols[label]),label) for pc,label in ((accept,'m24_accept_init'),(writer_call,'m24_write_result'),(fallback,'m24_dispatch'))]
    old=before[TABLE:TABLE+24*22]
    table=old[:288]+struct.pack('<3I',symbols['m24_init'],symbols['m24_create'],0x080159B0)
    table+=old[288:384]+WORD.pack(0x08015B40)+old[384:]+source[0x74FAC0:0x74FAC6]
    assert len(table)==25*22
    target=allocator.allocate(len(table),'25 normal mode dispatch and transition rows',4)
    patches.append((target,table,'native callback, exit and transition tables'))
    for site,old_offset,new_offset in zip(TABLE_POINTERS,(0,4,8,288,384),(0,4,8,300,400)):
        prev=WORD.pack(BASE+TABLE+old_offset)
        assert before.count(prev)==1 and before[site:site+4]==prev
        patches.append((site,WORD.pack(BASE+target+new_offset),'original mode table reader'))
    for at,raw,_ in patches:
        data[at:at+len(raw)]=raw
    inverse=data[:]
    for at,raw,_ in patches:inverse[at:at+len(raw)]=before[at:at+len(raw)]
    assert inverse==before
    entries=[dict(offset=at,size=len(raw),purpose=why,before_sha256=sha(before[at:at+len(raw)]),after_sha256=sha(raw)) for at,raw,why in sorted(patches)]
    return data,dict(input_sha256=expected[0],prior_owner_sha256=expected[1],link_owner_sha256=expected[2],
                     presentation_owner_sha256=expected[3],output_sha256=sha(data),source_sha256=SOURCE,
                     table=BASE+target,symbols=symbols,linkage=relocations,storage_exports=parent['storage_exports'],
                     allocations=allocator.allocations,prior_excluded_extents=prior,writes=entries,whole_image_inverse=True,
                     modules={Path(__file__).name:sha(Path(__file__).read_bytes()),'mode24_link_cards.py':sha(Path(__file__).with_name('mode24_link_cards.py').read_bytes())})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','source','owner','link-owner','presentation-owner','output'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('input','owner','link-owner','presentation-owner'):
        p.add_argument('--'+name+'-sha256',required=True)
    a=p.parse_args()
    raw,meta=build(a.input.read_bytes(),a.source.read_bytes(),a.owner.read_bytes(),a.link_owner.read_bytes(),
                   a.presentation_owner.read_bytes(),[a.input_sha256,a.owner_sha256,a.link_owner_sha256,a.presentation_owner_sha256])
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(raw)
    manifest=a.output/'manifest.json'
    manifest.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8',newline='\n')
    print(meta['output_sha256'],sha(manifest.read_bytes()))


if __name__=='__main__':
    main()
