"""Audit combined AI alignment/Iraira main wiring and complete fresh inventories.

No builders
are imported, no game is executed, and historical artifacts remain read-only.
"""
import argparse
import ast
import json
from pathlib import Path
import struct
from verify_id13_main_inventory import need, sha, read, inventory
ROOT=Path(__file__).resolve().parents[1]
MAIN_PATH='tools/build_current_candidate.py'
MAIN='CDE1B90D92035168C3AC11A77FF561BEE8DC4D4F5F8B6A552EA0FDBDD4174621'
OLD_MAIN='BADCCD5949EBBD04C8AF2DF4FAD20D8868DD492061F3079E0E16A80B08B948A6'
DEEE='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
ALIGN='E6B2C30E3E7D880BFFEE82A3201D0F69AE3DE0EBBEE5B523D24DD6D03FA08CF4'
FINAL='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
DEEE_MANIFEST='2645FA80910F747BEB4A07239645449536BCFA51652194D191749CF03DF063B3'
ALIGN_MANIFEST='4AFD13AEC814255B94F21D1C72D26EBF81A75E6F5FA7CC2FE89D028C48A2FA66'
MANIFEST='29D6854A21CEE021D0CE011A44783DA8B5CBFE902FF5489FBD87FE50AD01D900'
PRIOR=ROOT/'build/character-ai-main-inventory-20261117/final.json'
PRIOR_SHA='83C5AF9A71EFBE9771C318690E7C75AAF422EF232D55B35D0CDE0528C7896855'
SOURCE=Path.home()/'Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc'
SOURCE_SHA='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ALIGN_GATE='34CB670213FC84344BB76C6052E812DEAB079DC78F85AC46211D8DC389677664'
IRAIRA_GATE='0112FDCC4B6EB2A64DB67A22CB57583847840FEC6A96DA11ACB91614702DABCC'
PINS={
 'tools/build_character_ai_parameter_alignment.py':'1AF860301B07DB64520520802D1F88F2184565ACA6430692E0C574C23F6DEEBD',
 'tools/verify_character_ai_parameter_alignment.py':'526263526AFDDFEFA6A386B930149FF22A3035F0F3D8172089533D5B9AAC3EEC',
 'tools/verify_iraira_render_consumers.py':'E86C60BF7EF9C390A995BEFBF8A8E014D6F9D15437541C26ADCFC04918B54263',
 'tools/verify_character_ai_main_inventory.py':'C3E6A9AD45CAF7328A4D3025EE6F056CB3AA80D382D4FF62918822E77F07E579',
 'tools/build_iraira_render_repair.py':'4F66E1DD37B5A78099583816D74DCEEC9D91019BA4AC05BFBC7BB0D02AF95105',
}
ARTIFACTS={
 'intermediate/ai-parameter-alignment-verification.json':ALIGN_GATE,
 'intermediate/iraira-render-verification.json':IRAIRA_GATE,
 'character-ai-tables.gba':DEEE,'character-ai-tables.json':DEEE_MANIFEST,
 'character-ai-parameter-alignment.gba':ALIGN,'character-ai-parameter-alignment.json':ALIGN_MANIFEST,
 'current-candidate.gba':FINAL,'current-candidate.json':MANIFEST,
}
VARIABLES={'character_ai':"output / 'character-ai-tables.gba'",'ai_aligned':"output / 'character-ai-parameter-alignment.gba'",
 'alignment_review':"intermediate / 'ai-parameter-alignment-verification.json'",'iraira_review':"intermediate / 'iraira-render-verification.json'"}
CALLS={
 'build_character_ai_parameter_alignment.py':["'--before'",'character_ai',"'--source'",'args.wsc15',"'--owner'","output / 'character-ai-tables.json'","'--output'",'ai_aligned',"'--manifest'","output / 'character-ai-parameter-alignment.json'"],
 'build_iraira_render_repair.py':["'--before'",'ai_aligned',"'--source'",'args.wsc15',"'--alignment-owner'","output / 'character-ai-parameter-alignment.json'","'--output'",'candidate',"'--manifest'","output / 'current-candidate.json'"],
 'verify_character_ai_parameter_alignment.py':["'--before'",'character_ai',"'--after'",'ai_aligned',"'--source'",'args.wsc15',"'--owner'","output / 'character-ai-tables.json'","'--report'",'alignment_review'],
 'verify_iraira_render_consumers.py':["'--before'",'ai_aligned',"'--after'",'candidate',"'--source'",'args.wsc15',"'--manifest'","output / 'current-candidate.json'","'--alignment-owner'","output / 'character-ai-parameter-alignment.json'","'--report'",'iraira_review'],
}
GATES={'alignment_review':ALIGN_GATE,'iraira_review':IRAIRA_GATE}
META={
 'ai_parameter_alignment':{'verification_sha256':ALIGN_GATE,'source_bytes_per_row':17,'native_bytes_per_row':18,'rows':10,'declared_bytes':244,'changed_bytes':196,'new_RAM_bytes':0,'restores_source_halfwords_on_odd_rows':True,'supersedes_flat_read_model_for_parameter_loads':True,'actual_runtime_verified':False,'final_port_complete':False},
 'iraira_render':{'verification_sha256':IRAIRA_GATE,'source_tiles':512,'source_maps':8,'initial_palette_colors':111,'animated_palette_colors':38,'palette_counters':5,'declared_bytes':25382,'changed_bytes':23155,'new_RAM_bytes':0,'actual_runtime_verified':False,'final_port_complete':False},
}
ISOLATED={
 'build/ai-parameter-alignment-independent-20261117/report.json':ALIGN_GATE,
 'build/iraira-render-independent-20261117/report.json':IRAIRA_GATE,
 'build/ai-parameter-alignment-v83-20261117/component.gba':ALIGN,
 'build/ai-parameter-alignment-v83-20261117/component.json':ALIGN_MANIFEST,
 'build/iraira-render-repair-v84-20261117/component.gba':FINAL,
 'build/iraira-render-repair-v84-20261117/component.json':MANIFEST,
}
PARAM_REFS=(0xC7140,0xC714C,0xC7154,0xC715C,0xC7164,0xC716C,0xC7174,
 0xC717C,0xC7184,0xC718C,0xC7194,0xC719C,0xC71A4,0xC71AC,0xC71B4)
ALIGN_SPANS={0xD8AB00:180,0xC6D6C:4,**{a:4 for a in PARAM_REFS}}
IRAIRA_SPANS={0xD8AC00:140,0xD8AD00:380,0xD8AF00:52,0xD8AF40:52,0xD8AF80:32,
 0x582544:4,0x582548:4,0x58254C:4,0x582554:4,0x582560:4,
 0x582564:4,0x582568:4,0x582570:4,0x58257C:4,0x583C00:4,
 0xC4BC0:4,0xC4CC4:4,0x582528:4,0x583B28:4,
 0x598000:222,0x598100:16384,0x59C100:8064}

def inverse(before,after,manifest,spans,old,new,declared,changed):
 need(sha(before)==old and sha(after)==new and len(before)==len(after)==0x1000000,'whole pinned ROM layer')
 need({w['offset']:w['size'] for w in manifest['writes']}==spans and len(manifest['writes'])==len(spans),'complete exact write spans')
 restored=bytearray(after)
 for w in manifest['writes']:
  a,z=w['offset'],w['offset']+w['size']
  if 'before_hex' in w:
   need(before[a:z]==bytes.fromhex(w['before_hex']) and after[a:z]==bytes.fromhex(w['after_hex']),'exact declared bytes')
  else:
   need(sha(before[a:z])==w['before_sha256'] and sha(after[a:z])==w['after_sha256'],'exact declared byte hashes')
  restored[a:z]=before[a:z]
 need(bytes(restored)==before and sum(spans.values())==declared and sum(x!=y for x,y in zip(before,after))==changed,'whole inverse and all byte counts')

def source_layers(deee,aligned,final,am,im):
 source=read(SOURCE);need(sha(source)==SOURCE_SHA,'original source identity')
 inverse(deee,aligned,am,ALIGN_SPANS,DEEE,ALIGN,244,196)
 expected=bytearray(deee)
 for i in range(10):expected[0xD8AB00+i*18:0xD8AB00+(i+1)*18]=source[0x782970+i*17:0x782970+(i+1)*17]+b'\0'
 expected[0xC6D6C:0xC6D70]=bytes.fromhex('1210a0e3')
 for at in PARAM_REFS:expected[at:at+4]=struct.pack('<I',0x08D8AB00)
 need(bytes(expected)==aligned,'independent entire aligned image reconstructed from170source bytes and native18stride')
 inverse(aligned,final,im,IRAIRA_SPANS,ALIGN,FINAL,25382,23155)
 def color(v):return sum((2*((v>>s)&15)+(1 if (v>>s)&15 else 0))<<d for s,d in ((8,0),(4,5),(0,10)))
 palette=struct.pack('<111H',*(color(struct.unpack_from('<H',source,0x4C60E2+i*2)[0]) for i in range(111)))
 need(final[0x598000:0x5980DE]==palette,'111 correctly addressed source palette colors')
 for i in range(512):
  planar=source[0x4C61C0+i*32:0x4C61C0+(i+1)*32];packed=final[0x598100+i*32:0x598100+(i+1)*32]
  for y in range(8):
   for x in range(8):
    src=sum(((planar[y*4+p]>>(7-x))&1)<<p for p in range(4))
    need(src==(packed[y*4+x//2]>>(4*(x%2)))&15,'32768 source tile pixels')
 for i in range(4032):
  v=struct.unpack_from('<H',source,0x4CA1C0+i*2)[0]
  converted=(v&511)|((v&8192)>>4)|((v&0xC000)>>4)|((v&0x1E00)<<3)
  need(struct.unpack_from('<H',final,0x59C100+i*2)[0]==converted,'4032 source map cell translations')
 need(all(not max(a,c)<min(a+n,c+m) for a,n in ALIGN_SPANS.items() for c,m in IRAIRA_SPANS.items()),'both layer writes disjoint')
 return dict(alignment_spans=17,alignment_bytes=244,iraira_spans=22,iraira_bytes=25382,source_tile_pixels=32768,source_map_cells=4032,source_palette_colors=111)

def verify_main(raw):
 need(sha(raw)==MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n',b''),'frozen CRLF main')
 tree=ast.parse(raw)
 expected={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id.startswith('EXPECTED_')}
 need(all(expected['EXPECTED_LAYERS'][name]==value for name,value in (('character-ai-tables.gba',DEEE),('character-ai-parameter-alignment.gba',ALIGN),('current-candidate.gba',FINAL))),'all three explicit layer identities')
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
    if isinstance(key,ast.Constant) and key.value in (*META,'character-ai-tables.gba','character-ai-parameter-alignment.gba'):
     if key.value in META:
      need(key.value not in metadata,'unique metadata');metadata[key.value]=ast.literal_eval(value)
     lines.update(range(key.lineno-1,value.end_lineno))
 need(metadata==META,'exact bounded metadata for both layers')
 inverse=b''.join(line for i,line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
 changes=[(b'"--output", character_ai, "--manifest", output / "character-ai-tables.json")',b'"--output", candidate, "--manifest", output / "current-candidate.json")'),
  (b'run("verify_character_ai_tables.py", "--before", character_type8, "--after", character_ai,',b'run("verify_character_ai_tables.py", "--before", character_type8, "--after", candidate,'),
  (FINAL.encode(),DEEE.encode())]
 for new,old in changes:
  need(inverse.count(new)==1,'unique previous-layer retarget');inverse=inverse.replace(new,old)
 need(sha(inverse)==OLD_MAIN,'whole main inverse to BADCCD; every earlier call, gate and metadata retained')
 return expected

def preflight():
 raw=read(PRIOR);need(sha(raw)==PRIOR_SHA,'frozen completed v82 inventory')
 prior=json.loads(raw)
 need((prior['status'],prior['files_each'],prior['manifest_entries_each'],prior['final_sha256'])==('CHARACTER_AI_TWO_BUILD_INVENTORY_PASS',340,130,DEEE),'historical closure')
 pins={**prior['source_tool_sha256'],**PINS,MAIN_PATH:MAIN}
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'frozen source '+path)
 expected=verify_main(read(ROOT/MAIN_PATH))
 isolated={**prior['isolated_inputs'],**ISOLATED}
 for path,digest in isolated.items():need(sha(read(ROOT/path))==digest,'frozen isolated '+path)
 proofs=source_layers(read(ROOT/'build/character-ai-tables-v82-20261117/component.gba'),read(ROOT/'build/ai-parameter-alignment-v83-20261117/component.gba'),read(ROOT/'build/iraira-render-repair-v84-20261117/component.gba'),json.loads(read(ROOT/'build/ai-parameter-alignment-v83-20261117/component.json')),json.loads(read(ROOT/'build/iraira-render-repair-v84-20261117/component.json')))
 for path in prior['builds']:need(inventory(ROOT/path)==prior['sha256_by_relative_path'],'all340 historical files unchanged')
 report=dict(status='AI_IRAIRA_MAIN_PREFLIGHT_PASS',main_sha256=MAIN,whole_main_inverse_sha256=OLD_MAIN,isolated_inputs=isolated,final_sha256=FINAL,predicted_files_each=346,predicted_manifest_entries_each=132,new_calls=CALLS,independent_gates=GATES,component_proofs=proofs,old_semantic_suites_rerun=False,full_build_executed_by_auditor=False,emulator_launched_by_auditor=False)
 return prior,pins,expected,report

def audit(args,prior,pins,expected,report):
 need(args.root_completed and args.build_a and args.build_b,'root original completion of both full builds required')
 builds=[args.build_a.resolve(),args.build_b.resolve()];historical=[(ROOT/p).resolve() for p in prior['builds']]
 need(len(set(builds))==2 and not set(builds)&set(historical) and all(d.parent==ROOT/'build' for d in builds),'distinct fresh workspace builds')
 old=prior['sha256_by_relative_path'];actual=[inventory(d) for d in builds]
 added=set(ARTIFACTS)-{'current-candidate.gba','current-candidate.json'}
 need(len(added)==6 and actual[0]==actual[1] and len(actual[0])==346 and actual[0].keys()-old.keys()==added and not old.keys()-actual[0].keys(),'346 identical files and exactly six additions')
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
  need(len(entries)==132,'complete132 manifest entries');closures.append(entries)
  source_layers(read(directory/'character-ai-tables.gba'),read(directory/'character-ai-parameter-alignment.gba'),read(directory/'current-candidate.gba'),json.loads(read(directory/'character-ai-parameter-alignment.json')),json.loads(read(directory/'current-candidate.json')))
 need([inventory(d) for d in builds]==actual and all(inventory(d)==old for d in historical),'fresh and historical inventories unchanged after audit')
 for path,digest in pins.items():need(sha(read(ROOT/path))==digest,'all sources unchanged after audit')
 report.update(status='AI_IRAIRA_TWO_BUILD_INVENTORY_PASS',files_each=346,manifest_entries_each=132,builds=[d.relative_to(ROOT).as_posix() for d in builds],sha256_by_relative_path=actual[0],source_tool_sha256=pins,manifest_closures=closures,changed_shared_v82_paths=changed,baseline_audit_sha256=PRIOR_SHA,whole_new_layers_inverse=True,previous_340_artifacts_preserved=True)

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
