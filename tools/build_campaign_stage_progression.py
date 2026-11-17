"""Source-backed ordinary campaign producer; clean Ver.1.5 mode only.

No new RAM, no emulator, no guessed progress or mode flags. All mutable state
continues to use the existing native campaign owner.
"""
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
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
INPUT = 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
FIRST, LIMIT = 0xD3FB10, 0xD3FB80
EARLY, ROWS, CPU, DISPATCH = FIRST, FIRST+8, FIRST+0x30, FIRST+0x40
CONFIG, SCENE, STOP = 0x03002310, 0x03004738, 0x08001234
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(b): return hashlib.sha256(b).hexdigest().upper()
def word(b, at): return struct.unpack_from('<I', b, at)[0]
def asm(s, at): return bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(s, BASE+at)[0])


def source_contract(source, before):
    need(source[0x778674:0x778679] == bytes([8, 1, 9, 6, 10]), 'source early five')
    need(source[0x778679:0x7786A1] == bytes([
        5,0,3,2,4, 0,3,2,4,5, 3,2,4,5,0, 2,4,5,0,3,
        4,5,0,3,2, 5,0,3,2,4, 0,3,2,4,5, 2,4,5,0,3]), 'source eight rows')
    need(source[0x7786A1:0x7786AC] == bytes([0,1,2,5,6,4,3,15,13,14,11]), 'source CPU map')
    dispatch = [0x776F10+x for x in struct.unpack_from('<11H', source, 0x7786AC)]
    need(dispatch == [0x7786F9]*5+[0x778703]*5+[0x77871D], 'source eleven progress arms')
    need(source[0x778703:0x77871A].hex() == '33db8a5c1f5303db03db2d050003d85803d82e8a9f6917', 'source five-stride row expression')
    need(source[0x778725:0x778731].hex() == '885c0ef64425017403e8b4fe', 'actual stage write and conditional legacy scheduler')
    need(source[0x78070F:0x78071D].hex() == '33c02688450e2688451e2688451f', 'source zero stage/progress/row')
    need(source[0x78074F:0x78075B].hex() == '9ab51cff4f2507002688451f', 'source retained random row')
    need(source[0x777AEB:0x777AF4].hex() == '26fe441e9ab217f176', 'source successor increments then calls producer')
    need(source[0x7786E8:0x7786F9].hex() == '81641aefff814c1a200033dbb00be93f00', 'source dedicated challenge keeps stage')
    need(source[0x777049:0x777055].hex() == '807d0e0b7406807d0e07751f', 'source terminal stage11 or7 predicates')
    need(source[0x747A95:0x747A9F].hex() == '26c6450e0b9ac40fcf7c', 'dedicated source stage11 initializer')
    need(word(before, 0x9114C) == 0xE5C4001E and word(before, 0x911A0) == 0xE5C4001F, 'existing native progress/row producers')
    need(before[0x8A6F4:0x8A704].hex() == '1e80d4e5018098e21e80c4e5cc0300eb', 'existing native unbounded successor')
    need(before[0x8B60F:0x8B617] == source[0x7786A1:0x7786A9], 'retained eight native CPU identities include boss15')
    return dict(first=list(source[0x778674:0x778679]),
                rows=[list(source[a:a+5]) for a in range(0x778679,0x7786A1,5)],
                cpu=list(source[0x7786A1:0x7786AC]),
                progress_owner='0300232E', row_owner='0300232F (RNG & 7, not difficulty)',
                stage_owner='0300231E', mode_scope='source config+25 bit1 clear; no fabricated native flag',
                source_windows=[dict(start=a,end=z,sha256=sha(source[a:z])) for a,z in
                    ((0x778674,0x778750),(0x777AA3,0x777B47),(0x780707,0x78075B),(0x777049,0x777074),(0x747A68,0x747AC7))])


def ownership(before, audio_bytes, table_bytes, id13_bytes):
    pins = ('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
            '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
            '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD')
    need(tuple(map(sha,(audio_bytes,table_bytes,id13_bytes))) == pins, 'frozen reservation manifests')
    audio,tables,id13 = map(json.loads,(audio_bytes,table_bytes,id13_bytes))
    need([0xD33000,0xD40000] in audio['reservations'], 'enclosing audio reservation')
    need(id13['output_sha256'] == INPUT and id13['allocation']['suballocation'] == [0xD3F100,0xD3FA00], 'immediately preceding ID13 owner')
    for owner in (audio,tables,id13):
        for w in owner['writes']:
            a,z = w['offset'],w['offset']+w['size']
            need(not (max(a,FIRST)<min(z,LIMIT)), 'no prior owner write intersects allocation')
            if owner is audio:
                if 0xD33000 <= a < 0xD40000:
                    need(sha(before[a:z]) == w['after_sha256'], 'retained audio contents')
            else:
                need(before[a:z] == bytes.fromhex(w['after_hex']), 'retained table/ID13 contents')
    need(before[FIRST:LIMIT] == b'\xff'*(LIMIT-FIRST), 'entire authorized suballocation blank')
    need(sha(Path(scanner.__file__).read_bytes()) == SCANNER, 'frozen conservative scanner')
    scan = types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((FIRST,LIMIT),)),argdefs=scanner.inbound.__defaults__)
    hits = scan(before); need(not hits, 'no incoming encoded references into prospective allocation')
    return dict(enclosing=[0xD33000,0xD40000],suballocation=[FIRST,LIMIT],manifest_sha256=pins,inbound_hits=hits,scanner_sha256=SCANNER,new_RAM_bytes=0)


def make(before, source):
    after,writes = bytearray(before),[]
    def put(at,blob,label):
        need(not any(max(at,w['offset'])<min(at+len(blob),w['offset']+w['size']) for w in writes), 'disjoint new writes')
        writes.append(dict(offset=at,size=len(blob),label=label,before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex()))
        after[at:at+len(blob)] = blob
    for at,start,end,label in ((EARLY,0x778674,0x778679,'opening five stages'),(ROWS,0x778679,0x7786A1,'eight five-stage rows'),(CPU,0x7786A1,0x7786AC,'eleven stage CPU identities')):
        put(at,source[start:end],label)
    put(DISPATCH,struct.pack('<11I',*([0x0808B698]*5+[0x0808B6A8]*5+[0x0808B6C8])),'eleven progress dispatch entries')
    for site,old,target in ((0x8B718,0x0808B618,DISPATCH),(0x8B71C,0x0808B5EC,EARLY),(0x8B720,0x0808B5EF,ROWS),(0x8B724,0x0808B60F,CPU)):
        need(word(before,site)==old,'prior campaign table pointer')
        put(site,struct.pack('<I',BASE+target),'campaign table pointer')
    for site,expected,text,label in (
        (0x8B6AC,0xE0911001,'adds r1,r1,r1,lsl #2','five-stride row'),
        (0x8B6B0,0xE0911001,'mov r1,r1','retain computed five-stride row'),
        (0x8B6B4,0xE2500003,'subs r0,r0,#5','five opening stages'),
        (0x8B6D8,0xEBFFFF82,'mov r0,r0','clean1.5 skips legacy challenge scheduler'),
        (0x582C44,0xE5D8000A,'b 0x08582C6C','actual getter bypasses character override'),
        (0x584A04,0xE5D8000A,'b 0x08584A2C','legacy getter uses actual stage before analog map')):
        need(word(before,site)==expected,'prior instruction '+label)
        put(site,asm(text,site),label)
    inverse=bytearray(after)
    for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
    need(inverse==before,'whole-image inverse')
    return bytes(after),writes


def campaign_case(rom,first,rows,cpu,progress,row,player,color,flags=0,alias=False,stage=6):
    m=Machine(rom,seed=7,flags=0xA0000010)
    scene=CONFIG if alias else SCENE
    m.r[5]=scene;m.r[14]=STOP
    for a in range(CONFIG,CONFIG+0x26):m.put(a,0,1)
    for off,val in ((0xA,player),(0xB,color),(0xC,0xA5),(0xD,0x5A),(0xE,stage),(0x1E,progress),(0x1F,row)):
        m.put(CONFIG+off,val,1)
    m.put(CONFIG+0x1A,flags,2)
    if not alias:m.put(scene+0x1A,0xA55A,2)
    original=m.r[:]; beforemem=m.mem.copy()
    effective=flags&~0x10 if alias else flags
    if effective&0x10:
        wanted_stage=stage; wanted_cpu=11;wanted_flags=(effective&~0x10)|0x20
    else:
        wanted_stage=first[progress] if progress<5 else rows[row][progress-5] if progress<10 else 7
        wanted_cpu=cpu[wanted_stage];wanted_flags=effective
    m.run(0x0808B638,{STOP})
    need(m.get(CONFIG+0xE,1)==wanted_stage,'campaign stage')
    need(m.get(CONFIG+0xC,1)==wanted_cpu,'campaign CPU')
    need(m.get(CONFIG+0xD,1)==(color^1 if player==wanted_cpu else 0),'same-character CPU palette')
    need(m.get(CONFIG+0x1A,2)==wanted_flags,'run flags and legacy scheduler exclusion')
    if not alias:need(m.get(scene+0x1A,2)==0xA54A,'displaced scene flag clear')
    need(m.r[:8]==original[:8] and m.r[10:15]==original[10:15],'native preserved registers/SP/LR')
    allowed={CONFIG+0xC,CONFIG+0xD,CONFIG+0xE,CONFIG+0x1A,CONFIG+0x1B,scene+0x1A,scene+0x1B}
    for a in set(beforemem)|set(m.mem):
        if beforemem.get(a,0)!=m.mem.get(a,0):
            need(a in allowed or original[13]-16<=a<original[13],'no unrelated persistent write')
    need(not m.calls,'no RNG or legacy scheduler calls')


def getter_case(rom,stage,player,legacy):
    m=Machine(rom,seed=2);m.r[14]=STOP
    m.put(CONFIG+0xE,stage,1);m.put(CONFIG+0xA,player,1)
    original=m.r[:];sp=m.r[13];mem=m.mem.copy()
    m.run(0x08584A00 if legacy else 0x080D1C78,{STOP})
    want={8:0,9:6,10:3,11:7}.get(stage,stage) if legacy else stage
    need(m.r[0]==want,'actual-stage getter/legacy analog')
    need(m.r[1:8]==original[1:8] and m.r[9:15]==original[9:15] and m.r[13]==sp,'getter ABI')
    need(m.mem==mem,'read-only getter')


def checks(after,before,proof):
    first,rows,cpu=proof['first'],proof['rows'],proof['cpu']
    count=0
    for progress,row,player,color in itertools.product(range(11),range(8),range(16),range(2)):
        flags=(0,1,0x40,0x8000)[(progress+row+player+color)%4]
        campaign_case(after,first,rows,cpu,progress,row,player,color,flags);count+=1
    for flags,alias,stage,player in itertools.product((0x10,0x50,0xFFFF),(False,True),(0,8,9,10,11),(0,11)):
        campaign_case(after,first,rows,cpu,10,7,player,1,flags,alias,stage);count+=1
    getters=0
    for stage,player,legacy in itertools.product(range(256),range(16),(False,True)):
        getter_case(after,stage,player,legacy);getters+=1
    # Each mutation crosses a real source boundary and must fail actual ARM.
    mutations=[]
    def reject(at,blob,check,label):
        wrong=bytearray(after);wrong[at:at+len(blob)]=blob
        try:check(bytes(wrong))
        except (ValueError,AssertionError):mutations.append(label)
        else:raise ValueError('accepted mutation '+label)
    case=lambda r:campaign_case(r,first,rows,cpu,5,1,0,0)
    reject(0x8B6AC,asm('adds r1,r1,r1,lsl #1',0x8B6AC),case,'wrong row stride')
    reject(0x8B6B4,before[0x8B6B4:0x8B6B8],case,'old first-row threshold')
    reject(DISPATCH+12,struct.pack('<I',0x0808B6A8),lambda r:campaign_case(r,first,rows,cpu,3,0,0,0),'early/row boundary')
    reject(0x8B724,before[0x8B724:0x8B728],lambda r:campaign_case(r,first,rows,cpu,0,0,0,0),'retail short CPU table')
    reject(0x8B6D8,before[0x8B6D8:0x8B6DC],lambda r:campaign_case(r,first,rows,cpu,4,0,0,0),'unconditional legacy challenge')
    reject(0x582C44,before[0x582C44:0x582C48],lambda r:getter_case(r,9,13,False),'public character override')
    reject(0x584A04,before[0x584A04:0x584A08],lambda r:getter_case(r,9,13,True),'legacy character override')
    return dict(campaign_cases=count,getter_cases=getters,negative_controls=mutations)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ('before','source','audio_manifest','table_manifest','id13_manifest','output','manifest'):
        ap.add_argument('--'+key.replace('_','-'),type=Path,required=True)
    a=ap.parse_args()
    need(not a.output.exists() and not a.manifest.exists(),'fresh output files')
    paths=[getattr(a,k).resolve() for k in ('before','source','audio_manifest','table_manifest','id13_manifest','output','manifest')]
    need(len(set(paths))==len(paths),'nonalias inputs/outputs')
    before,source=a.before.read_bytes(),a.source.read_bytes()
    need((sha(before),sha(source))==(INPUT,SOURCE),'exact predecessor and source')
    proof=source_contract(source,before)
    owned=ownership(before,a.audio_manifest.read_bytes(),a.table_manifest.read_bytes(),a.id13_manifest.read_bytes())
    after,writes=make(before,source)
    execution=checks(after,before,proof)
    report=dict(status='CAMPAIGN_PRODUCER_AUTHORED',input_sha256=INPUT,output_sha256=sha(after),
        builder_sha256=sha(Path(__file__).read_bytes()),source=proof,allocation=owned,writes=writes,
        whole_inverse=True,ARM=execution,changed_bytes=sum(x!=y for x,y in zip(before,after)),
        runtime_verified=False,consumer_review_required=True,
        limits=['Clean config+25 bit1-clear Ver.1.5 scope; native alternate-mode owner is not invented.',
                'No clamp or fallback for invalid progress>=11 or row>=8; actual existing producers define the input domain.',
                'Dedicated stage11 initializer/guards and flag10 branch remain unchanged; complete playthrough is separate.'])
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],report['output_sha256'])


if __name__=='__main__':main()
