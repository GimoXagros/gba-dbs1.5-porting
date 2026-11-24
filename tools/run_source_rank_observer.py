"""Observe the WSC score and tag callbacks from the retained authentic stage-11 result."""
import argparse,json,shutil,time
from pathlib import Path
from mgba_headless_gdb_capture import PrivateDesktopProcess
from verify_mode23_completion_save import sha

r=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args();out=a.output.resolve();out.mkdir()
alias='W:/'+out.relative_to(r).as_posix()
donor=r/'build/bizhawk-wsc-terminal-tail-20261109-a';state=donor/'final.State'
assert sha(state.read_bytes())=='DB6DB2E7F3E1FF1E4E3AA6F155871CCA44476C8400AA0DD62041BB337A97BB4A'
rom=donor/'probe.wsc'
assert sha(rom.read_bytes())=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
shutil.copyfile(rom,out/'probe.wsc');shutil.copyfile(state,out/'source.State')
cfg=json.loads((donor/'config.json').read_bytes())
for i,ent in enumerate(cfg['PathEntries']['Paths']):
    ent['Path']=alias+'/data/'+str(i);Path(ent['Path']).mkdir(parents=True)
cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False)
(out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
exe=r/'local/BizHawk-2.11.1/EmuHawk.exe'
args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/bizhawk_observe_source_rank_result.lua','--userdata=output:'+alias,alias+'/probe.wsc']
with PrivateDesktopProcess(exe,args,exe.parent):
    deadline=time.monotonic()+240
    while not (out/'done.txt').exists() and time.monotonic()<deadline:time.sleep(.2)
proof=dict(source_sha256=sha(rom.read_bytes()),donor_state=sha(state.read_bytes()),guest_writes=[],private_desktop=True,
           outcome=(out/'done.txt').read_text()if(out/'done.txt').exists()else'timeout')
(out/'launch.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(proof)
