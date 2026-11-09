"""Read-only integrity audit of the preserved first positive-hit trial failure."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib
import io
import zipfile

import verify_gba_shoot_entry_capture_v2 as stateqa

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'build/bizhawk-gba-shoot-positive-hit-20261109-a'
P,Q,AUX=0x02011710,0x02011828,0x02011940
EXPECTED_REGS={'R0':0,'R1':0xFFFFFFF0,'R4':0x020112B0,'R5':P,'R8':0x0836EBA8,
 'R9':0x0A000003,'R14':0x08353FF0,'R15':0x0836EBA8}

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def half(b,a):return struct.unpack_from('<H',b,a)[0]
def long(b,a):return struct.unpack_from('<I',b,a)[0]
def fields(s):return dict(re.findall(r'(\w+)=([^ ]+)',s))
def png(blob):
 assert blob[:8]==b'\x89PNG\r\n\x1a\n' and blob[12:16]==b'IHDR'
 return list(struct.unpack_from('>II',blob,16))

def metadata(iw,ew,frame):
 return dict(core=str(frame),mode=str(half(iw,0x2310)),stage=str(iw[0x231E]),difficulty=str(iw[0x231F]),
  progress=f'{half(iw,0x232A):04X}',FIRST=f'{long(iw,0x489C):08X}',SECOND=f'{long(iw,0x48A0):08X}',
  flags=f'{half(iw,0x450A):04X}',P1HP=str(half(ew,P-0x02000000+0x64)),
  P2HP=str(half(ew,Q-0x02000000+0x64)),fighter=str(ew[P-0x02000000+0x11]),
  base=str(half(ew,P-0x02000000+8)>>8&1),input_task=f'{long(iw,0x4510):08X}',battle_task=f'{long(iw,0x4514):08X}')

def audit():
 d=DIRECTORY;launch_blob=(d/'launch.json').read_bytes();launch=json.loads(launch_blob)
 assert launch['completed'] and not launch['host_stop_requested'] and not launch['host_deadline_reached']
 assert not launch['visible'] and not launch['physical_background_input'] and not launch['supplied_save_used']
 assert launch['guest_writes']==[] and launch['outcome']=='failure:invalid-dispatch-target'
 actual={p.relative_to(d).as_posix():sha(p.read_bytes())for p in sorted(d.rglob('*'))if p.is_file()and p.name!='launch.json'}
 assert actual==launch['files'],'complete file inventory'
 for name,digest in launch['pins'].items():assert sha((ROOT/name).read_bytes())==digest
 host=ROOT/'build/run_gba_shoot_positive_hit_20261109.py'
 assert sha(host.read_bytes())==launch['launcher_sha256']=='036CC0E31CB4BB3032FF9614AFA40FFADF0BADF2C8968E9575BDC239C5446E0F'
 assert sha((ROOT/'build/gba-shoot-positive-hit-pins-20261109.json').read_bytes())==launch['reviewed_pins_sha256']=='2A85C6EF8E6AA0913F7B14BB14DE4172D6A8F6CEB08874C908D71260D0B2F1FD'
 rom=(d/'probe.gba').read_bytes()
 assert sha(rom)==launch['rom_sha256']=='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
 assert (d/'loaded-rom.bin').read_bytes()==rom and all(launch[k]for k in('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged'))
 original=ROOT/'build/bizhawk-gba-shoot-entry-replay-20261109-a'
 for name,digest in launch['checkpoint_pins'].items():
  assert sha((d/'checkpoint'/name).read_bytes())==sha((original/name).read_bytes())==digest
 cfg=json.loads((d/'config.json').read_text('utf8'))
 assert all(cfg[k]is False for k in('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled'))
 for row in cfg['PathEntries']['Paths']:assert row['Path'].startswith('W:/build/'+d.name+'/data/')
 source_state=(d/'checkpoint/healthy-activation.State').read_bytes()
 source_core,_=stateqa.checkpoint_core(source_state)
 restored=(d/'restored.State').read_bytes();restored_core,_=stateqa.checkpoint_core(restored)
 assert sha(source_core)==launch['source_core_sha256']=='6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'
 assert restored==(d/'00-before.State').read_bytes()
 assert len(restored_core)==len(source_core)
 expected=bytearray(source_core);struct.pack_into('<I',expected,12,zlib.crc32(rom))
 original_differences=[dict(offset=i,original=a,actual=b)for i,(a,b)in enumerate(zip(source_core,restored_core))if a!=b]
 differences=[dict(offset=i,expected=a,actual=b)for i,(a,b)in enumerate(zip(expected,restored_core))if a!=b]
 assert differences==launch['all_Core_byte_differences']
 assert [v['offset']for v in differences]==[326,327,330,342,343,384,385,393,397]
 assert (restored_core==expected)==launch['restored_core_exact_except_current_rom_crc']==False
 assert sha(restored_core)==launch['restored_core_sha256'] and sha(expected)==launch['expected_restored_core_sha256']
 length=long(source_core,0)
 assert source_core[0x24:0x134]==restored_core[0x24:0x134] and launch['CPU_bank_equal']
 assert source_core[4+0x61000:4+length]==restored_core[4+0x61000:4+length] and launch['native_extensions_equal']
 assert source_core[4+length:]==restored_core[4+length:] and launch['managed_suffix_equal']
 snapshots={}
 with zipfile.ZipFile(io.BytesIO(source_state))as archive:source_sync=json.loads(archive.read('SyncSettings.json'))
 for label,frame in(('00-before',68927),('invalid-dispatch-target',69166)):
  regions={region:(d/f'{label}-{region}.bin').read_bytes()for region in stateqa.OFFSETS}
  iw,ew=regions['iwram'],regions['ewram'];meta=metadata(iw,ew,frame)
  result=stateqa.parse_checkpoint((d/f'{label}.State').read_bytes(),meta,regions,rom)
  with zipfile.ZipFile(d/f'{label}.State')as archive:
   assert json.loads(archive.read('SyncSettings.json'))==source_sync
   bag=json.loads(archive.read('UserData.txt'))['o']
   assert set(bag)=={'$type','output','checkpoint_dir','probe_sha256'}
   assert bag['output']=='W:/build/'+d.name and bag['checkpoint_dir']=='W:/build/'+d.name+'/checkpoint'
   assert bag['probe_sha256']==launch['rom_sha256']
  assert result['frame']==frame and result['state']['P1HP']==4 and result['state']['P2HP']==37
  assert result['state']['stage']==11 and result['state']['mode']==7
  assert result['state']['flags']==(6 if label=='00-before'else 0x46)
  for region,blob in regions.items():
   if label=='00-before':assert blob==(d/'checkpoint'/f'13-healthy-activation-{region}.bin').read_bytes()
  assert long(iw,0x489C)==P and long(iw,0x48A0)==Q and long(iw,0x4D3C)==AUX
  for global_at,callback in((0x4510,0x08374FF4),(0x4514,0x083735BC)):
   header=long(iw,global_at);assert half(ew,header-0x02000000+0x10)&2
   assert long(ew,header-0x02000000)==callback
  snapshots[label]=dict(genuine_state=result,PNG_dimensions=png((d/f'{label}.png').read_bytes()))
 trace=(d/'positive-hit-trace.txt').read_text('utf8');lines=trace.splitlines()
 first=(d/'positive-hit-first-failure.txt').read_text('utf8')
 assert first.startswith('failure:invalid-dispatch-target\n')
 assert first.split('\n',1)[1]==trace.split('core=69166 kind=frame ',1)[0]
 marker=(d/'shoot-positive-hit-done.txt').read_text('utf8')
 assert marker==launch['done_text']=='failure:invalid-dispatch-target\nupdates=0\n'
 inputs=[];frames=[]
 for row in lines:
  m=re.fullmatch(r'core=(\d+) kind=input relative=(\d+) A=(true|false) B=(true|false) Left=(true|false) Right=(true|false)',row)
  if m:inputs.append((int(m[1]),int(m[2]),*[x=='true'for x in m.groups()[2:]]))
  if re.match(r'^core=\d+ kind=frame ',row):frames.append(row)
 assert len(inputs)==len(frames)==239
 iw=(d/'00-before-iwram.bin').read_bytes();ew=(d/'00-before-ewram.bin').read_bytes()
 previous_positions=[half(ew,P-0x02000000+0x34),half(ew,Q-0x02000000+0x34)]
 ab_counts={'A':0,'B':0}
 for index,((core,n,a,b,left,right),frame_row)in enumerate(zip(inputs,frames),1):
  assert core==68926+index and n==index
  assert a==((index-1)%60==0) and b==(index>=7 and(index-7)%12==0)
  dx=previous_positions[1]-previous_positions[0]
  assert left==(index>6 and abs(dx)>0x180 and dx<0)and right==(index>6 and abs(dx)>0x180 and dx>0)
  assert frame_row.startswith('core='+str(68927+index)+' kind=frame ')
  actors=frame_row.split(' actor=',1)[1].split(' | actor=')
  first_actor,upper_actor=fields(actors[0]),fields(actors[1])
  assert int(first_actor['hp'])==4 and int(upper_actor['hp'])==37
  assert int(first_actor['held'],16)&0xC0==((0x40 if a else 0)|(0x80 if b else 0))
  previous_positions=[int(first_actor['xy'].split(',')[0]),int(upper_actor['xy'].split(',')[0])]
  ab_counts['A']+=a;ab_counts['B']+=b
 failures=[row for row in lines if ' kind=invalid-dispatch-target 'in row]
 assert len(failures)==1 and failures[0].startswith('core=69165 ')
 regrow=lines[lines.index(failures[0])+1];registers={k:int(v,16)for k,v in fields(regrow).items()}
 assert all(registers[k]==v for k,v in EXPECTED_REGS.items())
 captures=[fields(row)for row in lines if ' kind=capture 'in row]
 assert len(captures)==2 and captures[-1]['name']=='invalid-dispatch-target'
 assert captures[-1]['observed_core']=='69165' and captures[-1]['export_core']=='69166'
 assert not any(re.search(r' kind=(damage-pre|first-positive-hit|nonfatal-hook|adapter-entry|flash-eight|timer-store|expiry-entry|flash-expired)\b',row)for row in lines)
 return dict(status='POSITIVE_TRIAL_FAILURE_CAPTURE_INTEGRITY_PASS',launch_sha256=sha(launch_blob),
  verifier_sha256=sha(Path(__file__).read_bytes()),files_verified=len(actual),current_script_pins_verified=len(launch['pins']),
  source_whole_Core_sha256=sha(source_core),actual_restored_Core_sha256=sha(restored_core),
  exact_original_Core_equal=False,strict_CRC_only_expected_Core_equal=False,
  actual_Core_differences_vs_unmodified_original=original_differences,
  actual_Core_differences_vs_CRC_adjusted_source=differences,CPU_extensions_managed_equal=True,
  SyncSettings_equal=True,only_new_userdata_arguments_preserved=True,
  snapshots=snapshots,ordinary_input_frames=239,button_pulses=ab_counts,
  failure_instruction_core=69165,postframe_capture_core=69166,failure_registers=registers,
  immediate_scalar_file_is_exact_pre_export_trace_prefix=True,positive_hit_observed=False,flash_expiry_observed=False,
  no_E5_producer_evidence_in_this_failure=True,dispatcher_causality_inferred=False,
  HUD_visual_parity_claim=False,HUD_reason='Snapshot restores existing VRAM; stale prior score tiles can persist',
  emulator_launched=False,savestate_loaded=False,guest_memory_written=False,
  limits=['Invalid-dispatch observer facts precede instruction; full memory/state is one outer frame later.',
   'R9 mirror/odd address semantics and actual bad-route classification belong to separate source audit.',
   'Full Core differences are retained exactly; no older-loader-pattern exemption or normalization is applied.',
   'Exact snapshots and scripted-input integrity do not establish a successful positive hit or E5 cause.'])

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists(),'fresh report'
 report=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print(f'PASS {report["files_verified"]} files;239 input frames; exact Core differences retained; no positive hit')

if __name__=='__main__':main()
