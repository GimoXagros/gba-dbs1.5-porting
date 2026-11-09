#!/usr/bin/env python3
"""Bound the 6D static owners and distinguish blanking from pixel alias parity."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_shoot_terminal_bx import exact, need, SOURCE
from analyze_shoot_scene_ownership import arm_at
from build_character_p0_completion import (
    source_pointer, source_layout, source_commands, converted_tiles,
)

NATIVE = '35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A'
BASE = 0x08000000


def u(data, at):
    return struct.unpack_from('<I', data, at)[0]


def contracts(s, b):
    exact(s, 0x747AD1, ['mov si, word ptr es:[0x65e]',
        'mov word ptr [bp - 6], si', 'mov di, word ptr es:[0x65c]',
        'mov word ptr [bp - 8], di'])
    exact(s, 0x747CA9, ['push 0x6d', 'push 0x4000', 'push 0xbd',
        'push 0x244e', 'push 0', 'lcall 0x4fff, 0x226e', 'add sp, 0xa',
        'push 0x137', 'push 0x4000', 'push 0xbd', 'push 0x20ca',
        'push 0', 'lcall 0x4fff, 0x226e'])
    exact(s, 0x747CF0, ['mov si, di', 'test word ptr [si + 8], 0x4000',
        'je 0x747d6f', 'and word ptr [si + 8], 0xbfff',
        'xor ax, ax', 'xor dx, dx', 'mov al, byte ptr [si + 0x10]',
        'mov dl, byte ptr [si + 0x11]', 'push 0', 'push dx', 'push ax',
        'lcall 0x4090, 0x2e74'])
    exact(s, 0x749CE7, ['push 5', 'push 0x6d', 'push 0x1800',
        'push 0x4000', 'push 0xbd', 'push 0x27ac', 'push 0',
        'push 0xbd', 'push 0x244e', 'push 0', 'push 0xbd',
        'push 0x223b', 'push 0', 'push 0xc00', 'push di',
        'lcall 0x4fff, 0x23f4'])
    exact(s, 0x74918B, ['push 5', 'push 0x137', 'push 0x1800',
        'push 0x4000', 'push 0xbd', 'push 0x27a9', 'push 0',
        'push 0xbd', 'push 0x20ca', 'push 0', 'push 0x8d',
        'push 0x2fec', 'push 0', 'push 0xc00', 'push di',
        'lcall 0x4fff, 0x23f4'])
    exact(s, 0x743867, ['mov dx, 0x49', 'cmp word ptr [bp + 6], 0',
        'je 0x743873', 'mov dx, 0x6d', 'push dx', 'push 0x4000',
        'push word ptr es:[di + 0x1e4]', 'push word ptr es:[di + 0x1e2]',
        'push word ptr es:[di + 0x1e0]', 'lcall 0x4fff, 0x226e'])
    exact(s, 0x7525FF, ['mov dx, word ptr es:[di + 8]', 'and dx, 2',
        'jne 0x75260c', 'jmp 0x7526aa'])
    exact(s, 0x752796, ['mov dx, word ptr es:[di + 8]', 'and dx, 2',
        'jne 0x7527a3', 'jmp 0x752841'])
    exact(s, 0x752984, ['mov ax, word ptr es:[di + 8]', 'and ax, 2',
        'jne 0x752990', 'jmp 0x7529f5'])
    exact(s, 0x749D2C, ['push 0', 'push 0xc00', 'push di',
        'lcall 0x4fff, 0x24cb', 'add sp, 6',
        'or word ptr [di + 8], 0x2000'])
    exact(s, 0x752297, ['shr dx, 1', 'xor ax, ax', 'mov es, ax',
        'mov di, word ptr [bp + 0xe]', 'shl di, cl',
        'add di, word ptr [bp + 0xc]', 'mov cx, dx', 'cld',
        'rep movsw word ptr es:[di], word ptr [si]'])
    for adapter, p0, tile in ((0x5C4500, 0x5DB300, 0x6D),
                              (0x5C4600, 0x5DB400, 0x137)):
        need(u(b, adapter + 0x80) == BASE + p0 and
             u(b, adapter + 0x88) == tile, 'actual native constructor bindings')
    # Existing draw reads descriptor pixels, not shared fixed-base RAM.
    arm_at(b, 0x12C8C, ['ldr r4, [r5, #0x48]', 'ldr fp, [r4, #4]',
        'ldrh r1, [r5, #8]', 'tst r1, #2', 'addne fp, fp, r3, lsl #3',
        'ldr fp, [fp, #4]'])


def resource(s, p0, base):
    layouts, desc = source_layout(s, p0)
    need(struct.unpack_from('<H', s, p0 + 14)[0] == 8,
         'positive static P0 flags8')
    need(struct.unpack_from('<H', s, p0 + 8)[0] == 5,
         'source tile stride32')
    _, pixels = converted_tiles(s, desc)
    tiles = {struct.unpack_from('<H', parts, k * 4)[0] & 511
             for n, parts in layouts for k in range(n)}
    need(max(tiles) * 32 + 32 <= len(pixels), 'bounded descriptor0 layout reads')
    return pixels, dict(p0=p0, descriptor=desc, layouts=len(layouts),
        bytes=len(pixels), tile_min=base + min(tiles), tile_max=base + max(tiles),
        upload_tile_range=[base, base + len(pixels)//32 - 1],
        source_byte_range_half_open=[0x4000 + base*32, 0x4000 + base*32 + len(pixels)],
        descriptor_indexed=False)


def proof(s, b):
    contracts(s, b)
    child, child_info = resource(s, 0x3D44E0, 0x6D)
    _, other_info = resource(s, 0x3D0CA0, 0x137)
    need((child_info['bytes'], child_info['layouts'], child_info['tile_max']) ==
         (768, 8, 132), '93E7 exact static interval')
    need((other_info['bytes'], other_info['layouts'], other_info['tile_min']) ==
         (1568, 18, 311), '888B is137, outside6D common projection')
    for source_p1 in (0x3D23B0, 0x0DFEC0):
        need(struct.unpack_from('<H', s, source_p1 + 2)[0] == 0,
             'child P1 adds no indexed flag')
    desc = u(b, 0x5DB304) - BASE
    need(u(b, desc) == len(child) and
         b[u(b, desc + 4) - BASE:u(b, desc + 4) - BASE + len(child)] == child,
         'native93E7 descriptor0 pixels exact converted source')
    rows = []
    for record in (*range(15, 30), *range(45, 60)):
        p0 = source_pointer(s, 0x740000 + record * 32)
        pixels, info = resource(s, p0, 0x6D)
        _, events, frames = source_commands(s, record)
        # Compare pixels after the same source preload address aliases 93E7.
        overlap = min(len(child), len(pixels), 23 * 32)
        different = [i for i in range(overlap // 32)
                     if child[i*32:(i+1)*32] != pixels[i*32:(i+1)*32]]
        need(different, 'positive companion/93E7 alias pixel distinction')
        group = 0x4A82D8 if record < 30 else 0x60B1E0
        native_p0 = u(b, group + (record % 15) * 32) - BASE
        need(struct.unpack_from('<H', b, native_p0 + 14)[0] == 8,
             'actual companion static P0')
        info.update(record=record, events=events, frames=len(frames),
                    alias_tiles_compared=overlap//32,
                    alias_different_logical_tiles=[0x6D+i for i in different])
        rows.append(info)
    need(max(r['tile_max'] for r in rows) == 144, 'P2 companion upper tile144')
    return dict(status='STATIC_6D_ALIAS_FACTS_PASS', child_93E7=child_info,
        excluded_888B=other_info, companions=rows,
        candidate_clear_tiles=[109, 131],
        event_or_child_creation_restores_pixels=False,
        companion_reload_can_replace_child_pixels=True,
        full_source_pixel_alias_parity_proven=False,
        extension_approved=False,
        initial_preload_order=['Existing companion preload in2E74',
            'Shoot747CB7 overwrites109..132 with93E7',
            'Shoot747CCE writes888B311..359',
            'Optional FIRST-only2E74 at747D0C writesbase49 companion'],
        extension='Blank-only candidate identified, not approved: restored pixels require actual shared-source writer provenance.',
        ordering_dependency='analyze_shoot_companion_draw_order.py: actor preloads precede battle6000 draw.',
        limit='No blanket child quiescence, arbitrary other writers, live Shoot entry or source shared-pixel emulation established.',
        ROM_modified=False, runtime_executed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'current', 'output'):
        parser.add_argument(name, type=Path)
    a = parser.parse_args()
    need(not a.output.exists(), 'fresh report required')
    s, b = a.source.read_bytes(), a.current.read_bytes()
    sha = lambda data: hashlib.sha256(data).hexdigest().upper()
    need((sha(s), sha(b)) == (SOURCE, NATIVE), 'exact source/corrected component')
    result = proof(s, b)
    negatives = []
    for name, native, at in [('93E7 base', False, 0x749CEA),
        ('888B base', False, 0x74918E), ('side1 reload', False, 0x743871),
        ('event upload gate', False, 0x752606), ('update upload gate', False, 0x75298A),
        ('static child flag', False, 0x3D44EE), ('native child identity', True, 0x5C4580)]:
        x, y = bytearray(s), bytearray(b)
        (y if native else x)[at] ^= 1
        try:
            proof(x, y)
        except (ValueError, AssertionError):
            negatives.append(name)
        else:
            raise ValueError('accepted mutation ' + name)
    result.update(source_sha256=SOURCE, current_sha256=NATIVE,
                  negative_controls_rejected=negatives)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('PASS 30 companion aliases;93E7 static6D;888B excluded137;7 negatives')


if __name__ == '__main__':
    main()
