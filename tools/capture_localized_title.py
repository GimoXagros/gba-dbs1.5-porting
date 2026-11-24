"""Fresh isolated language UI capture on a private desktop."""
import hashlib,json,os,shutil,sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from mgba_headless_gdb_capture import PrivateDesktopProcess
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
language=int(sys.argv[1]);assert 0<=language<=3
import re
run_id=sys.argv[2]
assert re.fullmatch(r'[a-z0-9-]+',run_id)
name=f'bizhawk-title-headers-{run_id}-lang{language}'
assert os.path.samefile('W:/',root)
rom=Path(sys.argv[3]).resolve()
rom_bytes=rom.read_bytes();assert len(rom_bytes)==0x1000000 and sha(rom_bytes)==sys.argv[4]
english_review = sys.argv[5:] == ['--english-review']
menu_review = sys.argv[5:] == ['--menu-review']
assert not sys.argv[5:] or (language == 0 and english_review) or menu_review
script_name = ('bizhawk_review_menu_matrix.lua' if menu_review else
               'bizhawk_capture_english_title.lua' if english_review else 'bizhawk_capture_localized_title.lua')
script = root/'tools'/script_name
script_bytes = script.read_bytes()
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
if menu_review:
 donor=root/'build/bizhawk-collection-v89-20261124-final-a/data/104/probe.SaveRAM'
 save_entry=cfg['PathEntries']['Paths'][104]
 assert (save_entry['System'],save_entry['Type'])==('GBA','Save RAM')
 digest=sha(donor.read_bytes())
 assert digest=='6B10ABBD459E034B6D16FC035AB89EA8A6A1280FC7A90C9FE1D1B7F0BA0B5148'
 shutil.copyfile(donor,Path(save_entry['Path'])/'probe.SaveRAM')
(out/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
shutil.copyfile(rom,out/'probe.gba')
args=['--gdi','--config='+alias+'/config.json','--lua=W:/tools/'+script_name,'--userdata=output:'+alias+';language:'+str(language)+(';english_review:1' if english_review else ''),alias+'/probe.gba']
report=dict(visible=False,physical_background_input=False,supplied_save_used=False,guest_writes=[],language=language,rom_sha256=sha(rom_bytes),script_sha256=sha(script_bytes),host_sha256=sha(Path(__file__).read_bytes()),arguments=args)
if menu_review:
 report['copied_campaign_eeprom']=digest
 report['branch_checkpoint']='in-run root after saving language in Options'
with PrivateDesktopProcess(exe,args,exe.parent) as process:
 report['pid']=process.pid
 (out/'launch.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 deadline=time.monotonic()+180
 while not (out/'done.txt').exists() and time.monotonic()<deadline and not (out/'stop.request').exists():time.sleep(.25)
 report['outcome']=(out/'done.txt').read_text()if(out/'done.txt').exists()else'host-timeout'
report['loaded_rom_exact']=(out/'loaded-rom.bin').exists() and (out/'loaded-rom.bin').read_bytes()==rom_bytes
report['script_unchanged']=script.read_bytes()==script_bytes
report['files']={p.relative_to(out).as_posix():sha(p.read_bytes())for p in sorted(out.rglob('*'))if p.is_file()and p.name!='launch.json'}
(out/'launch.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k]for k in('language','outcome','loaded_rom_exact','script_unchanged')}))
assert report['outcome']==('PASS' if menu_review else 'ordinary-language-title-portrait-complete') and report['loaded_rom_exact'] and report['script_unchanged']
