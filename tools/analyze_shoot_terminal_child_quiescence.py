#!/usr/bin/env python3
"""Pin actual terminal dispatch and the conditional no-new-child closure.

The fatal damage writer supplies the required callback pair. The independent
3030 HP writer remains an entry-ownership gate, not an assumed fatal path.
"""
from pathlib import Path
from collections import deque
import argparse
import hashlib
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_16,CS_OP_IMM,CS_OP_MEM
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BASE=0x740900
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)
def rows(r,a,z):
    out=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(r[a:z],a))
    need(sum(i.size for i in out)==z-a,'complete bounded source decode')
    return [(i.mnemonic,i.op_str) for i in out]
def context(r):
    need(rows(r,0x771F53,0x771F66)==[
       ('push','0x4090'),('push','0xb8b'),('push','0xc00'),('push','word ptr es:[0x3e0]'),
       ('lcall','0x4fff, 0xbc7')],'terminal battle callback owner')
    need(rows(r,0x771FA3,0x771FB6)==[
       ('push','0x4090'),('push','0x7d6'),('push','0xc00'),('push','word ptr es:[0x3de]'),
       ('lcall','0x4fff, 0xbc7')],'stage11 terminal input callback owner')
    need(rows(r,0x7601EC,0x760203)==[
       ('mov','ax, di'),('mov','word ptr [di], 0x7ab1'),('mov','word ptr [di + 2], 0x4090'),
       ('mov','di, word ptr [di + 0x1c]'),('mov','word ptr [di], 0x7d8d'),('mov','word ptr [di + 2], 0x4090')],
       'positive stage11 fatal callback pair')
    input_rows=rows(r,0x7410D6,0x7410FA)
    need(input_rows==[('mov','ax, 0xc00'),('mov','ds, ax'),('mov','ax, 0x1000'),('mov','es, ax'),
       ('mov','word ptr [0x3a20], 0'),('call','0x7424c6'),('mov','ax, word ptr es:[0x1de]'),
       ('mov','bx, word ptr es:[0x1e0]'),('mov','word ptr [0x3a14], ax'),
       ('mov','word ptr [0x3a16], bx'),('retf','')],'terminal input is snapshots/reset, not a key clear')
    need(rows(r,0x7414B3,0x7414C1)==[('test','byte ptr es:[0x3cd], 7'),('je','0x7414be'),
       ('jmp','0x74160a'),('call','0x7418c7')],'terminal retains actor movement pass')

def entry_writers(r):
    need(rows(r,0x7417B5,0x7417FE)==[
       ('mov','bx, 0xc00'),('mov','ax, 0x1000'),('mov','ds, bx'),('mov','es, ax'),
       ('cmp','word ptr es:[0x3d0], 2'),('jne','0x7417fe'),
       ('mov','bx, word ptr es:[0x65c]'),('cmp','word ptr [bx + 0x50], 0'),
       ('jne','0x7417e6'),('cmp','word ptr [bx + 0xa4], 0x3e'),('jne','0x7417e6'),
       ('push','4'),('lcall','0x71f0, 0'),('add','sp, 2'),('jmp','0x7418c6'),
       ('mov','bx, word ptr es:[0x65e]'),('cmp','word ptr [bx + 0x50], 0'),
       ('jg','0x7417fe'),('push','5'),('lcall','0x71f0, 0'),('add','sp, 2'),
       ('jmp','0x7418c6')],'actual kind2 second-actor nonpositive-HP root case5 caller')
    need(rows(r,0x771F69,0x771F8A)==[
       ('cmp','word ptr [bp + 6], 5'),('je','0x771f72'),('jmp','0x771ff7'),
       ('push','ax'),('push','ds'),('push','di'),('mov','di, 0x1000'),('mov','ds, di'),
       ('mov','di, 0x4e'),('xor','ax, ax'),('mov','al, byte ptr [di + 0xe]'),
       ('pop','di'),('pop','ds'),('cmp','ax, 0xb'),('pop','ax'),('je','0x771fa3')],
       'actual root case5 stage11 selects the terminal task')
    need(rows(r,0x771FB9,0x771FCA)==[
       ('push','0xff0'),('push','0x71f0'),('push','0x653'),('lcall','0x4fff, 0x980'),
       ('add','sp, 6')],'actual priority0FF0 terminal dispatcher allocation')
    need(rows(r,0x772553,0x77256F)==[
       ('push','ds'),('push','di'),('mov','di, 0x1000'),('mov','ds, di'),
       ('mov','di, 0x4e'),('xor','ax, ax'),('mov','al, byte ptr [di + 0xe]'),
       ('pop','di'),('pop','ds'),('cmp','ax, 0xb'),('jne','0x77256f'),
       ('lcall','0x71f0, 0x1750'),('retf','')],'actual stage11 terminal dispatch to1750')
    need(rows(r,0x760177,0x76019F)==[
       ('xor','ax, ax'),('mov','al, byte ptr [bp - 4]'),('test','word ptr [si + 8], 0x4000'),
       ('je','0x760185'),('shr','ax, 1'),('sub','word ptr [di + 0x50], ax'),
       ('cmp','word ptr [di + 0x50], 0'),('jle','0x760191'),('jmp','0x760229'),
       ('push','es'),('mov','ax, 0x1000'),('mov','es, ax'),
       ('cmp','byte ptr es:[0x5c], 0xb'),('je','0x7601ec')],
       'actual common fatal HP writer routes stage11 to the callback pair')
    need(rows(r,0x743962,0x74399C)==[
       ('xor','ax, ax'),('cmp','word ptr [si + 0x50], 0'),('jg','0x74396d'),
       ('jmp','0x743ad1'),('mov','al, byte ptr [si + 0x58]'),
       ('cmp','word ptr [si + 0x50], ax'),('jge','0x743978'),
       ('mov','ax, word ptr [si + 0x50]'),('or','ax, ax'),('jne','0x74397f'),
       ('jmp','0x743ad1'),('cmp','word ptr es:[0x3d0], 2'),('jne','0x74399c'),
       ('sub','word ptr [si + 0x50], ax'),('and','word ptr [si + 0xc], 0xbfff'),
       ('test','word ptr [si + 0x9e], 0x4000'),('jne','0x74399c'),
       ('or','word ptr [si + 0xc], 0x4000')],'3030 is an independent kind2 HP writer')
    c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    instructions=list(c.disasm(r[0x743930:0x743ADB],0x743930))
    need(sum(i.size for i in instructions)==0x1AB,'complete3030 service decode')
    stores=[(i.address,o.mem.disp) for i in instructions for o in i.operands
            if o.type==CS_OP_MEM and o.access&2 and i.reg_name(o.mem.base)=='si']
    need(stores==[(0x743987,0x50),(0x74398A,0xC),(0x743997,0xC)],
       '3030 parent stores do not install a callback pair')
    constructors=(0x7617AF,0x7618D5,0x761986)
    for at in constructors:
        need(rows(r,at,at+5)==[('lcall','0x4090, 0x3030')],
             'actual source attack constructor invokes3030')
    need(rows(r,0x7617DD,0x7617E7)==[
       ('mov','word ptr [si], 0x1817'),('mov','word ptr [si + 2], 0x5ffd'),('retf','')],
       '3030 caller installs ordinary reaction continuation, not the fatal pair')
    return dict(root_caller='7417F3: root71F0:0000 case5',
       predicate='kind2; first actor does not take case4; second actor signedHP<=0',
       callback_identity_checked_by_entry=False,
       stage11_dispatch=['771F84: stage==11','771FB9: allocate0FF0/71F0:0653',
                         '772569: call71F0:1750'],
       sufficient_fatal_writer='760185 subtractsDI+50; nonpositive result andstage11 reach7601EC pair assignment',
       separate_hp_writer='4090:3030 /743987 subtractsSI+50 in kind2; no parent callback stores',
       separate_writer_calls=[f'{at:06X}' for at in constructors],
       separate_writer_caller_continuation='7617DD assigns5FFD:1817 after3030',
       every_terminal_entry_writer_installs_pair_proven=False,
       open_gate='3030 can reduce positive HP tozero while its caller retains a different callback. Its possible actor/entry ownership needs closure before universal no-new-child can follow.')

def graph(r,seeds):
    bank=r[BASE:BASE+65536];c=Cs(CS_ARCH_X86,CS_MODE_16);c.detail=True
    todo=deque(seeds);seen=set();callbacks=set(seeds);imports=set();near=set()
    forbidden={0x881A,0x933B,0x9908,0x172A}
    while todo:
        at=todo.popleft()
        while at not in seen:
            ins=list(c.disasm(bank[at:at+15],at,count=1));need(bool(ins),'valid source graph instruction')
            i=ins[0];seen.add(at);nxt=at+i.size
            # Direct callback assignments pair offset and segment on the actor.
            if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==CS_OP_MEM:
                dst=i.operands[0].mem
                if dst.disp==0 and i.reg_name(dst.base)=='si':
                    need(i.operands[1].type==CS_OP_IMM,'resolved immediate actor callback')
                    ns=list(c.disasm(bank[nxt:nxt+15],nxt,count=1));need(bool(ns),'callback segment present')
                    j=ns[0]
                    need(j.mnemonic=='mov' and len(j.operands)==2 and j.operands[0].type==CS_OP_MEM and
                         j.reg_name(j.operands[0].mem.base)=='si' and j.operands[0].mem.disp==2 and
                         j.operands[1].type==CS_OP_IMM and j.operands[1].imm==0x4090,'typed callback assignment')
                    target=i.operands[1].imm&65535
                    need(target not in forbidden,'no spawn or normal rules callback replacement')
                    callbacks.add(target);todo.append(target)
            need(not any(o.type==CS_OP_MEM and i.reg_name(o.mem.base) in ('si','di') and o.mem.disp in (0x1E,0x20) for o in i.operands),
                 'closure independent of actor held/edge words')
            if i.mnemonic in ('ret','retf','iret'):break
            if i.mnemonic=='lcall':
                need(len(i.operands)==2 and all(o.type==CS_OP_IMM for o in i.operands),'resolved direct far import')
                seg,target=(o.imm&65535 for o in i.operands)
                need(not(seg==0x4090 and target in forbidden),'no actor allocation or active controller import')
                if seg==0x4090 and target!=0x181E:todo.append(target)
                else:imports.add((seg,target))
            elif i.mnemonic=='call' or i.mnemonic.startswith('j') or i.mnemonic.startswith('loop'):
                need(len(i.operands)==1 and i.operands[0].type==CS_OP_IMM,'no unresolved near transfer')
                target=i.operands[0].imm&65535;near.add(target)
                need(target not in forbidden,'no child creator/active controller transfer')
                todo.append(target)
                if i.mnemonic=='jmp':break
            at=nxt
    services={(0x4FFF,t) for t in (0x2389,0x24CB,0x2862,0x19A8,0x19BF,0x1BD9)}|{(0x4090,0x181E)}
    need(imports<=services,'only typed presentation/math or pool release imports; no task allocator')
    return dict(seeds=[f'{x:04X}' for x in seeds],instructions=len(seen),
       callback_closure=[f'{x:04X}' for x in sorted(callbacks)],imports=[f'{s:04X}:{o:04X}' for s,o in sorted(imports)],
       direct_near_targets=[f'{x:04X}' for x in sorted(near)])

def proof(r):
    context(r)
    entry_writers(r)
    death=graph(r,(0x7AB1,0x7D8D))
    children=graph(r,(0x9798,0x97BB))
    need(death['callback_closure']==['7AB1','7B1B','7B3A','7BFF','7C64','7CE5','7D7C','7D8D','7DA9','7DD8'],'complete fatal pair closure')
    need(children['callback_closure']==['9798','97BB','984D','9879'],'complete existing child closure')
    return death,children

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(a.source.suffix.lower()=='.wsc' and a.output.suffix.lower()=='.json','explicit source/report inputs')
    r=a.source.read_bytes();need(sha(r)==SOURCE,'immutable source')
    death,children=proof(r);negative=[]
    for label,at,data in (
       ('wrong terminal input owner',0x771FA7,bytes.fromhex('1A07')),
       ('fatal upper returns to active graph',0x7601F0,bytes.fromhex('9277')),
       ('fatal lower returns to spawn clock',0x7601FC,bytes.fromhex('C18E')),
       ('terminal lower resumes active controller',0x7486D8,bytes.fromhex('E82B1BCC')),
       ('terminal upper creates93E7',0x74867C,bytes.fromhex('E8BC15CC')),
       ('entry tests wrong actor',0x7417E9,bytes.fromhex('5C06')),
       ('entry reverses signedHP gate',0x7417EF,bytes.fromhex('7E')),
       ('terminal dispatch selects wrong stage',0x772566,bytes.fromhex('07')),
       ('fatal writer selects wrong stage',0x76019C,bytes.fromhex('07')),
       ('3030 callback write hidden as flag write',0x74398C,bytes.fromhex('02')),
       ('3030 caller forced to fatal continuation',0x7617DF,bytes.fromhex('B17A')),
       ('fatal graph imports task allocator',0x7483E1,bytes.fromhex('9A8009FF4F')),
       ('fatal graph unresolved callback assignment',0x7486A0,bytes.fromhex('89049090'))):
        b=bytearray(r);b[at:at+len(data)]=data
        try:proof(b)
        except (ValueError,IndexError):negative.append(label)
        else:raise ValueError('accepted mutation '+label)
    out=dict(status='CONDITIONAL_NO_NEW_CHILD_PASS',source_sha256=SOURCE,fatal_pair=death,preexisting_children=children,
       actual_terminal_entry=entry_writers(r),
       negative_controls=negative,input_keys_zero_proven=False,
       expiry_dependency='ExistingFDDCAE2A proof:93E7 source63+retire64/native56+57, not rerun.',
       gate='The actual upper/lower must already own the fatal7AB1/7D8D pair, with no later external retarget, before applying the no-new-child conclusion.',
       no_unconditional_terminal_entry_claim=True,
       limitations=['0B8B collision exclusion and07D6 input replacement do not clear stale actor keys or stop actor callbacks.',
         '1750 releases the orb list, not all26 actors; no blanket75-update expiry claim for888B.',
         'Actual terminal entry tests second actor HP, not callback identity. Source3030 is a separate HP writer without the pair; its actor/entry ownership remains open.',
         'Common presentation/math imports and existing181E pool release are typed retained services, not recursively reaudited.',
         'No ROM projection, emulator, save access, guest write or repeated child-duration census.'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(status=out['status'],sha256=sha(a.output.read_bytes()),fatal_instructions=death['instructions'],child_instructions=children['instructions'],negatives=len(negative))))

if __name__=='__main__':main()
