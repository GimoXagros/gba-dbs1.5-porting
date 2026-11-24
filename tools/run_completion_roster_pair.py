"""Observe the authorized WSC copy and independently earned GBA EEPROM in private cold boots."""
import argparse
import json
import os
import shutil
import time
from pathlib import Path

from mgba_headless_gdb_capture import PrivateDesktopProcess
from verify_mode23_completion_save import sha

ROOT=Path(__file__).resolve().parents[1]
WSC='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
ARCHIVE='051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F'
WRAPPER='D855BBDEED1F058B9769A11D6EDFB9AF8F863A22A7F2658F3F8141A641622185'
EARNED='AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--platform',required=True,choices=('wsc','gba'))
    p.add_argument('--rom',required=True,type=Path)
    p.add_argument('--rom-sha256',required=True)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    assert os.path.samefile('W:/',ROOT)
    original=a.platform=='wsc'
    assert sha(a.rom.read_bytes())==a.rom_sha256 and (not original or a.rom_sha256==WSC)
    src=ROOT/'build/bizhawk-wsc-saved-20261109-menu3'
    if original:
        donor=next((src/'data/276').glob('*.SaveRAM'))
        expected=WRAPPER
        packed=donor.read_bytes()
        assert sha(packed[1024:])==ARCHIVE
    else:
        donor=ROOT/'build/bizhawk-roster-name-v91-20261124-c/data/104/probe.SaveRAM'
        expected=EARNED
    assert sha(donor.read_bytes())==expected
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert sha(exe.read_bytes())=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
    out=a.output.resolve()
    out.mkdir(parents=True,exist_ok=False)
    alias='W:/'+out.relative_to(ROOT).as_posix()
    template=src if original else ROOT/'build/bizhawk-gba-diagnostic-20261026'
    cfg=json.loads((template/'config.json').read_text(encoding='utf-8-sig'))
    for i,e in enumerate(cfg['PathEntries']['Paths']):
        e['Path']=alias+'/data/'+str(i)
        Path(e['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    idx=276 if original else 104
    selected=cfg['PathEntries']['Paths'][idx]
    assert selected['Type']=='Save RAM'
    shutil.copyfile(donor,Path(selected['Path'])/donor.name)
    ext='wsc' if original else 'gba'
    shutil.copyfile(a.rom,out/('probe.'+ext))
    lua=ROOT/'tools/bizhawk_observe_completion_rosters.lua'
    args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/'+lua.name,
          '--userdata=output:'+alias,alias+'/probe.'+ext]
    with PrivateDesktopProcess(exe,args,exe.parent) as proc:
        deadline=time.monotonic()+160
        while not (out/'done.txt').exists() and time.monotonic()<deadline:
            time.sleep(.25)
    outcome=(out/'done.txt').read_text() if (out/'done.txt').exists() else 'timeout'
    report=dict(rom_sha256=a.rom_sha256,donor_sha256=expected,outcome=outcome,
                guest_writes=[],display='private desktop',lua_sha256=sha(lua.read_bytes()),
                loaded_exact=sha((out/'loaded-rom.bin').read_bytes())==a.rom_sha256)
    if original:
        expected_sram=bytearray(packed[1024:])
        expected_sram[0x4e]=1
        expected_sram[0x73]=0
        assert (out/'initial-sram.bin').read_bytes()==expected_sram
    assert sha(donor.read_bytes())==expected
    report['captures']={q.name:sha(q.read_bytes()) for q in sorted(out.glob('id-*'))}
    report['trace_sha256']=sha((out/'trace.txt').read_bytes())
    (out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(outcome,sha((out/'launch.json').read_bytes()))
    assert outcome=='ordinary-15-pass' and report['loaded_exact']


if __name__=='__main__':
    main()

