"""Complete the extended campaign's progress-indexed AI tables and round label.

Consumes the frozen producer component; uses no new RAM and no emulator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine as PriorMachine
import verify_shoot_caller_resident as scanner

BASE=0x08000000
INPUT='ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST,LIMIT=0xD3FEE0,0xD40000
BYTE_TABLES=FIRST
HALF_TABLES=FIRST+108
INITIAL_TABLE=FIRST+180
HUD=0xD3FFA4
INITIAL_HELPER=0xD3FFDC
SOURCE_BASE=0x782970
SOURCE_ROWS=(0xB9,0xC5,0xD1,0xE3,0xEF,0xFB,0x10D,0x119,0x125,0x137,0x14F,0x167)
SCANNER='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def need(ok,label):
    if not ok:raise ValueError(label)


def sha(b):return hashlib.sha256(b).hexdigest().upper()
def word(b,at):return struct.unpack_from('<I',b,at)[0]
def asm(text,at):return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(text,BASE+at)[0])


class Machine(PriorMachine):
    """Add only the two actual retained halfword forms used by these paths."""
    def run(self,start,stops,max_steps=16000):
        for _ in range(128):
            try:return super().run(start,stops,max_steps)
            except ValueError as error:
                if str(error)!='immediate halfword transfer':raise
                pc=self.r[15]-8;instruction=self.get(pc)
                if instruction==0xE19500F0:  # LDRSH r0,[r5,r0]
                    value=self.get((self.r[5]+self.r[0])&0xFFFFFFFF,2)
                    self.r[0]=(value if value<0x8000 else value-0x10000)&0xFFFFFFFF
                elif instruction==0xE0C500B2:  # STRH r0,[r5],#2
                    self.put(self.r[5],self.r[0],2,True)
                    self.r[5]=(self.r[5]+2)&0xFFFFFFFF
                else:raise ValueError('unreviewed halfword form '+hex(instruction))
                start=pc+4
        raise ValueError('bounded halfword extension exhausted')


def contract(source,before):
    pointers=[]
    for off in (0xDD,0x107,0x131,0x17F):
        pointers.extend(struct.unpack_from('<3H',source,SOURCE_BASE+off))
    need(tuple(pointers)==SOURCE_ROWS,'source three rows per family')
    rows=[];retained_bytes=0;retained_scaled=0
    for i,off in enumerate(SOURCE_ROWS):
        old=word(before,0xC7048+i*4)-BASE
        if i<9:
            values=list(source[SOURCE_BASE+off:SOURCE_BASE+off+12])
            need(before[old:old+9]==bytes(values[:9]),'nine retained native byte values')
            converted=values;retained_bytes+=9
        else:
            values=list(struct.unpack_from('<12H',source,SOURCE_BASE+off))
            converted=[v*4//5 for v in values]
            need(list(struct.unpack_from('<9H',before,old))==converted[:9], 'nine retained exact floor4/5 native halfwords')
            retained_scaled+=9
        rows.append(dict(source=SOURCE_BASE+off,old_native=old,width=1 if i<9 else 2,source_values=values,values=converted))
    initial=list(source[SOURCE_BASE+0x185:SOURCE_BASE+0x192])
    need(initial==[7,7,6,6,5,5,4,4,3,3,3,3,3],'complete source initial progress table')
    need(before[0xC7078:0xC7082]==bytes(initial[:10]),'ten retained initial progress entries')
    # Every source lookup explicitly loads game config+1E, not physical stage+0E.
    for at in (0x782C34,0x782C93,0x782CBB,0x782CDF,0x782D08):
        need(source[at:at+3]==bytes.fromhex('8a451e'),'source progress-indexed AI lookup')
    need(word(before,0xC824C)==0xE5D8001E and word(before,0xC8254)==0x03002310,'native progress getter owner')
    need(source[0x77E389:0x77E396].hex()=='3d0a007438b10a32e4fec0f6f1','source final10/decimal round numbering')
    need(word(before,0xB5FB4)==0xE3500007,'prior final7 round label')
    need(list(struct.unpack_from('<5H',before,0xB5FEA))==[0x221E,0x221F,0x2213,0x2205,0x2204],'retained final label tiles')
    return dict(rows=rows,initial=initial,retained_byte_witnesses=retained_bytes,
                retained_scaled_halfword_witnesses=retained_scaled,
                units='Only fourth AI family uses existing commercial floor(source*4/5); all27 old values agree.',
                source_windows=[dict(start=a,end=z,sha256=sha(source[a:z])) for a,z in
                    ((0x782A29,0x782B02),(0x782C26,0x782D2E),(0x77E378,0x77E3D4))])


def ownership(before,paths):
    pins=('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
          '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
          '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD',
          '54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55')
    blobs=[p.read_bytes() for p in paths]
    need(tuple(map(sha,blobs))==pins,'all four frozen owners')
    owners=list(map(json.loads,blobs))
    need([0xD33000,0xD40000] in owners[0]['reservations'],'enclosing owner')
    need(owners[3]['output_sha256']==INPUT and owners[3]['allocation']['suballocation']==[0xD3FB10,0xD3FB80],'immediate producer owner')
    for n,owner in enumerate(owners):
        for w in owner['writes']:
            a,z=w['offset'],w['offset']+w['size']
            need(not max(a,FIRST)<min(z,LIMIT),'all prior writes disjoint')
            if n==0:
                if 0xD33000<=a<0xD40000:need(sha(before[a:z])==w['after_sha256'],'audio preserved')
            else:need(before[a:z]==bytes.fromhex(w['after_hex']),'previous components preserved')
    need(before[FIRST:LIMIT]==b'\xff'*(LIMIT-FIRST),'entire residual suballocation blank')
    need(sha(Path(scanner.__file__).read_bytes())==SCANNER,'pinned reference scanner')
    scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
    hits=scan(before);need(not hits,'zero encoded incoming references; no mode exceptions')
    return dict(enclosing=[0xD33000,0xD40000],suballocation=[FIRST,LIMIT],prior_manifest_sha256=pins,inbound_hits=hits,new_RAM_bytes=0)


def build(before,proof):
    after,writes=bytearray(before),[]
    def put(at,blob,label):
        need(not any(max(at,w['offset'])<min(at+len(blob),w['offset']+w['size']) for w in writes),'disjoint writes')
        writes.append(dict(offset=at,size=len(blob),label=label,before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex()))
        after[at:at+len(blob)]=blob
    for i,row in enumerate(proof['rows']):
        at=BYTE_TABLES+i*12 if i<9 else HALF_TABLES+(i-9)*24
        blob=struct.pack('<12'+('B' if i<9 else 'H'),*row['values'])
        row['new_native']=BASE+at
        put(at,blob,'full AI progress row '+str(i))
        put(0xC7048+4*i,struct.pack('<I',BASE+at),'AI row pointer '+str(i))
    put(INITIAL_TABLE,bytes(proof['initial']),'source initial AI progress table')
    need(word(before,0xC6EEC)==0xE28F8F61,'original initial AI table ADR')
    put(0xC6EEC,asm(f'b 0x{BASE+INITIAL_HELPER:X}',0xC6EEC),'initial AI table redirect')
    initial=asm(f'ldr r8, table\nb 0x080C6EF0\ntable: .word 0x{BASE+INITIAL_TABLE:X}',INITIAL_HELPER)
    need(len(initial)==12,'bounded initial table adapter')
    put(INITIAL_HELPER,initial,'initial AI table adapter')
    hud=asm('''cmp r0,#10
      beq 0x080B6044
      cmp r0,#9
      bne 0x080B5FBC
      ldr r0, digit_one
      strh r0,[r5],#2
      sub r0,r0,#1
      strh r0,[r5],#2
      ldr r0, blank
      mov r2,#7
      b 0x080B5FD4
    digit_one: .word 0x2215
    blank: .word 0x2201
    ''',HUD)
    need(len(hud)==52 and HUD+len(hud)<=INITIAL_HELPER,'bounded HUD adapter')
    put(HUD,hud,'source final10 and two-digit round10')
    put(0xB5FB4,asm(f'b 0x{BASE+HUD:X}',0xB5FB4),'round label consumer hook')
    inverse=bytearray(after)
    for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
    need(inverse==before,'whole image inverse')
    return bytes(after),writes


def ai_case(rom,proof,progress,row):
    m=Machine(rom,seed=3);m.put(0x0300232E,progress,1);m.r[5]=row*4
    m.put(0x03004D8E,0x8E,1);m.put(0x03004DCA,0x1234,2);m.put(0x03004DCC,0x5678,2);m.put(0x03004DAA,0x2345,2)
    sp=m.r[13];m.run(0x080C6F6C,{0x080C7020})
    rows=proof['rows']
    need(m.get(0x03004D8E,1)==((0x8E+rows[row]['values'][progress])&15),'AI first byte addition/mask')
    need(m.get(0x03004DCA,2)==(0x1234+rows[3+row]['values'][progress])&65535,'AI second halfword addition')
    need(m.get(0x03004DCC,2)==rows[6+row]['values'][progress]&127,'AI third mask')
    need(m.get(0x03004DAA,2)==(0x2345+rows[9+row]['values'][progress])&65535,'AI fourth scaled addition')
    need(m.r[13]==sp,'AI balanced stack')
    need(m.get(0x0300232E,1)==progress,'AI preserves progress')


def initial_case(rom,proof,progress):
    m=Machine(rom,seed=4);m.put(0x0300232E,progress,1)
    r0,r5,sp=m.r[0],m.r[5],m.r[13]
    m.run(0x080C6EE0,{0x080C6F04})
    need(m.get(0x03003D72,2)==proof['initial'][progress],'initial progress table')
    need((m.r[0],m.r[5],m.r[13])==(r0,r5,sp),'initial table stack/register ownership')


def hud_case(rom,progress):
    m=Machine(rom,seed=5);m.r[0]=progress;m.r[5]=0x0600E80E
    for i in range(16):m.put(0x0600E800+i*2,0xA000+i,2)
    sp=m.r[13]
    end=m.run(0x080B5FB4,{0x080B6050,0x080B6054})
    if progress==10:
        need(end==0x080B6050 and m.r[4]==0x080B5FEA and m.r[5]==0x0600E800 and m.r[2]==16,'retained final DMA copy setup')
    else:
        expected=[0x2215+progress]+[0x2201]*8 if progress<9 else [0x2215,0x2214]+[0x2201]*7
        need(end==0x080B6054 and [m.get(0x0600E80E+i*2,2) for i in range(9)]==expected,'decimal round and exact nine-cell tail')
        need([m.get(0x0600E800+i*2,2) for i in range(7)]==[0xA000+i for i in range(7)],'prefix preserved')
        need(m.r[5]==0x0600E820,'same full-row write extent')
    need(m.r[13]==sp,'HUD preserves stack')


def checks(after,before,proof):
    for p in range(12):
        for row in range(3):ai_case(after,proof,p,row)
    for p in range(13):initial_case(after,proof,p)
    for p in range(11):hud_case(after,p)
    mutations=[]
    def reject(at,blob,fn,label):
        wrong=bytearray(after);wrong[at:at+len(blob)]=blob
        try:fn(bytes(wrong))
        except (ValueError,AssertionError):mutations.append(label)
        else:raise ValueError('accepted mutation '+label)
    for n in range(4):
        site=0xC7048+12*n
        progress=9 if n==2 else 10
        reject(site,before[site:site+4],lambda r:ai_case(r,proof,progress,0),'old short AI row family'+str(n))
    reject(INITIAL_TABLE+10,b'\x06',lambda r:initial_case(r,proof,10),'short initial table fallthrough')
    reject(HALF_TABLES+20,struct.pack('<H',148),lambda r:ai_case(r,proof,10,0),'unscaled new AI halfword')
    reject(HUD,asm('cmp r0,#7',HUD),lambda r:hud_case(r,7),'retail final7 label')
    reject(HUD+36,asm('mov r2,#8',HUD+36),lambda r:hud_case(r,9),'two-digit fill overrun')
    return dict(AI_row_cases=36,initial_AI_cases=13,HUD_cases=11,negative_controls=mutations)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    keys=('before','source','audio_manifest','table_manifest','id13_manifest','campaign_manifest','output','manifest')
    for key in keys:ap.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    a=ap.parse_args();need(not a.output.exists() and not a.manifest.exists(),'fresh outputs')
    need(len({getattr(a,k).resolve() for k in keys})==len(keys),'distinct paths')
    before,source=a.before.read_bytes(),a.source.read_bytes()
    need((sha(before),sha(source))==(INPUT,SOURCE),'frozen producer/source inputs')
    proof=contract(source,before)
    owned=ownership(before,[a.audio_manifest,a.table_manifest,a.id13_manifest,a.campaign_manifest])
    after,writes=build(before,proof);tested=checks(after,before,proof)
    report=dict(status='CAMPAIGN_PROGRESS_CONSUMERS_AUTHORED',input_sha256=INPUT,output_sha256=sha(after),
        builder_sha256=sha(Path(__file__).read_bytes()),source=proof,allocation=owned,writes=writes,
        whole_inverse=True,ARM=tested,changed_bytes=sum(x!=y for x,y in zip(before,after)),runtime_verified=False,
        limits=['Completes progress-indexed AI and round label for the earlier clean1.5 producer component.',
                'Final label test stops at retained DMA-copy call with exact arguments; no graphical runtime claim.',
                'No new alternate-mode owner, RAM, progression clamp, or gameplay input.'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],report['output_sha256'])


if __name__=='__main__':main()
