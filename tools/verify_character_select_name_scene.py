"""Independent source pixels, font geometry, whole-image and actual ARM header QA.

No asset builder, overlay generator or author checker imports. The shared strict
ARM interpreter is used with an explicit DMA3 MMIO model; no game is launched.
"""
import argparse,hashlib,json,re,struct,types
from pathlib import Path
from verify_shoot_static_companion_clear import Machine as CPU
import verify_shoot_caller_resident as scanner
from digicode_glyphs import BODIES,VOICED,SEMIVOICED

BASE=0x08000000
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE='280202556B6DC6AD624718A9F693C0466F2C6287F1A7681C46AFDB06D853D58B'
AFTER='9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5'
MANIFEST='8D4FC0A9973981D40FCA86CC639CF35D49AF580C13CC10B9810CAAB4D7636B43'
ASSETS='7F844AD8AA1672BE95EBBCD241AEF542DF2E9EA97D99A24D6CC96C2B81343204'
JA=('ギルモン','テリアモン','レナモン','ブイモン','ワームモン','アグモン','スカモン','アグモン','ロップモン','ガブモン','アグモン','インプモン','ギルモン','パタモン','テイルモン')
EN=('GUILMON','TERRIERMON','RENAMON','VEEMON','WORMMON','AGUMON','SUKAMON','AGUMON','LOPMON','GABUMON','AGUMON','IMPMON','GUILMON','PATAMON','GATOMON')
KO=('길몬','테리어몬','레나몬','브이몬','추추몬','아구몬','스카몬','아구몬','로프몬','파피몬','아구몬','임프몬','길몬','파닥몬','가트몬')
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(x,label):
 if not x:raise ValueError(label)
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def pixel(b,x,y,planar=False):
 at=((y//8)*12+x//8)*32+(y%8)*4
 return sum(((b[at+k]>>(7-x%8))&1)<<k for k in range(4))if planar else(b[at+(x%8)//2]>>(4*(x%2)))&15
def grid(b,planar=False):return {(x,y):pixel(b,x,y,planar)for y in range(16)for x in range(96)}
def protected(i,x,y):return y==0 or x<(7 if i==1 else 13)or x>=(89 if i==1 else 83)

def font(data):
 result={}
 for section in data.decode('utf-8').split('STARTCHAR ')[1:]:
  lines=section.splitlines();code=int(next(x.split()[1]for x in lines if x.startswith('ENCODING ')))
  if code<0 or chr(code)not in ''.join(KO):continue
  advance=int(next(x.split()[1]for x in lines if x.startswith('DWIDTH ')))
  w,height,left,bottom=map(int,next(x.split()[1:]for x in lines if x.startswith('BBX ')))
  rows=lines[lines.index('BITMAP')+1:lines.index('ENDCHAR')]
  points={(x+left,y-height-bottom)for y,line in enumerate(rows)for x in range(w)if int(line,16)&(1<<(((w+7)//8)*8-1-x))}
  need(len(rows)==height and points,'complete BDF glyph')
  result[chr(code)]=(advance,points)
 need(set(result)==set(''.join(KO)),'complete canonical Korean alphabet')
 return result

def korean_text(label,glyphs):
 result={};cursor=0
 for ch in label:
  _,points=glyphs[ch]
  outline={(x+dx,y+dy):2 for x,y in points for dx in(-1,0,1)for dy in(-1,0,1)}
  outline.update({p:1 for p in points});left=min(x for x,y in outline);right=max(x for x,y in outline)
  result.update({(x-left+cursor,y):v for(x,y),v in outline.items()});cursor+=right-left+3
 return result,cursor-2

def dg_character(ch):
 ch=chr(ord(ch)-0x60)if 0x30A1<=ord(ch)<=0x30F6 else ch
 base=VOICED.get(ch,SEMIVOICED.get(ch,ch));points=set()
 for stroke in BODIES[base].split(';'):
  vertices=[tuple(map(int,p.split(',')))for p in stroke.split()]
  points.update(vertices)
  for (x,y),(endx,endy)in zip(vertices,vertices[1:]):
   dx=abs(endx-x);dy=-abs(endy-y);sx=1 if x<endx else-1;sy=1 if y<endy else-1;error=dx+dy
   while(x,y)!=(endx,endy):
    twice=error*2
    if twice>=dy:error+=dy;x+=sx
    if twice<=dx:error+=dx;y+=sy
    points.add((x,y))
 points={(x,y+5)for x,y in points}
 if ch in VOICED:points|={(1,1),(2,2),(5,1),(4,2)}
 if ch in SEMIVOICED:points|={(3,1),(2,2),(4,2),(3,3)}
 return points

def dg_text(label):
 points={};cursor=0
 for ch in label:
  glyph=dg_character(ch);left=min(x for x,y in glyph);right=max(x for x,y in glyph)
  points.update({(cursor+x-left,y-15):1 for x,y in glyph});cursor+=right-left+2
 return points,max(x for x,y in points)+1

def pixel_check(source,before,headers,meta,bdf):
 need(sha(source[0x779EEF:0x779F48])=='021784FBE892E4F962762D13AFE5BADC2E3CA50EAA03ACA47DB4106BF651FD06','source typed portrait loader')
 glyphs=font(bdf);result=[];expected=[];source_offsets=[]
 for ident in range(15):
  selector=h(source,0x779DA4+ident*2);segment=h(source,0x779DC2+(selector>>8)*2)
  base=(selector&0x7F)*0x10000+(segment-0x3000)*16
  source_offsets.append(base+h(source,0x779D68+ident*4+2))
 for language in range(4):
  for ident in range(15):
   n=language*15+ident;row=meta['entries'][n];actual=grid(headers[n])
   palette,tiles=struct.unpack_from('<II',before,0x4A5BC0+8*ident);palette-=BASE;tiles-=BASE
   old=grid(before[tiles:tiles+768]);bg=old[48,1]
   want={p:(v if protected(ident,*p)else bg)for p,v in old.items()}
   label=(EN,JA,KO,tuple(x.replace('ッ','ツ')for x in JA))[language][ident]
   need(row['id']==ident and row['language']==('en','ja','ko','dg')[language]and row['label']==label,'canonical label and row identity')
   if language<2:
    raw=source_offsets[ident]+(0x1800 if language==0 else 0);view=grid(source[raw:raw+768],True)
    source_bg=view[48,1];edge=6 if view[10,1]==source_bg else 12
    ink={p:v for p,v in view.items()if 1<=p[1]<16 and edge<p[0]<95-edge and v!=source_bg}
    if ident==11:
     need(set(ink.values())=={2,3},'ID11 source name uses only its two typed colors')
     ink={p:{2:14,3:2}[v]for p,v in ink.items()}
     need(h(before,palette+28)==0x7FFF,'ID11 native white ink retained')
    need(row['source_header_raw']==raw,'metadata source address matches real table decode')
   else:
    points,width=korean_text(label,glyphs)if language==2 else dg_text(label)
    # Text palette comes from the real native header, with the separately
    # documented ID11 white/shadow remapping. Values are not inferred by color count.
    colors=((15,8,7),(15,11,8),(14,15,5),(15,4,6),(15,10,9),(15,2,5),(13,11,12),(14,15,4),(15,14,2),(1,2,11),(3,15,6),(6,14,2),(4,1,2),(1,15,12),(3,1,2))[ident]
    need(bg==colors[0],'native background palette index')
    y0=min(y for x,y in points);height=max(y for x,y in points)-y0+1
    x0=(96-width)//2;top=1+(15-height)//2+(language==3)
    ink={(x+x0,y-y0+top):(colors[1]if v==1 else colors[2])for(x,y),v in points.items()}
    need(row['width']==width and row['height']==height and row['top']==top,'independently decoded complete glyph bounds')
   need(ink and all(0<=x<96 and 0<=y<16 and not protected(ident,x,y)for x,y in ink),'complete ink without frame collision')
   want.update(ink);need(actual==want,'all1536 expected pixels, no residual old lettering')
   need(all(actual[p]==v for p,v in old.items()if protected(ident,*p)),'native checker and frame exact')
   if language==3:need(all(actual[x,1]==bg for x in range(96)if not protected(ident,x,1)),'one clear row below top frame')
   need(row['native_body_sha256']==sha(before[tiles+768:tiles+6144]),'body byte identity metadata')
   expected.append(want);result.append(dict(language=language,id=ident,glyph_pixels=len(ink),ink_bounds=[min(x for x,y in ink),min(y for x,y in ink),max(x for x,y in ink),max(y for x,y in ink)],protected_pixels=sum(protected(ident,x,y)for x,y in old)))
 return result,expected,source_offsets

class DMA(CPU):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.transfers=[]
 def put(self,address,value,size=4,log=False):
  super().put(address,value,size,log)
  if log and address==0x040000DE:
   need((size,value)==(2,0x8400),'actual DMA3 immediate32-bit request')
   src=self.get(0x040000D4);dst=self.get(0x040000D8);count=self.get(0x040000DC,2)
   need((dst,count)in((0x05000020,8),(0x06005780,1536),(0x06005780,192)),'only native palette, portrait or owned header DMA')
   need(BASE<=src<src+4*count<=BASE+len(self.rom),'complete ROM DMA source')
   payload=self.rom[src-BASE:src-BASE+4*count]
   self.mem.update(zip(range(dst,dst+len(payload)),payload));self.transfers.append((src,dst,count))
def mem(m,at,n):return bytes(m.get(at+i,1)for i in range(n))

def arm_case(before,after,pointers,headers,ident,lang,flags):
 old=DMA(before,seed=ident+lang*17,flags=flags<<28|0x1F);new=DMA(after,seed=ident+lang*17,flags=flags<<28|0x1F)
 for m in(old,new):m.r[1]=ident;m.put(0x0300112F,0xA0+lang,1)
 ret=old.r[14];sp=old.r[13]
 old.run(0x084A5C40,{ret});new.run(0x084A5C40,{ret})
 need(old.r[:15]==new.r[:15]and old.cpsr==new.cpsr,'entire native returned register/NZCV parity')
 need(new.transfers==old.transfers+[(pointers[15*lang+ident],0x06005780,192)],'one bounded extra header copy')
 need(mem(new,0x06005780,768)==headers[15*lang+ident],'actual correct language and ID header')
 # Compare every observed RAM/VRAM byte except the exact new header, DMA state
 # and dead helper stack. This includes all5376 portrait-body bytes and palette.
 for at in set(old.mem)|set(new.mem):
  if 0x06005780<=at<0x06005A80 or 0x040000D4<=at<0x040000E0 or sp-64<=at<sp:continue
  need(old.mem.get(at)==new.mem.get(at),'all other live memory and portrait bytes retained')
 for at,v,n in new.writes:
  need(sp-64<=at and at+n<=sp or at==0x0300472E and n==2 or 0x040000D4<=at and at+n<=0x040000E0,'no OAM, input or other persistent memory writes')
 return new

def inverse_check(before,after,meta):
 inverse=bytearray(after);spans=[]
 for r in meta['writes']:
  at,n=r['offset'],r['size'];spans.append((at,at+n))
  need(sha(before[at:at+n])==r['before_sha256']and sha(after[at:at+n])==r['after_sha256'],'actual declared bytes')
  inverse[at:at+n]=before[at:at+n]
 spans.sort();need(len(spans)==63 and all(a[1]<=b[0]for a,b in zip(spans,spans[1:])),'63 disjoint exact writes')
 need(bytes(inverse)==before,'complete whole-image inverse')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('source','before','after','manifest','assets','font','scene_owner','title_owner','report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh output')
 source,before,after,raw,assetraw=(x.read_bytes()for x in(a.source,a.before,a.after,a.manifest,a.assets/'manifest.json'))
 need(tuple(map(sha,(source,before,after,raw,assetraw)))==(SOURCE,BEFORE,AFTER,MANIFEST,ASSETS),'all independent fixed input pins')
 meta=json.loads(raw);assets=json.loads(assetraw);headers=[(a.assets/r['file']).read_bytes()for r in assets['entries']]
 need(len(headers)==60 and all(len(b)==768 and sha(b)==r['sha256']for b,r in zip(headers,assets['entries'])),'complete frozen60 headers')
 need(sha(a.font.read_bytes())=='4CA44E617B1A51D420B32AE1AC4663A6DAD0D5F7036E62F78F52B0086779DFED','pinned BDF')
 pixels,expected,offsets=pixel_check(source,before,headers,assets,a.font.read_bytes())
 inverse_check(before,after,meta)
 need(sha(a.scene_owner.read_bytes())==meta['scene_owner_sha256'] and sha(a.title_owner.read_bytes())==meta['title_owner_sha256'],'exact prior ownership manifests')
 owners=[json.loads(x.read_text(encoding='utf-8'))for x in(a.scene_owner,a.title_owner)]
 prior=[(0xDB0404,0xDB5C04)]+[(r['start'],r['end'])for owner in owners for r in owner['allocations']]
 allocations=meta['allocations'];need(len(allocations)==62,'62 fresh complete allocations')
 census=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((0xD90000,0x1000000),)),argdefs=scanner.inbound.__defaults__)(before)
 for r in allocations:
  lo,hi=r['start'],r['end'];need(before[lo:hi]==b'\xff'*(hi-lo),'complete erased allocation')
  need(all(hi<=a or lo>=b for a,b in prior),'full prior typed ownership and slack retained')
  need(not any(lo<=(target&0x1FFFFFF)<hi for _,_,target in census),'independent full-image strict-zero inbound')
 pointers=struct.unpack_from('<60I',after,meta['table_span'][0]);need(list(pointers)==meta['header_pointers'],'all table entries')
 for i,ptr in enumerate(pointers):need(after[ptr-BASE:ptr-BASE+768]==headers[i],'all installed header bytes')
 code=BASE+meta['code_span'][0];word=u(after,0x4A5C6C);delta=word&0xFFFFFF;delta=delta-(1<<24)if delta&(1<<23)else delta
 need(word>>24==0xEA and 0x084A5C74+delta*4==code and u(before,0x4A5C6C)==0xE59F401C,'actual displaced-load hook')
 cases=0
 for ident in range(15):
  for lang in range(4):
   for flags in range(16):arm_case(before,after,pointers,headers,ident,lang,flags);cases+=1
 tags=0
 for ident in range(15):
  for tag in range(256):
   m=DMA(after,seed=ident,flags=(tag%16)<<28|0x1F);m.r[1]=ident;m.put(0x0300112F,tag,1);old=m.r[:15].copy();flags=m.cpsr
   m.run(code,{0x084A5C70});lang=tag-0xA0 if 0xA0<=tag<=0xA3 else 0;old[4]=0x03004710
   need(m.r[:15]==old and m.cpsr==flags and mem(m,0x06005780,768)==headers[15*lang+ident],'all256 tag normalization and exact ABI');tags+=1
 mutations=[]
 for label,index,pos in(('protected border',0,(0,0)),('original English ink',0,pixels[0]['ink_bounds'][:2]),('Korean glyph',30,pixels[30]['ink_bounds'][:2]),('Digicode voiced mark',45,pixels[45]['ink_bounds'][:2])):
  bad=dict(expected[index]);point=tuple(pos);bad[point]^=1
  need(bad!=expected[index],'pixel mutation rejected');mutations.append(label)
 bad=bytearray(after);struct.pack_into('<I',bad,meta['table_span'][0],pointers[1])
 try:arm_case(before,bytes(bad),pointers,headers,0,0,0)
 except ValueError:mutations.append('wrong header pointer')
 else:raise ValueError('wrong pointer escaped actual consumer check')
 bad=bytearray(after);bad[0x500]^=1
 try:inverse_check(before,bytes(bad),meta)
 except ValueError:mutations.append('undeclared ROM change')
 else:raise ValueError('inverse mutation escaped')
 result=dict(status='PASS',source_sha256=SOURCE,before_sha256=BEFORE,after_sha256=AFTER,manifest_sha256=MANIFEST,assets_manifest_sha256=ASSETS,checker_sha256=sha(Path(__file__).read_bytes()),source_offsets_decoded_from_real_tables=offsets,header_cases=pixels,exact_expected_pixels=60*1536,full_native_ARM_cases=cases,all_tag_ARM_cases=tags,strict_zero_allocations=62,prior_excluded_extents=len(prior),whole_image_inverse=True,mutation_rejections=mutations,new_OAM=0,new_persistent_RAM=0,header_destination=[0x06005780,0x06005A80],body_preserved_bytes=5376,limits=['DMA3 MMIO transfer is modeled; actual loader, language getter, overlay, DMA setup and native return instructions execute','No emulator or live four-language screen claim','ID11 retains commercial portrait/palette: source white matches, shadow is an explicitly retained native palette adaptation','Korean canonical names are the approved project wording; glyph pixels independently decoded from pinned BDF','Digicode topology comes from the existing reviewed chart transcription; this verifier independently rasterizes its strokes and voice marks'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()
