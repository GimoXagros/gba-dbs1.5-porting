"""Run the post-Shoot campaign on a private desktop using the earned new-campaign state."""
import hashlib,json,os,shutil,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from mgba_headless_gdb_capture import PrivateDesktopProcess
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
name='bizhawk-roster-name-v91-20261124-'+sys.argv[1]
assert sys.argv[1] in ('a','b','c','d')
assert os.path.samefile('W:/',root)
rom=root/'build/mode11-extra-award-sequence-20261124/component.gba'
rom_bytes=rom.read_bytes();assert sha(rom_bytes)=='543F19927D5A21FA80C7EF70D50F571768E8F9C67F75847A13BAAFEEEA7ADA23'
script=root/'tools/bizhawk_probe_mode11_roster_name.lua';script_bytes=script.read_bytes()
exe=root/'local/BizHawk-2.11.1/EmuHawk.exe'
assert sha(exe.read_bytes())=='F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
out=root/'build'/name;out.mkdir(exist_ok=False);alias='W:/build/'+name
cfg=json.loads((root/'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
for i,entry in enumerate(cfg['PathEntries']['Paths']):
 entry['Path']=alias+'/data/'+str(i);Path(entry['Path']).mkdir(parents=True)
cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,SoundOutputMethod=3)
def check(value):
 if isinstance(value,dict):
  for k,v in value.items():
   if k=='AutoLoad':assert v is False
   check(v)
 elif isinstance(value,list):
  for v in value:check(v)
check(cfg)
(out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
source_state=root/'build/bizhawk-double-roster-search-v91-20261124-a/permanent-award.State'
assert sha(source_state.read_bytes())=='C524CD78CCE8B195E2D352CF83152A93441A03977C6E3D22E7663B00CAF95EFE'
shutil.copyfile(source_state,out/'campaign.State')
shutil.copyfile(rom,out/'probe.gba')
args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/bizhawk_probe_mode11_roster_name.lua','--userdata=output:'+alias+';probe_sha256:'+sha(rom_bytes)+';score_authorization:user-approved-development-score999;boss_authorization:user-approved-development-boss-once-per-stage',alias+'/probe.gba']
report=dict(visible=False,physical_background_input=False,supplied_save_used=False,guest_writes=[],rom_sha256=sha(rom_bytes),script_sha256=sha(script_bytes),host_sha256=sha(Path(__file__).read_bytes()),arguments=args)
with PrivateDesktopProcess(exe,args,exe.parent) as process:
 report['pid']=process.pid
 (out/'launch.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 deadline=time.monotonic()+180
 while not (out/'collection-done.txt').exists() and time.monotonic()<deadline and not (out/'stop.request').exists():time.sleep(.25)
 report['outcome']=(out/'collection-done.txt').read_text()if(out/'collection-done.txt').exists()else'host-timeout'
 if report['outcome']=='permanent-award-title':
  report['natural_process_exit']=process._wait_process(process.process.hProcess,20000)==0
  assert report['natural_process_exit'], 'save RAM flush and orderly emulator exit'
  assert (out/'data/104/probe.SaveRAM').is_file()

report['loaded_rom_exact']=(out/'loaded-rom.bin').exists() and (out/'loaded-rom.bin').read_bytes()==rom_bytes
report['script_unchanged']=script.read_bytes()==script_bytes
report['files']={p.relative_to(out).as_posix():sha(p.read_bytes())for p in sorted(out.rglob('*'))if p.is_file()and p.name!='launch.json'}
(out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k]for k in('outcome','loaded_rom_exact','script_unchanged')}))
assert report['outcome']== 'permanent-award-title' and report['loaded_rom_exact'] and report['script_unchanged']
