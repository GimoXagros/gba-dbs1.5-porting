"""Independent actual aim hit/flash/expiry capture integrity; no emulator."""
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
D=ROOT/'build/bizhawk-gba-shoot-positive-hit-aim-20261109-a'
P,Q,AUX=helpers.P,helpers.Q,helpers.AUX
sha,half,long,fields=helpers.sha,helpers.half,helpers.long,helpers.fields
ROM='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'

def actor_rows(row):return [fields(x)for x in row.split(' actor=',1)[1].split(' | actor=')]
def events(lines,kind):return [(n,s)for n,s in enumerate(lines)if re.match(r'^core=\d+ kind='+kind+r'( |$)',s)]
def reg_after(lines,n):
 assert lines[n+1].startswith('regs ')
 return {k:int(v,16)for k,v in fields(lines[n+1]).items()}
def frame(row):return int(re.match(r'core=(\d+)',row)[1])

def audit():
 assert sha(Path(helpers.__file__).read_bytes())=='C49AEB9B5A528E714D86E12396A046897259E63C2EA561C1EE8CA681D31A6A2A'
 launch_raw=(D/'launch.json').read_bytes();launch=json.loads(launch_raw)
 assert launch['completed'] and launch['outcome']=='positive-hit-flash-expired'
 assert not launch['host_stop_requested'] and not launch['host_deadline_reached'] and not launch['visible']
 assert not launch['physical_background_input'] and not launch['supplied_save_used'] and launch['guest_writes']==[]
 inventory={p.relative_to(D).as_posix():sha(p.read_bytes())for p in sorted(D.rglob('*'))if p.is_file()and p.name!='launch.json'}
 assert inventory==launch['files']
 for name,digest in launch['pins'].items():assert sha((ROOT/name).read_bytes())==digest
 assert len(launch['pins'])==4
 assert sha((ROOT/'build/run_gba_shoot_positive_hit_aim_20261109.py').read_bytes())==launch['launcher_sha256']=='50A7CDA6B589EA2FF80B0F613C118934D82CAE597980B14CA4A3EE9DAB1E31C9'
 assert sha((ROOT/'build/gba-shoot-positive-hit-aim-pins-20261109.json').read_bytes())==launch['reviewed_pins_sha256']=='377A8CCA68A09E7FDA1267F6BDD9EEC5FF19EF0A30C2C8CE6B5B58A641A4FC27'
 rom=(D/'loaded-rom.bin').read_bytes();assert rom==(D/'probe.gba').read_bytes()and sha(rom)==launch['rom_sha256']==ROM
 assert all(launch[k]for k in('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged'))
 original=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
 for name,digest in launch['checkpoint_pins'].items():assert sha((D/'checkpoint'/name).read_bytes())==sha((original/name).read_bytes())==digest
 cfg=json.loads((D/'config.json').read_text('utf8'))
 assert all(cfg[k]is False for k in('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
 assert all(v['Path'].startswith('W:/build/'+D.name+'/data/')for v in cfg['PathEntries']['Paths'])
 source_blob=(D/'checkpoint/healthy-activation.State').read_bytes();source_core,_=stateqa.checkpoint_core(source_blob)
 restored_core,_=stateqa.checkpoint_core((D/'restored.State').read_bytes())
 assert (D/'restored.State').read_bytes()==(D/'00-before.State').read_bytes()
 assert sha(source_core)==launch['source_core_sha256']=='6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
 assert len(source_core)==len(restored_core)
 expected=bytearray(source_core);struct.pack_into('<I',expected,12,zlib.crc32(rom))
 rawdiff=[dict(offset=i,original=a,actual=b)for i,(a,b)in enumerate(zip(source_core,restored_core))if a!=b]
 crcdiff=[dict(offset=i,expected=a,actual=b)for i,(a,b)in enumerate(zip(expected,restored_core))if a!=b]
 assert crcdiff==launch['all_Core_byte_differences'] and (restored_core==expected)==launch['restored_core_exact_except_current_rom_crc']
 assert sha(restored_core)==launch['restored_core_sha256'] and sha(expected)==launch['expected_restored_core_sha256']
 length=long(source_core,0)
 assert source_core[0x24:0x134]==restored_core[0x24:0x134]and launch['CPU_bank_equal']
 assert source_core[4+0x61000:4+length]==restored_core[4+0x61000:4+length]and launch['native_extensions_equal']
 assert source_core[4+length:]==restored_core[4+length:]and launch['managed_suffix_equal']
 previous_trial=ROOT/'build/bizhawk-gba-shoot-positive-hit-rect-20261109-a'
 old_core,_=stateqa.checkpoint_core((previous_trial/'restored.State').read_bytes())
 assert restored_core==old_core,'same-ROM restored initial whole Core identical to bounded trial, no normalization'
 snapshots={};region_data={}
 with zipfile.ZipFile(io.BytesIO(source_blob))as z:sync=json.loads(z.read('SyncSettings.json'))
 for label,core,hp,timer in(('00-before',68927,37,0),('first-positive-hit',69015,36,8),('flash-eight',69015,36,8),('flash-expired',69023,36,0)):
  regions={k:(D/f'{label}-{k}.bin').read_bytes()for k in stateqa.OFFSETS};iw,ew=regions['iwram'],regions['ewram']
  parsed=stateqa.parse_checkpoint((D/f'{label}.State').read_bytes(),helpers.metadata(iw,ew,core),regions,rom)
  assert parsed['state']['P1HP']==4 and parsed['state']['P2HP']==hp and parsed['state']['mode']==7 and parsed['state']['stage']==11
  assert half(ew,Q-0x02000000+0x74)==timer and long(iw,0x489C)==P and long(iw,0x48A0)==Q and long(iw,0x4D3C)==AUX
  assert half(iw,0x450A)==6 and half(iw,0x4D40)==0
  for actor,kind in((P,0),(Q,3),(AUX,6)):
   offset=actor-0x02000000;header=actor-0x18
   assert (header-0x02010000)%0x118==0 and 0<=(header-0x02010000)//0x118<52
   assert half(ew,header-0x02000000+0x10)&2 and half(ew,offset+4)&15==kind
  assert ew[P-0x02000000+0x11]==0 and ew[Q-0x02000000+0x11]==15
  assert long(ew,P-0x02000000+0x14)==P and long(ew,P-0x02000000+0x18)==Q
  assert long(ew,Q-0x02000000+0x14)==Q and long(ew,Q-0x02000000+0x18)==P
  assert long(ew,Q-0x02000000+0x28)==AUX and long(ew,AUX-0x02000000+0x18)==P and long(ew,AUX-0x02000000+0x28)==Q
  for global_at,callback in((0x4510,0x08374FF4),(0x4514,0x083735BC)):
   h=long(iw,global_at);assert half(ew,h-0x02000000+0x10)&2 and long(ew,h-0x02000000)==callback
  assert long(ew,Q-0x02000000+0xF0)==0x085D0000 and long(ew,Q-0x02000000+0xF4)==0x085D1000
  assert long(ew,AUX-0x02000000+0xF0)==0x085D029C and long(ew,AUX-0x02000000+0xF4)==0x085D1100
  with zipfile.ZipFile(D/f'{label}.State')as z:
   assert json.loads(z.read('SyncSettings.json'))==sync
   bag=json.loads(z.read('UserData.txt'))['o'];assert set(bag)=={'$type','output','checkpoint_dir','probe_sha256'}
   assert bag['probe_sha256']==ROM and bag['output']=='W:/build/'+D.name
  for k,b in regions.items():
   if label=='00-before':assert b==(D/'checkpoint'/f'13-healthy-activation-{k}.bin').read_bytes()
  snapshots[label]={'genuine_state':parsed,'PNG_dimensions':helpers.png((D/f'{label}.png').read_bytes())};region_data[label]=regions
 assert region_data['first-positive-hit']==region_data['flash-eight']
 assert (D/'first-positive-hit.State').read_bytes()==(D/'flash-eight.State').read_bytes()
 flash=region_data['flash-eight']['palette'];expired=region_data['flash-expired']['palette'];before=region_data['00-before']['palette']
 assert [half(flash,0x222+2*k)for k in range(15)]==[half(rom,0x5C0B08+2*k)for k in range(15)]
 assert [half(expired,0x222+2*k)for k in range(15)]==[half(rom,0x587108+2*k)for k in range(15)]
 assert all(half(flash,32*k)==0x1F for k in range(24))
 assert [half(expired,32*k)for k in range(16)]==[half(before,32*k)for k in range(16)]
 assert [half(expired,32*k)for k in range(1,16)]==[half(rom,0x586F40+2*k)for k in range(1,16)]
 assert half(expired,0)==0x0C63 and half(rom,0x586F40)==0,'outer-frame backdrop differs from immediate restore table; retain timing qualification'
 assert all(half(expired,0x200+32*k)==0x1F for k in range(8)),'OBJ zero entries are not falsely counted as restored'
 text=(D/'positive-hit-trace.txt').read_text('utf8');lines=text.splitlines()
 required=('damage-pre','first-positive-hit','nonfatal-hook','adapter-entry','flash-eight','expiry-entry','flash-expired')
 ev={}
 for name in required:
  matches=events(lines,name);assert len(matches)==1
  n,row=matches[0];ev[name]={'core':frame(row),'fields':fields(row),'registers':reg_after(lines,n)}
 assert ev['damage-pre']['fields']['before']=='37' and ev['damage-pre']['fields']['damage']=='1' and ev['damage-pre']['fields']['computed']=='36'
 for name,pc in(('damage-pre',0x0836E5E8),('first-positive-hit',0x0836E5EC),('nonfatal-hook',0x0836E638),('adapter-entry',0x085CD9A4),('flash-eight',0x085CDA24)):
  r=ev[name]['registers'];assert ev[name]['core']==69014 and r['R4']==P and r['R5']==Q and r['R15']==pc
 assert ev['damage-pre']['registers']['R0']==1 and ev['damage-pre']['registers']['R8']==36
 assert ev['damage-pre']['registers']['R13']==ev['flash-eight']['registers']['R13'],'real native palette argument frame balanced'
 assert ev['expiry-entry']['core']==ev['flash-expired']['core']==69022
 assert ev['expiry-entry']['registers']['R4']==Q and ev['expiry-entry']['registers']['R14']==0x08586C90
 stores=events(lines,'timer-store');assert len(stores)==8
 for index,(n,row)in enumerate(stores,1):
  values=fields(row);r=reg_after(lines,n)
  assert frame(row)==69014+index and int(values['update'])==index and int(values['before'])==9-index and int(values['computed'])==8-index
  assert r['R4']==P and r['R5']==Q and r['R8']==8-index and r['R15']==0x08586C80
 inputs=events(lines,'input');frames=events(lines,'frame');assert len(inputs)==len(frames)==96
 ew0=region_data['00-before']['ewram']
 prev={'cb':f'{long(ew0,P-0x02000000):08X}','freeze':str(half(ew0,P-0x02000000+0x76)),
  'facing':f'{half(ew0,P-0x02000000+0xB4):04X}','held':f'{half(ew0,P-0x02000000+0x2C):04X}',
  'xy':str(half(ew0,P-0x02000000+0x34))+','+str(half(ew0,P-0x02000000+0x36))}
 prevq={'xy':str(half(ew0,Q-0x02000000+0x34))+','+str(half(ew0,Q-0x02000000+0x36)),'event':f'{half(ew0,Q-0x02000000+0xBA):04X}'}
 counts={'Right':0,'B':0};triggers=[]
 for index,((_,inp),(_,fr))in enumerate(zip(inputs,frames),1):
  v=fields(inp);assert frame(inp)==68926+index and int(v['relative'])==index and frame(fr)==68927+index
  assert v['A']==v['Left']=='false';right,b=v['Right']=='true',v['B']=='true'
  ready=int(prev['cb'],16)in(0x0835620C,0x083562B4,0x083562E4)and int(prev['freeze'])==0
  px,py=map(int,prev['xy'].split(','));qx,qy=map(int,prevq['xy'].split(','));dx,dy=qx-px,qy-py
  expect_right=ready and int(prev['facing'],16)&0x4000==0
  expect_b=ready and not expect_right and int(prev['held'],16)&0x80==0 and int(prevq['event'],16)in(1,4,5) and 96<=dx<=384 and 128<=dy<=256
  if frame(inp)>69014:expect_right=expect_b=False
  assert right==expect_right and b==expect_b,'actual policy agrees with recorded callback/freeze/facing/priorheld/window'
  p,q,_=actor_rows(fr);assert int(p['hp'])==4 and int(q['hp'])==(37 if frame(fr)<69015 else 36)
  assert int(p['held'],16)&0xC0==(0x80 if b else 0)
  assert int(p['held'],16)&0xA==(2 if right else 0) and int(p['xy'].split(',')[1])==5376
  if index==1:assert int(p['edge'],16)&2 and int(prev['held'],16)&2==0
  if index==2:assert int(p['edge'],16)&2==0 and int(prev['held'],16)&2
  if b:
   assert int(p['edge'],16)&0x80 and int(prev['held'],16)&0x80==0
   triggers.append({'input_core':frame(inp),'relative':index,'dx':dx,'dy':dy,'event':prevq['event'],'callback':prev['cb']})
  counts['Right']+=right;counts['B']+=b;prev,prevq=p,q
 assert counts=={'Right':2,'B':1}and triggers[0]['input_core']==69000
 assert all(fields(inp)['A']=='false'for _,inp in inputs)
 for failure in('first-invalid-producer','invalid-overlap','invalid-scratch-type','invalid-dispatch-target','player-loss','player-death','bounded-no-completion'):
  assert not events(lines,failure)
 assert not (D/'positive-hit-first-failure.txt').exists()and not(D/'positive-hit-error.txt').exists()
 captures=[fields(row)for _,row in events(lines,'capture')]
 assert [(v['name'],int(v['observed_core']),int(v['export_core']))for v in captures]==[
  ('00-before',68927,68927),('first-positive-hit',69014,69015),('flash-eight',69014,69015),('flash-expired',69022,69023)]
 assert (D/'shoot-positive-hit-done.txt').read_text('utf8')==launch['done_text']=='positive-hit-flash-expired\nupdates=8\n'
 return dict(status='ACTUAL_POSITIVE_HIT_AND_FLASH_EXPIRY_CAPTURE_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),
  launch_sha256=sha(launch_raw),files_verified=len(inventory),script_pins_verified=len(launch['pins']),ordinary_frames=96,
  actual_input_counts=counts,B_triggers=triggers,native_A_mask=0x40,native_B_mask=0x80,A_never_pressed=True,
  actual_direct_FIRST_to_SECOND_hit={'hook_core':69014,'HP_before':37,'damage':1,'HP_after':36,'P1_HP':4},
  actual_hook_evidence=ev,timer_store_cores=list(range(69015,69023)),actual_expiry_core=69022,final_export_core=69023,
  actual_flash_palette_halfwords=15,red_color_zero_entries=24,BG_color_zero_entries_equal_before_at_outer_frame=16,OBJ_color_zero_entries_remaining_red=8,
  BG1_to_15_match_native_restore_table=True,BG0_outer_frame_value=0x0C63,BG0_native_restore_table_value=0,
  actual_palette_argument_frame_balanced=True,snapshots=snapshots,initial_whole_Core_equal_previous1477_trial=True,
  strict_original_Core_equal=restored_core==source_core,strict_CRC_expected_Core_equal=restored_core==expected,
  source_Core_sha256=sha(source_core),actual_restored_Core_sha256=sha(restored_core),raw_original_Core_differences=rawdiff,
  CRC_expected_Core_differences=crcdiff,CPU_extensions_managed_equal=True,
  per_frame_airborne_bit_separately_logged=False,grounding_evidence='Frozen policy checks bit1; recorded ready callback/freeze/facing/window match. No A; recorded player Y constant5376.',
  HUD_cold_entry_visual_proved=False,whole_Shoot_or_E5_closure_claim=False,
  emulator_launched=False,savestate_loaded=False,guest_memory_written=False,old_full_suite_rerun=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true',required=True)
 p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 report=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS{report["files_verified"]}files;actual37→36 hit69014;eightupdates/expiry69022;allstates5RAMexact')

if __name__=='__main__':main()
