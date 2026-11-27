"""Build native tiled battle poses from the selected WSC combatant's own events."""
import struct

from dark_wait_assets import (
    SOURCE_BG, U16, draw_part, layout_frames, packed, palette, parse_wsc_far_descriptor,
    source_layout, source_pointer, tile_pixels,
)


def sequence(source, header, event_table, events, out):
    """Resolve P1 holds/P0 layouts to one compact local atlas per unique pose."""
    layouts = layout_frames(source, header)
    _, descriptors = source_layout(source, header)
    frame_cache = {}
    result = []
    for event in events:
        count, payload = struct.unpack_from('<HH', source, event_table + 4 + 8 * event)
        frames = []
        for j in range(count):
            ticks, layout, bank = struct.unpack_from('<3H', source, event_table + payload + j*12)
            key = (layout, bank)
            if key not in frame_cache:
                size, raw = parse_wsc_far_descriptor(source, descriptors + bank*8)
                # 96x80 with actor feet at (48,64). Draw overlapping source parts in order.
                surface = bytearray(96*80)
                for flags, dx, dy in layouts[layout]:
                    index = flags & 511
                    x, y = 48 - dx - 8, 64 + dy
                    assert 0 <= x <= 88 and 0 <= y <= 72, (event, dx, dy)
                    assert index*32 < size
                    tile = source[raw+index*32:raw+index*32+32]
                    draw_part(surface, 96, tile_pixels(tile), x, y,
                              not flags & 0x4000, bool(flags & 0x8000))
                atlas, indices = {}, []
                for y in range(0, 80, 8):
                    for x in range(0, 96, 8):
                        tile = packed([surface[(y+j)*96+x+i] for j in range(8) for i in range(8)])
                        if any(tile):
                            index = atlas.setdefault(tile, len(atlas)+1)
                            indices.append(0x3000+index)
                        else:
                            indices.append(0)
                data = b''.join(atlas)
                frame_cache[key] = out.add(struct.pack('<3I', out.add(data) if data else 0,
                    len(data),out.add(struct.pack('<120H', *indices))))
            frames.append((frame_cache[key], max(1, ((ticks & 255)*4 + 2)//5)))
        assert frames
        result.append(out.add(struct.pack('<I', count)+b''.join(struct.pack('<2I', *f) for f in frames)))
    return out.add(struct.pack('<'+'I'*len(result), *result))


def assets(source, out):
    scene = 0x77b620
    actors = []
    for ident in range(15):
        record = 0x740000+ident*32
        header, events = (source_pointer(source, record+k) for k in (0, 6))
        if U16.unpack_from(source,scene+0x7c+ident*2)[0] == 0xb8:
            attacks = [source[scene+0x158+ident], source[scene+0x167+ident]]
        else:
            attacks = [28,49]
        motions = [0,1,*attacks,20,50,54,62,source[scene+0x5e+ident],source[scene+0x6d+ident]]
        actors.append(sequence(source, header, events, motions, out))
    # Extract the common incoming projectile directly from source actor 15 event 1.
    base = 0x740000+15*32
    header, events, colors = (source_pointer(source, base+k) for k in (0,6,12))
    layouts = layout_frames(source, header)
    _, desc = source_layout(source, header)
    n,payload = struct.unpack_from('<HH',source,events+12)
    shots = []
    for j in range(n):
        _,layout,bank = struct.unpack_from('<3H',source,events+payload+12*j)
        size,atlas = parse_wsc_far_descriptor(source,desc)
        surface = bytearray(32*16)
        for flags,dx,dy in layouts[layout]:
            offset = (flags & 511)*32
            assert offset < size
            draw_part(surface,32,tile_pixels(source[atlas+offset:atlas+offset+32]),
                      12+dx,8+dy,bool(flags&0x4000),bool(flags&0x8000))
        for y in (0,8):
            for x in (0,8,16,24):
                shots.append(packed([surface[(y+j)*32+x+i] for j in range(8) for i in range(8)]))
    assert n==3
    return (out.add(struct.pack('<15I', *actors)),out.add(b''.join(shots)),
            out.add(palette(struct.unpack_from('<16H',source,colors+6))))


def field(source, old_scenery, old_blob, out):
    """Reconstruct the bright fight grid from the WSC map under WAIT and the portrait."""
    tiles, size, _, foreground = struct.unpack_from('<4I',old_blob.data,old_scenery-old_blob.base)
    foreground = list(struct.unpack_from('<1024H',old_blob.data,foreground-old_blob.base))
    for y in range(2,18):
        foreground[32*y+16:32*y+28] = [0]*12
    # Extend the contiguous waiting atlas with every original grid tile. BG0 shares this atlas.
    tiles = old_blob.data[tiles-old_blob.base:tiles-old_blob.base+size]
    tile_lookup = {bytes(tiles[i:i+32]):i//32 for i in range(0,len(tiles),32)}
    grid = [0]*1024
    for y in range(1,17):
        for x in range(28):
            w = U16.unpack_from(source,SOURCE_BG+64*y+2*x)[0]
            if w:
                i = (w&511)-0x184
                assert 0<=i<100
                raw = source[0x420000+i*32:0x420020+i*32]
                grid[(y+1)*32+x+1] = tile_lookup[packed(tile_pixels(raw))] | ((w>>4)&0xc00)
    return out.add(struct.pack('<1024H',*grid)), out.add(struct.pack('<1024H',*foreground))
