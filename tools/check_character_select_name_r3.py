"""Affected Korean glyph/clearance proof; r2 other languages remain exact."""
import argparse,hashlib,json
from pathlib import Path
from build_options_korean_poc import FONT_SHA
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def pixels(b):return {(x,y):(b[(y//8*12+x//8)*32+4*(y%8)+x%8//2]>>(4*(x%2)))&15 for y in range(16)for x in range(96)}
def glyph(font,ch):
 for block in font.decode().split('STARTCHAR ')[1:]:
  lines=block.splitlines();f={x.split()[0]:x.split()[1:]for x in lines if x.split()}
  if int(f['ENCODING'][0])!=ord(ch):continue
  w,h,left,bottom=map(int,f['BBX']);rows=lines[lines.index('BITMAP')+1:lines.index('ENDCHAR')]
  ink={(left+x,y-h-bottom)for y,row in enumerate(rows)for x in range(w)if int(row,16)&(1<<((w+7)//8*8-x-1))}
  p={(x+dx,y+dy):2 for x,y in ink for dx in(-1,0,1)for dy in(-1,0,1)};p.update({pt:1 for pt in ink})
  lo=min(x for x,y in p);return {(x-lo,y):v for(x,y),v in p.items()}
 raise ValueError('missing pinned BDF glyph')
def main():
 p=argparse.ArgumentParser()
 for n in('before','after','font','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();font=a.font.read_bytes();assert sha(font)==FONT_SHA
 oldraw=(a.before/'manifest.json').read_bytes();newraw=(a.after/'manifest.json').read_bytes()
 assert sha(oldraw)=='9F479B7C13FA4BCECDBD24E3170628377369C31CC5FD4563D311B9B49A1C3C11'
 old=json.loads(oldraw);new=json.loads(newraw);facts=[];total=0
 for index,(r,s)in enumerate(zip(old['entries'],new['entries'])):
  b=(a.before/r['file']).read_bytes();c=(a.after/s['file']).read_bytes();assert len(b)==len(c)==768 and sha(b)==r['sha256']and sha(c)==s['sha256']
  if not 30<=index<45:assert b==c;continue
  i=r['id'];left,right=(6,89)if i==1 else(12,83);bg,ink,shadow=(r['colors'][k]for k in('background','ink','shadow'));bp,cp=pixels(b),pixels(c)
  guard={(x,y)for x,y in bp if y==0 or x<=left or x>=right};assert all(bp[k]==cp[k]for k in guard)
  assert s['label']==r['label']and s['top']==r['top']and s['height']==r['height']
  expected={};gaps=[];shapes=[]
  allpoints=[glyph(font,ch)for ch in r['label']];ymin=min(y for points in allpoints for x,y in points)
  for part,ch,points in zip(s['syllables'],r['label'],allpoints):
   assert part['character']==ch and part['right']-part['left']==max(x for x,y in points)
   local={(part['left']+x,s['top']+y-ymin):(ink if v==1 else shadow)for(x,y),v in points.items()}
   assert not expected.keys()&local.keys();expected.update(local);shapes.append(len(points));total+=len(points)
  actual={(x,y):v for(x,y),v in cp.items()if(x,y)not in guard and v!=bg}
  assert actual==expected
  for p,q in zip(s['syllables'],s['syllables'][1:]):
   gap=q['left']-p['right']-1;assert gap==2
   assert all(cp[x,y]==bg for x in range(p['right']+1,q['left'])for y in range(1,16));gaps.append(gap)
  assert min(x for x,y in actual)==s['left']and max(x for x,y in actual)-s['left']+1==s['width']<=70
  facts.append(dict(id=i,label=r['label'],width=s['width'],prior_width=r['width'],clear_columns=gaps,exact_syllable_pixels=shapes))
 assert len(facts)==15
 result=dict(status='PASS',before_manifest_sha256=sha(oldraw),after_manifest_sha256=sha(newraw),font_sha256=sha(font),checker_sha256=sha(Path(__file__).read_bytes()),unchanged_EN_JA_DG_headers=45,Korean_headers=facts,complete_outline_pixels=total,clipped_pixels=0,changed_protected_pixels=0,limits=['Affected asset/glyph check only; native helper and r2 other-language pixels unchanged.','New ROM layer and independent review follow separately.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()
