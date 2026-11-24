"""Run an assisted whole campaign from cold boot with an empty, private SaveRAM directory."""
import argparse,hashlib,json,os,shutil,time
from pathlib import Path
from mgba_headless_gdb_capture import PrivateDesktopProcess

ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest().upper()

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--expected',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rom=a.rom.resolve();out=a.output.resolve()
    assert os.path.samefile('W:/',ROOT) and out.is_relative_to(ROOT/'build') and sha(rom)==a.expected
    out.mkdir(parents=True,exist_ok=False)
    alias='W:/'+out.relative_to(ROOT).as_posix()
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert sha(exe)=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
    cfg=json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i,ent in enumerate(cfg['PathEntries']['Paths']):
        ent['Path']=alias+'/data/'+str(i)
        Path(ent['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    shutil.copyfile(rom,out/'probe.gba')
    script=ROOT/'tools/bizhawk_clean_ending_play.lua'
    assert 'savestate.load' not in script.read_text(encoding='utf8')
    args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/'+script.name,
          '--userdata=output:'+alias+';probe_sha256:'+a.expected+';score_authorization:user-approved-development-score999;boss_authorization:user-approved-development-boss-once-per-stage',alias+'/probe.gba']
    record=dict(rom_sha256=a.expected,script_sha256=sha(script),emulator_sha256=sha(exe),visible=False,
                supplied_save_used=False,initial_save_files=0,state_loads=0,
                authorized_assists=['ordinary P1 D-Spirit 999','stage 7 and 11 boss HP 1 once then player hit'])
    with PrivateDesktopProcess(exe,args,exe.parent) as proc:
        record['pid']=proc.pid
        (out/'launch.json').write_text(json.dumps(record,indent=2),encoding='utf8')
        until=time.monotonic()+1800
        while not (out/'done.txt').exists() and time.monotonic()<until:
            time.sleep(.5)
        record['outcome']=(out/'done.txt').read_text() if (out/'done.txt').exists() else 'timeout'
        deadline=time.monotonic()+10
        while record['outcome']=='PASS' and not (out/'data/104/probe.SaveRAM').exists() and time.monotonic()<deadline:time.sleep(.2)
    record['loaded_rom_exact']=(out/'loaded-rom.bin').is_file() and sha(out/'loaded-rom.bin')==a.expected
    record['files']={f.relative_to(out).as_posix():sha(f) for f in out.rglob('*') if f.is_file() and f.name!='launch.json'}
    (out/'launch.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
    print(record['outcome'])
    assert record['outcome']=='PASS' and record['loaded_rom_exact']
