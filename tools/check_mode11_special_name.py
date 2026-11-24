"""Exercise the source special-tag editor and the actual storage helpers on an EEPROM fixture."""
import argparse
import struct
from pathlib import Path
from mode11_special_name import assembly, EXPORTS
from mode23_linker import compose
from verify_mode22_stats_bridge import Device, TAIL, COMMIT, encode_snapshot, event_list, snapshot
from verify_mode23_completion_save import dump,fill

STATE = 0x02012040
BASE = 0x08000000
READER, WRITER = 0x08FB6130,0x08FB6230


def check(image, symbols):
    data=snapshot()
    struct.pack_into('<H',data,38,1)
    valid=encode_snapshot(data)
    def call(m, method, keys=0):
        m.r[0],m.r[1],m.r[14]=STATE,keys,0x0a000000
        regs=m.r[4:14]
        m.drive(symbols[method],{m.r[14]})
        assert m.r[4:14]==regs
        return m.r[0],m.r[1]

    m=Device(image,valid)
    fill(m,STATE-4,b'edge'+bytes([0xee])*8+b'tail')
    call(m,'tag_name_init')
    assert dump(m,STATE,8)==b'A'+bytes(7)
    for _ in range(64):
        call(m,'tag_name_step',1)
    assert dump(m,STATE,5)==b'A'+bytes(4)
    for _ in range(64):
        call(m,'tag_name_step',4)
    assert dump(m,STATE,5)==b'A'+bytes(4)
    for key in (1,64,1,1,64,1,1,1,64):
        call(m,'tag_name_step',key)
    assert dump(m,STATE,5)==b'BCD(\x03'
    call(m,'tag_name_step',0x80)
    assert dump(m,STATE,5)==b'BCD\x00\x02'
    call(m,'tag_name_step',64)
    assert call(m,'tag_name_step',64)==(1,6)
    for _ in range(61):
        assert call(m,'tag_name_step')[0]==0
    assert call(m,'tag_name_step')[0]==2
    assert dump(m,STATE-4,4)==b'edge' and dump(m,STATE+8,4)==b'tail'
    original=bytes(m.blocks)
    assert call(m,'tag_name_save')[0]==0
    result=data[:]
    result[14:18]=b'BCD\0'
    assert bytes(m.blocks)==original[:216]+encode_snapshot(result)+original[272:]
    assert m.events==event_list('read',TAIL)+event_list('write',COMMIT)

    call(m,'tag_name_init')
    for _ in range(ord('A')-ord('(')):
        call(m,'tag_name_step',8)
    assert call(m,'tag_name_step',64)==(1,6) and dump(m,STATE,4)==bytes(4)
    not_special=data[:]
    struct.pack_into('<H',not_special,38,0)
    records=[(encode_snapshot(not_special),3),(bytes(56),2),(valid[:-1]+bytes([valid[-1]^1]),3)]
    for record,status in records:
        m=Device(image,record)
        before=bytes(m.blocks)
        assert call(m,'tag_name_save')[0]==status and bytes(m.blocks)==before
    for direction in ('read','write'):
        for block in TAIL:
            m=Device(image,valid,faults=[(direction,block,1)])
            fill(m,STATE,b'BCD\0'+bytes(4))
            before=bytes(m.blocks)
            assert call(m,'tag_name_save')[0]==1
            assert bytes(m.blocks[:216])==before[:216] and bytes(m.blocks[272:])==before[272:]
            if direction=='read':
                assert bytes(m.blocks)==before
    print('PASS full and short names, wrap, undo, 62-frame wait, validated snapshot merge, 17 failure cases')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom',type=Path)
    parser.add_argument('source',type=Path)
    parser.add_argument('--entries',nargs=3,type=lambda s:int(s,0))
    args=parser.parse_args()
    image=args.rom.read_bytes()
    if args.entries:
        symbols=dict(zip(EXPORTS,args.entries))
    else:
        # Only the test fixture places code past the image. Storage runs at its installed addresses.
        code,symbols,_=compose([assembly(args.source.read_bytes(),READER,WRITER)],BASE+len(image),EXPORTS)
        image+=code
    check(image,symbols)
