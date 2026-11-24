"""Use localized lettering for the ordinary empty Collection message in KO and Digicode."""
import argparse
import json
import struct
from pathlib import Path
from build_character_select_name_scene import Allocator,BASE,exclude,sha
from build_options_korean_poc import FONT_SHA,font_glyphs,pack_tile
from digicode_glyphs import font_glyphs as digi_font,text_pixels as digi_pixels
from encode_digicode_reading import CATALOG
from mode23_linker import compose

KO = '태그가 없습니다'
JA_SOURCE = 'YOU HAVE NO TAGS'
HOOK = 0xF7AA88


def cells(font,language):
    if language=='ko':
        glyphs=font_glyphs(font,set(KO))
        ink=set()
        width=0
        for ch in KO:
            advance,body=glyphs[ch]
            ink.update((x+width,y) for x,y in body)
            width+=advance+1
    else:
        catalog=json.loads(CATALOG.read_bytes())
        glyphs=digi_font(catalog)
        ink=set()
        width=0
        for word in JA_SOURCE.split():
            pixels,advance=digi_pixels(word,catalog,glyphs,outline=False)
            ink.update((x+width,y) for x,y in pixels)
            width+=advance+4
    left,top=min(x for x,y in ink),min(y for x,y in ink)
    width=max(x for x,y in ink)-left+1
    height=max(y for x,y in ink)-top+1
    # Center against the original 224x144 viewport and the source text center (112,68).
    ink={(x-left+(224-width)//2,y-top+68-height//2) for x,y in ink}
    top=min(y for x,y in ink)
    pixels={(x+dx,y+dy):1 for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}
    for x,y in ink:
        pixels[x,y]=2+min(3,(y-top)*4//height)
    x0=min(x for x,y in pixels)//8
    y0=min(y for x,y in pixels)//8
    cols=max(x for x,y in pixels)//8-x0+1
    rows=max(y for x,y in pixels)//8-y0+1
    assert 0<=x0<x0+cols<=28 and 0<=y0<y0+rows<=18 and cols*rows<=64
    tiles=b''.join(pack_tile(pixels,8*x,8*y) for y in range(y0,y0+rows) for x in range(x0,x0+cols))
    return tiles,struct.pack('<'+'H'*(cols*rows),*(0x8001+i for i in range(cols*rows))),(x0,y0,cols,rows)


def build(before,font,parent):
    assert sha(before)==parent['output_sha256'] and sha(font)==FONT_SHA
    assert before[HOOK:HOOK+8]==bytes.fromhex('000090e5c8109fe5')
    assert before[0xF7AB88:0xF7AB90]==bytes.fromhex('f0412de90040a0e1')
    prior=parent['prior_excluded_extents']+[[a['start'],a['end']] for a in parent['allocations']]
    allocator=Allocator(before)
    exclude(allocator,prior)
    writes=[]
    blocks=[]
    for lang in ('ko','digicode'):
        tiles,tilemap,(x,y,w,h)=cells(font,lang)
        at=allocator.allocate(len(tiles)+len(tilemap),lang+' empty tag glyphs',4)
        writes.append((at,tiles+tilemap,lang+' message'))
        blocks.append(f'.word {BASE+at},0x06000020,{len(tiles)//2},1,{BASE+at+len(tiles)},{0x0600F800+y*64+x*2},{w},{h},0')
    body=f"""
empty_locale:
    cmp r5,#1
    bne empty_original
    ldr r1,=0x0300112f
    ldrb r1,[r1]
    cmp r1,#0xa2
    beq empty_ko
    cmp r1,#0xa3
    bne empty_original
    adr r0,empty_dg_copy
    b empty_copy
empty_ko:
    adr r0,empty_ko_copy
empty_copy:
    bl 0x08f7ab88
    b 0x08f7aab0
empty_original:
    ldr r0,[r0]
    b 0x08f7aa8c
.ltorg
empty_ko_copy:
{blocks[0]}
empty_dg_copy:
{blocks[1]}
"""
    trial=compose([body],0x08f00000,('empty_locale',))[0]
    at=allocator.allocate(len(trial),'mode22 localized empty text',4)
    code,_,_=compose([body],BASE+at,('empty_locale',))
    assert len(code)==len(trial)
    writes.extend([(at,code,'text dispatch'),(HOOK,struct.pack('<I',0xea000000|((at-HOOK-8)//4&0xffffff)),'empty selection')])
    out=bytearray(before)
    for pos,val,_ in writes: out[pos:pos+len(val)]=val
    inverse=out[:]
    for pos,val,_ in writes: inverse[pos:pos+len(val)]=before[pos:pos+len(val)]
    assert inverse==before
    return out,dict(input_sha256=sha(before),output_sha256=sha(out),prior_excluded_extents=prior,allocations=allocator.allocations,
        writes=[dict(offset=p,size=len(v),purpose=label,before_sha256=sha(before[p:p+len(v)]),after_sha256=sha(v)) for p,v,label in writes],
        storage_exports=parent['storage_exports'],whole_image_inverse=True,korean=KO,digicode_reading=JA_SOURCE,
        font_sha256=sha(font),digicode_catalog_sha256=sha(CATALOG.read_bytes()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('input','owner','font','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    owner=args.owner.read_bytes()
    image,manifest=build(args.input.read_bytes(),args.font.read_bytes(),json.loads(owner))
    manifest.update(prior_owner_sha256=sha(owner),builder_sha256=sha(Path(__file__).read_bytes()))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'component.gba').write_bytes(image)
    path=args.output/'manifest.json'
    path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    print(manifest['output_sha256'],sha(path.read_bytes()))
