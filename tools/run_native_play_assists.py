"""Cold native play from a copied settings save, with no emulator cheats or guest writes."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from mgba_headless_gdb_capture import PrivateDesktopProcess

ROOT=Path(__file__).resolve().parents[1]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def run(a):
    rom=a.rom.resolve();out=a.output.resolve()
    assert -1<=a.fixed<=999 and (a.route!='campaign' or a.fixed==999)
    assert Path('W:/').samefile(ROOT) and out.is_relative_to(ROOT/'build') and digest(rom)==a.expected
    assert digest(a.save)==a.save_sha256
    owner=json.loads(a.owner.read_bytes())
    with rom.open('rb') as f:
        for row in owner['writes']:
            f.seek(row['offset'])
            assert hashlib.sha256(f.read(row['size'])).hexdigest().upper()==row['after_sha256']
    out.mkdir(parents=True,exist_ok=False)
    alias='W:/'+out.relative_to(ROOT).as_posix()
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert digest(exe)=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
    cfg=json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i,entry in enumerate(cfg['PathEntries']['Paths']):
        entry['Path']=alias+'/data/'+str(i)
        Path(entry['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
    assert cfg['PathEntries']['Paths'][104]['Type']=='Save RAM'
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    saved=out/'data/104/probe.SaveRAM'
    shutil.copyfile(a.save,saved)
    shutil.copyfile(rom,out/'probe.gba')
    script=Path(__file__).with_name('bizhawk_native_play_assists.lua')
    frozen=out/'controller.lua'
    shutil.copyfile(script,frozen)
    lua=frozen.read_text(encoding='utf8')
    assert all(x not in lua for x in ('memory.write','savestate.','setregister','dofile','loadfile'))
    symbols=owner['symbols']
    u=f"output:{alias};fixed:{a.fixed};route:{a.route};score_pc:{symbols['assist_score_store']};boss_pc:{symbols['assist_boss_store']}"
    args=['--gdi','--config='+alias+'/config.json','--lua='+alias+'/controller.lua','--userdata='+u,alias+'/probe.gba']
    with PrivateDesktopProcess(exe,args,exe.parent):
        deadline=time.monotonic()+1800
        while not (out/'done.txt').is_file() and time.monotonic()<deadline:time.sleep(.4)
        outcome=(out/'done.txt').read_text() if (out/'done.txt').exists() else 'timeout'
        if outcome=='PASS' and a.route=='campaign':
            deadline=time.monotonic()+10
            while digest(saved)==a.save_sha256 and time.monotonic()<deadline:time.sleep(.2)
    report=dict(rom=a.expected,save_in=a.save_sha256,save_out=digest(saved),fixed=a.fixed,route=a.route,
                script_sha256=digest(frozen),visible=False,loaded_rom_exact=digest(out/'loaded-rom.bin')==a.expected,
                guest_writes=[],trace=digest(out/'play.txt'),outcome=outcome)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    lines=(out/'play.txt').read_text().splitlines()
    assert outcome=='PASS' and report['loaded_rom_exact'],(outcome,lines[-5:])
    if a.route=='campaign':
        assert [int(s.split()[-1]) for s in lines if 'boss assist' in s]==[7,11]
        assert [int(s.split()[-1]) for s in lines if 'real hit' in s]==[7,11]
        assert report['save_in']!=report['save_out']
        assert saved.read_bytes()[272:280]==a.save.read_bytes()[272:280], 'campaign altered assist settings'
    print(outcome,lines[-1],digest(out/'report.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for opt in ('rom','owner','save','output'):p.add_argument('--'+opt,required=True,type=Path)
    for opt in ('expected','save-sha256'):p.add_argument('--'+opt,required=True)
    p.add_argument('--fixed',type=int,required=True)
    p.add_argument('--route',choices=('sample','campaign'),required=True)
    run(p.parse_args())
