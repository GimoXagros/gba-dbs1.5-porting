"""Check capture provenance, native copied code, and Tonc OAM geometry.

Reference: https://www.coranac.com/tonc/text/regobj.htm
The hardware has 128 eight-byte OAM records, including affine interleaving.
Passing these invariants is not a claim of correct animation or full gameplay.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct

GBA_SHA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'


def sha(b): return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok: raise ValueError(label)


def inspect(capture,gba):
    manifest=json.loads((capture/'capture.json').read_text(encoding='utf-8'))
    need(manifest['schema']=='mgba-headless-gdb-capture-v2','capture provenance schema')
    need(manifest['process']['monitor_visible'] is False,'invisible capture')
    need(manifest['process']['gdb_endpoint_owner']['verified'],'actual process ownership')
    need(manifest['rom']['loaded_rom_identity']['verified'],'loaded ROM identity samples')
    need(manifest['gdb']['final_stop']=='S02' and not manifest['gdb']['asynchronous_stops'],
         'manual stop without recorded asynchronous fault')
    for name, identity in manifest['regions'].items():
        need(Path(name).name == name, 'local region filename')
        data = (capture / name).read_bytes()
        need(len(data) == identity['size'] and sha(data) == identity['sha256'], 'captured region identity: ' + name)
    ir=(capture/'iwram.bin').read_bytes()
    oam=(capture/'oam.bin').read_bytes()
    need(len(ir)==0x8000 and len(oam)==128*8,'IWRAM and hardware OAM extents')
    need(ir[0x200:0x380]==gba[0x12C58:0x12DD8], 'native DMA-copied renderer remains intact')
    active=affine=0
    for n in range(128):
        a0,a1,a2,interleaved=struct.unpack_from('<4H',oam,n*8)
        if a0 & 0x100:
            affine+=1
            active+=1
        elif not a0 & 0x200:
            active+=1
    return dict(status='PASS',rom_sha256=manifest['rom']['sha256'],
        capture_manifest_sha256=sha((capture/'capture.json').read_bytes()),
        renderer_sha256=sha(ir[0x200:0x380]),oam_records=128,
        enabled_objects_at_capture=active,affine_objects_at_capture=affine,
        reference='https://www.coranac.com/tonc/text/regobj.htm',
        claim_scope='provenance, bounded no-fault observation and copied-code integrity; visual correctness and complete gameplay excluded')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('capture',type=Path);p.add_argument('gba',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();gba=a.gba.read_bytes()
    need(sha(gba)==GBA_SHA,'original native identity')
    report=inspect(a.capture,gba)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
