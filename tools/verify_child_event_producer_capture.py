"""Bind actual unsupported child event to its callback writer and source branch."""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROM='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PROBE='B01A4F35A77D9CB7E24173E73C6D85818FBF8A3563B29FE55E69294EBCA7A9F9'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def row(line):
 pairs=re.findall(r'(\w+)=([^\s]+)',line);result=dict(pairs)
 kinds=[v for k,v in pairs if k=='kind']
 if len(kinds)>1:result['actor_kind']=kinds[-1]
 if kinds:result['kind']=kinds[0]
 return result
def hx(r,k):return int(r[k],16)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 folder=args.capture;raw=(folder/'launch.json').read_bytes();launch=json.loads(raw)
 assert launch['completed'] and launch['outcome']=='invalid-child-event-captured'
 assert launch['launcher_sha256']=='C8EE8525013740555C7A4E2D9D7F186418493A49501D62A07E3D5C252F75DC9E'
 assert launch['pins']['tools/bizhawk_probe_child_event_producer.lua']==PROBE
 assert launch['rom_sha256']==ROM and launch['guest_writes']==[] and not launch['visible'] and not launch['physical_background_input'] and not launch['supplied_save_used']
 for k in ('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged','CPU_bank_equal','native_extensions_equal','managed_suffix_equal'):assert launch[k],k
 for name,digest in launch['files'].items():assert sha((folder/name).read_bytes())==digest,name
 rom=(folder/'loaded-rom.bin').read_bytes();source=args.source.read_bytes();assert sha(rom)==ROM and sha(source)==SOURCE
 lines=(folder/'child-event-trace.txt').read_text().splitlines();assert lines[0]=='source_core=89405 frame_budget=1800 input=Right2-then-none guest_writes=none'
 def rows(prefix):return [row(x) for x in lines if x.startswith(prefix+' ')]
 setters=rows('setter');writes=rows('event-write');routes=rows('route-store');callbacks=rows('callback-write');bad=rows('first_invalid_event')
 assert [int(r['requested']) for r in setters]==[0,1,5]
 assert [int(r['value']) for r in writes]==[0,1,5]
 assert [int(r['core']) for r in writes]==[89587,89610,89628]
 assert len(bad)==1 and bad[0]==writes[-1];bad=bad[0]
 assert all(hx(r,'target')==0x0201135C and hx(r,'p1')==0x085B9000 and hx(r,'actor')==0x020112B0 for r in setters)
 assert [hx(r,'value') for r in callbacks]==[0x085B9800,0x085B9C00,0x083723E0]
 assert len(routes)==1;route=routes[0]
 assert hx(route,'r4')==0x020112B0 and hx(route,'callback')==0x085B9C00 and hx(route,'target_callback')==hx(route,'r8')==0x083723E0
 assert int(route['core'])==89627 and int(route['seq'])<int(callbacks[-1]['seq'])<int(setters[-1]['seq'])<int(bad['seq'])
 assert hx(callbacks[-1],'r15')==0x0836F788 and hx(callbacks[-1],'address')==0x020112B0
 assert hx(setters[-1],'caller')==hx(bad,'r14')==0x08372410
 assert hx(bad,'r15')==0x0801288C and hx(bad,'r3')==5 and hx(bad,'address')==0x0201136A and int(bad['old'])==1 and hx(bad,'callback')==0x083723E0
 assert hx(route,'actor_kind')==0xC10B and hx(bad,'actor_kind')==0xB
 assert hx(setters[0],'callback')==0 and hx(setters[0],'event')==5 and int(setters[0]['requested'])==0,'new constructor replaces stale presentation state'
 summary=rows('summary');assert len(summary)==1 and summary[0]['outcome']=='invalid-child-event-captured' and int(summary[0]['core'])==89629 and int(summary[0]['game_mode'])==7
 def word(at):return struct.unpack_from('<I',rom,at)[0]
 assert word(0x12884)==0xE1C530BE and word(0x372404)==0xE3A08005 and word(0x36F780)==0xE5848000 and word(0x36F88C)==0x083723E0
 table,reserved,leading_count,relative=struct.unpack_from('<4H',source,0x3D1E30)
 assert (table,reserved,leading_count,relative)==(4,0,6,28)
 count=1+(relative-12)//8;assert count==3
 assert (word(0x5B900C)-(0x085B9000+8))//16==count
 assert sha(source[0x760E4B:0x760E95])=='BC0EB46ABB9510987E1543E7F4472337ACCE2D706202F0581FCF910599E30582'
 assert source[0x760E5C:0x760E60]==bytes.fromhex('3c0b7419')
 assert source[0x760E79:0x760E82]==bytes.fromhex('c7046a96c744029040')
 original=json.loads((ROOT/'build/bizhawk-sprite-mode-replay-20261117-a/launch.json').read_bytes())
 assert not launch['restored_core_exact_except_current_rom_crc'] and launch['all_Core_byte_differences']==original['all_Core_byte_differences'] and len(launch['all_Core_byte_differences'])==15
 result=dict(result='PASS',launch_sha256=sha(raw),trace_sha256=sha((folder/'child-event-trace.txt').read_bytes()),source_sha256=SOURCE,rom_sha256=ROM,actual_event_sequence=[0,1,5],actual_event_frames=[89587,89610,89628],callback_sequence=['085B9800','085B9C00','083723E0'],wrong_callback_writer='0836F780',invalid_setter_caller='08372410',actual_event_store='08012884',actual_stage=11,source_stage11_callback='4090:966A',source_valid_event_count=count,initial_stale_event_replaced_by_constructor=True,source_core_sha256=launch['source_core_sha256'],restored_core_identity=False,all_Core_byte_differences=launch['all_Core_byte_differences'],preserved_restored_sections=['CPU bank','native extensions','managed suffix','all five captured RAM domains'],limits=['Loaded-state diagnostic; fifteen serialized core bytes differ and are retained explicitly.','Observed child0→1→5; valid event2 is source-defined but not reached before this diagnostic stop.','The later event6/OAM slot477 consequence is established by the separate finalized sprite replay, not re-executed past this stop.','No source correction or corrected gameplay success is claimed.'])
 args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
