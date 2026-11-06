#!/usr/bin/env python3
"""Bounded source proof for Shoot player action/landing ownership.

Reads immutable commercial source and exact v67 only. No emulation/save access.
The report separates closed action-family facts from unresolved whole-route
ownership; it must not be used to enable the external caller by itself.
"""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha

V67 = 'A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F'


def h(data, at):
    return struct.unpack_from('<H', data, at)[0]


def s(data, at):
    return struct.unpack_from('<h', data, at)[0]


def consumers(r):
    exact(r, 0x743811, ['mov ax, si', 'sub ax, 0x96', 'push word ptr es:[di + 0x1c]',
        'push word ptr es:[di + 0x1a]', 'push word ptr es:[di + 0x18]', 'push 0xc00',
        'push ax', 'lcall 0x80ea, 0', 'add sp, 0xa'])
    exact(r, 0x780EC8, ['mov di, word ptr [si + 0x64]', 'mov es, word ptr [si + 0x66]',
        'mov ax, word ptr [si + 0x68]', 'out 0xc2, al', 'mov di, word ptr es:[di]',
        'add di, word ptr [bp + 6]', 'add di, word ptr [bp + 6]',
        'mov di, word ptr es:[di]', 'and word ptr [si + 0xa], 0xfffb'])
    exact(r, 0x781480, ['test byte ptr es:[di + 0xa], 0x20', 'jne 0x78148a', 'jmp 0x781512'])
    exact(r, 0x7814FB, ['mov bx, word ptr [si + 0x12]', 'mov ax, word ptr [bx + 0x26]',
        'add ax, dx', 'mov word ptr [si + 0x26], ax', 'mov ax, word ptr [bx + 0x28]',
        'add ax, cx', 'mov word ptr [si + 0x28], ax'])
    exact(r, 0x781648, ['test word ptr [si + 6], 1', 'je 0x78167b',
        'cmp word ptr [si + 0x34], 0', 'jle 0x78167b', 'cmp byte ptr es:[di + 2], 2',
        'je 0x78167b', 'mov ax, word ptr [si + 4]', 'and ax, 0xf', 'cmp ax, 2',
        'ja 0x78167b', 'mov dx, di', 'mov di, si', 'add di, 0x96',
        'lcall 0x668e, 0x3c3', 'or ax, ax', 'je 0x781679', 'retf'])
    exact(r, 0x7818EF, ['cmp word ptr [si + 0x34], 0', 'jle 0x781904',
        'test word ptr [si + 0x48], 3', 'je 0x781904',
        'and word ptr [si + 6], 0xfffe', 'jmp 0x78194d'])
    exact(r, 0x78194D, ['test byte ptr es:[di + 0xc], 8', 'je 0x7819b5',
        'cmp word ptr es:[di + 0x18], 0', 'je 0x78197c'])
    exact(r, 0x7819D0, ['cmp word ptr es:[di + 0x16], 0', 'jne 0x781a2a',
        'mov ax, word ptr [si + 4]', 'and ax, 0xf', 'cmp ax, 2', 'ja 0x781a24',
        'test word ptr [si + 6], 1', 'jne 0x7819f6', 'mov di, si', 'add di, 0x96',
        'lcall 0x668e, 0xc3', 'retf'])
    exact(r, 0x766CA3, ['push dx', 'xor ax, ax', 'test word ptr [si + 0x48], 3',
        'jne 0x766cb0', 'jmp 0x766eb3', 'or word ptr [si + 6], 4'])
    exact(r, 0x766E62, ['mov ax, word ptr [si + 0x4a]', 'and ax, 0x3c', 'shr ax, 2',
        'cmp ax, 4', 'je 0x766e93', 'mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0', 'mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0', 'mov word ptr [si], 0x1d5e',
        'mov word ptr [si + 2], 0x668e', 'mov ax, 1', 'jmp 0x766eb3'])
    exact(r, 0x767A1C, ['mov byte ptr [si + 0x5a], 0', 'mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0', 'mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0', 'mov word ptr [si], 0x115d',
        'mov word ptr [si + 2], 0x668e'])
    exact(r, 0x785773, ['test word ptr [si + 0x48], 3', 'je 0x785780',
        'lcall 0x668e, 0xc3', 'retf', 'mov word ptr [si + 0x34], 0x80'])
    exact(r, 0x78572B, ['mov word ptr [si + 0x34], 0xffa0',
        'cmp word ptr [si + 0x28], 0x200', 'jg 0x785747',
        'mov word ptr [si + 0x28], 0x200'])
    # The two 3EFF masks mutate attack-side type11, not a fighter or lower6.
    exact(r, 0x76006F, ['mov bx, word ptr [si + 4]', 'and bx, 0xf', 'add bx, bx',
        'jmp word ptr cs:[bx + 0xad]'])
    table = struct.unpack_from('<13H', r, 0x76007D)
    need([i for i, off in enumerate(table) if off == 0xE57] == [11], 'terrain-clear handler owned by type11')
    exact(r, 0x760E79, ['mov word ptr [si], 0x966a', 'mov word ptr [si + 2], 0x4090',
        'and word ptr [si + 4], 0x3eff'])
    exact(r, 0x74120D, ['mov bx, word ptr es:[0x3d0]', 'add bx, bx',
        'jmp word ptr cs:[bx + 0x919]'])
    need(struct.unpack_from('<3H', r, 0x741219) == (0x91F, 0x968, 0x99D), 'kind2 skips opponent AI input branch')
    # This is a narrowing fact, not a proof that no other writer reaches P2.
    return dict(ordinary_landing='668E:03C3 -> 766E62 -> zero velocity/acceleration -> 1D5E',
        neutral_idle='668E:113C clears32/34/36/38 then115D polls key helpers',
        action_landing='80EA:0482 uses ordinary landing except endtype2 -> same collision transition',
        generic_attach_writer='781503/78150B requires action+a bit20',
        collision_terrain_clear_type=11,
        input='kind2 skips enemy AI assignment but P1 retains full held/edge input')


def action_rows(r):
    resources, total, landing_count = [], 0, 0
    for form in (0, 0x3C0):
        for identity in range(15):
            triple = 0x740000 + form + identity * 32 + 24
            off, seg, bank = struct.unpack_from('<3H', r, triple)
            base = (bank & 127) * 65536 + ((seg * 16 + off) & 65535)
            need(off == 0 and 0x2000 <= seg < 0x3000 and h(r, base) == 4, 'banked actor action table')
            count = h(r, base + 2)
            need(0 < count < 64, 'finite indexed action count')
            ptrs = struct.unpack_from('<' + 'H' * count, r, base + 4)
            need(ptrs == tuple(4 + count * 2 + i * 36 for i in range(count)), 'all action rows exactly contiguous36 bytes')
            rows = {p: r[base + p:base + p + 36] for p in ptrs}
            landing = []
            for index, p in enumerate(ptrs):
                row = rows[p]
                need(row[1] < 8 and row[2] < 5, 'motion/end selector domains')
                need(not row[10] & 0x20, 'no player action uses parent X/Y rewrite')
                need(all(h(row, k) == 0 or h(row, k) in rows for k in range(22, 36, 2)), 'all seven action links stay indexed')
                if row[2] != 2:
                    continue
                landing_count += 1
                targets = {h(row, 22)}
                if row[12] & 8:
                    targets.update((h(row, 24), h(row, 26)))
                outcomes = []
                for target in sorted(targets):
                    if target == 0:
                        outcomes.append(dict(next='native idle', vy=0, ay=0))
                        continue
                    nxt = rows[target]
                    # Successor's entry redirects could precede its motion assignment.
                    need(not nxt[10] & 0x81 and not nxt[11] & 2 and not nxt[13] & 0x80,
                         'landing successor has no pre-motion conditional redirect')
                    need(not nxt[12] & 0xA0 and not nxt[13] & 0x30 and not nxt[11] & 0x40,
                         'landing successor does not inherit/add vertical motion or home vertically')
                    motion = nxt[1]
                    need(motion in (0, 3, 4), 'landing successor exact decoded motion family')
                    vy, ay = (0, 0) if motion in (0, 3) else (s(nxt, 16), s(nxt, 20))
                    need(vy + ay <= 0 and (vy != 0 or ay == 0), 'first post-landing integration is zero or upward')
                    outcomes.append(dict(next=ptrs.index(target), motion=motion, vy=vy, ay=ay))
                landing.append(dict(index=index, pointer=f'{base+p:06X}', outcomes=outcomes))
            total += count
            resources.append(dict(identity=identity, form='evolved' if form else 'base',
                pointer=f'{base:06X}', count=count, sha256=sha(r[base:base + 4 + count * 38]),
                landing_type2=landing))
    need(total == 607, 'complete30 character resource population')
    return dict(resources=resources, resources_count=30, indexed_rows=total,
                landing_type2_rows=landing_count, parent_position_rewrite_rows=0)


def grid(r, candidate):
    data = r[0x33CA20:0x33CA20 + 56 * 54 * 4]
    need(candidate[0x607000:0x607000 + len(data)] == data, 'actual v67 complete Shoot collision grid')
    cells = list(struct.iter_unpack('<HH', data))
    need(set(a for a, b in cells) == {0, 1, 2, 3} and all(b == 0 for a, b in cells),
         'entire grid has no conveyor/force/material metadata')
    center = {y: sorted(set(cells[y * 56 + x][0] for x in range(24, 33)))
              for y in range(54) if any(cells[y * 56 + x][0] for x in range(24, 33))}
    need(center == {42: [2], 50: [1], 51: [3], 52: [3], 53: [3]}, 'actual central landing rows')
    radii = []
    for identity in range(15):
        row = h(r, 0x3B8460 + identity * 2)
        radius, height = struct.unpack_from('<HH', r, 0x3B8460 + row + 0x24)
        need((radius, height) == (6, 30), 'all15 source base fighter collision dimensions')
        radii.append([radius, height])
    return dict(cells=len(cells), sha256=sha(data), flags=[0, 1, 2, 3], auxiliary_all_zero=True,
                center_columns=[24, 32], center_solid_rows=center, base_dimensions=radii,
                consequence='no terrain material can add conveyor displacement; center landing is336px or400px, not necessarily below192px')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('candidate', type=Path)
    p.add_argument('--output', required=True, type=Path); a = p.parse_args()
    need(all(x.suffix.lower() not in ('.sav', '.state') for x in (a.source, a.candidate)), 'save/state input forbidden')
    r, g = a.source.read_bytes(), a.candidate.read_bytes()
    need(sha(r) == SOURCE_SHA and sha(g) == V67, 'immutable source and exact v67')
    result = dict(source_sha256=sha(r), candidate_sha256=sha(g), consumers=consumers(r),
                  actions=action_rows(r), grid=grid(r, g), complete_player_domain_proved=False,
                  remaining=['P1 grabbed-victim exclusion through actual boss input/damage ownership.',
                             'Whole trajectory drop-through/sidewall invariant and all external fighter displacement writers.',
                             'Lower movement exclusive ownership; terminal camera/IRQ are separate.'], ROM_modified=False)
    negatives = []
    for label, at, mutation, check in (
        ('parent attach row', 0x1DFCA0 + 0x30 + 10, 0x20, lambda data: action_rows(data)),
        ('landing branch', 0x781655, 1, lambda data: consumers(data)),
        ('type11 owner', 0x76007D + 11 * 2, 1, lambda data: consumers(data)),
        ('material metadata', 0x33CA20, 4, lambda data: grid(data, g))):
        bad = bytearray(r); bad[at] ^= mutation
        try:
            check(bytes(bad))
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError('negative accepted: ' + label)
    result['negative_controls_rejected'] = negatives
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f'PASS607 action rows, {result["actions"]["landing_type2_rows"]} landing transitions, full no-force grid; whole-route ownership remains explicit')


if __name__ == '__main__':
    main()
