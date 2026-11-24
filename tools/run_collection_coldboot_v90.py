"""Fresh isolated language UI capture on a private desktop."""
import hashlib,json,os,shutil,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from mgba_headless_gdb_capture import PrivateDesktopProcess
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
name='bizhawk-cold-collection-v90-20261124-'+sys.argv[1]
assert sys.argv[1] in ('a','b','c','d')
assert os.path.samefile('W:/',root)
rom=root/'build/source-english-submenus-20261124/component.gba'
rom_bytes=rom.read_bytes();assert sha(rom_bytes)=='8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
script=root/'tools/bizhawk_probe_collection_coldboot_v90.lua';script_bytes=script.read_bytes()
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
donor=root/'build/bizhawk-collection-v89-20261124-final-a/data/104/probe.SaveRAM'
save_digest=sha(donor.read_bytes())
assert save_digest=='6B10ABBD459E034B6D16FC035AB89EA8A6A1280FC7A90C9FE1D1B7F0BA0B5148'
entry=cfg['PathEntries']['Paths'][104]
assert entry['System']=='GBA' and entry['Type']=='Save RAM'
save=Path(entry['Path'])/'probe.SaveRAM'
assert not save.exists()
shutil.copyfile(donor,save)
assert sha(save.read_bytes())==save_digest
shutil.copyfile(rom,out/'probe.gba')
args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/bizhawk_probe_collection_coldboot_v90.lua','--userdata=output:'+alias,alias+'/probe.gba']
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
assert report['outcome']=='cold-collection-loaded' and report['loaded_rom_exact'] and report['script_unchanged']
