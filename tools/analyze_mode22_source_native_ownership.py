"""Bounded read-only source mode22 and current native ownership map.

This reports decoded source contracts and existing native service/storage
boundaries. It does not install mode22 or claim native gameplay parity.
"""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from capstone.x86 import X86_OP_IMM
import verify_mode23_eligibility_storage as storage
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE='B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
CS=0x7848F0

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
 if not v:raise ValueError(s)
def hits(b,pat):
 out=[];at=b.find(pat)
 while at>=0:out.append(at);at=b.find(pat,at+1)
 return out

def graph(source,roots):
 decoder=Cs(CS_ARCH_X86,CS_MODE_16);decoder.detail=True
 pending=list(roots);seen={};imports=set();edges=[]
 while pending:
  at=pending.pop()
  if at in seen:continue
  need(0<=at<0x92D,'bounded mode22 code target')
  ins=list(decoder.disasm(source[CS+at:CS+at+15],at,count=1));need(len(ins)==1,'source instruction decode')
  i=ins[0];seen[at]=i
  if i.mnemonic in ('ret','retf'):continue
  fall=at+i.size
  if i.mnemonic=='lcall':
   seg,off=[x.imm for x in i.operands];edges.append((at,seg,off))
   if seg==0x848F:pending.append(off)
   else:imports.add((seg,off))
  elif i.mnemonic=='call':
   need(i.operands[0].type==X86_OP_IMM,'no unbounded indirect near call');pending.append(i.operands[0].imm)
  elif i.mnemonic=='jmp' or i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
   need(i.operands[0].type==X86_OP_IMM,'no unbounded indirect branch');pending.append(i.operands[0].imm)
   if i.mnemonic=='jmp':continue
  pending.append(fall)
 rows=[dict(raw=CS+a,offset=a,bytes=i.bytes.hex(),op=i.mnemonic,args=i.op_str) for a,i in sorted(seen.items())]
 return dict(roots=list(roots),instructions=len(rows),instructions_sha256=sha(b''.join(bytes.fromhex(r['bytes']) for r in rows)),far_imports=[list(x) for x in sorted(imports)],far_edges=[list(x) for x in sorted(edges)],listing=rows)

def highest(values):
 return next((i for i in range(10,-1,-1) if values[i]),-1)
def award(values,index):
 out=list(values)
 if out[10] or all(x>=9 for x in out[index:]):return out,False
 while True:
  out[index]+=1
  if out[index]<10:break
  out[index]=9;index+=1
  if index==11:break
  out[index-1]=0
 return out,True

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 s,b=a.source.read_bytes(),a.native.read_bytes();need(sha(s)==SOURCE and sha(b)==NATIVE,'immutable source/current native')
 need(s[0x74FBD4:0x74FBE0]==bytes.fromhex('00008f8401048f848702a34f'),'source mode22 callback triple')
 need(s[0x784C1B:0x784C1E]==bytes.fromhex('b90100'),'initializer returns CX=1')
 table=struct.unpack_from('<I',b,0x15B70)[0]-0x08000000
 need(b[table+22*12:table+23*12]==bytes(12),'current mode22 callback row is absent')
 trans=struct.unpack_from('<I',b,0x15CC8)[0]-0x08000000
 need(s[0x74FA30+3*6+1]==22,'source title choice1 route22')
 need(s[0x74FA30+22*6]==20,'source mode22 choice0 route20')
 view=graph(s,(0,0x401,0x4BF,0x5B9,0x647,0x677))
 producers=graph(s,(0x728,0x81E,0x8C0))
 callers={f'{x:04X}':hits(s,b'\x9a'+struct.pack('<HH',x,0x848F)) for x in (0x728,0x81E,0x7FA)}
 need(callers['0728']==[0x77B106] and callers['081E']==[0x741EAD],'bounded direct award/loss caller census')
 need(callers['07FA']==[0x741E40,0x77420A,0x78021B,0x780317,0x784991,0x784A4E,0x785178],'all encoded highest-counter direct readers')
 need(s[0x784DD0:0x784DD7]==bytes.fromhex('26a15c38a9c000') and s[0x784EB6:0x784EBD]==bytes.fromhex('26a15c38a9c000'),'both input callbacks use repeat-qualified C0')
 need(s[0x751990:0x751993]==bytes.fromhex('a35c38') and struct.unpack_from('<I',b,0x11A60)[0]==0xE1C800BA,'paired repeat-input final store')
 thresholds=[list(struct.unpack_from('<11H',s,0x785092+22*d)) for d in range(4)]
 need(all(row==sorted(row) and row[-1]==65535 for row in thresholds),'four bounded unsigned ranking rows')
 rank_cases=0
 for row in thresholds:
  for value in range(65536):
   rank=next(i for i,t in enumerate(row) if value<=t);need(0<=rank<=10,'sentinel prevents index overrun');rank_cases+=1
 cases=[]
 for index in range(11):
  for pattern in (0,1,8,9):
   v=[pattern]*10+[0];out,changed=award(v,index)
   need(all(0<=x<=9 for x in out) and (out[:index]==v[:index]),'source decimal carry preserves lower ranks')
   cases.append(dict(index=index,initial=pattern,result=out,changed=changed))
 need(highest([0]*11)==-1 and highest([0]*10+[1])==10,'three-view selector endpoints')
 need(award([9]*10+[1],0)==([9]*10+[1],False),'special tag blocks further awards')
 # Reuse the already independent encoded census with only the new exact image pin.
 census=types.FunctionType(storage.source_and_storage.__code__,dict(storage.__dict__,REFERENCE=NATIVE))
 device=census(s,b)
 need(struct.unpack_from('<IHHB',b,0x3877D0)==(512,64,0x300,6),'native physical EEPROM capacity')
 spans={}
 for name,lo,hi in (
  ('view_init',CS,CS+0x336),('view_ctor',CS+0x401,CS+0x4BF),('normal_input_draw',CS+0x4BF,CS+0x5A5),('special_input_name',CS+0x5B9,CS+0x647),('line_irq',CS+0x647,CS+0x677),('frame_palette',CS+0x677,CS+0x728),('rank_award',CS+0x728,CS+0x7A2),('highest',CS+0x7FA,CS+0x81E),('linked_result',CS+0x81E,CS+0x8C0),('decimal_carry',CS+0x8C0,CS+0x92D),('new_record_clear',0x785E98,0x785EA9),('name_writer',0x774BB0,0x774BD4),('tag_unlock_high',0x77856D,0x7785B3),('tag_unlock_mid',0x778629,0x778674),('record_transfer',0x7860CF,0x786147),('source_repeat',0x751933,0x751993)):
  spans[name]=dict(start=lo,end=hi,sha256=sha(s[lo:hi]))
 assets=[]
 def asset(name,bank,seg,off,size,destination,kind):
  raw=(bank&127)*65536+((seg*16+off)&65535)
  need(raw+size<=len(s),'source asset bounds')
  assets.append(dict(name=name,source=raw,size=size,sha256=sha(s[raw:raw+size]),source_destination=destination,kind=kind))
 asset('shared_bg_tiles',0xC2,0x3000,0,0xC40,0xB080,'planar4bpp')
 asset('shared_bg_palette',0xC2,0x3000,0xC40,32,0xFE00,'RGB444')
 for name,off,size,dst,kind in (
  ('scroll_map',0x5B78,0x480,0x800,'32x18 map'),('ordinary_base_tiles',0x3A98,0x600,0x9600,'planar4bpp'),('ordinary_base_palette',0x3DB8,32,0xFF60,'RGB444'),('ordinary_base_map',0x3DD8,8*6*2,0x1000,'rectangle8x6'),('digit_tiles',0x5FF8,0x160,0x4020,'planar4bpp'),('digit_palette',0x6158,32,0xFFE0,'RGB444'),('ordinary_ten_palettes',0x3680,0x140,0xFE20,'RGB444'),('special_tiles',0x2E80,0xA80,0x7200,'planar4bpp'),('special_palette',0x37C0,32,0xFE20,'RGB444'),('special_map',0x3A20,10*6*2,0x1000,'rectangle10x6'),('name_palette',0x6178,32,0xFF00,'RGB444'),('special_banner_map',0x6198,28*2*2,0x1000,'rectangle28x2')):
  asset(name,0xAD,0x2936,off,size,dst,kind)
 for i in range(10):
  dst,off=struct.unpack_from('<HH',s,CS+0x347+i*4);asset(f'ordinary_tag_tiles_{i}',0xAD,0x2936,off,0x400,0x4000+dst,'planar4bpp')
  for key,table,size,dst,kind in (('rank_tiles',0x3BF,0x200,0x9A00,'planar4bpp'),('rank_palette',0x3D5,32,0xFF80,'RGB444'),('rank_map',0x3EB,32,0x1000,'rectangle8x2')):
   off=struct.unpack_from('<H',s,CS+table+i*2)[0];asset(f'{key}_{i}',0xAD,0x2936,off,size,dst,kind)
 for name,off,dst in (('common_edge',0x5AB8,0x800),('special_top',0x5AF8,0x800),('special_bottom',0x5B38,0xC40)):
  asset(name,0xAD,0x2936,off,64,dst,'32 map cells')
 asset('special_portrait_tiles',0xBA,0x25FA,0,0x700,0x7E80,'planar4bpp')
 asset('special_portrait_palette',0xBA,0x25FA,0x700,32,0xFE40,'RGB444')
 result=dict(status='MODE22_SOURCE_NATIVE_OWNERSHIP_MAP',tool_sha256=sha(Path(__file__).read_bytes()),source_sha256=SOURCE,native_sha256=NATIVE,source_spans=spans,view_graph=view,producer_graph=producers,encoded_far_callers=callers,rank_thresholds=thresholds,rank_domain_cases=rank_cases,carry_model_cases=cases,assets=assets,storage=device,storage_proposal=dict(source_tail=[0xC0,0xE8],payload_bytes=40,excluded_blocks=[25,26],candidate_blocks=list(range(27,34)),candidate_bytes=56,status='proposal only: layout, version/checksum, reset/load/write integration and RAM ownership still required'),native_services=dict(allocator=0x08011AC4,release=0x08011BE4,priority=0x08011E54,shared_oam=0x08011708,repeat_input=0x0300130A,copy_words=0x08000B84,audio_request=0x080D15C0,audio_service=0x080D1500,irq_enable=0x08000D18,mode20_constructor=0x08040470),limits=['Read-only source and native ownership map; no installed mode22 or native source-parity execution.','Ranking/carry cases are source-derived models, not an x86 execution claim.','EEPROM census covers encoded ARM/Thumb API references and veneer pointers; it is not a proof against arbitrary computed calls.','Native RAM relocation and counter producer hook placement are separate work. Source audioFC/font services and source IRQ translation remain explicit implementation dependencies.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
