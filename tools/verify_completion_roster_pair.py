"""Compare the actual ordinary character list and bounded persistent fields across independent saves."""
import argparse
import json
import re
import struct
import zlib
from pathlib import Path

from run_completion_roster_pair import ARCHIVE,EARNED,WSC,sha

ORDER=tuple(range(11))+(13,14,11,12)
HEADERS=(0xa28a0,0xa40e0,0xa5900,0xa7120,0xa8940,0xaa160,0xab980,0xad1a0,
         0xae9c0,0xb01e0,0xb1a00,0xa1080,0xe60020,0xf7e8e0,0xdcd480)


def checked(folder):
    record=json.loads((folder/'launch.json').read_bytes())
    assert record['loaded_exact'] and record['outcome']=='ordinary-15-pass' and record['guest_writes']==[]
    assert record['display']=='private desktop'
    for name,digest in record['captures'].items():
        assert sha((folder/name).read_bytes())==digest
    assert len(record['captures'])==30 and sha((folder/'trace.txt').read_bytes())==record['trace_sha256']
    return tuple(int(i) for i in re.findall(r'^\d+ selected (\d+)$',(folder/'trace.txt').read_text(),re.M)),record


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('original','native','archived-copy','earned-save','report'):
        p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    orig,om=checked(a.original)
    gba,gm=checked(a.native)
    src=(a.original/'loaded-rom.bin').read_bytes()
    rom=(a.native/'loaded-rom.bin').read_bytes()
    assert sha(src)==WSC and sha(rom)==gm['rom_sha256']
    assert orig==ORDER and len(gba)==15 and any(gba==ORDER[i:]+ORDER[:i] for i in range(15))
    for i in ORDER:
        ram=(a.original/f'id-{i}-ram.bin').read_bytes()
        assert struct.unpack_from('<15H',ram,0x30ea)==ORDER
        assert ORDER[struct.unpack_from('<H',ram,0x3116)[0]]==i
        vram=(a.native/f'id-{i}-vram.bin').read_bytes()
        at=HEADERS[i]
        assert vram[0x5780:0x5a80]==rom[at:at+768]
    archived=a.archived_copy.read_bytes()
    assert sha(archived)==ARCHIVE
    boot=bytearray(archived)
    boot[0x4e]=1;boot[0x73]=0
    assert boot==(a.original/'initial-sram.bin').read_bytes()
    assert sha(a.earned_save.read_bytes())==EARNED==gm['donor_sha256']
    raw=a.earned_save.read_bytes()
    physical=b''.join(raw[o:o+8][::-1] for o in range(0,272,8))
    assert sum(physical[:192])==struct.unpack_from('<I',physical,192)[0]
    assert physical[216:224]==b'BS15TAG\x01' and zlib.crc32(physical[224:268])==struct.unpack_from('<I',physical,268)[0]
    assert boot[0x88]==physical[18]==0x30
    assert boot[0x140]&1 and physical[208:216]==b'BS15M23\x01'
    source_stats=bytes(boot[0x104:0x140])
    native_stats=physical[0x8e:0xbe]+physical[224:236]
    assert source_stats==native_stats==bytes(60)
    source_tags=struct.unpack_from('<11H',boot,0x146)
    native_tags=struct.unpack_from('<11H',physical,242)
    assert source_tags==(2,1,1,1,0,2,0,0,1,1,0)
    assert native_tags==(0,)*10+(1,)
    report=dict(status='ORDINARY_15_ROSTER_AND_BOUNDED_SAVE_FIELDS_COMPARED',wsc_sha256=WSC,
        gba_sha256=sha(rom),wsc_input_save=ARCHIVE,native_earned_save=EARNED,
        launches=[sha((d/'launch.json').read_bytes()) for d in (a.original,a.native)],
        checked_wsc_cursor_ids=orig,checked_gba_portrait_ids=gba,gba_verified_header_bytes_per_id=768,
        matching_fields={'permanent_character_flags':'30','digimon_shoot_eligible':True,'fifteen_stat_pairs':'all zero'},
        unequal_fields={'tag_counts':{'wsc':source_tags,'gba':native_tags}},
        limits='Ordinary single-player selector only; other menu trees, arena/progression states and tag quantities were not certified identical. Each platform read its own physically different save.',
        checker_sha256=sha(Path(__file__).read_bytes()))
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':
    main()

