"""Verify split-process genuine award, raw EEPROM byte order/CRC, special viewer and exit."""
import argparse
import json
import struct
import zlib
from pathlib import Path
from verify_mode23_completion_save import sha


def check_run(folder,phase,rom):
    result=json.loads((folder/'launch.json').read_bytes())
    assert result['phase']==phase and result['outcome']==phase+'-pass'
    assert result['visible'] is False and result['guest_writes']==[] and result['supplied_save_used'] is False
    assert result['loaded_rom_exact'] and result['rom_sha256']==rom==sha((folder/'loaded-rom.bin').read_bytes())
    for name,digest in result['files'].items():assert sha((folder/name).read_bytes())==digest
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('award','cold','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    rom='78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924'
    run=check_run(a.award,'award',rom);cold=check_run(a.cold,'cold',rom)
    assert run['donor_sha256']=='001DF714CC4EE525DBFB566D7F1BDDFCFDC4894EF4303D3EA9C8A8163746936A'
    save=(a.award/'data/104/probe.SaveRAM').read_bytes()
    assert sha(save)==cold['donor_sha256']
    assert save==(a.cold/'data/104/probe.SaveRAM').read_bytes()
    assert save[512:]==b'\xff'*(len(save)-512)
    data=b''.join(save[i:i+8][::-1] for i in range(216,272,8))
    assert data[:8]==b'BS15TAG\1' and zlib.crc32(data[8:52])==int.from_bytes(data[52:],'little')
    assert struct.unpack_from('<11H',data,26)==(0,)*10+(1,)
    lines=(a.award/'trace.txt').read_text().splitlines()
    assert len(lines)==2 and lines[0].endswith('award score=2310 difficulty=2 result=800A count=1') and lines[1].endswith('successful-title-return')
    assert int(lines[0].split()[0])<int(lines[1].split()[0])
    cold_lines=(a.cold/'trace.txt').read_text().splitlines()
    assert len(cold_lines)==2 and cold_lines[0].endswith('rank10=1 special branch=4') and cold_lines[1].endswith('viewer exit mode=20')
    assert int(cold_lines[0].split()[0])<int(cold_lines[1].split()[0])
    ew=(a.cold/'cold-special-EWRAM.bin').read_bytes();iw=(a.cold/'cold-special-IWRAM.bin').read_bytes()
    assert int.from_bytes(iw[0x2310:0x2312],'little')==22
    tasks=[i for i in range(0x10000,0x10000+52*0x118,0x118) if ew[i+16]&2 and int.from_bytes(ew[i:i+4],'little')==0x08f7a71c]
    assert len(tasks)==1
    at=tasks[0]+24
    assert ew[at:at+26]==data[8+14:8+40] and ew[at+26]==4
    report=dict(status='MODE11_EARNED_SPECIAL_COLD_VIEW_EXIT_PASS',rom_sha256=rom,
        checker_sha256=sha(Path(__file__).read_bytes()),source_checkpoint=run['donor_sha256'],
        award_launch=sha((a.award/'launch.json').read_bytes()),cold_launch=sha((a.cold/'launch.json').read_bytes()),
        saved_physical_eeprom=sha(save),score=2310,difficulty=2,rank=10,special_saved_count=1,
        cold_native_mode=22,cold_exit=20,artifact_hashes={name:sha((a.cold/name).read_bytes()) for name in
        ('cold-special.png','cold-special-VRAM.bin','cold-special-PALRAM.bin','cold-special-OAM.bin')},
        limitations='Progress after a prior authentic assisted campaign checkpoint. No device/guest writes by these probes. Separate producer branch; this build has no intervening score/GET presentation.')
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
