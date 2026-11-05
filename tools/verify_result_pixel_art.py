#!/usr/bin/env python3
"""Independent source-pixel, native-tile and image checks for isolated result art.

No art builder or project font helper is imported; no image or ROM is written.
Native-size Hangul readability still requires the separately recorded visual review.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import argparse
import json
import struct
from PIL import Image

def digest(data):
    return sha256(data).hexdigest().upper()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read(data, offset, fmt):
    size = struct.calcsize(fmt)
    assert 0 <= offset <= len(data) - size
    return struct.unpack_from(fmt, data, offset)


def compose(parts, tiles, planar=False):
    pixels = {}
    for flags, top, left in parts:
        assert flags & 0x3F00 == 0x400
        tile = tiles[flags & 255]
        assert len(tile) == 32 and -128 <= top <= 127 and -128 <= left <= 127
        for y in range(8):
            for x in range(8):
                sx, sy = (7 - x if flags & 0x4000 else x), (7 - y if flags & 0x8000 else y)
                if planar:
                    color = sum(((tile[sy * 4 + bit] >> (7 - sx)) & 1) << bit for bit in range(4))
                else:
                    color = (tile[sy * 4 + sx // 2] >> (4 * (sx % 2))) & 15
                if color:
                    pixels.setdefault((left + x, top + y), color)
    return pixels


def summary(pixels):
    return {"bounds": [min(x for x, y in pixels), min(y for x, y in pixels),
                       max(x for x, y in pixels), max(y for x, y in pixels)],
            "pixels": len(pixels), "palette_counts": dict(sorted(Counter(pixels.values()).items())),
            "pixel_sha256": digest(b"".join(struct.pack("<hhB", x, y, v) for (x, y), v in sorted(pixels.items())))}


def source_frames(data):
    p0 = 0x3CB870
    assert read(data, p0, "<I") == (16,)
    segment, bank = read(data, p0 + 4, "<HH")
    mask = len(data) // 65536 - 1
    desc = (bank & mask) * 65536 + segment * 16 - 0x20000
    size, offset, segment, bank = read(data, desc, "<4H")
    start = (bank & mask) * 65536 + segment * 16 + offset - 0x20000
    assert (desc, start, size) == (0x3D8E80, 0x3A0000, 0xCC0)
    tiles = [data[a:a + 32] for a in range(start, start + size, 32)]
    arrays = []
    for index in range(16):
        count, offset = read(data, p0 + 16 + index * 4, "<HH")
        arrays.append([read(data, p0 + offset + i * 4, "<Hbb") for i in range(count)])
    return arrays, [compose(parts, tiles, planar=True) for parts in arrays]


def native_frames(data):
    table, desc = read(data, 0xB8210, "<II")
    size, start = read(data, desc - 0x08000000, "<II")
    start -= 0x08000000
    tiles = [data[a:a + 32] for a in range(start, start + size, 32)]
    arrays = []
    for index in range(15):
        count, address = read(data, table - 0x08000000 + index * 8, "<II")
        arrays.append([read(data, address - 0x08000000 + i * 4, "<Hbb") for i in range(count)])
    return arrays, tiles, [compose(parts, tiles) for parts in arrays]


def exported(frame, maximum):
    assert 0 < len(frame['parts']) <= maximum
    tiles=[bytes.fromhex(value) for value in frame['tiles_4bpp_hex']]
    assert 0 < len(tiles) <= 256
    pixels=compose(frame['parts'],tiles)
    serialized={(x,y):color for x,y,color in frame['pixels']}
    assert len(serialized)==len(frame['pixels']) and pixels==serialized
    assert summary(pixels)['bounds']==frame['bounds']
    assert summary(pixels)['pixel_sha256']==frame['palette_pixel_sha256']
    return pixels


def korean_contract(pixels,punctuation):
    assert {p:c for p,c in pixels.items() if p[0]>=42}==punctuation
    assert not any(x in (40,41) for x,y in pixels)
    body={p:c for p,c in pixels.items() if p[0]<40}
    assert body and set(body.values()) <= {6,7,8,9,10,12}
    assert all(-51<=x<=39 and -8<=y<=7 for x,y in body)
    ink={p for p,c in body.items() if c!=12}
    assert all(-50<=x<=38 and -7<=y<=6 for x,y in ink)
    outline={(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}-ink
    assert {p for p,c in body.items() if c==12}==outline
    return {'body_ink_pixels':len(ink),'body_outline_pixels':len(outline),
            'complete_one_pixel_outline':True,'punctuation_pixels':len(punctuation),
            'punctuation_exact':True,'clear_columns':[40,41]}


def glyph_contract(pixels,authoring,mask_path):
    ink={p for p,c in pixels.items() if p[0]<40 and c!=12}
    bounds=((-50,-7,-37,6),(-33,-7,-20,6),(-16,-7,-3,6),(5,-7,18,6),(23,-7,36,6))
    assert list(authoring['glyphs'])==list('마지막기회')
    union=set()
    for char,bound in zip('마지막기회',bounds):
        points=set(map(tuple,authoring['glyphs'][char]['ink']))
        assert summary({p:1 for p in points})['bounds']==list(bound)
        assert not union&points;union.update(points)
    assert union==ink
    holes={'마':{(x,y) for x in (-47,-46) for y in range(-4,4)},
           '막':{(x,y) for x in (-13,-12) for y in range(-4,-1)},
           '회':{(x,y) for x in range(25,30) for y in (-1,0)}}
    assert all(point not in pixels for points in holes.values() for point in points)
    # Independently reviewed final ㄱ, lower ㅗ and separate right ㅣ.
    assert {(x,y) for x in range(-16,-3) for y in (4,5)}|{(-5,6),(-4,6)} <= ink
    assert {(27,4),(28,4)}|{(x,y) for x in range(23,32) for y in (5,6)} <= ink
    assert {(x,y) for x in (35,36) for y in range(-7,7)} <= ink
    assert all((x,y) not in pixels for x in range(-1,4) for y in range(-8,8))
    with Image.open(mask_path) as image:
        mask=image.convert('L');assert mask.size==(102,16)
        assert all(mask.getpixel((x,y))==(255 if (x-51,y-8) in ink else 0)
                   for y in range(16) for x in range(102))
    return {'word_gap_clear_columns':list(range(-1,4)),
            'counter_transparent_pixels':{char:len(points) for char,points in holes.items()},
            'authored_ink_mask_exact':True,'final_giyeok_and_hoe_components_present':True}


def image_contract(path,pixels,palette,bounds,scale):
    left,top,right,bottom=bounds
    with Image.open(path) as image:
        rgba=image.convert('RGBA')
        assert rgba.size==((right-left+1)*scale,(bottom-top+1)*scale)
        for y in range(rgba.height):
            for x in range(rgba.width):
                color=rgba.getpixel((x,y));assert color[3] in (0,255)
                value=pixels.get((left+x//scale,top+y//scale),0)
                assert color[3]==(255 if value else 0)
                if value:assert color[:3]==palette[value]
    return {'path':str(path),'sha256':digest(path.read_bytes()),'scale':scale,
            'exact_pixel_grid':True,'binary_alpha':True,'native_palette':True}


def self_check():
    assert compose([(0x400,0,0)],[bytes([0x21])+bytes(31)])=={(0,0):1,(1,0):2}
    assert compose([(0xC400,0,0)],[bytes([0x21])+bytes(31)])=={(7,7):1,(6,7):2}
    assert compose([(0x400,0,0)],[bytes([0x80,0x40,0,0])+bytes(28)],True)=={(0,0):1,(1,0):2}
    assert compose([(0x400,0,0),(0x401,0,0)],[bytes([1])+bytes(31),bytes([2])+bytes(31)])=={(0,0):1}


def main():
    p=argparse.ArgumentParser()
    for name in ('art','gba','wsc15','digicode_image','korean_1x','korean_8x','output'):
        p.add_argument(name,type=Path)
    args=p.parse_args()
    if args.output.exists():p.error('refusing to overwrite existing QA evidence')
    self_check()
    gba=args.gba.read_bytes();wsc=args.wsc15.read_bytes()
    assert digest(gba)=='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
    assert digest(wsc)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert digest(args.digicode_image.read_bytes())=='7ED62F223587B4AEFE82ACA425F5D2B336548D3299DFA31D5E818225E7714D50'
    _,source=source_frames(wsc);native_parts,_,native=native_frames(gba)
    assert source[2:14]==native[2:14]
    words=read(gba,0xB914A,'<16H');original=read(wsc,0x3D7EB6,'<16H')
    converted=tuple(sum((2*((word>>shift)&15)+bool((word>>shift)&15))<<(5*i)
                        for i,shift in enumerate((8,4,0))) for word in original)
    assert converted==words
    palette=[tuple(((word>>shift)&31)*255//31 for shift in (0,5,10)) for word in words]
    art=load(args.art);assert art['native_palette_rgb888']==[list(c) for c in palette]
    japanese=[]
    assert len(art['japanese_common'])==2
    for frame,index in zip(art['japanese_common'],(0,1)):
        pixels=exported(frame,len(native_parts[index]));assert pixels==source[index]
        japanese.append({**summary(pixels),'parts':len(frame['parts']),'source_exact':True})
    dg=exported(art['digicode'],len(native_parts[14]));assert len(dg)==631
    image_contract(args.digicode_image,dg,palette,[-32,-8,31,7],16)
    ko=exported(art['korean'],len(native_parts[14]))
    punctuation={point:color for point,color in source[14].items() if point[0]>=42}
    assert len(punctuation)==65
    assert summary(punctuation)['pixel_sha256']=='26FD7DA7F10AF046A9401EF3385AA891026C5E69F7B59E3C0A45CBFAE18761B8'
    korean=korean_contract(ko,punctuation)
    korean.update(glyph_contract(ko,art['korean_authoring'],args.art.parent/'korean-ink-mask-1x.png'))
    images=[image_contract(path,ko,palette,[-51,-8,50,7],scale)
            for path,scale in ((args.korean_1x,1),(args.korean_8x,8))]
    for name,frame in (('japanese-win',art['japanese_common'][0]),
                       ('japanese-draw',art['japanese_common'][1]),('digicode-last-chance',art['digicode'])):
        pixels={(x,y):c for x,y,c in frame['pixels']}
        for scale in (1,8):
            images.append(image_contract(args.art.parent/f'{name}-{scale}x.png',pixels,palette,frame['bounds'],scale))
    rejected=[]
    point=next(iter(punctuation));changed=dict(ko);changed[point]=12 if changed[point]!=12 else 6
    changed_outline=dict(ko);changed_outline.pop(next(p for p,c in ko.items() if p[0]<40 and c==12))
    for label,pixels in (('punctuation recolored',changed),('outline pixel removed',changed_outline),
                         ('spacing column occupied',{**ko,(40,0):12}),('non-native ink index',{**ko,(-50,0):3})):
        try:korean_contract(pixels,punctuation)
        except AssertionError:rejected.append(label)
        else:raise AssertionError('negative control survived: '+label)
    report={'status':'PASS_DATA_ONLY','input_hashes':{'art':digest(args.art.read_bytes()),
            'gba':digest(gba),'wsc15':digest(wsc)},'japanese_common':japanese,
            'digicode':{**summary(dg),'parts':len(art['digicode']['parts']),'exact_user_image':True},
            'korean':{**summary(ko),**korean,'parts':len(art['korean']['parts']),
                      'tiles':len(art['korean']['tiles_4bpp_hex'])},'images':images,
            'original_digit_frames':12,'original_digit_parts':sum(map(len,native_parts[2:14])),
            'negative_controls':rejected,'visual_readability_review':'recorded separately',
            'limitations':['No ROM allocation, integration, emulator, saves or runtime OAM/timing proof.',
                           'Digicode original user-chart authentication is not newly established.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'report_sha256':digest(args.output.read_bytes()),
                      'korean':report['korean']},ensure_ascii=False))
    return 0


if __name__=='__main__':raise SystemExit(main())


