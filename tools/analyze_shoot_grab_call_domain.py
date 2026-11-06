#!/usr/bin/env python3
"""Actual mode2 input-to-grab call and upper presentation boundary, not reachability."""
import argparse
import json
from pathlib import Path
import struct
from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha


def proof(r):
    exact(r,0x741197,['mov si, word ptr es:[0x65c]',
        'mov di, word ptr es:[0x65e]','mov ax, word ptr [si + 0x26]',
        'mov bx, word ptr [si + 0x28]','sub ax, word ptr [di + 0x26]',
        'sub bx, word ptr [di + 0x28]','mov word ptr [di + 0x3e], ax',
        'mov word ptr [di + 0x40], bx','neg ax','neg bx',
        'mov word ptr [si + 0x3e], ax','mov word ptr [si + 0x40], bx'])
    exact(r,0x74120D,['mov bx, word ptr es:[0x3d0]','add bx, bx',
        'jmp word ptr cs:[bx + 0x919]'])
    need(struct.unpack_from('<H',r,0x74121D)[0]==0x99D,'mode2 normal-input target')
    exact(r,0x74129D,['mov ax, 0x1000','mov es, ax',
        'test byte ptr es:[0x3cd], 7','jne 0x7412f6',
        'mov si, word ptr es:[0x65c]','mov di, word ptr es:[0x65e]',
        'test word ptr [si + 0x20], 0x20','je 0x7412d5'])
    exact(r,0x7412D5,['test word ptr [di + 0x20], 0x20','je 0x741305'])
    exact(r,0x7412FA,['test byte ptr es:[0x3cd], 7','je 0x741305',
        'jmp 0x741315','push word ptr es:[0x65e]',
        'push word ptr es:[0x65c]','call 0x743001','add sp, 4','retf'])
    exact(r,0x743015,['mov si, word ptr [bp + 4]','mov di, word ptr [bp + 6]',
        'mov ax, word ptr [si + 0x28]','cmp ax, word ptr [di + 0x28]',
        'je 0x743026','jmp 0x743214','mov ax, word ptr [si + 6]',
        'or ax, word ptr [di + 6]','test ax, 1','je 0x743034','jmp 0x743214'])
    exact(r,0x743057,['test word ptr [di + 8], 0x4002','jne 0x743093',
        'cmp byte ptr [di + 0x5f], 0','jne 0x743093'])
    exact(r,0x743118,['add si, 0x96','add di, 0x96',
        'push 0x52','push 0xc00','push si','lcall 0x4fff, 0x24cb',
        'add sp, 6','push 0x48','push 0xc00','push di',
        'lcall 0x4fff, 0x24cb'])
    exact(r,0x7524D4,['mov si, word ptr es:[di + 0x30]',
        'mov ds, word ptr es:[di + 0x32]',
        'mov ax, word ptr es:[di + 0x34]','out 0xc2, al',
        'mov dx, word ptr [bp + 0xa]','mov word ptr es:[di + 0xe], dx',
        'mov bx, word ptr [si]','mov ax, dx','shl ax, 3','add bx, ax',
        'mov cx, word ptr [bx + 4]','mov word ptr es:[di + 0x20], cx',
        'mov cx, word ptr [bx + 6]','mov word ptr es:[di + 0x22], cx',
        'mov cx, word ptr [bx]','mov bx, word ptr [bx + 2]'])
    # Header first word is the local event-table offset; 24CB adds event*8.
    need(r[0x3CF410:0x3CF414]==bytes.fromhex('04000000'),'upper event-table header')
    need(r[0x3CF414+0x48*8:0x3CF41C+0x48*8]==bytes.fromhex('0000a80103ff0400'),
        'literal bytes consumed for generic grab event48')
    return dict(status='OPEN_REACHABILITY',
        actual_mode2_input_calls_grab=True,caller_kind3_exclusion=False,
        source_call='07FA -> mode2 table099D -> unpaused741305 ->743001',
        victim_event=0x48,upper_declared_events=6,
        unchecked_event48_words=[0,424,65283,4],
        proven_scope='Call-domain and literal unchecked event indexing only. No original bug or ordinary-input grab witness is claimed.',
        remaining=['Establish a reachable equal-Y, nonairborne P1/P2 state within grab distance.',
            'Establish victim8:4002 clear and5F zero at that same state, including predecessor and external effects.',
            'If reachable, account for the actual borrowed presentation and callbacks before using ordinary upper hitbox bounds.'],
        external_scene_entry_authorized=False,ROM_modified=False,runtime_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh output required')
    r=a.source.read_bytes();need(sha(r)==SOURCE_SHA,'immutable source')
    out=proof(r);negative=[]
    for label,at in [('mode2 target',0x74121D),('grab call',0x741310),
        ('victim condition',0x74305A),('victim event',0x74312F),
        ('unchecked index shift',0x7524EF),('event48 bytes',0x3CF654)]:
        bad=bytearray(r);bad[at]^=1
        try:proof(bad)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective mutation '+label)
    out.update(source_sha256=sha(r),negative_controls_rejected=negative)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print('PASS actual call and resource boundary; grab reachability remains open; six mutations rejected')


if __name__=='__main__':main()
