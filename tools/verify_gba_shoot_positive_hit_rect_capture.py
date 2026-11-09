"""Read-only completed1477 capture audit; controlled comparison with old6D run."""
import argparse
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

import verify_gba_shoot_positive_hit_capture as prior
import verify_gba_shoot_entry_capture_v2 as stateqa

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'build/bizhawk-gba-shoot-positive-hit-rect-20261109-a'
OLD=ROOT/'build/bizhawk-gba-shoot-positive-hit-20261109-a'
ROM='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
P,Q,AUX=prior.P,prior.Q,prior.AUX
sha,half,long,fields=prior.sha,prior.half,prior.long,prior.fields

def rows(text,kind):return [s for s in text.splitlines()if re.match(r'^core=\d+ kind='+kind+r' ',s)]

def audit():
 assert sha(Path(prior.__file__).read_bytes())=='C49AEB9B5A528E714D86E12396A046897259E63C2EA561C1EE8CA681D31A6A2A'
 raw=(D/'launch.json').read_bytes();launch=json.loads(raw)
 assert launch['completed'] and not launch['host_stop_requested'] and not launch['host_deadline_reached']
 assert not launch['visible'] and not launch['physical_background_input'] and not launch['supplied_save_used'] and launch['guest_writes']==[]
 assert launch['outcome']=='failure:bounded-no-completion' and launch['done_text']=='failure:bounded-no-completion\nupdates=0\n'
 inventory={p.relative_to(D).as_posix():sha(p.read_bytes())for p in sorted(D.rglob('*'))if p.is_file()and p.name!='launch.json'}
 assert inventory==launch['files']
 for name,digest in launch['pins'].items():assert sha((ROOT/name).read_bytes())==digest
 assert len(launch['pins'])==4
 assert sha((ROOT/'build/run_gba_shoot_positive_hit_rect_20261109.py').read_bytes())==launch['launcher_sha256']=='03CAD24CCD2FCB46C5DBC5DF6F2E37BF577B1C7CEF4B91F3F5D4C49F2E6AF434'
 assert sha((ROOT/'build/gba-shoot-positive-hit-rect-pins-20261109.json').read_bytes())==launch['reviewed_pins_sha256']=='5808FFEBBD2183EC574FE6F31EE0A1D009E472528728D3937393E4EA379EA603'
 rom=(D/'loaded-rom.bin').read_bytes();assert rom==(D/'probe.gba').read_bytes()and sha(rom)==launch['rom_sha256']==ROM
 assert all(launch[k]for k in('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged'))
 original=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
 for name,digest in launch['checkpoint_pins'].items():
  assert sha((D/'checkpoint'/name).read_bytes())==sha((original/name).read_bytes())==sha((OLD/'checkpoint'/name).read_bytes())==digest
 cfg=json.loads((D/'config.json').read_text('utf8'))
 assert all(cfg[k]is False for k in('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
 assert all(v['Path'].startswith('W:/build/'+D.name+'/data/')for v in cfg['PathEntries']['Paths'])
 source_blob=(D/'checkpoint/healthy-activation.State').read_bytes();source_core,_=stateqa.checkpoint_core(source_blob)
 restored_core,_=stateqa.checkpoint_core((D/'restored.State').read_bytes())
 assert (D/'restored.State').read_bytes()==(D/'00-before.State').read_bytes()
 assert sha(source_core)==launch['source_core_sha256']=='6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
 assert len(source_core)==len(restored_core)
 crc_expected=bytearray(source_core);struct.pack_into('<I',crc_expected,12,zlib.crc32(rom))
 differences=[dict(offset=i,expected=a,actual=b)for i,(a,b)in enumerate(zip(crc_expected,restored_core))if a!=b]
 raw_differences=[dict(offset=i,original=a,actual=b)for i,(a,b)in enumerate(zip(source_core,restored_core))if a!=b]
 assert differences==launch['all_Core_byte_differences']
 assert (restored_core==crc_expected)==launch['restored_core_exact_except_current_rom_crc']
 assert sha(restored_core)==launch['restored_core_sha256'] and sha(crc_expected)==launch['expected_restored_core_sha256']
 length=long(source_core,0)
 assert source_core[0x24:0x134]==restored_core[0x24:0x134] and launch['CPU_bank_equal']
 assert source_core[4+0x61000:4+length]==restored_core[4+0x61000:4+length] and launch['native_extensions_equal']
 assert source_core[4+length:]==restored_core[4+length:] and launch['managed_suffix_equal']
 old_launch_raw=(OLD/'launch.json').read_bytes();old_launch=json.loads(old_launch_raw)
 assert sha((ROOT/'build/gba-shoot-positive-hit-capture-qa-20261109/final-report.json').read_bytes())=='D240D22DB04A801DB70753C7B0B64D1B413C16F430F7FCF2B37CB75F3103EA2C'
 old_restored,_=stateqa.checkpoint_core((OLD/'restored.State').read_bytes())
 assert sha(old_restored)==old_launch['restored_core_sha256']=='924A0DCF506D60EA7E9FD564114E9D843DB5371F58D0F2B543820D773DC6A45A'
 controlled_expected=bytearray(old_restored);struct.pack_into('<I',controlled_expected,12,zlib.crc32(rom))
 assert restored_core==controlled_expected,'whole new/old restored Core equal after only ROM CRC12:16; no audio normalization'
 snapshots={}
 with zipfile.ZipFile(io.BytesIO(source_blob))as z:sync=json.loads(z.read('SyncSettings.json'))
 for label,frame in(('00-before',68927),('bounded-no-completion',70127)):
  regions={k:(D/f'{label}-{k}.bin').read_bytes()for k in stateqa.OFFSETS};iw,ew=regions['iwram'],regions['ewram']
  meta=prior.metadata(iw,ew,frame)
  parsed=stateqa.parse_checkpoint((D/f'{label}.State').read_bytes(),meta,regions,rom)
  with zipfile.ZipFile(D/f'{label}.State')as z:
   assert json.loads(z.read('SyncSettings.json'))==sync
   bag=json.loads(z.read('UserData.txt'))['o'];assert set(bag)=={'$type','output','checkpoint_dir','probe_sha256'}
   assert bag['probe_sha256']==ROM and bag['output']=='W:/build/'+D.name
  assert parsed['state']['P1HP']==4 and parsed['state']['P2HP']==37 and parsed['state']['stage']==11 and parsed['state']['mode']==7
  for global_at,cb in((0x4510,0x08374FF4),(0x4514,0x083735BC)):
   h=long(iw,global_at);assert half(ew,h-0x02000000+0x10)&2 and long(ew,h-0x02000000)==cb
  for k,b in regions.items():
   if label=='00-before':assert b==(D/'checkpoint'/f'13-healthy-activation-{k}.bin').read_bytes()==(OLD/f'00-before-{k}.bin').read_bytes()
  snapshots[label]={'genuine_state':parsed,'PNG_dimensions':prior.png((D/f'{label}.png').read_bytes())}
 trace=(D/'positive-hit-trace.txt').read_text('utf8');inputs=rows(trace,'input');frames=rows(trace,'frame')
 assert len(inputs)==len(frames)==1200
 oldtrace=(OLD/'positive-hit-trace.txt').read_text('utf8');oldinputs=rows(oldtrace,'input');oldframes=rows(oldtrace,'frame')
 assert len(oldinputs)==239 and inputs[:239]==oldinputs,'all previous239 inputs are identical'
 assert sha((OLD/'positive-hit-trace.txt').read_bytes())==old_launch['files']['positive-hit-trace.txt']
 ew=(D/'00-before-ewram.bin').read_bytes();previous_xy=[half(ew,P-0x02000000+0x34),half(ew,Q-0x02000000+0x34)]
 counts={'A':0,'B':0,'Left':0,'Right':0}
 for index,(i,f)in enumerate(zip(inputs,frames),1):
  m=re.fullmatch(r'core=(\d+) kind=input relative=(\d+) A=(true|false) B=(true|false) Left=(true|false) Right=(true|false)',i);assert m
  a,b,left,right=[x=='true'for x in m.groups()[2:]]
  assert int(m[1])==68926+index and int(m[2])==index and f.startswith('core='+str(68927+index)+' ')
  assert a==((index-1)%60==0)and b==(index>=7 and(index-7)%12==0)
  dx=previous_xy[1]-previous_xy[0]
  assert left==(index>6 and abs(dx)>0x180 and dx<0)and right==(index>6 and abs(dx)>0x180 and dx>0)
  actors=f.split(' actor=',1)[1].split(' | actor=');p,q=fields(actors[0]),fields(actors[1])
  assert int(p['hp'])==4 and int(q['hp'])==37
  assert int(p['held'],16)&0xC0==((0x40 if a else 0)|(0x80 if b else 0))
  previous_xy=[int(p['xy'].split(',')[0]),int(q['xy'].split(',')[0])]
  for k,v in zip(counts,(a,b,left,right)):counts[k]+=v
 failures=rows(trace,'bounded-no-completion');assert len(failures)==1 and failures[0].startswith('core=70127 ')
 first=(D/'positive-hit-first-failure.txt').read_text('utf8')
 assert first=='failure:bounded-no-completion\n'+trace.split('core=70127 kind=capture ',1)[0]
 assert (D/'shoot-positive-hit-done.txt').read_text('utf8')==launch['done_text']
 absent=('invalid-dispatch-target','first-invalid-producer','invalid-overlap','invalid-scratch-type','player-death','player-loss',
  'damage-pre','first-positive-hit','nonfatal-hook','adapter-entry','flash-eight','timer-store','expiry-entry','flash-expired')
 assert all(not rows(trace,k)for k in absent)
 captures=[fields(s)for s in rows(trace,'capture')]
 assert [c['name']for c in captures]==['00-before','bounded-no-completion']
 assert captures[-1]['observed_core']==captures[-1]['export_core']=='70127'
 assert len([f for f in frames if f.startswith('core=69166 ')])==1
 matched_prefix=0
 for a,b in zip(frames,oldframes):
  if a!=b:break
  matched_prefix+=1
 return dict(status='RECTANGLE_TRIAL_BOUNDED_CAPTURE_INTEGRITY_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),
  launch_sha256=sha(raw),files_verified=len(inventory),current_script_pins_verified=len(launch['pins']),
  source_whole_Core_sha256=sha(source_core),actual_restored_Core_sha256=sha(restored_core),
  exact_original_Core_equal=restored_core==source_core,strict_CRC_only_expected_Core_equal=restored_core==crc_expected,
  actual_raw_Core_differences=raw_differences,actual_Core_differences_vs_CRC_expected=differences,
  controlled_old6D_Core_equal_except_only_ROM_CRC=True,no_audio_or_other_state_normalization=True,
  initial_game_RAM_identical_to_source_and_old_trial=True,snapshots=snapshots,ordinary_input_frames=1200,
  old_first239_inputs_identical=True,old_actor_frame_prefix_equal=matched_prefix,button_pulses=counts,
  prior69165_dispatch_refusal_absent=True,continued_through_prior_boundary_to_core=70127,
  positive_hit_observed=False,flash_expiry_observed=False,P1_death_observed=False,final_P1_HP=4,final_SECOND_HP=37,
  first_failure='bounded-no-completion at70127; scalar prefix equals trace before outer capture',
  final_actor_record=frames[-1],HUD_visual_parity_claim=False,HUD_reason='Inherited source checkpoint VRAM is restored byte-exact',
  emulator_launched=False,savestate_loaded=False,guest_memory_written=False,historical_E5_cause_closed=False,
  limits=['Same initial full Core apart from CRC and same first239 inputs strengthen the controlled boundary comparison.',
   'No positive hit or expiry occurred; later coordinates and auxiliary timer are observations, not automatically bugs.',
   'Strict original-Core equality remains separately reported; no loader or audio-pattern exemption is applied.'])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 report=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS {report["files_verified"]} files;1200 inputs;old239/Core controlled comparison;no hit')

if __name__=='__main__':main()
