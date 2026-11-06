#!/usr/bin/env python3
"""Narrow terminal common-tile consumers and child countdown contracts.

These are consumer bounds, not a proof of the camera range or route safety.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_shoot_terminal_bx import exact, need, SOURCE
from build_character_p0_completion import source_pointer, source_commands, source_layout
from build_shoot_initializer import parse_p1, convert_p1
from verify_shoot_terminal_pause import arm


def contracts(s, b):
    exact(s, 0x7437A1, ['mov dx, 1', 'cmp word ptr [bp + 6], 0',
        'je 0x7437ad', 'mov dx, 0x99'])
    exact(s, 0x7437BE, ['cmp word ptr [bp + 0xa], 0', 'je 0x7437ce',
        'mov ax, 0x3c0', 'sub ax, 0', 'add bx, ax', 'add di, ax'])
    exact(s, 0x7437D3, ['push word ptr [bp + 6]', 'push dx',
        'push 0x1800', 'push 0x4000'])
    exact(s, 0x75243A, ['mov ax, word ptr [bp + 0x20]',
        'mov dx, word ptr [bp + 0x22]', 'mov word ptr es:[di + 0x10], ax'])
    # Alternate source graphics banks change the fixed tile identity too.
    exact(s, 0x752AE9, ['mov ax, word ptr es:[di + 0x10]',
        'add word ptr [bp - 6], ax', 'test word ptr es:[di + 8], 2',
        'je 0x752b14', 'mov al, byte ptr es:[di + 0x14]', 'or al, al',
        'je 0x752b14', 'mov si, word ptr es:[di + 0x36]',
        'mov ds, word ptr es:[di + 0x38]', 'mov ax, word ptr es:[di + 0x3a]',
        'out 0xc2, al', 'mov ax, word ptr [si + 0xa]', 'add word ptr [bp - 6], ax'])
    exact(s, 0x749CE7, ['push 5', 'push 0x6d', 'push 0x1800', 'push 0x4000',
        'push 0xbd', 'push 0x27ac', 'push 0', 'push 0xbd', 'push 0x244e',
        'push 0', 'push 0xbd', 'push 0x223b', 'push 0', 'push 0xc00',
        'push di', 'lcall 0x4fff, 0x23f4'])
    exact(s, 0x752517, ['mov al, byte ptr [bx]', 'mov byte ptr es:[di + 0x15], al'])
    exact(s, 0x752885, ['mov ax, word ptr [bp + 0xa]',
        'sub byte ptr es:[di + 0x15], al', 'cmp byte ptr es:[di + 0x15], 0',
        'jl 0x752896', 'jmp 0x7529f5'])
    exact(s, 0x7528A9, ['test word ptr es:[di + 0xa], 1', 'jne 0x7528c3',
        'dec word ptr es:[di + 0x18]', 'xor byte ptr es:[di + 0x14], 1',
        'or word ptr es:[di + 0xa], 0x2000', 'jmp 0x7529f5'])
    exact(s, 0x7528F6, ['mov al, byte ptr [bx]', 'cmp al, 2', 'jae 0x7528fe',
        'mov al, 2', 'add byte ptr es:[di + 0x15], al'])
    exact(s, 0x74A098, ['test word ptr [di + 0xa], 0x2000', 'jne 0x74a0ae',
        'push 1', 'push 0xc00', 'push di', 'lcall 0x4fff, 0x2862',
        'add sp, 6', 'retf', 'push 0xc00', 'push si',
        'lcall 0x4090, 0x181e', 'add sp, 4', 'retf'])
    exact(s, 0x7421B6, ['test byte ptr es:[0x3cd], 7', 'je 0x7421c1',
        'jmp 0x7421e9', 'and word ptr [si + 6], 0xfffb',
        'or word ptr [si + 8], 8', 'push si', 'lcall [si]'])
    exact(s, 0x773669, ['mov word ptr [si + 0x42], 0x97'])
    exact(s, 0x7736F8, ['dec word ptr [si + 0x42]', 'jne 0x773723'])
    exact(s, 0x773723, ['xor byte ptr es:[0x3cd], 7'])
    arm(b, 0x128BC, ['ldrb r0, [r1]', 'strb r0, [r5, #0x17]'])
    arm(b, 0x12AA0, ['ldrsb r8, [r5, #0x17]', 'subs r8, r8, r0',
        'strb r8, [r5, #0x17]', 'bpl #0x8012bb0'])
    arm(b, 0x12B3C, ['ldrb r0, [r1]', 'ldrb r8, [r5, #0x17]',
        'add r8, r8, r0', 'strb r8, [r5, #0x17]'])


def expiry(durations):
    # The first row starts at duration, subsequent rows ADD duration to -1.
    # There is one extra update in total, not one extra per row.
    index, left, updates = 0, durations[0], 0
    while index < len(durations):
        updates += 1
        left -= 1
        if left < 0:
            index += 1
            if index < len(durations):
                left += durations[index]
    return updates


def proof(s, b):
    contracts(s, b)
    characters = []
    for record in (*range(15), *range(30,45)):
        p0 = source_pointer(s, 0x740000 + record * 32)
        layouts, _ = source_layout(s, p0)
        _, events, frames = source_commands(s, record)
        flags, = struct.unpack_from('<H', s, p0 + 14)
        alternate, = struct.unpack_from('<H', s, p0 + 10)
        relative = {struct.unpack_from('<H', layouts[l][1], j * 4)[0] & 511
            for _, _, l, _ in frames for j in range(layouts[l][0])}
        actual = {1 + tile + bank for tile in relative
                  for bank in ((0, alternate) if flags & 2 else (0,))}
        need(max(actual) <= (52 if record < 15 else 72),
             'all P1 animations remain in fixed-base1 common tile bounds')
        characters.append(dict(record=record, events=events, frames=len(frames),
            relative_max=max(relative), alternate_offset=alternate, alternating=bool(flags & 2),
            fixed_base1_tile_min=min(actual), fixed_base1_tile_max=max(actual)))
    parsed = parse_p1(s, 0x3D23B0, 0x108)
    need(len(parsed['commands']) == 1 and parsed['commands'][0][:2] == (15,12),
         'one event and15direct rows')
    rows = parsed['payloads'][0]
    durations = [row[0] & 255 for row in rows]
    need(durations == [2,2,2,4,2,2,2,32,2,2,2,2,2,2,2], 'exact child lifetime rows')
    need(all(not row[3] & 1 for row in rows), 'child event cannot loop')
    converted = convert_p1(parsed, 0x5C4800)
    need(b[0x5C4800:0x5C4800+len(converted)] == converted, 'actual resident child P1')
    native_durations = [b[0x5C4818 + i * 16] for i in range(15)]
    source_updates, native_updates = expiry(durations), expiry(native_durations)
    need((source_updates, native_updates) == (63,56), 'exact complete countdown bounds')
    need(source_updates + 1 < 75 and native_updates + 1 < 60,
         'following callback retirement fits terminal unpaused update budget')
    return dict(characters=characters,
        P1_consumer_bound=dict(fixed_base=1, base_form_all_animation_tiles=[1,52],
            base_and_evolved_all_animation_tiles=[1,72],
            camera_common_clear_disjoint_if_BX_at_least=261,
            limit='fixed-base binding1 is required; this does not establish reached BX'),
        child_6D=dict(source_durations=durations, native_durations=native_durations,
            complete_updates=[source_updates,native_updates],
            following_callback_retirement_updates=[source_updates+1,native_updates+1],
            terminal_unpaused_budget=[75,60],
            limit='pre-existing93E7children only; no new spawn and final9798 callback ownership required'),
        ROM_modified=False, runtime_executed=False,
        remaining='actual camera tracking range, no-new-child producer chain, and non-common owner consumers')


def main():
    p = argparse.ArgumentParser()
    for name in ('source','current','output'): p.add_argument(name,type=Path)
    a = p.parse_args()
    need(not a.output.exists(), 'fresh evidence required')
    s,b = a.source.read_bytes(),a.current.read_bytes()
    sha=lambda data:hashlib.sha256(data).hexdigest().upper()
    need(sha(s)==SOURCE,'source identity')
    report=proof(s,b)
    rejected=[]
    for label,native,site in [('P1 fixed base',False,0x7437A2),
        ('evolved resource stride',False,0x7437C5),('alternate bank',False,0x752B0E),
        ('countdown initializer',False,0x752517),('countdown carry',False,0x7528FE),
        ('child loop',False,0x3D23B0+12+6),('child release',False,0x74A0B2),
        ('native countdown carry',True,0x12B44),('actual child duration',True,0x5C4818)]:
        x,y=bytearray(s),bytearray(b)
        (y if native else x)[site]^=1
        try: proof(x,y)
        except ValueError: rejected.append(label)
        else: raise ValueError('ineffective mutation '+label)
    report.update(status='PASS',source_sha256=SOURCE,current_sha256=sha(b),negative_controls=rejected)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS base/evolved P1 animations bound1..72; child retirement64/57updates;9negatives')


if __name__=='__main__': main()
