"""Independent campaign revision2 AI progress tables and decimal HUD verification."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from verify_shoot_static_companion_clear import Machine as PriorMachine
import verify_campaign_stage_progression as producer
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
SOURCE_BASE = 0x782970
FIRST, LIMIT = 0xD3FEE0, 0xD40000
CONFIG = 0x03002310
RETURN = 0x08001234
AFTER = '933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
MANIFEST = '6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C'


def need(value, why):
    if not value: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest().upper()


def word(raw, at): return struct.unpack_from('<I',raw,at)[0]


class Machine(PriorMachine):
    """Add retained typed register-offset load and post-index stores, without mocks."""
    def run(self,start,stops,max_steps=16000):
        for _ in range(128):
            try: return super().run(start,stops,max_steps)
            except ValueError as error:
                if str(error) != 'immediate halfword transfer': raise
                pc = self.r[15]-8; instruction = self.get(pc)
                if pc == 0x080C700C and instruction == 0xE19500F0:
                    value = self.get(self.r[5]+self.r[0],2)
                    self.r[0] = (value-0x10000 if value&0x8000 else value)&0xFFFFFFFF
                    start = pc+4
                    continue
                need(instruction & 0x0E000090 == 0x90 and instruction & 0x01600060 == 0x00400020,
                     'only unsigned immediate post-index halfword extension')
                base, target = (instruction>>16)&15, (instruction>>12)&15
                need(base != target and base != 15 and target != 15, 'nonalias transfer registers')
                offset = ((instruction>>4)&0xF0)|(instruction&15); address = self.r[base]
                if instruction & 0x100000: self.r[target] = self.get(address,2)
                else: self.put(address,self.r[target],2,True)
                self.r[base] = (address+(offset if instruction & 0x800000 else -offset))&0xFFFFFFFF
                start = pc+4
        raise ValueError('bounded post-index extension')


def source_contract(source,before):
    need(sha(source) == producer.SOURCE and sha(before) == producer.AFTER, 'source and frozenADBF pins')
    offsets = ((0xB9,0xC5,0xD1),(0xE3,0xEF,0xFB),(0x10D,0x119,0x125),(0x137,0x14F,0x167))
    for pointer_at, values in zip((0xDD,0x107,0x131,0x17F),offsets):
        need(struct.unpack_from('<3H',source,SOURCE_BASE+pointer_at) == values, 'source typed difficulty pointer family')
    byte_rows = [[list(source[SOURCE_BASE+p:SOURCE_BASE+p+12]) for p in family] for family in offsets[:3]]
    half_rows = [list(struct.unpack_from('<12H',source,SOURCE_BASE+p)) for p in offsets[3]]
    first = list(source[SOURCE_BASE+0x185:SOURCE_BASE+0x192])
    need(first == [7,7,6,6,5,5,4,4,3,3,3,3,3], 'complete first13 source values')
    need(list(before[0xC7078:0xC7082]) == first[:10], 'retained first-table prefix; following bytes belong to another table')
    for family in range(3):
        for difficulty in range(3):
            p = word(before,0xC7048+family*12+difficulty*4)-BASE
            need(list(before[p:p+9]) == byte_rows[family][difficulty][:9], 'all retained9-byte row prefixes')
    for difficulty in range(3):
        p = word(before,0xC706C+difficulty*4)-BASE
        expected = [v*4//5 for v in half_rows[difficulty]]
        need(list(struct.unpack_from('<9H',before,p)) == expected[:9], 'all27 retained halfwords establish4/5 integer conversion')
    producer.exact(source,0x782C2A,['mov di, 0x1000','mov ds, di','mov di, 0x4e','xor ax, ax',
        'mov al, byte ptr [di + 0x1e]','pop di','pop ds','mov di, ax','mov dl, byte ptr cs:[di + 0x185]'])
    for at in (0x782C93,0x782CBB,0x782CDF,0x782D08):
        producer.exact(source,at,['mov al, byte ptr [di + 0x1e]'])
    producer.exact(before,0xC8248,['ldr r8, [pc, #4]','ldrb r0, [r8, #0x1e]','bx lr'],True)
    need(word(before,0xC8254) == CONFIG, 'AI reads actual persisted progress, not physical stage')
    producer.exact(source,0x77E389,['cmp ax, 0xa','je 0x77e3c6','mov cl, 0xa','xor ah, ah','inc al','div cl'])
    producer.exact(source,0x77E39C,['mov cl, al','add cx, 0x2400','add cl, 0x14','mov word ptr es:[di], cx'])
    producer.exact(source,0x77E3AD,['mov al, ah','xor ah, ah','add ax, 0x2400','add al, 0x14',
        'mov word ptr es:[di], ax','inc di','inc di','mov ax, 0x2401','add cx, 8','rep stosw word ptr es:[di], ax'])
    return dict(byte_rows=byte_rows,source_half_rows=half_rows,native_half_rows=[[v*4//5 for v in row] for row in half_rows],
        first=first,progress_owner='0300232E, independent of physical stage0300231E and RNGrow0300232F',
        halfword_units='floor(source*4/5), proven by all27 existing native halfwords; no broader clock claim',
        source_AI_sha256=sha(source[0x782C20:0x782D2E]),source_HUD_sha256=sha(source[0x77E378:0x77E3DA]))


def fixture(rom,progress,difficulty=0,physical=0,row=0,seed=0):
    m = Machine(rom,seed=seed,flags=0xA0000010)
    for off in range(0x40):m.put(CONFIG+off,(off*13+9)&255,1)
    m.put(CONFIG+0x1E,progress,1);m.put(CONFIG+0xE,physical,1);m.put(CONFIG+0x1F,row,1)
    m.r[5]=difficulty*4;m.r[14]=RETURN
    for address,value in ((0x03004D8E,0xAB),(0x03004DCA,0xFFFE),(0x03004DCC,0xCAFE),(0x03004DAA,0xFF00)):
        m.put(address,value,1 if address==0x03004D8E else 2)
    return m


def ai_case(rom,model,progress,difficulty,physical=0,row=0):
    ends = (0x080C6FA4,0x080C6FCC,0x080C6FFC,0x080C7020)
    starts = (0x080C6F6C,0x080C6FA4,0x080C6FCC,0x080C6FFC)
    outputs = (0x03004D8E,0x03004DCA,0x03004DCC,0x03004DAA)
    values = [model['byte_rows'][k][difficulty][progress] for k in range(3)] + [model['native_half_rows'][difficulty][progress]]
    for k,(start,end,address) in enumerate(zip(starts,ends,outputs)):
        m=fixture(rom,progress,difficulty,physical,row);before=m.mem.copy();sp=m.r[13]
        m.run(start,{end})
        expected = ((0xAB+values[k])&15) if k==0 else ((0xFFFE+values[k])&0xFFFF) if k==1 else (values[k]&0x7F) if k==2 else ((0xFF00+values[k])&0xFFFF)
        size=1 if k==0 else 2
        need(m.get(address,size)==expected,'actual AI typed consumer field outcome')
        need(m.r[13]==sp,'actual AI segment stack balance')
        allowed=set(range(address,address+size))
        need(all(m.mem[a]==v for a,v in before.items() if a not in allowed),'AI adjacent config/state preserved')
        need([target for _,target,_ in m.calls]==[0x080C8248],'actual persisted-progress helper only')


def first_case(rom,model,progress):
    m=fixture(rom,progress);m.r[0]=0;regs=m.r[:]
    m.run(0x080C6EE0,{0x080C6EFC})
    need(m.r[3]==model['first'][progress] and all(m.r[k]==regs[k] for k in (0,5,13)),
         'actual first difficulty0 lookup preserves caller frame')


def hud_case(rom,progress,flags=0,alignment=0):
    m=Machine(rom,seed=4,flags=(flags<<28)|0x10);tile=0x0600E000+alignment
    m.r[0],m.r[5],m.r[14]=progress,tile,RETURN
    for off in range(-4,24):m.put(tile+off,0xCC,1)
    regs=m.r[:];before=m.mem.copy()
    end=m.run(0x080B5FB4,{0x080B6044,0x080B6054})
    if progress==10:
        need(end==0x080B6044 and m.mem==before and not m.calls,'final progress enters existing text path unchanged')
        need(m.r[5]==regs[5] and m.r[13]==regs[13] and m.r[14]==regs[14],'final text continuation ABI')
        return
    need(end==0x080B6054,'numeric progress uses ordinary post-fill continuation')
    digits=[int(x) for x in str(progress+1)]
    expected=[0x2214+x for x in digits]+[0x2201]*(9-len(digits))
    need([m.get(tile+2*i,2) for i in range(9)]==expected,'source decimal progress digits and exact blank count')
    need(m.r[5]==tile+18 and m.r[13]==regs[13],'HUD complete nine-word write and balanced stack')
    need(all(m.mem[a]==v for a,v in before.items() if not tile<=a<tile+18),'HUD adjacent tile preservation')
    need([target for _,target,_ in m.calls]==[0x08001064],'actual existing halfword fill helper executes')


def behavior(rom,model):
    ai=0
    for progress,difficulty,physical,row in itertools.product(range(12),range(3),(0,8,11),(0,7)):
        ai_case(rom,model,progress,difficulty,physical,row);ai+=4
    for progress in range(13):first_case(rom,model,progress)
    hud=0
    for progress,flags,alignment in itertools.product(range(11),range(16),(0,2)):
        hud_case(rom,progress,flags,alignment);hud+=1
    return dict(actual_AI_consumer_cases=ai,actual_first_lookup_cases=13,actual_HUD_cases=hud,
        existing_fill_executed=True,source_rows_extended_without_physical_stage_substitution=True)


def branch(at,target,cond=14):
    delta=target-at-8
    need(delta%4==0 and -(1<<25)<=delta<(1<<25),'ARM branch extent')
    return (cond<<28)|0x0A000000|((delta//4)&0xFFFFFF)


def structural(before,after,manifest,model,owner_bytes):
    need(sha(after)==AFTER,'frozen r2 candidate')
    expected={}
    for family in range(3):
        for difficulty in range(3):
            index=family*3+difficulty;at=FIRST+index*12
            expected[at]=bytes(model['byte_rows'][family][difficulty])
            expected[0xC7048+index*4]=struct.pack('<I',BASE+at)
    for difficulty in range(3):
        at=0xD3FF4C+difficulty*24
        expected[at]=struct.pack('<12H',*model['native_half_rows'][difficulty])
        expected[0xC706C+difficulty*4]=struct.pack('<I',BASE+at)
    expected[0xD3FF94]=bytes(model['first'])
    expected[0xC6EEC]=struct.pack('<I',branch(0xC6EEC,0xD3FFDC))
    expected[0xD3FFDC]=struct.pack('<3I',0xE59F8000,branch(0xD3FFE0,0xC6EF0),BASE+0xD3FF94)
    expected[0xB5FB4]=struct.pack('<I',branch(0xB5FB4,0xD3FFA4))
    expected[0xD3FFA4]=struct.pack('<13I',0xE350000A,branch(0xD3FFA8,0xB6044,0),
        0xE3500009,branch(0xD3FFB0,0xB5FBC,1),0xE59F0014,0xE0C500B2,0xE2400001,
        0xE0C500B2,0xE59F0008,0xE3A02007,branch(0xD3FFCC,0xB5FD4),0x2215,0x2201)
    need(len(expected)==29 and sum(map(len,expected.values()))==313,'independent29-span313-byte definition')
    rows=manifest['writes'];need(len(rows)==29 and {r['offset']:bytes.fromhex(r['after_hex']) for r in rows}==expected,
        'source tables, exact ARMv4 instructions/literals and hooks')
    restored=bytearray(after)
    for r in rows:
        at,size=r['offset'],r['size']
        need(size==len(expected[at]) and after[at:at+size]==expected[at] and
             before[at:at+size]==bytes.fromhex(r['before_hex']),'exact declared before/after span')
        restored[at:at+size]=before[at:at+size]
    need(len(after)==len(before)==0x1000000 and restored==before and
         sum(a!=b for a,b in zip(before,after))==297,'whole16MiB inverse and297 changed bytes')
    pins=('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
        '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
        '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD',producer.MANIFEST)
    need(tuple(map(sha,owner_bytes))==pins,'four prior allocation owners')
    owners=list(map(json.loads,owner_bytes))
    need([0xD33000,0xD40000] in owners[0]['reservations'] and
         owners[1]['allocation']['remaining_tail']==[0xD3F05A,0xD40000] and
         owners[2]['allocation']['suballocation']==[0xD3F100,0xD3FA00] and
         owners[3]['allocation']['suballocation']==[0xD3FB10,0xD3FB80],'positive parent and prior intervals')
    prior_count=0
    for k,owner in enumerate(owners):
        for r in owner['writes']:
            lo,hi=r['offset'],r['offset']+r['size']
            need(max(lo,FIRST)>=min(hi,LIMIT),'new span avoids every prior allocation write')
            if k==0:
                if not 0xD33000<=lo<0xD40000:continue
                need(sha(before[lo:hi])==r['after_sha256'],'prior audio contents')
            else:need(before[lo:hi]==bytes.fromhex(r['after_hex']),'prior source table/controller contents')
            need(after[lo:hi]==before[lo:hi],'prior content preserved after r2');prior_count+=1
    need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'whole authorized new interval blank')
    scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),
        argdefs=scanner.inbound.__defaults__)
    hits=scan(before);need(not hits,'zero conservative inbound references; no exemptions')
    need(manifest['allocation']['suballocation']==[FIRST,LIMIT] and manifest['allocation']['new_RAM_bytes']==0,
         'bounded allocation/no RAM claim')
    for r in owners[3]['writes']:
        at,size=r['offset'],r['size'];restored[at:at+size]=bytes.fromhex(r['before_hex'])
    need(sha(restored)==producer.BEFORE,'complete two-component inverse to frozenFBD9')
    return dict(spans=29,declared_bytes=313,changed_bytes=297,whole_inverse=True,
        combined_inverse_sha256=sha(restored),suballocation=[FIRST,LIMIT],prior_writes_checked=prior_count,
        prior_owner_sha256=pins,inbound_hits=hits,new_RAM_bytes=0)


def mutations(before,after,model):
    rejected=[]
    def reject(label,at,blob,check):
        changed=bytearray(after);changed[at:at+len(blob)]=blob
        try:check(bytes(changed))
        except (ValueError,IndexError):rejected.append(label)
        else:raise ValueError('semantic mutation survived: '+label)
    for family in range(4):
        at=0xC7048+family*12
        progress=9 if family==2 else 10
        reject('retail short AI family'+str(family),at,before[at:at+4],
            lambda rom,p=progress:ai_case(rom,model,p,0))
    reject('short first table retained',0xC6EEC,before[0xC6EEC:0xC6EF0],lambda rom:first_case(rom,model,10))
    reject('new halfword lacks native conversion',0xD3FF4C+20,
        struct.pack('<H',model['source_half_rows'][0][10]),lambda rom:ai_case(rom,model,10,0))
    reject('AI reads physical stage instead of progress',0xC824C,struct.pack('<I',0xE5D8000E),
        lambda rom:ai_case(rom,model,10,0,physical=0))
    reject('HUD final triggers at old progress7',0xD3FFA4,struct.pack('<I',0xE3500007),lambda rom:hud_case(rom,7))
    reject('HUD second digit remains one',0xD3FFBC,struct.pack('<I',0xE2400000),lambda rom:hud_case(rom,9))
    reject('two-digit HUD blank fill overruns',0xD3FFC8,struct.pack('<I',0xE3A02008),lambda rom:hud_case(rom,9))
    return rejected


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','manifest','source','audio-manifest','table-manifest','id13-manifest',
                 'producer-manifest','producer-review','report'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report required')
    pins={'verify_campaign_stage_progression.py':'142A81724FD15EFF70330C6A154DFCF83DB3DEB024FD3D1AC75854F5546697F5',
        'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
        'verify_shoot_attack_dispatch.py':'695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698',
        'verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}
    for name,digest in pins.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen independent dependency '+name)
    before,after,source=(x.read_bytes() for x in (a.before,a.after,a.source))
    raw=a.manifest.read_bytes();need(sha(raw)==MANIFEST,'frozen r2 manifest')
    review_raw=a.producer_review.read_bytes()
    need(sha(review_raw)=='1162727F1240E8AB2F9A658AF93D4E07E41B695F37B8262F48A574549B83E2C0' and
         json.loads(review_raw)['status']=='CAMPAIGN_PRODUCER_INDEPENDENT_PASS','completed producer gate retained')
    model=source_contract(source,before)
    allocation=structural(before,after,json.loads(raw),model,
        [x.read_bytes() for x in (a.audio_manifest,a.table_manifest,a.id13_manifest,a.producer_manifest)])
    cases=behavior(after,model);negative=mutations(before,after,model)
    report=dict(status='CAMPAIGN_PROGRESS_CONSUMERS_INDEPENDENT_PASS',before_sha256=sha(before),after_sha256=sha(after),
        manifest_sha256=MANIFEST,verifier_sha256=sha(Path(__file__).read_bytes()),source=model,
        allocation=allocation,actual_ARM=cases,rejected_semantic_mutations=negative,
        predecessor_review_sha256=sha(review_raw),production_builder_imported=False,emulator_launched=False,
        old_producer_semantic_suite_rerun=False,runtime_verified=False,
        limitations=['Source clean default campaign mode remains the producer scope; alternate mode not added.',
            'Final HUD label branches to the exact retained text-copy path; this is not graphical runtime evidence.',
            'AI progress table conversion inherits the27 matching native halfword prefix; no global timing parity claim.',
            'No whole campaign playthrough or complete-port claim.'])
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()
