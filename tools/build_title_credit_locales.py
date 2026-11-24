"""Install three localized title credit strips in the two existing title background loaders."""
import argparse
import json
import struct
from pathlib import Path
from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_options_korean_poc import FONT_SHA, font_glyphs
from build_poc import convert_planar_tile
from build_stage_assets import convert_map
from build_title_background import MAP, TILES1, TILES2, SOURCE, PALETTE, branch
from convert_wsc_palette_block import convert_color
from encode_digicode_reading import CATALOG
from mode23_compact_menu_digicode import compact_text
from mode23_linker import compose

KOREAN = ('혼고 아키요시', '도에이 애니메이션')
READING = ('ほんごうあきよし', 'とうえいアニメーシヨン')
FIRST = 0x2E5
COUNT = 38

def strip_pixels(word, tiles, cells):
    pixels = {}
    for y in range(120,136):
        for x in range(40,200):
            c = cells[y//8*28 + x//8]
            sx,sy = (7-x%8 if c&1024 else x%8),(7-y%8 if c&2048 else y%8)
            n = (tiles[((c&1023)-400)*32+sy*4+sx//2] >> (sx%2*4))&15
            pixels[x,y] = word(c>>12,n)
    return pixels

def credits(before, source, font):
    assert sha(source)==SOURCE and sha(font)==FONT_SHA
    tilemap = struct.unpack_from('<504H',before,MAP)
    tiles = before[TILES1:TILES1+8192]+before[TILES2:TILES2+4864]
    palette = struct.unpack_from('<16H',before,PALETTE+128)
    ids = [tilemap[y*28+x] for y in (15,16) for x in range(5,24)]
    assert ids==list(range(0x5000+FIRST,0x5000+FIRST+COUNT))
    assert all(sum(1 for c in tilemap if (c&1023)==(v&1023))==1 for v in ids)
    original = strip_pixels(lambda _,n:n,tiles,tilemap)
    base = 0x4A80C0
    alt_cells=struct.unpack('<504H',convert_map(source[base+0x36F0:base+0x36F0+1008]))
    alt_tiles=b''.join(convert_planar_tile(source[p:p+32]) for p in range(base+0x3AE0,base+0x6DE0,32))
    alt_pal=struct.unpack_from('<96H',source,base+0x6D60)
    alt=strip_pixels(lambda p,n:convert_color(alt_pal[(p-1)*16+n]),alt_tiles,alt_cells)
    # Remove the Japanese glyphs and their navy edge with exposed backdrop from the English artwork.
    # Where both original captions cover a pixel, continue the nearest visible backdrop color.
    background=original.copy()
    uncertain=[]
    for y in range(120,132):
        for x in range(53,192):
            if original[x,y] in (8,15):
                c=alt[x,y]
                if c in palette[1:8]:
                    background[x,y]=palette.index(c)
                elif c==0:
                    background[x,y]=8
                else:
                    uncertain.append((x,y))
    seeds=[(x,y,v) for (x,y),v in background.items() if 53<=x<192 and 120<=y<133 and v in range(1,8)]
    for x,y in uncertain:
        background[x,y]=min(seeds,key=lambda p:(x-p[0])**2+(y-p[1])**2)[2]
    # English extends one cell past the Japanese line. This tile has no other map references.
    assert tilemap[15*28+24]==0x329D and sum((c&1023)==0x29D for c in tilemap)==1
    def distance(a,b):
        return sum(((a>>s&31)-(b>>s&31))**2 for s in (0,5,10))
    def english_color(x,y):
        c=alt[x,y]
        return min(range(1,16),key=lambda n:distance(palette[n],c))
    ko_font=font_glyphs(font,set(''.join(KOREAN)))
    catalog=json.loads(CATALOG.read_bytes())
    def label(words,digi):
        result=set()
        cursor=55 if digi else 54
        for j,word in enumerate(words):
            if j:
                result.update((cursor+dx,125+dy) for dx in (0,1) for dy in (0,1))
                cursor+=5
            if digi:
                pts,width=compact_text(word,catalog)
                result.update((cursor+x,126+y) for x,y in pts)
                cursor+=width+2
            else:
                for ch in word:
                    advance,points=ko_font[ch]
                    result.update((cursor+x,132+y) for x,y in points)
                    cursor+=advance+1
        return result
    def pack(grid,columns,rows):
        return bytes(grid[x+i,y+j] | grid[x+i+1,y+j]<<4
            for y in rows for x in columns for j in range(8) for i in (0,2,4,6))
    english=original.copy()
    for y in range(120,132):
        for x in range(40,200):
            english[x,y]=english_color(x,y)
    assert all((english[x,y]==15)==(alt[x,y]==0x7fff) for y in range(120,130) for x in range(40,200))
    output={'en':pack(english,range(40,192,8),(120,128))+pack(english,(192,),(120,))}
    for lang,ink in (('ko',label(KOREAN,False)),('dg',label(READING,True))):
        assert min(x for x,y in ink)>=52 and max(x for x,y in ink)<=190
        assert min(y for x,y in ink)>=120 and max(y for x,y in ink)<=131
        grid=background.copy()
        for x,y in ink:
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    if 120<=y+dy<133 and x+dx>=52: grid[x+dx,y+dy]=8
        grid.update(dict.fromkeys(ink,15))
        output[lang]=pack(grid,range(40,192,8),(120,128))
        assert len(output[lang])==COUNT*32
        assert all(grid[x,y]==original[x,y] for x in range(40,192) for y in range(133,136))
    return output

def build(before, source, font, parent):
    assert sha(before)==parent['output_sha256']
    prior=parent['prior_excluded_extents']+[[r['start'],r['end']] for r in parent['allocations']]
    allocator=Allocator(before)
    exclude(allocator,prior)
    writes=[]
    pointers={}
    for lang,data in credits(before,source,font).items():
        at=allocator.allocate(len(data),lang+' title copyright tiles',4)
        pointers[lang]=BASE+at
        writes.append((at,data,lang+' credit tiles'))
    ab=f"""
title_credit:
    push {{lr}}
    bl 0x08000b84
    push {{r0,r1,r2,r4,r5,r8,r12}}
    mrs r1,cpsr
    ldr r0,=0x0300112f
    ldrb r0,[r0]
    cmp r0,#0xa1
    beq title_credit_done
    cmp r0,#0xa2
    ldreq r4,={pointers['ko']}
    beq title_credit_copy
    cmp r0,#0xa3
    ldreq r4,={pointers['dg']}
    ldrne r4,={pointers['en']}
title_credit_copy:
    ldr r5,={0x06000000+FIRST*32}
    mov r2,#{COUNT*8}
    bl 0x08000b84
    cmp r0,#0xa2
    beq title_credit_done
    cmp r0,#0xa3
    beq title_credit_done
    ldr r5,=0x060053a0
    mov r2,#8
    bl 0x08000b84
    ldr r0,[sp,#28]
    ldr r4,=0x080406ec
    cmp r0,r4
    ldreq r5,=0x0600fbf0
    ldreq r4,=0x529d
    strheq r4,[r5]
title_credit_done:
    msr cpsr_f,r1
    pop {{r0,r1,r2,r4,r5,r8,r12}}
    pop {{lr}}
    bx lr
title_credit_map:
    push {{r0,r1,r4}}
    mrs r1,cpsr
    ldr r0,=0x0300112f
    ldrb r0,[r0]
    sub r0,r0,#0xa1
    cmp r0,#2
    ldrhi r0,=0x0600f3f0
    ldrhi r4,=0x529d
    strhhi r4,[r0]
    msr cpsr_f,r1
    pop {{r0,r1,r4}}
    mov r8,#0
    b 0x0809095c
.ltorg
"""
    labels=('title_credit','title_credit_map')
    trial=compose([ab],0x08f00000,labels)[0]
    at=allocator.allocate(len(trial),'title credit language dispatch',4)
    code,symbols,_=compose([ab],BASE+at,labels)
    assert len(code)==len(trial)
    writes.append((at,code,'localized second title DMA'))
    for site in (0x6FC2B4,0xD8B41C):
        assert before[site:site+4]==branch(site,BASE+0xB84)
        writes.append((site,branch(site,BASE+at),'title loader'))
    assert before[0x90958:0x9095c]==bytes.fromhex('0080a0e3')
    writes.append((0x90958,branch(0x90958,symbols['title_credit_map']),'ordinary English credit map edge'))
    out=bytearray(before)
    for p,v,_ in writes: out[p:p+len(v)]=v
    inverse=out[:]
    for p,v,_ in writes: inverse[p:p+len(v)]=before[p:p+len(v)]
    assert inverse==before
    return out,dict(input_sha256=sha(before),output_sha256=sha(out),prior_excluded_extents=prior,
        allocations=allocator.allocations,storage_exports=parent['storage_exports'],credit_tiles=pointers,
        writes=[dict(offset=p,size=len(v),purpose=k,before_sha256=sha(before[p:p+len(v)]),after_sha256=sha(v)) for p,v,k in writes],
        source_sha256=sha(source),font_sha256=sha(font),whole_image_inverse=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for a in ('input','owner','source','font','output'): p.add_argument('--'+a,type=Path,required=True)
    a=p.parse_args()
    raw=a.owner.read_bytes()
    image,meta=build(a.input.read_bytes(),a.source.read_bytes(),a.font.read_bytes(),json.loads(raw))
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(image)
    meta.update(prior_owner_sha256=sha(raw),builder_sha256=sha(Path(__file__).read_bytes()))
    path=a.output/'manifest.json'
    path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(meta['output_sha256'],sha(path.read_bytes()))
