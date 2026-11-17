"""Reconnect the existing mode20 return-to-title consumer to source title art."""
import argparse,hashlib,json,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner
BASE=0x08000000
INPUT='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OWNER='29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900'
FIRST,LIMIT=0xD8B400,0xD8B440
MAP,PAL,TILE1,TILE2=0x6FBDA8,0x6FC198,0x712680,0x717F40

def need(v,s):
 if not v:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def color(v):return sum((2*((v>>s)&15)+(1 if (v>>s)&15 else 0))<<d for s,d in ((8,0),(4,5),(0,10)))
def asm(s,a):return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(s,BASE+a)[0])
def contract(b,s):
 need(sha(b)==INPUT and sha(s)==SOURCE,'fixed current and original source identities')
 for a,hexcode in ((0x7827FC,'B0CAE6C3'),(0x78281C,'33C033C00BC07547'),(0x78282B,'B80C388ED8BE0000'),(0x782848,'BF0072BEF003B98019FCF3A5'),(0x782854,'B800038EC0BF220383C720BEF035B96000FCF3A5')):
  expect=bytes.fromhex(hexcode);need(s[a:a+len(expect)]==expect,'source mode20 graphic producer '+hex(a))
 need(b[0x40668:0x4074C] and sha(b[0x40668:0x4074C])=='708F52F8A2666A862D11825AF8B4930FAE4ABABC7909AFDEB8040688805D1364','retained whole native asset callback')
 need(sha(b[0xB84:0xBA8])=='7F3A5BB5C97441ACE990D2F73353C30FB43540ED3E5528A303FF7CC81A4D64C8','native DMA32 ABI')
 need([u(b,a) for a in (0x40728,0x4072C,0x40730,0x40734,0x40738,0x4073C)]==[0x0600F800,0x0808B768,0x06003200,0x0808BB58,0x05000020,0x0808FB58],'all six typed source/destination literals')
 need(u(b,0x406DC)==0xE59F504C,'only original destination load hook')
 need(u(b,0x90B7C)==BASE+PAL and u(b,0x90B90)==BASE+MAP,'existing ordinary-title same source assets')
 palette=struct.pack('<96H',*(color(h(s,0x4AB6B0+2*i)) for i in range(96)))
 need(b[PAL:PAL+0xC0]==palette and b[PAL+0xC0:PAL+0x100]==b[0x8FC18:0x8FC58],'six source rows and unchanged native padding rows')
 tiles=b[TILE1:TILE1+0x2000]+b[TILE2:TILE2+0x1300]
 for t in range(408):
  for y in range(8):
   for x in range(8):
    expected=sum(((s[0x4A84B0+t*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
    need((tiles[t*32+y*4+x//2]>>(4*(x%2)))&15==expected,'all26112 source tile pixels')
 for i in range(504):
  v=h(s,0x4A80C0+i*2);native=(v&511)|((v&8192)>>4)|((v&0xC000)>>4)|((v&0x1E00)<<3)
  need(h(b,MAP+2*i)==native and 0x190<=native&1023<0x328 and 1<=native>>12<=6,'all504 source cells bounded to loaded titles')
 return dict(source_palette=0x4AB6B0,source_tiles=0x4A84B0,source_map=0x4A80C0,source_colors=96,loaded_tiles=408,source_pixels=26112,map_cells=504,tile_destination=[0x06003200,0x06006500],old_tile_extent=[0x06003200,0x06007200],map_destination=0x0600F800,palette_destination=[0x05000020,0x05000120])
def helper():
 result=asm('''ldr r5,destination
 ldr r4,first
 mov r2,#0x800
 bl 0x08000B84
 ldr r4,second
 mov r2,#0x4c0
 ldr lr,continuation
 b 0x08000B84
destination:.word 0x06003200
first:.word 0x08712680
second:.word 0x08717F40
continuation:.word 0x080406EC
''',FIRST)
 need(len(result)==48,'eight instructions four literals')
 cs=Cs(CS_ARCH_ARM,CS_MODE_ARM);cs.detail=True
 ins=list(cs.disasm(result[:32],BASE+FIRST))
 need(len(ins)==8 and all(not x.update_flags for x in ins),'complete flag-preserving helper')
 return result

def validate(b,after):
 def dma(m):
  source,dest,count=m.r[4],m.r[5],m.r[2]
  need(count in (0x800,0x4C0,0x1000,0x40),'bounded native DMA count')
  for i in range(count):m.put(dest+4*i,m.get(source+4*i),4)
  m.r[4]+=count*4;m.r[5]+=count*4;m.r[8]=0x04000000;m.r[12]=0x8400
 for flags in range(16):
  m=Machine(after,seed=4,flags=(flags<<28)|0x1F);m.services[0x08000B84]=dma
  saved=list(m.r);cpsr=m.cpsr
  m.run(0x080406DC,{0x08000B84})
  dma(m)  # Explicit tail-entered DMA service; the bounded walker summarizes BL only.
  need(m.r[2]==0x4C0 and m.r[4]==BASE+TILE2+0x1300 and m.r[5]==0x06006500 and m.r[14]==0x080406EC,'two-piece DMA cursor and native continuation')
  need(all(m.r[i]==saved[i] for i in (0,1,3,6,7,9,10,11,13)) and m.cpsr==cpsr,'preserved non-DMA registers flags and stack')
  expected=after[TILE1:TILE1+0x2000]+after[TILE2:TILE2+0x1300]
  need(bytes(m.get(0x06003200+i,1) for i in range(0x3300))==expected,'complete destination tile image')
  m.run(0x080406EC,{0x080406FC})
  need(bytes(m.get(0x05000020+i,1) for i in range(0x100))==after[PAL:PAL+0x100],'retained following palette copy')
  need(m.r[2]==0x40 and m.r[4]==BASE+PAL+0x100 and m.r[5]==0x05000120 and m.r[14]==0x080406FC and m.cpsr==cpsr,'native palette continuation ABI')
 return dict(actual_ARM_helper_cases=16,palette_continuation_cases=16,dma_service='Explicit existing DMA32 transfer summary; no emulator execution.',no_new_RAM=True)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('before','source','owner','output','manifest'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();need(not a.output.exists() and not a.manifest.exists(),'fresh isolated outputs')
 b,s=a.before.read_bytes(),a.source.read_bytes();proof=contract(b,s)
 ownerbytes=a.owner.read_bytes();need(sha(ownerbytes)==OWNER,'frozen preceding owner');owner=json.loads(ownerbytes)
 need(b[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'whole64-byte reservation blank')
 scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
 hits=scan(b);need(not hits,'zero conservative inbound references')
 writes=[];out=bytearray(b)
 for at,data,label in ((FIRST,helper(),'source title split DMA with mode20 continuation'),(0x406DC,asm(f'b 0x{BASE+FIRST:X}',0x406DC),'mode20-only tile transfer'),(0x4072C,struct.pack('<I',BASE+MAP),'mode20 source map alias'),(0x4073C,struct.pack('<I',BASE+PAL),'mode20 source palette alias')):
  writes.append(dict(offset=at,size=len(data),before_hex=b[at:at+len(data)].hex(),after_hex=data.hex(),label=label));out[at:at+len(data)]=data
 for w in owner['writes']:
  lo,hi=w['offset'],w['offset']+w['size']
  need(sha(b[lo:hi])==w['after_sha256'] and out[lo:hi]==b[lo:hi],'all22 preceding Iraira writes preserved')
 need(all(not max(lo,FIRST)<min(hi,LIMIT) for lo,hi in owner['reservations']),'new code disjoint from prior reservation')
 inverse=bytearray(out)
 for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
 need(bytes(inverse)==b and sum(w['size'] for w in writes)==60,'whole3FE5 inverse and60declaredbytes')
 checks=validate(b,bytes(out))
 report=dict(status='PASS',input_sha256=INPUT,output_sha256=sha(out),source_sha256=SOURCE,owner_sha256=OWNER,reservations=[[FIRST,LIMIT]],writes=writes,declared_bytes=60,changed_bytes=sum(x!=y for x,y in zip(b,out)),new_RAM_bytes=0,inbound_hits=hits,source_contract=proof,validation=checks,preceding_iraira_writes_preserved=22,whole_image_inverse=True,actual_runtime_verified=False,limits=['No mode23 implementation or new entry is exposed.','Existing native fade timing, task handshake, IRQ and localized labels unchanged.','Static source asset reconnection, not a captured visual proof.'])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.manifest.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_bytes(out);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps(dict(status='PASS',output_sha256=sha(out),manifest_sha256=sha(a.manifest.read_bytes()),declared_bytes=60,changed_bytes=report['changed_bytes'],validation=checks)))
if __name__=='__main__':main()
