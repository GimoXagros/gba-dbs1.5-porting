#!/usr/bin/env python3
"""Positive constructor/dispatch and finite reused-boss callback control audit."""
import argparse
from collections import deque
import json
from pathlib import Path
import struct

from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha
from analyze_shoot_upper_state_graph import (Cs, CS_ARCH_X86, CS_MODE_16,
    CS_OP_IMM, CS_OP_MEM, callback_assignment, decode_one, direct_target, contiguous_ranges)


def contracts(r):
    exact(r, 0x740CC7, ['mov bx, word ptr [0x3d0]', 'add bx, bx',
        'jmp word ptr cs:[bx + 0x3d2]'])
    need(struct.unpack_from('<3H',r,0x740CD2)[2] == 0x46E,'mode2 creates boss pair')
    exact(r, 0x740D6E, ['mov byte ptr [0x3cc], 0', 'xor ax, ax',
        'mov al, byte ptr [0x58]', 'push 0', 'push 3', 'push 0', 'push 0xf',
        'push ax', 'lcall 0x4090, 0x29e4', 'add sp, 0xa'])
    exact(r, 0x74333F, ['mov ax, word ptr [bp + 0xc]', 'or ax, 0xe700',
        'push 4', 'push 0', 'push ax', 'push 0x668e', 'push 0x113c',
        'push 0x1000', 'push 0x65e', 'lcall 0x4090, 0x172a'])
    exact(r, 0x7420CC, ['mov word ptr [di + 0x20], 0',
        'mov word ptr [di + 0x1e], 0'])
    exact(r, 0x743621, ['mov word ptr [si + 0x1e], 0',
        'mov word ptr [si + 0x20], 0'])
    exact(r, 0x745640, ['and word ptr [si + 4], 0x73ff',
        'mov byte ptr [si + 0x11], 0xf'])
    exact(r, 0x747AD1, ['mov si, word ptr es:[0x65e]',
        'mov word ptr [bp - 6], si', 'mov di, word ptr es:[0x65c]',
        'mov word ptr [bp - 8], di', 'or word ptr [si + 4], 0x20'])
    exact(r, 0x747B36, ['and word ptr [si + 4], 0x43ff'])
    exact(r, 0x7421D9, ['mov ax, word ptr [si + 4]', 'and ax, 0xf',
        'cmp ax, 2', 'jg 0x7421e9', 'lcall 0x4090, 0x2ae0'])
    exact(r, 0x74120D, ['mov bx, word ptr es:[0x3d0]', 'add bx, bx',
        'jmp word ptr cs:[bx + 0x919]'])
    need(struct.unpack_from('<3H',r,0x741219)[2] == 0x99D,'mode2 skips opponent AI input')
    exact(r, 0x741824, ['mov bx, word ptr es:[0x3d0]', 'add bx, bx',
        'jmp word ptr cs:[bx + 0xf30]'])
    need(struct.unpack_from('<3H',r,0x741830)[2] == 0xFC6,'mode2 skips link input')
    exact(r, 0x7418C6, ['retf'])
    exact(r, 0x74309A, ['test word ptr [di + 0x20], 0x80', 'je 0x7430f2',
        'test word ptr [di + 0x1e], 5', 'jne 0x7430f2',
        'test word ptr [di + 0x1e], 0xa', 'je 0x7430f2'])
    # Priority swaps use task header +4 after subtracting actor bias10.
    exact(r, 0x76702F, ['push si', 'push di', 'sub si, 0x10', 'sub di, 0x10',
        'mov ax, word ptr [si + 4]', 'cmp ax, word ptr [di + 4]',
        'jg 0x767042', 'pop di', 'pop si', 'retf',
        'mov word ptr [si + 4], 0x3000', 'mov word ptr [di + 4], 0x3800'])
    exact(r, 0x760EF7, ['mov word ptr [si + 0x7c], 0'])
    exact(r, 0x760F70, ['mov ax, word ptr [si + 0x7c]',
        'or word ptr [si + 0x20], ax', 'lcall [si]', 'retf'])
    exact(r, 0x760F79, ['test word ptr [si + 0xc], 2', 'jne 0x760f89',
        'mov ax, word ptr [si + 0x20]', 'and ax, 0xfff5',
        'or word ptr [si + 0x7c], ax'])
    exact(r, 0x746923, ['mov bx, word ptr [si + 0x1c]',
        'and word ptr [bx + 4], 0xafff', 'mov word ptr [bx], 0x64c0',
        'mov word ptr [bx + 2], 0x4090'])
    exact(r, 0x762EEE, ['mov bx, 0x3868', 'mov bx, word ptr cs:[bx]',
        'push cs', 'lcall 0x668e, 0', 'add sp, 2', 'retf'])
    need(struct.unpack_from('<H',r,0x763838)[0]==0x38A4,'grab throw descriptor pointer')
    need(struct.unpack_from('<4H',r,0x763874)==(0,0x38,0x11FE,0x5FFD),
         'borrowed throw continues in typed damage11FE, not arbitrary callback')
    exact(r, 0x766921, ['mov ax, word ptr es:[bx + 4]', 'mov word ptr [si], ax',
        'mov ax, word ptr es:[bx + 6]', 'mov word ptr [si + 2], ax'])
    exact(r, 0x760047, ['mov bx, word ptr [di + 4]', 'and bx, 0xf',
        'add bx, bx', 'jmp word ptr cs:[bx + 0x85]'])
    need(struct.unpack_from('<13H',r,0x760055)[3]==0xD1,'kind3 victim dispatch')
    exact(r, 0x786BFA, ['push 0x1000', 'push 0x86bf', 'push 0x119',
        'lcall 0x4fff, 0x980', 'add sp, 6', 'mov ds, dx',
        'add ax, 0x10', 'mov bx, ax'])
    exact(r, 0x786D38, ['mov ax, word ptr [8]', 'add ax, 0x10',
        'pop ds', 'mov bx, ax'])


def callback_graph(r):
    bank=r[0x740900:0x750900]
    c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    seeds=(0x649A,0x64C0,0x64C6,0x7792,0x88F6,0x7AB1,0x7D8D)
    todo=deque(seeds);seen=set();coverage=set();callbacks=set();imports=set()
    while todo:
        at=todo.popleft()
        while at not in seen:
            i=decode_one(c,bank,at);need(i is not None,'valid callback instruction')
            seen.add(at);coverage.update(range(at,at+i.size))
            dst=i.op_str.split(',')[0]
            need(not (i.mnemonic not in ('cmp','test','push') and dst in
                 ('word ptr [si + 0x1e]','word ptr [di + 0x1e]',
                  'word ptr [si + 0x20]','word ptr [di + 0x20]')),
                 'direct boss callbacks preserve held and edge words')
            cb=callback_assignment(c,bank,i)
            if cb is not None: callbacks.add(cb);todo.append(cb)
            nxt=at+i.size
            if i.mnemonic in ('ret','retf','iret'): break
            if i.mnemonic=='lcall':
                need(len(i.operands)==2 and all(o.type==CS_OP_IMM for o in i.operands),
                     'no unresolved far transfer in boss graph')
                seg,target=(o.imm&65535 for o in i.operands)
                if seg==0x4090:
                    if target!=0x9908: todo.append(target)
                else: imports.add((seg,target))
            elif i.mnemonic in ('call','jmp') or i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                target=direct_target(i);need(target is not None,'no unresolved near transfer')
                if target!=0x9908: todo.append(target)
                if i.mnemonic=='jmp': break
            at=nxt
    need(all(seg==0x4FFF for seg,target in imports),'all graph imports are common presentation/RNG')
    return dict(seeds=[hex(n) for n in seeds], instructions=len(seen),
        callbacks=[hex(n) for n in sorted(callbacks)],
        imports=[f'{seg:04X}:{target:04X}' for seg,target in sorted(imports)],
        ranges=[dict(start=hex(0x740900+a),end=hex(0x740900+b),
                     sha256=sha(bank[a:b])) for a,b in contiguous_ranges(coverage)],
        controller_cut='4090:9908 is existing lower-controller owner; not recursively revisited')


def borrowed_graph(r):
    """Follow actual grab-victim/throw states with invariant zero keys and idF."""
    c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    todo=deque([(0x5FFD,0x2D78),(0x5FFD,0x11FE)])
    seen=set();imports=set();callbacks=set();indirect=[];pruned=[]
    while todo:
        seg,at=todo.popleft();base=0x700000+seg*16;bank=r[base:base+65536]
        known_zf=None
        while (seg,at) not in seen:
            i=decode_one(c,bank,at);need(i is not None,'valid borrowed callback instruction')
            seen.add((seg,at));nxt=at+i.size
            dst=i.op_str.split(',')[0]
            if i.mnemonic not in ('cmp','test','push') and dst in (
                    'word ptr [si + 0x1e]','word ptr [si + 0x20]'):
                need((seg,at)==(0x5FFD,0xFA3), 'only input effect is proven hitfreeze edge ORzero')
            if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==CS_OP_MEM and i.operands[0].mem.disp==0 and i.operands[1].type==CS_OP_IMM:
                j=decode_one(c,bank,nxt)
                if j and j.mnemonic=='mov' and len(j.operands)==2 and j.operands[0].type==CS_OP_MEM and j.operands[0].mem.disp==2 and j.operands[1].type==CS_OP_IMM:
                    target=(j.operands[1].imm&65535,i.operands[1].imm&65535)
                    if target[0] in (0x5FFD,0x668E):todo.append(target);callbacks.add(target)
                    else:imports.add(target)
            if i.mnemonic in ('ret','retf','iret'):break
            if i.mnemonic in ('je','jne') and known_zf is not None:
                taken=known_zf==(i.mnemonic=='je')
                pruned.append((seg,at,taken));known_zf=None
                at=direct_target(i) if taken else nxt;continue
            known_zf=None
            if i.mnemonic=='test' and dst in ('word ptr [si + 0x1e]','word ptr [si + 0x20]'):
                known_zf=True
            elif i.mnemonic=='cmp' and dst=='byte ptr [si + 0x11]' and i.operands[1].type==CS_OP_IMM:
                known_zf=i.operands[1].imm==15
            elif i.mnemonic=='lcall':
                if len(i.operands)==2 and all(o.type==CS_OP_IMM for o in i.operands):
                    target=tuple(o.imm&65535 for o in i.operands)
                    if target[0] in (0x5FFD,0x668E) and target!=(0x668E,0):todo.append(target)
                    else:imports.add(target)
                else:
                    need((seg,at)==(0x5FFD,0xFA6),'only far-indirect is restored previous callback')
                    indirect.append('5FFD:0FA6 resumes callback already stored in freeze wrapper')
            elif i.mnemonic=='call' or i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                target=direct_target(i)
                if target is None:
                    need((seg,at)==(0x668E,0x41E),'only near-indirect is bounded landing selector')
                    targets=struct.unpack_from('<4H',r,0x766D03)
                    for target in targets:todo.append((seg,target))
                    indirect.append('668E:041E landingCX0..3 -> '+','.join(hex(n) for n in targets))
                else:todo.append((seg,target))
                if i.mnemonic=='jmp':break
            at=nxt
    return dict(instructions=len(seen), callbacks=[f'{s:04X}:{o:04X}' for s,o in sorted(callbacks)],
        imports=[f'{s:04X}:{o:04X}' for s,o in sorted(imports)],
        resolved_indirect=indirect, pruned_zero_keys_or_idF=len(pruned),
        assumptions='held=edge0 from constructor/dispatch; actor identityF; freeze savededge0')


def kind3_damage(r):
    bank=r[0x75FFD0:0x76FFD0]
    c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    todo=deque([0xD1]);seen=set();imports=set();writes=[]
    while todo:
        at=todo.popleft()
        while at not in seen and at not in (0x9F,0xC7):
            i=decode_one(c,bank,at);need(i is not None,'valid kind3 damage instruction')
            seen.add(at);dst=i.op_str.split(',')[0]
            need(not(i.mnemonic not in ('cmp','test','push') and dst in
                ('word ptr [di + 0x1e]','word ptr [di + 0x20]')),
                'kind3 victim damage preserves both control fields')
            if i.mnemonic in ('ret','retf'):break
            if i.mnemonic=='lcall':
                need(len(i.operands)==2 and all(o.type==CS_OP_IMM for o in i.operands),'direct kind3 import')
                imports.add(tuple(o.imm&65535 for o in i.operands))
            elif i.mnemonic=='call' or i.mnemonic.startswith('j'):
                target=direct_target(i);need(target is not None,'direct kind3 branch')
                todo.append(target)
                if i.mnemonic=='jmp':break
            at+=i.size
    return dict(instructions=len(seen), imports=[f'{s:04X}:{o:04X}' for s,o in sorted(imports)],
        exit_owner='5FFD:009F switches to attacker SI dispatch; 00C7 is common return',
        visual_child='86BF:0000 allocates new BX child; callback0119 reloads currenttask+10 intoBX; parent only read',
        palette_owner='4FFF:2389 receives palette arguments, no actor control pointer')


def imported_effects(r):
    c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    writes=[]
    for i in c.disasm(r[0x743930:0x743ADB],0x743930):
        for o in i.operands:
            if o.type==CS_OP_MEM and o.access&2 and i.reg_name(o.mem.base)=='si':
                writes.append((i.address,o.mem.disp))
    need(writes==[(0x743987,0x50),(0x74398A,0xC),(0x743997,0xC)],
         '3030 parent effect exactly HP and damage-side flags')
    exact(r,0x7439EE,['push 0','push 0','push 0x8217','push 0x4090',
        'push 0x323d','push 0x1000','push 0x66a','lcall 0x4090, 0x172a',
        'add sp, 0xe','mov bx, word ptr es:[0x66a]'])
    visual_writes=[]
    for a,z in ((0x786BF0,0x786D09),(0x786D09,0x786EE8)):
        ins=list(c.disasm(r[a:z],a))
        need(ins and ins[-1].address+ins[-1].size==z,'complete visual function decoding')
        for i in ins:
            for o in i.operands:
                if o.type==CS_OP_MEM and o.access&2:
                    need(i.reg_name(o.mem.base) in ('bx','bp'),
                         'visual writes only allocated/current child BX or local BP')
                    visual_writes.append(i.address)
    palette=list(c.disasm(r[0x747888:0x7478DE],0x747888))
    need(all(not(o.type==CS_OP_MEM and o.access&2) for i in palette for o in i.operands),
         '6F88 has no memory stores, only palette calls')
    return dict(orb_parent_writes=[f'{p:06X}:actor+{o:X}' for p,o in writes],
        orb_child_owner='743A09 reloads newly allocated066A intoBX; ES1000 list versus DS0C00 parent',
        visual_memory_writes=len(visual_writes), visual_owner='all writes BX new/current task or BP stack',
        common_presentation='4FFF:24CB/2862/2A16 operate renderer actor+96; palette2389 has no control pointer',
        descriptor='668E:0000 actual38A4 descriptor assigns5FFD:11FE and fields7E..94',
        reviewed_independently='root: 86BF constructor+0119 and4090:3030 exact parent/child effects')


def analyze(r):
    need(sha(r)==SOURCE_SHA,'immutable source');contracts(r)
    graph=callback_graph(r);borrowed=borrowed_graph(r);damage=kind3_damage(r);effects=imported_effects(r)
    negative=[]
    for at in (0x740D7B,0x7421E0,0x74121D,0x741834,0x7430A8,0x760EF7):
        bad=bytearray(r);bad[at]^=1
        try: contracts(bad)
        except ValueError: negative.append(hex(at))
        else: raise ValueError('ineffective mutation')
    for at,value,check in ((0x746DAD,0x1E,callback_graph),
                           (0x743989,0x1E,imported_effects),
                           (0x786D69,0x04,imported_effects)):
        bad=bytearray(r);bad[at]=value
        try: check(bad)
        except ValueError: negative.append(hex(at))
        else: raise ValueError('ineffective graph/ownership mutation '+hex(at))
    return dict(source_sha256=SOURCE_SHA, actor_kind=3, game_input_mode=2,
        constructor_held_edge=[0,0], callback_graph=graph, borrowed_callback_graph=borrowed,
        kind3_damage_graph=damage,
        imported_effects=effects,
        freeze_zero_induction='saved7C starts0, accumulates zeroedge; restore ORzero leavesedge0; held untouched',
        grab_victim_gate='P1 victim requires P2 held&A !=0, independently of edge80',
        priority_swap='767047 writes taskheaderpriority3800, notactor terrainflags',
        negative_controls_rejected=negative,
        complete_held_invariant=True,
        conclusion='reused kind3 opponent controls remainzero across audited mode2 boss/Shoot/borrowed callback ownership; P1 cannot enter grab-victim path through743176',
        ROM_modified=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh output required')
    result=analyze(a.source.read_bytes());a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',result['callback_graph']['instructions'],'reachable boss callback instructions')


if __name__=='__main__': main()
