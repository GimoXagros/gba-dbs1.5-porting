"""Reapply the normal source English suffix over two independently audited parents."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import build_current_candidate as main
from verify_id13_main_inventory import inventory
from verify_v89_main_inventory import PINS as PREVIOUS
PRIMARY='CE0B212E544E8A3576D7312E36CA6B7869A27E6606FB4FB0927B13F756F0394D'
FINAL='8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
OWNER='183A4C195AF6AC917D9AF5E58FBF0957B5F433423E3282848AD620E306EF6065'
REVIEW='A11A01E8C45A942167B35494354A83663420D30F7EF7237227E17F08A9D7DC42'

def sha(data):
    return hashlib.sha256(data).hexdigest().upper()

def build(parent, output, usa, source):
    shutil.copytree(parent,output)
    (output/'current-candidate.gba').rename(output/'initial-portrait.gba')
    (output/'current-candidate.json').rename(output/'initial-portrait.json')
    main.source_english_tail(usa,source, output/'intermediate/mode23-title/manifest.json', output)
    path=output/'build-manifest.json'
    manifest=json.loads(path.read_bytes())
    manifest['layers']=main.EXPECTED_LAYERS
    manifest['collection_and_language']['english_title_graphics']={'usa':list(range(5)),'wsc15_english':list(range(5,11))}
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

def run():
    parser=argparse.ArgumentParser()
    for name in ('first-parent','second-parent','first','second','usa','source','v89-audit','report'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    assert sha(Path(main.__file__).read_bytes())==PRIMARY
    original=json.loads(args.v89_audit.read_bytes())
    assert original['status']=='TITLE_AND_PORTRAITS_TWO_FRESH_BUILDS_PASS'
    assert original['final_sha256']==PREVIOUS['current-candidate.gba']
    assert len({p.resolve() for p in (args.first_parent,args.second_parent,args.first,args.second)})==4
    assert not any(p.exists() for p in (args.first,args.second,args.report))
    with ThreadPoolExecutor(2) as pool:
        jobs=[pool.submit(build,parent,out,args.usa,args.source) for parent,out in
              [(args.first_parent,args.first),(args.second_parent,args.second)]]
        for job in jobs:
            job.result()
        inventories=list(pool.map(inventory,(args.first,args.second)))
    files=inventories[0]
    assert files==inventories[1]
    old=original['sha256_by_relative_path']
    differences={name for name in old if old[name]!=files[name]}
    assert differences=={'current-candidate.gba','current-candidate.json','build-manifest.json'}
    extra=files.keys()-old.keys()
    assert extra=={'initial-portrait.gba','initial-portrait.json','intermediate/source-english-menus-verification.json'}
    for name,digest in main.EXPECTED_LAYERS.items():
        assert files[name]==digest
    assert files['current-candidate.gba']==FINAL and files['current-candidate.json']==OWNER
    assert files['initial-portrait.gba']==old['current-candidate.gba'] and files['initial-portrait.json']==old['current-candidate.json']
    assert files['intermediate/source-english-menus-verification.json']==REVIEW
    report=dict(status='V90_SOURCE_ENGLISH_INDEPENDENT_PARENT_SUFFIX_PASS', main_sha256=PRIMARY,
                parent_audit_sha256=sha(args.v89_audit.read_bytes()), files_each=len(files),
                manifest_layers=len(main.EXPECTED_LAYERS), inherited_unchanged=len(old)-3, new_files=len(extra),
                verification='Each audited v89 inventory was copied, and normal production source_english_tail executed separately.',
                final_sha256=FINAL, report_sha256=REVIEW, sha256_by_relative_path=files)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['status'],len(files),sha(args.report.read_bytes()))

if __name__=='__main__':
    run()

