#!/usr/bin/env python3
"""Completed v75 ordinary-KO capture and raw v74 regression comparison."""
import argparse
import hashlib
import json
from pathlib import Path

import verify_result_language_capture as q

ROOT=Path(__file__).resolve().parents[1]
FRESH=ROOT/'build/bizhawk-result-v75-20261110-a'
OLD=ROOT/'build/bizhawk-result-v74-20261109-a'
FINAL='46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
PRIOR='70D002DE25C7509EF367FF4843D610783A2D6F04403AAB136A3E37029C529B40'
PINS={
 'tools/verify_result_language_capture.py':'C31719BAE4C6D1BBD6B92A6BA8C0AB04C1494339EEEDF6D0D61435CBD4279A67',
 'tools/verify_result_language.py':'3607645DB4A8DD214A5EBBA02ECE12F725DA1D573015E7E131ED69E5653C86CA',
 'build/run_result_v75_20261110.py':'B006A842802BF90241538D9CCE744F75ED58889E2B14468745183C065B97120F',
 'tools/verify_result_v74_capture.py':'D526C9921AC5668C8F5C9CCC7B62B4D65AF06F798D42029738C291DEB231BF00',
 'build/result-v74-runtime-qa-20261109/ko-audit.json':PRIOR}

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def read(path):
    need(path.suffix.lower()not in('.sav','.state'),'no save/state access')
    return path.read_bytes()
def flat_inventory(directory):return {p.name:sha(read(p))for p in sorted(directory.iterdir())if p.is_file()}
def changes(a,b):
    need(len(a)==len(b),'equal region lengths')
    offsets=[i for i,(x,y)in enumerate(zip(a,b))if x!=y];ranges=[]
    for i in offsets:
        if ranges and ranges[-1]['end']==i:ranges[-1]['end']=i+1
        else:ranges.append(dict(start=i,end=i+1))
    for r in ranges:
        r['before']=a[r['start']:r['end']].hex().upper();r['after']=b[r['start']:r['end']].hex().upper()
    words=[dict(offset=i,before=f'{int.from_bytes(a[i:i+4],"little"):08X}',after=f'{int.from_bytes(b[i:i+4],"little"):08X}')for i in sorted({j&~3 for j in offsets})]
    return dict(changed_bytes=len(offsets),changed_ranges=ranges,aligned_words=words)
def trace(directory):
    lines=read(directory/'trace.txt').decode('utf8').splitlines()
    return lines,{q.fields(l)['capture']:q.fields(l)for l in lines if l.startswith('capture=')}
def rows(lines,prefix,omit):return [{k:v for k,v in q.fields(l).items()if k not in omit}for l in lines if l.startswith(prefix)]

def audit(root_completed,outdir):
    need(root_completed,'root must confirm completed emulator run before reading capture')
    for path,digest in PINS.items():need(sha(read(ROOT/path))==digest,'frozen dependency '+path)
    prior=json.loads(read(ROOT/'build/result-v74-runtime-qa-20261109/ko-audit.json'))
    old_launch=json.loads(read(OLD/'launch.json'))
    need(sha(read(OLD/'launch.json'))==prior['launch_sha256']and sha(read(OLD/'trace.txt'))==prior['trace_sha256'],'trusted complete v74 capture')
    for name,digest in old_launch['files'].items():need(Path(name).name==name and sha(read(OLD/name))==digest,'prior flat artifact '+name)
    before=[flat_inventory(OLD),flat_inventory(FRESH)]
    cfg=json.loads(read(FRESH/'config.json'))
    need(cfg['SoundOutputMethod']==1 and cfg['SoundEnabled']is False and cfg['AutoLoadLastSaveSlot']is False and cfg['AutosaveSaveRAM']is False,'observed saved method1, sound disabled and no autoload/autosave')
    report=q.audit(FRESH,read(ROOT/'build/bizhawk-result-v75-20261110-a/probe.gba'),
        read(Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba')),read(ROOT/'tools/bizhawk_probe_result_languages.lua'))
    need(report['rom_sha256']==FINAL and report['language']=='ko'and report['snapshots']==8,'actual final46B3 Korean eight-snapshot capture')
    need((report['writer_calls'],report['init_calls'],report['draw_calls'])==(1,7,88),'same native observation populations')
    need(report['rendered_label']['pixels']==1508,'full actual WIN label proof')
    oldlines,oldcaps=trace(OLD);newlines,newcaps=trace(FRESH)
    need(list(oldcaps)==list(newcaps)and len(oldcaps)==8,'same eight full capture labels')
    snapshots=[]
    for name in oldcaps:
        need(all(oldcaps[name][k]==newcaps[name][k]for k in('mode','tag','result_age','timing')),'capture semantic metadata '+name)
        row=dict(capture=name,old_core=int(oldcaps[name]['core']),new_core=int(newcaps[name]['core']),
            core_delta=int(newcaps[name]['core'])-int(oldcaps[name]['core']),regions={})
        for region in q.SIZES:
            a,b=(read(d/(name+'-'+region+'.bin'))for d in(OLD,FRESH))
            row['regions'][region]=changes(a,b)
            need(a==b,'whole game/display region including IWRAM '+name+'/'+region)
        row['screenshot_identical']=read(OLD/(name+'.png'))==read(FRESH/(name+'.png'))
        need(row['screenshot_identical'],'whole screenshot regression '+name)
        snapshots.append(row)
    typed={}
    for prefix,omit in(('input ',{'relative'}),('mode=',{'core','relative'}),('stage=',{'core','relative'}),
        ('native-writer-entry ',{'core'}),('text-draw ',{'core'}),('initialized ',{'core','event','layout','flags','x','y'}),('summary ',set())):
        oldrows,newrows=rows(oldlines,prefix,omit),rows(newlines,prefix,omit)
        need(oldrows==newrows,'typed trace identity '+prefix)
        timing=[]
        for i,(a,b)in enumerate(zip(rows(oldlines,prefix,set()),rows(newlines,prefix,set()))):
            deltas={k:dict(old=int(a[k]),new=int(b[k]),delta=int(b[k])-int(a[k]))for k in('core','relative')if k in a}
            if deltas:timing.append(dict(row=i,fields=deltas))
        typed[prefix]=dict(rows=len(oldrows),identity_equal=True,all_frame_deltas=timing)
    raw_diffs=[dict(line=i+1,old=a,new=b)for i,(a,b)in enumerate(zip(oldlines,newlines))if a!=b]
    need(len(oldlines)==len(newlines) and not raw_diffs,'complete trace identity and zero frame deltas')
    need([flat_inventory(OLD),flat_inventory(FRESH)]==before,'both final capture inventories unchanged during audit')
    for path,digest in PINS.items():need(sha(read(ROOT/path))==digest,'dependencies unchanged '+path)
    outdir.mkdir(parents=True,exist_ok=True)
    report_path=outdir/'ko-audit.json';comparison_path=outdir/'v74-comparison.json'
    need(not report_path.exists()and not comparison_path.exists(),'fresh outputs outside capture')
    report_path.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'))
    comparison=dict(status='PASS',baseline_report_sha256=PRIOR,baseline_launch_sha256=prior['launch_sha256'],
        baseline_trace_sha256=prior['trace_sha256'],fresh_report_sha256=sha(read(report_path)),
        flat_capture_inventories=before,snapshots=snapshots,typed_trace_comparisons=typed,
        full_trace_byte_identical=read(OLD/'trace.txt')==read(FRESH/'trace.txt'),full_raw_trace_differences=raw_diffs,
        checker_sha256=sha(read(Path(__file__))),dependencies=PINS,
        audio_config=dict(pinned_host_configured_method=3,completed_saved_method=1,sound_enabled=False,
                          qualification='Host configures3; emulator-completed saved config records1. Actual audio backend not inferred.'),
        limits=['Every timing delta and raw IWRAM difference is retained; no normalization or whole-RAM/performance parity claim.',
                'Initializer hooks precede complete initialization; identity fields compared and every raw line difference retained.',
                'Ordinary Korean Options/title/battle/WIN regression only; actual Shoot positive-hit, terminal and historical E5 are separate.',
                'No emulator, isolated SaveRAM tree, supplied save/State, old manual suite, main/host/Git edit or capture mutation by auditor.'])
    comparison_path.write_bytes((json.dumps(comparison,indent=2)+'\n').encode('utf8'))
    return sha(read(report_path)),sha(read(comparison_path))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--outdir',type=Path,required=True);a=p.parse_args()
    need(a.outdir.resolve()not in(FRESH.resolve(),OLD.resolve()),'reports outside frozen captures')
    print('PASS',*audit(a.root_completed,a.outdir))

if __name__=='__main__':main()
