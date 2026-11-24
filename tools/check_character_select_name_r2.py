"""Affected-pixel-only r1 to r2 header proof; frozen ARM/helper unchanged."""
import argparse,hashlib,json
from pathlib import Path
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def pixels(b):return {(x,y):(b[(y//8*12+x//8)*32+4*(y%8)+x%8//2]>>(4*(x%2)))&15 for y in range(16)for x in range(96)}
def main():
 p=argparse.ArgumentParser()
 for name in('before','after','prior-report','report'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists()
 oldraw=(a.before/'manifest.json').read_bytes();newraw=(a.after/'manifest.json').read_bytes()
 assert sha(oldraw)=='E97C5354601F0A3826C6A111AC83D95F0A5FEA65D7C1CA2EA1542E8C1C6B5F7E'
 assert sha(a.prior_report.read_bytes())=='E9FF408C2FD40E87B4760226929D07ABB1C94AA80E27FC4D35C9A6594DEAAF9E'
 assert sha(Path(__file__).with_name('character_select_name_overlay.py').read_bytes())=='4156DDC0A8AD9FD2B9D3C5E2B2745DEEF5E17034D98BCC32B9D83B3F94B76824'
 old=json.loads(oldraw);new=json.loads(newraw);facts=[]
 for index,(r,s)in enumerate(zip(old['entries'],new['entries'])):
  b=(a.before/r['file']).read_bytes();c=(a.after/s['file']).read_bytes();assert len(b)==len(c)==768 and sha(b)==r['sha256']and sha(c)==s['sha256']
  if index<45:assert b==c;continue
  i=r['id'];left,right=(6,89)if i==1 else(12,83);bg=r['colors']['background'];bp,cp=pixels(b),pixels(c)
  guard={(x,y)for x,y in bp if y==0 or x<=left or x>=right}
  assert all(bp[k]==cp[k]for k in guard)
  before={(x,y):v for(x,y),v in bp.items()if(x,y)not in guard and v!=bg}
  after={(x,y):v for(x,y),v in cp.items()if(x,y)not in guard and v!=bg}
  assert after=={(x,y+1):v for(x,y),v in before.items()}
  assert all(cp[x,1]==bg for x in range(left+1,right))
  assert min(y for x,y in after)>=2 and max(y for x,y in after)<=15
  facts.append(dict(id=i,pixels=len(after),top_clear=min(y for x,y in after)-1,bottom_clear=15-max(y for x,y in after)))
 assert len(facts)==15
 result=dict(status='PASS',before_manifest_sha256=sha(oldraw),after_manifest_sha256=sha(newraw),prior_ARM_report_sha256=sha(a.prior_report.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),unchanged_EN_JA_KO_headers=45,DG_headers=facts,full_glyph_translation=[0,1],clipped_pixels=0,changed_protected_pixels=0,unchanged_helper=True,limits=['Affected byte proof only: frozen E9FF actual ARM tests retained without rerunning.','ROM allocation and independent pixel review remain separate.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()
