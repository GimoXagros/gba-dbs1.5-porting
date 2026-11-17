"""Independent standalone mode23 background source tiles, rectangle map and colors."""
import argparse,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def color(v):return sum((2*((v>>s)&15)+bool((v>>s)&15))<<d for s,d in ((8,0),(4,5),(0,10)))
def code(s,a,z):return list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(s[a:z],a))
def rectangles(s):
 ins=code(s,0x785D22,0x785DCE);assert sum(i.size for i in ins)==0xAC
 regs=dict(ax=0,bx=0,cx=0,dx=0,si=0,di=0,es=0,ds=0x3F73);stack=[];calls=[]
 def val(v):return regs[v] if v in regs else int(v,0)
 for i in ins:
  if i.mnemonic=='mov':
   dst,src=i.op_str.split(', ');regs[dst]=0x1000 if src=='word ptr [bp + 6]' else val(src)
  elif i.mnemonic=='xor':
   dst,src=i.op_str.split(', ');assert dst==src;regs[dst]=0
  elif i.mnemonic=='add':
   dst,src=i.op_str.split(', ')
   if dst=='sp':assert src=='0x12';del stack[-9:]
   else:regs[dst]=(regs[dst]+val(src))&65535
  elif i.mnemonic=='push':stack.append(val(i.op_str))
  elif i.mnemonic=='pop':regs[i.op_str]=stack.pop()
  elif i.mnemonic=='lcall':
   assert i.op_str=='0x4fff, 0x30c9';args=list(reversed(stack[-9:]));dest,es,x,y,src,ds,width,height,wrap=args
   assert (dest,es,src,ds,width,height,wrap)==(0x1000,0,0,0x3F73,16,8,8)
   calls.append((x,y))
  else:raise ValueError('unexpected source map operation '+i.mnemonic)
 assert not stack and calls==[(0,0),(16,0),(8,8),(24,8),(0,16),(16,16),(8,24),(24,24)]
 return calls
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('source','assets','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();s=a.source.read_bytes();assert sha(s)==SOURCE
 ins={i.address:(i.mnemonic,i.op_str) for i in code(s,0x785CEA,0x785DDD)}
 for at,op in ((0x785CF8,'al, 0xc1'),(0x785CFC,'ax, 0x3f73'),(0x785D01,'si, 0x100'),(0x785D08,'di, 0x8000'),(0x785D0B,'cx, 0x360'),(0x785D11,'si, 0x7c0'),(0x785D16,'di, 0xfe00'),(0x785D1B,'cx, 0x10')):assert ins[at]==('mov',op)
 assert ins[0x785D14]==ins[0x785D15]==('inc','si') and ins[0x785D19]==ins[0x785D1A]==('inc','di') and ins[0x785D1E]==('dec','cx')
 assert ins[0x785D0F][0]==ins[0x785D20][0]=='rep movsw' and ins[0x785DDC][0]=='retf'
 base=0x410000+0x3F73*16-0x30000;assert base==0x41F730 and base+0x100==0x41F830 and base+0x7C2==0x41FEF2
 abi={i.address:(i.mnemonic,i.op_str) for i in code(s,0x7530B9,0x753138)}
 for at,op in ((0x7530EF,'cx, word ptr [bp + 0x12]'),(0x7530EC,'bx, word ptr [bp + 0x14]'),(0x7530E7,'cx, word ptr [bp + 0x16]')):assert abi[at]==('mov',op)
 assert abi[0x7530FE]==('and','ax, 0x3f') and abi[0x753101]==('and','di, 0xffc0') and abi[0x75310A]==('add','di, 0x40')
 dim={i.address:(i.mnemonic,i.op_str) for i in code(s,0x74AE9F,0x74AEC4)}
 assert dim[0x74AEA2]==('lcall','0x859a, 0x34a') and dim[0x74AEAE]==('mov','si, 0xfe00') and dim[0x74AEB1]==('mov','cx, 0x10')
 assert dim[0x74AEB7]==('shr','ax, 1') and dim[0x74AEB9]==('and','ax, 0x777') and dim[0x74AEC2]==('loop','0x74aeb4')
 assert all(((v>>1)&0x777)==((v&0xEEE)>>1) for v in range(65536))
 blobs={n:(a.assets/n).read_bytes() for n in ('tiles.bin','map.bin','palette.bin','palette-dim.bin')}
 assert list(map(len,blobs.values()))==[54*32,2048,30,30]
 pixels=0
 for t in range(54):
  for y in range(8):
   for x in range(8):
    expected=sum(((s[0x41F830+t*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
    actual=(blobs['tiles.bin'][t*32+y*4+x//2]>>(4*(x&1)))&15;assert actual==expected;pixels+=1
 coverage=[0]*1024;words=[None]*1024;calls=rectangles(s)
 for x,y in calls:
  for dy in range(8):
   for dx in range(16):
    idx=(y+dy)*32+(x+dx)%32;v=h(s,0x41F730+2*(dy*16+dx))
    words[idx]=(v&511)|((v&0x2000)>>4)|((v&0xC000)>>4)|((v&0x1E00)<<3);coverage[idx]+=1
 assert coverage==[1]*1024 and struct.pack('<1024H',*words)==blobs['map.bin']
 assert min(words)==512 and max(words)==565 and all(512<=v<=565 for v in words)
 for i in range(15):
  v=h(s,0x41FEF2+2*i);assert h(blobs['palette.bin'],2*i)==color(v) and h(blobs['palette-dim.bin'],2*i)==color((v&0xEEE)>>1)
 manifest=(a.assets/'manifest.json').read_bytes();meta=json.loads(manifest)
 assert meta['status']=='MODE23_BACKGROUND_ASSETS_PREPARED' and meta['source_sha256']==SOURCE
 assert not meta['actual_runtime_verified'] and not meta['mode23_implemented']
 assert meta['files']=={n:dict(bytes=len(b),sha256=sha(b)) for n,b in blobs.items()}
 assert {f.name for f in a.assets.iterdir()}==set(blobs)|{'manifest.json'}
 palette_contract=meta['source_contract']['palette']
 assert palette_contract['palette_zero_inherited'] and not palette_contract['palette_zero_bytes_emitted'] and palette_contract['caller_also_dims_inherited_source_color_zero']
 result=dict(status='MODE23_BACKGROUND_ASSETS_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),source_sha256=SOURCE,author_manifest_sha256=sha(manifest),files={n:dict(bytes=len(b),sha256=sha(b)) for n,b in blobs.items()},
  decoded_source_rectangle_calls=calls,complete_map_cells=1024,each_map_cell_written_once=True,source_tile_pixels=pixels,tile_count=54,native_relative_indices=[512,565],palette_colors=15,source_dim_equivalence_cases=65536,
  limits=['Only colors1..15 are exported. Source caller also dims inherited color0, which remains a runtime dependency.',
   'Artifacts have no ROM placement, native private state, menu binding or executable mode23 implementation. No visual/runtime claim.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
