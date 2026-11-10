"""Narrow v76 display-epoch wiring and inverse preflight; no build/capture."""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import verify_result_language_capture as runtime
from verify_result_v74_integration import need,sha,read,audit_prefix
from verify_shoot_terminal_display_epoch_production import inverse,INPUT,OUTPUT

ROOT=Path(__file__).resolve().parents[1]
MAIN='DE4B99720523A7B1FA4D4CD68C06F251A8B7C26C97167294C9195991BC0235C0'
RUNTIME='665AE76FDFCCF1806FE060C137E2E591FF3B6510CC601F148EEB35FFABE3D328'
OLD_RUNTIME='C31719BAE4C6D1BBD6B92A6BA8C0AB04C1494339EEEDF6D0D61435CBD4279A67'
HOST='43210C82D6EE6D0D6334E26EC37AB9C4762970420D65565F8AE8BE8A3D12DA64'
OLD_HOST='B006A842802BF90241538D9CCE744F75ED58889E2B14468745183C065B97120F'
REPORT='AFC67C96B20744286BEC58BA05313808A7CE22D3788E05E6B2385874A8ADCE65'

def check():
    mainraw=read(ROOT/'tools/build_current_candidate.py');raw=read(ROOT/'tools/verify_result_language_capture.py')
    host=read(ROOT/'build/run_result_v76_20261110.py');oldhost=read(ROOT/'build/run_result_v75_20261110.py')
    need(tuple(map(sha,(mainraw,raw,host,oldhost)))==(MAIN,RUNTIME,HOST,OLD_HOST),'frozen identities')
    need(sha(read(ROOT/'tools/verify_result_v74_integration.py'))=='67C68ECED8B42BC0736F8A04EAECE3C4163F757901CFF08052EB7E62A860FB68','reused pre-capture helper')
    need(sha(read(ROOT/'tools/verify_shoot_terminal_display_epoch_production.py'))=='E82C9F1A7EBC199DB13647776F93041AEA9F5A4600AA48491E5D696C185EE974','pure gate source')
    function=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='audit')
    added=function.body[1];need(isinstance(added,ast.If),'leading display inverse branch')
    removed=set(range(added.lineno-1,added.end_lineno))
    previous=b''.join(line for i,line in enumerate(raw.splitlines(keepends=True)) if i not in removed)
    need(len(removed)==9 and sha(previous)==OLD_RUNTIME,'only nine added lines; complete C317 unchanged')
    need(host==oldhost.replace(b'v75-20261110',b'v76-20261110').replace(INPUT.encode(),OUTPUT.encode()),'ordinary host version/ROM-only delta')
    ast.parse(host)
    tree=ast.parse(mainraw);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    env=dict(output=Path('FRESH'),intermediate=Path('FRESH/intermediate'),args=SimpleNamespace(wsc15=Path('ORIGINAL.wsc')))
    paths={'shoot_palette_calls':'shoot-palette-calls.gba','shoot_owner_link':'shoot-owner-link.gba','candidate':'current-candidate.gba',
           'owner_link_review':'shoot-owner-link-verification.json','display_epoch_review':'shoot-display-epoch-verification.json'}
    for name,path in paths.items():
        parent='intermediate' if name.endswith('_review') else 'output'
        nodes=[n for n in main.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)]
        need(len(nodes)==1 and ast.unparse(nodes[0].value)==f"{parent} / '{path}'",'fresh path '+name)
        env[name]=env[parent]/path
    p,o,c,w=env['shoot_palette_calls'],env['shoot_owner_link'],env['candidate'],env['args'].wsc15
    expected={
        'build_shoot_terminal_owner_link.py':[p,w,o,'--manifest',Path('FRESH/shoot-owner-link.json')],
        'build_shoot_terminal_display_epoch.py':[o,w,c,'--manifest',Path('FRESH/current-candidate.json')],
        'verify_shoot_terminal_owner_link_production.py':['--before',p,'--after',o,'--source',w,'--manifest',Path('FRESH/shoot-owner-link.json'),'--report',env['owner_link_review']],
        'verify_shoot_terminal_display_epoch_production.py':['--before',o,'--after',c,'--source',w,'--manifest',Path('FRESH/current-candidate.json'),'--report',env['display_epoch_review']]}
    calls={};pins={}
    for n in ast.walk(main):
        if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Name) or not n.args:continue
        if n.func.id=='run' and isinstance(n.args[0],ast.Constant) and n.args[0].value in expected:
            key=n.args[0].value;need(key not in calls,'unique caller')
            calls[key]=[eval(compile(ast.Expression(a),'caller','eval'),{'__builtins__':{}},env) for a in n.args[1:]]
        if n.func.id=='require_hash' and isinstance(n.args[0],ast.Name) and n.args[0].id in ('owner_link_review','display_epoch_review'):
            key=n.args[0].id;need(key not in pins,'unique report pin');pins[key]=ast.literal_eval(n.args[1])
    need(calls==expected and pins==dict(owner_link_review='8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3',display_epoch_review=REPORT),'exact affected fresh calls/pins')
    layers=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED_LAYERS' for t in n.targets)))
    need(layers['shoot-owner-link.gba']==INPUT and layers['current-candidate.gba']==OUTPUT,'new preserved/final layer bindings')
    claims=[]
    for n in ast.walk(tree):
        if isinstance(n,ast.Dict):
            for k,v in zip(n.keys,n.values):
                if isinstance(k,ast.Constant) and k.value=='shoot_terminal_display_epoch':claims.append(ast.literal_eval(v))
    expected_claim=dict(verification_sha256=REPORT,declared_bytes=84,changed_bytes=69,new_RAM_bytes=0,additional_stack_bytes=0,
                        consumption_entry='086FF720',planned_mapping_checked=True,live_display_fields_rechecked=True,
                        earliest_compare_runtime_verified=False,final_port_complete=False)
    need(claims==[expected_claim],'accurate bounded metadata, earliest runtime deadline remains unverified')
    before=read(ROOT/'build/shoot-terminal-owner-link-20261109/component.gba');after=read(ROOT/'build/shoot-terminal-display-epoch-20261110/component.gba')
    need((sha(before),sha(after))==(INPUT,OUTPUT),'component identities');inverse(before,after)
    changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b];need(len(changed)==69,'actual69-byte difference')
    retail=read(Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba'));observer=read(ROOT/'tools/bizhawk_probe_result_languages.lua')
    for rom in (before,after):audit_prefix(runtime.audit,rom,retail,observer,True)
    rejected=[]
    for start,size in ((0x6FF6E8,4),(0x6FF720,72),(0x6FFDE8,4),(0x6FFDEC,4)):
        for at in (start-1,start,start+size-1,start+size):
            bad=bytearray(after);bad[at]^=1;audit_prefix(runtime.audit,bytes(bad),retail,observer,False);rejected.append(at)
    audit_prefix(runtime.audit,after+b'\xff',retail,observer,False)
    controls=[]
    for old,new in ((b"bytes.fromhex('449FFBEB')",b"bytes.fromhex('0C0000EB')"),
                    (b"b'\\xff' * 72",b"b'\\xff' * 71"),
                    (b"bytes.fromhex('CCDF0000')",b"bytes.fromhex('CC000000')"),
                    (b"bytes.fromhex('001E0000')",b"bytes.fromhex('00000000')")):
        need(raw.count(old)==1,'unique inverse mutation')
        scope={'__file__':str(ROOT/'tools/verify_result_language_capture.py'),'__name__':'v76_control'}
        exec(compile(raw.replace(old,new),'inverse-control','exec'),scope)
        audit_prefix(scope['audit'],after,retail,observer,False);controls.append(old.decode())
    return dict(status='PASS_V76_MAIN_INVERSE_HOST_PREFLIGHT',main_sha256=MAIN,runtime_sha256=RUNTIME,host_sha256=HOST,
        reconstructed_prior_runtime_sha256=sha(previous),new_inverse_lines=9,host_delta_only=['v75→v76','46B3→280D'],
        fresh_affected_callers={k:list(map(str,v)) for k,v in calls.items()},report_pins=pins,new_layer_claim=expected_claim,
        whole_display_layer_inverse=True,declared_bytes=84,changed_bytes=69,changed_offsets=changed,
        actual_audit_pre_capture_positives=2,corruptions_rejected_before_capture_IO=rejected+['length'],semantic_inverse_controls=controls,
        capture_files_opened=0,full_build_executed=False,emulator_launched=False,old_semantic_suites_rerun=False,
        checker_sha256=sha(read(Path(__file__))),qualification='Integration only; fresh inventories and actual runtime audit remain separate; earliest counter deadline and final port remain open.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    need(not a.report.exists(),'fresh report');r=check();a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode());print(r['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
