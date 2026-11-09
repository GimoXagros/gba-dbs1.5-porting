#!/usr/bin/env python3
"""Independent bounded source/captured-native check; never imports the builder."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

from verify_shoot_initializer_p1_assets import parse_wsc
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as refs

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
BEFORE='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
AFTER='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR='185072F560F82D5A8AD63E416E3E8C9A5A2503B353A5AEA9597C9F44CF20A3E1'
RECT=0x5B9180
ATTACK,VICTIM=0x020112B0,0x02011710
POPS=((0x3D1E30,0x5B9000,[6,8,6]),(0x3CF410,0x5D0000,[7,8,2,7,2,8]),
      (0x3BD730,0x5D029C,[12,4,2,12,12,4,6,2,12,5,4,16,18]))

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a,n=4):return int.from_bytes(b[a:a+n],'little')
def put(b,a,v,n=4):b[a:a+n]=v.to_bytes(n,'little')

def inverse(before,after,writes):
    need(len(before)==len(after)==0x800000,'eight MiB unchanged')
    restored=bytearray(after)
    for at,old,new in writes:
        need(before[at:at+len(old)]==old and after[at:at+len(new)]==new,'exact span '+hex(at))
        restored[at:at+len(old)]=old
    need(bytes(restored)==before,'whole ROM inverse')

def memory_machine(rom,iw,ew,flags=0):
    m=Machine(rom,0,(flags<<28)|0x10)
    m.mem.update({0x03000000+i:v for i,v in enumerate(iw)})
    m.mem.update({0x02000000+i:v for i,v in enumerate(ew)})
    return m

def producer(rom,iw,ew,command,flags):
    m=memory_machine(rom,iw,ew,flags)
    m.r[4],m.r[5]=command,ATTACK+0xAC
    for at,value,n in ((0x03004C50,ATTACK,4),(0x03004C54,0x085B9178,4),
        (0x03004C5C,8,2),(0x03004C58,0xE00,2),(0x03004C5A,0x113D,2),(0x03004C4D,0,1)):
        m.put(at,value,n)
    m.run(0x08353C88,{0x08353CB8})
    need(u(rom,0x353CB8)==0xE0000093,'exact MUL without flags')
    m.r[0]=(m.r[0]*m.r[3])&0xFFFFFFFF
    m.run(0x08353CBC,{0x08353D38})
    record=[m.get(0x030048C8+i,2)for i in (4,6,8,10,12)]
    need(m.get(0x030048C8)==ATTACK and m.get(0x030048D8)==0x085B9178 and
         m.get(0x03004C4D,1)==1,'producer owner metadata count')
    return m,record

def dispatch(m,kind):
    m.put(0x03004D20,kind,2)
    m.r[4],m.r[5],m.r[8]=ATTACK,VICTIM,0x03004D20
    m.run(0x0836EB58,{0x0836EBA4})
    return m.r[1],m.r[8],m.r[9]

def overlap(rom,iw,ew,halfextents):
    m=memory_machine(rom,iw,ew)
    # Real helper arguments are pushed half-extents and center coordinates.
    m.r[14]=0x09000000
    values=[halfextents[1],halfextents[0],0x113D,0xE00,0xD8,0xB8,0x1410,0xDC0,0,0x03006000]
    for i,v in enumerate(values):m.put(m.r[13]+i*4,v)
    for i in range(8):m.put(0x03006000+i,0,1)
    initial=m.r[13]
    m.run(0x080135D4,{0x09000000})
    need(m.r[13]==initial,'geometry stack restored')
    return m.r[0]

def audit(before,after,gba,source,capture):
    need(tuple(map(sha,(before,after,gba,source)))==(BEFORE,AFTER,GBA,WSC),'exact four ROM identities')
    need(sha((ROOT/'tools/build_shoot_child_attack_rectangle.py').read_bytes())==AUTHOR,'frozen author')
    source_contracts=((0x74250E,'8b751e8b45348e4532e6c2'),
        (0x74258A,'26837c0a007503e95300268b740a'),
        (0x7425B2,'268b4402f746fa00407402f7d80346fe894704268b44040346fc894706268b4406894708268b440889470a268b04'))
    for at,he in source_contracts:
        need(source[at:at+len(bytes.fromhex(he))]==bytes.fromhex(he),'source ES-relative rectangle consumer '+hex(at))
    pointer_sites=[];population=[]
    for raw,native,counts in POPS:
        parsed=parse_wsc(source,raw)
        need(parsed['counts']==counts,'manual source P1 population')
        need(u(before,native)==BASE+native+8,'native P1 table')
        nonzero=0
        for event,items in enumerate(parsed['payloads']):
            count,commands,metadata,event_b=struct.unpack_from('<4I',before,native+8+event*16)
            need(count==len(items),'native command count')
            for index,item in enumerate(items):
                at=commands-BASE+index*16;relative=u(item,10,2)
                if relative:
                    need(raw==0x3D1E30 and event==1 and relative==0x10C,'bounded local pointer population')
                    need(at==0x5B9098+index*16 and u(before,at+12)==0x08350438,'captured malformed pointer domain')
                    need(raw+relative==0x3D1F3C,'local WSC bank-relative resolution')
                    pointer_sites.append(at+12);nonzero+=1
                else:need(u(before,at+12)==u(after,at+12)==0,'null remains null')
        population.append(dict(raw=raw,native=native,count=sum(counts),nonzero=nonzero))
    need(sum(p['count']for p in population)==163 and len(pointer_sites)==8,'163 commands eight refs')
    rectangle=source[0x3D1F3C:0x3D1F46]
    need(rectangle==bytes.fromhex('190000000000d000d000'),'source type/center/half extents')
    writes=[(a,(0x08350438).to_bytes(4,'little'),(BASE+RECT).to_bytes(4,'little'))for a in pointer_sites]
    writes.append((RECT,b'\xff'*10,rectangle));inverse(before,after,writes)
    need(gba[0x350438:0x350442]==bytes.fromhex('000000000000000005ff'),'wrong native rectangle')
    for a,z in ((0x135D4,0x136C0),(0x353C88,0x353D38),(0x36E348,0x36E3B8)):
        need(before[a:z]==after[a:z]==gba[a:z],'retained native consumer '+hex(a))
    need(before[0x36EB54:0x36EBF0]==after[0x36EB54:0x36EBF0] and
         before[0x6FD000:0x6FD044]==after[0x6FD000:0x6FD044],'dispatcher unchanged')
    ledger_blob=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    need(sha(ledger_blob)=='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33','ledger pin')
    ledger=json.loads(ledger_blob);need((ledger['normalized_interval_count'],ledger['layer_count'])==(1394,70),'full ledger')
    owned=ledger['merged_union']+[[0,0x400000],[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0],
        [0x6FF380,0x6FF400],[0x6FF400,0x6FF410],[0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0]]
    need(all(not(a<RECT+10 and RECT<z)for a,z in owned),'no existing owner or reservation')
    need(0x5B851C<=0x5B9000<RECT and RECT==0x5B9000+384 and RECT+10<=0x5B9200<0x5B9328,'explicit resource family extension')
    refs.SPANS=((RECT,RECT+10),)
    need(refs.inbound(before)==[],'strict all-byte mirrored ARM Thumb inbound scan')
    scanner_controls=[]
    for alignment in range(4):
        for mirror in (0x08000000,0x0A000000,0x0C000000):
            blob=b'\xff'*alignment+(mirror+RECT).to_bytes(4,'little')+b'\xff'*8
            need(refs.inbound(blob),'unaligned mirrored pointer control');scanner_controls.append([alignment,mirror])
    for encoding in (struct.pack('<I',0xEA0000FE),struct.pack('<H',0xE1FE)):
        need(refs.inbound(encoding+b'\xff'*8,RECT-0x400),'branch inbound control')
        scanner_controls.append(encoding.hex())
    files=['invalid-dispatch-target-iwram.bin','invalid-dispatch-target-ewram.bin','positive-hit-first-failure.txt']
    evidence={name:sha((capture/name).read_bytes())for name in files}
    iw,ew=((capture/name).read_bytes()for name in files[:2])
    need(len(iw)==0x8000 and len(ew)==0x40000,'actual full captured RAM')
    def guest(at,n=4):return u(iw,at-0x03000000,n)if at>=0x03000000 else u(ew,at-0x02000000,n)
    need((guest(0x0300489C),guest(0x030048C8),guest(0x030048CC,2),guest(0x030048D8))==
         (VICTIM,ATTACK,0,0x085B9178),'actual list FIRST attacker type metadata')
    need((guest(ATTACK),guest(ATTACK+4,2)&15,guest(ATTACK+0xF0),guest(ATTACK+0xF4),guest(ATTACK+0xBA,2),
          guest(ATTACK+0xC6,2),guest(ATTACK+0xC8,2),guest(ATTACK+0xD0))==
         (0x085B9C00,0xB,0x085B9000,0x085B9200,1,0,8,0x085B9098),'actual child action and P1 ownership')
    need(guest(ATTACK-0x18)==0x08352580 and guest(ATTACK-8,2)&2,'actual active task slot17')
    need(guest(VICTIM+0x64,2)==4 and guest(guest(0x030048A0)+0x64,2)==37,'actual no positive hit HP')
    cases=0
    for site in pointer_sites:
        for flags in range(16):
            m,record=producer(after,iw,ew,BASE+site-12,flags)
            need(record==[0x19,0xE00,0x113D,0xD0,0xD0],'actual producer source geometry')
            m.r[4],m.r[5]=0x030048C8,0x030049B8
            m.run(0x0836E348,{0x0836E3B8})
            need(m.get(0x03004D20,2)==0x19 and m.r[4]==ATTACK and m.r[5]==VICTIM,'actual overlap metadata scratch transfer')
            need(dispatch(m,0x19)==(34,0x0836EBA8,0x0836F37C),'type19 legacy valid dispatcher boundary')
            cases+=1
    m,wrong=producer(before,iw,ew,0x085B9098,4)
    need(wrong==[0,0xE00,0x113D,0,0xFF05],'actual old producer geometry')
    need(dispatch(m,0)==(0xFFFFFFF0,0x0836EBA8,0x0A000003),'exact captured bad branch arithmetic')
    old_overlap=overlap(before,iw,ew,(0,0xFF05));new_overlap=overlap(after,iw,ew,(0xD0,0xD0))
    need((old_overlap,new_overlap)==(1,0),'real collision helper rejects source rectangle at actual failure positions')
    rejected=[]
    for at in pointer_sites+[RECT,RECT+1,RECT+6,RECT+10,0x5B9178,0x36EB9C,0x6FD000,0x1302]:
        bad=bytearray(after);bad[at]^=1
        try:inverse(before,bad,writes)
        except ValueError:rejected.append(at)
        else:raise ValueError('unrejected inverse mutation '+hex(at))
    return dict(status='INDEPENDENT_CHILD_RECTANGLE_PASS',input_sha256=sha(before),output_sha256=sha(after),
        source_sha256=sha(source),retail_sha256=sha(gba),author_sha256=AUTHOR,
        source_populations=population,payloads=163,nonzero=8,null_unchanged=155,source_consumer_spans=source_contracts,
        written_spans=[dict(at=a,before=o.hex(),after=n.hex())for a,o,n in writes],declared_bytes=42,
        changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        explicit_resource_extension=[RECT,RECT+10],ownership_scan_exemptions=[],scanner_controls=len(scanner_controls),
        actual_capture=str(capture),capture_hashes=evidence,actual_child=ATTACK,actual_victim=VICTIM,
        producer_metadata_dispatch_cases=cases,old_counterexample=dict(record=wrong,index=0xFFFFFFF0,target=0x0A000003),
        captured_position_geometry=dict(old_overlap=old_overlap,source_overlap=new_overlap,attacker=[0xE00,0x113D],victim=[0xDC0,0x1410],victim_half_extents=[0xB8,0xD8]),
        inverse_mutations_rejected=rejected,guest_RAM_files_unchanged=True,
        qualification='Offline actual ARM fragments stop before the reaction body. Source rectangle removes the observed false overlap; runtime hit/expiry/terminal are not established. Original strict full-Core restore failure remains, no state normalization or rewriting. Historical E5 remains separate.',
        dependencies={name:sha((ROOT/'tools'/name).read_bytes())for name in
          ('verify_shoot_initializer_p1_assets.py','verify_shoot_static_companion_clear.py','verify_shoot_attack_dispatch.py','verify_shoot_caller_resident.py',Path(__file__).name)})

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','gba','source','capture','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    report=audit(*(getattr(a,k).read_bytes()for k in ('before','after','gba','source')),a.capture)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(report['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
