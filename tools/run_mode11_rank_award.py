"""Prove a real earned SPECIAL record and load that physical save in a separate hidden process."""
import argparse
import json
import os
import shutil
import time
from pathlib import Path

from mgba_headless_gdb_capture import PrivateDesktopProcess
from verify_mode23_completion_save import sha

ROOT=Path(__file__).resolve().parents[1]
CANDIDATE='78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
STATE='001DF714CC4EE525DBFB566D7F1BDDFCFDC4894EF4303D3EA9C8A8163746936A'


def run(phase,out,rom,donor):
    assert os.path.samefile('W:/',ROOT)
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert sha(exe.read_bytes())=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
    out.mkdir()
    alias='W:/'+out.relative_to(ROOT).as_posix()
    cfg=json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for n,item in enumerate(cfg['PathEntries']['Paths']):
        item['Path']=alias+'/data/'+str(n)
        Path(item['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False, AutoLoadLastSaveSlot=False, AutosaveSaveRAM=False, SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    save=out/'data/104/probe.SaveRAM'
    assert cfg['PathEntries']['Paths'][104]['Type']=='Save RAM'
    if phase=='award':
        assert sha(donor.read_bytes())==STATE
        shutil.copyfile(donor,out/'earned-campaign.State')
    else:
        packed=donor.read_bytes()
        assert len(packed)>=512 and packed[512:]==b'\xff'*(len(packed)-512)
        assert packed[216:224][::-1]==b'BS15TAG\x01'
        shutil.copyfile(donor,save)
    shutil.copyfile(rom,out/'probe.gba')
    lua=ROOT/'tools/bizhawk_probe_mode11_rank_award.lua'
    args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/'+lua.name,
          '--userdata=output:'+alias+';phase:'+phase+';result_pc:'+str(148704292),alias+'/probe.gba']
    report=dict(phase=phase,visible=False,guest_writes=[],supplied_save_used=False,rom_sha256=sha(rom.read_bytes()),
        script_sha256=sha(lua.read_bytes()),host_sha256=sha(Path(__file__).read_bytes()),donor_sha256=sha(donor.read_bytes()))
    with PrivateDesktopProcess(exe,args,exe.parent) as process:
        report['pid']=process.pid
        deadline=time.monotonic()+210
        while not (out/'done.txt').exists() and time.monotonic()<deadline:time.sleep(.25)
        report['outcome']=(out/'done.txt').read_text() if (out/'done.txt').is_file() else 'host-timeout'
        # The core exports SaveRAM while exiting. Keep the private desktop alive for that flush.
        if phase=='award' and report['outcome']=='award-pass':
            stop=time.monotonic()+12
            while not save.exists() and time.monotonic()<stop:time.sleep(.2)
    report['loaded_rom_exact']=(out/'loaded-rom.bin').exists() and (out/'loaded-rom.bin').read_bytes()==rom.read_bytes()
    report['files']={p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}
    (out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(phase,report['outcome'],flush=True)
    assert report['outcome']==phase+'-pass' and report['loaded_rom_exact']
    return save


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--previous-award',type=Path)
    a=p.parse_args()
    out=a.output.resolve()
    out.mkdir()
    rom=ROOT/'build/mode11-rank-award-20261124/component.gba'
    assert sha(rom.read_bytes())==CANDIDATE
    state=ROOT/'build/bizhawk-collection-hidden-aux-v91-20261124-b/permanent-award.State'
    if a.previous_award:
        prev=a.previous_award.resolve()
        proof=json.loads((prev/'launch.json').read_bytes())
        save=prev/'data/104/probe.SaveRAM'
        assert proof['outcome']=='award-pass' and proof['loaded_rom_exact']
        assert proof['rom_sha256']==CANDIDATE and sha(save.read_bytes())==proof['files']['data/104/probe.SaveRAM']
    else:
        save=run('award',out/'award',rom,state)
    run('cold',out/'cold',rom,save)


if __name__=='__main__':main()
