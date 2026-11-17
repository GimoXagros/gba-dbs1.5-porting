"""Independent finalized sprite replay identity, first overflow and mode writer.

This establishes the native writing consumer and captured metadata; source P0
ownership requires a separate original-source reconstruction once identified.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROM='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
HOST='A19E994876CA5E6704CDA3AEDC646D147D36BD6E54F6283A2B6FCA2FF3BBB3C8'
PROBE='E281FF8D3CC2D61289A6C6CC1AD6217E6C18F11193AFC2B3935203F68E36EFB9'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def fields(line):return dict(re.findall(r'(\w+)=([^\s]+)',line))
def hx(row,key):return int(row[key],16)
def dec(row,key):return int(row[key])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 folder=args.capture;launchb=(folder/'launch.json').read_bytes();launch=json.loads(launchb)
 assert launch['completed'] and launch['outcome']=='first-invalid-game-mode','requires finalized diagnostic success'
 assert launch['launcher_sha256']==HOST
 assert all(launch[k] for k in ('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged','CPU_bank_equal','native_extensions_equal','managed_suffix_equal'))
 assert launch['pins']['tools/bizhawk_probe_sprite_mode_corruption.lua']==PROBE
 assert launch['rom_sha256']==ROM and not launch['visible'] and not launch['physical_background_input'] and not launch['supplied_save_used'] and launch['guest_writes']==[]
 for name,digest in launch['files'].items():assert sha((folder/name).read_bytes())==digest,name
 rom=(folder/'loaded-rom.bin').read_bytes();assert sha(rom)==ROM
 assert (folder/'sprite-replay-done.txt').read_text().strip()=='first-invalid-game-mode'
 lines=(folder/'renderer-trace.txt').read_text().splitlines()
 assert lines[0]=='source_core=89405 frame_budget=1800 input=Right2-then-none guest_writes=none'
 assert [fields(x) for x in lines if x.startswith('input ')]==[
  {'core':'89405','relative':'0','right':'true'},
  {'core':'89406','relative':'1','right':'true'},
  {'core':'89407','relative':'2','right':'false'}]
 def one(prefix):
  rows=[fields(x) for x in lines if x.startswith(prefix+' ')]
  assert len(rows)==1,(prefix,len(rows));return rows[0]
 out=one('first_out_of_bounds_oam');mode=one('first_invalid_mode')
 assert out['kind']=='outside-oam' and mode['kind']=='invalid-mode-write'
 assert 89405<=dec(out,'core')<=dec(mode,'core')<=91205
 for r in [out]+[fields(x) for x in lines if x.startswith('retained ') and 'kind=outside-oam ' in x]:
  ptr=hx(r,'destination');slot=dec(r,'slot')
  assert ptr==0x03001428+slot*8 and slot>=128
  assert hx(r,'r12')==ptr and hx(r,'tile_destination')==0x02000000+slot*32==hx(r,'r14')==hx(r,'native_tiles')
  assert dec(r,'display_count')==slot and dec(r,'remaining')==hx(r,'r2')
 assert hx(mode,'address')==0x03002310 and dec(mode,'value')>20
 assert hx(mode,'r12')==0x03002310 and hx(mode,'r14')==0x02003BA0
 assert hx(mode,'r3')&65535==dec(mode,'value')
 assert hx(mode,'r15') in (0x086FEAE8,0x086FEAF0),'actual opcode or exposed pipelined PC'
 assert struct.unpack_from('<I',rom,0x6FEAE8)[0]==0xE1CC30B0
 contexts={}
 for line in lines:
  if line.startswith('overflow_context '):
   row=fields(line);contexts[row['kind']]=row
 assert {'dispatch','count-load','layout-load','layout-ready'}<=contexts.keys()
 dispatch=contexts['dispatch'];load=contexts['layout-load'];ready=contexts['layout-ready'];cursor=contexts['count-load']
 assert len({hx(x,'r5') for x in (dispatch,load,ready,cursor,out)})==1
 words=[int(x,16) for x in dispatch['words'].split(',')];assert len(words)==20
 present=struct.pack('<20I',*words)
 p0=struct.unpack_from('<I',present,0x48)[0];layout=struct.unpack_from('<H',present,0x18)[0]
 assert p0==hx(dispatch,'p0') and layout==hx(dispatch,'layout')
 def read32(address):
  if 0x08000000<=address<=0x08fffffc:return struct.unpack_from('<I',rom,address-0x08000000)[0]
  raise ValueError(f'captured source pointer requires separate RAM epoch reconstruction: {address:08X}')
 table=read32(p0);entry=table+layout*8
 assert entry==hx(load,'layout_entry')==hx(ready,'layout_entry')
 count,parts=read32(entry),read32(entry+4)
 assert count==hx(load,'source_count')==dec(ready,'loaded_count')==hx(ready,'r2')
 assert parts==hx(load,'part_pointer')==hx(ready,'part_pointer')
 assert 0<=dec(cursor,'cursor_initial')<127
 result=dict(result='PASS',scope='actual first staging overflow and mode writer; original source layout producer not yet resolved',launch_sha256=sha(launchb),journal_sha256=sha((folder/'renderer-trace.txt').read_bytes()),rom_sha256=ROM,source_core_sha256=launch['source_core_sha256'],restored_core_exact_except_current_rom_crc=launch['restored_core_exact_except_current_rom_crc'],first_outside=out,mode_writer=mode,captured_metadata=dict(presentation=f'{hx(dispatch,"r5"):08X}',p0=f'{p0:08X}',layout=layout,layout_table=f'{table:08X}',entry=f'{entry:08X}',parts=count,part_pointer=f'{parts:08X}',initial_cursor=dec(cursor,'cursor_initial'),saved_caller=cursor['saved_caller'],words=dispatch['words']),limits=['All full-capture hashes bind the finalized private replay.','The first overflow and mode-store addresses are reconstructed from native OAM/tile pointer arithmetic.','A source-aware fix is not inferred from a large count alone; source P0/layout producer ownership remains separate.'])
 args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
