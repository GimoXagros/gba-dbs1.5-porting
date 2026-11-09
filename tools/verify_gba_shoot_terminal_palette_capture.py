"""Independent controlled FF3A terminal observation audit; no emulator or state load."""
import argparse
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

import verify_gba_shoot_terminal_capture as oldqa
import verify_gba_shoot_entry_capture_v2 as stateqa

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'build/bizhawk-gba-shoot-terminal-palette-20261109-a'
OLD=ROOT/'build/bizhawk-gba-shoot-terminal-20261109-a'
P,Q,AUX=oldqa.P,oldqa.Q,oldqa.AUX
sha,half,long,fields=oldqa.sha,oldqa.half,oldqa.long,oldqa.fields
event,core,actors,regs,state_fields=oldqa.event,oldqa.core,oldqa.actors,oldqa.regs,oldqa.state_fields
ROM='FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
S=0x020121E8

def audit():
 assert sha(Path(oldqa.__file__).read_bytes())=='1C19681BA22C6CF01B2A0B0B5C0EC8258456A94E27E4277E9F514511AF3AE5F5'
 launch_raw=(D/'launch.json').read_bytes();launch=json.loads(launch_raw)
 assert launch['completed']and launch['outcome']=='failure:bounded-no-completion'
 assert launch['done_text']==(D/'shoot-terminal-done.txt').read_text('utf8')=='failure:bounded-no-completion\n'
 assert not any(launch[k]for k in('visible','physical_background_input','supplied_save_used','host_stop_requested','host_deadline_reached'))
 inventory={p.relative_to(D).as_posix():sha(p.read_bytes())for p in sorted(D.rglob('*'))if p.is_file()and p.name!='launch.json'}
 assert inventory==launch['files']and len(inventory)==187
 for path,digest in launch['pins'].items():assert sha((ROOT/path).read_bytes())==digest
 assert len(launch['pins'])==4
 assert launch['pins']['tools/bizhawk_probe_gba_shoot_terminal_palette.lua']=='F0FB2E3164A69F666756C4CB51B0FDAE416BA2624A93BDA95D650C6303D6B278'
 assert launch['pins']['tools/bizhawk_probe_gba_shoot_terminal.lua']=='964BC4E16A722D576F3CE4BF7516A1D8495967E33847ACF65515FF35C8AB5C74'
 assert sha((ROOT/'build/run_gba_shoot_terminal_palette_20261109.py').read_bytes())==launch['launcher_sha256']=='F6EC291569166A3BA996AD46325DD4BB2203F8520FEB0E7A087BE7C03A168502'
 assert sha((ROOT/'build/gba-shoot-terminal-palette-pins-20261109.json').read_bytes())==launch['reviewed_pins_sha256']=='42A3FE105E0005AE0D67B2A7CE1369B008CC8DE3ED1EA78BF0E31229059C6E0D'
 assert all(launch[k]for k in('authorized_write_verified','loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged'))
 rom=(D/'loaded-rom.bin').read_bytes();assert rom==(D/'probe.gba').read_bytes()and sha(rom)==launch['rom_sha256']==ROM
 baseline=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
 for name,digest in launch['checkpoint_pins'].items():assert sha((D/'checkpoint'/name).read_bytes())==sha((baseline/name).read_bytes())==digest
 cfg=json.loads((D/'config.json').read_text('utf8'))
 assert all(cfg[k]is False for k in('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
 assert all(v['Path'].startswith('W:/build/'+D.name+'/data/')for v in cfg['PathEntries']['Paths'])
 source_blob=(D/'checkpoint/healthy-activation.State').read_bytes();source_core,_=stateqa.checkpoint_core(source_blob)
 restored_core,_=stateqa.checkpoint_core((D/'restored.State').read_bytes())
 assert (D/'restored.State').read_bytes()==(D/'00-before.State').read_bytes()
 assert sha(source_core)==launch['source_core_sha256']=='6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
 assert sha(restored_core)==launch['restored_core_sha256']
 expected=bytearray(source_core);struct.pack_into('<I',expected,12,zlib.crc32(rom))
 differences=[dict(offset=i,expected=a,actual=b)for i,(a,b)in enumerate(zip(expected,restored_core))if a!=b]
 rawdiff=[dict(offset=i,original=a,actual=b)for i,(a,b)in enumerate(zip(source_core,restored_core))if a!=b]
 assert differences==launch['all_Core_byte_differences']and len(differences)==9
 assert restored_core!=expected and not launch['restored_core_exact_except_current_rom_crc']and sha(expected)==launch['expected_restored_core_sha256']
 length=long(source_core,0);assert len(source_core)==len(restored_core)
 assert source_core[0x24:0x134]==restored_core[0x24:0x134]and launch['CPU_bank_equal']
 assert source_core[4+0x61000:4+length]==restored_core[4+0x61000:4+length]and launch['native_extensions_equal']
 assert source_core[4+length:]==restored_core[4+length:]and launch['managed_suffix_equal']
 old_launch_raw=(OLD/'launch.json').read_bytes();assert sha(old_launch_raw)=='D794BA5633B36882230BD6C7107960B930A959B956463BB1C9DB7313013AA7FE'
 old_launch=json.loads(old_launch_raw)
 crc_equal=[]
 for name in('restored','00-before','01-authorized-hp1','02-lethal-hit','03-terminal-route'):
  blob=(OLD/f'{name}.State').read_bytes();assert sha(blob)==old_launch['files'][f'{name}.State']
  prior_core,_=stateqa.checkpoint_core(blob);comparison=bytearray(prior_core);struct.pack_into('<I',comparison,12,zlib.crc32(rom))
  actual,_=stateqa.checkpoint_core((D/f'{name}.State').read_bytes())
  assert actual==comparison,'onlyCRC12:16crossROMcomparison:'+name
  crc_equal.append(name)
 lines=(D/'terminal-trace.txt').read_text('utf8').splitlines();oldtext=(OLD/'terminal-trace.txt').read_bytes();assert sha(oldtext)==old_launch['files']['terminal-trace.txt']
 oldlines=oldtext.decode().splitlines();assert lines[:190]==oldlines[:190]
 assert 'name=03-terminal-route'in lines[189]and 'kind=actor-85BDD00'in lines[190]
 inputs=event(lines,'input');oldinputs=event(oldlines,'input');assert inputs==oldinputs and len(inputs)==88
 assert [core(s)for s in inputs if fields(s)['Right']=='true']==[68927,68928]
 assert [core(s)for s in inputs if fields(s)['B']=='true']==[69000]
 ledger=(D/'terminal-write-ledger.txt').read_text('utf8').strip();assert ledger==launch['guest_write_ledger']==(OLD/'terminal-write-ledger.txt').read_text('utf8').strip()
 assert fields(ledger)==dict(core='69000',actor='02011828',address='0201188C',bytes='2',before='37',requested='1',P1HP='4',P1score='0',left='2120',right='4',attempt_consumed='true',after='1',verified='true')
 captures=event(lines,'capture');assert len(captures)==19
 assert len(list(D.glob('*.State')))==20
 with zipfile.ZipFile(io.BytesIO(source_blob))as z:sync=json.loads(z.read('SyncSettings.json'))
 snapshots={};ram={};timeline=[]
 for n,row in enumerate(captures):
  c=fields(row);name=c['name'];frame=int(c['export_core']);assert name.startswith(f'{n:02d}-')and core(row)==frame
  regions={k:(D/f'{name}-{k}.bin').read_bytes()for k in stateqa.OFFSETS};iw,ew=regions['iwram'],regions['ewram']
  parsed=stateqa.parse_checkpoint((D/f'{name}.State').read_bytes(),oldqa.helpers.metadata(iw,ew,frame),regions,rom)
  assert parsed['state']['mode']==7 and parsed['state']['stage']==11
  assert parsed['state']['P1HP']==(4 if n<=2 else 1)and parsed['state']['P2HP']==(37 if n==0 else 1 if n==1 else 0)
  assert long(iw,0x489C)==P and long(iw,0x48A0)==Q and long(iw,0x4D3C)==AUX
  for a,kind in((P,0),(Q,3),(AUX,6)):
   at=a-0x02000000;assert half(ew,at-0x18+0x10)&2 and half(ew,at+4)&15==kind
  for a,v in((P+0x14,P),(P+0x18,Q),(Q+0x14,Q),(Q+0x18,P),(Q+0x28,AUX),(AUX+0x18,P),(AUX+0x28,Q)):
   assert long(ew,a-0x02000000)==v
  for at,cb in((0x4510,0x08374FF4 if n<=1 else 0x08374FAC),(0x4514,0x083735BC if n<=1 else 0x0837354C)):
   h=long(iw,at);assert half(ew,h-0x02000000+0x10)&2 and long(ew,h-0x02000000)==cb
  if n>=2:assert half(ew,S-0x02000000+0x10)&2 and long(ew,S-0x02000000+4)==0xFF0
  assert oldqa.helpers.png((D/f'{name}.png').read_bytes())==[240,160]and len((D/f'{name}-display.bin').read_bytes())==96
  with zipfile.ZipFile(D/f'{name}.State')as z:
   assert json.loads(z.read('SyncSettings.json'))==sync
   args=json.loads(z.read('UserData.txt'))['o'];assert set(args)=={'$type','output','checkpoint_dir','probe_sha256','boss_authorization'}
   assert args['probe_sha256']==ROM and args['boss_authorization']=='user-approved-development-boss-once-per-stage'
  if n==0:
   for k,b in regions.items():assert b==(D/'checkpoint'/f'13-healthy-activation-{k}.bin').read_bytes()
  if n<=3:
   for k,b in regions.items():assert b==(OLD/f'{name}-{k}.bin').read_bytes()
  if n==1:assert half(ew,Q-0x02000000+0x62)==2120 and half(ew,Q-0x02000000+0x66)==4 and half(ew,P-0x02000000+0x66)==0
  for item in c['events'].split(','):
   if '@'in item:
    kind,observed=item.split('@');assert event(lines,kind)and any(core(x)==int(observed)for x in event(lines,kind))
    assert frame==int(observed)+(0 if kind in('authorized-hp1','bounded-no-completion')else 1)
  snapshots[name]=parsed;ram[name]=regions
  timeline.append(dict(name=name,export_core=frame,events=c['events'],scene_callback=f'{long(ew,S-0x02000000):08X}',timer=half(ew,S-0x02000000+0x18+0x50),flags=f'{half(iw,0x450A):04X}',common=f'{half(iw,0x4506):04X}',control=iw[0x4529],camera=half(iw,0x451E)))
 counts={}
 for row in lines:
  kind=re.match(r'^core=\d+ kind=([^ ]+)',row)[1];counts[kind]=counts.get(kind,0)+1
 expected={'capture':19,'input':88,'frame':185}
 for kind in('authorized-hp1','lethal-pre','lethal-hit','fatal-branch','fatal-adapter','fatal-pair','root5','case5','terminal-route','terminal-entry','phase-85CD0A0','actor-85BDD00','actor-85CDA40','actor-85BE000','actor-85BF204','actor-85CDA70','actor-85BF400','actor-85BF600','phase-85CD120','phase-85CD270','actor-85BE200','actor-85BE600','phase-85CD2B0','camera-capture','camera-adapter','camera-return','actor-85CDA50','actor-85BEA00','phase-85CD340','actor-85CDA60','actor-85BEE00','actor-85BF200','phase-85CD3A0','phase-85CD420','phase-85CD4B0','phase-85CD510','guard-refusal','bounded-no-completion'):expected[kind]=1
 assert counts==expected
 milestones={'actor-85BDD00':69016,'actor-85BE000':69016,'actor-85BF204':69016,'actor-85BF400':69016,'actor-85BF600':69135,'phase-85CD120':69136,'phase-85CD270':69137,'actor-85BE200':69196,'actor-85BE600':69253,'phase-85CD2B0':69261,'phase-85CD340':69262,'actor-85BEE00':69320,'actor-85BF200':69440,'phase-85CD3A0':69441,'phase-85CD420':69501,'phase-85CD4B0':69533,'phase-85CD510':69593}
 for kind,frame in milestones.items():assert core(event(lines,kind)[0])==frame
 assert core(event(lines,'lethal-pre')[0])==69014 and fields(event(lines,'lethal-pre')[0])['computed']=='0000'
 pair=regs(event(lines,'fatal-pair')[0]);assert pair['R4']==P and pair['R5']==AUX and pair['R0']==Q
 assert actors(event(lines,'root5')[0])[0]['HP']=='4'
 cam=event(lines,'camera-capture')[0];ret=event(lines,'camera-return')[0];assert core(cam)==core(ret)==69261
 assert regs(cam)['R1']==268 and fields(ret)['camera']=='268'and fields(ret)['scene52']=='0F58'
 assert 0xF00|(2*268-448)==0xF58
 refusal=event(lines,'guard-refusal')[0];assert core(refusal)==69932 and 'native-guard-aux18-not-upper'in refusal
 r=regs(refusal);assert r['R15']==0x086FF9C4 and r['R14']==0x086FF698
 assert 'prepared=1/08587200 copied=1/08587200'in refusal
 assert 'actor=02011940 cb=085BF600'in refusal and 'links=02011710,02011828'in refusal
 final=ram['18-bounded-no-completion'];iw,ew=final['iwram'],final['ewram'];at=S-0x02000000
 assert long(ew,at)==0x085CD510 and half(ew,at+0x18+0x50)==0 and half(ew,at+0x18+0x52)==0xF58
 assert half(iw,0x450A)==0x1486 and half(iw,0x4506)==0x90 and iw[0x4529]==0 and half(iw,0x451E)==268
 assert long(ew,Q-0x02000000)==0x085BF200 and long(ew,AUX-0x02000000)==0x085BF600
 assert half(ew,P-0x02000000+0x2C)==half(ew,P-0x02000000+0x2E)==0
 assert long(iw,0x2474)==1 and long(iw,0x2478)==0x08587200 and long(iw,0x4574)==0 and long(iw,0x4578)==0x08587200
 failure=(D/'terminal-first-failure.txt').read_text('utf8').splitlines();assert failure[0]=='failure:bounded-no-completion'and failure[2:]==lines[:-1][-256:]
 assert core(lines[-1])==71927 and not(D/'terminal-error.txt').exists()
 return dict(status='ACTUAL_TERMINAL_PALETTE_PROGRESS_AND_REFUSAL_CAPTURE_INTEGRITY_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),launch_sha256=sha(launch_raw),files_verified=187,genuine_states=snapshots,capture_timeline=timeline,
  actual_outcome=launch['outcome'],advances=3000,actual_one_word_ledger=fields(ledger),same88_prefatal_input_records=True,identical_initial_trace_lines=190,
  crossROM_whole_Core_equal_after_only_CRC12_to16=crc_equal,all_five_RAM_equal_previous_trial_first_four_snapshots=True,
  observed_new_native_milestones=milestones,actual_camera=dict(core=69261,R1=268,scene52='0F58'),guard_refusal=dict(core=69932,reason='native-guard-aux18-not-upper',aux18='02011710',aux28='02011828',prepared_and_copied='1/08587200'),
  guard_return_R0_zero_not_directly_logged=True,accepted_queue_or_IRQ_family_observed=False,cleanup_observed=False,actual_mode8_observed=False,
  final_scene_callback='085CD510',final_scene_timer=0,final_flags='1486',final_common='0090',final_control=0,final_HP=[1,0],final_prepared_count=1,final_copied_count=0,final_queue_pointer='08587200',exact_hook_event_counts=counts,
  all19_genuine_states_all5_RAM_exact=True,source_whole_Core_equal=False,CRC_adjusted_source_Core_equal=False,raw_original_Core_differences=rawdiff,CRC_adjusted_Core_differences=differences,CPU_extensions_managed_equal=True,
  source_cause_and_next_patch_separate=True,source_DI_restore_claim=False,inherited_HUD_not_cold_visual_proof=True,terminal_or_IRQ_completion_claim=False,historical_E5_closure_claim=False,
  emulator_launched=False,savestate_loaded=False,guest_memory_written_by_reviewer=False,old_full_suite_rerun=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 report=audit();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS187immutablefiles/19genuineStates;CRC-onlycontrolledprefix;realprogress+actualauxguardrefusal;noIRQcompletion')

if __name__=='__main__':main()
