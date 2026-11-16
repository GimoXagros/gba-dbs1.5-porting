"""Capture-free independent cache repair and actual Thumb header-consumer gate."""
import argparse,hashlib,json,struct,types
from pathlib import Path
from verify_shoot_attack_dispatch import Machine
import verify_shoot_caller_resident as scanner
ROOT=Path(__file__).resolve().parents[1]
INPUT='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
OUTPUT='C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
MANIFEST='32A7942A7945B12EF191995B908DC8844C1935DA33340B0484700E4813203B8B'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
    if not v:raise ValueError(s)
def branch(a,b,c=14):return struct.pack('<I',(c<<28)|0x0A000000|(((b-a-8)//4)&0xFFFFFF))
def thumb(rom,entry,sid,active):
    """Decode only actual executed Thumb instructions; MPlay call is boundary."""
    regs=[0]*16;regs[0]=sid;regs[13]=0x03007D00;regs[14]=0x09000001;pc=entry;mem={};calls=[];z=False;steps=0
    def read(a,n=4):
        if 0x08000000<=a<0x09000000:return int.from_bytes(rom[a-0x08000000:a-0x08000000+n],'little')
        return sum(mem.get(a+i,0)<<(8*i) for i in range(n))
    def put(a,v):
        for i in range(4):mem[a+i]=(v>>(8*i))&255
    row=0xD33000+sid*8;player=struct.unpack_from('<H',rom,row+4)[0]
    playerptr=read(0x0837FBB4+12*player);need(0x02000000<=playerptr<0x04000000,'actual player pointer');put(playerptr,active)
    while pc!=0x09000000:
        steps+=1;need(steps<60,'bounded Thumb consumer');op=read(pc,2);at=pc;pc+=2
        if op==0xB500:regs[13]-=4;put(regs[13],regs[14])
        elif op==0xBC01:regs[0]=read(regs[13]);regs[13]+=4
        elif op==0x4700:pc=regs[0]&~1
        elif op&0xF800 in (0,0x0800):
            rd=op&7;rs=(op>>3)&7;n=(op>>6)&31;regs[rd]=((regs[rs]<<n)&0xffffffff) if op&0xF800==0 else regs[rs]>>(n or 32)
        elif op&0xF800==0x4800:regs[(op>>8)&7]=read(((at+4)&~3)+(op&255)*4)
        elif op&0xFE00==0x1800:regs[op&7]=(regs[(op>>3)&7]+regs[(op>>6)&7])&0xffffffff
        elif op&0xFE00==0x1C00:regs[op&7]=(regs[(op>>3)&7]+((op>>6)&7))&0xffffffff
        elif op&0xF800==0x6800:regs[op&7]=read(regs[(op>>3)&7]+((op>>6)&31)*4)
        elif op&0xF800==0x8800:regs[op&7]=read(regs[(op>>3)&7]+((op>>6)&31)*2,2)
        elif op&0xFFC0==0x4280:z=regs[op&7]==regs[(op>>3)&7]
        elif op&0xFF00==0xD100:
            if not z:pc=at+4+struct.unpack('b',bytes([op&255]))[0]*2
        elif op&0xF800==0xF000:
            second=read(pc,2);need(second&0xF800==0xF800,'Thumb BL suffix');hi=op&0x7ff;hi=hi-0x800 if hi&0x400 else hi;target=at+4+(hi<<12)+((second&0x7ff)<<1)
            need(target in (0x0837C9C8,0x0837C1A8),'actual MPlay stop/resume target');calls.append((target,regs[0]));regs[14]=(pc+2)|1;pc+=2
        else:raise ValueError(f'Unsupported actual Thumb {at:08X}:{op:04X}')
    need(regs[13]==0x03007D00,'Thumb stack balanced');return calls,playerptr
def arm(rom,sid,flags=0):
    m=Machine(rom,seed=31,flags=(flags<<28)|0x1F);m.r[8]=sid;m.r[13]=0x03007E00;m.r[14]=0x09000000;m.put(0x03004E98,15);calls=[]
    m.services={0x0837DB78:lambda c:calls.append(('play',c.r[0])),0x0837DB84:lambda c:calls.append(('stop',None))};m.run(0x0837B44C,{0x09000000});return m,calls
def verify(before,after,manifest):
    need((sha(before),sha(after),sha(manifest))==(INPUT,OUTPUT,MANIFEST),'frozen inputs')
    need(sha((ROOT/'tools/build_evolution_music_pause_cache.py').read_bytes())=='7488DE49EC398BF0C1AD7FBFB4AA04A2EBB133ECBE17DC6227A6BE3123F03810','builder pin')
    need(sha(Path(scanner.__file__).read_bytes())=='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D','scanner pin')
    need(before[0xD7DFC0:0xD7E000]==b'\xff'*64,'owned erased64B')
    scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((0xD7DFC0,0xD7DFD4),)),argdefs=scanner.inbound.__defaults__);need(not scan(before),'full predecessor inbound zero')
    stub=struct.pack('<I',0xE358006C)+branch(0xD7DFC4,0x37B464,3)+struct.pack('<I',0xE3580070)+branch(0xD7DFCC,0x37B464,2)+branch(0xD7DFD0,0x37B45C)
    expected=bytearray(before);expected[0x37B458:0x37B45C]=branch(0x37B458,0xD7DFC0,5);expected[0xD7DFC0:0xD7DFD4]=stub;need(expected==after,'whole two-span independent reconstruction')
    m=json.loads(manifest);inverse=bytearray(after)
    need([(x['offset'],x['size']) for x in m['writes']]==[(0x37B458,4),(0xD7DFC0,20)],'exact manifest spans')
    for w in m['writes']:
        a=w['offset'];n=w['size'];need(bytes.fromhex(w['before_hex'])==before[a:a+n] and bytes.fromhex(w['after_hex'])==after[a:a+n],'manifest bytes');inverse[a:a+n]=bytes.fromhex(w['before_hex'])
    need(inverse==before and sum(a!=b for a,b in zip(before,after))==23,'whole inverse23changed')
    ids=list(range(0x80))+[0xFFFF,0x10000,0x7FFFFFFF,0x80000000,0x8000001D,0x8000001E,0xFFFFFFFF];armcases=0
    for sid in ids:
        for flags in (0,5,10,15):
            old,c0=arm(before,sid,flags);new,c1=arm(after,sid,flags);added=0x6C<=sid<0x70
            need(c0==c1 and new.get(0x03004E98)==(sid if added else old.get(0x03004E98)),'only four cache additions')
            need([x for x in new.writes if x[0]!=0x03004E98]==[x for x in old.writes if x[0]!=0x03004E98],'noncache effects identical')
            need(all(new.r[i]==old.r[i] for i in range(15) if not(added and i==9)),'ARM ABI retained');armcases+=2
    routes=[]
    stale=struct.unpack_from('<I',after,0xD33000+15*8)[0]
    for sid in range(108,112):
        active=struct.unpack_from('<I',after,0xD33000+sid*8)[0];need(active!=stale,'distinct stale header')
        for entry,bridge,te,target,label in ((0x0837B48C,0x0837DB90,0x0837C348,0x0837C9C8,'pause'),(0x0837B4A8,0x0837DB9C,0x0837C37C,0x0837C1A8,'resume')):
            machine,_=arm(after,sid);machine.r[14]=0x09000000;passed=[];machine.services={bridge:lambda c:passed.append(c.r[0])};machine.run(entry,{0x09000000});need(passed==[sid],'actual ARM cached ID consumption')
            for cached,header,accept in ((sid,active,True),(15,active,False),(sid,stale,False),(sid,0,False)):
                calls,player=thumb(after,te,cached,header);need(calls==([(target,player)] if accept else []),'actual Thumb equality/negative header branch');routes.append(dict(song=sid,route=label,cached=cached,active_header=header,called=bool(calls)))
    return dict(status='PASS',input_sha256=INPUT,output_sha256=OUTPUT,manifest_sha256=MANIFEST,verifier_sha256=sha(Path(__file__).read_bytes()),declared_bytes=24,changed_bytes=23,whole_inverse=True,conservative_inbound_hits=[],actual_ARM_cases=armcases,actual_Thumb_header_cases=len(routes),header_cases=routes,scope='Actual ARM cache/pause/resume and decoded Thumb table/player/header equality through real MPlay call targets; downstream MPlay implementation is an explicit boundary.',runtime_verified=False,emulator_executed=False)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('before','after','manifest','report'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();need(len({getattr(a,n).resolve() for n in ('before','after','manifest','report')})==4 and not a.report.exists(),'fresh nonalias report');r=verify(a.before.read_bytes(),a.after.read_bytes(),a.manifest.read_bytes());a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode());print(sha(a.report.read_bytes()))
if __name__=='__main__':main()
