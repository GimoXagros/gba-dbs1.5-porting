"""Author actual-native queue checks; score playback is independently specified elsewhere."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'vendor'))
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_sound_adapter import assembly,MAPPING
CODE=0x08E00000;OWNER=0x030022F0
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('native','source_report','audio_manifest','report'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
 a=p.parse_args();assert not a.report.exists();native=a.native.read_bytes()
 assert sha(native)=='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
 code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(assembly(a.source_report.read_bytes(),a.audio_manifest.read_bytes()),CODE)[0])
 rom=bytearray(native);rom[CODE-0x08000000:CODE-0x08000000+len(code)]=code
 cases=0
 for ident,(target,priority) in MAPPING.items():
  for delay in (0,1,65535):
   for flag in range(16):
    m=Machine(rom,seed=11,flags=(flag<<28)|31)
    for i in range(0x12):m.put(OWNER+i,(i*37+11)&255,1)
    m.put(OWNER+6,delay,2);old=dict(m.mem);regs=m.r[4:12].copy();sp=m.r[13]
    m.r[0]=ident;m.r[1]=priority;m.run(CODE,{m.r[14]})
    assert m.r[4:12]==regs and m.r[13]==sp
    expected=dict(old)
    def half(at,v):expected[at]=v&255;expected[at+1]=(v>>8)&255
    if delay==0:
     half(OWNER+2,target);half(OWNER+14,priority);half(OWNER+6,0);half(OWNER+16,(old[OWNER+16]|old[OWNER+17]<<8)|0x100)
    assert all(m.get(k,1)==v for k,v in expected.items())
    assert all(OWNER<=x<OWNER+18 or sp-36<=x<sp for at,v,n in m.writes for x in range(at,at+n))
    cases+=1
 result=dict(status='MODE23_SOUND_ADAPTER_AUTHOR_PASS',checker_sha256=sha(Path(__file__).read_bytes()),adapter_sha256=sha((ROOT/'tools/mode23_sound_adapter.py').read_bytes()),linked_bytes=len(code),linked_sha256=sha(code),actual_native_queue='080D15C0',cases=cases,command_count=len(MAPPING),pending_delay_values=[0,1,65535],NZCV_patterns=16,limits=['New audio IDs70..79 require separate reviewed table and bundle installation','No audio playback/game/emulator execution','Unknown runtime IDs are outside source-proved caller domain'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
