"""Power-cycle the earned post-award EEPROM in a new private GBA process."""
import hashlib,json,os,shutil,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from mgba_headless_gdb_capture import PrivateDesktopProcess
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
name='bizhawk-cold-roster-v91-20261124-'+sys.argv[1]
assert sys.argv[1] in ('a','b','c','d')
assert os.path.samefile('W:/',root)
rom=root/'build/mode11-extra-award-sequence-20261124/component.gba'
rom_bytes=rom.read_bytes();assert sha(rom_bytes)=='543F19927D5A21FA80C7EF70D50F571768E8F9C67F75847A13BAAFEEEA7ADA23'
script=root/'tools/bizhawk_probe_mode11_roster_cold.lua';script_bytes=script.read_bytes()
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
campaign=(root/sys.argv[2]).resolve()
launch=json.loads((campaign/'launch.json').read_bytes())
assert launch['outcome']=='permanent-award-title' and launch['loaded_rom_exact']
donor=campaign/'data/104/probe.SaveRAM'
save_digest=sha(donor.read_bytes())
assert save_digest==launch['files']['data/104/probe.SaveRAM']
raw=donor.read_bytes()
logical=b''.join(raw[i:i+8][::-1] for i in range(0,200,8))
assert logical[18]&48==48 and sum(logical[:192])==int.from_bytes(logical[192:196],'little')
entry=cfg['PathEntries']['Paths'][104]
assert entry['System']=='GBA' and entry['Type']=='Save RAM'
save=Path(entry['Path'])/'probe.SaveRAM'
assert not save.exists()
shutil.copyfile(donor,save)
assert sha(save.read_bytes())==save_digest
shutil.copyfile(rom,out/'probe.gba')
args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/bizhawk_probe_mode11_roster_cold.lua','--userdata=output:'+alias,alias+'/probe.gba']
report=dict(visible=False,physical_background_input=False,supplied_save_used=False,guest_writes=[],rom_sha256=sha(rom_bytes),script_sha256=sha(script_bytes),host_sha256=sha(Path(__file__).read_bytes()),copied_genuine_completion_save=save_digest,arguments=args)
with PrivateDesktopProcess(exe,args,exe.parent) as process:
 report['pid']=process.pid
 (out/'launch.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 deadline=time.monotonic()+180
 while not (out/'done.txt').exists() and time.monotonic()<deadline and not (out/'stop.request').exists():time.sleep(.25)
 report['outcome']=(out/'done.txt').read_text()if(out/'done.txt').exists()else'host-timeout'
report['loaded_rom_exact']=(out/'loaded-rom.bin').exists() and (out/'loaded-rom.bin').read_bytes()==rom_bytes
assert sha(donor.read_bytes())==save_digest
report['script_unchanged']=script.read_bytes()==script_bytes
report['files']={p.relative_to(out).as_posix():sha(p.read_bytes())for p in sorted(out.rglob('*'))if p.is_file()and p.name!='launch.json'}
(out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k]for k in('outcome','loaded_rom_exact','script_unchanged')}))
assert report['outcome']=='both-portraits-loaded' and report['loaded_rom_exact'] and report['script_unchanged']
