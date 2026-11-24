"""Author native task allocator/retirement and mode23 context ownership checks."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
import mode23_native_services as services
import mode23_scene_lifecycle as life
import mode23_participant_setup as setup
CODE=0x08E00000;BASE=0x08000000;POOL=0x02010000

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('source','native','report'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();s=a.source.read_bytes();native=a.native.read_bytes()
 assert s[0x74A9E2:0x74A9E6]==bytes.fromhex('26A05800')
 assert s[0x74AA7B:0x74AA8D]==bytes.fromhex('BF4E00C745040100C745060000C745080000')
 assert struct.unpack_from('<I',native,0x15A74)[0]==0x03002310
 bodies=services.assembly(native)+'\n'+life.assembly(s)+'\n'+setup.assembly(s)
 labels=set(re.findall(r'^(\w+):',bodies,re.M));refs=set(re.findall(r'\bm23_\w+',bodies));external=sorted(refs-labels)
 names=sorted(labels|set(external));prefix='\n'.join('.word '+n for n in names)+'\n'
 code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(prefix+bodies+'\n'+'\n'.join(n+':bx lr' for n in external),CODE)[0]);sym=dict(zip(names,struct.unpack_from('<'+'I'*len(names),code)))
 rom=bytearray(native);rom[CODE-BASE:CODE-BASE+len(code)]=code
 cases=0
 for existing in (0,3):
  for r,row in enumerate(setup.tables(s)):
   for ident in (0,11,14):
    m=Machine(rom,seed=7,flags=0xA000001F)
    for i in range(52*0x118):m.put(POOL+i,0xE5,1)
    for i in range(52):m.put(POOL+i*0x118+0x10,0,2)
    for at in (0x03001338,0x0300133C,0x03001340,0x03001344):m.put(at,0)
    m.put(0x0300231A,ident,1)
    events=[]
    def fixture(name):
     def f(vm):events.append((name,vm.r[:4].copy()))
     return f
    mocked=['m23_audio_reset','m23_audio_service','m23_sound','m23_actor_resources','m23_intro_resources','m23_base_param','m23_evolved_param','m23_event']
    m.services={sym[n]:fixture(n) for n in mocked if n in sym}
    def run(name):
     old=m.r[4:12].copy();sp=m.r[13]
     try:m.run(sym[name],{m.r[14]},max_steps=30000)
     except Exception as e:raise RuntimeError((name,existing,r,ident,hex(m.r[15]-8),[hex(x) for x in m.r[:12]],m.calls[-5:])) from e
     assert m.r[4:12]==old and m.r[13]==sp,(name,'callee state')
    for i in range(existing):
     m.r[:3]=[0x7FFF,0x0800159B0,0x12345678];run('m23_spawn')
    prior=[POOL+i*0x118 for i in range(existing)]
    run('m23_scene_create');ctx=m.r[0]+0x18;m.r[4]=m.r[5]=ctx
    assert m.get(0x03001338,2)==existing+3
    assert m.get(ctx+0xFC)==ctx and m.get(ctx+0x2D,1)==ident
    root_headers=[m.get(ctx+x) for x in (0,4,8)]
    assert len(set(root_headers))==3 and all(m.get(x+0x114)==ctx for x in root_headers)
    assert m.get(ctx+0x24,2)==m.get(ctx+0x2A,1)==m.get(ctx+0xD4,2)==0
    m.put(ctx+0x2A,r,1);run('m23_participants_create')
    count=row['count'];assert m.get(0x03001338,2)==existing+3+count
    actors=[m.get(ctx+12+i*4) for i in range(count)]
    assert len(set(root_headers+actors+prior))==existing+3+count
    assert all(m.get(x+0x114)==ctx for x in actors)
    assert all(m.get(x+0x10,2)&2 for x in actors+root_headers+prior)
    run('m23_src_A50D');assert m.get(0x03001338,2)==existing+3
    assert all(not m.get(x+0x10,2)&2 for x in actors)
    assert all(m.get(x+0x10,2)&2 for x in root_headers+prior)
    run('m23_src_A0FD');assert m.get(0x03001338,2)==existing
    assert all(not m.get(x+0x10,2)&2 for x in root_headers)
    assert all(m.get(x+0x10,2)&2 for x in prior)
    assert [m.get(0x03002310+x,2) for x in (4,6,8)]==[1,0,0]
    assert m.get(0x030012B6,2)==0x8000
    assert m.get(0x05000100,2)==m.get(0x05000200,2)==0
    cases+=1
 result=dict(status='MODE23_NATIVE_TASK_LIFECYCLE_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),source_sha256=sha(s),native_sha256=sha(native),linked_sha256=sha(code),linked_bytes=len(code),cases=cases,source_rounds=7,identities=[0,11,14],existing_tasks=[0,3],native_allocator='08011AC4',native_priority_insertion='08011F90',native_retirement='08011BE4',limits=['Audio and presentation-resource calls are explicit fixtures','No game/emulator/registered entry or memory allocation installed','Task pool test is bounded to the source maximum9 additions and three existing tasks'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
