"""Independent finalized source-child contact chronology and capture audit."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from verify_child_event_producer_capture import row, hx, sha
from verify_gba_shoot_entry_capture_v2 import checkpoint_core

ROM='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
PRIOR='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args(); folder=a.capture
    raw=(folder/'launch.json').read_bytes(); launch=json.loads(raw)
    assert launch['completed'] and launch['outcome']=='source-child-contact-retired'
    assert launch['launcher_sha256']=='1C0BCBBBAE7FED9E7E2FFF7C3E094965D9C43C659272E1278D683BD43012A2FF'
    assert launch['pins']['tools/bizhawk_probe_child_contact_positive.lua']=='D5EE2AEEB153946E74ABE43B8B386BC3AFBF5634CF32A3687EDF76B027793BD8'
    assert launch['pins']['tools/bizhawk_probe_child_event_producer.lua']=='B01A4F35A77D9CB7E24173E73C6D85818FBF8A3563B29FE55E69294EBCA7A9F9'
    assert launch['rom_sha256']==ROM and launch['source_rom_sha256']==PRIOR
    assert launch['guest_writes']==[] and not any(launch[k] for k in ('visible','physical_background_input','supplied_save_used','host_deadline_reached','host_stop_requested'))
    for k in ('loaded_rom_exact','scripts_unchanged','checkpoint_copies_unchanged','CPU_bank_equal','native_extensions_equal','managed_suffix_equal'): assert launch[k],k
    for name,digest in launch['files'].items(): assert sha((folder/name).read_bytes())==digest,name
    rom=(folder/'loaded-rom.bin').read_bytes(); assert sha(rom)==ROM
    assert (folder/'probe.gba').read_bytes()==rom
    assert (folder/'child-contact-done.txt').read_text().strip()=='source-child-contact-retired'
    lines=(folder/'child-event-trace.txt').read_text().splitlines()
    assert lines[0]=='source_core=89405 frame_budget=1800 input=Right2-then-none guest_writes=none'
    def rows(prefix):return [row(s) for s in lines if s.startswith(prefix+' ')]
    setters=rows('setter');stores=rows('store');writes=rows('event-write');callbacks=rows('callback-write')
    contacts=rows('contact'); summary=rows('summary')[0]
    assert [int(r['requested']) for r in setters]==[0,1,1,2]
    assert [int(r['requested']) for r in stores]==[0,1,1,2]
    assert [int(r['value']) for r in writes]==[0,1,1,2]
    assert [int(r['core']) for r in writes]==[89587,89610,89628,90753]
    assert all(hx(r,'actor')==0x020112B0 and hx(r,'address')==0x0201136A and hx(r,'r15')==0x0801288C for r in writes)
    assert [hx(r,'value') for r in callbacks]==[0x085B9800,0x085B9C00,0x08D8C864,0x08D8C910,0x08D8C980]
    assert hx(callbacks[2],'r15')==0x08D8C834 and int(callbacks[2]['core'])==89627
    assert [r['kind'] for r in contacts]==['first','effect','wait','release','retired']
    assert [int(r['core']) for r in contacts]==[89628,89628,89629,90754,90768]
    first,effect,wait,release,retired=contacts
    assert int(callbacks[2]['seq']) < int(first['seq']) < int(effect['seq']) < int(writes[2]['seq']) < int(wait['seq']) < int(writes[3]['seq']) < int(release['seq']) < int(retired['seq'])
    assert hx(effect,'r15')==0x08359730 and hx(effect,'r14')==0x08D8C8AC and hx(effect,'r5')==hx(effect,'target')==0x02011710
    assert hx(effect,'r11')==0 and hx(effect,'r8')==3 and hx(effect,'flags')==0x8010
    assert all(hx(r,'caller')==0x08D8CA24 and hx(r,'target')==0x0201135C for r in setters[2:])
    assert hx(retired,'r15')==0x08D8C9C0 and hx(retired,'r14')==0x08D8C9A8
    assert hx(retired,'flags')==6 and hx(retired,'target_flags')==0x8800
    assert not rows('first_invalid_event') and not rows('route-store')
    assert all(int(r['mode'])==7 and int(r['stage'])==11 for r in setters+stores+writes+callbacks+contacts)
    assert summary['outcome']=='source-child-contact-retired' and int(summary['core'])==90769 and int(summary['game_mode'])==7
    # These two inherited summary fields have no active renderer hooks in B01;
    # do not use their false values as evidence of all-frame OAM bounds.
    iw=(folder/'diagnostic-iwram.bin').read_bytes(); ew=(folder/'diagnostic-ewram.bin').read_bytes()
    h=lambda b,o:struct.unpack_from('<H',b,o)[0]
    assert h(iw,0x2310)==7 and iw[0x231E]==11 and h(iw,0x450A)==6
    assert h(iw,0x12CA)==35 and h(ew,0x11718)==0x8800
    assert h(ew,0x112BA)&0x8000 and h(ew,0x11366)&0x2000
    assert h(ew,0x1136A)==2 and h(ew,0x11374)==0
    # Native retirement replaces the task-header callback with the existing
    # deferred release service while preserving the current payload until safe.
    assert struct.unpack_from('<I',ew,0x11298)[0]==0x08352ADC
    source_core,_=checkpoint_core((folder/'checkpoint/healthy-activation.State').read_bytes())
    restored,_=checkpoint_core((folder/'restored.State').read_bytes())
    assert sha(source_core)=='43B2893A6BD9537D3D5C3FDE47C65FE12A386F76BB12B342FC4ADAE3C978E9E7'
    expected=bytearray(source_core);struct.pack_into('<I',expected,12,zlib.crc32(rom))
    diffs=[dict(offset=i,expected=x,actual=y) for i,(x,y) in enumerate(zip(expected,restored)) if x!=y]
    assert len(expected)==len(restored) and diffs==launch['all_Core_byte_differences']
    assert [d['offset'] for d in diffs]==[310,325,326,327,330,342,343,384,385,392,393,394,396,397,1336]
    n=struct.unpack_from('<I',source_core)[0]
    assert source_core[0x24:0x134]==restored[0x24:0x134]
    assert source_core[4+0x61000:4+n]==restored[4+0x61000:4+n] and source_core[4+n:]==restored[4+n:]
    for region in ('iwram','ewram','vram','palette','oam'):
        assert (folder/f'restored-{region}.bin').read_bytes()==(folder/f'checkpoint/41-healthy-activation-{region}.bin').read_bytes()
    result=dict(status='PASS',launch_sha256=sha(raw),trace_sha256=sha((folder/'child-event-trace.txt').read_bytes()),
      rom_sha256=ROM,actual_event_sequence=[0,1,1,2],actual_event_frames=[89587,89610,89628,90753],
      contact_milestones={r['kind']:int(r['core']) for r in contacts},effect_target='02011710',effect_kind=3,
      child_deferred_retirement_callback='08352ADC',terminal_core=90769,terminal_mode=7,terminal_stage=11,
      terminal_oam_staging_cursor=35,terminal_child_event=2,terminal_child_layout=0,
      terminal_match_flags='0006',terminal_target_flags='8800',old_failure_core90753_survived=True,
      restored_core_identity=False,all_Core_byte_differences=diffs,
      limits=['Bounded restored-state source contact success, not complete Shoot or whole-game completion.',
      'Effect call stack was enforced by the pinned observer at the native entry; the journal directly records target/R5/R11/kind/LR.',
      'Terminal OAM cursor35 and valid child layout are captured; inherited false outside/oversized summary fields are inert and prove no all-frame renderer bound.',
      'All15 serialized Core differences remain explicit; CPU/native extensions/managed suffix and five RAM images match.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result))

if __name__=='__main__':main()
