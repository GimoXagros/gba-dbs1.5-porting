"""Author check: header pixels and actual ARM loader/getter/DMA/tail composition."""
import argparse,hashlib,json,struct
from pathlib import Path
from verify_shoot_static_companion_clear import Machine as Parent
import character_select_name_overlay as overlay
import build_character_select_name_assets as assets

BASE=0x08000000
CODE=0x08F00000
TABLE=0x08F00200
DATA=0x08F01000
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,why):
 if not ok:raise ValueError(why)
class Machine(Parent):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.dma=[]
 def put(self,address,value,size=4,log=False):
  super().put(address,value,size,log)
  if log and address==0x040000DE:
   need(size==2 and value==0x8400,'actual native DMA3 control')
   source=self.get(0x040000D4);dest=self.get(0x040000D8);words=self.get(0x040000DC,2)
   need((dest,words)in((0x05000020,8),(0x06005780,0x600),(0x06005780,0xC0)),'only owned palette/full atlas/header DMA')
   need(BASE<=source<BASE+len(self.rom) and source+words*4<=BASE+len(self.rom),'bounded ROM DMA source')
   payload=self.rom[source-BASE:source-BASE+words*4]
   self.mem.update(zip(range(dest,dest+len(payload)),payload));self.dma.append((source,dest,words))
def memory(m,start,size):return bytes(m.mem[start+i]for i in range(size))
def composed(native,headers,code=CODE,table=TABLE,data=DATA):
 rom=bytearray(native);blob=overlay.assemble(code,table)
 rom[code-BASE:code-BASE+len(blob)]=blob
 for i,b in enumerate(headers):struct.pack_into('<I',rom,table-BASE+4*i,data+i*768)
 rom[data-BASE:data-BASE+60*768]=b''.join(headers)
 rom[overlay.HOOK-BASE:overlay.HOOK-BASE+4]=overlay.hook(code)
 return bytes(rom),blob
def fixture(rom,i,tag,flags):
 m=Machine(rom,seed=i,flags=(flags<<28)|0x1F);m.r[1]=i;m.put(0x0300112F,tag,1)
 return m
def run(native,headers):
 need(sha(native)==assets.NATIVE,'exact baseline native input')
 need(sha(native[0x633400:0x63341C])==overlay.GETTER_SHA,'actual existing 256-tag getter')
 need(struct.unpack_from('<I',native,overlay.HOOK-BASE)[0]==overlay.OLD_WORD,'unique displaced native word')
 rom,blob=composed(native,headers);count=0
 for i in range(15):
  pal,tiles=struct.unpack_from('<II',native,0x4A5BC0+i*8);body=native[tiles-BASE+768:tiles-BASE+6144]
  for flags in range(16):
   old=fixture(native,i,0xA0,flags);ret=old.r[14];sp=old.r[13];old.run(0x084A5C40,{ret})
   for language in range(4):
    m=fixture(rom,i,0xA0+language,flags);m.run(0x084A5C40,{ret})
    need(m.r[:15]==old.r[:15] and m.cpsr==old.cpsr,'entire returned register/NZCV/SP/LR parity')
    need(m.get(0x0300472E,2)==i+1,'native cached identity tail retained')
    need(memory(m,0x06005780,768)==headers[15*language+i],'selected localized header')
    need(memory(m,0x06005A80,5376)==body,'all native portrait bytes below header retained')
    need(memory(m,0x05000020,32)==memory(old,0x05000020,32),'native palette retained')
    need(m.dma==old.dma+[(DATA+(15*language+i)*768,0x06005780,192)],'only extra header DMA')
    for at,v,size in m.writes:
     need(sp-64<=at<sp or at==0x0300472E or 0x040000D4<=at<0x040000E0,'no OAM, input, language, save or persistent state writes')
    count+=1
 alltags=0
 for i in range(15):
  for tag in range(256):
   m=fixture(rom,i,tag,tag%16);before=m.r[:];flags=m.cpsr;m.run(CODE,{0x084A5C70})
   language=tag-0xA0 if 0xA0<=tag<=0xA3 else 0
   need(memory(m,0x06005780,768)==headers[language*15+i],'all tags select normalized language')
   before[4]=0x03004710
   need(m.r[:15]==before[:15] and m.cpsr==flags,'displaced-load-only state change')
   alltags+=1
 # Relocated code and scatter pointers are actual code inputs, not fixed-PC fixtures.
 scatter,other=composed(native,headers,0x08EF9000,0x08EF9800,0x08F10000)
 m=fixture(scatter,14,0xA3,15);m.run(0x084A5C40,{m.r[14]});need(memory(m,0x06005780,768)==headers[59],'relocation actual execution')
 return dict(full_native_loader_cases=count,all_tag_overlay_cases=alltags,relocated_case=1,code_bytes=len(blob),code_sha256=sha(blob),displaced_instruction='LDR R4,[PC,#1C] -> 03004710',extra_DMA_bytes=768,new_OAM=0,new_persistent_RAM=0,maximum_extra_stack_bytes=60,actual_DMA_function='08000B84..08000BA4',getter='08633400..08633418',limits=['This is an author fixture, not independent QA or an installed ROM allocation proof.','DMA3 MMIO transfers are modeled; actual loader/getter/DMA setup/tail ARM executes.','Stack scratch is owned below live SP; freed stack bytes and final DMA3 source/count differ intentionally.'])
def pixels(native,source,headers):
 cases=0;glyphs=0
 for lang in range(4):
  for i in range(15):
   t=struct.unpack_from('<I',native,0x4A5BC4+8*i)[0]-BASE;old=assets.unpack(native[t:t+768]);new=assets.unpack(headers[lang*15+i])
   need(all(old[y][x]==new[y][x]for y in range(16)for x in range(96)if assets.protected(i,x,y)),'all exact native protected border pixels')
   if lang<2:
    at=assets.SOURCE_TILES[i]+(0x1800 if lang==0 else 0)
    src=[[sum(((source[at+(y//8*12+x//8)*32+y%8*4+plane]>>(7-x%8))&1)<<plane for plane in range(4))for x in range(96)]for y in range(16)]
    bg=src[1][48];edge=6 if src[1][10]==bg else 12
    for y in range(1,16):
     for x in range(edge+1,95-edge):
      if src[y][x]!=bg:
       value={2:14,3:2}[src[y][x]]if i==11 else src[y][x]
       need(new[y][x]==value,'every original EN/JA letter pixel at exact coordinate');glyphs+=1
   cases+=1
 # Reject a changed frame pixel with the same unchanged name interior.
 bad=assets.unpack(headers[0]);bad[0][0]^=1
 need(bad[0][0]!=assets.unpack(native[struct.unpack_from('<I',native,0x4A5BC4)[0]-BASE:struct.unpack_from('<I',native,0x4A5BC4)[0]-BASE+768])[0][0],'protected frame mutation is distinguishable')
 return dict(header_cases=cases,source_EN_JA_glyph_pixels=glyphs,protected_border_pixels_per_header=[sum(assets.protected(i,x,y)for y in range(16)for x in range(96))for i in range(15)])
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('native','source','assets','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 native=a.native.read_bytes();source=a.source.read_bytes();manifest=json.loads((a.assets/'manifest.json').read_text(encoding='utf-8'));headers=[]
 need(sha(source)==assets.SOURCE,'source pin')
 for row in manifest['entries']:
  b=(a.assets/row['file']).read_bytes();need(len(b)==768 and sha(b)==row['sha256'],'asset bytes pinned');headers.append(b)
 result=dict(status='PASS',native_sha256=sha(native),source_sha256=sha(source),assets_manifest_sha256=sha((a.assets/'manifest.json').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),overlay_sha256=sha(Path(overlay.__file__).read_bytes()),pixel_checks=pixels(native,source,headers),ARM_checks=run(native,headers))
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()
