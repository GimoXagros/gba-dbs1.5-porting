"""Warm native title palette treatment for Korean/Digicode Start prompts only."""
from digicode_glyphs import BODIES,VOICED,SEMIVOICED
from mode23_compact_menu_digicode import line
from encode_digicode_reading import encode

READING='スタートボタンをおしてね'
KOREAN='시작 버튼을 눌러 주세요!'


def warm_existing(frame):
    # Preserve the complete existing Korean lettering and native !. The white
    # BDF ink alone adopts the source prompt's top-to-bottom indices11..7.
    ink={p for p,v in frame.items()if v==13}
    top=min(y for x,y in ink);height=max(y for x,y in ink)-top+1
    return {p:(11-min(4,(p[1]-top)*5//height)if p in ink else v)for p,v in frame.items()}


def prompt_digicode(japanese,catalog):
    encode(READING,catalog)
    ink=set();cursor=1
    for ch in READING:
        ch=chr(ord(ch)-0x60)if 0x30A1<=ord(ch)<=0x30F6 else ch
        base=VOICED.get(ch,SEMIVOICED.get(ch,ch));body=set()
        for path in BODIES[base].split(';'):
            vertices=[tuple(map(int,p.split(',')))for p in path.split()]
            vertices=[((x*5+3)//6,(y*6+4)//9)for x,y in vertices]
            body.update(vertices)
            for a,b in zip(vertices,vertices[1:]):body.update(line(a,b))
        body={(x,y+3)for x,y in body}
        if ch in VOICED:body|={(1,0),(2,1),(4,0),(5,1)}
        if ch in SEMIVOICED:body|={(3,0),(2,1),(4,1),(3,2)}
        left=min(x for x,y in body);right=max(x for x,y in body)
        ink.update((x-left+cursor,y-5)for x,y in body)
        cursor+=right-left+2
    # One-pixel dark edge, with the same unchanged native palette index15.
    out={(x+dx,y+dy):15 for x,y in ink for dx in(-1,0,1)for dy in(-1,0,1)}
    out.update({(x,y):11-min(4,(y+5)//2)for x,y in ink})
    width=max(x for x,y in out)+1
    punctuation={(x-48+width+2,y+2):v for(x,y),v in japanese.items()if 48<=x<=50}
    assert len(punctuation)==22
    out.update(punctuation);width=max(x for x,y in out)+1
    return {(x-width//2,y):v for(x,y),v in out.items()}
