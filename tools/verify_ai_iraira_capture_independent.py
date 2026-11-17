"""Actual aligned AI source fields and Iraira source-index/owner evidence."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROM='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,why):
 if not ok:raise ValueError(why)
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def fields(line):return dict(re.findall(r'(\w+)=([^\s]+)',line))

def all_parameter_rows(directory,manifest,source):
 rows=[]
 for progress in range(10):
  paths=list(directory.glob(f'*-campaign-active-{progress:02d}-iwram.bin'))
  if not paths:continue
  need(len(paths)==1,'unique normal active snapshot');raw=paths[0].read_bytes()
  need(sha(raw)==manifest['files'][paths[0].name],'actual per-row snapshot pin')
  ident=raw[0x231C];index=7 if ident==11 else ident-5 if ident>=13 else ident
  need(raw[0x232E]==progress and 0<=index<10,'typed normal initializer domain')
  expected=[h(source,0x782970+17*index+x) for x in (0,2)]
  actual=[h(raw,0x4D88+x) for x in (2,4)]
  need(actual==expected,'both actual source halfwords retained at first active')
  rows.append(dict(progress=progress,cpu=ident,normalized=index,source_halfwords=expected,actual_halfwords=actual,snapshot=paths[0].name))
 return dict(complete=len(rows)==10 and {r['normalized'] for r in rows}==set(range(10)),rows=rows)

def ai_proof(raw,rom,source):
 rows=[fields(x) for x in raw.decode().splitlines() if x.startswith('first seq=')];first={x['kind']:x for x in rows}
 required=('raw-id','row-index','first-read','first-copy','parameter-copies-complete','action-first-copy','selector-load','target')
 missing=[x for x in required if x not in first]
 if missing:return dict(status='NOT_OBSERVED',missing=missing,source_parameter_parity=False)
 r=[first[k] for k in required]
 need(all((x['stage'],x['cpu'],x['progress'])==('9','14','2') for x in r),'typed CPU14 Waterfall owner')
 need(r[0]['raw_id']=='14' and r[1]['effective_id']=='9' and r[1]['stride']=='18','actual source ID normalization and even native stride')
 need(r[2]['row_base']=='08D8AB00' and r[2]['offset']=='162' and r[2]['src']=='08D8ABA2','actual aligned source row9')
 row=source[0x782970+9*17:0x782970+10*17]
 need(bytes.fromhex(r[2]['row17'])==row==rom[0xD8ABA2:0xD8ABB3],'original WSC row equals observed loaded row')
 need(r[3]['r0']=='000002E4' and r[3]['dst']=='03004D8A' and r[3]['value']=='02E4','actual full source halfword store replaces old00E4')
 copied=bytes.fromhex(r[4]['params_03004D88'])
 projection=((0,2,2),(2,4,2),(4,6,1),(5,7,1),(6,28,1),(7,29,1),(8,30,1),(9,31,1),(10,32,1),(11,33,1),(12,34,1),(13,8,1),(14,9,1),(15,36,1),(16,37,1))
 need(all(copied[y:y+n]==row[x:x+n] for x,y,n in projection) and copied[35]==0,'all15 actual copied fields source exact')
 need(len({x['core'] for x in r[:5]})==1 and [int(x['seq']) for x in r[:5]]==sorted(int(x['seq']) for x in r[:5]),'same ordered initializer invocation')
 action=r[5];index=int(action['ordinal'],16);src=int(action['src'],16)
 need(0<=index<264 and src==0x08D89800+index*18,'bounded relocated native action copy')
 need(bytes.fromhex(action['action18'])==rom[src-0x08000000:src-0x08000000+18] and int(action['word'],16)==h(rom,src-0x08000000),'actual copy source bytes')
 need(action['bank']=='0D80' and action['lr']=='080C69B8' and action['r5']=='03003D50' and int(action['r4'],16)==src+2,'saved behavior bank and real copy ABI')
 load,tgt=r[6:];dispatch=int(tgt['index'],16)
 need(0<=dispatch<12 and tgt['table']=='080C65F4' and int(tgt['slot'],16)==0x080C65F4+dispatch*4,'bounded native target slot')
 need(int(tgt['target'],16)==int(tgt['word'],16)==u(rom,0xC65F4+dispatch*4),'observed actual native callback')
 need(load['core']==tgt['core'] and load['index']==tgt['index'] and int(action['seq'])<int(load['seq'])<int(tgt['seq']),'copy then load then target ordering')
 return dict(status='ALIGNED_AI_SOURCE_PREFIX_PASS',source_parameter_parity=True,fields_matched=15,initializer_core=int(r[0]['core']),first_halfword=0x2E4,
  action_core=int(action['core']),action_ordinal=index,action_address=action['src'],behavior_bank=0xD80,target=tgt['target'],target_core=int(tgt['core']))

def iraira_proof(directory,manifest,rom,s):
 names=list(directory.glob('*-campaign-active-04-iwram.bin'))
 if not names:return dict(status='NOT_OBSERVED')
 need(len(names)==1,'unique Iraira active snapshot');prefix=names[0].name[:-len('iwram.bin')]
 chunks={}
 for kind in ('iwram','vram','display'):
  name=prefix+kind+'.bin';data=(directory/name).read_bytes();need(sha(data)==manifest['files'][name],'actual snapshot pin '+kind);chunks[kind]=data
 iw,vr,display=(chunks[x] for x in ('iwram','vram','display'))
 need((iw[0x231E],iw[0x231C],iw[0x232E])==(10,11,4),'actual Iraira logical owner')
 owners=[]
 for owner,res,source_res,mapbase,ports in ((0x2338,26,38,0xF000,0x030012B8),(0x2388,25,37,0xF800,0x030012BA)):
  need([u(iw,owner+i) for i in (0,4,8,0x24)]==[ports,ports+1,0x06000000+mapbase,u(rom,0x580000+res*24+8)],'actual resource/owner/map/port routing')
  need((h(iw,owner+0xC),h(iw,owner+0xE))==(2,2),'actual source2x2 geometry')
  owners.append(dict(owner=f'{0x03000000+owner:08X}',source_resource=source_res,native_resource=res,map=f'{0x06000000+mapbase:08X}'))
 need(h(iw,0x2654)==0,'actual source black backdrop global')
 need(h(iw,0x2568) in (0,2),'separate display phase domain')
 counters=[h(iw,0x3D30+2*i) for i in range(5)]
 need(all(0<=v<z for v,z in zip(counters,(8,5,4,7,6))),'compact source palette counter domains')
 # Last17 tile slots belong to the existing shared overlay in actual captures.
 # Validate the dedicated495slots directly against original WSC planar pixels.
 pixels=0
 for tile in range(495):
  for y in range(8):
   for x in range(8):
    expected=sum(((s[0x4C61C0+tile*32+y*4+p]>>(7-x))&1)<<p for p in range(4))
    actual=(vr[0x4000+tile*32+y*4+x//2]>>(4*(x&1)))&15
    need(actual==expected,'actual dedicated VRAM pixel index equals original WSC');pixels+=1
 matched=[]
 for owner in owners:
  base=int(owner['map'],16)-0x06000000;values=struct.unpack_from('<1024H',vr,base)
  start=0 if owner['source_resource']==37 else 4
  source_values=set()
  for k in range(start,start+4):source_values.update(struct.unpack_from('<504H',rom,0x59C100+k*1008))
  overlap=sum(v in source_values for v in values)
  need(any(v!=0 and v in source_values for v in values),'actual nonblank source-resource map cells present')
  matched.append(overlap)
 return dict(status='IRAIRA_SOURCE_PIXELS_AND_OWNERS_PASS',snapshot=prefix[:-1],owners=owners,dedicated_source_pixels=pixels,
  excluded_shared_overlay_slots=17,ringmap_cell_value_membership=matched,palette_counters=counters,phase=h(iw,0x2568),backdrop=h(iw,0x2654),
  limitation='Checks pixel indices and resource ownership, not full raster composition or exact ringmap coordinate order; shared overlay and dynamic palette/clock/visuals separately audited.')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('capture','source','report'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report');j=json.loads((a.capture/'launch.json').read_bytes())
 need(j['completed'] and j['loaded_rom_exact'] and j['scripts_unchanged'] and not j['host_stop_requested'] and not j['host_deadline_reached'],'finalized capture only')
 need(j['launcher_sha256']=='2E68861ADF5D4CC5BC9CFE404557D62F37DDCAD54EFA3227DF8A2B9460161140' and j['pins']['tools/bizhawk_probe_ai_aligned_iraira.lua']=='C32E0C08B82F5EBC805387C25990B6FC9C4C0A6056E84412D020A83266872860','reviewed host and observer')
 blobs={n:(a.capture/n).read_bytes() for n in ('loaded-rom.bin','ai-producer-provenance.txt','campaign-complete-done.txt','type8-event-provenance.txt')}
 need(all(sha(b)==j['files'][n] for n,b in blobs.items()),'frozen actual evidence pins');rom=blobs['loaded-rom.bin'];need(sha(rom)==ROM,'actual3FE5')
 s=a.source.read_bytes();need(sha(s)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','immutable original source')
 ai=ai_proof(blobs['ai-producer-provenance.txt'],rom,s);iraira=iraira_proof(a.capture,j,rom,s);population=all_parameter_rows(a.capture,j,s)
 outcome=blobs['campaign-complete-done.txt'].decode().strip();need(outcome==j['outcome'],'honest final outcome')
 match=re.search(rb'^first-chain count=(\d+)$',blobs['type8-event-provenance.txt'],re.M)
 result=dict(status='AI_IRAIRA_SCOPED_ACTUAL_PASS' if ai['status'].endswith('PASS') and iraira['status'].endswith('PASS') else 'SCOPED_WITNESS_NOT_OBSERVED',
  checker_sha256=sha(Path(__file__).read_bytes()),rom_sha256=sha(rom),ai=ai,all_ten_parameter_rows=population,iraira=iraira,campaign_outcome=outcome,
  type8_chain_rows=int(match.group(1)) if match else None,limitations=['Full campaign, clock, phase, palette and visual acceptance remain separate QA.','A type8 event16 claim requires its own chain; this report does not infer it from campaign progress.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
