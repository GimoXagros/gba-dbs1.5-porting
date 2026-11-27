"""Register D-Ark's real disconnected waiting scene in the formerly empty USA mode 18."""
import hashlib
import struct

from dark_wait_assets import Blob, fighter, scenery
from dark_wait_arm import assembly
from mode23_linker import compose

BASE = 0x08000000
START = 0xD50000
LIMIT = 0xD6E000
ROW = 0xE38DD8 + 18*12
DISPATCH = 0xE38F04 + 18*4
HEADERS = 0x08E24130


def apply(image, source):
    assert hashlib.sha256(source).hexdigest() == 'c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7'
    assert struct.unpack_from('<6H',source,0x74FACC+18*12) == (0x2ef,0x7b62,0x2f0,0x7b62,0x287,0x4fa3)
    assert source[0x74FA30+18*6:0x74FA30+19*6] == bytes([20,0,0,0,0,0])
    assert struct.unpack_from('<I',image,0x15B70)[0] == BASE+0xE38DD8
    assert struct.unpack_from('<I',image,0x15C6C)[0] == BASE+0xE38F04
    assert struct.unpack_from('<I',image,0xDACC5C)[0] == HEADERS
    assert bytes(image[ROW:ROW+12]) == bytes(12)
    assert struct.unpack_from('<I',image,DISPATCH)[0] == 0x08015b48
    out = Blob(BASE+START)
    background = scenery(source, image, out)
    actors = out.add(struct.pack('<15I',*(fighter(source, ident, out) for ident in range(15))))
    code_address = out.base + ((len(out.data)+3)&~3)
    code, symbols, _ = compose([assembly(background,actors,HEADERS)],code_address,('dark_init','dark_create','dark_frame'))
    assert out.add(code) == code_address
    end = START+len(out.data)
    assert end <= LIMIT and bytes(image[START:end]) == b'\xff'*(end-START)
    image[START:end] = out.data
    struct.pack_into('<III',image,ROW,symbols['dark_init'],symbols['dark_create'],0x080159b0)
    struct.pack_into('<I',image,DISPATCH,0x08015b40)
    return end
