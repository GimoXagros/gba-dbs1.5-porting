#!/usr/bin/env python3
"""Narrow v74 main/inverse/host preflight; no full build or capture I/O."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import verify_result_language_capture as runtime

ROOT=Path(__file__).resolve().parents[1]
MAIN='1090E51AE1CA2C6EC4B2C13A2F05D5D271DBBDB250B149D716B0F6FE691B3AA3'
RUNTIME='DFDD17521A0B728EE4ED1B511EF606D736DD61269B87EFC9AF2CFBD22CE42025'
OLD='989EA9640E4CB7AF35F73A9FAC6BFC73093EEF92F31CBB4BB8CDA9BC517235FE'
HOST='58D9E9EBE7ECF4823DAC35DC7EE4EE5146301AF963E9D4E4C84937D178E2AAD5'
OLDHOST='B0DED582D07658950E0E8F27B0EC048E54074E09E11E40C2BEB30EB0AA2C1FCA'
FATAL='6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7'
SCENE='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
FINAL='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
SCENE_QA='37812C30D6A1EA005F48CB1E3298D38FBCD795008A614CEEA9339679B16B75B8'
RECT_QA='BAD282D7F5AEAC391022D3A3C350C4257A6BC15A901406EC29F875CEDFB4DACA'

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def read(path):
    need(path.suffix.lower()not in('.sav','.state'),'no save/state input')
    return path.read_bytes()

class CaptureBlocked(Exception):pass

def audit_prefix(fn,data,retail,observer,positive):
    calls=[]
    def blocked(path):calls.append(path.name);raise CaptureBlocked()
    globals_=fn.__globals__;oldread=globals_['read'];globals_['read']=blocked
    try:
        try:fn(Path('CAPTURE_IO_MUST_NOT_OPEN'),data,retail,observer)
        except CaptureBlocked:need(positive and calls==['launch.json'],'valid ROM reaches first capture read')
        except ValueError:need(not positive and calls==[],'invalid ROM rejected before capture read')
        else:raise ValueError('audit returned without required capture')
    finally:globals_['read']=oldread

def main_calls(tree):
    paths={'shoot_fatal':'shoot-fatal-callback.gba','shoot_native_scene':'shoot-native-scene.gba','candidate':'current-candidate.gba'}
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    for name,path in paths.items():
        node=next(n for n in main.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in n.targets))
        need(ast.unparse(node.value)==f"output / '{path}'",'fresh layer path '+name)
    env=dict(output=Path('FRESH'),intermediate=Path('FRESH/intermediate'),
        shoot_guarded_transition=Path('FRESH/shoot-guarded-transition.gba'),
        args=SimpleNamespace(gba=Path('ORIGINAL.gba'),wsc15=Path('ORIGINAL.wsc')))
    env.update({name:Path('FRESH')/path for name,path in paths.items()})
    for name,path in (('fatal_review','shoot-fatal-callback-verification.json'),('scene_review','shoot-native-scene-verification.json'),('rectangle_review','shoot-child-rectangle-verification.json')):
        env[name]=Path('FRESH/intermediate')/path
    selected={
      'build_shoot_fatal_callback_route.py','build_shoot_native_scene_connection.py','build_shoot_child_attack_rectangle.py',
      'verify_shoot_fatal_callback_route.py','verify_shoot_native_scene_connection.py','verify_shoot_child_attack_rectangle_production.py'}
    calls={}
    for node in ast.walk(main):
        if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='run'and node.args and isinstance(node.args[0],ast.Constant)and node.args[0].value in selected:
            key=node.args[0].value;need(key not in calls,'one production caller per layer')
            calls[key]=[eval(compile(ast.Expression(a),'main call','eval'),{'__builtins__':{}},env)for a in node.args[1:]]
    need(set(calls)==selected,'all six affected builder/verifier callers')
    f,s,c=(env[x]for x in ('shoot_fatal','shoot_native_scene','candidate'));g,w=env['args'].gba,env['args'].wsc15
    expected={
      'build_shoot_fatal_callback_route.py':[env['shoot_guarded_transition'],g,w,f,'--manifest',Path('FRESH/shoot-fatal-callback.json')],
      'build_shoot_native_scene_connection.py':[f,g,w,s,'--manifest',Path('FRESH/shoot-native-scene.json')],
      'build_shoot_child_attack_rectangle.py':[s,g,w,c,'--manifest',Path('FRESH/current-candidate.json')],
      'verify_shoot_fatal_callback_route.py':[f,env['shoot_guarded_transition'],g,w,'--manifest',Path('FRESH/shoot-fatal-callback.json'),'--output',env['fatal_review']],
      'verify_shoot_native_scene_connection.py':['--before',f,'--after',s,'--gba',g,'--source',w,'--manifest',Path('FRESH/shoot-native-scene.json'),'--report',env['scene_review']],
      'verify_shoot_child_attack_rectangle_production.py':['--before',s,'--after',c,'--gba',g,'--source',w,'--manifest',Path('FRESH/current-candidate.json'),'--report',env['rectangle_review']]}
    need(calls==expected,'exact fresh production argument/manifest chain')
    pins={}
    for n in ast.walk(main):
        if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='require_hash'and n.args and isinstance(n.args[0],ast.Name)and n.args[0].id in('fatal_review','scene_review','rectangle_review'):
            pins[n.args[0].id]=ast.literal_eval(n.args[1])
    need(pins==dict(fatal_review='61656691CD4126193003FB2E43B851F3CAA57A8C6C78A147ED602B181F2F2FD4',scene_review=SCENE_QA,rectangle_review=RECT_QA),'all affected report hash pins')
    return {name:[str(x)for x in values]for name,values in calls.items()}

def check():
    mainraw=read(ROOT/'tools/build_current_candidate.py');raw=read(ROOT/'tools/verify_result_language_capture.py')
    host=read(ROOT/'build/run_result_v74_20261109.py');oldhost=read(ROOT/'build/run_result_v73_20261109.py')
    need(tuple(map(sha,(mainraw,raw,host,oldhost)))==(MAIN,RUNTIME,HOST,OLDHOST),'frozen main/runtime/host identities')
    tree=ast.parse(raw);function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
    new_cases=function.body[1:3];need(all(isinstance(n,ast.If)for n in new_cases),'only first two inverse cases')
    removed={i for n in new_cases for i in range(n.lineno-1,n.end_lineno)}
    previous=b''.join(line for i,line in enumerate(raw.splitlines(keepends=True))if i not in removed)
    need(sha(previous)==OLD,'every byte of frozen989E runtime retained after removing two new cases')
    need(host==oldhost.replace(b'v73',b'v74').replace(FATAL.encode(),FINAL.encode()),'host exact names/ROM delta only')
    ast.parse(host)
    need(all(token in host for token in (b"cfg['SoundEnabled'] = False",b"cfg['SoundOutputMethod'] = 3",b"cfg['AutoLoadLastSaveSlot'] = False",b"cfg['AutosaveSaveRAM'] = False",b'PrivateDesktopProcess',b"guest_writes=[]",b"physical_background_input=False")),'retained private host configuration')
    main_tree=ast.parse(mainraw);calls=main_calls(main_tree)
    layers=ast.literal_eval(next(n.value for n in main_tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='EXPECTED_LAYERS'for t in n.targets)))
    need({k:layers[k]for k in ('shoot-fatal-callback.gba','shoot-native-scene.gba','current-candidate.gba')}==
         {'shoot-fatal-callback.gba':FATAL,'shoot-native-scene.gba':SCENE,'current-candidate.gba':FINAL},'layer identities')
    # Literal manifest claims may contain dynamic unrelated fields. Inspect only
    # the changed layer dictionaries, without importing/executing the builder.
    dictionaries={}
    for n in ast.walk(main_tree):
        if isinstance(n,ast.Dict):
            for key,value in zip(n.keys,n.values):
                if isinstance(key,ast.Constant)and key.value in('shoot_native_scene_connection','shoot_child_command_rectangles','shoot_fatal_callback_route','resident_scene'):
                    dictionaries[key.value]=ast.literal_eval(value)
    need(dictionaries['shoot_native_scene_connection']['external_scene_route_installed']is True and
         dictionaries['shoot_native_scene_connection']['nonfatal_hook_installed']is True and
         dictionaries['shoot_native_scene_connection']['final_port_complete']is False,'accurate installed scene/limits')
    need(dictionaries['shoot_fatal_callback_route']['external_scene_route_installed_by_this_layer']is False and
         dictionaries['shoot_fatal_callback_route']['historical_E5_cause_resolved']is False and
         dictionaries['shoot_child_command_rectangles']['historical_E5_cause_resolved']is False and
         dictionaries['resident_scene']['external_route_installed']is True,'historical/final layer claims distinguished')
    need(all(t in mainraw for t in (b'UNRESOLVED_OBSERVER',b'general terminal ',b'interrupted-DI and moving-player camera domains remain unfulfilled')),'retained unresolved scope')
    need(all(t in mainraw for t in (b'at that historical layer the phase assigns upper entry 7792 internally without an external caller',
        b'at that historical layer this second player phase awaited complete initialization',
        b'had no external caller at that historical layer')),'three historical reachability claims qualified')
    paths=('build/shoot-child-attack-rectangle-20261109/component.gba','build/shoot-native-scene-connection-20261109/component.gba','build/shoot-fatal-callback-route-20261109/component.gba')
    final,scene,fatal=(read(ROOT/p)for p in paths)
    need(tuple(map(sha,(final,scene,fatal)))==(FINAL,SCENE,FATAL),'actual approved component inputs')
    restored=bytearray(final)
    for at in range(0x5B90A4,0x5B9115,16):restored[at:at+4]=bytes.fromhex('38043508')
    restored[0x5B9180:0x5B918A]=b'\xff'*10
    need(bytes(restored)==scene,'actual full child inverse')
    for at,he in ((0x33FD04,'A8809FE5'),(0x5C9108,'141094E5'),(0x5C910C,'F403D1E1'),(0x5C9120,'F633D1E1'),
        (0x5C9174,'F403D1E1'),(0x5C91A4,'F603D1E1'),(0x373ED8,'070059E3'),(0x36E634,'5C809FE5')):
        restored[at:at+4]=bytes.fromhex(he)
    restored[0x6FF380:0x6FF3E8]=b'\xff'*104;restored[0x6FF400:0x6FF410]=b'\xff'*16
    need(bytes(restored)==fatal,'actual full scene inverse into existing6A')
    retail=read(Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba'))
    observer=read(ROOT/'tools/bizhawk_probe_result_languages.lua')
    for rom in (final,scene,fatal):audit_prefix(runtime.audit,rom,retail,observer,True)
    negatives=[]
    sites=list(range(0x5B90A4,0x5B9115,16))+[0x5B9180,0x33FD04,0x6FF380,0x5C9108,0x5C910C,0x5C9120,0x5C9174,0x5C91A4,0x373ED8,0x6FF400,0x36E634,
        0x5B918A,0x5B9178,0x6FF3E8,0x6FF410,0x36E5EC,0xD0BE8,0x6FF720,0x7FFFFF]
    for at in sites:
        bad=bytearray(final);bad[at]^=1;audit_prefix(runtime.audit,bytes(bad),retail,observer,False);negatives.append(hex(at))
    audit_prefix(runtime.audit,final+b'\xff',retail,observer,False);negatives.append('length')
    semantic_controls=[]
    for old,new in ((b'0x5B9115',b'0x5B9105'),(b"restored[0x5B9180:0x5B918A] = b'\\xff' * 10",b"restored[0x5B9180:0x5B918A] = b'\\xff' * 9"),
        (b"restored[0x5C9174:0x5C9178] = bytes.fromhex('F403D1E1')",b"restored[0x5C9174:0x5C9178] = bytes.fromhex('F403D6E1')")):
        need(raw.count(old)==1,'unique new inverse mutation anchor')
        namespace={'__name__':'inverse_delta_control','__file__':str(ROOT/'tools/verify_result_language_capture.py')}
        exec(compile(raw.replace(old,new),'inverse delta mutation','exec'),namespace)
        audit_prefix(namespace['audit'],final,retail,observer,False);semantic_controls.append(old.decode())
    return dict(status='PASS_V74_MAIN_INVERSE_HOST_PREFLIGHT',main_sha256=MAIN,runtime_sha256=RUNTIME,host_sha256=HOST,
        reconstructed_unchanged_prior_runtime_sha256=sha(previous),removed_new_inverse_lines=len(removed),host_delta_only=['v73 names→v74','6A ROM→1477'],
        fresh_affected_callers=calls,main_layer_claims=dictionaries,whole_child_and_scene_inverses=True,
        actual_audit_pre_capture_positives=3,corruptions_rejected_before_capture_IO=negatives,semantic_inverse_controls=semantic_controls,
        capture_files_opened=0,full_build_executed=False,emulator_launched=False,old_semantic_suites_rerun=False,
        component_report_pins=[SCENE_QA,RECT_QA],checker_sha256=sha(read(Path(__file__))),
        qualification='Narrow changed wiring/inverse/private-host delta only. FreshA/B build reproducibility and actual runtime acceptance remain separate root-owned gates; historical E5/full-port limits retained.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    need(not a.report.exists(),'fresh report');result=check()
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
