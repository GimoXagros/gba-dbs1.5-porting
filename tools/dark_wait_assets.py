"""Build the disconnected D-Ark screen from its WSC map and native fighter events."""
import struct

from build_character_p0_completion import source_layout, source_pointer
from build_full_asset_poc import parse_wsc_far_descriptor
from convert_wsc_palette_block import convert_color
from render_wsc_asset_tiles import tile_pixels
from render_wsc_asset_frames import layout_frames

U16 = struct.Struct('<H')
U32 = struct.Struct('<I')
SOURCE_BG = 0x421500
SOURCE_RAIL = 0x41FF70


def packed(pixels):
    return bytes(lo | hi << 4 for lo, hi in zip(pixels[::2], pixels[1::2]))


def palette(words):
    return struct.pack('<16H', *(convert_color(c) for c in words))


def cell(grid, x, y):
    return packed([grid[(y+j)*64+x+i] for j in range(8) for i in range(8)])


def draw_part(grid, width, tile, x, y, fx, fy):
    for j in range(8):
        for i in range(8):
            v = tile[(7-j if fy else j)*8+(7-i if fx else i)]
            if v:
                grid[(y+j)*width+x+i] = v


class Blob:
    def __init__(self, base):
        self.base = base
        self.data = bytearray()
        self.assets = {}

    def add(self, data):
        if data in self.assets:
            return self.assets[data]
        self.data.extend(bytes(-len(self.data) % 4))
        address = self.base + len(self.data)
        self.data.extend(data)
        self.assets[data] = address
        return address


def fighter(source, ident, out):
    record = 0x740000 + ident*32
    p0, p1 = (source_pointer(source, record+k) for k in (0, 6))
    layouts = layout_frames(source, p0)
    _, descriptors = source_layout(source, p0)
    palettes = []
    for offset in (12, 18):
        raw = source_pointer(source, record+offset)
        colors = list(struct.unpack_from('<16H', source, raw+6))
        colors[0] = 0
        palettes.append(out.add(palette(colors)))
    # 7B62:0428 starts the falling event 7. The landing state at +001C uses idle event 0.
    atlas, tiles, frames = {}, [], []
    for event in (7, 18, 0):
        n, payload = struct.unpack_from('<HH', source, p1+4+8*event)
        sequence = []
        for j in range(n):
            ticks, layout, bank = struct.unpack_from('<3H', source, p1+payload+j*12)
            size, raw = parse_wsc_far_descriptor(source, descriptors+bank*8)
            surface = bytearray(64*80)
            for flags, dx, dy in layouts[layout]:
                index = flags & 511
                assert index*32 < size
                # The source constructor explicitly flips the selected Digimon toward the screen center.
                px, py = 32-dx-8, 64+dy
                assert 0 <= px <= 56 and 0 <= py <= 72
                start = raw+index*32
                draw_part(surface, 64, tile_pixels(source[start:start+32]), px, py,
                          not flags & 0x4000, bool(flags & 0x8000))
            indices = []
            for y in range(0, 80, 8):
                for x in range(0, 64, 8):
                    t = cell(surface, x, y)
                    if t == bytes(32):
                        indices.append(0)
                    else:
                        if t not in atlas:
                            atlas[t] = len(tiles)+1
                            tiles.append(t)
                        indices.append(0x3000+atlas[t])
            # The source ticks at 75 Hz. Its low command byte is the animation hold.
            sequence.append((out.add(struct.pack('<80H', *indices)), max(1, (ticks & 255)*4//5)))
        frames.append((out.add(b''.join(struct.pack('<II', *fr) for fr in sequence)), n))
    assert len(tiles) < 768
    return out.add(struct.pack('<10I', out.add(b''.join(tiles)), len(tiles)*32,
                               *palettes, *frames[0], *frames[1], *frames[2]))


def scenery(source, image, out):
    # Background and top/bottom rail tile IDs start at 0x184 in WSC character bank 1.
    tile_rom = 0x420000
    tiles = [bytes(32)]
    bg = [0]*1024
    rail = [0]*2048
    lookup = {}
    def translated(word):
        if word == 0:
            return 0
        assert word & 0x2000
        index = (word & 511)-0x184
        assert 0 <= index < 100
        if index not in lookup:
            lookup[index] = len(tiles)
            p = tile_rom + 32*index
            tiles.append(packed(tile_pixels(source[p:p+32])))
        return lookup[index] | ((word >> 4) & 0xc00)
    for y in range(1, 17):
        for x in range(28):
            bg[(y+1)*32 + x+1] = translated(U16.unpack_from(source,SOURCE_BG+y*64+x*2)[0])
    for x in range(64):
        value = translated(U16.unpack_from(source, SOURCE_RAIL+2*(x%28))[0])
        base = (x//32)*1024 + x%32
        rail[32+base] = rail[18*32+base] = value
    # Original event 8 is layout 16, sourced from 3B09C0's single static tile atlas.
    header, event = 0x3B09C0, 0x3CF9A0
    n, payload = struct.unpack_from('<HH',source,event+4+8*8)
    assert n == 1 and U16.unpack_from(source,event+payload+2)[0] == 16
    _, desc = source_layout(source,header)
    size, start = parse_wsc_far_descriptor(source,desc)
    mask = bytearray(64*32)
    for flags, dx, dy in layout_frames(source,header)[16]:
        i = flags & 511
        assert i*32 < size
        p = start + i*32
        draw_part(mask,64,tile_pixels(source[p:p+32]),32+dx,16+dy,
                  bool(flags & 0x4000),bool(flags & 0x8000))
    # WSC anchor (56,52), so the first possible body pixel is at y=40.
    for y in range(4):
        for x in range(8):
            tile = packed([mask[(4+y*8+j)*64+x*8+i] if 4+y*8+j<32 else 0
                           for j in range(8) for i in range(8)])
            if any(tile):
                bg[(6+y)*32+4+x] = 0x2000+len(tiles)
                tiles.append(tile)
    # The WSC fades BG0 and the portrait while keeping the waiting graphic/actor bright.
    bg_pal = (0,0x30,0x30,0,0,0x30,0x30,0x30,0x30,0,0x30,0x30,0,0,0x383,0x131)
    msg_pal = (0,0,0xFFE,0xFE9,0xEC6,0x541,0x752,0xCA5,0x984,0xFA0,0x431,0x320,0x873,0x210,0,0xFFF)
    portrait = [0]*1024
    for y in range(16):
        for x in range(12):
            portrait[(y+2)*32+x+16] = 0x1100+y*12+x
    # The native cart wraps the 224x144 playfield with four repeating ornamental tiles.
    # BG0 shares the portrait's four-pixel horizontal offset, including at the corners.
    ornamental = image[0x654:0x6D4]
    for row in range(20):
        for col in range(31):
            if 1 <= row < 19 and 2 <= col < 29:
                continue
            pixels = []
            for y in range(row*8, row*8+8):
                for x in range(col*8-4, col*8+4):
                    if not 0 <= x < 240 or (8 <= x < 232 and 8 <= y < 152):
                        pixels.append(0)
                        continue
                    tile = ((x//8+y//8)%4)*32
                    b = ornamental[tile+(y%8)*4+x%8//2]
                    pixels.append((b>>(4*(x%2)))&15)
            if any(pixels):
                key = packed(pixels)
                if key not in lookup:
                    lookup[key] = len(tiles)
                    tiles.append(key)
                portrait[row*32+col] = 0xF000+lookup[key]
    assert len(tiles) < 256
    return out.add(struct.pack('<8I',out.add(b''.join(tiles)),len(tiles)*32,
                  out.add(struct.pack('<1024H',*bg)),out.add(struct.pack('<1024H',*portrait)),
                  out.add(struct.pack('<2048H',*rail)),out.add(palette(bg_pal)),
                  out.add(palette(msg_pal)),0))
