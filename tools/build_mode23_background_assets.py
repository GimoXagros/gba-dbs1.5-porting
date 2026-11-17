"""Prepare source-bound mode23 background assets without installing a scene."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from build_poc import convert_planar_tile
from build_stage_assets import convert_map
from convert_wsc_palette_block import convert_color
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CODE={(0x785CEA,0x785DDD):'A77CD1D5EA3BEB815B6A25689AA684148E4017C1A75B288B96FA0C1CBACC6368',
 (0x7530B9,0x753138):'566183C711ABF63C610CBC54E9AE112130EC199C0DDCDA8F2CE9497377EF61D3',
 (0x74AE9F,0x74AEC4):'C7BCFCE96EEB4FBC7BB1C06586C9E3E9D409671D9934DF8AF6A5DBF1C0559C9B'}
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def far_c3(bank,segment,offset,size):
 linear=segment*16+offset
 need(0x80<=bank<=0xFF and 0x30000<=linear<linear+size<=0x40000,'known C3 window and whole extent')
 return (bank&0x7F)*0x10000+linear-0x30000
def rectangle_calls(source):
 """Execute only the pinned straight-line argument producer; summarize no scene."""
 d=Cs(CS_ARCH_X86,CS_MODE_16);regs=dict(ax=0,bx=0,cx=0,dx=0,si=0,di=0,es=0,ds=0x3F73)
 stack=[];calls=[];instructions=list(d.disasm(source[0x785D22:0x785DCE],0x785D22))
 need(sum(i.size for i in instructions)==0xAC,'whole rectangle producer decoded')
 def value(v):return regs[v] if v in regs else int(v,0)
 for i in instructions:
  operands=i.op_str.split(', ')
  if i.mnemonic=='mov':
   dest,src=operands
   need(dest in regs,'known mov register')
   regs[dest]=0x1000 if src=='word ptr [bp + 6]' else value(src)
  elif i.mnemonic=='xor':
   need(len(operands)==2 and operands[0]==operands[1] and operands[0] in regs,'known zeroing idiom');regs[operands[0]]=0
  elif i.mnemonic=='add':
   dest,src=operands
   if dest=='sp':
    need(src=='0x12' and len(stack)>=9,'exact nine argument cleanup');del stack[-9:]
   else:
    need(dest in regs,'known add register');regs[dest]=(regs[dest]+value(src))&65535
  elif i.mnemonic=='push':stack.append(value(i.op_str))
  elif i.mnemonic=='pop':
   need(i.op_str=='ax' and stack,'saved AX restore');regs['ax']=stack.pop()
  elif i.mnemonic=='lcall':
   need(i.op_str=='0x4fff, 0x30c9' and len(stack)>=9,'only source rectangle copier')
   dest,es,x,y,src,ds,width,height,wrap=list(reversed(stack[-9:]))
   need((dest,es,src,ds,width,height,wrap)==(0x1000,0,0,0x3F73,16,8,8),'exact source map/destination/rectangle contract')
   need(0<=x<32 and 0<=y<=24,'bounded32x32 destination')
   calls.append(dict(call=i.address,x=x,y=y,width=width,height=height,wrap_x=True,source_offset=src,source_segment=ds,source_bank=0xC1,source_destination=dest))
  else:raise ValueError('unknown source instruction '+i.mnemonic+' '+i.op_str)
 need(not stack and len(calls)==8,'eight calls and balanced arguments')
 return calls
def build(source):
 need(sha(source)==SOURCE,'exact original WSC1.5')
 for (a,z),pin in CODE.items():need(sha(source[a:z])==pin,'complete source code anchor')
 pattern=far_c3(0xC1,0x3F73,0,256)
 tile_at=far_c3(0xC1,0x3F73,0x100,0x6C0)
 palette_at=far_c3(0xC1,0x3F73,0x7C2,30)
 need((pattern,tile_at,palette_at)==(0x41F730,0x41F830,0x41FEF2),'typed source addresses')
 calls=rectangle_calls(source);words=[None]*1024;coverage=[0]*1024
 for c in calls:
  for y in range(c['height']):
   for x in range(c['width']):
    dest=(c['y']+y)*32+(c['x']+x)%32
    need(words[dest] is None,'no overlapping destination cells')
    words[dest]=h(source,pattern+2*(y*16+x));coverage[dest]+=1
 need(all(n==1 for n in coverage),'complete1024-cell map written exactly once')
 need(all(v&0x2000 and (v&511)<54 and ((v>>9)&15)==0 for v in words),'all map cells use the loaded54 bank1 tiles and palette0')
 source_map=struct.pack('<1024H',*words)
 # Existing converter has a504-cell input contract; pad only the final
 # temporary chunk, and retain every real cell of the full32x32 map.
 converted=bytearray()
 for at in range(0,len(source_map),1008):
  chunk=source_map[at:at+1008];converted.extend(convert_map(chunk.ljust(1008,b'\0'))[:len(chunk)])
 need(len(converted)==2048,'no28x18 crop or invented viewport')
 for i,v in enumerate(words):
  expected=(v&511)|((v&0x2000)>>4)|((v&0xC000)>>4)|((v&0x1E00)<<3)
  need(h(converted,2*i)==expected,'all native tile/bank/flip/palette fields')
 tiles=b''.join(convert_planar_tile(source[a:a+32]) for a in range(tile_at,tile_at+0x6C0,32))
 for n in range(54):
  for y in range(8):
   for x in range(8):
    pixel=sum(((source[tile_at+n*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
    need(((tiles[n*32+y*4+x//2]>>(4*(x%2)))&15)==pixel,'all3456 source tile pixels')
 colors=[h(source,palette_at+2*i) for i in range(15)]
 need(all(0<=v<=4095 for v in colors),'all source RGB444 channels')
 normal=struct.pack('<15H',*(convert_color(v) for v in colors))
 dim=struct.pack('<15H',*(convert_color((v&0xEEE)>>1) for v in colors))
 need(any(convert_color((v&0xEEE)>>1)!=(convert_color(v)>>1)&0x3DEF for v in colors),'source dimming is not rounded-native-color shifting')
 files={'tiles.bin':tiles,'map.bin':bytes(converted),'palette.bin':normal,'palette-dim.bin':dim}
 proof=dict(source_code=[dict(start=a,end=z,sha256=pin) for (a,z),pin in CODE.items()],
  pattern=dict(offset=pattern,bytes=256,width=16,height=8),
  rectangles=calls,map=dict(width=32,height=32,cells=1024,source_destination=0x1000,source_word_sha256=sha(source_map),all_cells_written_once=True,native_tile_range=[512,565],native_palette_bank=0,viewport_not_selected=True),
  tiles=dict(offset=tile_at,bytes=1728,count=54,pixels=3456,source_destination=0x8000,native_relative_tile_base=512),
  palette=dict(offset=palette_at,colors=15,bytes_each=30,first_color_index=1,source_destination=0xFE02,dim_formula='convert_rgb444_to_native((source & 0x0EEE) >> 1)',palette_zero_inherited=True,palette_zero_bytes_emitted=False,caller_also_dims_inherited_source_color_zero=True),
  no_ROM_installation=True,no_native_RAM_or_VRAM_reservation=True,no_menu_or_scene_implementation=True)
 return files,proof
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
 need(not a.output_dir.exists(),'fresh standalone output directory required')
 source=a.source.read_bytes();files,proof=build(source)
 manifest=dict(status='MODE23_BACKGROUND_ASSETS_PREPARED',source_sha256=SOURCE,builder_sha256=sha(Path(__file__).read_bytes()),
  primitive_sha256={name:sha((ROOT/'tools'/name).read_bytes()) for name in ('build_poc.py','build_stage_assets.py','convert_wsc_palette_block.py')},
  files={name:dict(bytes=len(data),sha256=sha(data)) for name,data in files.items()},source_contract=proof,
  actual_runtime_verified=False,mode23_implemented=False,
  limits=['Prepared assets only; no native screen base, viewport, task state, menu entry or ROM address allocated.',
   'Palette color0 is inherited by source and dimmed by its caller; it is deliberately not invented in either30-byte palette output.',
   'Native map indices512..565 require future typed charbase ownership; output is not directly an installed native scene.'])
 a.output_dir.mkdir(parents=True)
 for name,data in files.items():(a.output_dir/name).write_bytes(data)
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(dict(status=manifest['status'],manifest_sha256=sha(path.read_bytes()),files=manifest['files'])))
if __name__=='__main__':main()
