#!/usr/bin/env python3
"""Completed fresh v74 inventories/manifest closures; no component reruns."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BUILDS=[ROOT/'build'/('repro-v74-20261109-'+x)for x in('a','b')]
PRIOR=ROOT/'build/repro-v73-final-audit-20261109/audit.json'
PRIOR_SHA='C512D0F62F05DB54CF4FD0A4315B14C6B313D09663C600BA34D079F8CE0120F6'
PRIOR_SCRIPT_SHA='4D5C0AD35E8674F180E5D561E21E04FCC98D28410E8A5C6896CBCC9E62A0595F'
V73='6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7'
SCENE='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
FINAL='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
SCENE_MANIFEST='242392FDE02B9DD6666578EE97E0F5F3EBA26E684F60BECABCC66EC1EBAC8639'
RECT_MANIFEST='FF0B5FFF3B43E692128A0A6B857AFC97F9FE714657439ACFD2CE05D078B2FF73'
SCENE_QA='37812C30D6A1EA005F48CB1E3298D38FBCD795008A614CEEA9339679B16B75B8'
RECT_QA='BAD282D7F5AEAC391022D3A3C350C4257A6BC15A901406EC29F875CEDFB4DACA'
PINS={
 'tools/build_current_candidate.py':'1090E51AE1CA2C6EC4B2C13A2F05D5D271DBBDB250B149D716B0F6FE691B3AA3',
 'tools/verify_result_language_capture.py':'DFDD17521A0B728EE4ED1B511EF606D736DD61269B87EFC9AF2CFBD22CE42025',
 'tools/build_shoot_native_scene_connection.py':'2C73B081970F3466CEE1932AC15CAA876F3292CB6A2C59916C6AE2071D652E2E',
 'tools/build_shoot_child_attack_rectangle.py':'185072F560F82D5A8AD63E416E3E8C9A5A2503B353A5AEA9597C9F44CF20A3E1',
 'tools/verify_shoot_native_scene_connection.py':'7DCD32B0628DF3ACA1A32D77C6E3A8BA5680071612E5727616553DBCCF26F72F',
 'tools/verify_shoot_child_attack_rectangle_production.py':'18CA71F93F238A33B0BC1C756CBE0A3F47FEC6E98B47C7B2F21F82751BC90FB4',
 'tools/verify_result_v74_integration.py':'67C68ECED8B42BC0736F8A04EAECE3C4163F757901CFF08052EB7E62A860FB68'}
NEW_PATHS={'shoot-fatal-callback.gba','shoot-fatal-callback.json','shoot-native-scene.gba','shoot-native-scene.json',
 'intermediate/shoot-native-scene-verification.json','intermediate/shoot-child-rectangle-verification.json'}
SCENE_SPANS=[(0x33FD04,4),(0x6FF380,104),(0x5C9108,4),(0x5C910C,4),(0x5C9120,4),(0x5C9174,4),(0x5C91A4,4),
 (0x373ED8,4),(0x6FF400,16),(0x36E634,4)]
RECT_SPANS=[(a,4)for a in range(0x5B90A4,0x5B9115,16)]+[(0x5B9180,10)]
HISTORICAL=('resident_controller_bridge','shoot_attack_dispatch','shoot_spatial_subset','shoot_static_companion_clear',
            'shoot_projectile_clear','shoot_guarded_transition','shoot_fatal_callback_route')

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(blob):return hashlib.sha256(blob).hexdigest().upper()
def read(path):
    need(path.suffix.lower()not in('.sav','.state'),'no save/state access')
    return path.read_bytes()
def inventory(directory):
    return {p.relative_to(directory).as_posix():sha(read(p))for p in sorted(directory.rglob('*'))if p.is_file()}
def inverse(after,before,spans):
    need(len(after)==len(before)==0x800000,'complete eight MiB')
    restored=bytearray(after)
    for a,n in spans:restored[a:a+n]=before[a:a+n]
    need(bytes(restored)==before,'complete inverse including unowned bytes/padding')

def expected_sections(source):
    expected={};literal_sections={}
    tree=ast.parse(source)
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for name in node.targets:
                if isinstance(name,ast.Name)and name.id.startswith('EXPECTED_'):expected[name.id]=ast.literal_eval(node.value)
    for node in ast.walk(tree):
        if isinstance(node,ast.Dict):
            for key,value in zip(node.keys,node.values):
                if isinstance(key,ast.Constant)and key.value in HISTORICAL+('shoot_native_scene_connection','shoot_child_command_rectangles','resident_scene','resident_callers','claim_scope'):
                    literal_sections[key.value]=ast.literal_eval(value)
    return expected,literal_sections

def manifest_writes(before,after,manifest,spans):
    need([(w['raw'],w['bytes'])for w in manifest['writes']]==spans,'exact manifest write domain')
    for w in manifest['writes']:
        at,n=w['raw'],w['bytes']
        need(before[at:at+n]==bytes.fromhex(w['before'])and after[at:at+n]==bytes.fromhex(w['after']),'fresh manifest actual old/new bytes')
    inverse(after,before,spans)

def audit(root_completed):
    need(root_completed,'root must confirm both build processes completed before audit')
    need(sha(read(PRIOR))==PRIOR_SHA and sha(read(PRIOR.with_name('audit_inputs.py')))==PRIOR_SCRIPT_SHA,'frozen completed v73 audit')
    trusted=json.loads(read(PRIOR));old=trusted['sha256_by_relative_path']
    need(trusted['status']=='PASS'and trusted['final_sha256']==V73 and len(old)==295,'trusted completed prior inventory')
    pins={**trusted['source_tool_sha256'],**PINS,'tools/'+Path(__file__).name:sha(read(Path(__file__)))}
    for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'frozen source '+path)
    actual=[inventory(directory)for directory in BUILDS]
    need(actual[0]==actual[1]and len(actual[0])==301,'all fresh A/B relative paths and full file hashes identical')
    changed=sorted(k for k in actual[0].keys()&old.keys()if actual[0][k]!=old[k])
    need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'only three shared outputs changed')
    need(not old.keys()-actual[0].keys()and actual[0].keys()-old.keys()==NEW_PATHS,'six exact new paths and no old artifact removed')
    need(actual[0]['shoot-fatal-callback.gba']==old['current-candidate.gba']==V73 and
         actual[0]['shoot-fatal-callback.json']==old['current-candidate.json'],'entire old final ROM/manifest preserved as fatal layer')
    need(actual[0]['shoot-native-scene.gba']==SCENE and actual[0]['shoot-native-scene.json']==SCENE_MANIFEST and
         actual[0]['current-candidate.gba']==FINAL and actual[0]['current-candidate.json']==RECT_MANIFEST,'new ROMs and source-only manifests pinned')
    need(actual[0]['intermediate/shoot-native-scene-verification.json']==SCENE_QA and
         actual[0]['intermediate/shoot-child-rectangle-verification.json']==RECT_QA,'fresh path-independent production proofs exact')
    previous=read(ROOT/'build/repro-v73-20261109-a/current-candidate.gba')
    need(sha(previous)==V73 and read(ROOT/'build/repro-v73-20261109-b/current-candidate.gba')==previous,'completed prior ROM identity')
    oldbm_blob=read(ROOT/'build/repro-v73-20261109-a/build-manifest.json')
    need(sha(oldbm_blob)==old['build-manifest.json'],'old main manifest bound')
    oldbm=json.loads(oldbm_blob)
    expected,sections=expected_sections(read(ROOT/'tools/build_current_candidate.py'))
    allowed_changed={'claim_scope','layers','resident_scene','resident_callers',*HISTORICAL}
    need(len(SCENE_SPANS+RECT_SPANS)==19 and sum(n for _,n in SCENE_SPANS+RECT_SPANS)==194,'19 spans194 declared bytes')
    sorted_spans=sorted((a,a+n)for a,n in SCENE_SPANS+RECT_SPANS)
    need(all(z<=a for(_,z),(a,_)in zip(sorted_spans,sorted_spans[1:])),'pairwise disjoint composition')
    closures=[];results=[]
    for directory in BUILDS:
        fatal,scene,final=(read(directory/p)for p in('shoot-fatal-callback.gba','shoot-native-scene.gba','current-candidate.gba'))
        need(fatal==previous,'exact preserved v73 fatal predecessor')
        sm,rm=(json.loads(read(directory/p))for p in('shoot-native-scene.json','current-candidate.json'))
        need((sm['input_sha256'],sm['output_sha256'])==(V73,SCENE)and(rm['input_sha256'],rm['output_sha256'])==(SCENE,FINAL),'manifest chain identities')
        manifest_writes(fatal,scene,sm,SCENE_SPANS);manifest_writes(scene,final,rm,RECT_SPANS)
        inverse(final,fatal,SCENE_SPANS+RECT_SPANS)
        need(sum(a!=b for a,b in zip(fatal,scene))==sm['changed_bytes']==136 and
             sum(a!=b for a,b in zip(scene,final))==rm['changed_bytes']==34 and
             sum(a!=b for a,b in zip(fatal,final))==170,'full ROM changed-byte counts')
        for at in(0x5B918A,0x6FF3E8,0x6FF410,0x6FF720,0x36E5EC,0xD0BE8,0x7FFFFF):
            bad=bytearray(final);bad[at]^=1
            try:inverse(bytes(bad),fatal,SCENE_SPANS+RECT_SPANS)
            except ValueError:pass
            else:raise ValueError('undeclared corruption accepted '+hex(at))
        for name in('shoot-native-scene.json','current-candidate.json'):
            for tool,digest in json.loads(read(directory/name))['dependencies'].items():
                need(sha(read(ROOT/'tools'/tool))==digest,'fresh component tracked dependency '+tool)
                pins['tools/'+tool]=digest
        for name in('shoot-native-scene-verification.json','shoot-child-rectangle-verification.json'):
            report=json.loads(read(directory/'intermediate'/name))
            for tool,digest in report['dependencies'].items():
                need(sha(read(ROOT/'tools'/tool))==digest,'fresh proof tracked dependency '+tool)
                pins['tools/'+tool]=digest
        bm=json.loads(read(directory/'build-manifest.json'))
        for key in oldbm:
            if key not in allowed_changed:need(bm[key]==oldbm[key],'retained manifest field '+key)
        need(bm.keys()-oldbm.keys()=={'shoot_native_scene_connection','shoot_child_command_rectangles'},'only two new manifest sections')
        for key,value in sections.items():need(bm[key]==value,'fresh main literal contract '+key)
        for section in HISTORICAL:
            renames=('external_scene_route_installed','nonfatal_hook_installed')if section=='shoot_fatal_callback_route'else('external_scene_route_installed',)
            historical=dict(oldbm[section])
            for key in renames:historical[key+'_by_this_layer']=historical.pop(key)
            need(bm[section]==historical,'old layer contract only historical key qualification')
        need(all(bm['resident_scene'][k]==v for k,v in oldbm['resident_scene'].items()if k not in('external_route_installed','scope')),'retained scene fields')
        need(all(bm['resident_callers'][k]==v for k,v in oldbm['resident_callers'].items()if k!='scope'),'resident callers change only qualified scope')
        entries=[]
        for key,subdir,const in(('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),
            ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')):
            need(bm[key]==expected[const],'complete expected main section '+key)
            for name,digest in bm[key].items():
                need(Path(name).name==name and sha(read(directory/subdir/name))==digest,'manifest closure '+name)
                entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
        need(len(entries)==117,'all117 manifest entries recomputed')
        closures.append(entries);results.append(dict(build=directory.relative_to(ROOT).as_posix(),scene_inverse=True,rectangle_inverse=True,
            full_inverse_to_v73=True,declared_bytes=194,changed_bytes=170))
    need(inventory(BUILDS[0])==actual[0]==inventory(BUILDS[1]),'both inventories unchanged during audit')
    for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'source remains frozen '+path)
    return dict(status='PASS',files_each=301,builds=[p.relative_to(ROOT).as_posix()for p in BUILDS],sha256_by_relative_path=actual[0],
        source_tool_sha256=pins,final_sha256=FINAL,exact_v73_predecessor=V73,native_scene_intermediate=SCENE,
        trusted_v73_audit_sha256=PRIOR_SHA,trusted_v73_script_sha256=PRIOR_SCRIPT_SHA,
        entire_relative_path_and_hash_inventories_match=True,changed_shared_v73_paths=changed,new_relative_paths=sorted(NEW_PATHS),
        all_previous_artifacts_and_proofs_retained=True,manifest_closures=closures,manifest_entries_each=117,
        new_written_spans=19,new_declared_bytes=194,new_changed_bytes=170,whole_new_layers_inverse_to_v73=True,
        isolated_component_QA_sha256=[SCENE_QA,RECT_QA],independent_verifiers_rerun=[],builds_verified=results,
        outside_boundary_corruption_negatives_each=7,
        limits=['Completed full output inventories and exact inverse only; existing v73/component semantic evidence reused without rerun.',
                'No emulator, original save/State access, game-memory write, ROM/main/Git modification or full build by auditor.',
                'Actual native positive-hit/expiry capture is a separate gate; terminal, moving low-Y, interrupted-DI, historical E5 and final-port completion remain open.'])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    need(not a.report.exists(),'fresh report');report=audit(a.root_completed)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'))
    print('PASS',report['files_each'],sha(read(a.report)))

if __name__=='__main__':main()
