"""Exercise the proposed record through actual ARM code and a block device fixture."""
import struct
import zlib
from mode22_snapshot_storage import assemble
from verify_mode23_completion_save import Machine, fill, dump

BASE, START, BUFFER = 0x08000000, 0x08010000, 0x02018000
READ, WRITE = 0x0837DB60, 0x0837DB54
code, symbols, _ = assemble(START)
rom = bytes(START-BASE) + code
input_data = bytes((n*47+9)&255 for n in range(42))
expected = bytearray(input_data)
expected[12] = 0

def execute(device, writing=False, fault=None):
    m = Machine(rom, seed=3, flags=31)
    fill(m, BUFFER, input_data)
    m.r[0] = BUFFER
    initial = m.r[:]
    pc = symbols['m22_write_snapshot' if writing else 'm22_read_snapshot']
    ops = []
    while True:
        pc = m.run(pc,{initial[14],READ,WRITE})
        if pc == initial[14]:
            break
        block, pointer = m.r[:2]
        assert 27 <= block <= 33 and pointer%2 == 0
        assert len(ops)<7
        ops.append(block)
        if fault != block:
            if pc == READ:
                fill(m,pointer,device[block*8:block*8+8])
            else:
                device[block*8:block*8+8]=dump(m,pointer,8)
        m.r[0]=int(fault==block)*0x8000
        for i in (1,2,3,12):m.r[i]=0x7c00+i
        pc=m.r[14]
    assert m.r[1:15]==initial[1:15]
    return m.r[0],dump(m,BUFFER,42),ops

def main():
    original=bytes((n*17+3)&255 for n in range(512))
    device=bytearray(original)
    status, unchanged, writes=execute(device,True)
    assert (status,unchanged,writes)==(0,input_data,[28,29,30,31,32,33,27])
    body=bytes(expected)+bytes(2)
    assert device[216:272]==b'BS15TAG\x01'+body+struct.pack('<I',zlib.crc32(body))
    assert device[:216]==original[:216] and device[272:]==original[272:]
    assert execute(device)==(0,expected,list(range(27,34)))
    for i in range(56):
        damaged=device[:];damaged[216+i]^=1
        assert execute(damaged)[:2]==(3,input_data)
    for blank in (0,255):
        erased=device[:];erased[216:272]=bytes([blank])*56
        assert execute(erased)[:2]==(2,bytes(42))
    for offset in range(27,34):
        assert execute(device,fault=offset)[:2]==(1,input_data)
        erased=device[:];erased[216:272]=bytes([255])*56
        assert execute(erased,True,offset)[0]==1
        assert erased[:216]==original[:216] and erased[272:]==original[272:]
        assert execute(erased)[0] in (2,3)
    print('PASS ARM snapshot roundtrip, 56 single-byte corruptions, legacy zero/FF and 14 block I/O failures')
if __name__=='__main__':main()
