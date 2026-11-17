"""Bounded native20 title-resource consumer and DMA lifetime verification."""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
BASE=0x08000000
BEFORE='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST,LIMIT=0xD8B400,0xD8B440
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def branch(a,z,link=False):return (0xEB000000 if link else 0xEA000000)|(((z-a-8)//4)&0xFFFFFF)
def rgb(v):return sum((2*((v>>s)&15)+bool((v>>s)&15))<<d for s,d in ((8,0),(4,5),(0,10)))

class DMA(Machine):
 """Actual native0B84 instructions; immediate DMA3 transfer is explicit model."""
 def __init__(self,*a,**k):super().__init__(*a,**k);self.transfers=[]
 def put(self,address,value,size=4,log=False):
  super().put(address,value,size,log)
  if address==0x040000DE and size==2:
   need(value==0x8400,'only native immediate32bit DMA control')
   src,dst,n=self.get(0x040000D4),self.get(0x040000D8),self.get(0x040000DC,2)
   need(BASE<=src and src+n*4<=BASE+len(self.rom),'ROM DMA source bound')
   need((0x06003200<=dst and dst+n*4<=0x06007200) or (dst==0x05000020 and n==0x40),'typed tile/palette DMA owner')
   self.transfers.append((src,dst,n))
   data=self.rom[src-BASE:src-BASE+n*4]
   for i,v in enumerate(data):super().put(dst+i,v,1,True)

def fixture(rom,flags):
 m=DMA(rom,seed=4,flags=(flags<<28)|0x1F);original=m.r[:]
 # The unchanged initializer prologue saved r0..r5/lr before this transfer hook.
 m.r[13]-=28
 for i,v in enumerate(original[:6]+[original[14]]):m.put(m.r[13]+4*i,v)
 m.put(0x03004738,0x101,2);m.put(0x0300133C,0x0201F000);m.put(0x0201F000,0x08040668)
 return m,original

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before','after','source','owner','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report');before,after,s=(getattr(a,k).read_bytes() for k in ('before','after','source'))
 need((sha(before),sha(s))==(BEFORE,SOURCE) and len(after)==len(before)==0x1000000,'immutable inputs')
 helper=struct.pack('<12I',0xE59F5018,0xE59F4018,0xE3A02B02,branch(FIRST+12,0xB84,True),0xE59F4010,0xE3A02D13,0xE59FE00C,branch(FIRST+28,0xB84),0x06003200,0x08712680,0x08717F40,0x080406EC)
 expected=bytearray(before);expected[FIRST:FIRST+48]=helper
 for site,value in ((0x406DC,branch(0x406DC,FIRST)),(0x4072C,0x086FBDA8),(0x4073C,0x086FC198)):struct.pack_into('<I',expected,site,value)
 need(after==expected,'wholeimage equals only48bytehelper andthreeoldwords')
 need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'new reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 need(not scan(before),'zero conservative inbound references')
 ownerraw=a.owner.read_bytes();owner=json.loads(ownerraw)
 need(owner['output_sha256']==BEFORE and owner['reservations']==[[0xD8AC00,0xD8B400]],'prior Iraira owner')
 for w in owner['writes']:
  x,z=w['offset'],w['offset']+w['size'];need(before[x:z]==after[x:z],'all prior Iraira writes retained')
 # Establish this fixed-language consumer selects the same already-proved title assets.
 ins={i.address:(i.mnemonic,i.op_str) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(s[0x7827CA:0x7828E0],0x7827CA)}
 for at,pair in {0x7827FC:('mov','al, 0xca'),0x78282B:('mov','ax, 0x380c'),0x782830:('mov','si, 0'),0x782848:('mov','di, 0x7200'),0x78284B:('mov','si, 0x3f0')}.items():need(ins.get(at)==pair,'source fixed title transfer anchor')
 need(('mov','cx, 0x1980') in ins.values() and ('mov','si, 0x35f0') in ins.values() and ('mov','cx, 0x60') in ins.values(),'source tile/palette extents')
 for i in range(504):
  source=h(s,0x4A80C0+i*2);v=h(after,0x6FBDA8+i*2)
  need((v&1023)==((source&511)|((source&0x2000)>>4)) and v>>12==(source>>9)&15 and bool(v&0x400)==bool(source&0x4000) and bool(v&0x800)==bool(source&0x8000),'new map reference names source map')
 for i in range(96):need(h(after,0x6FC198+i*2)==rgb(h(s,0x4AB6B0+i*2)),'new palette reference names six source rows')
 need(before[0x6FC198+192:0x6FC298]==after[0x6FC198+192:0x6FC298],'two retained native palette rows unchanged')
 need(u(after,0x40728)==0x0600F800 and u(after,0x40738)==0x05000020,'native map and palette destinations retained')
 need(before[0x40448:0x406DC]==after[0x40448:0x406DC] and before[0x4074C:0x407BC]==after[0x4074C:0x407BC],'mode20 task timing/fade/retirement unchanged')
 cases=0
 for flags in range(16):
  m,regs=fixture(after,flags);old,_=fixture(before,flags)
  m.run(0x080406DC,{regs[14]});old.run(0x080406DC,{regs[14]})
  need(m.transfers==[(0x08712680,0x06003200,0x800),(0x08717F40,0x06005200,0x4C0),(0x086FC198,0x05000020,0x40)],'actual nativeDMA two tile extents then palette')
  need(old.transfers==[(0x0808BB58,0x06003200,0x1000),(0x0808FB58,0x05000020,0x40)],'retained original nativeDMA ABI')
  want=after[0x712680:0x714680]+after[0x717F40:0x719240]
  need(bytes(m.get(0x06003200+i,1) for i in range(0x3300))==want,'mode20 VRAM source title transfer exact')
  need(bytes(m.get(0x05000020+i,1) for i in range(256))==after[0x6FC198:0x6FC298],'mode20 palette transfer exact')
  need(m.r[:15]==old.r[:15] and m.cpsr==old.cpsr and m.r[13]==regs[13],'full tail register flags and stack parity')
  need(m.get(0x03004738,2)==old.get(0x03004738,2)==0x103 and m.get(0x0201F000)==old.get(0x0201F000)==0x0804074C,'sameflag2 and callback handoff')
  cases+=1
 result=dict(status='MODE20_TITLE_CONSUMERS_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),before_sha256=sha(before),after_sha256=sha(after),
  spans=4,declared_bytes=60,changed_bytes=sum(x!=y for x,y in zip(before,after)),whole_image_inverse=True,reservation=[FIRST,LIMIT],
  actual_native_DMA_cases=cases,source_map_cells_bound=504,source_palette_colors_bound=96,new_tile_extent=[0x06003200,0x06006500],old_tile_extent=[0x06003200,0x06007200],
  original_map_destination=0x0600F800,original_palette_destination=0x05000020,task_flags_timing_and_mode23_untouched=True,
  limitations=['DMA hardware transfer is explicitly modeled while native CPU instructions execute; no emulator result.',
   'Existing frozen title tile payload is reused unchanged; prior full title pixel audit not repeated.',
   'This repairs fixed native20 assets only, not source/native timing differences or missing mode23.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
