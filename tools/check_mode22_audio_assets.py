"""Author check of FC source note timing, actual M4A control flow and PCM imports."""
import argparse,json,struct
from pathlib import Path
from analyze_wsc_evolution_music import extract,sha,WSC_SHA
from verify_mode23_audio_assets import decode_native,source_tick
from build_mode23_audio_assets import WAITS
def main():
 p=argparse.ArgumentParser()
 for n in('source','native','assets','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();s=a.source.read_bytes();native=a.native.read_bytes();raw=(a.assets/'manifest.json').read_bytes();meta=json.loads(raw);blob=(a.assets/'audio.bin').read_bytes()
 assert sha(s)==WSC_SHA and sha(native)==meta['native_PCM_input_sha256']and sha(blob)==meta['bundle_sha256']
 for r in meta['external_PCM']:assert sha(native[r['address']-0x08000000:r['address']-0x08000000+r['bytes']])==r['sha256']
 facts=[]
 for address in(0x08E00000,0x08F00000):
  linked=bytearray(blob)
  for f in meta['local_u32_fixups']:
   assert linked[f['offset']:f['offset']+4]==bytes(4)
   assert 0<=f['relative_target']<len(blob)
   struct.pack_into('<I',linked,f['offset'],address+f['relative_target'])
  for i,row in enumerate(meta['tracks']):
   at=row['offset'];end=at+row['bytes'];notes,ticks,loop_tick,loop_at=decode_native(linked[at:end],WAITS,address+at)
   source,_=extract(s,0xFC+i)
   if i==3:
    assert source==bytes.fromhex('00000000ffff')and not notes and ticks==0 and loop_at is None
    continue
   speed=source[0];current=0;events=[];marker=None
   for op,arg in zip(source[4::2],source[5::2]):
    if op==0xFD:assert arg==0xF0;marker=current
    elif op<0xA0:
     if op&15<12:events.append((source_tick(speed,current),source_tick(speed,current+arg)))
     current+=arg
    elif op in(0xB0,0xFF):pass
    else:assert op in(0xA0,0xA2,0xA3,0xA4,0xA5)or 0xC0<=op<=0xCF
   assert [(n['start'],n['end'])for n in notes]==events
   assert ticks==source_tick(speed,current)and loop_tick==source_tick(speed,marker)and ticks-loop_tick==1024
   assert loop_at==row['loop_offset']
   if address==0x08E00000:facts.append(dict(source_id=0xFC+i,note_count=len(notes),intro_updates=loop_tick,repeat_updates=ticks-loop_tick))
 result=dict(status='MODE22_FC_AUTHOR_PASS',source_sha256=sha(s),manifest_sha256=sha(raw),bundle_sha256=sha(blob),checker_sha256=sha(Path(__file__).read_bytes()),relocations=2,tracks=facts,source_FF_immediate_end=True,exact_external_PCM=3,limits=['Actual M4A bytecode decoded with source note onset/end and loop recurrence; no playback/hardware audio claim.','Native pitch/envelope quantization uses existing converter and remains subject to independent audio review.','No ROM song-table allocation or request adapter installed.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('PASS',sha(a.report.read_bytes()))
if __name__=='__main__':main()
