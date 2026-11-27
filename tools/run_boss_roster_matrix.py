"""Replay the source-earned final campaign round through both boss fights for each fighter."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import time

from run_flow_release import BIZHAWK, DONOR, PrivateDesktopProcess, ROOT, digest


def play(args, fighter, form, progress, donor):
    out = args.out / f"id{fighter:02d}-form{form}"
    out.mkdir(parents=True, exist_ok=False)
    alias = 'W:/' + out.relative_to(ROOT).as_posix()
    cfg = json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i, entry in enumerate(cfg['PathEntries']['Paths']):
        entry['Path'] = f'{alias}/data/{i}'
        Path(entry['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False, AutoLoadLastSaveSlot=False, AutosaveSaveRAM=False,
               SoundEnabled=False, SoundOutputMethod=3, ClockThrottle=False, Unthrottled=True)
    (out/'config.json').write_text(json.dumps(cfg), encoding='utf8')
    slot = out/'data/104/probe.SaveRAM'
    shutil.copyfile(donor, slot)
    shutil.copyfile(args.rom, out/'probe.gba')
    script = ROOT/'tools/bizhawk_boss_roster_matrix.lua'
    shutil.copyfile(script, out/'driver.lua')
    resume = ''
    if args.resume_dir:
        prefix = args.resume_dir / out.name
        names = (['after-ko-11.State'] if args.after_ko else []) + ['live-11.State','live-7.State']
        checkpoint = next((prefix/n for n in names if (prefix/n).is_file()), None)
        if checkpoint:
            shutil.copyfile(checkpoint,out/'entry.State')
            resume = ';resume:'+checkpoint.stem[-2:].lstrip('-')
            if checkpoint.name.startswith('after-ko'):
                resume += ';postko:1'
            else:
                trace = (prefix/'events.txt').read_text(encoding='utf8')
                stage=checkpoint.stem.split('-')[1]
                hits=trace.split(f'KO stage={stage} ',1)
                if len(hits)==2:
                    retries = re.findall(rf'input retry {stage} (\d+)', hits[0])
                    resume += ';variant:'+(retries[-1] if retries else '0')
    runargs = ['--gdi', '--config='+alias+'/config.json', '--lua='+alias+'/driver.lua',
               f'--userdata=out:{alias};fighter:{fighter};form:{form};progress:{progress};first_strategy:{args.strategy}'+resume, alias+'/probe.gba']
    exe = ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    with PrivateDesktopProcess(exe,runargs,exe.parent) as proc:
        deadline = time.monotonic() + 720
        while not (out/'done').exists() and time.monotonic()<deadline:
            time.sleep(.4)
        outcome=(out/'done').read_text(encoding='utf8') if (out/'done').exists() else 'timeout'
        if (out/'done').exists():
            assert proc._wait_process(proc.process.hProcess, 20000)==0
    assert digest(out/'loaded.bin')==args.expected
    result=dict(fighter=fighter,form=form,rom=args.expected,save_in=digest(donor),save_out=digest(slot),
                script_sha256=digest(out/'driver.lua'),trace_sha256=digest(out/'events.txt'),visible=False,
                progress_at_selection=progress, outcome=outcome)
    if resume:
        result.update(checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint))
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(fighter,form,outcome,flush=True)
    return outcome


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True)
    p.add_argument('--expected',required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--ids',type=int,nargs='+',default=list(range(15)),choices=range(15))
    p.add_argument('--form',type=int,default=0,choices=(0,1))
    p.add_argument('--workers',type=int,default=3)
    p.add_argument('--resume-dir',type=Path,help='Reuse each fighter’s captured live boss state from the same matrix')
    p.add_argument('--after-ko',action='store_true',help='Prefer a genuine first-frame-after-lethal snapshot for A/B replay')
    p.add_argument('--strategy',type=int,default=0,choices=range(25))
    args=p.parse_args()
    args.out=args.out.resolve()
    assert args.out.is_relative_to(ROOT/'build') and Path('W:/').samefile(ROOT)
    assert digest(args.rom)==args.expected
    assert digest(ROOT/'local/BizHawk-2.11.1/EmuHawk.exe')==BIZHAWK
    donor=ROOT/'build/bizhawk-cold-roster-v91-20261124-c/data/104/probe.SaveRAM'
    assert digest(donor)==DONOR
    snapshot=ROOT/'build/bizhawk-double-roster-v91-20261124-b/campaign-stage-11-IWRAM.bin'
    assert digest(snapshot)=='8CF5F44050BC0322017999EF7679240EEFD01B28966E67777EBCB5F15DAADFA6'
    progress=snapshot.read_bytes()[0x232e]
    assert progress==10
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        outcomes=list(pool.map(lambda fid:play(args,fid,args.form,progress,donor),args.ids))
    raise SystemExit(0 if all(s=='PASS' for s in outcomes) else 1)


if __name__=='__main__':
    main()
