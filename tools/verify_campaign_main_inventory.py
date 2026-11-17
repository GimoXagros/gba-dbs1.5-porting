"""Independent campaign main wiring, whole-layer inverses and fresh inventories."""
import argparse
import ast
import json
from pathlib import Path
from verify_id13_main_inventory import need, sha, read, inventory

ROOT=Path(__file__).resolve().parents[1]
MAIN_PATH='tools/build_current_candidate.py'
MAIN='B82099CA9E1257148DF978F35BA763F7B8F78CFECBDFB90679C3ECD1E6A162BC'
OLD_MAIN='59F43FB5516E1500683A03FD90F197F8FFDDB1CA22A9CE028C0DF9A39C04D10C'
OLD='FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
MID='ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9'
FINAL='933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
OLD_MANIFEST='64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD'
MID_MANIFEST='54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55'
FINAL_MANIFEST='6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C'
GATE1='1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0'
GATE2='3E22A59DD56C2A5EF6F61FABDCACEEA62174636EDACE6BAEB1D7BACCB3FE9A84'
PRIOR=ROOT/'build/id13-main-inventory-20261117/final.json'
PRIOR_SHA='40FF6E21D86C7770C02337A524C6B1CE1074D7D820A02BDD7F5435A8B69900C6'
PINS={MAIN_PATH:MAIN,
 'tools/build_campaign_stage_progression.py':'91214454AEA2B90B8FC394C0E613A4B2CD3FC71A12B58A82C270531E5CA77699',
 'tools/build_campaign_progression_consumers.py':'1B1E669C90CEB4D7736A97D84052613158625C91B3D955D98EE01DECA449CA04',
 'tools/verify_campaign_stage_progression.py':'142A81724FD15EFF70330C6A154DFCF83DB3DEB024FD3D1AC75854F5546697F5',
 'tools/verify_campaign_stage_consumers_r2.py':'C84430D6E4007AFA316FC9F626964A4C3402EF561F94CB9BE574206B99D3AFAD',
 'tools/verify_id13_main_inventory.py':'596A662F1BA9BFD2B0F6F75059D3A86FBB8029195F35355A1A6DBF50B47E73B2'}
ARTIFACTS={'id13-air-relaunch.gba':OLD,'id13-air-relaunch.json':OLD_MANIFEST,
 'campaign-stage-progression.gba':MID,'campaign-stage-progression.json':MID_MANIFEST,
 'current-candidate.gba':FINAL,'current-candidate.json':FINAL_MANIFEST,
 'intermediate/campaign-stage-progression-verification.json':GATE1,
 'intermediate/campaign-stage-consumers-verification.json':GATE2}
ADDED=set(ARTIFACTS)-{'current-candidate.gba','current-candidate.json'}
META={'producer_verification_sha256':GATE1,'consumer_verification_sha256':GATE2,
 'mode_scope':'source config+25 mask0001 clear; alternate-mode owner remains unimplemented',
 'encounters':11,'RNG_rows':8,'ordinary_CPU_entries':11,'initial_AI_entries':13,
 'AI_entries_per_difficulty':12,'difficulty_rows':3,'declared_bytes':453,'changed_bytes':423,'new_RAM_bytes':0,
 'temporary_character_stage_override_removed':True,'dedicated_stage11_preserved':True,
 'actual_runtime_verified':False,'whole_campaign_runtime_verified':False,'final_port_complete':False}
SCOPE=(
 (('floor classification table; spawn selects the existing logical-stage service without changing ',
   'campaign progression, whose temporary character-route policy remains incomplete; '),
  ('floor classification table; spawn selects the existing logical-stage service; ',
   'clean Ver.1.5 mode now uses the source eleven-encounter campaign, RNG row and CPU table, ',
   'with authoritative stage getters, extended progress-indexed AI and decimal round labels; ')),
 (('source-only Train hazard state remains unimplemented; ',),
  ('source Train shake update reachability and native private state remain unproved; ',)),
 (('two manager lookups prioritize dedicated logical stage11 over temporary character routes; ',),
  ('two manager lookups retain dedicated logical stage11 priority; ',)))
CALLS={
 'build_campaign_stage_progression.py':["'--before'",'id13_air',"'--source'",'args.wsc15',
  "'--audio-manifest'","output / 'evolution-music.json'","'--table-manifest'","output / 'evolution-transition.json'",
  "'--id13-manifest'","output / 'id13-air-relaunch.json'","'--output'",'campaign_stage',"'--manifest'","output / 'campaign-stage-progression.json'"],
 'build_campaign_progression_consumers.py':["'--before'",'campaign_stage',"'--source'",'args.wsc15',
  "'--audio-manifest'","output / 'evolution-music.json'","'--table-manifest'","output / 'evolution-transition.json'",
  "'--id13-manifest'","output / 'id13-air-relaunch.json'","'--campaign-manifest'","output / 'campaign-stage-progression.json'",
  "'--output'",'candidate',"'--manifest'","output / 'current-candidate.json'"],
 'verify_campaign_stage_progression.py':["'--before'",'id13_air',"'--after'",'campaign_stage',
  "'--manifest'","output / 'campaign-stage-progression.json'","'--source'",'args.wsc15',"'--gba'",'args.gba',
  "'--audio-manifest'","output / 'evolution-music.json'","'--table-manifest'","output / 'evolution-transition.json'",
  "'--id13-manifest'","output / 'id13-air-relaunch.json'","'--report'",'campaign_review'],
 'verify_campaign_stage_consumers_r2.py':["'--before'",'campaign_stage',"'--after'",'candidate',
  "'--manifest'","output / 'current-candidate.json'","'--source'",'args.wsc15',
  "'--audio-manifest'","output / 'evolution-music.json'","'--table-manifest'","output / 'evolution-transition.json'",
  "'--id13-manifest'","output / 'id13-air-relaunch.json'","'--producer-manifest'","output / 'campaign-stage-progression.json'",
  "'--producer-review'",'campaign_review',"'--report'",'campaign_consumers_review']}
SPANS1={0xD3FB10:5,0xD3FB18:40,0xD3FB40:11,0xD3FB50:44,
 **{at:4 for at in (0x8B718,0x8B71C,0x8B720,0x8B724,0x8B6AC,0x8B6B0,0x8B6B4,0x8B6D8,0x582C44,0x584A04)}}
SPANS2={**{0xD3FEE0+i*12:12 for i in range(9)},**{0xD3FF4C+i*24:24 for i in range(3)},
 **{0xC7048+i*4:4 for i in range(12)},0xD3FF94:13,0xD3FFDC:12,0xD3FFA4:52,0xC6EEC:4,0xB5FB4:4}


def verify_main(raw):
 need(sha(raw)==MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n',b''),'exact frozenCRLF main')
 tree=ast.parse(raw)
 expected={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and
  len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('EXPECTED_')}
 need({k:expected['EXPECTED_LAYERS'][k] for k in ('id13-air-relaunch.gba','campaign-stage-progression.gba','current-candidate.gba')}
      =={k:ARTIFACTS[k] for k in ('id13-air-relaunch.gba','campaign-stage-progression.gba','current-candidate.gba')},'three exact image stages')
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
 variables={'id13_air':"output / 'id13-air-relaunch.gba'",'campaign_stage':"output / 'campaign-stage-progression.gba'",
  'campaign_review':"intermediate / 'campaign-stage-progression-verification.json'",
  'campaign_consumers_review':"intermediate / 'campaign-stage-consumers-verification.json'"}
 checks={'campaign_review':GATE1,'campaign_consumers_review':GATE2}
 bindings,calls,gates,removed={},{},{},[]
 for n in main.body:
  if isinstance(n,ast.Assign):
   for target in n.targets:
    if isinstance(target,ast.Name) and target.id in variables:
     need(target.id not in bindings,'one binding');bindings[target.id]=ast.unparse(n.value);removed.append(n)
  if not(isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)):continue
  call=n.value
  if not(isinstance(call.func,ast.Name) and call.args):continue
  arg=call.args[0]
  if call.func.id=='run' and isinstance(arg,ast.Constant) and arg.value in CALLS:
   need(arg.value not in calls and not call.keywords,'one new literal call')
   calls[arg.value]=[ast.unparse(x) for x in call.args[1:]];removed.append(n)
  if call.func.id=='require_hash' and isinstance(arg,ast.Name) and arg.id in checks:
   need(arg.id not in gates,'one independent gate');gates[arg.id]=ast.literal_eval(call.args[1]);removed.append(n)
 need(bindings==variables and calls==CALLS and gates==checks and len(removed)==10,'exact four new calls/paths/two gates')
 lines={i for n in removed for i in range(n.lineno-1,n.end_lineno)};metadata=[]
 for n in ast.walk(tree):
  if isinstance(n,ast.Dict):
   for key,value in zip(n.keys,n.values):
    if isinstance(key,ast.Constant) and key.value in ('campaign_progression','id13-air-relaunch.gba','campaign-stage-progression.gba'):
     if key.value=='campaign_progression':metadata.append(ast.literal_eval(value))
     lines.update(range(key.lineno-1,value.end_lineno))
 need(metadata==[META],'new metadata qualified and exact')
 inverse=b''.join(line for i,line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
 changes=[
  (b'"--output", id13_air,\r\n        "--manifest", output / "id13-air-relaunch.json"',
   b'"--output", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
  (b'"--after", id13_air,\r\n        "--manifest", output / "id13-air-relaunch.json"',
   b'"--after", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
  (FINAL.encode(),OLD.encode())]
 for old,new in SCOPE:changes.append(('"\r\n            "'.join(new).encode(),'"\r\n            "'.join(old).encode()))
 for new,old in changes:
  need(inverse.count(new)==1,'unique reviewed predecessor retarget or scope sentence');inverse=inverse.replace(new,old)
 need(sha(inverse)==OLD_MAIN,'complete B820→59F inverse; every earlier call/gate preserved')
 return expected


def inverse_rom(before,after,manifest,spans,changed):
 need(len(before)==len(after)==0x1000000,'complete16MiB layer')
 need(len(manifest['writes'])==len(spans) and {w['offset']:w['size'] for w in manifest['writes']}==spans,'independent exact write extents')
 restored=bytearray(after)
 for w in manifest['writes']:
  at,size=w['offset'],w['size']
  need(before[at:at+size]==bytes.fromhex(w['before_hex']) and after[at:at+size]==bytes.fromhex(w['after_hex']),'exact declared span bytes')
  restored[at:at+size]=before[at:at+size]
 need(restored==before and sum(a!=b for a,b in zip(before,after))==changed,'whole layer inverse and change count')


def preflight():
 raw=read(PRIOR);need(sha(raw)==PRIOR_SHA,'frozen completev79 audit');prior=json.loads(raw)
 need((prior['status'],prior['files_each'],prior['manifest_entries_each'],prior['final_sha256'])==
      ('ID13_TWO_BUILD_INVENTORY_PASS',328,126,OLD),'completed historical closure')
 pins={**prior['source_tool_sha256'],**PINS}
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'unchanged source '+path)
 expected=verify_main(read(ROOT/MAIN_PATH))
 isolated={'build/id13-air-relaunch-v79-20261117/component.gba':OLD,
  'build/id13-air-relaunch-v79-20261117/component.json':OLD_MANIFEST,
  'build/campaign-stage-progression-v80-20261117/component.gba':MID,
  'build/campaign-stage-progression-v80-20261117/component.json':MID_MANIFEST,
  'build/campaign-stage-progression-independent-v80-20261117/audit.json':GATE1,
  'build/campaign-stage-progression-v80-20261117-r2/component.gba':FINAL,
  'build/campaign-stage-progression-v80-20261117-r2/component.json':FINAL_MANIFEST,
  'build/campaign-stage-consumers-independent-v80-20261117-r2/audit.json':GATE2}
 blobs={p:read(ROOT/p) for p in isolated};need({p:sha(b) for p,b in blobs.items()}==isolated,'isolated components and gates')
 images=[b for p,b in blobs.items() if p.endswith('.gba')]
 manifests=[json.loads(b) for p,b in blobs.items() if p.endswith('/component.json')]
 inverse_rom(images[0],images[1],manifests[1],SPANS1,126);inverse_rom(images[1],images[2],manifests[2],SPANS2,297)
 need(sum(SPANS1.values())+sum(SPANS2.values())==453 and sum(a!=b for a,b in zip(images[0],images[2]))==423,'combined453/423 closure')
 report=dict(status='CAMPAIGN_MAIN_PREFLIGHT_PASS',main_sha256=MAIN,whole_main_inverse_sha256=OLD_MAIN,
  isolated_inputs=isolated,final_sha256=FINAL,predicted_files_each=334,predicted_manifest_entries_each=128,
  new_relative_paths=sorted(ADDED),new_calls=CALLS,independent_gate_sha256=[GATE1,GATE2],
  old_semantic_suites_rerun=False,full_build_executed_by_auditor=False,emulator_launched_by_auditor=False)
 return prior,pins,expected,report


def audit(args,prior,pins,expected,report):
 need(args.root_completed and args.build_a and args.build_b,'explicit root completion of both builds required')
 builds=[args.build_a.resolve(),args.build_b.resolve()];historical=[(ROOT/p).resolve() for p in prior['builds']]
 need(len(set(builds))==2 and not set(builds)&set(historical) and all(d.parent==ROOT/'build' for d in builds),'two distinct fresh workspace builds')
 old=prior['sha256_by_relative_path'];need(all(inventory(d)==old for d in historical),'all328 prior artifacts retained')
 actual=[inventory(d) for d in builds]
 need(actual[0]==actual[1] and len(actual[0])==334 and actual[0].keys()-old.keys()==ADDED and
      not old.keys()-actual[0].keys(),'identical334 maps and exactsix additions')
 changed=sorted(p for p in old if old[p]!=actual[0][p])
 need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'only three shared paths changed')
 for path,digest in ARTIFACTS.items():need(actual[0][path]==digest,'exact new/retained artifact '+path)
 old_manifest=json.loads(read(historical[0]/'build-manifest.json'));closures=[]
 for directory in builds:
  manifest=json.loads(read(directory/'build-manifest.json'))
  need(manifest.keys()-old_manifest.keys()=={'campaign_progression'} and not old_manifest.keys()-manifest.keys(),'one new metadata section')
  need(manifest['campaign_progression']==META,'qualified campaign claims')
  for key,value in old_manifest.items():
   if key=='layers':continue
   if key=='claim_scope':
    for old_parts,new_parts in SCOPE:
     old_text=''.join(old_parts);need(value.count(old_text)==1,'exact old scope text');value=value.replace(old_text,''.join(new_parts))
   need(manifest[key]==value,'retained metadata '+key)
  entries=[]
  for key,subdir,const in [('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),
   ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')]:
   need(manifest[key]==expected[const],'literal closure '+key)
   for name,digest in manifest[key].items():
    need(Path(name).name==name and sha(read(directory/subdir/name))==digest,'actual closure '+name)
    entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
  need(len(entries)==128,'all128 manifest entries');closures.append(entries)
  images=[read(directory/p) for p in ('id13-air-relaunch.gba','campaign-stage-progression.gba','current-candidate.gba')]
  inverse_rom(images[0],images[1],json.loads(read(directory/'campaign-stage-progression.json')),SPANS1,126)
  inverse_rom(images[1],images[2],json.loads(read(directory/'current-candidate.json')),SPANS2,297)
  need(sum(a!=b for a,b in zip(images[0],images[2]))==423,'combined exact423 changes')
 need([inventory(d) for d in builds]==actual and all(inventory(d)==old for d in historical),'fresh and historical inventories stable')
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'sources unchanged after audit '+path)
 report.update(status='CAMPAIGN_TWO_BUILD_INVENTORY_PASS',files_each=334,manifest_entries_each=128,
  builds=[d.relative_to(ROOT).as_posix() for d in builds],sha256_by_relative_path=actual[0],source_tool_sha256=pins,
  manifest_closures=closures,changed_shared_v79_paths=changed,baseline_audit_sha256=PRIOR_SHA,
  whole_new_layer_inverses=True,previous_328_artifacts_preserved=True)


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',action='store_true');p.add_argument('--root-completed',action='store_true')
 p.add_argument('--build-a',type=Path);p.add_argument('--build-b',type=Path);p.add_argument('--report',type=Path,required=True)
 args=p.parse_args();need(not args.report.exists(),'fresh report required');prior,pins,expected,result=preflight()
 if args.preflight:need(not args.root_completed and not args.build_a and not args.build_b,'preflight excludes fresh outputs')
 else:audit(args,prior,pins,expected,result)
 result['checker_sha256']=sha(read(Path(__file__)));args.report.parent.mkdir(parents=True,exist_ok=True)
 with args.report.open('x',encoding='utf-8',newline='\n') as output:json.dump(result,output,indent=2);output.write('\n')
 print(result['status'],sha(read(args.report)))
