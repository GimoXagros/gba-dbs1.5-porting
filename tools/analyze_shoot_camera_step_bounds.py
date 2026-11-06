#!/usr/bin/env python3
"""Finite source camera-step closure, including ring-scroll alignment."""
import argparse
import json
from pathlib import Path

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha


def contracts(r):
    exact(r, 0x752F22, ['mov byte ptr [di + 0x1a], al', 'mov byte ptr [di + 0x1b], al',
        'mov word ptr [di + 0x10], ax', 'mov word ptr [di + 0x12], ax',
        'mov word ptr [di + 0x14], ax', 'mov word ptr [di + 0x16], ax',
        'mov byte ptr [di + 0x18], al', 'mov byte ptr [di + 0x19], al'])
    exact(r, 0x752F18, ['xor ax, ax'])
    exact(r, 0x77DD7C, ['lcall 0x4fff, 0x2f1c', 'add sp, 4'])
    exact(r, 0x7535D3, ['xor cx, cx', 'mov cl, al', 'shr cx, 3', 'mov ah, cl',
        'shl ah, 3', 'inc cx', 'sub al, ah', 'jne 0x7535e7', 'dec cx',
        'mov al, 8', 'xor ah, ah', 'test word ptr [bp + 0xa], 4',
        'jne 0x7535f2', 'neg ax', 'mov word ptr [di + 0x36], ax'])
    exact(r, 0x75362C, ['mov bh, al', 'mov bl, byte ptr [di + 0x1b]',
        'xor ax, ax', 'mov al, bl', 'and al, 7', 'or ax, ax', 'je 0x75364a',
        'add al, bh', 'cmp ax, 0xef', 'jge 0x75364a', 'cmp ax, 8',
        'jg 0x75364a', 'jmp 0x7536e3'])
    exact(r, 0x753948, ['xor ax, ax', 'mov al, byte ptr [di + 0x19]', 'add al, bh',
        'je 0x75399c', 'cmp ax, 0xef', 'jge 0x75398e', 'cmp ax, 0x90',
        'je 0x7539a7', 'jg 0x7539bc', 'test word ptr [bp + 6], 4',
        'jne 0x753972'])
    exact(r, 0x753988, ['xor cx, cx', 'inc cx', 'jmp 0x7539c8'])
    exact(r, 0x75398E, ['mov word ptr [bp - 2], 0x11', 'xor cx, cx',
        'mov word ptr [bp - 4], cx', 'dec cx', 'jmp 0x7539c8'])
    exact(r, 0x75399C, ['xor cx, cx', 'mov word ptr [bp - 2], cx',
        'mov word ptr [bp - 4], cx', 'jmp 0x7539c8'])
    exact(r, 0x7539A7, ['mov word ptr [bp - 2], 0x11',
        'mov word ptr [bp - 4], 0x12', 'xor cx, cx', 'inc cx', 'dec bl',
        'jmp 0x7539c8'])
    exact(r, 0x7539BC, ['xor cx, cx', 'mov word ptr [bp - 2], cx',
        'mov word ptr [bp - 4], 0x12', 'inc cx', 'inc cx'])
    exact(r, 0x7539C8, ['test word ptr [bp + 6], 0x80', 'jne 0x753a01',
        'mov dx, word ptr [di + 0xe]', 'sub dx, word ptr [di + 0x16]',
        'sub dx, cx', 'je 0x7539b9', 'xor dx, dx',
        'mov dl, byte ptr [di + 0x19]', 'shr dx, 3',
        'add dx, word ptr [di + 0x16]', 'add dx, cx', 'inc dx', 'je 0x7539b9'])
    exact(r, 0x7539B9, ['jmp 0x753ad3'])
    exact(r, 0x753AD3, ['xor bx, bx', 'pop ds', 'pop es', 'pop di',
        'pop si', 'pop cx', 'mov sp, bp', 'pop bp', 'retf'])
    exact(r, 0x7536E6, ['or bh, bh', 'jne 0x7536f2',
        'or word ptr [di + 0x3e], 0x8000', 'jmp 0x75375d'])
    exact(r, 0x7536F2, ['mov dx, bx', 'add dh, byte ptr [di + 0x1b]',
        'mov byte ptr [di + 0x1b], dh', 'xor dx, dx',
        'mov dl, byte ptr [di + 0x19]', 'add dl, bh', 'cmp dx, 0xef',
        'jge 0x753713', 'cmp dx, 0x90', 'jge 0x75371e', 'jmp 0x75372b'])
    exact(r, 0x753713, ['mov dh, 0x90', 'add dl, dh',
        'sub word ptr [di + 0x16], 1', 'jmp 0x75372b'])
    exact(r, 0x75371E, ['mov dh, 0x90', 'sub dh, byte ptr [di + 0x19]',
        'mov dl, bh', 'sub dl, dh', 'add word ptr [di + 0x16], 1'])
    exact(r, 0x75375D, ['mov ax, word ptr [di + 0x16]', 'shl ax, 3',
        'mov cx, 0x12', 'mul cx', 'xor cx, cx',
        'mov cl, byte ptr [di + 0x19]', 'add ax, cx', 'mov word ptr [di + 0x12], ax'])


def step(y, ring, delta, enforce_bounds=True):
    block, offset = divmod(y, 144)
    fraction = ring & 7
    edge = (fraction + delta) & 255
    if fraction == 0 or edge >= 239 or edge > 8:
        prospective = (offset + delta) & 255
        if prospective == 0:
            row_delta = 0
        elif prospective >= 239:
            row_delta = -1
        elif prospective == 144:
            row_delta = 1
        elif prospective > 144:
            row_delta = 2
        else:
            row_delta = int(delta > 0)
        if enforce_bounds and (3 - block - row_delta == 0 or
                ((offset >> 3) + block + row_delta + 1) & 65535 == 0):
            return y, ring
    return y + delta, (ring + delta) & 255


def analyze(r):
    need(sha(r) == SOURCE_SHA, 'immutable original')
    contracts(r)
    count = blocked = 0
    for y in range(289):
        for ring in range(y & 7, 256, 8):
            for delta in (*range(-8, 0), *range(1, 9)):
                after, next_ring = step(y, ring, delta)
                need(0 <= after <= 288, 'every actual bounded camera substep stays in0..288')
                need((after & 7) == (next_ring & 7), 'ring/camera tile-phase invariant')
                blocked += after == y
                count += 1
    need(step(288, 32, 1, False)[0] == 289 and step(0, 0, -1, False)[0] == -1,
         'both boundary gates are necessary')
    negatives = []
    for at in (0x7539D7, 0x7539E7, 0x753AD3, 0x75363D):
        bad = bytearray(r); bad[at] ^= 1
        try:
            contracts(bad)
        except ValueError:
            negatives.append(hex(at))
        else:
            raise ValueError('ineffective mutation')
    return dict(source_sha256=SOURCE_SHA, cases=count, blocked_substeps=blocked,
        camera_Y=[0, 288], substep_range=[-8,8], phase_invariant='ringY&7 == cameraY&7',
        source='3367/3945 nonwrapping boundary checks cancel movement viaBX=0',
        texture_policy='all texture banks assumed present; missing banks only cancel more steps',
        conditions=['descriptorheight3, wrappingbit80clear, resetzero or validpreviousstate',
                    'all writes use reset or these camera steps; caller ownership audited separately'],
        negative_controls_rejected=negatives, ROM_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh output required')
    result=analyze(a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',result['cases'],'camera substeps; exact range0..288 and ringphase preserved')


if __name__=='__main__':
    main()
