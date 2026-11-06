#!/usr/bin/env python3
"""Exact eight ordinary upper routes, including asymmetric X/Y rounding.

This source-only bound assumes the ordinary route owns position/motion.
External grab/damage/callback changes require separate ownership proofs.
"""
import argparse
import json
from pathlib import Path
import struct
from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha


def contracts(r):
    need(sha(r[0x7486D9:0x748968])=='54E18CA677F0A504D1BD077FE027197A4E59108F987ECE081E7471636762C3AD',
         'complete ordinary route selector and two-axis callback')
    need(sha(r[0x742219:0x74235D])=='60EA9094922CF91911C6C98C4E2D7F62AFDC326F180D6A8BD0E779AB4B6DED0D',
         'complete source motion integration and caps')
    exact(r,0x747B36,['and word ptr [si + 4], 0x43ff',
        'mov word ptr [si + 0x26], 0','mov word ptr [si + 0x28], 0',
        'mov word ptr [si + 0x32], 0','mov word ptr [si + 0x34], 0',
        'mov word ptr [si + 0x36], 0','mov word ptr [si + 0x38], 0'])
    exact(r,0x7486F6,['lcall 0x4fff, 0x1cb5','and ax, 7',
        'mov bx, ax','shl bx, 3','mov ax, word ptr cs:[bx - 0x7f34]'])
    exact(r,0x74872D,['mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0','mov word ptr [si + 0x80], 0'])
    exact(r,0x748913,['cmp word ptr [si + 0x80], 3','jne 0x74893c',
        'push 3','push 0xc00','push di','lcall 0x4fff, 0x24cb',
        'add sp, 6','mov word ptr [si + 0x32], 0',
        'mov word ptr [si + 0x34], 0','mov word ptr [si], 0x8069',
        'mov word ptr [si + 2], 0x4090','retf'])
    exact(r,0x742315,['mov ax, word ptr [bp - 2]',
        'mov bx, word ptr [si + 0x34]','cmp ax, 0','jge 0x742322',
        'neg ax','sar ax, 4','sar bx, 4',
        'cmp word ptr [bp - 2], 0','jge 0x742330','neg ax'])
    routes=list(struct.iter_unpack('<4h',r[0x7489CC:0x748A0C]))
    need(routes==[(3584,3456,3584,6272),(2176,4544,3904,6272),
        (1536,5888,5632,5888),(3264,6272,4992,4544),
        (3584,6272,3584,3456),(3904,6272,2176,4544),
        (5632,5888,1536,5888),(4992,4544,3264,6272)],'exact eight routes')
    return routes


def axis(position,velocity,start,target):
    midpoint=((start-target)>>1)+target
    if target>=start:
        if target<=position:return velocity,True
        return max(128,min(768,velocity+(2 if position<=midpoint else -2))),False
    if target>=position:return velocity,True
    return max(-768,min(-128,velocity+(-2 if position>=midpoint else 2))),False


def analyze(r):
    routes=contracts(r);results=[]
    for index,(sx,sy,tx,ty) in enumerate(routes):
        x,y=sx,sy;vx=vy=reached=0;seen=set();trace=[]
        for tick in range(1024):
            state=(x,y,vx,vy,reached)
            need(state not in seen,'no nonterminating route cycle')
            seen.add(state);trace.append(state)
            vx,x_done=axis(x,vx,sx,tx)
            vy,y_done=axis(y,vy,sy,ty)
            reached|=int(x_done)|(int(y_done)<<1)
            if reached==3:
                vx=vy=0
                break
            # Sticky reached bits do not zero an individual velocity. The
            # actual callback stops both axes only after reached==3.
            dx=(abs(vx)>>4)*(-1 if vx<0 else 1)
            dy=vy>>4
            need(-127<=dx<=127 and -127<=dy<=127,'source caps are inactive')
            x+=dx;y+=dy
        else:raise ValueError('route exceeded finite bound')
        results.append(dict(index=index,start=[sx,sy],target=[tx,ty],
            final=[x,y],callback_updates=tick+1,minimum_Y=min(s[1] for s in trace),
            maximum_Y=max(s[1] for s in trace),states=len(seen)))
    low=min(t['minimum_Y'] for t in results);high=max(t['maximum_Y'] for t in results)
    need((low,high)==(3451,6276),'actual finite route envelope including overshoot')
    need(low>1476,'requested loose upper Y lower bound')
    return dict(status='PASS',source_ordinary_routes=results,Y_inclusive=[low,high],
        total_states=sum(t['states'] for t in results),
        semantics='X truncates abs(vx)/16 then reapplies sign; Y uses signed floor vy/16; per-axis velocity ±2 clipped128..768; reached bits sticky, both-axis stop only at3',
        conditions=['Ordinary 7DD9→7EBB route owns position/motion; initializer acceleration remains zero.',
            'No external position correction, grab, damage continuation or callback change is admitted by this finite route proof.',
            'Pure pauses that preserve route coordinates, velocities and fields can delay completion but add no new position states.'],
        complete_actor_Y_domain=False,native_motion_equivalence_proved=False,
        ROM_modified=False,runtime_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh evidence required')
    r=a.source.read_bytes();need(sha(r)==SOURCE_SHA,'immutable source')
    out=analyze(r);negative=[]
    for label,at in [('route start',0x7489CE),('reached stop',0x748917),
                     ('Y rounding',0x742327),('speed floor',0x7488E7),
                     ('acceleration reset',0x747B58)]:
        bad=bytearray(r);bad[at]^=1
        try:analyze(bad)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective mutation '+label)
    out.update(source_sha256=sha(r),negative_controls_rejected=negative)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print('PASS8 ordinary source routes: Y3451..6276;5mutations; external ownership remains separate')


if __name__=='__main__':main()
