"""Korean-spacing headers on the final compact/warm-prompt title r4 base.

Reuse the frozen strict component builder with only explicit artifact pins
changed. Its full reservation exclusion, scanner and inverse are unchanged.
"""
import argparse,json,types
from pathlib import Path
import build_character_select_name_scene as prior
INPUT='280202556B6DC6AD624718A9F693C0466F2C6287F1A7681C46AFDB06D853D58B'
TITLE_OWNER='91618BDC7A28BB36A829AABDD19271CDCB66747B305917E5174968AC38D9F412'
ASSETS='7F844AD8AA1672BE95EBBCD241AEF542DF2E9EA97D99A24D6CC96C2B81343204'
PRIOR_BUILDER='6DA9E5855F9A90A38E15977A0EAF20DE8259AAB9997447221DACF5BE9D7F4177'
def build(before,headers,meta,scene,title):
 assert prior.sha(Path(prior.__file__).read_bytes())==PRIOR_BUILDER
 context=dict(prior.__dict__,INPUT=INPUT,TITLE_OWNER=TITLE_OWNER,ASSETS=ASSETS,__file__=__file__)
 fn=types.FunctionType(prior.build.__code__,context)
 after,report,hits=fn(before,headers,meta,scene,title)
 report.update(prior_builder_sha256=PRIOR_BUILDER,revision='KO two-clear-column syllable spacing; EN/JA/DG preserved r2; title r4 preserved')
 return after,report,hits
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('input','assets','scene-owner','title-owner','output-dir'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists()
 raw=(a.assets/'manifest.json').read_bytes();sr=a.scene_owner.read_bytes();tr=a.title_owner.read_bytes()
 assert tuple(map(prior.sha,(raw,sr,tr)))==(ASSETS,prior.SCENE_OWNER,TITLE_OWNER)
 meta=json.loads(raw);headers=[]
 for row in meta['entries']:
  b=(a.assets/row['file']).read_bytes();assert prior.sha(b)==row['sha256'];headers.append(b)
 after,report,hits=build(a.input.read_bytes(),headers,meta,json.loads(sr),json.loads(tr))
 a.output_dir.mkdir(parents=True);(a.output_dir/'component.gba').write_bytes(after)
 census=(json.dumps(dict(input_sha256=INPUT,range=[0xD90000,0x1000000],hits=hits,new_allocation_hits=0),indent=2)+'\n').encode();(a.output_dir/'allocation-census.json').write_bytes(census);report['allocation_census_sha256']=prior.sha(census)
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS',report['output_sha256'],prior.sha(path.read_bytes()))
if __name__=='__main__':main()
