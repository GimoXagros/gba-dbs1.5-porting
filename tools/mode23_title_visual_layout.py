"""Uninstalled r2 title typography: exact retail letters plus explicit extensions."""
from encode_digicode_reading import encode


def bold_glyphs(frames):
    # Each rectangle is actual retail English title ink (seven rows, two-pixel stems).
    rows = {
        '1': (1,-20,-18), '2': (2,-22,-17), 'P': (1,-14,-9),
        'B': (1,-3,2), 'A': (1,4,9), 'T': (1,11,16),
        'L': (1,25,29), 'E': (1,31,35), 'O': (3,-20,-15),
        'I': (3,2,3), 'N': (3,14,19), 'S': (3,24,27),
        'D': (4,-15,-10), 'R': (4,9,14), 'K': (4,17,22),
    }
    result = {}
    for char,(event,left,right) in rows.items():
        result[char] = (right-left+1, {(x-left,y):v for (x,y),v in frames[event].items()
                                    if left<=x<=right and -3<=y<=3 and v in (13,14)})
    # C uses the actual O top/bottom/left curves; only its inner right stem is removed.
    result['C'] = (6,{p:v for p,v in result['O'][1].items() if p[1] in (-3,3) or p[0]<4})
    # Other missing letters are disclosed matching-style extensions, not claimed retail glyphs.
    patterns = {
        'G': ('+####+','##    ','##    ','## ###','##  ##','##  ##','+####+'),
        'H': ('##  ##','##  ##','##  ##','######','##  ##','##  ##','##  ##'),
        'M': ('##  ##','######','######','##++##','##  ##','##  ##','##  ##'),
        'V': ('##  ##','##  ##','##  ##','##  ##','+####+',' #### ','  ##  '),
        '5': ('######','##    ','##    ','#####+','    ##','##  ##','+####+'),
        '.': ('  ','  ','  ','  ','  ','##','##'),
    }
    for char,lines in patterns.items():
        result[char]=(len(lines[0]),{(x,y-3):(13 if v=='#' else 14)
                     for y,line in enumerate(lines) for x,v in enumerate(line) if v!=' '})
    return result,rows,tuple(patterns)


def bold_text(text,glyphs):
    result={};cursor=0
    for char in text:
        if char==' ':
            cursor+=4
            continue
        width,pixels=glyphs[char]
        result.update({(x+cursor,y):v for (x,y),v in pixels.items()})
        cursor+=width+1
    return result,cursor-1


def spaced_digicode(reading,catalog,glyphs):
    """Keep every catalog ink pixel; two empty columns between glyph ink."""
    ink={};cursor=0
    for ident in encode(reading,catalog):
        pts={(x,y) for y,row in enumerate(glyphs[ident]) for x in range(8) if row&(128>>x)}
        left=min(x for x,y in pts);right=max(x for x,y in pts)
        ink.update({(cursor+x-left,y-8):13 for x,y in pts})
        cursor+=right-left+3
    # Catalog ink is y1..14 when voiced; y5..14 otherwise. Both retain one blank outer row.
    return ink,cursor-2


def open_digicode_panel(text,width,marker):
    # The old enclosing white border met voiced marks. A black 16-row backplate
    # retains all fourteen ink rows with one blank row above/below, without a border.
    extent=max(88,((width+22+6+7)//8)*8)
    assert extent<=176 and all(-7<=y<=6 for x,y in text)
    left=-52  # Shared root origin: all markers and glyph starts align.
    result={(x,y):15 for y in range(-8,8) for x in range(left,left+extent)}
    result.update({(x+left+44,y):v for (x,y),v in marker.items()})
    start=left+22
    result.update({(x+start,y):v for (x,y),v in text.items()})
    assert min(x for(x,y),v in text.items() if v==13)+start>=left+22
    assert max(x for(x,y),v in text.items() if v==13)+start<=left+extent-7
    return result
