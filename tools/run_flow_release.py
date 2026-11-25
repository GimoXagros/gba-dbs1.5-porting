"""Capture one real selection and fight from a game-earned 15-fighter save."""
import argparse
import json
import shutil
import time
from pathlib import Path

from run_native_play_assists import ROOT, PrivateDesktopProcess, digest

DONOR = "AE15A17E9B0B4C66EC85A19AA390069048A0D9B9B973CDC05FFACAE220995E5D"
BIZHAWK = "F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD"


def capture(rom, expected, donor, out, fighter, record_hash=None):
    out, rom = out.resolve(), rom.resolve()
    assert out.is_relative_to(ROOT / 'build') and Path('W:/').samefile(ROOT)
    train = fighter is None and not record_hash
    assert digest(rom) == expected
    if train:
        assert donor is None and expected=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    elif record_hash:
        assert digest(donor)==record_hash and donor.stat().st_size==512
    else:
        assert digest(donor)==DONOR
    exe = ROOT / 'local/BizHawk-2.11.1/EmuHawk.exe'
    assert digest(exe) == BIZHAWK
    alias = 'W:/' + out.relative_to(ROOT).as_posix()
    out.mkdir(parents=True, exist_ok=False)
    cfg = json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i, entry in enumerate(cfg['PathEntries']['Paths']):
        entry['Path'] = alias+'/data/'+str(i)
        Path(entry['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False, AutoLoadLastSaveSlot=False, AutosaveSaveRAM=False,
               SoundEnabled=False, SoundOutputMethod=3)
    assert cfg['PathEntries']['Paths'][104]['Type']=='Save RAM'
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    saved = out/'data/104/probe.SaveRAM'
    if record_hash:
        envelope=ROOT/'build/bizhawk-cold-roster-v91-20261124-c/data/104/probe.SaveRAM'
        assert digest(envelope)==DONOR
        saved.write_bytes(donor.read_bytes()+envelope.read_bytes()[512:])
    elif not train:
        shutil.copyfile(donor,saved)
    filename='original.wsc' if train else 'probe.gba'
    shutil.copyfile(rom,out/filename)
    lua = out/'controller.lua'
    controller='bizhawk_flow_release_train.lua' if train else ('bizhawk_flow_release_records.lua' if record_hash else 'bizhawk_flow_release.lua')
    shutil.copyfile(Path(__file__).with_name(controller), lua)
    script = digest(lua)
    assert not any(s in lua.read_text() for s in ('memory.write','loadfile','setregister','savestate.load'))
    args=['--gdi','--config='+alias+'/config.json','--lua='+alias+'/controller.lua',
          '--userdata=out:'+alias+';fighter:'+str(fighter),alias+'/'+filename]
    with PrivateDesktopProcess(exe,args,exe.parent) as process:
        deadline = time.monotonic()+360
        while not (out/'done').exists() and time.monotonic()<deadline:
            time.sleep(.25)
        if (out/'done').exists():
            assert process._wait_process(process.process.hProcess, 20000)==0, 'emulator did not shut down'
    status = (out/'done').read_text() if (out/'done').exists() else 'timeout'
    if record_hash and status=='PASS':
        import struct
        raw=donor.read_bytes()
        data=b''.join(raw[i:i+8][::-1] for i in range(0,len(raw),8))
        assert len(data)==512
        lines=(out/'events.txt').read_text().splitlines()
        indexed={int(fields[2]): tuple(map(int,fields[3:5])) for line in lines if len(fields:=line.split())==5 and fields[1]=='row'}
        assert set(indexed)==set(range(15))
        for i,values in indexed.items():
            offset=0x8e+i*4 if i<12 else 224+(i-12)*4
            assert struct.unpack_from('<HH',data,offset)==values,(i,values)
        assert donor.read_bytes()==saved.read_bytes()[:512] and any(x[1]>0 for x in indexed.values()),'statistics must come from an earned battle'
    report=dict(rom=expected,source_save=None if train else digest(donor),final_save=None if train else digest(saved),controller=script,
                exact_rom=digest(out/'loaded.bin')==expected,visible=False,guest_writes=[],
                events=digest(out/'events.txt'),result=status,player=fighter)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(status, fighter,flush=True)
    assert status=='PASS' and report['exact_rom'],status


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('rom','out'): p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--save',type=Path)
    p.add_argument('--expected',required=True)
    route=p.add_mutually_exclusive_group(required=True)
    route.add_argument('--fighter',type=int,choices=range(15))
    route.add_argument('--original-train',action='store_true')
    route.add_argument('--record-save-sha256')
    a=p.parse_args()
    capture(a.rom,a.expected,a.save,a.out,a.fighter,a.record_save_sha256)
