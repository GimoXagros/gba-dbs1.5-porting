"""Independent immutable actual terminal-trial integrity/stall audit; no emulator."""
import argparse
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

import verify_gba_shoot_positive_hit_capture as helpers
import verify_gba_shoot_entry_capture_v2 as stateqa

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'build/bizhawk-gba-shoot-terminal-20261109-a'
P,Q,AUX=helpers.P,helpers.Q,helpers.AUX
SCENE=0x020121E8
sha,half,long,fields=helpers.sha,helpers.half,helpers.long,helpers.fields
ROM='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'

def event(lines,kind):return [s for s in lines if re.match(r'^core=\d+ kind='+kind+r'( |$)',s)]
def core(row):return int(re.match(r'core=(\d+)',row)[1])
def state_fields(row):return fields(row.split(' | ',1)[0])
def actors(row):return [fields(s)for s in row.split(' | ')[1:]]
def regs(row):return {k:int(v,16)for k,v in fields(row).items()if re.fullmatch(r'R\d+|CPSR|SPSR',k)}

def audit():
 assert sha(Path(helpers.__file__).read_bytes())=='C49AEB9B5A528E714D86E12396A046897259E63C2EA561C1EE8CA681D31A6A2A'
 launch_blob=(D/'launch.json').read_bytes();launch=json.loads(launch_blob)
 assert launch['completed']and launch['outcome']=='failure:bounded-no-completion'
 assert launch['done_text']==(D/'shoot-terminal-done.txt').read_text('utf8')=='failure:bounded-no-completion\n'
 assert not any(launch[k]for k in('visible','physical_background_input','supplied_save_used','host_stop_requested','host_deadline_reached'))
 inventory={p.relative_to(D).as_posix():sha(p.read_bytes())for p in sorted(D.rglob('*'))if p.is_file()and p.name!='launch.json'}
 assert inventory==launch['files']
 for path,digest in launch['pins'].items():assert sha((ROOT/path).read_bytes())==digest
 assert len(launch['pins'])==3 and launch['pins']['tools/bizhawk_probe_gba_shoot_terminal.lua']=='964BC4E16A722D576F3CE4BF7516A1D8495967E33847ACF65515FF35C8AB5C74'
 assert sha((ROOT/'build/run_gba_shoot_terminal_20261109.py').read_bytes())==launch['launcher_sha256']=='914E6A14460DB022B9ACF63C483ABF9E6CB6AFF459EC23D9A036149A6D97C4F0'
 assert sha((ROOT/'build/gba-shoot-terminal-pins-20261109.json').read_bytes())==launch['reviewed_pins_sha256']=='EED7348B69043191C49BFA7BE185C40717A38718DFF50FCB1A4373129BDE5E4E'
 assert all(launch[k]for k in('authorized_write_verified','loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged'))
 rom=(D/'loaded-rom.bin').read_bytes();assert rom==(D/'probe.gba').read_bytes()and sha(rom)==launch['rom_sha256']==ROM
 original=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
 for name,digest in launch['checkpoint_pins'].items():assert sha((D/'checkpoint'/name).read_bytes())==sha((original/name).read_bytes())==digest
 cfg=json.loads((D/'config.json').read_text('utf8'))
 assert all(cfg[k]is False for k in('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
 assert all(e['Path'].startswith('W:/build/'+D.name+'/data/')for e in cfg['PathEntries']['Paths'])
 source_blob=(D/'checkpoint/healthy-activation.State').read_bytes();source_core,_=stateqa.checkpoint_core(source_blob)
 restored_core,_=stateqa.checkpoint_core((D/'restored.State').read_bytes())
 assert (D/'restored.State').read_bytes()==(D/'00-before.State').read_bytes()
 prior_aim=ROOT/'build/bizhawk-gba-shoot-positive-hit-aim-20261109-a'
 assert restored_core==stateqa.checkpoint_core((prior_aim/'restored.State').read_bytes())[0]
 assert sha(source_core)==launch['source_core_sha256']=='6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
 assert sha(restored_core)==launch['restored_core_sha256']=='4A282CF92BD125BC0C9045CF1546482B2AD6AB72DABF2009E4FE22AB5586F783'
 expected=bytearray(source_core);struct.pack_into('<I',expected,12,zlib.crc32(rom))
 rawdiff=[dict(offset=i,original=a,actual=b)for i,(a,b)in enumerate(zip(source_core,restored_core))if a!=b]
 differences=[dict(offset=i,expected=a,actual=b)for i,(a,b)in enumerate(zip(expected,restored_core))if a!=b]
 assert len(source_core)==len(restored_core)and differences==launch['all_Core_byte_differences']and len(differences)==9
 assert restored_core!=expected and not launch['restored_core_exact_except_current_rom_crc']
 assert sha(expected)==launch['expected_restored_core_sha256']
 length=long(source_core,0)
 assert source_core[0x24:0x134]==restored_core[0x24:0x134]and launch['CPU_bank_equal']
 assert source_core[4+0x61000:4+length]==restored_core[4+0x61000:4+length]and launch['native_extensions_equal']
 assert source_core[4+length:]==restored_core[4+length:]and launch['managed_suffix_equal']
 samples={};ram={}
 specs=(('00-before',68927,4,37,0x08374FF4,0x083735BC),('01-authorized-hp1',69000,4,1,0x08374FF4,0x083735BC),
  ('02-lethal-hit',69015,4,0,0x08374FAC,0x0837354C),('03-terminal-route',69016,1,0,0x08374FAC,0x0837354C),('04-bounded-no-completion',71927,1,0,0x08374FAC,0x0837354C))
 with zipfile.ZipFile(io.BytesIO(source_blob))as z:sync=json.loads(z.read('SyncSettings.json'))
 for name,frame,php,qhp,inputcb,battlecb in specs:
  regions={k:(D/f'{name}-{k}.bin').read_bytes()for k in stateqa.OFFSETS};iw,ew=regions['iwram'],regions['ewram']
  parsed=stateqa.parse_checkpoint((D/f'{name}.State').read_bytes(),helpers.metadata(iw,ew,frame),regions,rom)
  assert parsed['state']['P1HP']==php and parsed['state']['P2HP']==qhp and parsed['state']['mode']==7 and parsed['state']['stage']==11
  assert long(iw,0x489C)==P and long(iw,0x48A0)==Q and long(iw,0x4D3C)==AUX
  for a,kind in((P,0),(Q,3),(AUX,6)):
   at=a-0x02000000;header=a-0x18
   assert (header-0x02010000)%0x118==0 and 0<=(header-0x02010000)//0x118<52
   assert half(ew,header-0x02000000+0x10)&2 and half(ew,at+4)&15==kind
  assert ew[P-0x02000000+0x11]==0 and ew[Q-0x02000000+0x11]==15
  for a,v in((P+0x14,P),(P+0x18,Q),(Q+0x14,Q),(Q+0x18,P),(Q+0x28,AUX),(AUX+0x18,P),(AUX+0x28,Q)):
   assert long(ew,a-0x02000000)==v
  for at,cb in((0x4510,inputcb),(0x4514,battlecb)):
   h=long(iw,at);assert half(ew,h-0x02000000+0x10)&2 and long(ew,h-0x02000000)==cb
  assert half(ew,Q-0x02000000+0x62)==2120 and half(ew,Q-0x02000000+0x66)==4 and half(ew,P-0x02000000+0x66)==0
  assert half(iw,0x450A)==6
  assert len((D/f'{name}-display.bin').read_bytes())==0x60 and helpers.png((D/f'{name}.png').read_bytes())==[240,160]
  with zipfile.ZipFile(D/f'{name}.State')as z:
   assert json.loads(z.read('SyncSettings.json'))==sync
   args=json.loads(z.read('UserData.txt'))['o'];assert set(args)=={'$type','output','checkpoint_dir','probe_sha256','boss_authorization'}
   assert args['probe_sha256']==ROM and args['boss_authorization']=='user-approved-development-boss-once-per-stage'
  if name=='00-before':
   for k,b in regions.items():assert b==(D/'checkpoint'/f'13-healthy-activation-{k}.bin').read_bytes()
  samples[name]=parsed;ram[name]=regions
 ledger=(D/'terminal-write-ledger.txt').read_text('utf8').strip();assert ledger==launch['guest_write_ledger']
 values=fields(ledger);assert values==dict(core='69000',actor='02011828',address='0201188C',bytes='2',before='37',requested='1',P1HP='4',P1score='0',left='2120',right='4',attempt_consumed='true',after='1',verified='true')
 assert launch['guest_writes_expected']==[dict(actor='02011828',address='0201188C',bytes=2,before=37,after=1,count=1)]
 lines=(D/'terminal-trace.txt').read_text('utf8').splitlines();counts={}
 for row in lines:
  kind=re.match(r'^core=\d+ kind=([^ ]+)',row)[1];counts[kind]=counts.get(kind,0)+1
 expected_counts={'capture':5,'input':88,'frame':185}
 for k in('authorized-hp1','lethal-pre','lethal-hit','fatal-branch','fatal-adapter','fatal-pair','root5','case5','terminal-route','terminal-entry','phase-85CD0A0','bounded-no-completion'):expected_counts[k]=1
 assert counts==expected_counts,'exactregisteredhookeventset; no inventedlaterIRQ/phase evidence'
 inputs=event(lines,'input');oldinputs=event((prior_aim/'positive-hit-trace.txt').read_text('utf8').splitlines(),'input')
 for n,row in enumerate(inputs,1):
  f=fields(row);old=fields(oldinputs[n-1]);assert core(row)==68926+n and f['relative']==str(n)
  assert f['B']==old['B'] and f['Right']==old['Right']
 assert [core(s)for s in inputs if fields(s)['Right']=='true']==[68927,68928]
 assert [core(s)for s in inputs if fields(s)['B']=='true']==[69000]
 assert lines.index(event(lines,'authorized-hp1')[0])<lines.index(event(lines,'input')[73])
 frames=event(lines,'frame');assert [core(s)for s in frames]==list(range(68928,69015))+list(range(69017,71928,30))
 for row in frames:
  a=actors(row);p,q,aux=a
  assert int(p['held'],16)&0xC0==(0x80 if core(row)==69001 else 0)
  if core(row)==68928:assert p['held']==p['edge']=='0002'
  if core(row)==68929:assert p['held']=='0002'and p['edge']=='0000'
  if core(row)==69000:assert q['HP']=='37'and p['held']==p['edge']=='0000'
  if core(row)==69001:assert q['HP']=='1'and p['held']==p['edge']=='0080'
  if core(row)>=69017:
   s=state_fields(row);assert s['scene']=='020121E8'and s['timer']=='120'and s['scene52']=='0005'and s['common']=='0080'and s['control']=='07'
   assert p['HP']=='1'and q['HP']=='0'and q['cb']=='085BDD00'and aux['cb']=='085BF204'
   assert q['counter']=='26,1,0'and aux['counter']=='FF93,0,0'and p['held']==p['edge']=='0000'
 for name,pc in(('lethal-pre',0x0836E5E8),('lethal-hit',0x0836E5EC),('fatal-branch',0x0836E5F0),('fatal-adapter',0x085CD964)):
  row=event(lines,name)[0];r=regs(row);assert core(row)==69014 and r['R15']==pc and r['R4']==P and r['R5']==Q
 pre=fields(event(lines,'lethal-pre')[0]);assert pre['before']=='1'and pre['damage']=='1'and pre['computed']=='0000'
 pair=event(lines,'fatal-pair')[0];r=regs(pair);assert r['R15']==0x0836E608 and r['R0']==Q and r['R4']==P and r['R5']==AUX
 assert actors(pair)[1]['cb']=='085BDD00'and actors(pair)[2]['cb']=='085BF204'
 root=event(lines,'root5')[0];assert core(root)==69014 and actors(root)[0]['HP']=='4'and regs(root)['R15']==0x083736B4
 case=event(lines,'case5')[0];assert core(case)==69014 and regs(case)['R8']==0x086FC300 and regs(case)['R15']==0x0833FD0C
 entry=event(lines,'terminal-entry')[0];assert core(entry)==69015 and state_fields(entry)['scene']=='020121E8'and regs(entry)['R15']==0x085CD004
 phase=event(lines,'phase-85CD0A0')[0];assert core(phase)==69015 and state_fields(phase)['timer']=='121'and actors(phase)[0]['HP']=='1'
 frozen=[]
 a,b=ram['03-terminal-route']['ewram'],ram['04-bounded-no-completion']['ewram']
 for h in(SCENE,P-0x18,Q-0x18,AUX-0x18):
  at=h-0x02000000;assert a[at:at+0x118]==b[at:at+0x118];frozen.append(f'{h:08X}')
 at=SCENE-0x02000000
 assert long(b,at)==0x085CD0A0 and long(b,at+4)==0xFF0 and half(b,at+0x10)&2 and half(b,at+0x18+0x50)==120 and half(b,at+0x18+0x52)==5
 captures=event(lines,'capture');assert [fields(s)['name']for s in captures]==[s[0]for s in specs]
 assert [core(s)for s in captures]==[s[1]for s in specs]
 assert fields(captures[2])['events']=='lethal-hit@69014,fatal-pair@69014,root5@69014,case5@69014'
 assert fields(captures[3])['events']=='terminal-route@69015,terminal-entry@69015,phase-85CD0A0@69015'
 failure=(D/'terminal-first-failure.txt').read_text('utf8').splitlines();assert failure[0]=='failure:bounded-no-completion'and failure[2:]==lines[:-1][-256:]
 assert not (D/'terminal-error.txt').exists()
 return dict(status='ACTUAL_TERMINAL_BOUNDED_STALL_CAPTURE_INTEGRITY_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),launch_sha256=sha(launch_blob),files_verified=len(inventory),snapshots=samples,
  actual_outcome=launch['outcome'],advances=3000,prefatal_input_records=88,prefatal_policy_identical_to_successful_aim=True,native_Right2_and_fresh_B80_edge_verified=True,
  authorized_write_ledger=values,word_neighbors_verified_from_ledger_and_snapshots=True,independent_same_epoch_before_write_full_RAM_dump=False,
  actual_lethal_core=69014,actual_damage=1,SECOND_HP_before=1,SECOND_HP_after=0,P1_HP_at_root5=4,native_P1_HP1_observed_core=69015,
  native_scene_entry_core=69015,outer_scene_capture_core=69016,final_capture_core=71927,scene_header='020121E8',scene_callback='085CD0A0',scene_timer=120,
  full_0x118_byte_slots_equal_69016_to_71927=frozen,unchanged_slot_boundary_distance_frames=2911,
  later_actor_entry_hook_calls=0,IRQ_guard_or_family_hook_calls=0,cleanup_hook_calls=0,actual_mode8_observed=False,
  actor_entry_absence_is_hook_observation_not_complete_cpu_trace=True,aux18_FIRST_retained=True,known_aux_guard_predicate_not_reached=True,
  exact_trace_event_counts=counts,all5_RAM_exact_for_all5_genuine_states=True,
  source_whole_Core_equal=False,CRC_adjusted_whole_Core_equal=False,raw_original_Core_differences=rawdiff,CRC_adjusted_Core_differences=differences,
  whole_restored_Core_equal_previous_1477_success_trial=True,CPU_extensions_managed_equal=True,
  inherited_HUD_not_cold_visual_proof=True,terminal_or_IRQ_completion_claim=False,historical_E5_closure_claim=False,
  source_cause_analysis_separate=True,emulator_launched=False,savestate_loaded=False,guest_memory_written_by_reviewer=False,old_full_suite_rerun=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 report=audit();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print('PASS immutableactualterminalcapture;real1to0/fatal/scene;3000boundstalled;all5genuineStates5RAMexact')

if __name__=='__main__':main()
