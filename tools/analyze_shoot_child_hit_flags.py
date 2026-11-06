#!/usr/bin/env python3
"""Narrow source proof: hitting a 93E7 child cannot supply attack hit/block flags.

Does not exclude the child's outgoing attack or other actors' damage effects.
No source/ROM/save mutation; negative controls use host byte copies only.
"""
import argparse
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from analyze_shoot_opponent_controls import contracts as control_contracts, imported_effects


def writes(r, start, end, operand):
    ins = list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(r[start:end],start))
    need(sum(i.size for i in ins)==end-start,'complete bounded instruction slice')
    return [(i.address,i.mnemonic,i.op_str) for i in ins
            if i.op_str.split(',')[0]==operand
            and i.mnemonic not in ('test','cmp','push')]


def proof(r):
    dependency=Path(__file__).with_name('analyze_shoot_opponent_controls.py')
    need(sha(dependency.read_bytes())=='30052414FDC255B5E553ED23243956A30933C8D4A4D72574A16622DB8B330F64',
         'frozen visual/orb imported ownership checker')
    control_contracts(r)
    effects=imported_effects(r)
    exact(r,0x749C52,['push 0','push 1','push 0x4104','push 0','push 0',
        'push 0x1000','push 0x724','lcall 0x4090, 0x172a'])
    exact(r,0x7420B6,['mov ax, word ptr [bp + 0xe]',
        'mov cx, word ptr [bp + 0x10]','mov word ptr [di + 4], ax',
        'mov word ptr [di + 6], cx'])
    exact(r,0x749C8E,['mov byte ptr [di + 0x10], 1'])
    exact(r,0x749CDA,['mov ax, word ptr [si + 0x94]',
        'mov word ptr [di + 0x28], ax','mov si, di','add di, 0x96'])
    exact(r,0x749D18,['mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0','mov word ptr [si + 0x36], 0',
        'mov word ptr [si + 0x38], 0'])
    exact(r,0x749D65,['mov word ptr [si], 0x9798',
        'mov word ptr [si + 2], 0x4090'])
    exact(r,0x74A098,['test word ptr [di + 0xa], 0x2000','jne 0x74a0ae',
        'push 1','push 0xc00','push di','lcall 0x4fff, 0x2862',
        'add sp, 6','retf','push 0xc00','push si','lcall 0x4090, 0x181e',
        'add sp, 4','retf'])
    exact(r,0x760033,['mov si, word ptr [si]','mov di, word ptr [di]',
        'or word ptr [si + 0xa], 1','or word ptr [di + 0xa], 2',
        'or word ptr [si + 0xa2], 0x1000','mov bx, word ptr [di + 4]',
        'and bx, 0xf','add bx, bx','jmp word ptr cs:[bx + 0x85]'])
    need(struct.unpack_from('<H',r,0x760055+4*2)[0]==0x2DD,
         'kind4 victim dispatch reaches7602AD')
    exact(r,0x7602AD,['cmp word ptr [bp - 8], 0x13','je 0x7602cd',
        'cmp word ptr [bp - 8], 0x10','je 0x7602cd',
        'cmp word ptr [bp - 8], 0x11','je 0x7602cd',
        'mov ax, word ptr [si + 4]','and ax, 0xf','cmp ax, 6',
        'je 0x7602cd','jmp 0x7602d0','jmp 0x760097'])
    exact(r,0x760301,['mov word ptr [di], 0',
        'mov word ptr [di + 2], 0x6ff9'])
    exact(r,0x760344,['jmp 0x76006f','jmp 0x76006f'])
    need(writes(r,0x7602AD,0x76034A,'word ptr [si + 0xa]')==[],
         'kind4 victim handler has no attacker hit/block flag write')
    exact(r,0x76006F,['mov bx, word ptr [si + 4]','and bx, 0xf',
        'add bx, bx','jmp word ptr cs:[bx + 0xad]'])
    need(struct.unpack_from('<3H',r,0x76007D)==(0xD2D,)*3,
         'fighter attacker kinds0..2 share760CFD')
    exact(r,0x760D07,['mov ax, word ptr [di + 4]','and ax, 0xf',
        'cmp ax, 2','jg 0x760d2b'])
    need(writes(r,0x760CFD,0x760D86,'word ptr [si + 0xa]')==
         [(0x760D3F,'or','word ptr [si + 0xa], 0x1000')],
         'fighter continuation never adds hit4 or block10')
    need(writes(r,0x760E98,0x760F2C,'word ptr [si + 0xa]')==[],
         'freeze constructor does not supply hit/block flags')
    # The freeze continuation restores the saved callback; that callback owns
    # its further actions. No claim is made about unrelated future collisions.
    need(writes(r,0x760F2C,0x760F79,'word ptr [si + 0xa]')==[],
         'freeze restore has no direct actor hit/block writes')
    exact(r,0x780F1A,['cmp word ptr es:[di + 0x18], 0','je 0x780f26',
        'and word ptr [si + 0xa], 0xfffb','cmp word ptr es:[di + 0x1a], 0',
        'je 0x780f32','and word ptr [si + 0xa], 0xffef'])
    victim=struct.unpack_from('<5h',r,0x3D2470)
    need(victim==(0,4048,4128,0,0),'93E7 exact dummy victim descriptor')
    return dict(status='PASS',child_kind=4,side=1,
        child_Y='source upper+94 captured at749CDA; zero motion;9798 only animates/releases',
        dummy_victim=dict(type=victim[0],offset_X=victim[1],offset_Y=victim[2],
                          half_width=victim[3],half_height=victim[4]),
        common_collision_attacker_flags_added=1,
        kind4_victim_attacker_hit_block_writes=[],
        fighter_attacker_possible_extra_flags=0x1000,
        imported_owner_effects=effects,
        row22_cycle_trigger_bits=0x14,
        conclusion='A fighter hitting a93E7 kind4 child does not add actor+A hit4/block10 and cannot by that collision alone trigger row22→18.',
        limitations=['Outgoing93E7 attacks may still damageP1; their reset effects remain separate.',
            'Other targets, pre-existing flags and later unrelated collisions are not excluded.',
            'Zero-area victim descriptor is not assumed unhittable: source overlap uses positive sum-of-extents minus distance.'],
        ROM_modified=False,runtime_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh evidence required')
    r=a.source.read_bytes();need(sha(r)==SOURCE_SHA,'immutable source identity')
    out=proof(r);negative=[]
    for label,at in [('child kind',0x749C57),('victim dispatch',0x76005D),
                     ('common hit bit',0x76003B),('fighter flag',0x760D43),
                     ('dummy descriptor',0x3D2474),('fresh hit clear',0x780F25)]:
        bad=bytearray(r);bad[at]^=1
        try:proof(bad)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective mutation '+label)
    out.update(source_sha256=sha(r),negative_controls_rejected=negative)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print('PASS93E7 victim cannot supply fighter hit4/block10;6direct mutations rejected')


if __name__=='__main__':main()
