"""Menu-only six-column/eight-row pixel redraw; portrait font is unchanged.

The reviewed chart paths retain their character identities. Integer endpoints
are regridded and connected with one-pixel strokes, never filtered or blurred.
Voicing uses a separate two-row band above the body and remains fully present.
"""
from digicode_glyphs import BODIES,VOICED,SEMIVOICED
from encode_digicode_reading import encode


def line(a,b):
 x,y=a;ex,ey=b;dx=abs(ex-x);dy=-abs(ey-y)
 sx=1 if x<ex else-1;sy=1 if y<ey else-1;error=dx+dy;out={(x,y)}
 while(x,y)!=(ex,ey):
  twice=error*2
  if twice>=dy:error+=dy;x+=sx
  if twice<=dx:error+=dx;y+=sy
  out.add((x,y))
 return out


def glyph(character):
 character=chr(ord(character)-0x60)if 0x30A1<=ord(character)<=0x30F6 else character.upper()if character.isascii()else character
 base=VOICED.get(character,SEMIVOICED.get(character,character));points=set()
 for path in BODIES[base].split(';'):
  original=[tuple(map(int,p.split(',')))for p in path.split()]
  vertices=[((x*5+3)//6,(y*7+4)//9)for x,y in original]
  points.update(vertices)
  for a,b in zip(vertices,vertices[1:]):points.update(line(a,b))
 # Explicit compact repair: retain the separated top/bottom hourglass strokes
 # of KO rather than merging adjacent source rows during endpoint reduction.
 if base=='こ':
  points={(x,y)for y,xs in enumerate(((0,1,2,3,4),(1,2,3),(2,),(0,1,2,3,4),(),(2,),(1,2,3),(0,1,2,3,4)))for x in xs}
 points={(x,y+4)for x,y in points}
 if character in VOICED:points|={(1,0),(2,1),(4,0),(5,1)}
 if character in SEMIVOICED:points|={(3,0),(2,1),(4,1),(3,2)}
 assert points and all(0<=x<=5 and 0<=y<=11 for x,y in points)
 return points


def compact_text(reading,catalog,unused_glyphs=None):
 # Encoding is still validated against the unchanged approved identity catalog.
 encode(reading,catalog)
 pixels={};cursor=0
 for character in reading:
  points=glyph(character);left=min(x for x,y in points);right=max(x for x,y in points)
  pixels.update({(cursor+x-left,y-6):13 for x,y in points})
  cursor+=right-left+2
 return pixels,cursor-1


def framed_panel(text,width,marker):
 assert width<=68 and all(-6<=y<=5 for x,y in text)
 left=-44;right=43
 out={(x,y):(13 if x in(left,right)or y in(-8,7)else 15)for y in range(-8,8)for x in range(left,right+1)}
 out.update({(x,y):v for(x,y),v in marker.items()})
 start=left+16+(71-width)//2
 out.update({(x+start,y):v for(x,y),v in text.items()})
 assert all(out[x,y]==v for(x,y),v in marker.items())
 assert all(out[x,-7]==out[x,6]==15 for x in range(-28,43))
 return out
