"""Independent installed-image ownership and native lifecycle consumer review.

No emulator or save is used. Immediate DMA is hardware-modeled; native MP2K
stop/start boundary calls are recorded, not represented as audible playback.
"""
import argparse,copy,hashlib,inspect,json,re,struct,textwrap,types
from pathlib import Path
import verify_shoot_static_companion_clear as arm
import verify_shoot_caller_resident as scanner
from verify_shoot_child_contact_component import Machine as MulMachine
from mode23_linker import compose
import build_mode23_scene as builder
ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000;POOL=0x02010000;CONFIG=0x03002310
BEFORE='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
AFTER='B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def need(v,s):
 if not v:raise ValueError(s)
def memory(m,a,n):return bytes(m.get(a+i,1) for i in range(n))
def fill(m,a,b):
 for i,v in enumerate(b):m.put(a+i,v,1)

class Machine(MulMachine):
 def __init__(self,rom,flags=31):
  super().__init__(rom,seed=23,flags=flags);self.audio=[];self.dmas=[];self.hardware=False;self.mmio=[]
  self.services={0x0837DB84:lambda m:self.audio.append(('stop',m.r[0])),0x0837DB78:lambda m:self.audio.append(('start',m.r[0]))}
 def raw(self,at,v,size=4):super().put(at,v,size)
 def put(self,at,v,size=4,log=False):
  if self.hardware and at in (0x04000004,0x04000200,0x04000202):
   need(size==2,'reviewed MMIO halfword');self.mmio.append((at,v&65535))
   if at==0x04000202:v=self.get(at,2)&~v # IF write-one-to-clear.
   elif at==0x04000004:
    v=(self.get(at,2)&7)|(v&0xFFF8)
    match=self.get(0x04000006,2)==v>>8
    if match and v&0x20 and not v&4:self.raw(0x04000202,self.get(0x04000202,2)|4,2)
    v=(v|4) if match else (v&~4)
  super().put(at,v,size,log)
  if at==0x040000DE and v&0x8000:
   need(size==2 and v in (0x8000,0x8400,0x8500),'bounded immediate DMA3')
   src,dst,n=self.get(0x040000D4),self.get(0x040000D8),self.get(0x040000DC,2)
   unit=4 if v&0x400 else 2;fixed=bool(v&0x100)
   need(0<n<=0x4000,'bounded DMA count');self.dmas.append((src,dst,n,unit,fixed))
   data=memory(self,src,unit if fixed else n*unit)
   if fixed:data*=n
   for i,x in enumerate(data):super().put(dst+i,x,1,True)

# Extend only immediate halfword pre/post writeback; keep frozen interpreters.
_run=textwrap.dedent(inspect.getsource(arm.Machine.run))
start=_run.index('elif w & 0x0E000090 == 0x00000090:')
end=_run.index('elif w & 0x0C000000 == 0:',start)
_run=_run[:start]+'''elif w & 0x0FC000F0 == 0x00000090:
            need(not w & 0x00300000, 'ordinary non-S MUL')
            self.r[(w >> 16) & 15] = (self.r[w & 15] * self.r[(w >> 8) & 15]) & 0xFFFFFFFF
        elif w & 0x0E000090 == 0x00000090:
            need(w & 0x400000, 'immediate halfword')
            offset=((w>>4)&0xF0)|(w&15)
            base,reg,kind=(w>>16)&15,(w>>12)&15,(w>>5)&3
            updated=(self.r[base]+(offset if w&0x800000 else -offset))&0xFFFFFFFF
            address=updated if w&0x1000000 else self.r[base]
            if w&0x100000:
                value=self.get(address,1 if kind==2 else 2)
                self.r[reg]=(signed(value,8 if kind==2 else 16) if kind in (2,3) else value)&0xFFFFFFFF
            else:
                need(kind==1,'STRH only');self.put(address,self.r[reg],2,True)
            if w&0x200000 or not w&0x1000000:self.r[base]=updated
        '''+_run[end:]
_ns=dict(arm.__dict__);exec(compile(_run,__file__+':halfword-extension','exec'),_ns);Machine.run=_ns['run']

def installed(before,after,source,meta,source_audio,audio_contract):
 need((sha(before),sha(after),sha(source))==(BEFORE,AFTER,SOURCE),'exact immutable inputs')
 spans=sorted((r['offset'],r['offset']+r['size'],r) for r in meta['writes'])
 need(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])),'disjoint declared spans')
 inverse=bytearray(after)
 for lo,hi,row in spans:
  need(sha(before[lo:hi])==row['before_sha256'] and sha(after[lo:hi])==row['after_sha256'],'each span actual bytes')
  inverse[lo:hi]=before[lo:hi]
 need(inverse==before,'whole image inverse, no undeclared changes')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((0xD90000,0x1000000),)),argdefs=scanner.inbound.__defaults__)
 hits=scan(before);targets={target&0x1FFFFFF for _,_,target in hits}
 for lo,hi,row in spans:
  if lo>=0xD90000:
   need(before[lo:hi]==b'\xff'*(hi-lo),'FF ownership')
   need(not any(lo<=t<hi for t in targets),'strict zero inbound, no exceptions')
 need(not any(0xDB0404<=t<0xDB5C04 for t in targets),'whole code/root reservation')
 values,_=builder.bodies(source,before,meta['resources'],meta['graphics'],source_audio,audio_contract)
 labels=re.findall(r'^(\w+):','\n'.join(values),re.M)
 code,sym,link=compose(values,BASE+meta['code']['start'],labels)
 need(code==after[meta['code']['start']:meta['code']['end']],'all installed linked bytes reconstructed')
 need(link['direct_branches_checked']==512 and len(link['native_veneers'])==19,'complete linked branch census')
 need(all(after[t-BASE:t-BASE+4]==before[t-BASE:t-BASE+4] for t in [x['target'] for x in link['native_veneers'].values()]),'all native entry words unchanged')
 return sym,dict(writes=len(spans),allocations=len(meta['allocations']),declared=sum(hi-lo for lo,hi,_ in spans),changed=sum(x!=y for x,y in zip(before,after)),conservative_hits=len(hits),direct_branches=512,native_veneers=19)

def empty(rom):
 m=Machine(rom)
 fill(m,0x03000000,bytes(0x8000));fill(m,0x0201DC00,bytes(0x100));fill(m,0x05000000,bytes(0x400));fill(m,0x04000000,bytes(0x210))
 for i in range(52):fill(m,POOL+i*0x118,bytes([0xE5])*0x118);m.put(POOL+i*0x118+0x10,0,2)
 for at in (0x03001338,0x0300133C,0x03001340,0x03001344):m.put(at,0)
 for at in range(CONFIG,CONFIG+0x30):m.put(at,0,1)
 m.hardware=True
 return m
def invoke(m,addr,limit=300000):
 sp,lr,regs=m.r[13],m.r[14],m.r[4:12].copy()
 try:m.run(addr,{lr},max_steps=limit)
 except Exception as e:raise RuntimeError((hex(addr),hex(m.r[15]-8),[hex(x) for x in m.r],m.calls[-6:])) from e
 need(m.r[13]==sp,'balanced call stack')
 return regs

def allocate_native(m,callback,priority):
 sp=m.r[13];m.r[13]-=12
 for off,value in ((0,priority),(4,0),(8,callback)):m.put(m.r[13]+off,value)
 m.r[11]=0;invoke(m,0x08011AC4);m.r[13]=sp
 return m.r[0]

def old_irq(m):
 # Exact startup relocation, not a replacement service for C9000.
 fill(m,0x03000DB0,m.rom[0xC9008:0xC9074])
 m.raw(0x04000004,3,2);m.raw(0x04000006,160,2)
 invoke(m,0x0801F590);invoke(m,0x0801F2F4)
 need(m.get(0x030012E0)==0x0801F5EC and m.get(0x03004574)==3,'native old IRQ registration')
 epochs=[]
 for expected in (16,21,136,144):
  compare=m.get(0x04000004,2)>>8;need(compare==expected,'actual native compare progression')
  m.raw(0x04000006,compare,2);invoke(m,0x0801F5EC)
  epochs.append(dict(compare=compare,queue=m.get(0x03004574),counter=m.get(0x03004668,2)))
 need(m.get(0x03004574)==0 and m.get(0x03004668,2)==4,'last native line job drained')
 need(m.get(0x04000004,2)>>8==144,'last compare remains144, not152')
 return epochs

def owned_entry(m,headers):
 # A checker contract, NOT runtime guards inserted in the game.
 need(m.get(CONFIG,2)==23,'proof requires registered mode23')
 need(all(not m.get(x+0x10,2)&2 for x in headers),'proof requires retired charselect tasks')
 need(m.get(0x03004574)==0,'proof requires drained old queue')
 need(m.get(0x030012E0)==0x0801F5EC,'proof requires known old callback')
 need(m.get(0x03004668,2)>=4,'proof requires exhausted old raster cases')

def predecessor(rom):
 m=empty(rom);m.r[11]=0
 keep=allocate_native(m,0x080159B4,0xF0000000)
 need(keep==POOL,'persistent native dispatcher allocation')
 invoke(m,0x080818C0)
 need(m.get(0x03001338,2)==7,'six charselect tasks plus persistent dispatcher')
 headers=[POOL+(i+1)*0x118 for i in range(6)]
 need([m.get(x) for x in headers]==[0x080819E8,0x08082C7C,0x08082324,0x08082714,0x08082098,0x0808313C],'actual task callback population')
 epochs=old_irq(m)
 terminals=(0x08082D50,0x08082438,0x080827E8,0x080820C8,0x08083118)
 m.put(headers[0]+0x18,5,2);m.put(0x03004738,0,2)
 for i,at in enumerate(terminals,1):
  m.put(0x0300133C,headers[i]);invoke(m,at)
  need(not m.get(headers[i]+0x10,2)&2,'retired predecessor producer')
 need(m.get(0x03004738,2)==0xF80 and m.get(0x03001338,2)==2,'all five producer retirement bits')
 m.put(0x0300133C,headers[0]);m.put(CONFIG+0x1A,8,2);m.put(CONFIG,4,2)
 for bit in (0x80,0x100,0x200,0x400,0x800):
  trial=copy.deepcopy(m);trial.put(0x03004738,0xF80^bit,2);invoke(trial,0x08081F70)
  need(trial.get(CONFIG+4,2)==0 and trial.get(headers[0]+0x10,2)&2,'missing predecessor completion does not exit')
 invoke(m,0x08081F70)
 need(m.get(0x03001338,2)==1 and m.get(keep+0x10,2)&2,'only predecessor scene tasks retire')
 need([m.get(CONFIG+x,2) for x in (4,6,8)]==[1,5,0],'actual normal choice5 request')
 need(m.get(0x030012B8,1)==m.get(0x030012B9,1)==0,'old logical camera reset')
 # Actual transition consumer, with the live dispatcher as current task.
 m.put(0x0300133C,keep);m.r[5]=CONFIG
 sp=m.r[13];m.r[13]-=4;m.put(m.r[13],m.r[14]);m.run(0x08015AE4,{m.r[14]},max_steps=200)
 need(m.r[13]==sp,'native transition returns dispatcher saved LR')
 owned_entry(m,headers)
 rejected=0
 for address,value,size in ((CONFIG,4,2),(headers[1]+0x10,2,2),(0x03004574,1,4),(0x030012E0,0x08000000,4),(0x03004668,3,2)):
  trial=copy.deepcopy(m);trial.put(address,value,size)
  try:owned_entry(trial,headers)
  except ValueError:rejected+=1
 need(rejected==5,'negative proof-precondition cases fail closed')
 return m,dict(native_constructor=0x080818C0,producer_terminals=list(terminals),retirement_mask=0xF80,persistent_dispatcher=keep,remaining_tasks=1,irq_epochs=epochs,missing_completion_cases=5,rejected_proof_preconditions=rejected,runtime_guard=False)

def irq_contract(rom,sym):
 target=sym['m23_retire_vcount'];create=sym['m23_scene_create']
 callers=[]
 for at in range(0xDB0420,0xDB4400,4):
  w=u(rom,at)
  if w&0x0E000000==0x0A000000 and BASE+at+8+arm.signed(w&0xFFFFFF,24)*4==target:callers.append(BASE+at)
 need(callers==[create+8],'sole explicit call immediately after display disable')
 need(rom.count(struct.pack('<I',target))==0,'no encoded helper function pointers')
 cases=0
 for flags in range(16):
  for bit in range(16):
   for complement in (0,1):
    ie=(1<<bit)^(0xFFFF if complement else 0);pending=(1<<((bit+5)%16))^(0xFFFF if not complement else 0)
    line=bit*17 if complement and bit<14 else (bit*17+1)%228
    disp=((bit*17)<<8)|0xF8|(bit&3)|(4 if line==bit*17 else 0)
    m=Machine(rom,(flags<<28)|31);m.raw(0x04000200,ie,2);m.raw(0x04000202,pending,2);m.raw(0x04000004,disp,2);m.raw(0x04000006,line,2);m.hardware=True
    before=m.r.copy();cpsr=m.cpsr;invoke(m,target)
    need(m.get(0x04000200,2)==ie&~4 and m.get(0x04000202,2)==pending&~4,'only VCOUNT IE/pending retired')
    need(m.get(0x04000004,2)==disp&~0x20,'compare, status, HBlank/VBlank requests preserved')
    need(m.r[3:15]==before[3:15] and m.cpsr==cpsr,'helper nonargument registers/flags preserved')
    need(m.mmio==[(0x04000200,ie&~4),(0x04000004,disp&~0x20),(0x04000202,4)],'exact retirement MMIO order and W1C mask')
    cases+=1
 # Every physical scanline and every compare value, independent of elapsed time.
 idle=0
 for compare in range(256):
  for line in range(228):
   disp=(compare<<8)|0x18
   raised=(line==compare and bool(disp&0x20))
   need(not raised,'disabled request cannot relatch IF during arbitrarily long idle');idle+=1
 return dict(helper=target,sole_caller=callers[0],actual_arm_cases=cases,long_idle_line_compare_cases=idle,hardware_model='IF W1C and DISPSTAT bits0..2 read-only; request bit5 gates VCOUNT IF assertion',runtime_guard=False)

def flush_oam(m,count):
 staged=memory(m,0x03001428,count*8);tiles=memory(m,0x02000000,count*32)
 m.run(0x08011708,{0x080117D0},max_steps=20000)
 need(memory(m,0x07000000,count*8)==staged,'actual native OAM flush copies all used slots')
 if count:need(memory(m,0x06010000,count*32)==tiles,'actual native OBJ tile upload')
 need(all(m.get(0x07000000+i*8)==0x00F002B0 and m.get(0x07000004+i*8,2)==0 for i in range(count,128)),'every remaining physical OAM slot hidden')
 need(m.get(0x030012CA,1)==0,'shared OAM cursor resets')

def scene_native(m,sym,source):
 # The normal dispatcher invokes the actual installed constructor, no summary.
 m.put(0x0300133C,POOL);m.r[2]=1;m.raw(0x04000006,160,2)
 irq_before=(m.get(0x04000200,2),m.get(0x04000004,2),m.get(0x04000202,2),m.get(0x030012E0))
 invoke(m,0x080159B4)
 roots=[POOL+i*0x118 for i in range(1,4)]
 controller=[x for x in roots if m.get(x)==sym['m23_cb_A56B']]
 need(len(controller)==1 and m.get(POOL)==0x08015AB4,'installed constructor registered through actual dispatcher')
 ctx=controller[0]+0x18;m.r[4]=m.r[5]=ctx
 need(m.get(0x03001338,2)==4 and m.get(ctx+0xFC)==ctx,'three owned roots plus dispatcher')
 need(m.get(0x04000200,2)==irq_before[0]&~4 and m.get(0x04000004,2)==irq_before[1]&~0x20 and m.get(0x04000202,2)==irq_before[2]&~4,'constructor owns exact IRQ retirement')
 need(m.get(0x030012E0)==irq_before[3],'retired callback storage is unchanged')
 owned_mmio_end=len(m.mmio)
 shared=m.get(POOL+0x10,2)
 # Linked intro, all seven source populations, native presentation and OAM.
 invoke(m,sym['m23_intro_prepare'])
 need(m.get(0x04000008,2)==0x1F02 and m.get(0x0400000A,2)==0x1E03,'BG0/BG1 charbase0 and F800/F000 ownership')
 cases=[]
 for round_no in range(7):
  m.r[4]=m.r[5]=ctx;m.put(ctx+0x2A,round_no,1)
  invoke(m,sym['m23_participants_create'])
  count=source[0x74A34E+2*round_no]
  need(m.get(ctx+0x2B,1)==count and m.get(0x03001338,2)==4+count,'actual source round task population')
  actors=[m.get(ctx+0xC+i*4)+0x18 for i in range(count)]
  need(len(set(actors))==count and all(m.get(x+0xFC)==ctx for x in actors),'disjoint participants retain private context')
  for actor in actors:
   m.r[0]=actor;invoke(m,sym['m23_draw'])
  n=m.get(0x030012CA,1);need(0<n<128,'actual layouts fit shared OAM capacity')
  flush_oam(m,n)
  m.r[4]=m.r[5]=ctx
  invoke(m,sym['m23_round_prepare'])
  need(m.get(ctx+0xD4,2)==16,'private fade counter initialized')
  if round_no==0:
   goal=memory(m,0x0203E000,0x100)+memory(m,0x0203E200,0x100)
   for tick in range(16):
    invoke(m,sym['m23_palette_fade_in']);need(m.r[0]==(tick==15),'installed fade-in completion epoch')
   need(memory(m,0x05000000,0x100)+memory(m,0x05000200,0x100)==goal,'actual native snapshot and full source fade-in restore shared palettes')
   invoke(m,sym['m23_palette_snapshot'])
   for tick in range(32):
    invoke(m,sym['m23_palette_fade_out']);need(m.r[0]==(tick==31),'installed alternating fade-out completion epoch')
   need(memory(m,0x05000000,0x100)+memory(m,0x05000200,0x100)==bytes(0x200),'installed fade-out clears both owned palette halves')
  need(m.get(0x030012BC,1)==0xB4 and m.get(0x030012BD,1)==0xE0 and m.get(0x030012BE,1)==m.get(0x030012BF,1)==0x70,'correct WIN1 shadows')
  # Actual generic display/window projection, bounded before OAM flush.
  m.r[9]=0x04000000;m.run(0x08011638,{0x080116DC},max_steps=400)
  need(m.get(0x04000042,2)==0xBCE8 and m.get(0x04000046,2)==0x7878,'native window margins and physical WIN1 ownership')
  m.r[4]=m.r[5]=ctx
  invoke(m,sym['m23_src_A50D'])
  need(m.get(0x03001338,2)==4 and all(not m.get(x-8,2)&2 for x in actors),'all round actors retire individually')
  need(m.get(POOL+0x10,2)==shared,'shared dispatcher survives participant cleanup')
  cases.append(dict(round=round_no,participants=count,physical_oam_slots=n))
 m.r[4]=m.r[5]=ctx;invoke(m,sym['m23_src_A0FD'])
 need(m.get(0x03001338,2)==1 and m.get(POOL+0x10,2)==shared,'all scene roots retire; dispatcher survives')
 need([m.get(CONFIG+x,2) for x in (4,6,8)]==[1,0,0],'normal exit request')
 flush_oam(m,0)
 m.put(0x0300133C,POOL);invoke(m,0x08015AB4)
 need(m.get(CONFIG,2)==20 and memory(m,CONFIG+4,6)==bytes(6) and m.get(POOL)==0x080159B4,'actual common dispatcher completes normal mode20 transition')
 need(len(m.mmio)==owned_mmio_end,'tested owned scene paths do not reinstall a line IRQ')
 # Next legitimate native owner installs its queue/callback before re-enabling.
 # Mode20 is NOT asserted to install a line IRQ.
 next_owner=copy.deepcopy(m);next_owner.raw(0x04000006,160,2)
 invoke(next_owner,0x0801F590);invoke(next_owner,0x0801F2F4)
 need(next_owner.get(0x030012E0)==0x0801F5EC and next_owner.get(0x03004574)==3 and next_owner.get(0x04000004,2)>>8==16,'next legitimate owner installs fresh queue/callback/compare')
 need(next_owner.get(0x04000004,2)&0x20 and next_owner.get(0x04000200,2)&4,'native D18 enables only after next owner setup')
 return dict(context=ctx,palette_fade_in_calls=16,palette_fade_out_calls=32,rounds=cases,retained_dispatcher=POOL,exit_mode=20,next_irq_owner=0x0801F2F4,native_audio_boundary_calls=m.audio)

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('before','component','source','manifest','source-audio-report','audio-contract','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 before,after,source=a.before.read_bytes(),a.component.read_bytes(),a.source.read_bytes();meta=json.loads(a.manifest.read_bytes())
 sym,own=installed(before,after,source,meta,a.source_audio_report.read_bytes(),a.audio_contract.read_bytes())
 irq=irq_contract(after,sym)
 mutations=[]
 for offset,word,name in ((12,0xE3C22006,'mask also HBlank'),(24,0xE3C22030,'disable also HBlank request'),(32,0xE3A02006,'ack also HBlank pending')):
  bad=bytearray(after);struct.pack_into('<I',bad,sym['m23_retire_vcount']-BASE+offset,word)
  try:irq_contract(bytes(bad),sym)
  except ValueError:mutations.append(name)
 need(len(mutations)==3,'independent MMIO matrix rejects ownership mutations')
 irq['rejected_mutations']=mutations
 m,pred=predecessor(after)
 lifecycle=scene_native(m,sym,source)
 result=dict(status='MODE23_COMPONENT_NATIVE_LIFECYCLE_PASS',tool_sha256=sha(Path(__file__).read_bytes()),component_sha256=sha(after),manifest_sha256=sha(a.manifest.read_bytes()),source_audio_sha256=sha(a.source_audio_report.read_bytes()),audio_contract_sha256=sha(a.audio_contract.read_bytes()),ownership=own,predecessor=pred,irq=irq,lifecycle=lifecycle,limits=['Actual ARM executes in an independent instruction interpreter with immediate DMA and documented MMIO semantics; no emulator gameplay or physical playback is claimed.','Normal charselect handoff is a verified application precondition; the production IRQ helper is unconditional, not runtime guarded.','MP2K stop/start are recorded boundary services. The title menu producer remains unexposed.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
