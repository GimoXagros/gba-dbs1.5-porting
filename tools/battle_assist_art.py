"""Build native Options presentations in the four installed languages."""

import json
import struct

from build_options_selector import pack_p0, pack_tile
from digicode_glyphs import font_glyphs, text_pixels as digicode_pixels
from encode_digicode_reading import CATALOG


# Digicode follows the Japanese reading. Decimal digits and control decorations
# use the same conventional numeric symbols as the original Options screen.
LABELS = (
    ("ASSIST", "BATTLE ASSIST", "D-SPIRIT", "BOSS HP 1", "APPLY", "BACK", "OFF", "ON", "SAVE ERROR"),
    ("ほじょ", "バトルほじょ", "Dスピリット", "ボス HP 1", "ほぞん", "もどる", "なし", "あり", "ほぞんエラー"),
    ("전투 보조", "전투 보조", "D-스피릿", "보스 체력 1", "저장", "돌아가기", "꺼짐", "켜짐", "저장 오류"),
    ("ほじよ", "ばとるほじよ", "Dすぴりつと", "ぼすHP1", "ほぞん", "もどる", "なし", "あり", "ほぞんえらー"),
)
DIGITS = tuple("0123456789")
CONTROLS = "L -100   R +100"
BASE = 0x08000000


def glyphs_for(font, chars):
    result = {}
    for block in font.decode("utf-8").split("STARTCHAR ")[1:]:
        lines=block.splitlines()
        fields={p[0]:p[1:] for line in lines if (p:=line.split())}
        code=int(fields["ENCODING"][0])
        if code < 0 or chr(code) not in chars:
            continue
        w,h,left,bottom=map(int,fields["BBX"])
        bits=(w+7)//8*8
        rows=lines[lines.index("BITMAP")+1:lines.index("ENDCHAR")]
        ink={(left+x,y-bottom-h) for y,row in enumerate(rows) for x in range(w)
             if int(row,16)&(1<<(bits-x-1))}
        result[chr(code)]=(int(fields["DWIDTH"][0]),ink)
    assert set(result)==chars
    return result


def lettering(text, glyphs):
    ink = set()
    x = 0
    for char in text:
        advance, points = glyphs[char]
        ink.update((x + dx, y) for dx, y in points)
        x += advance
    left = min(x for x, y in ink)
    ink = {(x-left+1, y-1) for x,y in ink}
    pixels = {(x+dx,y+dy):2 for x,y in ink for dy in (-1,0,1) for dx in (-1,0,1)}
    pixels.update({p:1 for p in ink})
    return pixels


def resource(font, lang, raw):
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    labels = LABELS[lang]
    shared = (*DIGITS, CONTROLS, ">")
    chars = set("".join(shared + (labels if lang < 3 else ())))
    glyphs = glyphs_for(font, chars)
    digicode = font_glyphs(catalog) if lang == 3 else None
    atlas, layouts, bounds = [], [], []
    for index, text in enumerate((*labels, *shared)):
        if lang == 3 and index < len(labels):
            word = text.rstrip("1")
            pixels, width = digicode_pixels(word, catalog, digicode)
            if word != text:
                pixels.update({(width+2+x,y):v for (x,y),v in lettering("1",glyphs).items()})
        else:
            pixels = lettering(text, glyphs)
        width = max(x for x,y in pixels) + 1
        top = min(y for x,y in pixels)
        height = max(y for x,y in pixels) - top + 1
        parts = []
        for y in range(top,top+height,8):
            for x in range(0,width,8):
                tile = pack_tile(pixels,x,y)
                if any(tile):
                    if tile not in atlas:
                        atlas.append(tile)
                    parts.append((atlas.index(tile),y,x))
        layouts.append(parts)
        bounds.append([text,width,top,height,len(parts)])
    data = pack_p0(layouts,atlas,raw)
    p1 = BASE+raw+len(data)
    data.extend(struct.pack("<6I",p1+8,0,len(layouts),p1+24,0,0))
    for index in range(len(layouts)):
        data.extend(struct.pack("<BBHHHII",1,255,index,0,0,0,0))
    return bytes(data),dict(p0=BASE+raw,p1=p1,frames=bounds)
