"""Extract/convert source FC Tamer Tag score into a standalone relocatable bundle."""
import argparse,json,struct
from pathlib import Path
from analyze_wsc_evolution_music import extract,sha,WSC_SHA
from analyze_mode23_looped_music import split_track,initial_state,stable_loop,score_track,pcm_data
from build_mode23_audio_assets import Bundle,music_track,sample_blob,noise_pcm,pitch_divisor,TEMPO,WAVE_REUSE,NOISE0_REUSE,BEFORE

def build(source,native):
 assert sha(source)==WSC_SHA and sha(native)==BEFORE
 # Actual constructor source FC/priority4/delay0 and request bit100.
 assert source[0x784D13:0x784D27]==bytes.fromhex('c74402fc00c7440e0400c744060000814c100001')
 bundle=Bundle(bytearray(8),[],[]);freq=round(3072000*4*1024/pitch_divisor(source,0));voice_ids={9:0,10:1,'noise0':2}
 external=[]
 for wave in(9,10):
  payload=sample_blob(pcm_data(source,wave),0,freq);at=WAVE_REUSE[wave]
  assert native[at:at+len(payload)]==payload
  external.append(dict(voice=voice_ids[wave],kind=f'wave{wave}',address=0x08000000+at,bytes=len(payload),sha256=sha(payload)))
 pcm,loop=noise_pcm(0);payload=sample_blob(pcm,loop,freq);assert native[NOISE0_REUSE:NOISE0_REUSE+len(payload)]==payload
 external.append(dict(voice=2,kind='noise0',address=0x08000000+NOISE0_REUSE,bytes=len(payload),sha256=sha(payload)))
 voices=b''.join(bytes((0,60,0,0))+struct.pack('<I',r['address'])+bytes((255,0,255,0))for r in external)
 voice_offset=bundle.append('mode22-FC-voicegroup',voices);tracks=[];source_rows=[]
 for sid in range(0xFC,0x100):
  payload,info=extract(source,sid)
  if sid==0xFF:
   assert payload==bytes.fromhex('00000000ffff')
   data=TEMPO+b'\xB1';details=dict(source_id=sid,kind='source-immediate-end',updates=0)
   source_rows.append(info|dict(header=list(payload[:4]),source_immediate_end=True))
  else:
   _,summary=score_track(payload,info,8);first,repeat,_,_=split_track(payload)
   proof=stable_loop(first,repeat,initial_state(payload),info['hardware_channel'],8)
   assert proof['nonsteady_loop_count']==0 and proof['steady_loop_count']==1 and proof['steady_update_period']==1024
   track=dict(payload=payload,info=info,first=first,repeat=repeat,proof=proof,quiet=False)
   data,details=music_track(source,track,0,1,voice_ids);source_rows.append(summary)
  at=bundle.append(f'mode22-FC-channel-{sid-0xFC}',data)
  if 'loop_offset'in details:bundle.pointer(at+len(data)-4,at+details['loop_offset'])
  tracks.append(details|dict(offset=at,bytes=len(data),sha256=sha(data)))
 assert len({(r['intro_updates'],r['repeat_updates'])for r in tracks[:3]})==1
 song=bundle.append('mode22-FC-song',bytes((4,0,0,128))+bytes(20));bundle.pointer(song+4,voice_offset)
 for i,r in enumerate(tracks):bundle.pointer(song+8+4*i,r['offset'])
 bundle.pointer(0,song)
 assert native[0x37FBB4+8]>=4
 data=bytes(bundle.data)
 report=dict(status='MODE22_FC_STANDALONE_AUDIO',source_sha256=WSC_SHA,native_PCM_input_sha256=BEFORE,builder_sha256=sha(Path(__file__).read_bytes()),bundle_sha256=sha(data),bytes=len(data),source_request=0xFC,source_priority=4,native_player=0,native_song_id=None,table_entry_offset=0,song_header_offset=song,voicegroup_offset=voice_offset,source_tracks=source_rows,tracks=tracks,asset_objects=bundle.objects,local_u32_fixups=bundle.fixups,external_PCM=external,limits=['No song table, native request adapter, ROM allocation or viewer installed.','Source FF track ends immediately; it is not replaced with a silent infinite loop.','Existing verified conversion retains score timing and source PCM; native mixer/envelope/pitch quantization limits remain.','The three audible channels share1024update recurrence after sourceintro; actual playback still needs independent/native validation.'])
 return data,report
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in('source','native','output-dir'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.output_dir.exists();data,report=build(a.source.read_bytes(),a.native.read_bytes());a.output_dir.mkdir(parents=True)
 (a.output_dir/'audio.bin').write_bytes(data);p=a.output_dir/'manifest.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASS',sha(data),sha(p.read_bytes()))
if __name__=='__main__':main()
