#!/usr/bin/env python3
"""Extend 8EF3 to every source-defined normal pattern; leave nonpattern scope open."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct
import sys
import types
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from analyze_shoot_lifetime_consumers import SOURCE_SHA, exact, need, sha
import verify_shoot_caller_resident as resident

INPUT='B64022D567EC2F023CB59DA8AC4D3FAE27EDD4278D3E522E872D5FF51FE8F84B'
BASE=0x08000000
HOOK,START,LIMIT=0x5CC0F0,0x6FE000,0x6FE020
BODY_SHA='B39AA67A3E25A17E4BA8CE84CA08E19DE2749623139F6A7D26400281BF0B800D'
SCANNER_SHA='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def signed(v):return v-65536 if v&32768 else v


def partition(s):
    exact(s,0x7497F3,['mov cx, 5','mov bx, 0x8fef',
        'mov ax, word ptr [si + 0x8c]','cmp ax, word ptr cs:[bx]',
        'jle 0x749807','add bx, 8','loop 0x7497fd',
        'mov cx, word ptr cs:[bx + 2]','mov bx, word ptr cs:[bx + 4]',
        'mov ax, word ptr [si + 0x26]','cmp ax, word ptr cs:[bx]',
        'jl 0x74981c','add bx, 4','loop 0x749812',
        'mov bx, word ptr cs:[bx + 2]','mov ax, bx','add bx, bx',
        'jmp word ptr cs:[bx - 0x7025]'])
    reads=set()
    def word(off):
        off&=65535;reads.add(0x740900+off)
        return struct.unpack_from('<H',s,0x740900+off)[0]
    ys={}
    for y in range(-32768,32768):
        row=0x8FEF
        for _ in range(5):
            if y<=signed(word(row)):break
            row+=8
        ys.setdefault(row,[]).append(y)
    result=[];normal=old=added=unrelated=0
    for row,yvalues in sorted(ys.items()):
        count,pointer=word(row+2),word(row+4)
        need(0<count<=9,'actual finite exhausted-loop count')
        intervals=[]
        for x in range(-32768,32768):
            bx=pointer
            for _ in range(count):
                if x<signed(word(bx)):break
                bx=(bx+4)&65535
            selector=word(bx+2);target=word(0x8FDB+selector*2)
            is_normal=selector<=9 and target==(0x8F29 if selector==0 else 0x8F65)
            admitted=yvalues[0]<=0x1B00 and (x<0x1E00 or yvalues[0]<=0x1600)
            need(admitted==is_normal,'proposed domain equals source normal-pattern population')
            if x>=0x1E00 and admitted:
                need(selector==(1 if yvalues[0]<=0x1500 else 0),'exact exhaustion selector')
            weight=len(yvalues)
            normal+=weight*is_normal;unrelated+=weight*(not is_normal)
            old+=weight*(yvalues[0]<=0x1B00 and x<0x1E00)
            added+=weight*(admitted and x>=0x1E00)
            identity=(selector,target,bx)
            if intervals and tuple(intervals[-1]['identity'])==identity:intervals[-1]['X'][1]=x
            else:intervals.append(dict(X=[x,x],identity=list(identity)))
        result.append(dict(Y=[yvalues[0],yvalues[-1]],row=hex(row),
            count=count,x_pointer=hex(pointer),intervals=intervals))
    need(normal==2568421376 and normal+unrelated==2**32,'exact full sixteen-bit partition')
    need(normal==old+added and added>0,'strict source-normal extension')
    return dict(rows=result,all_input_pairs=2**32,normal_pattern_pairs=normal,
        old_accepted_pairs=old,newly_accepted_pairs=added,nonpattern_pairs=unrelated,
        source_read_halfwords=[hex(a) for a in sorted(reads)],
        source_read_scope='CS code/table window only; no collision-grid access',
        normal_domain='signed Y<=1600: all signed X; 1600<signed Y<=1B00: signed X<1E00',
        unresolved_targets=['4090:0A80 code-middle','4090:E59A data-as-code','4090:EB4C data-as-code'])


def assembly(code,at):return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(code,BASE+at)[0])


def payload():
    return assembly('cmp r1, #0x1600\nbgt 0x085CC1C0\n'
        'cmp r1, #0x1500\nbgt 0x085CC188\nmov r1, #1\nb 0x085CC150',START)


def inbound(g):
    need(sha(Path(resident.__file__).read_bytes())==SCANNER_SHA,'frozen full conservative census')
    scan=types.FunctionType(resident.inbound.__code__,
        dict(resident.__dict__,SPANS=((START,LIMIT),)),argdefs=resident.inbound.__defaults__)
    # Rebind only a private globals dictionary, never the imported module.
    for data,origin in [(struct.pack('<I',0x0C000000+START+28),0),
        (struct.pack('<I',0xE28F0078),START-128),
        (struct.pack('<HH',0x481F,0),START-128),
        (struct.pack('<HH',0xE03E,0),START-128)]:
        need(bool(scan(data,origin)),'mirrored pointer/ARM ADR/Thumb literal/Thumb branch census fixtures')
    return scan(g)


def validate(before,after):
    stub=payload();branch=assembly(f'bge 0x{BASE+START:X}',HOOK)
    need(len(stub)==24 and len(branch)==4,'minimal24B stub and4B guard')
    need(after[START:START+24]==stub and after[HOOK:HOOK+4]==branch,'exact component bytes')
    inverse=bytearray(after);inverse[START:START+24]=b'\xFF'*24
    inverse[HOOK:HOOK+4]=before[HOOK:HOOK+4]
    need(bytes(inverse)==before and sha(inverse)==INPUT,'whole-ROM inverse and unchanged outside writes')
    # Direct decoded-contract verification, not a general CPU emulator.
    rows=[f'{i.mnemonic} {i.op_str}' for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(stub,BASE+START)]
    need(rows==['cmp r1, #0x1600','bgt #0x85cc1c0','cmp r1, #0x1500',
        'bgt #0x85cc188','mov r1, #1','b #0x85cc150'],'actual ARM dispatch and preserved register footprint')
    return rows


def build(before,source):
    need(sha(before)==INPUT and sha(source)==SOURCE_SHA,'exact B640/source inputs')
    need(sha(before[0x5CC0D0:0x5CC1D0])==BODY_SHA,'retained full8EF3 implementation')
    need(before[START:LIMIT]==b'\xFF'*(LIMIT-START),'whole reservation FF')
    refs=inbound(before);need(not refs,'no existing pointer/branch into reservation')
    proof=partition(source)
    out=bytearray(before);out[START:START+24]=payload()
    out[HOOK:HOOK+4]=assembly(f'bge 0x{BASE+START:X}',HOOK)
    decoded=validate(before,bytes(out));negatives=[]
    for label,at in [('branch',HOOK),('low-Y boundary',START),('upper-Y rejection',START+4),
        ('vector boundary',START+8),('zero target',START+12),('vector selector',START+16),
        ('vector target',START+20),('outside write',START+31)]:
        bad=bytearray(out);bad[at]^=1
        try:validate(before,bytes(bad))
        except ValueError:negatives.append(label)
        else:raise ValueError('ineffective mutation '+label)
    changed=sum(a!=b for a,b in zip(before,out))
    return bytes(out),dict(status='PASS',input_sha256=INPUT,output_sha256=sha(out),
        source_sha256=SOURCE_SHA,partition=proof,decoded_stub=decoded,
        conservative_census_dependency_sha256=SCANNER_SHA,
        incoming_references=refs,negative_controls_rejected=negatives,
        expected_writes=[dict(raw=hex(HOOK),bytes=4),dict(raw=hex(START),bytes=24)],
        changed_bytes=changed,whole_ROM_inverse=True,
        accepted_behavior='All old accepted inputs follow byte-identical code; new inputs reuse exact existing vector1/zero bodies, one RNG call and existing success continuation.',
        nonpattern_behavior='Retains prior native rejection. This is not claimed equivalent to source unrelated control transfers.',
        complete_controller_input_domain=False,external_scene_entry_authorized=False,
        runtime_executed=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    paths=[a.input.resolve(),a.source.resolve(),a.output.resolve(),a.manifest.resolve()]
    need(len(set(paths))==4,'distinct input/output paths')
    need(not a.output.exists() and not a.manifest.exists(),'fresh outputs required')
    after,report=build(a.input.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS28B source-normal subset extension; full inverse and8 mutations; external route remains closed')


if __name__=='__main__':main()
