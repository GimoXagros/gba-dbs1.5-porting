"""Relocatable mode23 BG phase assets and native constructors.

Caller owns text BG1/0, charblock0, mapsF000/F800 and palette rows0..7.
No placement, scene registration, global RAM reservation or ROM is written.
Inherited bank0 tile0 and intro palette0 remain explicit entry contracts.
"""
import hashlib,struct
from build_poc import convert_planar_tile
from build_stage_assets import convert_map
from convert_wsc_palette_block import convert_color
from build_mode23_background_assets import build as intro_build
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'

def build(source,target):
 if hashlib.sha256(source).hexdigest().upper()!=SOURCE:raise ValueError('mode23 graphics source')
 assets,contract=intro_build(source)
 files={'intro_tiles':assets['tiles.bin'],'intro_map':assets['map.bin'],'intro_palette':assets['palette-dim.bin']}
 raw=[]
 def tiles(name,at,size):
  assert size%32==0
  files[name]=b''.join(convert_planar_tile(source[x:x+32]) for x in range(at,at+size,32))
  raw.append(dict(name=name,source=at,size=size,kind='planar4bpp'))
 def palette(name,at,size):
  words=struct.unpack_from('<'+'H'*(size//2),source,at);assert all(x<4096 for x in words)
  files[name]=struct.pack('<'+'H'*len(words),*(convert_color(x) for x in words))
  raw.append(dict(name=name,source=at,size=size,kind='RGB444'))
 def maps(name,at,padding=None,tail=False):
  words=struct.unpack_from('<504H',source,at)
  assert all(v&0x2000 or (v&511)==0 for v in words),'only inherited bank0 tile0'
  converted=convert_map(source[at:at+1008])
  if padding is not None:
   fill=(padding&511)|((padding&0x2000)>>4)|((padding&0xC000)>>4)|((padding&0x1E00)<<3)
   converted=b''.join(converted[y*56:(y+1)*56]+struct.pack('<4H',*[fill]*4) for y in range(18))
   if tail:converted+=struct.pack('<448H',*[fill]*448)
  files[name]=converted
  raw.append(dict(name=name,source=at,size=1008,kind='map',padding=padding,full32=tail,inherited_bank0_tile0=any(not v&0x2000 for v in words)))
 for key,at in [('round',0x2B9BA0),('last',0x2BB600)]:tiles(key+'_tiles',at,0x3D40)
 for key,at in [('round',0x2BF910),('last',0x2BF9F0)]:palette(key+'_palette',at,0x100)
 maps('round_map',0x2BED40,0);maps('last_map',0x2BF130,0);maps('power_map',0x2BF520,0)
 tiles('failure_tiles',0x3B4090,0x8E0);palette('failure_palette',0x3D8790,32);maps('failure_map',0x3C3800,0x2000,True)
 tiles('completion_tiles',0x3A5FA0,0x700);palette('completion_palette',0x3A66A0,32);maps('completion_map',0x3A66C0)
 out=bytearray();rows={}
 for name,data in files.items():
  while (target+len(out))%4:out.append(0)
  rows[name]={'address':0x08000000+target+len(out),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest().upper()}
  out.extend(data)
 return bytes(out),dict(tables=rows,source_assets=raw,intro_contract=contract,entry_dependencies=['source-equivalent inherited bank0 tile0','source-equivalent inherited intro palette0','exclusive BG1/BG0 and palette mirror lifecycle'],runtime_verified=False)

def assembly(rows):
 def copy(name,dst):
  row=rows[name]
  return f'ldr r0,={row["address"]}\nldr r1,={dst}\nldr r2,={row["bytes"]//2}\nbl m23_graphics_copy\n'
 def body(name,code):return f'{name}:\npush {{r4-r11,lr}}\n{code}pop {{r4-r11,lr}}\nbx lr\n.ltorg\n'
 out=[]
 intro='mov r0,#0x04000000\nldr r1,=0x1f02\nstrh r1,[r0,#8]\nldr r1,=0x1e03\nstrh r1,[r0,#10]\n'
 intro+=copy('intro_tiles',0x06004000)+copy('intro_map',0x0600F800)
 intro+='mov r1,#0x05000000\nldrh r3,[r1]\nmov r2,#0\n'
 for shift in (0,5,10):
  intro+=f'mov r0,r3,lsr #{shift}\nand r0,r0,#31\nmov r0,r0,lsr #2\ncmp r0,#0\nmov r0,r0,lsl #1\naddne r0,r0,#1\norr r2,r2,r0,lsl #{shift}\n'
 intro+='strh r2,[r1]\n'+copy('intro_palette',0x05000002)+'add r0,r4,#0x34\nbl m23_intro_resources\nmov r0,#112\nstrh r0,[r4,#0x34]\nmov r0,#72\nstrh r0,[r4,#0x36]\n'
 out.append(body('m23_intro_prepare',intro))
 common='add r0,r4,#0x84\nbl m23_aim_resources\nldrb r0,[r4,#0x2a]\ncmp r0,#6\nbeq m23_graphics_last_round\n'
 common+=copy('round_tiles',0x06004000)+copy('round_palette',0x05000000)+copy('round_map',0x0600F000)+'b m23_graphics_round_shared\nm23_graphics_last_round:\n'
 common+=copy('last_tiles',0x06004000)+copy('last_palette',0x05000000)+copy('last_map',0x0600F000)+'m23_graphics_round_shared:\n'+copy('power_map',0x0600F800)
 common+='bl m23_scroll_reset\nmov r0,#0xb4\nbl m23_window_left\nmov r0,#0xe0\nbl m23_window_right\nmov r0,#0x70\nbl m23_window_top\nmov r0,#0x70\nbl m23_window_bottom\nadd r0,r4,#0x34\nbl m23_round_start_resources\nmov r0,#112\nstrh r0,[r4,#0x34]\nmov r0,#72\nstrh r0,[r4,#0x36]\nbl m23_palette_prepare_fade_in\nmov r0,#0x25\nbl m23_display_low\n'
 out.append(body('m23_round_prepare',common))
 failure='mov r0,#0\nbl m23_display_low\n'+copy('failure_palette',0x05000000)+copy('failure_tiles',0x06004000)+copy('failure_map',0x0600F800)
 failure+='add r0,r4,#0x34\nbl m23_failure_resources\nldrh r0,[r4,#0x3c]\norr r0,r0,#0x6400\nstrh r0,[r4,#0x3c]\nmvn r0,#19\nstrh r0,[r4,#0x34]\nmov r0,#76\nstrh r0,[r4,#0x36]\nmov r0,#0x26\nbl m23_display_low\nmov r0,#0\nbl m23_window_left\nmov r0,#1\nbl m23_window_right\nmov r0,#0x32\nbl m23_window_top\nmov r0,#0x50\nbl m23_window_bottom\nmov r0,#0x24\nmov r1,#4\nbl m23_sound\n'
 out.append(body('m23_failure_prepare',failure))
 completion='mov r0,#0\nbl m23_display_low\nadd r0,r4,#0x34\nmov r1,#11\nmov r2,#0x18\nbl m23_full_base_resources\n'
 completion+=copy('completion_tiles',0x06004000)
 completion+=f'ldr r6,={rows["completion_map"]["address"]}\nldr r7,=0x0600f800\nmov r8,#18\nm23_graphics_completion_row:\nmov r0,r6\nmov r1,r7\nmov r2,#28\nbl m23_graphics_copy\nadd r6,r6,#56\nadd r7,r7,#64\nsubs r8,r8,#1\nbne m23_graphics_completion_row\n'
 completion+=copy('completion_palette',0x05000000)+'mov r0,#6\nbl m23_display_low\n'
 out.append(body('m23_completion_prepare',completion))
 out.append('m23_graphics_copy:\npush {r3,lr}\nm23_graphics_copy_loop:\nldrh r3,[r0]\nstrh r3,[r1]\nadd r0,r0,#2\nadd r1,r1,#2\nsubs r2,r2,#1\nbne m23_graphics_copy_loop\npop {r3,lr}\nbx lr\n')
 return '\n'.join(out)
