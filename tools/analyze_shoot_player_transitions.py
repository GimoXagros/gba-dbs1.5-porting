#!/usr/bin/env python3
"""Positive Shoot input/landing contracts; no whole-route reachability claim."""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha


def contracts(r):
    exact(r, 0x7410D6, ['mov ax, 0xc00', 'mov ds, ax', 'mov ax, 0x1000',
        'mov es, ax', 'mov word ptr [0x3a20], 0', 'call 0x7424c6',
        'mov ax, word ptr es:[0x1de]', 'mov bx, word ptr es:[0x1e0]',
        'mov word ptr [0x3a14], ax', 'mov word ptr [0x3a16], bx', 'retf'])
    exact(r, 0x7424C6, ['mov byte ptr [0x3bae], 0', 'mov byte ptr [0x3baf], 0',
        'mov byte ptr [0x3cd6], 0', 'ret'])
    exact(r, 0x741305, ['push word ptr es:[0x65e]', 'push word ptr es:[0x65c]',
        'call 0x743001', 'add sp, 4', 'retf'])
    exact(r, 0x74309A, ['test word ptr [di + 0x20], 0x80', 'je 0x7430f2',
        'test word ptr [di + 0x1e], 5', 'jne 0x7430f2',
        'test word ptr [di + 0x1e], 0xa', 'je 0x7430f2'])
    exact(r, 0x743176, ['mov word ptr [si], 0x2d78',
        'mov word ptr [si + 2], 0x5ffd', 'or word ptr [si + 6], 0x40'])
    exact(r, 0x74120D, ['mov bx, word ptr es:[0x3d0]', 'add bx, bx',
        'jmp word ptr cs:[bx + 0x919]'])
    need(struct.unpack_from('<3H', r, 0x741219) == (0x91F, 0x968, 0x99D),
         'kind2 enters common tail after AI branch')
    exact(r, 0x74129D, ['mov ax, 0x1000', 'mov es, ax',
        'test byte ptr es:[0x3cd], 7', 'jne 0x7412f6',
        'mov si, word ptr es:[0x65c]', 'mov di, word ptr es:[0x65e]'])
    exact(r, 0x7412D5, ['test word ptr [di + 0x20], 0x20', 'je 0x741305'])
    exact(r, 0x773752, ['mov word ptr [si + 0x1e], 0',
        'mov word ptr [si + 0x20], 0'])
    exact(r, 0x773776, ['cmp word ptr [si + 0x28], 0xc00', 'ja 0x773797',
        'push bx', 'push ds', 'mov ax, 0xc00', 'mov ds, ax',
        'mov ax, word ptr [8]', 'mov bx, ax', 'mov ax, 0x197a'])
    exact(r, 0x773797, ['mov word ptr [si + 0x8a], 0xfc43',
        'mov word ptr [si + 0x8c], 0x10', 'mov word ptr [si + 0x8e], 0xc',
        'mov word ptr [si + 0x92], 1', 'mov byte ptr [si + 0x5c], 0x14'])
    exact(r, 0x7737C6, ['mov word ptr [si], 0x1e51',
        'mov word ptr [si + 2], 0x668e'])
    exact(r, 0x773854, ['mov si, word ptr es:[0x65c]',
        'test word ptr [si + 6], 4', 'jne 0x773861', 'retf'])
    exact(r, 0x77386D, ['mov ax, 0x197a', 'mov word ptr [bx], ax',
        'mov ax, 0x71f0', 'mov word ptr [bx + 2], ax'])
    exact(r, 0x766CED, ['and word ptr [si + 6], 0xfffe'])
    exact(r, 0x766E70, ['mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0', 'mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0', 'mov word ptr [si], 0x1d5e',
        'mov word ptr [si + 2], 0x668e'])
    exact(r, 0x76867F, ['test word ptr [di + 0xa], 0x2000', 'jne 0x7686c9'])
    exact(r, 0x7686C9, ['lcall 0x668e, 0xc3', 'retf'])
    exact(r, 0x767A20, ['mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0', 'mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0', 'mov word ptr [si], 0x115d',
        'mov word ptr [si + 2], 0x668e'])
    exact(r, 0x767A3D, ['lcall 0x668e, 0x224', 'or ax, ax', 'je 0x767a47', 'retf',
        'lcall 0x668e, 0x36d', 'or ax, ax', 'je 0x767a51', 'retf',
        'lcall 0x668e, 0x175', 'or ax, ax', 'je 0x767a5b', 'retf',
        'lcall 0x668e, 0x1d6', 'or ax, ax', 'je 0x767a65', 'retf',
        'lcall 0x668e, 0x332', 'or ax, ax', 'je 0x767a6f', 'retf',
        'lcall 0x668e, 0x5d5', 'or ax, ax', 'je 0x767a79', 'retf',
        'and word ptr [si + 8], 0xfff7', 'push 1', 'push 0xc00', 'push di',
        'lcall 0x4fff, 0x2862', 'add sp, 6', 'retf'])
    # These are the six actual helper entries of neutral idle, not an opcode scan.
    for at, rows in (
        (0x766B04, ['push bx', 'xor ax, ax', 'test word ptr [si + 0x20], 0x80',
                    'jne 0x766b11', 'jmp 0x766b98']),
        (0x766C4D, ['xor ax, ax', 'test word ptr [si + 0x1e], 4', 'je 0x766c77']),
        (0x766A55, ['push dx', 'xor ax, ax', 'test word ptr [si + 0x20], 0x40', 'je 0x766ab4']),
        (0x766AB6, ['xor ax, ax', 'test word ptr [si + 0x20], 0x40', 'je 0x766b03']),
        (0x766C12, ['push bx', 'xor ax, ax', 'test word ptr [si + 8], 0x4000',
                    'je 0x766c1f', 'jmp 0x766c4b']),
        (0x766C1F, ['test word ptr [si + 8], 0x100', 'je 0x766c29', 'jmp 0x766c4b']),
        (0x766C29, ['test word ptr [si + 0x20], 0xf00', 'jne 0x766c33', 'jmp 0x766c4b']),
        (0x766EB5, ['push bx', 'push es', 'xor ax, ax',
                    'test word ptr [si + 0x1e], 0xa', 'jne 0x766ec3', 'jmp 0x766f83'])):
        exact(r, at, rows)
    for at, rows in ((0x766B98, ['pop bx', 'retf']), (0x766C77, ['retf']),
        (0x766AB4, ['pop dx', 'retf']), (0x766B03, ['retf']),
        (0x766C4B, ['pop bx', 'retf']), (0x766F83, ['pop es', 'pop bx', 'retf'])):
        exact(r, at, rows)
    exact(r, 0x74190A, ['test word ptr [si + 6], 2', 'je 0x741917',
        'push word ptr [si + 0x28]', 'push word ptr [si + 0x3c]'])
    exact(r, 0x74196A, ['test word ptr [si + 6], 2', 'je 0x741977',
        'pop word ptr [si + 0x3c]', 'pop word ptr [si + 0x28]'])
    exact(r, 0x7419C0, ['mov ax, word ptr [si + 0x3a]',
        'mov dx, word ptr [si + 0x3c]', 'add word ptr [si + 0x26], ax',
        'add word ptr [si + 0x28], dx'])
    exact(r, 0x768619, ['test word ptr [si + 0x4a], 3', 'jne 0x76862f',
        'mov word ptr [si], 0x1b8f', 'mov word ptr [si + 2], 0x668e',
        'and word ptr [si + 6], 0xfffd', 'retf'])
    exact(r, 0x76F9A6, ['test word ptr [di + 6], 1', 'jne 0x76f9cd',
        'mov cx, dx', 'mov bx, 3', 'and cx, bx', 'cmp cx, bx', 'je 0x76f9c0',
        'and word ptr [di + 0x28], 0xff80', 'jmp 0x76f9cd'])
    exact(r, 0x76F919, ['mov cx, word ptr [di + 0x26]', 'or cx, cx', 'js 0x76f937',
        'shr cx, 4', 'mov ax, cx', 'add cx, word ptr [di + 0x42]', 'shr cx, 3',
        'cmp bx, cx', 'jg 0x76f932', 'mov cx, bx', 'dec cx',
        'sub ax, word ptr [di + 0x42]', 'jns 0x76f945'])
    exact(r, 0x76F945, ['shr ax, 3', 'sub cx, ax', 'js 0x76f8e2',
        'add ax, ax', 'add ax, ax', 'inc cx', 'add si, ax', 'mov bx, 4',
        'xor ax, ax', 'xor dx, dx', 'or ax, word ptr es:[si + 2]',
        'or dx, word ptr es:[si]', 'add si, bx', 'dec cx', 'jne 0x76f95a'])
    return dict(grab_owner='ordinary input07FA tail741305 ->743001; kind2 shares tail',
        terminal_input='complete07D6 and its sole callee cannot perform grab or write P1 input',
        neutral_landing='grounded1D5E zero motion -> idle113C/115D; six key helpers inert at held=edge=0',
        direct_terminal_branch='unsigned Y<=0C00 skips193B groundwait; stationarity not established there',
        forced_jump='668E:1E51, parameters FC43/0010/000C,193B waits6:4 before197A',
        drop_restore='pre-cap Y and deltaY saved at741911/14, restored741971/74, committed7419C9',
        drop_limit='movement cap alone is insufficient while drop-through flag6:2 is set')


def geometry(r):
    cells = list(struct.iter_unpack('<HH', r[0x33CA20:0x33CA20 + 56*54*4]))
    need(all(b == 0 and a in (0, 1, 2, 3) for a, b in cells), 'no-force terrain')
    def sample(x, y):
        left = ((x >> 4) - 6) >> 3
        right = min(((x >> 4) + 6) >> 3, 55)
        value = 0
        for col in range(left, right + 1):
            value |= cells[(y >> 7)*56 + col][0]
        return value
    # Terminal182F's strict center interval, including all subpixel fractions.
    fixed = 0
    for x in range(0xDC1, 0xE40):
        for row in (42, 50):
            for fraction in range(128):
                y = row*128 + fraction
                ground = sample(x, y)
                need(ground in (1, 2), 'center landing uses non-kind3 solid/one-way')
                normalized = y & 0xFF80
                need(sample(x, normalized) == ground, 'ground normalization is stable')
                fixed += 1
    empty = 0
    for x in range(7*128 + 6*16, 49*128 - 6*16):
        for row in range(45, 50):
            need(sample(x, row*128) == 0, 'full footprint empty below final platform')
            empty += 1
    need(sample(7*128 + 6*16 - 1, 45*128) != 0,
         'left boundary witness must reject one-unit expansion')
    need(sample(49*128 - 6*16, 45*128) != 0,
         'right boundary witness must reject one-unit expansion')
    return dict(center_normalization_cases=fixed, stable_center_Y=[42*128, 50*128],
        empty_ground_cases=empty, empty_ground_X=[7*128+6*16,49*128-6*16-1],
        empty_rows=list(range(45,50)),
        assumptions=['center proof starts with airborne clear, zero delta and no external displacement',
            'drop proof requires sidewall-retained X and actual sampling before crossing rows45..49'],
        first_ground_alignment_may_move_Y=True, complete_player_domain_proved=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    need(a.source.suffix.lower() == '.wsc', 'only original WSC input permitted')
    need(not a.output.exists(), 'refuse to overwrite frozen evidence')
    r = a.source.read_bytes()
    need(sha(r) == SOURCE_SHA, 'exact original WSC1.5')
    result = dict(source_sha256=sha(r), contracts=contracts(r), geometry=geometry(r))
    rejected = []
    for label, at, mask, check in (
        ('ordinary grab owner', 0x74130F+1, 1, contracts),
        ('terminal direct signedness', 0x77377B, 1, contracts),
        ('drop restoration', 0x741971, 1, contracts),
        ('neutral helper input gate', 0x766B07+3, 1, contracts),
        ('ground normalization', 0x76F9B8+3, 1, contracts),
        ('empty gap cell', 0x33CA20+4*(45*56+7), 1, geometry)):
        bad = bytearray(r); bad[at] ^= mask
        try:
            check(bytes(bad))
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('negative accepted: '+label)
    result.update(negative_controls_rejected=rejected, ROM_modified=False,
        whole_route_closed=False, implementation_change_justified=False)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print('PASS source transitions, bounded geometry, six mutation negatives; whole-route remains open')


if __name__ == '__main__':
    main()
