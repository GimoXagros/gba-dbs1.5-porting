#!/usr/bin/env python3
"""Replace the legacy commercial-only child command pointer with source-relative data."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import no_inbound
from shoot_resource_conversion import parse_shoot_p1,convert_shoot_payload_item
from verify_shoot_static_companion_clear import Machine

ROOT=Path(__file__).resolve().parents[1]
INPUT='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
RECT=0x5B9180
LEDGER='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
POPS=(('child',0x3D1E30,0x5B9000,(6,8,6)),
      ('upper',0x3CF410,0x5D0000,(7,8,2,7,2,8)),
      ('rules',0x3BD730,0x5D029C,(12,4,2,12,12,4,6,2,12,5,4,16,18)))
DEPS={
 'shoot_resource_conversion.py':'9DC5CAF3564CD3BF38A37A267A369AA7CA925249D4A498AB2EE9E89CAD7F6B62',
 'build_shoot_initializer_p1_assets.py':'910CC5188CF32B0BA94F4572BF2ACBC90F5B877BC4484292E32D2C9E1114CC9B',
 'build_shoot_resource_integration.py':'FADCFC5F2E7DC7022B0B6E202F07A3EF2A2E516BFD170B198DB7B4EA2FAA34CD',
 'analyze_waterfall_third_pattern.py':'DB327A22961631CBEE0CEB725525BFBA06775115313C0F34504AF1D9CAE174A3',
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943'}
PINS=((0x353C88,0x353D38,'1597DA8147E3E463232DDE90D53E62DD597DE1A34E53497BFD6B06A48354D0F3'),
      (0x36E348,0x36E3B8,'09C6FF0028F9798681E907A360FC70D3C0C6B90C78880B8B0E6EA4007123A2D7'),
      (0x36EB54,0x36EBF0,'768615E7DC5C692A064FC970FB481C2095C4DD32654FC452379DEFCA7878AAD6'),
      (0x6FD000,0x6FD044,'872440BE1C198881123D116F60ECE4A534820333C98B356B0045D5C8071FD397'))


def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
def word(v):return struct.pack('<I',v)


def population(before,source):
    found=[];rows=[];total=0
    for name,raw,native,counts in POPS:
        parsed=parse_shoot_p1(source,raw)
        need(tuple(parsed['counts'])==counts,'bounded source payload population '+name)
        need(u(before,native)==0x08000000+native+8,'native event table '+name)
        local=[]
        for event,payload in enumerate(parsed['payloads']):
            count,commands,metadata,event_b=struct.unpack_from('<4I',before,native+8+event*16)
            need(count==len(payload),'source/native event count')
            for index,item in enumerate(payload):
                at=commands-0x08000000+index*16;relative=struct.unpack_from('<H',item,10)[0]
                # This legacy conversion is an EXPECTED OLD BYTES oracle only.
                # Nonzero source pointers below are resolved from their own container.
                need(before[at:at+16]==convert_shoot_payload_item(item),'exact historical payload predecessor')
                if relative:
                    need(name=='child' and event==1 and relative==0x10C,'reject unknown nonzero command pointer')
                    need(at==0x5B9098+index*16 and u(before,at+12)==0x08350438,'exact obsolete child mapping')
                    found.append((at+12,raw+relative));local.append(dict(event=event,index=index,source=raw+relative,site=at+12))
                else:need(u(before,at+12)==0,'zero source command pointer remains null')
                total+=1
        rows.append(dict(name=name,source=raw,native=native,payloads=sum(counts),nonzero=local))
    need(total==163 and len(found)==8 and len({s for _,s in found})==1,'complete current shared-converter production population')
    return found,rows


def apply(before,writes):
    out=bytearray(before)
    for a,old,new in writes:
        need(len(old)==len(new) and out[a:a+len(old)]==old,'ExpectedWrite '+hex(a))
        out[a:a+len(new)]=new
    return bytes(out)


def validate(before,after,writes):
    need(len(before)==len(after),'unchanged size')
    need(apply(after,[(a,new,old)for a,old,new in writes])==before,'whole-ROM inverse')


def actual_fragment(rom,command,flags=0):
    """Actual producer suffix and legacy dispatch, no services or BIOS models.

    The only added instruction is the exact native MUL at353CB8; the existing
    strict runner handles the remaining complete producer and dispatch.
    """
    m=Machine(rom,flags%3,(flags<<28)|0x10)
    actor,victim,slot=0x020112B0,0x02011710,0x030048C8
    m.r[4]=command
    for a,v,n in ((0x03004C50,actor,4),(0x03004C54,0x085B9178,4),
                  (0x03004C5C,0x4000,2),(0x03004C58,3584,2),(0x03004C5A,4413,2),(0x03004C4D,0,1),(0x03004C62,0,2)):
        m.put(a,v,n)
    m.run(0x08353C88,{0x08353CB8})
    need(u(rom,0x353CB8)==0xE0000093,'exact native MUL r0,r3,r0')
    m.r[0]=(m.r[3]*m.r[0])&0xFFFFFFFF
    m.run(0x08353CBC,{0x08353D38})
    rectangle=[m.get(slot+x,2)for x in (4,6,8,10,12)]
    need(m.get(slot)==actor and m.get(slot+16)==0x085B9178 and m.get(0x03004C4D,1)==1,'real producer owner/metadata/count')
    m.put(0x030049B8,victim);m.put(0x030049BC,0,2);m.put(0x030049C8,0x080D7A38)
    m.r[4],m.r[5]=slot,0x030049B8
    m.run(0x0836E348,{0x0836E3B8})
    need(m.get(0x03004D20,2)==rectangle[0] and m.r[4]==actor and m.r[5]==victim,'actual overlap metadata transfer and owners')
    m.put(victim+8,0,2)
    m.run(0x0836EB54,{0x0836EBA4})
    return rectangle,m.r[1],m.r[9]


def build(before,gba,source):
    need((sha(before),sha(gba),sha(source))==(INPUT,GBA,SOURCE),'exact6D and immutable originals')
    for name,digest in DEPS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen dependency '+name)
    for a,z,digest in PINS:need(sha(before[a:z])==digest,'unchanged real producer/consumer '+hex(a))
    found,rows=population(before,source)
    rectangle=source[found[0][1]:found[0][1]+10]
    need(rectangle==bytes.fromhex('190000000000D000D000'),'exact source type19 offsets0/0 and halfextents208/208')
    need(gba[0x350438:0x350442]==bytes.fromhex('000000000000000005FF'),'actual obsolete retail pointer reads unrelated animation bytes')
    ledger_bytes=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    need(sha(ledger_bytes)==LEDGER,'complete ownership ledger pin');ledger=json.loads(ledger_bytes)
    need(ledger['normalized_interval_count']==1394 and ledger['layer_count']==70,'complete ownership population')
    owned=[[0,0x400000]]+ledger['merged_union']+[[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0],
        [0x6FF380,0x6FF400],[0x6FF400,0x6FF410],[0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0]]
    need(RECT==0x5B9000+384 and RECT+10<=0x5B9200,'explicit child P1 resource-family extension before P0')
    need(not any(a<RECT+10 and RECT<z for a,z in owned),'extension overlaps no declared interval or reservation')
    need(before[RECT:RECT+10]==b'\xff'*10,'whole extension erased')
    ownership=no_inbound(before,[(RECT,RECT+10)])
    need(not ownership['classified_instruction_interiors'],'zero no-inbound exemptions')
    writes=[(at,word(0x08350438),word(0x08000000+RECT))for at,_ in found]+[(RECT,b'\xff'*10,rectangle)]
    after=apply(before,writes);validate(before,after,writes)
    # Only these eight nonzero command pointers are authoritative source-relative
    # relocations. Every zero command pointer, event B, metadata and timing stays exact.
    for name,raw,native,counts in POPS:
        for event,count in enumerate(counts):
            commands=u(after,native+12+event*16)-0x08000000
            for index in range(count):
                at=commands+index*16+12
                need(u(after,at)==(0x08000000+RECT if name=='child' and event==1 else 0),'all163 final command-pointer domain')
    checks=0
    for at,_ in found:
        for flags in range(16):
            result,index,destination=actual_fragment(after,0x08000000+at-12,flags)
            need(result==[0x19,3584,4413,208,208] and index==34 and destination==u(gba,0x36EBEC)==0x0836F37C,'source-correct real producer/legacy dispatch')
            checks+=1
    wrong,index,destination=actual_fragment(before,0x085B9098)
    need(wrong[0]==0 and index==0xFFFFFFF0 and destination==0x0A000003,'actual original malformed producer counterexample')
    rejected=[]
    for at in [a for a,_,_ in writes]+[RECT+10,0x5B9178,0x5D00D8,0x36EB9C,0x6FD000]:
        bad=bytearray(after);bad[at]^=1
        try:validate(before,bad,writes)
        except ValueError:rejected.append(at)
        else:raise ValueError('ineffective inverse mutation')
    return after,dict(schema=1,status='SOURCE_RELATIVE_CHILD_ATTACK_RECTANGLE_PASS',input_sha256=INPUT,
        retail_sha256=GBA,source_sha256=SOURCE,output_sha256=sha(after),
        source_rectangle=dict(raw=0x3D1F3C,bytes=10,sha256=sha(rectangle),type=0x19,offsets=[0,0],half_extents=[208,208]),
        producer_populations=rows,total_source_payloads=163,nonzero_relocations=8,unchanged_null_pointers=155,
        ownership=ownership,reservations=[[RECT,RECT+10]],layout_ledger_sha256=LEDGER,
        ownership_family=dict(original_resource_envelope=[0x5B851C,0x5B9328],original_P1=[0x5B9000,RECT],
                              explicit_P1_extension=[RECT,RECT+10],next_P0=0x5B9200,anonymous_tail_reuse=False),
        writes=[dict(raw=a,bytes=len(old),before=old.hex().upper(),after=new.hex().upper())for a,old,new in writes],
        declared_bytes=42,changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        actual_ARM_producer_overlap_dispatch_cases=checks,original_actual_ARM_counterexample=dict(type=wrong[0],index=index,target=destination),
        fragment_boundary='Actual353C88 full producer including exact native MUL353CB8; actual36E348 metadata transfer; actual36EB54 and6FD000 dispatch. No BIOS/services, collision geometry test or reaction body executed.',
        inverse_mutations_rejected=rejected,legacy_converter_unchanged=True,
        authoritative_rule='Nonzero child command pointer resolves against its own WSC1.5 P1 base; commercial-only hardcoded032C mapping is not source1.5 proof.',
        runtime_executed=False,independent_QA_pending=True,main_promotion_approved=False,
        dependencies={**DEPS,Path(__file__).name:sha(Path(__file__).read_bytes())})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','gba','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    need(len({v.resolve()for v in (a.input,a.gba,a.source,a.output,a.manifest)})==5,'distinct paths')
    need(not a.output.exists() and not a.manifest.exists(),'fresh outputs')
    result,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('[SOURCE RECTANGLE PASS] '+report['output_sha256'])


if __name__=='__main__':main()
