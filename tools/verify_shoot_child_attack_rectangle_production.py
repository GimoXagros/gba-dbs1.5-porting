#!/usr/bin/env python3
"""Source-only production inverse/ownership proof; no capture or ARM replay."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

from verify_shoot_initializer_p1_assets import parse_wsc
import verify_shoot_caller_resident as refs

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
INPUT='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
OUTPUT='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR='185072F560F82D5A8AD63E416E3E8C9A5A2503B353A5AEA9597C9F44CF20A3E1'
MANIFEST='FF0B5FFF3B43E692128A0A6B857AFC97F9FE714657439ACFD2CE05D078B2FF73'
LEDGER='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
PRIOR_QA='281C43DF0334374A872D88209D9305CF787E32893ED55C91E2B20116667E1C5B'
RECT=0x5B9180
POPS=((0x3D1E30,0x5B9000,[6,8,6]),(0x3CF410,0x5D0000,[7,8,2,7,2,8]),
      (0x3BD730,0x5D029C,[12,4,2,12,12,4,6,2,12,5,4,16,18]))
DEPS={
 'verify_shoot_initializer_p1_assets.py':'8FA7300FB4EAB4EDFB721392090CCDDC2E1A60409066A3F75CE10E11E0D49208',
 'verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a,n=4):return int.from_bytes(b[a:a+n],'little')
def word(v):return v.to_bytes(4,'little')

def inverse(before,after,writes):
    need(len(before)==len(after)==0x800000,'eight MiB unchanged')
    restored=bytearray(after)
    for at,old,new in writes:
        need(before[at:at+len(old)]==old and after[at:at+len(new)]==new,'ExpectedWrite '+hex(at))
        restored[at:at+len(old)]=old
    need(bytes(restored)==before,'whole-ROM inverse')

def source_population(before,after,source):
    rows=[];sites=[]
    for raw,native,counts in POPS:
        parsed=parse_wsc(source,raw)
        need(parsed['counts']==counts,'bounded source P1 counts')
        need(u(before,native)==BASE+native+8 and u(before,native+4)==0,'native P1 header')
        nonzero=0
        for event,items in enumerate(parsed['payloads']):
            count,pointer,metadata,event_b=struct.unpack_from('<4I',before,native+8+event*16)
            need(count==len(items),'source/native command counts')
            for index,item in enumerate(items):
                command=pointer-BASE+index*16;relative=u(item,10,2)
                need(0<=command<=len(before)-16,'bounded native command')
                if relative:
                    need(raw==0x3D1E30 and event==1 and relative==0x10C and raw+relative==0x3D1F3C,
                         'source P1-local sixth word')
                    need(command==0x5B9098+index*16,'all eight exact child event1 commands')
                    sites.append(command+12);nonzero+=1
                else:need(u(before,command+12)==u(after,command+12)==0,'155 null command pointers unchanged')
        rows.append(dict(source=raw,native=native,payloads=sum(counts),nonzero=nonzero))
    need(sum(r['payloads']for r in rows)==163 and len(sites)==8,'complete bounded producer population')
    # Current presentation selects its P1 bank/segment, then dereferences the
    # current source command+0A within ES before reading the ten-byte rectangle.
    contracts=((0x74250E,'8b751e8b45348e4532e6c2'),(0x74258A,'26837c0a007503e95300268b740a'),
      (0x7425B2,'268b4402f746fa00407402f7d80346fe894704268b44040346fc894706268b4406894708268b440889470a268b04'))
    for at,he in contracts:need(source[at:at+len(bytes.fromhex(he))]==bytes.fromhex(he),'source local rectangle consumer')
    return sites,rows

def audit(before,after,gba,source,manifest_blob):
    need(tuple(map(sha,(before,after,gba,source)))==(INPUT,OUTPUT,GBA,SOURCE),'four immutable ROM identities')
    need(sha((ROOT/'tools/build_shoot_child_attack_rectangle.py').read_bytes())==AUTHOR,'frozen author identity')
    for name,digest in DEPS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'pinned independent helper '+name)
    need(sha(manifest_blob)==MANIFEST,'exact source-only author manifest')
    manifest=json.loads(manifest_blob)
    sites,population=source_population(before,after,source)
    rectangle=source[0x3D1F3C:0x3D1F46]
    need(rectangle==bytes.fromhex('190000000000d000d000'),'type19/zero offsets/208 half extents')
    need(gba[0x350438:0x350442]==bytes.fromhex('000000000000000005ff'),'obsolete retail rectangle identity')
    writes=[(at,word(0x08350438),word(BASE+RECT))for at in sites]+[(RECT,b'\xff'*10,rectangle)]
    inverse(before,after,writes)
    need(len(writes)==9 and sum(len(old)for _,old,_ in writes)==42,'nine spans42 declared bytes')
    expected_manifest=[dict(raw=a,bytes=len(o),before=o.hex().upper(),after=n.hex().upper())for a,o,n in writes]
    need(manifest['writes']==expected_manifest and manifest['input_sha256']==INPUT and manifest['output_sha256']==OUTPUT and
         manifest['total_source_payloads']==163 and manifest['unchanged_null_pointers']==155,'manifest exact independent structure')
    ledger_blob=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    need(sha(ledger_blob)==LEDGER,'tracked ledger pin')
    ledger=json.loads(ledger_blob)
    need((ledger['normalized_interval_count'],ledger['layer_count'])==(1394,70),'complete ownership population')
    owned=[[0,0x400000]]+ledger['merged_union']+[[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0],
        [0x6FF380,0x6FF400],[0x6FF400,0x6FF410],[0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0]]
    need(not any(a<RECT+10 and RECT<z for a,z in owned),'no prior declared owner or full reservation overlap')
    need(0x5B851C<=0x5B9000 and RECT==0x5B9000+384 and RECT+10<=0x5B9200<0x5B9328,'explicit resource family extension before P0')
    refs.SPANS=((RECT,RECT+10),)
    need(refs.inbound(before)==[],'strict all-alignment mirrored pointer ARM Thumb no-inbound zero exemptions')
    scanner_controls=0
    for mirror in (0x08000000,0x0A000000,0x0C000000):
        need(refs.inbound(b'\xff'+word(mirror+RECT)+b'\xff'*8),'unaligned mirror control');scanner_controls+=1
    for blob in (word(0xEA0000FE),struct.pack('<H',0xE1FE)):
        need(refs.inbound(blob+b'\xff'*8,RECT-0x400),'ARM Thumb branch control');scanner_controls+=1
    rejected=[]
    for at in sites+[RECT,RECT+1,RECT+6,RECT+10,0x5B9178,0x36EB9C,0x6FD000,0x1302]:
        bad=bytearray(after);bad[at]^=1
        try:inverse(before,bad,writes)
        except ValueError:rejected.append(at)
        else:raise ValueError('ineffective inverse mutation')
    return dict(status='INDEPENDENT_SOURCE_ONLY_CHILD_RECTANGLE_PRODUCTION_PASS',input_sha256=INPUT,output_sha256=OUTPUT,
        source_sha256=SOURCE,retail_sha256=GBA,builder_sha256=AUTHOR,manifest_sha256=MANIFEST,
        source_population=population,total_source_payloads=163,nonzero_relocations=8,unchanged_null_pointers=155,
        source_rectangle=dict(raw=0x3D1F3C,hex=rectangle.hex().upper(),type=0x19,offsets=[0,0],half_extents=[208,208]),
        writes=expected_manifest,declared_bytes=42,changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        ownership=dict(ledger_sha256=LEDGER,declared_intervals=1394,layers=70,original_P1=[0x5B9000,RECT],
            explicit_extension=[RECT,RECT+10],next_P0=0x5B9200,resource_family=[0x5B851C,0x5B9328],scan_exemptions=[]),
        scanner_controls=scanner_controls,inverse_mutations_rejected=rejected,
        reused_actual_capture_ARM_QA_sha256=PRIOR_QA,reused_QA_artifact_read=False,
        captured_data_dependency=False,ARM_semantics_rerun=False,emulator_or_state_used=False,
        dependencies={**DEPS,Path(__file__).name:sha(Path(__file__).read_bytes())},
        qualification='Source-only component identity/inverse/ownership. Frozen281C actual producer, geometry and dispatcher evidence is cited by hash without reading it. Runtime acceptance, final main promotion and historical E5 remain separate.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','gba','source','manifest','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    result=audit(*(getattr(a,k).read_bytes()for k in ('before','after','gba','source','manifest')))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
