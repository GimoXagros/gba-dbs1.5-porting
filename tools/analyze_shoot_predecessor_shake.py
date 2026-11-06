#!/usr/bin/env python3
"""Pin stage7's actual projection-shake producer and stage11 dispatch exclusion."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_shoot_terminal_bx import exact, need, SOURCE


def contracts(s):
    exact(s,0x77CF23,['mov di, 0x4e','xor ax, ax','mov al, byte ptr [di + 0xe]',
        'pop di','pop ds','mov bx, ax'])
    exact(s,0x77CF92,['add bx, bx','call word ptr cs:[bx + 0x3c]'])
    need(struct.unpack_from('<H',s,0x77CD3A)[0]==0xC42,'stage7graphics entry77D932')
    exact(s,0x77D9C1,['mov di, 0x300','mov es, di','mov di, 0x112','xor ax, ax',
        'mov word ptr es:[di], ax','mov word ptr es:[di + 2], ax',
        'mov word ptr es:[di + 4], ax','mov word ptr es:[di + 6], ax',
        'mov word ptr es:[di + 8], ax','ret'])
    exact(s,0x7693ED,['mov di, 0x4e','xor ax, ax','mov al, byte ptr [di + 0xe]',
        'pop di','pop ds','mov bx, ax','xor cx, cx','add bx, bx',
        'call word ptr cs:[bx + 0x43c]'])
    need(struct.unpack_from('<H',s,0x7693BA)[0]==0x1901,'stage7update76A871')
    need(struct.unpack_from('<H',s,0x7693C2)[0]==0x2067,'stage11update76AFD7')
    exact(s,0x76A8BF,['call 0x76a724','call 0x76a58c','call 0x76a519',
        'mov sp, bp','pop bp','ret'])
    exact(s,0x76A51E,['mov si, 0x1000','mov ds, si','mov si, 0x3ce',
        'mov ax, word ptr [si + 8]','mov si, 0x300','mov ds, si','mov si, 0x112',
        'test ax, 1','jne 0x76a552','test ax, 4','jne 0x76a55e',
        'test ax, 2','jne 0x76a558','test ax, 7','je 0x76a586'])
    exact(s,0x76A552,['mov di, 0x1591','jmp 0x76a561','mov di, 0x1599',
        'jmp 0x76a561','mov di, 0x15a1',
        'inc word ptr [si + 2]','cmp word ptr [si + 2], 4','jb 0x76a586',
        'xor ax, ax','mov word ptr [si + 2], ax','inc word ptr [si + 4]',
        'and word ptr [si + 4], 3','add di, word ptr [si + 4]',
        'mov al, byte ptr cs:[di]','mov byte ptr [si], al',
        'mov al, byte ptr cs:[di + 4]','mov byte ptr [si + 1], al'])
    need(s[0x76A501:0x76A519]==bytes.fromhex(
        '00ff0001fe000200000100ff0100ff0000fe00fe00fe00fe'),'three exact shake tables')
    # Shoot's complete dispatch arm has just these two calls. Its local
    # palette helper contains no call instruction or camera-field store.
    exact(s,0x76B02F,['lcall 0x5eea, 0xe0b','call 0x76b1db',
        'mov sp, bp','pop bp','ret'])
    exact(s,0x76B1EF,['mov ax, 0x1000','mov ds, ax','mov si, 0x174'])
    exact(s,0x76B310,['pop cx','ret'])
    for site in (0x745B78,0x745EBB,0x746D8A):
        exact(s,site,['mov ax, 0x300','mov es, ax','mov word ptr es:[0x112], 0'])
    # Complete decoded function boundaries establish call populations.
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    c=Cs(CS_ARCH_X86,CS_MODE_16)
    def ins(a,z):
        result=list(c.disasm(s[a:z],a))
        need(sum(x.size for x in result)==z-a,'complete source body')
        return result
    calls=[(x.mnemonic,x.op_str) for x in ins(0x76AFD7,0x76B03B)
           if x.mnemonic in ('call','lcall')]
    need(calls==[('lcall','0x5eea, 0xe0b'),('call','0x76b1db')],
         'actualstage11 has no generic76B3D2 or stage7shake call')
    need(not any(x.mnemonic in ('call','lcall') for x in ins(0x76B1DB,0x76B312)),
         'palette leaf has no camera callee')


def proof(s):
    contracts(s)
    domain={0}
    for base in (0x76A501,0x76A509,0x76A511):
        domain.update(struct.unpack_from('<4b',s,base))
    need(domain=={-2,-1,0,1},'actual stage7 vertical projection shake range')
    cases=0
    for old in domain:
        for flags in range(8):
            for timer in range(4):
                for phase in range(4):
                    value=old
                    if flags and timer==3:
                        base=0x76A501 if flags&1 else 0x76A511 if flags&4 else 0x76A509
                        value=struct.unpack_from('<b',s,base+((phase+1)&3))[0]
                    need(value in domain,'all producer transitions preserve bounded shake')
                    cases+=1
    return dict(stage7_graphics_entry='77D932',stage7_update_entry='76A871',
        stage11_update_entry='76AFD7',projection_shake_values=sorted(domain),
        producer_transition_cases=cases,
        zero_invariant=False,
        generic_camera_shake_excluded_from_actual_stage11_dispatch=True,
        scope='stage7 initializer, stage7 shake writer/zero resetters, stage11 dispatch arm and palette leaf',
        limit='not an exhaustive RAM-writer proof or terminal camera/player tracking invariant; existing stage11E0B has its own later shake',
        ROM_modified=False,runtime_executed=False)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();s=a.source.read_bytes()
    sha=lambda x:hashlib.sha256(x).hexdigest().upper()
    need(sha(s)==SOURCE,'source identity');need(not a.output.exists(),'fresh output')
    result=proof(s);rejected=[]
    for label,at in [('stage7 graphics mapping',0x77CD3A),('stage11 update mapping',0x7693C2),
        ('shake table values',0x76A501),('producer phase bound',0x76A576),
        ('stage7 producer call',0x76A8C5),('stage11 camera exclusion',0x76B034)]:
        m=bytearray(s);m[at]^=1
        try:proof(m)
        except ValueError:rejected.append(label)
        else:raise ValueError('ineffective mutation '+label)
    result.update(status='PASS',source_sha256=SOURCE,negative_controls=rejected)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS stage7shake[-2,-1,0,1];512transitions;stage11dispatch;6negatives')


if __name__=='__main__':main()
