"""Independent native copy provenance; selector lookup reconstruction is labeled."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def h(b,a): return struct.unpack_from('<H',b,a)[0]
def u(b,a): return struct.unpack_from('<I',b,a)[0]
def need(ok,why):
 if not ok: raise ValueError(why)
def signed(v): return v-65536 if v&32768 else v

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('capture','rom','source','report'): p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();need(not a.report.exists(),'fresh report')
 b=a.rom.read_bytes();s=a.source.read_bytes()
 need(sha(b)=='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F','frozen75BD')
 need(sha(s)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','source1.5')
 journal=(a.capture/'ai-producer-provenance.txt').read_bytes()
 rows=[dict(re.findall(r'(\w+)=([^\s]+)',x)) for x in journal.decode().splitlines() if x.startswith('seq=')]
 need(len(rows)==32 and [int(x['seq']) for x in rows]==list(range(1,33)),'complete32observations')
 need(all((x['stage'],x['cpu'],x['progress'])==('9','14','2') for x in rows),'typed owner')
 need([x['kind'] for x in rows[:5]]==['raw-id','row-index','first-read','first-copy','parameter-copies-complete'],'init ordering')
 need(all(x['core']=='19961' for x in rows[:5]),'same initializer boundary')
 need(rows[0]['raw_id']==rows[1]['effective_id']=='14' and rows[1]['stride']=='17','raw identity used as index')
 row=b[0xC6C7C+14*17:0xC6C7C+15*17]
 need(rows[2]['src']=='080C6D6A' and rows[2]['row17']==row.hex().upper(),'actual out-of-range read')
 need(rows[3]['dst']=='03004D8A' and rows[3]['value']=='E92D' and h(row,0)==0xE92D,'actual first copy')
 copied=bytes.fromhex(rows[4]['params_03004D88'])
 projection=((0,2,2),(2,4,2),(4,6,1),(5,7,1),(6,0x1C,1),(7,0x1D,1),(8,0x1E,1),(9,0x1F,1),(10,0x20,1),(11,0x21,1),(12,0x22,1),(13,8,1),(14,9,1),(15,0x24,1),(16,0x25,1))
 need(all(copied[y:y+n]==row[x:x+n] for x,y,n in projection),'all15 actual parameter field copies')
 need(copied[0x23]==0,'zeroextended parameter field')
 prefix='10-first-invalid-ai-collider-target-'
 iw=(a.capture/(prefix+'iwram.bin')).read_bytes();ew=(a.capture/(prefix+'ewram.bin')).read_bytes()
 need((len(iw),len(ew))==(0x8000,0x40000),'actual RAM extents')
 ai=iw[0x4D88:0x4DAE]
 need(h(ai,10)==14*384,'same unnormalized identity retained for behavior row')
 # This reconstructs the table lookup from the final captured owner fields and
 # the pinned native instructions; it is not an additional executed hook.
 ops={0xC6494:0xE1A01301,0xC64A4:0xE2022003,0xC64B4:0xE1A030A3,
      0xC64B8:0xE0033000,0xC64D0:0xE0833003,0xC64D8:0xE1D880BA,
      0xC64DC:0xE0811008,0xC64E0:0xE0811003,0xC64E8:0xE19100F8,
      0xC6534:0xE1C800B0,0xC6538:0xE3A01012,0xC653C:0xE0010190,
      0xC6990:0xE1D800B0,0xC6994:0xE3A03012,0xC6998:0xE0010093}
 need(all(u(b,at)==op for at,op in ops.items()),'native lookup/copy instructions')
 x,y=signed(h(ai,0x10)),signed(h(ai,0x12));group=2
 if h(ew,0x11828+8)&0x4000:
  if y<=ai[0x1F] and x<=ai[0x21]:group=int(x>ai[0x20])
  group+=3
 elif y<=ai[0x1C] and x<=ai[0x1E]:group=int(x>ai[0x1D])
 difficulty=h(iw,0x4DC4)&3;mask=31>>difficulty
 # Native arithmetic LSR sees sign-extended random owner, followed by mask.
 bucket=(signed(h(iw,0x4DB2))>>1)&mask
 if difficulty==3 and ew[0x11710+0x6E]==8:bucket+=4
 address=u(b,0xC658C)+h(ai,10)+group*64+bucket*2
 action=h(b,address-0x08000000)
 need((address,action)==(0x080C554A,0xFFFF),'reconstructed invalid behavior selection')
 selected=rows[28]
 need(selected['kind']=='selector-write' and selected['reported_pc']=='080110EC' and selected['lr']=='080C69B8','actual native copy writer')
 need(selected['r1']=='0011FFEE' and int(selected['r1'],16)==action*18,'actual action offset')
 base=u(b,0xC6A3C);src=base+action*18
 need(base==0x080C4FC4 and src==0x081E4FB2,'actual action literal and bad source')
 need(int(selected['r4'],16)==src+2 and selected['r5']=='03003D50','copy source postincrement and destination')
 need(iw[0x3D50:0x3D62]==b[src-0x08000000:src-0x08000000+18],'all18 copied action bytes')
 need(selected['value']=='000F' and selected['old']=='0000' and h(iw,0x3D50)==15,'first invalid selector write')
 need(all(x['core']=='20165' for x in rows[28:]),'copy-to-target same boundary')
 need(rows[29]['motion']=='FFFF' and rows[30]['index']=='0F' and rows[31]['target']=='E3A00000','observed continuation to bad branch')
 need(u(b,0xC65F4+15*4)==0xE3A00000,'invalid slot reads following instruction')
 states=sorted({h(s,0x74D89A+i*18)&255 for i in range(264)})
 need(states==[0,1,2,3,5,6,7,8,9,10],'complete source action state population excludes15')
 behavior=struct.unpack_from('<1920H',s,0x74EB2A)
 need(max(behavior)==262 and all(h(s,0x74D89A+i*18+14)<264 for i in range(264)),'source behavior and continuation indices bounded')
 report=dict(status='AI_BAD_ACTION_COPY_PROVENANCE_PASS',checker_sha256=sha(Path(__file__).read_bytes()),journal_sha256=sha(journal),
   rom_sha256=sha(b),iwram_sha256=sha(iw),ewram_sha256=sha(ew),initial_parameter_fields=15,
   raw_identity=14,behavior_row_offset=14*384,reconstructed_behavior_address=f'{address:08X}',action_index=action,
   observed_action_copy_source=f'{src:08X}',all18_action_bytes_match=True,observed_writer='080110EC; LR080C69B8',
   observed_selector=15,observed_target='E3A00000',source_action_states=states,
   limitations=['Behavior selection address is reconstructed from captured owner fields, not directly observed at a hook.',
     'Parameter corruption and behavior offset both originate in unnormalized ID14; no assertion that a particular corrupted threshold alone caused the branch.',
     'No repaired runtime or complete campaign success is claimed.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(report['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
