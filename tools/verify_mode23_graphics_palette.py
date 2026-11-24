#!/usr/bin/env python3
"""Reconstruct mode 23 graphics from source and check linked ARM instructions."""
import argparse
import json
from pathlib import Path
import re
import struct

from verify_shoot_static_companion_clear import Machine, ROOT, need, sha
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
import mode23_native_services
import mode23_palette_phases
import mode23_scene_graphics

ROM, CODE, CTX = 0x08000000, 0x08E00000, 0x02010018
PAL, MIRROR, IO, VRAM = 0x05000000, 0x0203E000, 0x04000000, 0x06000000
SHADOW, SNAPSHOT, PROJECT, PROJECT_END = 0x030012B6, 0x085C1900, 0x0801155C, 0x080116DC
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
AUTHOR = 'B924F1779D586E72E469B93A833040EE417ADB69AD5F976D42CA53C6089B0923'
SOURCE_SPANS = {
    (0x772061, 0x77208B): '760581E89D46555951EAD46CC68139A6F4881444F5D28E9A9D432ED1ECF5BE04',
    (0x7720AB, 0x7720FE): 'C8F46E470692CD97580DCB02CCD64DB7A17A96F39A986281D2C52851EBF5FD19',
    (0x751E8D, 0x751F6B): '205C09848C45077D6D597B44B7224ABF74C9F7EB8E84179DAD8C5B3A2DA98D11',
    (0x74B32D, 0x74B3B9): 'AA9A89080DA124BB838B1F42EFCD3DD3E49BE19CC134D0EB9C429FFC5D92E77B',
    (0x74AA98, 0x74AC0B): 'C61936F5C3548F0827CE34D195E7F02760C23D285A14122BF4737E1FBF79A0C0',
    (0x74B775, 0x74B7D2): 'C868D0355203265EC2BD3E8FC9F97B280DF00F6CDE7A7B08F78765005E3E63F9',
    (0x74B84B, 0x74B8B0): '89AD2FD0BBBC7591189E5312518B054EB03DF70D0EB8C8549B04339DC9531AEB',
    (0x74BA1C, 0x74BA5B): '2A0F8FE411AAFEBD73CEBB8ADE245C3E3657B836199E2DA53E0DC7D0D5D05ABE',
}
FIXTURES = ('m23_intro_resources', 'm23_aim_resources', 'm23_round_start_resources',
            'm23_failure_resources', 'm23_view_install', 'm23_sound', 'm23_bf42_atan')
ENTRIES = ('m23_intro_prepare', 'm23_round_prepare', 'm23_failure_prepare', 'm23_completion_prepare',
           'm23_palette_snapshot', 'm23_palette_prepare_fade_in', 'm23_palette_fade_out',
           'm23_palette_fade_in', 'm23_display_enable', 'm23_obj_color0')

def halfwords(data, start, count):
    return struct.unpack_from(f'<{count}H', data, start)

def pack(words):
    return struct.pack(f'<{len(words)}H', *words)

def rgb(word, transform=lambda value: value):
    blue, green, red = (transform((word >> shift) & 15) for shift in (0, 4, 8))
    return sum((channel * 2 + int(channel > 0)) << shift
               for channel, shift in zip((red, green, blue), (0, 5, 10), strict=True))

def tile_pixels(raw):
    result = bytearray()
    for i in range(0, len(raw), 4):
        pixels = [sum(bool(plane & (128 >> x)) << p for p, plane in enumerate(raw[i:i + 4]))
                  for x in range(8)]
        result.extend(pixels[x] + 16 * pixels[x + 1] for x in range(0, 8, 2))
    return bytes(result)

def map_word(word):
    tile, bank, flips, palette = word & 511, (word >> 13) & 1, word >> 14, (word >> 9) & 15
    return tile + 512 * bank + 1024 * flips + 4096 * palette

def source_assets(source, manifest, assets):
    intro = halfwords(source, 0x41F730, 128)
    # Source calls tile the pattern with horizontal offsets 0 and 16, then 8 and 24.
    maps = {'intro_map': tuple(intro[(y % 8) * 16 + (x - 8 * ((y // 8) % 2)) % 16]
                               for y in range(32) for x in range(32))}
    limits = {'intro_map': 54}
    for name, address, fill, tail, limit in (
        ('round_map', 0x2BED40, 0, 0, 490), ('last_map', 0x2BF130, 0, 0, 490),
        ('power_map', 0x2BF520, 0, 0, 490), ('failure_map', 0x3C3800, 0x2000, 448, 71),
        ('completion_map', 0x3A66C0, None, 0, 56),
    ):
        words = halfwords(source, address, 504)
        if fill is not None:
            words = tuple(word for y in range(18) for word in (*words[y * 28:(y + 1) * 28], *([fill] * 4)))
        maps[name] = words + (fill,) * tail
        limits[name] = limit
    tables = {}
    counts = {}
    for name, words in maps.items():
        need(all((word & 511) < limits[name] if word & 0x2000 else (word & 511) == 0
                 for word in words), f'{name} references only occupied bank1 or inherited bank0 tile0')
        need(max((word >> 9) & 15 for word in words) <= 7, f'{name} within mode 23 BG palette ownership')
        tables[name] = pack([map_word(word) for word in words])
        counts[name] = dict(cells=len(words), bank0_tile0=sum(not (word & 0x2000) for word in words))
    for name, address, count in (
        ('intro', 0x41F830, 54), ('round', 0x2B9BA0, 490), ('last', 0x2BB600, 490),
        ('failure', 0x3B4090, 71), ('completion', 0x3A5FA0, 56),
    ):
        tables[name + '_tiles'] = tile_pixels(source[address:address + count * 32])
        counts[name + '_tiles'] = dict(tiles=count, pixels=64 * count)
    for name, address, count in (
        ('intro', 0x41FEF2, 15), ('round', 0x2BF910, 128), ('last', 0x2BF9F0, 128),
        ('failure', 0x3D8790, 16), ('completion', 0x3A66A0, 16),
    ):
        words = halfwords(source, address, count)
        need(all(word < 0x1000 for word in words), 'source RGB444 channels')
        tables[name + '_palette'] = pack([rgb(word, (lambda v: v // 2) if name == 'intro' else (lambda v: v))
                                          for word in words])
        counts[name + '_palette'] = dict(colors=count)
    need(set(manifest) == set(tables), 'exact relocatable asset inventory')
    placed = sorted(manifest.items(), key=lambda entry: entry[1]['address'])
    first = placed[0][1]['address']
    offset = 0
    for name, row in placed:
        alignment = (offset + 3) & ~3
        payload = tables[name]
        need(first + alignment == row['address'] and not any(assets[offset:alignment])
             and row['bytes'] == len(payload) and row['sha256'] == sha(payload)
             and assets[alignment:alignment + len(payload)] == payload, f'{name} exact author bytes and placement')
        offset = alignment + len(payload)
    need(offset == len(assets), 'complete author asset span')
    return first, tables, counts

class CheckedArm(Machine):
    """Execute only known ARM instructions and unsigned immediate halfword post-index."""
    def execute(self, start, addresses, stop, step_bound):
        pc = start
        positions = set(addresses) | {stop}
        self.snapshot_visits = 0
        for _ in range(step_bound):
            if pc == stop:
                return
            need(pc in positions, f'unmapped execution {pc:08X}')
            self.snapshot_visits += int(pc == SNAPSHOT)
            word = self.get(pc)
            if word & 0x0F6000F0 == 0x004000B0:
                source, dest = (word >> 16) & 15, (word >> 12) & 15
                address = self.r[source]
                need(address % 2 == 0 and source != dest and max(source, dest) < 15,
                     f'bounded aligned non-aliasing post-index halfword at {pc:08X}')
                self.r[15] = pc + 8
                if self.condition(word >> 28):
                    if word & 0x00100000:
                        self.r[dest] = self.get(address, 2)
                    else:
                        self.put(address, self.r[dest], 2, True)
                    step = ((word >> 4) & 0xF0) + (word & 15)
                    self.r[source] = address + (step if word & 0x00800000 else -step)
                pc += 4
            else:
                positions.remove(pc)
                old = pc
                try:
                    pc = super().run(pc, positions, 2)
                except ValueError as err:
                    raise ValueError(f'{pc:08X} {word:08X} LR={self.r[14]:08X} stop={stop:08X}') from err
                positions.add(old)
        raise ValueError('bounded execution did not return')

def link(source, native, manifest, assets, first):
    asm = '\n'.join((mode23_scene_graphics.assembly(manifest), mode23_palette_phases.assembly(source),
                     mode23_native_services.assembly(native)))
    # Numeric absolute BL operands after literal pools misrelocate in this Keystone build.
    native_targets = sorted(set(re.findall(r'^bl (0x[0-9a-f]+)$', asm, re.M)))
    veneers = {target: 'qa_native_' + target[2:] for target in native_targets}
    for target, name in veneers.items():
        asm = asm.replace(f'bl {target}\n', f'bl {name}\n')
    asm += '\n' + '\n'.join(f'{name}: ldr pc,[pc,#-4]\n.word {target}'
                              for target, name in veneers.items())
    labels = set(re.findall(r'^(\w+):', asm, re.M))
    unresolved = {n for n in re.findall(r'^b(?:l)? (\w+)$', asm, re.M) if n not in labels and not n.startswith('0x')}
    need(unresolved == set(FIXTURES), f'exact dependency fixtures {sorted(unresolved)}')
    names = ENTRIES + FIXTURES
    prefix = '\n'.join(f'.word {name}' for name in names) + '\n'
    suffix = '\n'.join(f'{name}: bx lr' for name in FIXTURES)
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(prefix + asm + '\n.ltorg\n' + suffix, CODE)[0])
    sym = dict(zip(names, struct.unpack_from(f'<{len(names)}I', code), strict=True))
    all_addresses = set(range(CODE + len(names) * 4, CODE + len(code), 4))
    all_addresses.update(range(SNAPSHOT, SNAPSHOT + 0x60, 4))
    rom = bytearray(native)
    for address, payload in ((CODE, code), (first, assets)):
        offset = address - ROM
        need(not any(byte != 0xFF for byte in rom[offset:offset + len(payload)]),
             f'fixture image uses blank ROM span at {address:08X}')
        rom[offset:offset + len(payload)] = payload
    return bytes(rom), sym, all_addresses, sha(code)

def invoke(m, sym, pos, label):
    m.writes.clear()
    m.calls.clear()
    regs = m.r[4:12].copy()
    sp = m.r[13]
    m.execute(sym[label], pos, m.r[14], 132000)
    need(m.r[4:12] == regs and m.r[13] == sp, f'{label} preserved callee registers and SP')

def seeds(m, base, count, seed=53):
    for off in range(count):
        m.put(base + off, (seed + off * 37 + (off >> 5) * 11) & 255, 1)

def binary(m, address, count):
    return bytes(m.get(address + off, 1) for off in range(count))

def fixture(rom):
    m = CheckedArm(rom, seed=12, flags=0xB000001F)
    m.r[4] = CTX
    for base, length in ((CTX, 256), (SHADOW - 2, 22), (IO, 0x60), (PAL, 1024), (MIRROR, 1024)):
        seeds(m, base, length)
    return m

def palette_fixture(m):
    colors = [(((i * 53) & 15) << 8) | (((i * 61 + 5) >> 2) & 15) << 4 | ((i * 43 + i // 13) & 15)
              for i in range(256)]
    for i, color in enumerate(colors):
        if i < 128:
            address = PAL + i * 2
        else:
            obj = i - 128
            address = PAL + 0x200 + obj * 2 - (0x100 if obj % 16 == 0 else 0)
            if obj % 16 == 0:
                m.put(address + 0x100, rgb(color ^ 0xFFF), 2)
        m.put(address, rgb(color), 2)
    return colors

def palette_checks(rom, sym, pos):
    def compare(m, colors, levels, up):
        for i, value in enumerate(colors):
            color = rgb(value, (lambda v: min(levels[i // 128], v)) if up else
                        (lambda v: max(0, v - levels[i // 128])))
            offset = 2 * (i % 128) + (0x200 if i >= 128 else 0)
            need(m.get(PAL + offset, 2) == color, f'active RGB trajectory at {offset:03X}')
            if i >= 128 and i % 16 == 0:
                need(m.get(PAL + offset - 0x100, 2) == color, 'BG/OBJ zero aliases')
    def addresses(obj=False):
        return list(range(PAL + (0x200 if obj else 0), PAL + (0x300 if obj else 0x100), 2))
    aliases = list(range(PAL + 0x100, PAL + 0x200, 32))
    def verify_writes(m, expected):
        need([(address, size) for address, _, size in m.writes
              if PAL <= address < PAL + 0x400] == [(a, 2) for a in expected], 'ordered aligned palette writes')
    down = fixture(rom)
    colors = palette_fixture(down)
    invoke(down, sym, pos, 'm23_palette_snapshot')
    verify_writes(down, [])
    for i, color in enumerate(colors):
        address = MIRROR + 2 * i + (0x100 if i >= 128 else 0)
        need(down.get(address, 2) == rgb(color), 'resident snapshot substitutes saved OBJ zero from alias')
    for phase in range(32):
        invoke(down, sym, pos, 'm23_palette_fade_out')
        verify_writes(down, addresses(bool(phase % 2)) + (aliases if phase % 2 else []))
        need(down.get(CTX + 0xD4, 2) == phase + 1 and down.r[0] == int(phase == 31), 'source fade-out callback result')
        if phase == 0:
            # OBJ zeros are intentionally dirty before the first OBJ phase.
            need(all(down.get(address, 2) == rgb(color, lambda v: max(0, v - 1))
                     for address, color in zip(addresses(), colors[:128], strict=True)), 'first even phase only')
        else:
            compare(down, colors, ((phase + 2) // 2, (phase + 1) // 2), False)
    up = fixture(rom)
    colors = palette_fixture(up)
    invoke(up, sym, pos, 'm23_palette_prepare_fade_in')
    verify_writes(up, addresses() + addresses(True) + aliases)
    compare(up, colors, (0, 0), True)
    for phase in range(16):
        invoke(up, sym, pos, 'm23_palette_fade_in')
        verify_writes(up, addresses() + addresses(True) + aliases)
        compare(up, colors, (phase + 1,) * 2, True)
        need(up.get(CTX + 0xD4, 2) == 15 - phase and up.r[0] == int(phase == 15), 'source fade-in callback result')
    return dict(source_fade_out_calls=32, source_fade_in_calls=16, words_per_fade_out=128,
                words_per_fade_in=256, high_zero_aliases=aliases, per_tick_actual_write_geometry=True)

def check_graphics(rom, sym, pos, tables, label, round_id=0):
    m = fixture(rom)
    seeds(m, VRAM, 0x10000)
    m.put(CTX + 0x2A, round_id, 1)
    m.put(SHADOW, 0x80DF, 2)
    m.put(PAL, rgb(0x6E9), 2)
    m.put(PAL + 0x100, rgb(0x19C), 2)
    # Other display state belongs to the predecessor/common services.
    m.put(IO, 0, 2)
    before = dict(m.mem)
    expected = dict(before)
    def stage(address, data):
        expected.update((address + i, v) for i, v in enumerate(data))
    def write(address, value, size=2):
        stage(address, value.to_bytes(size, 'little'))
    def copy(table, address):
        stage(address, tables[table])

    reached = []
    def mark(name, vm):
        reached.append((name, tuple(vm.r[:4])))
    m.services = {sym[name]: (lambda vm, name=name: mark(name, vm)) for name in FIXTURES}
    invoke(m, sym, pos, label)
    if label == 'm23_intro_prepare':
        copy('intro_tiles', VRAM + 0x4000)
        copy('intro_map', VRAM + 0xF800)
        write(PAL, rgb(0x6E9, lambda v: v // 2))
        copy('intro_palette', PAL + 2)
        write(IO + 8, 0x1F02)
        write(IO + 10, 0x1E03)
        write(CTX + 0x34, 112)
        write(CTX + 0x36, 72)
        need([(name, args[0]) for name, args in reached] == [('m23_intro_resources', CTX + 0x34)], 'intro presentation ABI')
        native_display, window = 0x80DF, None
    elif label == 'm23_round_prepare':
        name = 'last' if round_id == 6 else 'round'
        copy(name + '_tiles', VRAM + 0x4000)
        copy(name + '_map', VRAM + 0xF000)
        copy('power_map', VRAM + 0xF800)
        copy(name + '_palette', MIRROR)
        stage(MIRROR + 0x200, bytes(before[PAL + 0x200 + i] for i in range(256)))
        for i in range(8):
            off = i * 32
            stage(MIRROR + 0x200 + off, bytes(before[PAL + 0x100 + off + j] for j in range(2)))
            write(PAL + 0x100 + off, 0)
        stage(PAL, bytes(256))
        stage(PAL + 0x200, bytes(256))
        write(CTX + 0x34, 112)
        write(CTX + 0x36, 72)
        write(CTX + 0xD4, 16)
        write(SHADOW + 2, 0, 4)
        native_display, window = 0x8025, (180, 112, 224, 112)
        need([(name, args[0]) for name, args in reached] ==
             [('m23_aim_resources', CTX + 0x84), ('m23_round_start_resources', CTX + 0x34)], 'round presentation ABI')
        need(m.snapshot_visits == 1, 'round calls actual snapshot once')
    elif label == 'm23_failure_prepare':
        copy('failure_tiles', VRAM + 0x4000)
        copy('failure_map', VRAM + 0xF800)
        copy('failure_palette', PAL)
        write(CTX + 0x34, 0xFFEC)
        write(CTX + 0x36, 76)
        write(CTX + 0x3C, (before[CTX + 0x3C] + 256 * before[CTX + 0x3D]) | 0x6400)
        native_display, window = 0x8026, (0, 50, 1, 80)
        need([name for name, _ in reached] == ['m23_failure_resources', 'm23_sound']
             and reached[0][1][0] == CTX + 0x34 and reached[1][1][:2] == (0x24, 4), 'failure call order and ABI')
    else:
        copy('completion_tiles', VRAM + 0x4000)
        copy('completion_palette', PAL)
        for y in range(18):
            stage(VRAM + 0xF800 + y * 64, tables['completion_map'][y * 56:(y + 1) * 56])
        native_display, window = 0x8006, None
        need(len(reached) == 1 and reached[0][0] == 'm23_view_install'
             and (reached[0][1][0], reached[0][1][2]) == (CTX + 0x34, 0x80), 'completion commercial resource view ABI')
    low_writes = [(value, size) for address, value, size in m.writes if address == SHADOW]
    expected_low = [] if label == 'm23_intro_prepare' else [(native_display & 255, 1)]
    if label in ('m23_failure_prepare', 'm23_completion_prepare'):
        expected_low.insert(0, (0, 1))
    need(low_writes == expected_low, f'{label} ordered display shadow writes')
    write(SHADOW, native_display)
    if window is not None:
        for displacement, byte in zip((6, 8, 7, 9), window, strict=True):
            write(SHADOW + displacement, byte, 1)
    for address, value in expected.items():
        need(m.get(address, 1) == value, f'{label} bytes at {address:08X}')
    allowed = {address for address in expected if before[address] != expected[address]}
    # Output writes may idempotently store a byte identical to the sentinel.
    ranges = {
        'm23_intro_prepare': ((IO + 8, 4), (VRAM + 0x4000, 1728), (VRAM + 0xF800, 2048), (PAL, 32), (CTX + 52, 4)),
        'm23_round_prepare': ((VRAM + 0x4000, 15680), (VRAM + 0xF000, 1152), (VRAM + 0xF800, 1152),
                              (PAL, 256), (PAL + 0x200, 256), (MIRROR, 256), (MIRROR + 0x200, 256), (CTX + 52, 4),
                              (CTX + 0xD4, 2), (SHADOW + 2, 4),
                              *((PAL + 0x100 + i * 32, 2) for i in range(8))),
        'm23_failure_prepare': ((VRAM + 0x4000, 2272), (VRAM + 0xF800, 2048), (PAL, 32), (CTX + 52, 4), (CTX + 60, 2)),
        'm23_completion_prepare': ((VRAM + 0x4000, 1792), (PAL, 32),
                                   *((VRAM + 0xF800 + y * 64, 56) for y in range(18))),
    }
    allowed |= {address for a, size in ranges[label] for address in range(a, a + size)}
    if label != 'm23_intro_prepare':
        allowed.add(SHADOW)
    if window is not None:
        allowed.update(SHADOW + off for off in (6, 7, 8, 9))
    sp = m.r[13]
    need(all(address in allowed or sp - 256 <= address < sp for a, _, size in m.writes
             for address in range(a, a + size)), f'{label} exact declared/shadow/local stack write bounds')
    need(binary(m, VRAM, 32) == bytes(before[VRAM + i] for i in range(32)), 'inherited bank0 tile0 preserved')
    if label != 'm23_intro_prepare':
        m.put(IO + 8, 0x1F02, 2)
        m.put(IO + 0xA, 0x1E03, 2)
    expected_backdrop = m.get(PAL + 0x100, 2)
    m.execute(PROJECT, range(PROJECT, PROJECT_END, 4), PROJECT_END, 1000)
    need(m.get(PAL, 2) == expected_backdrop, 'actual common backdrop selects BG alias for shadow high byte80')
    need((m.get(IO + 8, 2), m.get(IO + 0xA, 2)) == (0x1F02, 0x1E03), 'common BG pass preserves charblock and map bases')
    low = native_display & 255
    physical = 0x0800 + (0x0200 if low & 1 else 0) + (0x0100 if low & 2 else 0) \
        + (0x1000 if low & 4 else 0) + (0x4000 if low & 0x20 else 0)
    need(m.get(IO, 2) == physical, 'actual common screen/window/OBJ enable')
    if window is not None:
        left, top, right, bottom = window
        need(m.get(IO + 0x42, 2) == (left + 8) * 256 + right + 8
             and m.get(IO + 0x46, 2) == (top + 8) * 256 + bottom + 8, 'actual WIN1H/V sourced with one 8px margin')
    if label == 'm23_round_prepare':
        need(all(m.get(IO + off, 2) == 0xFFF8 for off in (0x10, 0x12, 0x14, 0x16)), 'reset projects all four -8 scrolls')
    return dict(entry=label, round=round_id, shadow=native_display, physical_dispcnt=physical,
                physical_bg0cnt=m.get(IO + 8, 2), physical_bg1cnt=m.get(IO + 10, 2),
                physical_win1h=m.get(IO + 0x42, 2) if window is not None else None,
                physical_win1v=m.get(IO + 0x46, 2) if window is not None else None)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('source', 'native', 'author-dir', 'report'):
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    source, native = args.source.read_bytes(), args.native.read_bytes()
    metadata, assets = (args.author_dir / 'report.json').read_bytes(), (args.author_dir / 'assets.bin').read_bytes()
    need((sha(source), sha(native), sha(metadata)) == (SOURCE, NATIVE, AUTHOR), 'pinned source, native and author manifest')
    for (start, stop), digest in SOURCE_SPANS.items():
        need(sha(source[start:stop]) == digest, f'source behavior span {start:06X}')
    manifest = json.loads(metadata)['tables']
    first, tables, counts = source_assets(source, manifest, assets)
    rom, sym, addresses, code_sha = link(source, native, manifest, assets, first)
    phases = palette_checks(rom, sym, addresses)
    graphics = [check_graphics(rom, sym, addresses, tables, ENTRIES[1], round_id) for round_id in range(7)]
    graphics += [check_graphics(rom, sym, addresses, tables, ENTRIES[i]) for i in (0, 2, 3)]
    report = dict(status='MODE23_GRAPHICS_PALETTE_INDEPENDENT_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  source_sha256=sha(source), native_sha256=sha(native), author_manifest_sha256=sha(metadata),
                  assets_sha256=sha(assets), bytes=len(assets), reconstructed=counts, phases=phases,
                  constructors=graphics, actual_linked_code_sha256=code_sha,
                  modules={m.__name__: sha(Path(m.__file__).read_bytes())
                           for m in (mode23_native_services, mode23_palette_phases, mode23_scene_graphics)},
                  exercised_common_display=[PROJECT, PROJECT_END], external_call_fixtures=FIXTURES,
                  limits=['Mode table, task lifetime and exclusive mirror ownership require integration evidence',
                          'Predecessor creates blank tile0 and black entry palette0 on ordinary character-select path',
                          'No registered scene execution or video/audio result'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))

if __name__ == '__main__':
    main()

