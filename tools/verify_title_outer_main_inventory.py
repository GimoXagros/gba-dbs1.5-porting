"""Audit title/outer-palette main integration and fresh complete inventories.
No production builders or semantic suites are executed by this checker.
"""
import argparse,ast,json,struct
from pathlib import Path
from verify_id13_main_inventory import need,sha,read,inventory
from verify_ai_iraira_main_inventory import inverse
ROOT=Path(__file__).resolve().parents[1]
MAIN_PATH='tools/build_current_candidate.py'
MAIN='6479CBB3A72F23E741E557AF4BC7CCF4300B1157CA41D470E99681E324EF500A'
OLD_MAIN='CDE1B90D92035168C3AC11A77FF561BEE8DC4D4F5F8B6A552EA0FDBDD4174621'
BEFORE='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
TITLE='3CB7A7137762AA77C7C8D9147CF32AB356CDB269E6CE819115B911DEF444E49E'
FINAL='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
BEFORE_MANIFEST='29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900'
TITLE_MANIFEST='2EDEA4E7EFF23EDD7A9C2F5E39262CF92089BBC379EE83F571665324E7E678DD'
MANIFEST='4BD830DB3203F961E45E587EAAC244A17B756C1D29A3FC3DA608CA9EE191CCF9'
PRIOR=ROOT/'build/ai-iraira-main-inventory-20261117/final.json'
PRIOR_SHA='42593FA65CCEAD092CB16227A4625A2BA385C10FCA87DED5DDD14DBCA8ED28A6'
TITLE_GATE='94DCC785AD5CF8305F4B0B95143E82AC82C9DE46D123FDF659FCC1F63BAB10F2'
OUTER_GATE='C095EBCB4238A058BA763C2C322E70EF59B0D0C348B19F6282AD3034A10C1C8B'
PINS={
 'tools/build_mode20_title_assets.py':'39F0DBD4F715AE9393009DBCDFDD2ACFB71B6960A3666ACFF2A34E0CDB30B1D0',
 'tools/build_iraira_outer_palette_route.py':'C316A5D4BAC203B17AB6760B4524D9070599D534B779F91A216CF3987C77C08D',
 'tools/verify_mode20_title_assets.py':'115720219E185AE284EF999EA747A94F79AA8A48DACE09585CBD093A2BD7EC03',
 'tools/verify_iraira_outer_palette_route_portable.py':'B4B083E8D01FFEFC0608A34810E338DEF623780103206A01946A779C8BD0BF75',
 'tools/verify_iraira_palette_outer_reconstruction.py':'928A6C4C1F34D5F411BD811385E5BC284AD4332C42DB864069BC3308E4D67987',
 'tools/verify_ai_iraira_main_inventory.py':'22D8F63C808AA8AE4054ACABD82DD200022F6AA6C2FE63FC58BB8A815D59E145',
}
ARTIFACTS={'iraira-render.gba':BEFORE,'iraira-render.json':BEFORE_MANIFEST,
 'mode20-title-assets.gba':TITLE,'mode20-title-assets.json':TITLE_MANIFEST,
 'intermediate/mode20-title-assets-verification.json':TITLE_GATE,
 'intermediate/iraira-outer-palette-verification.json':OUTER_GATE,
 'current-candidate.gba':FINAL,'current-candidate.json':MANIFEST}
VARIABLES={'iraira_render':"output / 'iraira-render.gba'",'mode20_title':"output / 'mode20-title-assets.gba'",
 'mode20_review':"intermediate / 'mode20-title-assets-verification.json'",'outer_review':"intermediate / 'iraira-outer-palette-verification.json'"}
CALLS={
 'build_mode20_title_assets.py':["'--before'",'iraira_render',"'--source'",'args.wsc15',"'--owner'","output / 'iraira-render.json'","'--output'",'mode20_title',"'--manifest'","output / 'mode20-title-assets.json'"],
 'build_iraira_outer_palette_route.py':["'--before'",'mode20_title',"'--source'",'args.wsc15',"'--owners'","output / 'mode20-title-assets.json'","output / 'iraira-render.json'","output / 'character-ai-parameter-alignment.json'","'--output'",'candidate',"'--manifest'","output / 'current-candidate.json'"],
 'verify_mode20_title_assets.py':["'--before'",'iraira_render',"'--after'",'mode20_title',"'--source'",'args.wsc15',"'--owner'","output / 'iraira-render.json'","'--report'",'mode20_review'],
 'verify_iraira_outer_palette_route_portable.py':["'--before'",'mode20_title',"'--after'",'candidate',"'--source'",'args.wsc15',"'--report'",'outer_review'],
}
GATES={'mode20_review':TITLE_GATE,'outer_review':OUTER_GATE}
META={
 'mode20_title_assets':{'verification_sha256':TITLE_GATE,'declared_bytes':60,'changed_bytes':58,'new_RAM_bytes':0,'mode23_implemented':False,'native_timing_and_task_handshake_retained':True,'actual_runtime_verified':False,'final_port_complete':False},
 'iraira_outer_palette':{'verification_sha256':OUTER_GATE,'declared_bytes':64,'changed_bytes':63,'new_RAM_bytes':0,'replaces_stage10_legacy_stage3_display_dispatch':True,'retains_source_common_font_overlay':True,'actual_runtime_verified':False,'final_port_complete':False},
}
ISOLATED={
 'build/mode20-title-assets-v85-20261117/component.gba':TITLE,
 'build/mode20-title-assets-v85-20261117/component.json':TITLE_MANIFEST,
 'build/iraira-outer-palette-v86-20261117/component.gba':FINAL,
 'build/iraira-outer-palette-v86-20261117/component.json':MANIFEST,
 'build/mode20-title-independent-20261117/report.json':TITLE_GATE,
 'build/iraira-outer-palette-portable-independent-20261117/report.json':OUTER_GATE,
}
TITLE_SPANS={0xD8B400:48,0x406DC:4,0x4072C:4,0x4073C:4}
OUTER_SPANS={0xD8B640:60,0xD0BD0:4}
def component_layers(before,title,final,tm,om):
 inverse(before,title,tm,TITLE_SPANS,BEFORE,TITLE,60,58)
 inverse(title,final,om,OUTER_SPANS,TITLE,FINAL,64,63)
 expected=bytearray(before)
 # Exact reviewed instructions and typed aliases, no builder imports.
 expected[0xD8B400:0xD8B430]=bytes.fromhex('18509fe518409fe5022ba0e3dcd5c9eb10409fe5132da0e30ce09fe5d8d5c9ea0032000680267108407f7108ec060408')
 for a,v in ((0x406DC,0xEA352B47),(0x4072C,0x086FBDA8),(0x4073C,0x086FC198)):struct.pack_into('<I',expected,a,v)
 need(bytes(expected)==title,'entire title layer independently reconstructed')
 expected[0xD8B640:0xD8B67C]=struct.pack('<15I',0xE92D4007,0xE10F2000,0xE59F1024,0xE5D1000E,0xE350000A,0x0A000002,0xE128F002,0xE8BD4007,0xEADFE4E6,0xE128F002,0xE8BD4007,0xE59FE004,0xEACCE593,0x03002310,0x080D0BE8)
 struct.pack_into('<I',expected,0xD0BD0,0xEB32EA9A)
 need(bytes(expected)==final,'entire outer layer independently reconstructed')
 need(all(not max(a,c)<min(a+n,c+m) for a,n in TITLE_SPANS.items() for c,m in OUTER_SPANS.items()),'new layers disjoint')
 return dict(title_spans=4,title_declared_bytes=60,title_changed_bytes=58,outer_spans=2,outer_declared_bytes=64,outer_changed_bytes=63,new_RAM_bytes=0,entire_images_reconstructed=True)

def verify_main(raw):
 need(sha(raw)==MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n',b''),'frozen CRLF main')
 tree=ast.parse(raw)
 expected={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('EXPECTED_')}
 need(all(expected['EXPECTED_LAYERS'][name]==value for name,value in (('iraira-render.gba',BEFORE),('mode20-title-assets.gba',TITLE),('current-candidate.gba',FINAL))),'all three explicit layer identities')
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 removed=[];bindings={};calls={};gates={}
 for node in main.body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name) and target.id in VARIABLES:
     need(target.id not in bindings,'unique new variable');bindings[target.id]=ast.unparse(node.value);removed.append(node)
  if not(isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)):continue
  call=node.value
  if not(isinstance(call.func,ast.Name) and call.args):continue
  first=call.args[0]
  if call.func.id=='run' and isinstance(first,ast.Constant) and first.value in CALLS:
   need(first.value not in calls and not call.keywords,'unique new layer call');calls[first.value]=[ast.unparse(v) for v in call.args[1:]];removed.append(node)
  if call.func.id=='require_hash' and isinstance(first,ast.Name) and first.id in GATES:
   need(first.id not in gates,'unique independent gate');gates[first.id]=ast.literal_eval(call.args[1]);removed.append(node)
 need(bindings==VARIABLES and calls==CALLS and gates==GATES and len(removed)==10,'exact four bindings, four calls, two independent gates')
 lines={i for n in removed for i in range(n.lineno-1,n.end_lineno)};metadata={}
 for node in ast.walk(tree):
  if isinstance(node,ast.Dict):
   for key,value in zip(node.keys,node.values):
    if isinstance(key,ast.Constant) and key.value in (*META,'iraira-render.gba','mode20-title-assets.gba'):
     if key.value in META:
      need(key.value not in metadata,'unique metadata');metadata[key.value]=ast.literal_eval(value)
     lines.update(range(key.lineno-1,value.end_lineno))
 need(metadata==META,'exact bounded metadata for both layers')
 inverse=b''.join(line for i,line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
 changes=[(b'"--output", iraira_render, "--manifest", output / "iraira-render.json")',b'"--output", candidate, "--manifest", output / "current-candidate.json")'),
  (b'run("verify_iraira_render_consumers.py", "--before", ai_aligned, "--after", iraira_render,',b'run("verify_iraira_render_consumers.py", "--before", ai_aligned, "--after", candidate,'),
  (b'"--source", args.wsc15, "--manifest", output / "iraira-render.json",',b'"--source", args.wsc15, "--manifest", output / "current-candidate.json",'),
  (FINAL.encode(),BEFORE.encode())]
 for new,old in changes:
  need(inverse.count(new)==1,'unique previous-layer retarget');inverse=inverse.replace(new,old)
 need(sha(inverse)==OLD_MAIN,'whole main inverse to CDE1; every earlier call, gate and metadata retained')
 return expected

def preflight():
 raw=read(PRIOR);need(sha(raw)==PRIOR_SHA,'frozen completed v84 inventory')
 prior=json.loads(raw)
 need((prior['status'],prior['files_each'],prior['manifest_entries_each'],prior['final_sha256'])==('AI_IRAIRA_TWO_BUILD_INVENTORY_PASS',346,132,BEFORE),'historical closure')
 pins={**prior['source_tool_sha256'],**PINS,MAIN_PATH:MAIN}
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'frozen source '+path)
 expected=verify_main(read(ROOT/MAIN_PATH))
 isolated={**prior['isolated_inputs'],**ISOLATED}
 for path,digest in isolated.items():need(sha(read(ROOT/path))==digest,'frozen isolated '+path)
 proofs=component_layers(read(ROOT/'build/iraira-render-repair-v84-20261117/component.gba'),read(ROOT/'build/mode20-title-assets-v85-20261117/component.gba'),read(ROOT/'build/iraira-outer-palette-v86-20261117/component.gba'),json.loads(read(ROOT/'build/mode20-title-assets-v85-20261117/component.json')),json.loads(read(ROOT/'build/iraira-outer-palette-v86-20261117/component.json')))
 for path in prior['builds']:need(inventory(ROOT/path)==prior['sha256_by_relative_path'],'all346 historical files unchanged')
 report=dict(status='TITLE_OUTER_MAIN_PREFLIGHT_PASS',main_sha256=MAIN,whole_main_inverse_sha256=OLD_MAIN,isolated_inputs=isolated,final_sha256=FINAL,predicted_files_each=352,predicted_manifest_entries_each=134,new_calls=CALLS,independent_gates=GATES,component_proofs=proofs,old_semantic_suites_rerun=False,full_build_executed_by_auditor=False,emulator_launched_by_auditor=False)
 return prior,pins,expected,report

def audit(args,prior,pins,expected,report):
 need(args.root_completed and args.build_a and args.build_b,'root original completion of both full builds required')
 builds=[args.build_a.resolve(),args.build_b.resolve()];historical=[(ROOT/p).resolve() for p in prior['builds']]
 need(len(set(builds))==2 and not set(builds)&set(historical) and all(d.parent==ROOT/'build' for d in builds),'distinct fresh workspace builds')
 old=prior['sha256_by_relative_path'];actual=[inventory(d) for d in builds]
 added=set(ARTIFACTS)-{'current-candidate.gba','current-candidate.json'}
 need(len(added)==6 and actual[0]==actual[1] and len(actual[0])==352 and actual[0].keys()-old.keys()==added and not old.keys()-actual[0].keys(),'352 identical files and exactly six additions')
 changed=sorted(p for p in old if old[p]!=actual[0][p])
 need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'only three shared paths changed')
 for path,digest in ARTIFACTS.items():need(actual[0][path]==digest,'actual new layer or gate '+path)
 old_manifest=json.loads(read(historical[0]/'build-manifest.json'));closures=[]
 for directory in builds:
  manifest=json.loads(read(directory/'build-manifest.json'))
  need(manifest.keys()-old_manifest.keys()==set(META) and not old_manifest.keys()-manifest.keys(),'exactly two new metadata sections')
  for key,value in META.items():need(manifest[key]==value,'bounded new metadata '+key)
  for key,value in old_manifest.items():
   if key!='layers':need(manifest[key]==value,'all prior metadata unchanged '+key)
  entries=[]
  for key,subdir,const in [('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')]:
   need(manifest[key]==expected[const],'literal manifest closure '+key)
   for name,digest in manifest[key].items():
    need(Path(name).name==name and sha(read(directory/subdir/name))==digest,'actual asset/layer '+name)
    entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
  need(len(entries)==134,'complete134 manifest entries');closures.append(entries)
  component_layers(read(directory/'iraira-render.gba'),read(directory/'mode20-title-assets.gba'),read(directory/'current-candidate.gba'),json.loads(read(directory/'mode20-title-assets.json')),json.loads(read(directory/'current-candidate.json')))
 need([inventory(d) for d in builds]==actual and all(inventory(d)==old for d in historical),'fresh and historical inventories unchanged after audit')
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'all sources unchanged after audit')
 report.update(status='TITLE_OUTER_TWO_BUILD_INVENTORY_PASS',files_each=352,manifest_entries_each=134,builds=[d.relative_to(ROOT).as_posix() for d in builds],sha256_by_relative_path=actual[0],source_tool_sha256=pins,manifest_closures=closures,changed_shared_v84_paths=changed,baseline_audit_sha256=PRIOR_SHA,whole_new_layers_inverse=True,previous_346_artifacts_preserved=True)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--preflight',action='store_true');p.add_argument('--root-completed',action='store_true')
 p.add_argument('--build-a',type=Path);p.add_argument('--build-b',type=Path);p.add_argument('--report',type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report required')
 prior,pins,expected,result=preflight()
 if a.preflight:need(not a.root_completed and not a.build_a and not a.build_b,'preflight excludes fresh builds')
 else:audit(a,prior,pins,expected,result)
 result['checker_sha256']=sha(read(Path(__file__)));a.report.parent.mkdir(parents=True,exist_ok=True)
 with a.report.open('x',encoding='utf-8',newline='\n') as out:json.dump(result,out,indent=2);out.write('\n')
 print(result['status'],sha(read(a.report)))
