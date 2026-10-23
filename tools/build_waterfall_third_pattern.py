#!/usr/bin/env python3
"""Restore the source-owned third Waterfall configuration and constructor.

Four spans,156 bytes. Existing mode1 wait/exit code is source-equivalent and
retained. Two phase2 row calculations now select source-prescribed successors.
No fallback, selector clamp, palette, RAM allocation, or shared stage-getter
change is introduced.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import (BASE,PARENT,GBA,OLD,NEW,RECORD,ENTRY,SLOT,
    RESERVATIONS,WRITE_SPANS,PHASE2,need,sha,u32,proof,no_inbound)


def bl(at,target):
    delta=target-(BASE+at+8)
    need(delta%4==0 and -(1<<25)<=delta<(1<<25),"ARM BL extent")
    return 0xEB000000|((delta//4)&0xFFFFFF)


def build(before,gba,old,source):
    need(tuple(map(sha,(before,gba,old,source)))==(PARENT,GBA,OLD,NEW),"fixed predecessor and source ROMs")
    evidence=proof(before,gba,old,source)
    for s,e in RESERVATIONS:
        need(before[s:e]==b'\xff'*(e-s),"exact FF ownership")
    ownership=no_inbound(before,WRITE_SPANS)
    # Retain every constructor instruction except two source constants and
    # four necessary PC-relative relocations. Shared wait installs shared exit.
    entry=bytearray(before[0x585200:0x585274])
    replacements={0x04:0xE59F8068,  # owner literal at entry+74
                  0x08:0xE3A00003,  # source hazard mode3 before event service
                  0x20:bl(ENTRY+0x20,0x08012874),
                  0x4C:0xE3A080C0,  # source initial sine phaseC0
                  0x60:0xE59F8010,  # retained wait pointer at entry+78
                  0x68:bl(ENTRY+0x68,0x08585274)}
    for off,word in replacements.items():
        struct.pack_into('<I',entry,off,word)
    entry.extend(struct.pack('<III',0x0300256A,0x08585274,BASE+ENTRY))
    need(len(entry)==128 and ENTRY+124==SLOT,"124B constructor plus4B callback slot")
    source_record=source[0x7450C1:0x7450D1]
    record=source_record[:14]+bytes(2)+struct.pack('<I',BASE+SLOT)
    writes=((RECORD,record,"source third config"),(ENTRY,bytes(entry),"mode3 constructor and callback slot"))+tuple(
        (at,struct.pack('<I',new),"source phase2 successor row")for at,_,new in PHASE2)
    after=bytearray(before)
    for at,blob,_ in writes:
        after[at:at+len(blob)]=blob
    inverse=bytearray(after)
    for at,blob,_ in writes:
        inverse[at:at+len(blob)]=before[at:at+len(blob)]
    need(bytes(inverse)==before,"full ROM inverse")
    need(u32(after,RECORD+16)==BASE+SLOT and u32(after,SLOT)==BASE+ENTRY,"actual selector2 callback graph")
    need(after[0x585200:0x585390]==before[0x585200:0x585390],"retained mode1 entry/wait/exit unchanged")
    need(after[0x629500:0x629518]==before[0x629500:0x629518],"separate stage-priority proposal untouched")
    need(u32(after,0x58467C)==0xE2451001,"phase1 subtraction remains unchanged")
    for at,_,word in PHASE2:
        need(u32(after,at)==word,"two flags-neutral phase2 MOV instructions")
    report=dict(schema=1,kind="waterfall-third-pattern-native-repair",status="PASS",
        input_sha256=sha(before),output_sha256=sha(after),output_bytes=len(after),
        declared_bytes=sum(len(blob)for _,blob,_ in writes),changed_bytes=sum(a!=b for a,b in zip(before,after)),
        writes=[dict(offset=f"{at:06X}",bytes=len(blob),purpose=label,sha256=sha(blob))for at,blob,label in writes],
        source_record_hex=source_record.hex(),constructor_replacements={f"{k:02X}":f"{v:08X}"for k,v in replacements.items()},
        route={"pattern_selector":2,"record":"08584CE8","callback_slot":f"{BASE+SLOT:08X}","entry":f"{BASE+ENTRY:08X}","wait":"08585274","exit":"08585310"},
        full_inverse=True,reservation=ownership,source_proof_sha256=sha((json.dumps(evidence,sort_keys=True,separators=(',',':'))+'\n').encode()),
        limits=["No runtime claim; root owns execution probes.","No whole-stage or unrestricted native-service parity claim.","Stage-priority helper is not installed."])
    return bytes(after),report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('before','gba','old','source','output'):
        parser.add_argument(name,type=Path)
    parser.add_argument('--manifest',type=Path,required=True)
    args=parser.parse_args()
    need(args.before.suffix.lower()=='.gba' and args.gba.suffix.lower()=='.gba' and
         args.old.suffix.lower()=='.wsc' and args.source.suffix.lower()=='.wsc',
         "ROM-only input extensions checked before reading")
    inputs={getattr(args,k).resolve()for k in ('before','gba','old','source')}
    need(args.output.suffix.lower()=='.gba' and args.manifest.suffix.lower()=='.json',"output types")
    need(args.output.resolve() not in inputs and args.manifest.resolve() not in inputs and
         args.output.resolve()!=args.manifest.resolve(),"output/input alias rejected before reading")
    after,report=build(*(getattr(args,k).read_bytes()for k in ('before','gba','old','source')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(dict(status="PASS",output_sha256=report['output_sha256'],declared_bytes=report['declared_bytes'],changed_bytes=report['changed_bytes'])))


if __name__=='__main__':
    main()
