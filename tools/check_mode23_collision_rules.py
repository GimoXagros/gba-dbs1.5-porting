"""Author checks of collision ARM and source-derived arithmetic/scene effects.

External task/pickup/sound helpers are explicit fixtures, not native execution.
"""
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine as Parent
from mode23_collision_rules import assembly, DEPENDENCIES

BASE=0x08000000
CTX=0x02010018
ACTORS=[0x02010478+i*0x118 for i in range(6)]
AUX=0x02010360

def s16(x): return (x & 32767)-(x & 32768)
def sha(x): return hashlib.sha256(x).hexdigest().upper()

def sqrt16(n):
    assert 0<n<65536
    old=n
    for k in range(1,41):
        new=((n//old+old)&65535)>>1
        delta=s16(new-old)
        delta=s16(-delta if delta<0 else delta)
        old=new
        if k>=40:return 65534
        if delta<=2:return new
    raise AssertionError

def atan16(y,x):
    y,x=s16(y),s16(x)
    def ratio(a,b):
        a,b=a&65535,b&65535
        if a<0x4000:a=(a*2)&65535
        else:b>>=1
        if not b:raise ZeroDivisionError('source atan denominator zero')
        return (6+a*13//b) if a>b else a*19//b
    def quarter(a,b):
        return 64-ratio(b,a) if s16(a)>s16(b) else ratio(a,b)
    if y>=0:
        v=quarter(s16(-x),y)+64 if x<0 else quarter(y,x)
    else:
        v=quarter(s16(-y),s16(-x))+128 if x<0 else quarter(x,s16(-y))-64
    return s16(v)

class Machine(Parent):
    def execute(self, start, positions, limit=150000):
        end=self.r[14];pc=start
        for step in range(limit):
            if pc==end:return step
            if pc in self.services:
                self.services[pc](self);pc=self.r[14];continue
            assert pc in positions, hex(pc)
            w=self.get(pc);cond=self.condition(w>>28)
            if not cond:pc+=4;continue
            if w&0x0FC000F0==0x00000090:
                rd,rm,rs=(w>>16)&15,w&15,(w>>8)&15
                assert not w&0x00300000 and rd!=rm and 15 not in (rd,rm,rs)
                self.r[rd]=(self.r[rm]*self.r[rs])&0xffffffff;pc+=4
            elif w&0x0FFFFFF0==0x019100F0:
                self.r[0]=s16(self.get(self.r[1]+self.r[w&15],2))&0xffffffff;pc+=4
            elif w&0x0FE00000==0x00A00000:
                assert not w&0x100000
                self.r[(w>>12)&15]=(self.r[(w>>16)&15]+self.shifted(w)+((self.cpsr>>29)&1))&0xffffffff
                pc+=4
            else:
                # Parent deliberately retains logical C; actual MOVS shift
                # supplies its shifter carry to the following ADC in udiv.
                carry=None
                if w&0x0FF00000==0x01B00000 and not w&0x02000000:
                    count=(w>>7)&31;kind=(w>>5)&3;v=self.r[w&15]
                    if count and kind==0:carry=(v>>(32-count))&1
                    if count and kind==1:carry=(v>>(count-1))&1
                pc=super().run(pc,(positions-{pc})|{end},2)
                if carry is not None:self.cpsr=(self.cpsr&~0x20000000)|(carry<<29)
        raise AssertionError('collision execution limit')

def link(source):
    names=['m23_src_BF42','m23_bf42_sqrt','m23_bf42_atan','m23_bf42_udiv','m23_bf42_sin','m23_bf42_cos']+list(DEPENDENCIES)
    src='\n'.join('.word '+n for n in names)+'\n'+assembly(source)+'\n'.join(n+': bx lr' for n in DEPENDENCIES)
    data=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(src,BASE)[0])
    return data,dict(zip(names,struct.unpack_from('<'+'I'*len(names),data))),set(range(BASE+len(names)*4,BASE+len(data),4))

def model(actors, aux, flags, table):
    a=[dict(x) for x in actors];events=[]
    def get(p,o):return s16(p.get(o,0))
    def put(p,o,v):p[o]=v&65535
    def dist(p,q):return sum(((get(p,o)>>4)-(get(q,o)>>4))**2>>4 for o in (4,6))-4096
    def trig(t,cos=False):return table[(t+(64 if cos else 0))&255]
    def prod(x,y):return s16(s16(x)*s16(y)>>8)
    def rel(p,q):return s16(get(q,10)-get(p,10)),s16(get(q,8)-get(p,8))
    def response(p,q,second):
        vx,vy=get(p,12),get(p,14)
        mag=((vx*vx>>8)+(vy*vy>>8))&65535
        if not mag:return
        mag=s16(sqrt16(mag)<<4);dy,dx=rel(p,q)
        if second:angle=atan16(s16(dy-vy),s16(dx-vx))
        else:
            delta=(atan16(dy,dx)&255)-(atan16(vy,vx)&255)
            angle=-delta if delta<=0 or delta>=127 else delta
        power=prod(trig(angle,True),mag)
        if power<0:power=s16(-power)
        angle=atan16(dy,dx)
        for o,cos in ((20,True),(22,False)):
            z=prod(trig(angle,cos),power);put(q,o,z);put(p,o,-z)
    for p in a:
        for o in (24,26,28):put(p,o,0)
    for i,p in enumerate(a[:-1]):
        if get(p,0)&1:continue
        for j in range(i+1,len(a)):
            q=a[j]
            if get(q,0)&1:continue
            d=dist(p,q)
            if d>=0:continue
            mag=s16(sqrt16((-d)&65535)<<6);dy,dx=rel(p,q);angle=atan16(dy,dx)
            for o,cos in ((26,True),(28,False)):
                z=prod(mag,trig(angle,cos))>>1;put(q,o,get(q,o)+z);put(p,o,get(p,o)-z)
            put(p,24,get(p,24)+1);put(q,24,get(q,24)+1)
            response(p,q,False);response(q,p,True)
            for k,v in ((i,p),(j,q)):
                put(v,12,get(v,12)+get(v,20));put(v,14,get(v,14)+get(v,22));events.append(('callback',k,'B7D9'))
            events.append(('sound',0xd9,1))
    for p in reversed(a):
        if get(p,24):
            for o,z in ((26,4),(28,6)):
                n=get(p,o);v=abs(n)//get(p,24);v=-v if n<0 else v
                put(p,o,v);put(p,z,get(p,z)+v)
    if flags&4:
        for i,p in enumerate(a):
            if get(p,0)&1 or dist(p,aux)>=0:continue
            flags&=~4
            if get(p,0)&0x8000:events += [('callback','aux','BC1C'),('sound',0x9a,1)]
            else:events.append(('pickup',i,'aux'))
            break
    return a,flags,events

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    source=args.source.read_bytes();data,symbols,positions=link(source)
    table=struct.unpack_from('<256h',source,0x7519c9);rng=random.Random(23017)
    def trigs(m):
        m.services[symbols['m23_sin']]=lambda vm:vm.r.__setitem__(0,table[vm.r[0]&255]&0xffffffff)
        m.services[symbols['m23_cos']]=lambda vm:vm.r.__setitem__(0,table[(vm.r[0]+64)&255]&0xffffffff)
    cases=0
    def run_math(name,a,b,expected):
        nonlocal cases
        m=Machine(data,7,0xA000001F);m.r[0]=a&0xffffffff;m.r[1]=b&0xffffffff;before=m.r[4:15].copy()
        trigs(m)
        m.execute(symbols['m23_bf42_'+name],positions)
        assert m.r[0]==expected&0xffffffff,(name,a,b,hex(m.r[0]),expected)
        assert m.r[4:12]==before[:8] and m.r[13:15]==before[9:],(name,'ABI');cases+=1
    for n in [1,2,3,4,5,15,16,17,255,256,4095,4096,32767,32768,65534,65535]+[rng.randrange(1,65536) for _ in range(64)]:run_math('sqrt',n,0,sqrt16(n))
    for y,x in [(1,0),(0,1),(-1,0),(0,-1),(256,256),(-32768,1),(1,-32768)]+[(rng.randrange(-2048,2048),rng.randrange(-2048,2048)) for _ in range(100)]:
        try:expected=atan16(y,x)
        except ZeroDivisionError:continue
        run_math('atan',y,x,expected)
    for n in range(256):
        run_math('sin',n,0,table[n]);run_math('cos',n,0,table[(n+64)&255])
    for n,d in [(0,1),(0xffffffff,65535),(65535,1)]+[(rng.randrange(0x100000),rng.randrange(1,65536)) for _ in range(32)]:run_math('udiv',n,d,n//d)
    scenarios=0
    for count in range(3,7):
        for variant in range(32):
            actors=[]
            for i in range(count):
                x=(i%3)*0x180+(variant%3)*0x100;y=(i//3)*0x180
                if variant%4==0:x=i*0x1800
                actors.append({0:(1 if variant%7==0 and i==1 else 0)|(0x8000 if variant%5==0 else 0),4:x,6:y,8:x>>4,10:y>>4,12:rng.randrange(-400,401)&65535,14:rng.randrange(-400,401)&65535,20:0,22:0})
                if variant>=24:
                    actors[-1].update({12:0,14:0,20:(17+i*3)&65535,22:(-19-i*5)&65535})
            aux={4:0,6:0};flags=4 if variant&1 else 0
            try:expected,ef,ee=model(actors,aux,flags,table)
            except ZeroDivisionError:continue
            m=Machine(data,variant,0xA000001F);m.r[4]=m.r[5]=CTX
            for ptr in [CTX,AUX]+ACTORS:
                for i in range(0x100):m.put(ptr+i,0,1)
            m.put(CTX+0x2b,count,1);m.put(CTX+0x24,flags,2);m.put(CTX+8,AUX-0x18)
            for i,a in enumerate(actors):
                for o,v in a.items():m.put(ACTORS[i]+o,v,2)
            for o,v in aux.items():m.put(AUX+o,v,2)
            events=[]
            def actor(vm):
                assert vm.r[0]<count;vm.r[0]=ACTORS[vm.r[0]]
            def cb(vm):events.append(('callback','aux' if vm.r[0]==AUX else ACTORS.index(vm.r[0]),'BC1C' if vm.r[1]==symbols['m23_cb_BC1C'] else 'B7D9'))
            m.services={symbols['m23_actor']:actor,symbols['m23_callback']:cb,symbols['m23_sound']:lambda vm:events.append(('sound',*vm.r[:2])),symbols['m23_collision_pickup']:lambda vm:events.append(('pickup',ACTORS.index(vm.r[0]),'aux'))}
            trigs(m)
            before=m.r[4:15].copy();m.execute(symbols['m23_src_BF42'],positions)
            assert m.r[4:12]==before[:8] and m.r[13:15]==before[9:],'scene ABI'
            assert events==ee,(count,variant,events,ee)
            assert m.get(CTX+0x24,2)==ef
            for i,a in enumerate(expected):
                for o,v in a.items():assert m.get(ACTORS[i]+o,2)==v,(count,variant,i,o,m.get(ACTORS[i]+o,2),v)
            allowed=[(p+o,p+o+2) for p in ACTORS[:count] for o in (4,6,12,14,20,22,24,26,28)]+[(CTX+0x24,CTX+0x26)]
            for at,v,size in m.writes:assert 0x03007000<=at<before[9] or any(lo<=at and at+size<=hi for lo,hi in allowed),(hex(at),'write extent')
            scenarios+=1
    report=dict(result='PASS',source_sha256=sha(source),generator_sha256=sha((ROOT/'tools/mode23_collision_rules.py').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),linked_bytes=len(data),linked_sha256=sha(data),arithmetic_cases=cases,scene_cases=scenarios,stale_response_scenes=32,source_body=[hex(0x74C842),hex(0x74D075)],source_body_sha256=sha(source[0x74C842:0x74D075]),limits=['Author model and actual generated ARM; not independent review or gameplay execution.','External actor/callback/sound/pickup services are explicit fixtures.','Source atan(0,0), sqrt(0), overflowing x86 divide and participant count outside3..6 are outside the tested contract; no zero-vector gameplay claim.','All three strength-threshold sound branches are identical D9/priority1; unused stack strength computation is omitted.'])
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))

if __name__=='__main__':main()
