#!/usr/bin/env python3
"""Pin real Shoot terrain consumers and finite lower tracking invariants.

This proves the stated component contracts. It does not infer complete fighter
callback ownership from the terrain grid, or authorize external scene entry.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
from functools import lru_cache
from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha, s16


def terrain(source, candidate):
    for index in (39,40):
        at=0x3B4DD0+index*24
        need(struct.unpack_from("<HH",source,at)==(2,3),"actual Shoot dimensions")
        off,seg=struct.unpack_from("<HH",source,at+12)
        raw=(source[at+5]&127)*65536+((seg*16+off)&65535)
        need(raw==0x33CA20,"actual Shoot collision bank/segment")
    grid=source[0x33CA20:0x33CA20+56*54*4]
    for index in (29,30):
        at=0x580000+index*24
        need(struct.unpack_from("<HH",candidate,at)==(2,3),"native Shoot dimensions")
        need(struct.unpack_from("<I",candidate,at+12)[0]==0x08607000,"actual native collision pointer")
    need(candidate[0x607000:0x607000+len(grid)]==grid,"all3024 native cells source-exact")
    flags=[struct.unpack_from("<H",grid,i*4)[0] for i in range(3024)]
    need(all((x&3) in (1,3) for x in flags[50*56:]),"complete solid bottom four rows")
    need(all(x==3 for x in flags[51*56:]),"three full type3 rows")
    drop=[i//56 for i,x in enumerate(flags) if x&3==2]
    need(sorted(set(drop))==[33,39,42,44],"all drop-through rows")
    need(all(flags[y*56+x]==0 for y in range(45,50) for x in range(7,49)),"five-row interior gap")
    exact(source,0x74192C,["cmp word ptr [si + 0x3a], 0x7f","jle 0x741937",
        "mov word ptr [si + 0x3a], 0x7f","cmp word ptr [si + 0x3a], -0x7f",
        "jge 0x741942","mov word ptr [si + 0x3a], 0xff81","cmp word ptr [si + 0x3c], 0x7f",
        "jle 0x74194d","mov word ptr [si + 0x3c], 0x7f","cmp word ptr [si + 0x3c], -0x7f",
        "jge 0x741958","mov word ptr [si + 0x3c], 0xff81"])
    exact(source,0x76FC1B,["mov ax, word ptr es:[si + 0xe]","mov bx, 0x12","mul bx","shl ax, 7",
        "mov word ptr [bp - 0x10], ax","mov ax, word ptr es:[si + 0xc]","mov bx, 0x1c",
        "mul bx","shl ax, 7","mov word ptr [bp - 0xe], ax"])
    exact(source,0x76FED4,["add bx, ax","or ax, ax","js 0x76ff02","add bx, cx",
        "mov ax, word ptr [bp - 0xe]","cmp ax, bx","jae 0x76fef0","mov bx, ax","sub bx, cx",
        "mov word ptr [di + 0x2a], bx","dec word ptr [di + 0x2a]","jmp 0x76fef6",
        "and bx, 0xff80","sub bx, cx","dec bx","mov word ptr [di + 0x26], bx",
        "mov word ptr [di + 0x3a], 0"])
    exact(source,0x766A55,["push dx","xor ax, ax","test word ptr [si + 0x20], 0x40",
        "je 0x766ab4","test word ptr [si + 0x1e], 4","je 0x766ab4",
        "mov ax, word ptr [si + 0x4a]","and ax, 3","cmp ax, 2","jne 0x766ab4"])
    exact(source,0x768619,["test word ptr [si + 0x4a], 3","jne 0x76862f",
        "mov word ptr [si], 0x1b8f","mov word ptr [si + 2], 0x668e","and word ptr [si + 6], 0xfffd"])
    exact(source,0x747D74,["mov word ptr [si + 4], 0xe700","mov word ptr [si + 6], 0x40",
        "mov word ptr [si + 8], 0","mov word ptr [si + 0xa], 0"])
    exact(source,0x747D8E,["mov word ptr [si + 0x26], 0xe00","mov word ptr [si + 0x2a], 0xe00",
        "mov word ptr [si + 0x28], 0xff80","mov word ptr [si + 0x2c], 0xff80"])
    return dict(source_grid="33CA20",native_grid="08607000",cells=3024,bytes=len(grid),grid_sha256=sha(grid),
        world_units=dict(width=0x1C00,height=0x1B00),solid_rows=[50,51,52,53],drop_rows=sorted(set(drop)),
        source_actor_reset=dict(flags4="E700",flags6="0040",flags8=0,flagsA=0,x="0E00",y="FF80"),
        actual_consumer="7418C7 object loop -> 6F76:03B1 -> live BG dimensions and wall correction -> 7419C6/C9 commit",
        right_wall="76FED4..76FEFA: width - radius - 1, then deltaX=0",
        movement_cap="74192C..741953: signed deltaX/deltaY in[-127,127] when terrain8000 and bypass0800 clear",
        drop_condition="A edge40 and Down held4 and ground lowbits2; clear flag6:2 on empty ground",
        remaining="Terrain/grid proof is not complete fighter-callback/landing/bypass ownership.")


def tracking(source):
    exact(source,0x749702,["mov ax, word ptr [bx + 0x26]","add ax, 0x10",
        "cmp ax, word ptr [si + 0x26]","jb 0x74971a","sub ax, 0x20",
        "cmp ax, word ptr [si + 0x26]","ja 0x749720","xor ax, ax","jmp 0x749723",
        "mov ax, 0xfe80","jmp 0x749723","mov ax, 0x180","mov word ptr [si + 0x32], ax"])
    exact(source,0x749668,["mov word ptr [si + 0x80], 0xe1"])
    exact(source,0x7496A0,["mov word ptr [si + 0x80], 0x14","mov bx, word ptr [si + 0x14]",
        "mov ax, word ptr [bx + 0x28]","mov word ptr [si + 0x8c], ax"])
    exact(source,0x749752,["mov bx, word ptr [si + 0x14]","mov ax, word ptr [bx + 0x26]",
        "cmp ax, word ptr [si + 0x26]","jb 0x749764","ja 0x74976a","xor ax, ax","jmp 0x74976d",
        "mov ax, 0xfe80","jmp 0x74976d","mov ax, 0x180","mov word ptr [si + 0x32], ax"])
    max_target=0x1BFF
    def velocity(x,t,band):
        if band:
            a=(t+16)&65535
            return -24 if a<x else 24 if ((a-32)&65535)>x else 0
        return -24 if t<x else 24 if t>x else 0
    @lru_cache(None)
    def actions(x,band):
        # Each unsigned comparison is monotone inside these exact target
        # intervals. Enumerate both endpoints; include subtract-wrap at16.
        cuts=sorted({0,max_target+1,*[max(0,min(max_target+1,k))
            for k in (16,x-16,x-15,x,x+1,x+16,x+17)]})
        reps={v for a,b in zip(cuts,cuts[1:]) for v in (a,b-1) if a<b}
        return frozenset(velocity(x,t,band) for t in reps)
    for x in (0,1,15,16,17,31,32,0x1BEF,0x1BFF,0x1C06,0x8000,0xFFF9,0xFFFF):
        for band in (False,True):
            need(actions(x,band)=={velocity(x,t,band) for t in range(max_target+1)},"partition edge cross-check")
    # Independent integer-inequality elimination of target t. For the band
    # case split t<16 (subtraction wraps) from t>=16; addition never wraps.
    # This checks the interval implementation for every possible current X.
    for x in range(65536):
        band_actions=set()
        if x>16:band_actions.add(-24)
        if x<=31 or x<max_target-16:band_actions.add(24)
        if x<=max_target+16:band_actions.add(0)
        follow_actions=set()
        if x>0:follow_actions.add(-24)
        if x<max_target:follow_actions.add(24)
        if x<=max_target:follow_actions.add(0)
        need(actions(x,True)==band_actions and actions(x,False)==follow_actions,"all65536 X action preimages")
    # Begin at any allowed P1 X, not only the initializer coordinate. This
    # overapproximates arbitrary player movement between every tracking tick.
    states={(x,0) for x in range(max_target+1)}
    maximum=0;minimum=0;transitions=0
    for tick in range(245):
        if tick<224:
            states={((x+v)&65535,v) for x,_ in states for v in actions(x,True)}
        elif tick==224:  # expiring225th tracking tick retains previous vx
            states={((x+v)&65535,v) for x,v in states}
        elif tick<244:
            states={((x+v)&65535,v) for x,_ in states for v in actions(x,False)}
        else: states={(x,0) for x,_ in states}
        transitions+=len(states)
        maximum=max(maximum,max(s16(x) for x,_ in states));minimum=min(minimum,min(s16(x) for x,_ in states))
        need(all(s16(x)<0x1E00 for x,_ in states),"all finite pursuit X outcomes stay in selector domain")
    return dict(tracking_updates=224,expiry_kept_velocity_updates=1,follow_updates=19,stop_updates=1,
        complete_action_preimages=65536*2,
        abstract_state_visits=transitions,reachable_signed_min=minimum,reachable_signed_max=maximum,
        initial_target_domain=[0,max_target],target_choice="arbitrary each tick; no assumed player speed",
        wrapping="actual16-bit coordinate wrap and unsigned tracking comparisons preserved",
        condition="P1 X remains in0..1BFF, lower receives only own±0180 velocity integration, and phase timing follows exact callbacks",
        result="Under these explicit contracts every captured currentX satisfies signedX<1E00; no idle/clamp fallback used.")


def main():
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("candidate",type=Path)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    need(a.source.suffix.lower()!=".sav" and a.candidate.suffix.lower()!=".sav","save inputs forbidden")
    s,g=a.source.read_bytes(),a.candidate.read_bytes()
    need(sha(s)==SOURCE_SHA,"immutable source")
    need(sha(g)=="5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46","exact v65")
    report=dict(source_sha256=sha(s),candidate_sha256=sha(g),terrain=terrain(s,g),tracking=tracking(s),
        complete_reachable_domain_proved=False,ROM_modified=False)
    for which,offset in (("grid",0x33CA20+50*56*4),("tracking",0x749704)):
        bad=bytearray(s);bad[offset]^=1
        try: terrain(bytes(bad),g) if which=="grid" else tracking(bytes(bad))
        except ValueError: pass
        else: raise ValueError("negative control accepted: "+which)
    report["negative_controls_rejected"]=2
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+"\n")
    print("PASS real terrain/native grid and conditional complete finite tracking; fighter lifetime remains explicit")


if __name__=="__main__":main()
