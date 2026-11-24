"""Restore the fixed FF ending-card selector retained in WonderSwan version 1.5."""
import argparse
import hashlib
from pathlib import Path
import struct

from verify_shoot_static_companion_clear import Machine

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = '8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869'
HOOK = 0xC0D28
BASE = 0x08000000

def build(source, before):
    digest = lambda data: hashlib.sha256(data).hexdigest().upper()
    assert digest(source) == SOURCE and digest(before) == BEFORE
    assert source[0x77B34D:0x77B355] == bytes.fromhex('b0ff3c007506b9fc')
    assert source[0x77B38B:0x77B38F] == bytes.fromhex('3c0a755f')
    assert struct.unpack_from('<II',before,HOOK) == (0xE5D5000A,0xE3500000)
    after = before[:HOOK] + struct.pack('<I',0xE3A000FF) + before[HOOK+4:]
    # Compare the original lookup and the 1.5 selector through the whole native
    # decision chain. Stop before either branch performs its first shared call.
    for image, fixed in [(before,False),(after,True)]:
        for saved in range(256):
            m=Machine(image,seed=saved,flags=31)
            m.r[5]=0x02010000
            m.put(m.r[5]+10,saved,1)
            expected_card = not fixed and saved in (0,1,2,3,4,9,10)
            reached=m.run(BASE+HOOK,{0x080C0D98,0x080C0E04})
            assert reached == (0x080C0D98 if expected_card else 0x080C0E04)
    return after

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('source','before','output'):
        parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args()
    image=build(args.source.read_bytes(),args.before.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('xb') as f: f.write(image)
    print('PASS original and 1.5 ending selectors, 512 native decisions',hashlib.sha256(image).hexdigest().upper())
