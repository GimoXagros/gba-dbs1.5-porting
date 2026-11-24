"""Convert the source score and earned-tag resource lists, without using captured frames."""
import struct

from build_full_asset_poc import convert_tile
from convert_wsc_palette_block import convert_color
from render_wsc_asset_frames import layout_frames


def resources(source):
    result = {}
    def tiles(label, offset, length):
        result[label] = b''.join(convert_tile(source[pos:pos+32])
                                 for pos in range(offset, offset+length, 32))
    def palette(label, offset, colors):
        values = struct.unpack_from(f'<{colors}H', source, offset)
        result[label] = struct.pack(f'<{colors}H', *(convert_color(color) for color in values))
    def tilemap(label, offset, count):
        values = struct.unpack_from(f'<{count}H', source, offset)
        result[label] = struct.pack(f'<{count}H', *((v & 511) | ((v & 0xe000) >> 4)
                                    | ((v & 0x1e00) << 3) for v in values))
    tiles('shared', 0x420000, 0xc00)
    palette('green', 0x420c40, 16)
    tiles('scorebg', 0x421b40, 0x520)
    palette('scorebgpal', 0x421b00, 32)
    tilemap('back', 0x2df61a, 32*18)
    tilemap('front', 0x2dfa9a, 32*18)
    tiles('font', 0x43e9c0, 0x800)
    palette('gold', 0x43f1c0, 16)
    tiles('digits', 0x3a0000, 0xcc0)
    palette('digitpal', 0x3d7eb6, 16)
    tiles('get', 0x3c6fc0, 0x360)
    palette('getpal', 0x3d8726, 16)
    for label, offset, tile_count in (('digits',0x3cb870,102), ('get',0x3d5340,27)):
        for i, parts in enumerate(layout_frames(source, offset)):
            assert all((f & 511) < tile_count for f,_,_ in parts)
            result[f'{label}_frame{i}'] = struct.pack('<I',len(parts)) + b''.join(
                struct.pack('<Hbb', f, dy, dx) for f, dx, dy in parts)
    for i in range(11):
        a,b = struct.unpack_from('<HH',source,0x77407c+i*4)
        tiles(f'tag{i}',0x2d9360+a, (60 if i==10 else 28)*32)
        palette(f'tagpal{i}',0x2d9360+b,16)
    tilemap('tagmap',0x2df56a,28)
    tilemap('specialmap',0x2df5a2,60)
    for i in range(4):
        label,dx = struct.unpack_from('<Hh',source,0x775242+i*4)
        pos = 0x773d30+label
        result[f'level{i}'] = bytes([72+dx])+source[pos:source.index(0,pos)+1]
    result['total'] = source[0x775283:0x775283+15]
    assert result['total'] == b'TOTAL POINT[S]\x00'
    # 73D3:0990ff. The special-name scene's background and the 28x18 map.
    tiles('namebg',0x3a5fa0,0x700)
    palette('namebgpal',0x3a66a0,16)
    palette('nameink',0x2d9360+0x6178,16)
    tilemap('namebgmap',0x3a66c0,28*18)
    return result

