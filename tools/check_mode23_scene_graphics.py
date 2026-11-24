"""Author ARM copy/graphics boundary checks with explicit presentation fixtures."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_scene_graphics import build,assembly
BASE=0x08000000;CODE=0x08E00000;ASSETS=0xE10000;CTX=0x02001018
NATIVE='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','output_dir'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 s=a.source.read_bytes();native=a.native.read_bytes();assert sha(native)==NATIVE
 data,meta=build(s,ASSETS);rows=meta['tables'];asm=assembly(rows)
 labels=set(re.findall(r'^(\w+):',asm,re.M));refs=set(re.findall(r'^bl (\w+)$',asm,re.M));external=sorted(refs-labels)
 entries=['m23_intro_prepare','m23_round_prepare','m23_failure_prepare','m23_completion_prepare'];names=entries+external
 prefix='\n'.join('.word '+n for n in names)+'\n'
 code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(prefix+asm+'\n'+'\n'.join(n+':bx lr' for n in external),CODE)[0]);sym=dict(zip(names,struct.unpack_from('<'+'I'*len(names),code)))
 rom=bytearray(native);rom[CODE-BASE:CODE-BASE+len(code)]=code;rom[ASSETS:ASSETS+len(data)]=data
 cases=0
 def run(entry,round=0,flag=0):
  nonlocal cases
  m=Machine(rom,seed=5,flags=(flag<<28)|31);m.r[4]=m.r[5]=CTX
  for first,size in ((0x06000000,0x10000),(0x05000000,0x400),(CTX,256),(0x04000000,0x60)):
   for i in range(size):m.put(first+i,(i*73+19)&255,1)
  m.put(CTX+0x2A,round,1);m.put(0x05000000,0x7FFF,2)
  before=dict(m.mem);events=[]
  def service(name):
   def f(vm):
    events.append((name,tuple(vm.r[:4])))
    if name=='m23_palette_prepare_fade_in':events.append(('palette_snapshot',bytes(vm.get(0x05000000+i,1) for i in range(256))))
   return f
  m.services={sym[n]:service(n) for n in external};regs=m.r[4:12].copy();sp=m.r[13];m.run(sym[entry],{m.r[14]},max_steps=130000)
  assert m.r[4:12]==regs and m.r[13]==sp
  expected=dict(before)
  def copy(name,to):
   x=rows[name];raw=rom[x['address']-BASE:x['address']-BASE+x['bytes']]
   expected.update((to+i,v) for i,v in enumerate(raw))
  def half(at,v):expected[at]=v&255;expected[at+1]=(v>>8)&255
  if entry=='m23_intro_prepare':
   copy('intro_tiles',0x06004000);copy('intro_map',0x0600F800);copy('intro_palette',0x05000002)
   half(0x05000000,0x3DEF);half(0x04000008,0x1F02);half(0x0400000A,0x1E03)
   half(CTX+0x34,112);half(CTX+0x36,72)
   assert [x[0] for x in events]==['m23_intro_resources']
  elif entry=='m23_round_prepare':
   key='last' if round==6 else 'round'
   copy(key+'_tiles',0x06004000);copy(key+'_palette',0x05000000);copy(key+'_map',0x0600F000);copy('power_map',0x0600F800)
   half(CTX+0x34,112);half(CTX+0x36,72)
   assert [x[0] for x in events]==['m23_aim_resources','m23_scroll_reset','m23_window_left','m23_window_right','m23_window_top','m23_window_bottom','m23_round_start_resources','m23_palette_prepare_fade_in','palette_snapshot','m23_display_low']
   assert events[-2][1]==bytes(expected[0x05000000+i] for i in range(256))
   assert [events[i][1][0] for i in (2,3,4,5,9)]==[180,224,112,112,37]
  elif entry=='m23_failure_prepare':
   copy('failure_palette',0x05000000);copy('failure_tiles',0x06004000);copy('failure_map',0x0600F800)
   half(CTX+0x3C,(before[CTX+0x3C]|before[CTX+0x3D]<<8)|0x6400);half(CTX+0x34,0xFFEC);half(CTX+0x36,76)
   assert events[-1][0]=='m23_sound' and events[-1][1][:2]==(0x24,4)
  else:
   copy('completion_tiles',0x06004000);copy('completion_palette',0x05000000)
   row=rows['completion_map'];raw=rom[row['address']-BASE:row['address']-BASE+row['bytes']]
   for y in range(18):expected.update((0x0600F800+y*64+i,v) for i,v in enumerate(raw[y*56:(y+1)*56]))
   assert events[1][0]=='m23_full_base_resources' and events[1][1][:3]==(CTX+0x34,11,24)
  for at,v in expected.items():assert m.get(at,1)==v,(entry,round,hex(at),m.get(at,1),v)
  changed={a for a,v,n in m.writes for a in range(a,a+n)}
  assert all(a in expected or sp-72<=a<sp for a in changed),'declared graphics/context/deadstack only'
  cases+=1
 for f in range(16):run('m23_intro_prepare',flag=f)
 for r in range(7):run('m23_round_prepare',round=r)
 run('m23_failure_prepare');run('m23_completion_prepare')
 meta.update(status='MODE23_GRAPHICS_AUTHOR_PASS',source_sha256=sha(s),native_sha256=sha(native),module_sha256=sha((ROOT/'tools/mode23_scene_graphics.py').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),asset_bytes=len(data),asset_sha256=sha(data),linked_bytes=len(code),linked_sha256=sha(code),ARM_cases=cases,imports=external,limits=['Native presentation/audio/window services are explicit fixtures; not actual game execution','No native ROM placement or scene entry installed','Inherited bank0tile0, palette0 and exclusive mirror lifecycle remain external contracts'])
 a.output_dir.mkdir(parents=True);(a.output_dir/'assets.bin').write_bytes(data);(a.output_dir/'report.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n');print(meta['status'],sha((a.output_dir/'report.json').read_bytes()))
if __name__=='__main__':main()
