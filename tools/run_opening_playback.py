"""Record the original opening graph and native conversion with ordinary no-input and Start routes."""
import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from mgba_headless_gdb_capture import PrivateDesktopProcess

ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def owners(ws):
    if ws:
        w=json.loads((ROOT/'evidence/wsc-opening-callback-graph.json').read_bytes())['wsc_15']
        slots={row['runtime_offset']:row['index'] for row in w['functions']}
        mapped={row['physical_start']:row['index'] for row in w['functions']}
        for row in w['functions']:
            for store in row['callback_stores']:
                if store['target_population_body'] in mapped:
                    slots[store['runtime_offset']]=mapped[store['target_population_body']]
        for i,k in enumerate(('convergence_function','terminal_function'),24):
            slots[w[k]-w['physical_to_runtime_bias']]=i
        return slots
    g=json.loads((ROOT/'evidence/gba-opening-callback-graph.json').read_bytes())['topology']
    linear=g['linear_functions'][:7]+[0x085b6000,0x085b6800,0x085b7000,0x085b7800]+g['linear_functions'][7:]
    order=linear+g['choice_functions']+[0x085b4c00,0x085b4600,g['convergence_function'],g['terminal_function']]
    assert len(order)==len(set(order))==26
    return dict(zip(order,range(26)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--limit',type=int,default=36000);p.add_argument('--skip',action='store_true')
    a=p.parse_args();ws=a.rom.suffix.lower()=='.wsc'
    rom=a.rom.read_bytes()
    expected='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7' if ws else 'D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99'
    assert sha(rom)==expected and Path('W:/').samefile(ROOT)
    exe=ROOT/'local/BizHawk-2.11.1/EmuHawk.exe'
    assert sha(exe.read_bytes())=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    alias=Path('W:/')/out.relative_to(ROOT)
    src=Path(__file__).with_name('bizhawk_opening_playback.lua')
    symbols=','.join(f'[0x{k:x}]={v}' for k,v in owners(ws).items())
    script=src.read_text(encoding='utf8').replace('@@SYMBOLS@@',symbols).replace('@@SKIP@@',str(a.skip).lower()).replace('@@LIMIT@@',str(a.limit))
    (out/'probe.lua').write_text(script,encoding='utf8',newline='\n')
    filename='game'+a.rom.suffix.lower()
    shutil.copyfile(a.rom,out/filename)
    cfg=json.loads((ROOT/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
    for i,row in enumerate(cfg['PathEntries']['Paths']):
        row['Path']=(alias/'data'/str(i)).as_posix();Path(row['Path']).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
    (out/'config.json').write_text(json.dumps(cfg),encoding='utf8')
    args=['--gdi','--config='+(alias/'config.json').as_posix(),'--lua='+(alias/'probe.lua').as_posix(),
          '--userdata=output:'+alias.as_posix(),(alias/filename).as_posix()]
    with PrivateDesktopProcess(exe,args,exe.parent):
        until=time.monotonic()+300
        while not (out/'finished.txt').exists() and time.monotonic()<until:time.sleep(.25)
    status=(out/'finished.txt').read_text() if (out/'finished.txt').exists() else 'host-timeout'
    result=dict(status=status,rom_sha256=expected,loaded_rom_exact=(out/'loaded-rom.bin').read_bytes()==rom,
                visible=False,guest_writes=[],supplied_save=False,host_limit=a.limit,skip=a.skip,
                script_sha256=sha((out/'probe.lua').read_bytes()),trace_sha256=sha((out/'trace.txt').read_bytes()))
    (out/'launch.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(status,result['trace_sha256'])
    assert result['loaded_rom_exact'] and status in ('title','bounded-after-title')


if __name__=='__main__':main()
