"""Independent original-source colors and actual corrected outer caller witness."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROM='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def fields(s):return dict(re.findall(r'(\w+)=([^\s]+)',s))
def color(v):return sum((2*((v>>s)&15)+bool((v>>s)&15))<<d for s,d in ((8,0),(4,5),(0,10)))
GROUPS=(('42',0,16,2,11,0x42,0x08D8AD5C),('62',64,8,2,6,0x62,0x08D8AD8C),('82',96,8,3,7,0x82,0x08D8ADBC),('A2',152,8,4,7,0xA2,0x08D8ADEC),('C2',200,8,3,7,0xC2,0x08D8AE1C))
def expected(rows,event):
 phases=list(map(int,event['counters'].split(',')));gates=[int(v,16) for v in event['gates'].split(',')]
 assert len(phases)==5 and all(0<=v<n for v,n in zip(phases,(8,5,4,7,6)))
 values=[]
 for kind,off,step,phase,n,dst,pc in GROUPS:
  for i in range(n):
   idx=off+step*phases[phase]+i;v=rows[idx]
   if gates[2]:v=(v&0xEEE)>>1
   values.append((kind,0x05000000+dst+2*i,color(v),0x08584200+idx*2+2,pc+4))
 return values
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('capture','source','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();meta=json.loads((a.capture/'launch.json').read_bytes())
 assert meta['completed'] and meta['loaded_rom_exact'] and meta['scripts_unchanged'] and meta['outcome']=='palette-witness-121-frames'
 assert meta['launcher_sha256']=='A36696E07BC2CA71DE2646B99D6EDDAA640B9135672EEF686A0EB199165B51BB'
 blobs={k:(a.capture/k).read_bytes() for k in ('loaded-rom.bin','iraira-palette-witness.txt','iraira-palette-witness-done.txt')}
 assert all(sha(b)==meta['files'][k] for k,b in blobs.items()) and sha(blobs['loaded-rom.bin'])==ROM
 s=a.source.read_bytes();assert sha(s)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7';rows=struct.unpack_from('<256H',s,0x76AD13)
 lines=blobs['iraira-palette-witness.txt'].decode().splitlines();summary=fields(lines[0]);assert summary['samples']=='121' and summary['guest_writes']=='none'
 counts={v['kind']:v for v in (fields(x) for x in lines if x.startswith('count '))}
 for k in ('retail-stage3-handler','retail-gradient-backdrop','legacy-stage-branch'):assert int(counts.get(k,{}).get('total','0'))==0,'wrong stage3 route must be absent'
 assert int(counts['projector-enter']['after_first_clock'])>0 and int(counts['palette-dispatch']['after_first_clock'])>0
 samples=[fields(x) for x in lines if x.startswith('sample ')];assert len(samples)==121
 for n,e in enumerate(samples,1):
  assert int(e['index'])==n and int(e['colors'].split(',')[0],16)==0 and int(e['shadow'],16)==0
  colors=[int(x,16) for x in e['colors'].split(',')];bydst={dst:v for _,dst,v,_,_ in expected(rows,e)}
  assert colors[1:]==[bydst[x] for x in (0x05000042,0x05000082,0x050000C2)],'all sampled physical watched colors match current source phase'
  if n>1:assert int(e['core'])==int(samples[n-2]['core'])+1 and int(e['clock'])==int(samples[n-2]['clock'])-1
 events=[fields(x) for x in lines if x.startswith('seq=')];complete=[];pending=None
 for e in events:
  if e['kind']=='projector-enter':
   assert e['lr']=='080D0BE8' and int(e['pc'],16)==0x08D8AD04
   pending=[e,[]]
  elif pending and e['kind'].startswith('source-store-'):pending[1].append(e)
  elif pending and e['kind']=='projector-exit':
   entry,stores=pending;pending=None
   if not stores:continue
   want=expected(rows,entry);assert len(stores)==len(want)==38
   for store,(kind,dst,value,src,pc) in zip(stores,want):
    assert store['kind']=='source-store-'+kind and int(store['r2'],16)==dst and int(store['r0'],16)==value and int(store['r1'],16)==src and int(store['pc'],16)==pc
    assert store['counters']==entry['counters'] and store['gates']==entry['gates']
   complete.append(dict(core=int(entry['core']),seq=int(entry['seq']),counters=entry['counters'],source_store_operands=38))
 assert complete,'a complete actual projector invocation must be retained'
 result=dict(status='IRAIRA_PALETTE_ACTUAL_SOURCE_PASS',checker_sha256=sha(Path(__file__).read_bytes()),rom_sha256=ROM,physical_source_phase_samples=121,physical_backdrop_black_samples=121,complete_projector_invocations=complete,wrong_retail_stage3_handler_calls=0,
  limits=['All38 actual pre-store operands are source-exact in complete retained invocations; physical bus watches directly cover only color0 and group starts42/82/C2.',
   'This is a bounded palette witness, not another complete campaign or mode20 runtime validation.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
