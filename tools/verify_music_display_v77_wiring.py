"""Narrow v77 main/runtime/host inverse preflight; no build or capture access."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import types

import verify_result_language_capture as runtime

ROOT=Path(__file__).resolve().parents[1]
MAIN='57945F1D28BC4BB7C4674E2AECEC874CDE461CC9DEADCC59E9BBE6743FB81D7C'
RUNTIME='3E717B33E0225DBDF813400AED20F39222CA503718BDCFD8C856AA4B5A5AE7AF'
HOST='62868550FD49522EDE1ED0F8C5D6C032E830061B9BC14D43005F217ADD4ADC15'
FINAL='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
DISPLAY='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
WRAPPER='5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF'
BASE='928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
sha=lambda b:hashlib.sha256(b).hexdigest().upper()


def need(ok,label):
    if not ok:raise ValueError(label)


def without_nodes(raw,nodes):
    removed={i for n in nodes for i in range(n.lineno-1,n.end_lineno)}
    return b''.join(row for i,row in enumerate(raw.splitlines(keepends=True)) if i not in removed)


def check_main(raw):
    tree=ast.parse(raw);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    added_tools={'build_wsc_evolution_music.py','build_evolution_music_integration.py','verify_wsc_evolution_music_author.py','verify_evolution_music_display_composition.py'}
    added_vars={'shoot_display_epoch','evolution_music','music_author_review','music_integration_review'}
    remove=[];calls={};pins={}
    for n in main.body:
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in added_vars for t in n.targets):remove.append(n)
        if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name):
            c=n.value
            if c.func.id=='run'and isinstance(c.args[0],ast.Constant)and c.args[0].value in added_tools:
                need(c.args[0].value not in calls,'one new call per layer');calls[c.args[0].value]=[ast.unparse(x) for x in c.args[1:]];remove.append(n)
            if c.func.id=='require_hash'and isinstance(c.args[0],ast.Name)and c.args[0].id in ('music_author_review','music_integration_review'):
                pins[c.args[0].id]=ast.literal_eval(c.args[1]);remove.append(n)
    need(set(calls)==added_tools and len(remove)==10,'exact two new paths/two reviews/four calls/two pins')
    need(pins=={'music_author_review':'D7B0A1E03B1AA25F7B627FF0CA316DF09364FEF12F6664FC7B17AEA3FF20B0FD','music_integration_review':'FAFF1A4105F0F9A555FAB4FA18B3599EBA27915B6796E51C19AF27F4A1A38FD0'},'new gate hashes')
    for n in ast.walk(tree):
        if isinstance(n,ast.Dict):
            for key,value in zip(n.keys,n.values):
                if isinstance(key,ast.Constant)and key.value=='original_evolution_music':
                    remove.append(types.SimpleNamespace(lineno=key.lineno,end_lineno=value.end_lineno))
    old=without_nodes(raw,remove).decode()
    for name,digest in (('shoot-display-epoch.gba',DISPLAY),('evolution-music.gba','DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049')):
        line='    "'+name+'": "'+digest+'",\r\n';need(old.count(line)==1,'new layer entry');old=old.replace(line,'')
    old=old.replace('shoot_display_epoch','candidate').replace('shoot-display-epoch.json','current-candidate.json').replace(FINAL,DISPLAY)
    claim='            "exact current integration candidate with four source evolution scores and original waveforms; "\r\n            "existing production music stop/return behavior retained, audible parity not claimed; "\r\n            "including the five-state "'
    need(old.count(claim)==1,'bounded new claim wording')
    old=old.replace(claim,'            "exact current integration candidate including the five-state "')
    need(sha(old.encode())=='DE4B99720523A7B1FA4D4CD68C06F251A8B7C26C97167294C9195991BC0235C0','complete main inverse to frozen v76')
    return calls,pins,sha(old.encode())


def check_runtime(raw):
    tree=ast.parse(raw);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
    need(isinstance(fn.body[1],ast.Assign)and isinstance(fn.body[2],ast.If),'new script identity and music inverse prefix')
    old=without_nodes(raw,fn.body[1:3]).decode()
    old=old.replace('sha(observer) == script_sha','sha(observer) == SCRIPT').replace("launch['script_sha256'] == script_sha","launch['script_sha256'] == SCRIPT").replace('observer_sha256=script_sha','observer_sha256=SCRIPT')
    need(old.count('complete actual loaded ROM')==1,'extent-neutral diagnostic label')
    old=old.replace('complete actual loaded ROM','complete actual loaded8MB ROM')
    need(sha(old.encode())=='665AE76FDFCCF1806FE060C137E2E591FF3B6510CC601F148EEB35FFABE3D328','complete shared runtime inverse to frozen v76')
    return sha(old.encode())


def check_host(raw):
    text=raw.decode()
    block="wrapped_script = root / 'tools/bizhawk_probe_result_languages.lua'\nwrapped_sha = sha(wrapped_script)\nassert wrapped_sha == '"+BASE+"'\n"
    need(text.count(block)==1,'wrapped source prepin');text=text.replace(block,'')
    need(text.count(' and sha(wrapped_script) == wrapped_sha')==1,'wrapped source immutable postcheck');text=text.replace(' and sha(wrapped_script) == wrapped_sha','')
    need(text.count("report['wrapped_script_sha256'] = wrapped_sha\n")==1,'wrapped source report');text=text.replace("report['wrapped_script_sha256'] = wrapped_sha\n",'')
    text=text.replace('v77-20261110','v76-20261110').replace(FINAL,DISPLAY).replace(WRAPPER,BASE).replace('bizhawk_probe_result_languages_16m.lua','bizhawk_probe_result_languages.lua')
    need(sha(text.encode())=='43210C82D6EE6D0D6334E26EC37AB9C4762970420D65565F8AE8BE8A3D12DA64','complete private host inverse to frozen v76')
    return sha(text.encode())


class CaptureBlocked(Exception):pass


def prefix(rom,retail,observer,positive):
    calls=[]
    allowed={ROOT/'tools/build_evolution_music_integration.py',ROOT/'tools/bizhawk_probe_result_languages.lua'}
    def guarded(path):
        if path in allowed:return path.read_bytes()
        calls.append(str(path));raise CaptureBlocked()
    fn=types.FunctionType(runtime.audit.__code__,dict(runtime.audit.__globals__,read=guarded),argdefs=runtime.audit.__defaults__)
    try:fn(Path('NO_CAPTURE_IO'),rom,retail,observer)
    except CaptureBlocked:need(positive and calls==['NO_CAPTURE_IO\\launch.json'],'valid prefix reaches only first capture read')
    except ValueError:need(not positive and not calls,'bad prefix rejected before capture read')
    else:raise ValueError('audit prefix did not reach boundary')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();need(not args.report.exists(),'fresh output')
    raw=(ROOT/'tools/build_current_candidate.py').read_bytes();qraw=(ROOT/'tools/verify_result_language_capture.py').read_bytes();hraw=(ROOT/'build/run_result_v77_r1_20261110.py').read_bytes()
    need(tuple(map(sha,(raw,qraw,hraw)))==(MAIN,RUNTIME,HOST),'frozen main/runtime/actual host')
    calls,pins,main_old=check_main(raw);runtime_old=check_runtime(qraw);host_old=check_host(hraw)
    rom=(ROOT/'build/evolution-music-integration-20261110/component.gba').read_bytes();display=(ROOT/'build/shoot-terminal-display-epoch-20261110/component.gba').read_bytes()
    retail=Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba').read_bytes()
    observer=(ROOT/'tools/bizhawk_probe_result_languages_16m.lua').read_bytes();base=(ROOT/'tools/bizhawk_probe_result_languages.lua').read_bytes()
    need((sha(observer),sha(base))==(WRAPPER,BASE),'observer/transitive base pins')
    prefix(rom,retail,observer,True);prefix(display,retail,base,True);prefix(rom,retail,base,False)
    rejected=[]
    for at in (0xD14A8,0x37C2A4,0x6FF720,0xD33000,0xD7E000,0xFFFFFF):
        bad=bytearray(rom);bad[at]^=1;prefix(bytes(bad),retail,observer,False);rejected.append(at)
    prefix(rom[:-1],retail,observer,False);rejected.append('truncated16MiB')
    report=dict(status='V77_MUSIC_DISPLAY_MAIN_RUNTIME_HOST_PREFLIGHT_PASS',main_sha256=MAIN,runtime_sha256=RUNTIME,host_sha256=HOST,complete_reconstructed_v76_sources=dict(main=main_old,runtime=runtime_old,host=host_old),fresh_new_calls=calls,new_gate_pins=pins,observer_sha256=WRAPPER,wrapped_source_sha256=BASE,actual_prefix_positive_cases=2,rejected_before_capture_IO=rejected,old8MiB_observer_rejected_for_C508=True,all_other_v76_bytes_preserved=True,verifier_sha256=sha(Path(__file__).read_bytes()),capture_files_opened=0,emulator_launched=False,full_build_executed=False,old_semantic_suite_rerun=False)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],sha(args.report.read_bytes()))


if __name__=='__main__':main()
