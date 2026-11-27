"""Install the linked D-Ark controller into a build already containing the waiting scene."""
import hashlib
import struct

import dark_battle_assets
import dark_battle_link
import dark_battle_scene
import dark_entry_repair as waiting
from dark_wait_assets import Blob, fighter, scenery
from dark_wait_arm import assembly
from mode23_linker import compose


START = 0x900000
LIMIT = 0xa80000


def apply(image, source):
    assert hashlib.sha256(source).hexdigest() == 'c415f227ed9a277f6553b4ec03ca16ce4d0058d1c1104889d90bd88071d76fd7'
    old = Blob(waiting.BASE+waiting.START)
    bg = scenery(source, image, old)
    actors = old.add(struct.pack('<15I', *(fighter(source,i,old) for i in range(15))))
    old_address = old.base + ((len(old.data)+3)&~3)
    original, old_symbols, _ = compose([assembly(bg,actors,waiting.HEADERS)],old_address,('dark_init','dark_create'))
    assert image[waiting.START:waiting.START+len(old.data)] == old.data
    assert image[old_address-waiting.BASE:old_address-waiting.BASE+len(original)] == original
    assert struct.unpack_from('<III',image,waiting.ROW) == (old_symbols['dark_init'],old_symbols['dark_create'],0x080159b0)
    out = Blob(waiting.BASE+START)
    battle_actors, shots, colors = dark_battle_assets.assets(source, out)
    grid, front = dark_battle_assets.field(source,bg,old,out)
    tables = 0x74fff0
    patterns = out.add(bytes(source[tables+0x1494:tables+0x14a4]))
    # Existing USA loss scene (source raw 772021) requests song 1A, priority 4.
    assert image[0x34020C:0x340214] == bytes.fromhex("1a80a0e30490a0e3")
    categories = out.add(bytes(source[0x787267:0x787277]))
    stats = out.add(bytes(source[tables+0x14a4:tables+0x1504]))
    code_address = out.base + ((len(out.data)+3)&~3)
    code, symbols, _ = compose([assembly(bg,actors,waiting.HEADERS,linked=True),
        dark_battle_link.assembly(patterns,stats),
        dark_battle_scene.assembly(battle_actors,grid,front,shots,colors,categories)],code_address,('dark_create',))
    assert out.add(code) == code_address
    end = START+len(out.data)
    assert end<=LIMIT and image[START:end] == b'\xff'*(end-START)
    # Native multiplayer's status poll consumes only SIOCNT bits 2,3,4,5,7.
    # A word load also reads and acknowledges the adjacent UART RX FIFO.
    poll = 0x37b1a8
    assert image[poll:poll+2] == bytes.fromhex('3568')  # ldr r5,[r6]
    assert struct.unpack_from('<I',image,0x37b1c0)[0] == 0x04000128
    image[poll:poll+2] = bytes.fromhex('3588')  # ldrh r5,[r6]
    image[START:end] = out.data
    struct.pack_into('<I',image,waiting.ROW+4,symbols['dark_create'])
    return end
