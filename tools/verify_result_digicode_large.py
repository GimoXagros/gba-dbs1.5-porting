#!/usr/bin/env python3
"""Independently reconstruct the requested larger seven-kana Digicode sprite."""
from pathlib import Path
import argparse,json,struct
from PIL import Image
from verify_result_pixel_art import digest,load,exported,source_frames,image_contract,summary,self_check

IDS=("jp-3089","jp-3059","jp-3068","jp-3061","jp-3084","jp-3093","jp-3059")
READING="ラストチヤンス"
WIDTHS=(12,10,12,10,10,12,10)

def counters(ink,width,height):
    empty={(x,y) for x in range(-1,width+1) for y in range(-1,height+1)}-ink
    outside={p for p in empty if p[0] in (-1,width) or p[1] in (-1,height)};pending=list(outside)
    while pending:
        x,y=pending.pop()
        for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if point in empty and point not in outside:outside.add(point);pending.append(point)
    remaining=empty-outside;count=0
    while remaining:
        count+=1;pending=[remaining.pop()]
        while pending:
            x,y=pending.pop()
            for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if point in remaining:remaining.remove(point);pending.append(point)
    return count

def expected_ink(font,separated=False):
    ink=set();groups=[];origin=-50
    widths=tuple(w-1 for w in WIDTHS) if separated else WIDTHS
    gap=3 if separated else 2
    for glyph_id,char,width in zip(IDS,READING,widths,strict=True):
        rows=bytes.fromhex(font['glyphs'][glyph_id]);assert len(rows)==16
        points={(x,y) for y,row in enumerate(rows) for x in range(8) if row&(128>>x)}
        left,top,right,bottom=summary({p:1 for p in points})['bounds'];height=bottom-top+1;old_width=right-left+1
        assert height==10 and old_width in (6,7)
        local={(x,y) for y in range(14) for x in range(width)
               if (left+x*old_width//width,top+y*height//14) in points}
        counter_count=counters({(x-left,y-top) for x,y in points},old_width,height)
        assert counters(local,width,14)==counter_count
        placed={(origin+x,-7+y) for x,y in local};assert not ink&placed;ink.update(placed)
        groups.append({'character':char,'glyph_id':glyph_id,'source_size':[old_width,height],
                       'target_size':[width,14],'origin':[origin,-7],
                       'source_ink_pixels':len(points),'target_ink_pixels':len(local),
                       'source_and_expanded_counters':counter_count,
                       'local_mask_sha256':digest(bytes(int((x,y) in local) for y in range(14) for x in range(width)))})
        origin+=width+gap
    assert origin-gap==(37 if separated else 38) and groups[1]['local_mask_sha256']==groups[6]['local_mask_sha256']
    return ink,groups

def shape_contract(pixels,ink,punctuation,separated=False):
    body={p:c for p,c in pixels.items() if p[0]<40}
    assert {p for p,c in body.items() if c!=12}==ink
    edge={(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}-ink
    assert {p for p,c in body.items() if c==12}==edge
    assert set(body.values()) <= {6,7,8,9,10,12}
    assert {p:c for p,c in pixels.items() if p[0]>=42}==punctuation
    assert not any(x in (40,41) for x,y in pixels)
    assert summary(body)['bounds']==[-51,-8,37 if separated else 38,7]
    return len(edge)

def main():
    p=argparse.ArgumentParser()
    for name in ('art','baseline','font','wsc15','output'):p.add_argument(name,type=Path)
    p.add_argument('--separated',action='store_true')
    a=p.parse_args();assert not a.output.exists();self_check()
    old=load(a.baseline);art=load(a.art);font=load(a.font);wsc=a.wsc15.read_bytes()
    assert digest(a.baseline.read_bytes())=='7FB3925216D8E80DE8410970C2E4ACEFD314C1E675DD0FCB1973C342BDFE00B0'
    assert digest(wsc)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert art['japanese_common']==old['japanese_common'] and art['korean']==old['korean']
    assert art['native_palette_rgb888']==old['native_palette_rgb888']
    # The reference byte identity is checked independently of producer metadata.
    assert digest(a.font.read_bytes())=='ABDFB29C40C3C8F38BB64214B1F3695FED4774C32362A6ACC1F4EE5D90029EEA'
    small_ink=set();cursor=-31
    for glyph_id in IDS:
        rows=bytes.fromhex(font['glyphs'][glyph_id])
        points={(x,y) for y,row in enumerate(rows) for x in range(8) if row&(128>>x)}
        left=min(x for x,y in points);right=max(x for x,y in points)
        small_ink.update((cursor+x-left,y-8) for x,y in points);cursor+=right-left+2
    assert len(small_ink)==240
    assert small_ink=={(x,y) for x,y,c in old['digicode']['pixels'] if x<21 and c!=12}
    ink,groups=expected_ink(font,a.separated)
    _,source=source_frames(wsc)
    punctuation={p:c for p,c in source[14].items() if 42<=p[0]<=50};assert len(punctuation)==65
    pixels=exported(art['digicode'],28);edge_count=shape_contract(pixels,ink,punctuation,a.separated)
    clear_columns=[]
    if a.separated:
        clear_columns=[g['origin'][0]+g['target_size'][0]+1 for g in groups[:-1]]
        assert all((x,y) not in pixels for x in clear_columns for y in range(-8,8))
    palette=[tuple(c) for c in art['native_palette_rgb888']]
    images=[]
    for scale in (1,8):
        images.append(image_contract(a.art.parent/f'digicode-last-chance-{scale}x.png',pixels,palette,[-51,-8,50,7],scale))
    negatives=[]
    changed=dict(pixels);changed.pop(next(iter(ink)))
    recolored=dict(pixels);point=next(iter(punctuation));recolored[point]=12 if recolored[point]!=12 else 6
    for name,variant in (('lost identity pixel',changed),('changed source punctuation',recolored),('occupied gap',{**pixels,(40,0):12})):
        try:shape_contract(variant,ink,punctuation,a.separated)
        except AssertionError:negatives.append(name)
        else:raise AssertionError(name)
    report={'status':'PASS_DATA_ONLY','art_sha256':digest(a.art.read_bytes()),'font_file_sha256':digest(a.font.read_bytes()),
            'source_reading':'ラストチャンス','render_reading':READING,'glyphs':groups,
            'digicode':{**summary(pixels),'parts':len(art['digicode']['parts']),'ink_pixels':len(ink),'outline_pixels':edge_count},
            'original_punctuation_pixels':65,'korean_and_japanese_unchanged':True,'images':images,'negative_controls':negatives,
            'separated_revision':a.separated,'fully_transparent_interglyph_columns':clear_columns,
            'visual_review':'recorded separately','limitations':['New authored expansion of frozen local Digicode glyphs, not identical to the smaller supplied image.','No ROM allocation/integration/runtime/OAM or original-chart authentication.']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'sha256':digest(a.output.read_bytes()),'digicode':report['digicode']},ensure_ascii=False))

if __name__=='__main__':main()
