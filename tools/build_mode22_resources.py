"""Typed source mode22 graphics/font resources; no native placement or scene claim."""
import argparse,hashlib,json,struct
from pathlib import Path
from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CS=0x7848F0
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def build(source):
 assert sha(source)==SOURCE
 objects=[];blob=bytearray()
 def add(name,raw,size,kind,destination=None):
  old=source[raw:raw+size];assert len(old)==size
  if kind=='tiles':
   assert size%32==0;data=b''.join(convert_tile(old[i:i+32])for i in range(0,size,32))
  elif kind=='palette':
   colors=struct.unpack('<'+'H'*(size//2),old);assert all(x<4096 for x in colors)
   data=struct.pack('<'+'H'*len(colors),*(convert_color(x)for x in colors))
  elif kind=='map':
   values=struct.unpack('<'+'H'*(size//2),old)
   data=struct.pack('<'+'H'*len(values),*((v&511)|((v&0x2000)>>4)|((v&0xc000)>>4)|((v&0x1e00)<<3)for v in values))
  else:assert kind=='bytes';data=old
  blob.extend(bytes((-len(blob))%4));offset=len(blob);blob.extend(data)
  objects.append(dict(label=name,offset=offset,size=len(data),kind=kind,source_raw=raw,source_bytes=size,source_sha256=sha(old),sha256=sha(data),source_destination=destination))
 add('shared-bg-tiles',0x420000,0xC40,'tiles',0xB080);add('shared-bg-palette',0x420C40,32,'palette',0xFE00)
 rawbase=0x2D9360
 for name,offset,size,dst,kind in(
  ('scroll-map',0x5B78,0x480,0x800,'map'),('ordinary-base-tiles',0x3A98,0x600,0x9600,'tiles'),('ordinary-base-palette',0x3DB8,32,0xFF60,'palette'),('ordinary-base-map',0x3DD8,96,0x1000,'map'),
  ('digits-tiles',0x5FF8,352,0x4020,'tiles'),('digits-palette',0x6158,32,0xFFE0,'palette'),('ordinary-palettes',0x3680,320,0xFE20,'palette'),
  ('special-tiles',0x2E80,0xA80,0x7200,'tiles'),('special-palette',0x37C0,32,0xFE20,'palette'),('special-map',0x3A20,120,0x1000,'map'),('name-palette',0x6178,32,0xFF00,'palette'),('special-banner-map',0x6198,112,0x1000,'map'),
  ('common-edge',0x5AB8,64,0x800,'map'),('special-top',0x5AF8,64,0x800,'map'),('special-bottom',0x5B38,64,0xC40,'map')):add(name,rawbase+offset,size,kind,dst)
 icons=[]
 for i in range(10):
  dst,offset=struct.unpack_from('<HH',source,CS+0x347+4*i);add(f'tag-{i}-tiles',rawbase+offset,0x400,'tiles',0x4000+dst)
  offset,width,x,y=struct.unpack_from('<4H',source,CS+0x36F+8*i);add(f'tag-{i}-map',rawbase+offset,width*4*2,'map',0x1000)
  coordinate=struct.unpack_from('<H',source,CS+0x5A5+2*i)[0]
  icons.append(dict(rank=i,map_width=width,map_height=4,map_x=x,map_y=y,digit_x=coordinate>>8,digit_y=coordinate&255))
  for name,table,size,dst,kind in(('rank-tiles',0x3BF,512,0x9A00,'tiles'),('rank-palette',0x3D5,32,0xFF80,'palette'),('rank-map',0x3EB,32,0x1000,'map')):
   offset=struct.unpack_from('<H',source,CS+table+2*i)[0];add(f'{name}-{i}',rawbase+offset,size,kind,dst)
 add('special-portrait-tiles',0x3A5FA0,0x700,'tiles',0x7E80);add('special-portrait-palette',0x3A66A0,32,'palette',0xFE40)
 # Exact 86EF:0000 type1/type2 source font choice: C3:3E1C+800.
 assert source[0x786F47:0x786F70]==bytes.fromhex('c1e005c1e2058bf8b8e00f8ec0be0010b81c3e8ed8b91000fcf3a58bfab800048ec08bf3b90004f3a5')
 add('ascii-font-tiles',0x43E9C0,0x800,'tiles',0x4020);add('ascii-font-palette',0x43F1C0,32,'palette',0xFF00)
 assert source[CS+0x336:CS+0x347]==b'YOU HAVE NO TAGS\x00'
 add('empty-text',CS+0x336,17,'bytes')
 report=dict(status='MODE22_TYPED_GRAPHICS_RESOURCES',source_sha256=SOURCE,builder_sha256=sha(Path(__file__).read_bytes()),bundle_sha256=sha(blob),bytes=len(blob),objects=objects,ordinary_icons=icons,
  rectangle_placements={'ordinary-base-map':[10,6,8,6],'rank-map':[10,8,8,2],'special-map':[9,4,10,6],'special-banner-map':[0,12,28,2]},
  font=dict(first_ASCII=32,count=64,tile_base=1,palette_bank=8,empty_screen=2,empty_position=[6,8],special_name_position=[100,62]),
  limits=['Resources only, not a registered/complete native viewer.','Source destination addresses are metadata; native BG/OBJ/IRQ ownership and layout projection remain separate.','Ordinary source tile uploads overlap by128bytes for several ranks; preserve original upload order.','Source untouched tile0 and source-compatible entry display lifetime still require explicit proof.'])
 return bytes(blob),report
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();assert not a.output_dir.exists()
 data,report=build(a.source.read_bytes());a.output_dir.mkdir(parents=True);(a.output_dir/'resources.bin').write_bytes(data);p=a.output_dir/'manifest.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS',sha(data),sha(p.read_bytes()))
if __name__=='__main__':main()
