#!/usr/bin/env python3
"""Source-pinned horizontal guards and counterexamples to broad X-only bounds.

This does NOT close the actual controller producer domain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from analyze_shoot_terminal_bx import exact, need, SOURCE


def contracts(s):
    exact(s,0x76FB4D,['xor bx, bx','cmp ax, 6','jne 0x76fbb6'])
    exact(s,0x76FB1D,['xor ax, ax','mov word ptr [bp - 4], ax'])
    exact(s,0x76FBB6,['mov dx, word ptr [bp - 2]','mov cx, word ptr [bp - 4]',
        'push bx','call 0x76fbea'])
    exact(s,0x76FD92,['mov bx, word ptr [di + 0x3a]','or bx, bx','je 0x76fd76',
        'jns 0x76fd9d','neg bx','shr bx, 4','cmp bx, 8','jb 0x76fda8','jmp 0x76ff6f'])
    exact(s,0x76FDC2,['test ax, 0x70','je 0x76fdd5','mov dx, ax','and dx, 0x7f',
        'add dx, cx','cmp dx, 0x80','jb 0x76fdf2'])
    exact(s,0x76FDD5,['add cx, ax','cmp cx, word ptr [bp - 0xe]','jb 0x76fde9',
        'mov cx, word ptr [bp - 0xe]','sub cx, 0x80','mov bx, 0x8000',
        'mov word ptr [bp - 0xa], bx'])
    exact(s,0x76FDFA,['mov dx, word ptr [di + 0x42]','shl dx, 4','sub ax, dx',
        'js 0x76fe1d','cmp word ptr [bp - 0x16], 0','jne 0x76fe19',
        'test ax, 0x70','je 0x76fe19','mov dx, ax','and dx, 0x7f',
        'add dx, cx','jns 0x76fdf2','add cx, ax','jns 0x76fe22',
        'xor cx, cx','mov bx, 0x8000'])
    exact(s,0x76FE28,['mov ax, word ptr [di + 0x28]',
        'add ax, word ptr [di + 0x3c]','js 0x76fdf5'])
    exact(s,0x76FDF5,['mov dx, bx','jmp 0x76fe98'])
    exact(s,0x76FEB0,['or dx, dx','je 0x76feff','mov word ptr [bp - 0xa], dx',
        'test dx, 0x8000','jne 0x76fec8','and dx, 3','je 0x76feff',
        'cmp dx, 2','je 0x76feff'])
    exact(s,0x76FEC8,['mov ax, word ptr [di + 0x3a]','mov bx, word ptr [di + 0x26]',
        'mov cx, word ptr [di + 0x42]','shl cx, 4','add bx, ax','or ax, ax',
        'js 0x76ff02','add bx, cx','mov ax, word ptr [bp - 0xe]','cmp ax, bx',
        'jae 0x76fef0','mov bx, ax','sub bx, cx','mov word ptr [di + 0x2a], bx',
        'dec word ptr [di + 0x2a]','jmp 0x76fef6','and bx, 0xff80','sub bx, cx',
        'dec bx','mov word ptr [di + 0x26], bx','mov word ptr [di + 0x3a], 0'])
    exact(s,0x76FF02,['sub bx, cx','jns 0x76ff0e','mov bx, cx',
        'mov word ptr [di + 0x2a], bx','jmp 0x76ff18','and bx, 0xff80',
        'add bx, 0x80','add bx, cx','mov word ptr [di + 0x26], bx',
        'mov word ptr [di + 0x3a], 0'])
    exact(s,0x747D8E,['mov word ptr [si + 0x26], 0xe00',
        'mov word ptr [si + 0x2a], 0xe00'])
    need(struct.unpack_from('<2H',s,0x3B4DD0+39*24)==(2,3),'actual Shoot2x3screen descriptor')


def horizontal_step(x, delta, terrain, negative_feet, width=7168, radius=96):
    if delta == 0:
        return x
    edge=x+(radius if delta>0 else -radius)
    if delta>0:
        if edge & 0x70 and (edge & 127)+delta<128:
            return x+delta
        outer=edge+delta>=width
    else:
        if edge>=0 and edge & 0x70 and (edge & 127)+delta>=0:
            return x+delta
        outer=edge<0 or edge+delta<0
    flags=(0x8000 if outer else 0) | (0 if negative_feet else terrain)
    if not flags & 0x8000 and flags & 3 in (0,2):
        return x+delta
    edge=x+delta+(radius if delta>0 else -radius)
    if delta>0:
        return width-radius-1 if edge>width else (edge & ~127)-radius-1
    return radius if edge<0 else (edge & ~127)+128+radius


def analyze(s):
    contracts(s)
    lo,hi=96,7071
    need(lo<=0xE00<=hi,'actual initial X is inside the full-width footprint')
    count=0
    for x in range(lo,hi+1):
        for delta in range(-127,128):
            after=horizontal_step(x,delta,0,True)
            need(lo<=after<=hi,'negative feet preserve outer footprint via world flags')
            count+=1
    # Actual inner-wall terrain can break both tempting X-only invariants.
    # Whether normal player motion reaches these starting states is separate.
    need(horizontal_step(7009,-1,1,False)==7136,'inside-wall corner exceeds radius envelope')
    need(horizontal_step(7167,1,0,True)==7168,'source can exceed nominal world width')
    need(horizontal_step(7199,1,0,True)==7071,'next phase crossing restores outer edge')
    path=[7009]
    for delta in (-1,1,-1,1,-1):path.append(horizontal_step(path[-1],delta,1,False))
    need(path==[7009,7136,7137,7264,7265,7392],'successive solid-wall phase-corner counterexample')
    need(all(struct.unpack_from('<H',s,0x33CA20+col*4)[0]&3 in (1,3)
             for col in (54,55,56)),'corresponding source row0/row1 cells are solid')
    return dict(source_sha256=SOURCE,status='OPEN_DOMAIN',producer_domain_closed=False,
        initial_X=0xE00,negative_feet_only_invariant=[lo,hi],negative_feet_cases=count,
        delta_range=[-127,127],radius_pixels=6,nominal_width=7168,
        positive_feet_solid_corner_path=path,
        rejected_generalizations=['all-Y full-footprint96..7071','all-Y nominal0..7167','all-Y overshoot0..7199'],
        remaining='positive normal-player exclusion or coupled XY invariant for entering the outer wall from above',
        scope='counterstates verify instruction/model behavior; actual initial-to-corner reachability is not asserted',
        ROM_modified=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();s=a.source.read_bytes()
    need(hashlib.sha256(s).hexdigest().upper()==SOURCE,'source identity')
    need(not a.output.exists(),'fresh evidence required')
    result=analyze(s);negative=[]
    for at in (0x76FD97,0x76FDD3,0x76FE17,0x76FE2E,0x76FEBB,0x76FEF6,0x76FF12):
        b=bytearray(s);b[at]^=1
        try:contracts(b)
        except ValueError:negative.append(hex(at))
        else:raise ValueError('ineffective mutation')
    result['negative_controls']=negative
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print('OPEN DOMAIN;',result['negative_feet_cases'],'negative-feet cases; solid-wall counterexamples;7negatives')


if __name__=='__main__':main()
