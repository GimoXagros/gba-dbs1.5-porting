"""Independent main inverse and two fresh inventories for child-contact repair."""
import argparse
import ast
import json
from pathlib import Path

from verify_id13_main_inventory import need,sha,read,inventory
from verify_shoot_child_contact_component import ownership

ROOT=Path(__file__).resolve().parents[1]
MAIN='7B293379F8EA36BC9AE8264561F7F2A59660F7A03A78857FA9D4C44FD7C54F3E'
OLD_MAIN='6479CBB3A72F23E741E557AF4BC7CCF4300B1157CA41D470E99681E324EF500A'
BEFORE='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
FINAL='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
MANIFEST='162C4A9D2B8A684582EF2C3F22D8E60B6887E832BEBE4CB23730169C2198425C'
PRIOR=ROOT/'build/title-outer-main-inventory-20261117/final.json'
PRIOR_SHA='EB576653FAD931104CF36EB0A8F381F215B5B36F5B380061446531CBF6769DFB'
GATES={'contact_review':'74462AE34C72F28510474E1DF68B3CFA9DB8BD49C95EB8F9C3314FE17991DF77',
 'contact_callbacks_review':'D6958EA29893D14A0684DB110240C0B58805191C62B6419F47C2052341E20C3B'}
PINS={'tools/build_shoot_child_contact.py':'4DB5FA23EB23B3BE60B295405B300C2C2C7A4F7F05CCD88E08DC3DC20983ACE0',
 'tools/shoot_child_contact_callbacks.py':'8520DA8E5ECB4163936759FCD7FA690222A8A1498B74FC51CFEBC740905EFA98',
 'tools/verify_shoot_child_contact_component.py':'7CAFD1342EC1F9F799A7D2A1553ACA349CFD2333C65FDF16D3E5958FF8A11029',
 'tools/verify_shoot_child_contact_callbacks.py':'807A282826D7EE5AFF2006C7D71803E3DEAB4413E59369BB2E314D7671F7A117'}
CALLS={
 'build_shoot_child_contact.py':["'--before'",'iraira_outer',"'--source'",'args.wsc15',"'--output'",'candidate',"'--manifest'","output / 'current-candidate.json'"],
 'verify_shoot_child_contact_component.py':["'--before'",'iraira_outer',"'--after'",'candidate',"'--source'",'args.wsc15',"'--report'",'contact_review'],
 'verify_shoot_child_contact_callbacks.py':["'--before'",'iraira_outer',"'--installed'",'candidate',"'--source'",'args.wsc15',"'--entry'","'0x08D8C800'","'--report'",'contact_callbacks_review']}
VARIABLES={'iraira_outer':"output / 'iraira-outer-palette.gba'",'contact_review':"intermediate / 'shoot-child-contact-verification.json'",'contact_callbacks_review':"intermediate / 'shoot-child-contact-callback-verification.json'"}
META={'verification_sha256':GATES['contact_review'],'callback_verification_sha256':GATES['contact_callbacks_review'],
 'declared_bytes':620,'changed_bytes':607,'new_RAM_bytes':0,'source_callbacks':['966A','96E6','973E'],
 'restores_stage11_contact_and_parent_parent_cooldown':True,'actual_runtime_verified':False,'final_port_complete':False}
ARTIFACTS={'iraira-outer-palette.gba':BEFORE,'iraira-outer-palette.json':'4BD830DB3203F961E45E587EAAC244A17B756C1D29A3FC3DA608CA9EE191CCF9',
 'intermediate/shoot-child-contact-verification.json':GATES['contact_review'],
 'intermediate/shoot-child-contact-callback-verification.json':GATES['contact_callbacks_review'],
 'current-candidate.gba':FINAL,'current-candidate.json':MANIFEST}

def verify_main(raw):
    need(sha(raw)==MAIN,'frozen main')
    tree=ast.parse(raw); removed=[]; bindings={}; calls={}; gates={}; meta=[]
    expected={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('EXPECTED_')}
    need(expected['EXPECTED_LAYERS']['iraira-outer-palette.gba']==BEFORE and expected['EXPECTED_LAYERS']['current-candidate.gba']==FINAL,'literal layer identities')
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    for n in main.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in VARIABLES:
            key=n.targets[0].id;need(key not in bindings,'unique binding');bindings[key]=ast.unparse(n.value);removed.append(n)
        if not isinstance(n,ast.Expr) or not isinstance(n.value,ast.Call):continue
        c=n.value
        if not isinstance(c.func,ast.Name) or not c.args:continue
        if c.func.id=='run' and isinstance(c.args[0],ast.Constant) and c.args[0].value in CALLS:
            key=c.args[0].value;need(key not in calls and not c.keywords,'unique call');calls[key]=[ast.unparse(x) for x in c.args[1:]];removed.append(n)
        if c.func.id=='require_hash' and isinstance(c.args[0],ast.Name) and c.args[0].id in GATES:
            key=c.args[0].id;need(key not in gates,'unique gate');gates[key]=ast.literal_eval(c.args[1]);removed.append(n)
    need(bindings==VARIABLES and calls==CALLS and gates==GATES and len(removed)==8,'exact3 bindings3 calls2 gates')
    lines={i for n in removed for i in range(n.lineno-1,n.end_lineno)}
    for n in ast.walk(tree):
        if not isinstance(n,ast.Dict):continue
        for k,v in zip(n.keys,n.values):
            if isinstance(k,ast.Constant) and k.value in ('shoot_child_contact','iraira-outer-palette.gba'):
                if k.value=='shoot_child_contact':meta.append(ast.literal_eval(v))
                lines.update(range(k.lineno-1,v.end_lineno))
    need(meta==[META],'bounded metadata')
    inverse=b''.join(s for i,s in enumerate(raw.splitlines(keepends=True)) if i not in lines)
    replacements=[(b'"--output", iraira_outer,',b'"--output", candidate,'),
      (b'"--manifest", output / "iraira-outer-palette.json")',b'"--manifest", output / "current-candidate.json")'),
      (b'"--after", iraira_outer,',b'"--after", candidate,'),(FINAL.encode(),BEFORE.encode())]
    for current,prior in replacements:
        need(inverse.count(current)==1,'unique prior-layer retarget');inverse=inverse.replace(current,prior)
    need(sha(inverse)==OLD_MAIN,'entire main inverse to6479')
    return expected

def preflight():
    raw=read(PRIOR);need(sha(raw)==PRIOR_SHA,'prior352-file final inventory')
    prior=json.loads(raw)
    need((prior['files_each'],prior['manifest_entries_each'],prior['final_sha256'])==(352,134,BEFORE),'historical baseline')
    pins={**prior['source_tool_sha256'],**PINS,'tools/build_current_candidate.py':MAIN}
    for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'source pin '+path)
    expected=verify_main(read(ROOT/'tools/build_current_candidate.py'))
    before=read(ROOT/'build/iraira-outer-palette-v86-20261117/component.gba')
    after=read(ROOT/'build/shoot-child-contact-20261117/component.gba')
    need(sha(before)==BEFORE and sha(after)==FINAL and ownership(before,after)==607,'isolated whole inverse')
    need(sha(read(ROOT/'build/shoot-child-contact-20261117/manifest.json'))==MANIFEST,'isolated manifest')
    isolated={**prior['isolated_inputs'],
      'build/shoot-child-contact-20261117/component.gba':FINAL,
      'build/shoot-child-contact-20261117/manifest.json':MANIFEST,
      'build/shoot-child-contact-independent-20261117/report.json':GATES['contact_review']}
    for path,digest in isolated.items():need(sha(read(ROOT/path))==digest,'isolated pin '+path)
    for path in prior['builds']:need(inventory(ROOT/path)==prior['sha256_by_relative_path'],'historical352 files unchanged')
    result=dict(status='CHILD_CONTACT_MAIN_PREFLIGHT_PASS',main_sha256=MAIN,whole_main_inverse_sha256=OLD_MAIN,
      final_sha256=FINAL,predicted_files_each=356,predicted_manifest_entries_each=135,
      independent_gates=GATES,isolated_inputs=isolated,old_semantic_suites_rerun=False,emulator_launched=False)
    return prior,pins,expected,result

def audit(a,prior,pins,expected,result):
    need(a.root_completed and a.build_a and a.build_b,'original root completion required')
    dirs=[a.build_a.resolve(),a.build_b.resolve()]; historical=[(ROOT/p).resolve() for p in prior['builds']]
    need(len(set(dirs))==2 and not set(dirs)&set(historical) and all(d.parent==ROOT/'build' for d in dirs),'two distinct fresh builds')
    old=prior['sha256_by_relative_path']; actual=[inventory(d) for d in dirs]
    added=set(ARTIFACTS)-{'current-candidate.gba','current-candidate.json'}
    need(actual[0]==actual[1] and len(actual[0])==356 and actual[0].keys()-old.keys()==added and not old.keys()-actual[0].keys(),'356 identical files; exactly4 additions')
    changed=sorted(p for p in old if old[p]!=actual[0][p])
    need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'only3 shared output changes')
    for path,digest in ARTIFACTS.items():need(actual[0][path]==digest,'new artifact '+path)
    previous=json.loads(read(historical[0]/'build-manifest.json'));closures=[]
    for d in dirs:
        manifest=json.loads(read(d/'build-manifest.json'))
        need(manifest.keys()-previous.keys()=={'shoot_child_contact'} and not previous.keys()-manifest.keys(),'one metadata addition')
        need(manifest['shoot_child_contact']==META,'bounded new metadata')
        for key,value in previous.items():
            if key!='layers':need(manifest[key]==value,'prior metadata '+key)
        entries=[]
        for key,subdir,const in [('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')]:
            need(manifest[key]==expected[const],'literal closure '+key)
            for name,digest in manifest[key].items():
                need(Path(name).name==name and sha(read(d/subdir/name))==digest,'actual asset/layer '+name)
                entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
        need(len(entries)==135,'all135 manifest entries');closures.append(entries)
        need(ownership(read(d/'iraira-outer-palette.gba'),read(d/'current-candidate.gba'))==607,'actual fresh whole inverse')
    need([inventory(d) for d in dirs]==actual and all(inventory(d)==old for d in historical),'fresh/historical outputs stable')
    for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'source stable '+path)
    result.update(status='CHILD_CONTACT_TWO_BUILD_INVENTORY_PASS',files_each=356,manifest_entries_each=135,
      builds=[d.relative_to(ROOT).as_posix() for d in dirs],sha256_by_relative_path=actual[0],source_tool_sha256=pins,
      manifest_closures=closures,changed_shared_paths=changed,baseline_audit_sha256=PRIOR_SHA,
      previous_352_artifacts_preserved=True,whole_new_layer_inverse=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight',action='store_true');p.add_argument('--root-completed',action='store_true')
    p.add_argument('--build-a',type=Path);p.add_argument('--build-b',type=Path);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report required')
    prior,pins,expected,result=preflight()
    if a.preflight:need(not a.root_completed and not a.build_a and not a.build_b,'preflight excludes fresh builds')
    else:audit(a,prior,pins,expected,result)
    result['checker_sha256']=sha(read(Path(__file__)));a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(result['status'],sha(read(a.report)))
