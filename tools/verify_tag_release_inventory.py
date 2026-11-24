"""Independently extend two authenticated original-backed builds and compare every output."""
import argparse
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import build_current_candidate as production
import build_tag_release_tail as tail
from build_ending_awards_main_tail import sha
from verify_id13_main_inventory import inventory

PARENT_AUDIT='772EF5207CC97F1678AB3F31A7008E9DF74CD1108A28570CEE9A9D713D5D334B'

def build(parent,output,previous,source,font,credit):
    assert inventory(parent)==previous
    shutil.copytree(parent,output)
    rows=tail.install(output,source,font,credit,production.run)
    path=output/'build-manifest.json'
    meta=json.loads(path.read_bytes())
    meta['layers']=production.EXPECTED_LAYERS
    meta['collection_and_language']['ending_and_title_build']=rows
    path.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    return inventory(output)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('first-parent','second-parent','first','second','parent-audit','source','font','credit-font','report'):
        parser.add_argument('--'+arg,type=Path,required=True)
    a=parser.parse_args()
    assert len({p.resolve() for p in (a.first_parent,a.second_parent,a.first,a.second)})==4
    assert all(not p.exists() for p in (a.first,a.second,a.report))
    raw=a.parent_audit.read_bytes()
    assert sha(raw)==PARENT_AUDIT
    previous=json.loads(raw)['sha256_by_relative_path']
    with ThreadPoolExecutor(2) as workers:
        results=[workers.submit(build,old,new,previous,a.source,a.font,a.credit_font) for old,new in
                 ((a.first_parent,a.first),(a.second_parent,a.second))]
        first,second=[job.result() for job in results]
    assert first==second and len(previous)==540
    assert {k for k,v in previous.items() if first.get(k)!=v}=={'current-candidate.gba','current-candidate.json','build-manifest.json'}
    assert first['ending-awards.gba']==previous['current-candidate.gba']
    assert first['ending-awards.json']==previous['current-candidate.json']
    assert all(first[key]==value for key,value in production.EXPECTED_LAYERS.items())
    result=dict(status='PASS',parent_audit=PARENT_AUDIT,previous_files=len(previous),
                files_each=len(first),final_sha256=first['current-candidate.gba'],
                pipeline_sha256=sha(Path(production.__file__).read_bytes()),
                stages_sha256=sha(tail.PINS.read_bytes()),sha256_by_relative_path=first)
    a.report.parent.mkdir(exist_ok=True,parents=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS',len(first),'files per build',result['final_sha256'],sha(a.report.read_bytes()))

if __name__=='__main__': main()
