"""Completed v76 inventories and new display layer; no build/semantic rerun."""
import argparse
import ast
import json
from pathlib import Path
from verify_repro_v74_inventory import ROOT,need,sha,read,inventory
from verify_shoot_terminal_display_epoch_production import inverse,INPUT,OUTPUT,WRITES

PRIOR=ROOT/'build/repro-v75-final-audit-20261110/audit.json'
PRIOR_SHA='B1A1B933658967298554D12FBDF1D565AB75A27C31A82E4565B7BD2FAEE4FC08'
PINS={
 'tools/build_current_candidate.py':'DE4B99720523A7B1FA4D4CD68C06F251A8B7C26C97167294C9195991BC0235C0',
 'tools/verify_result_language_capture.py':'665AE76FDFCCF1806FE060C137E2E591FF3B6510CC601F148EEB35FFABE3D328',
 'tools/build_shoot_terminal_display_epoch.py':'93BDB86A50E72E7227476369CA2DDFD8F9301B93BB3E40928291C48BFA16B260',
 'tools/verify_shoot_terminal_display_epoch_production.py':'E82C9F1A7EBC199DB13647776F93041AEA9F5A4600AA48491E5D696C185EE974'}
ADDED={'shoot-owner-link.gba','shoot-owner-link.json','intermediate/shoot-display-epoch-verification.json'}
BUILDS=[ROOT/'build'/('repro-v76-20261110-'+x) for x in ('a','b')]

def audit(completed):
    need(completed,'root confirms both finished before reading outputs')
    need(sha(read(PRIOR))==PRIOR_SHA,'completed v75 baseline')
    prior=json.loads(read(PRIOR));old=prior['sha256_by_relative_path']
    need(prior['status']=='PASS' and prior['final_sha256']==INPUT and len(old)==307,'v75 contract')
    pins={**prior['source_tool_sha256'],**PINS,'tools/'+Path(__file__).name:sha(read(Path(__file__)))}
    for p,h in pins.items():need(sha(read(ROOT/p))==h,'source '+p)
    baseline=[ROOT/'build'/('repro-v75-20261110-'+x) for x in ('a','b')]
    need(all(inventory(p)==old for p in baseline),'both v75 inventories intact')
    actual=[inventory(p) for p in BUILDS]
    need(actual[0]==actual[1],'all actual fresh relative paths and hashes equal')
    need(not old.keys()-actual[0].keys() and actual[0].keys()-old.keys()==ADDED,'three exact additions no removed paths')
    need(len(actual[0])==len(old)+len(ADDED)==310,'derived310 files')
    changed=sorted(k for k in old.keys()&actual[0].keys() if old[k]!=actual[0][k])
    need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'three changed shared paths')
    for p,h in {'shoot-owner-link.gba':INPUT,'shoot-owner-link.json':old['current-candidate.json'],
                'current-candidate.gba':OUTPUT,'current-candidate.json':'F8C53C3C4FCA703316F0638DE0DFC61AEA16F3A2D987D781DB7215A9D82F345B',
                'intermediate/shoot-display-epoch-verification.json':'AFC67C96B20744286BEC58BA05313808A7CE22D3788E05E6B2385874A8ADCE65'}.items():
        need(actual[0][p]==h,'new/preserved artifact '+p)
    tree=ast.parse(read(ROOT/'tools/build_current_candidate.py'));expected={};sections={}
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id.startswith('EXPECTED_'):expected[t.id]=ast.literal_eval(n.value)
    for n in ast.walk(tree):
        if isinstance(n,ast.Dict):
            for k,v in zip(n.keys,n.values):
                if isinstance(k,ast.Constant) and k.value in ('claim_scope','shoot_terminal_display_epoch'):sections[k.value]=ast.literal_eval(v)
    need(len(sections)==2,'new main literal contracts')
    oldbm=json.loads(read(baseline[0]/'build-manifest.json'));closures=[]
    for directory in BUILDS:
        before=read(directory/'shoot-owner-link.gba');after=read(directory/'current-candidate.gba');inverse(before,after)
        m=json.loads(read(directory/'current-candidate.json'))
        need(m['input_sha256']==INPUT and m['output_sha256']==OUTPUT and m['expected_writes']==
             [dict(offset=a,before=before[a:a+len(b)].hex(),after=b.hex()) for a,b in WRITES],'exact new manifest words')
        need(sum(a!=b for a,b in zip(before,after))==m['changed_bytes']==69 and m['declared_bytes']==84,'actual byte counts')
        bm=json.loads(read(directory/'build-manifest.json'))
        need(bm.keys()-oldbm.keys()=={'shoot_terminal_display_epoch'} and not oldbm.keys()-bm.keys(),'one new section only')
        for key,value in oldbm.items():
            if key not in ('claim_scope','layers'):need(bm[key]==value,'retained manifest field '+key)
        for key,value in sections.items():need(bm[key]==value,'new literal '+key)
        entries=[]
        for key,subdir,const in (('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),
             ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')):
            need(bm[key]==expected[const],'complete expected '+key)
            for name,h in bm[key].items():
                need(Path(name).name==name and sha(read(directory/subdir/name))==h,'closure '+name)
                entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=h))
        need(len(entries)==prior['manifest_entries_each']+1==120,'derived120 closure entries');closures.append(entries)
    need(actual[0]==inventory(BUILDS[0])==inventory(BUILDS[1]),'new outputs unchanged during audit')
    need(all(inventory(p)==old for p in baseline),'old outputs remain unchanged')
    for p,h in pins.items():need(sha(read(ROOT/p))==h,'source remains frozen '+p)
    return dict(status='PASS',files_each=len(actual[0]),manifest_entries_each=len(closures[0]),final_sha256=OUTPUT,
                sha256_by_relative_path=actual[0],source_tool_sha256=pins,manifest_closures=closures,
                trusted_v75_audit_sha256=PRIOR_SHA,exact_v75_predecessor=INPUT,changed_shared_v75_paths=changed,
                new_relative_paths=sorted(ADDED),all_previous_artifacts_and_proofs_retained=True,
                new_written_spans=4,new_declared_bytes=84,new_changed_bytes=69,whole_new_layer_inverse_to_v75=True,
                independent_verifiers_rerun=[],full_build_executed=False,emulator_launched=False,
                earliest_counter_runtime_deadline_verified=False,final_port_complete=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report');r=audit(a.root_completed)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode())
    print('PASS',r['files_each'],r['manifest_entries_each'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
