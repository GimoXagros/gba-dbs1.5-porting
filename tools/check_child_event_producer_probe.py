"""Author Lua fixture of child event producer observation; no emulator launch."""
import argparse,json,re,struct
from pathlib import Path
from types import FunctionType
from check_campaign_complete_probe import host,quote
from check_sprite_mode_corruption_probe import FIXTURE as BASE_FIXTURE
from verify_gba_shoot_entry_capture import ROOT,sha
PROBE='tools/bizhawk_probe_child_event_producer.lua'
ROM='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'

def fixture():
 s=BASE_FIXTURE
 a=s.index(' local function step()');z=s.index(' local function read_file(path)',a)
 s=s[:a]+r'''
 local actor,present=0x020112B0,0x0201135C
 put(present+0x44,0x085B9000,4);put(actor,0x085B9C00,4);put(actor+4,0x410B,2)
 put(0x0300133C,actor,4)
 local function step()
  assert(not inside)
  if case=="invalid" and core<=89408 then
   local value=core-89405
   if value==3 then
    fire(0x0836F77C,{R4=actor})
    fire(0x0836F780,{R8=0x083723E0})
    inside=true;hooks[actor](actor,0x083723E0,0x4000);inside=false
    put(actor,0x083723E0,4);value=5
   end
   put(0x03007E80,value,4);put(0x03007E84,0,4);put(0x03007E88,present,4)
   fire(0x08012874,{R13=0x03007E80,R14=value==5 and 0x08372410 or 0x085B9D14,R5=0x11111111})
   fire(0x08012884,{R5=present,R3=value})
   inside=true;regs.R15=0x0801288C;hooks[present+0xE](present+0xE,value,0x2000);inside=false
   put(present+0xE,value,2)
   fire(0x08012920,{R0=value,R1=0x085B9098})
  end
  core=core+1
 end
''' + s[z:]
 s=s.replace('assert(at==0x03002310);hooks[at]=fn','assert(at==0x020112B0 or at==0x0201136A);hooks[at]=fn')
 s=s.replace('sprite%-replay%-done.txt','child%-event%-done.txt').replace('sprite-replay-done.txt','child-event-done.txt')
 s=s.replace('renderer-trace.txt','child-event-trace.txt').replace('renderer-error.txt','child-event-error.txt')
 s=s.replace('not hooks[0x086FEAE8]','not hooks[0x08012874]')
 a=s.index('   assert(done=="first-invalid-game-mode');z=s.index('\n  else\n',a)
 s=s[:a]+r'''
   assert(done=="invalid-child-event-captured\n" and core==89409 and #inputs==5)
   assert(trace:find("requested=0") and trace:find("requested=1") and trace:find("requested=2") and trace:find("requested=5"))
   assert(trace:find("target=0201135C requested=5 caller=08372410"))
   assert(trace:find("target_callback=083723E0") and trace:find("kind=callback%-write"))
   assert(trace:find("address=0201136A old=2 value=5"))
   assert(trace:find("first_invalid_event") and trace:find("causal_setter"))
   assert(created[out.."/child-first-invalid-event.txt"])
''' + s[z:]
 s=s.replace('bounded-no-invalid-mode','bounded-no-invalid-child-event').replace('renderer-first-invalid-mode.txt','child-first-invalid-event.txt')
 return s

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);args=p.parse_args()
 raw=(ROOT/PROBE).read_bytes();rom=(ROOT/'build/repro-v86-20261117-a/current-candidate.gba').read_bytes()
 assert sha(rom)==ROM
 words={int(a,16):int(b,16) for a,b in re.findall(rb'hook\(0x([0-9A-F]+),0x([0-9A-F]+),',raw)}
 assert len(words)==5 and all(struct.unpack_from('<I',rom,a-0x08000000)[0]==b for a,b in words.items())
 assert not re.search(rb'memory\.write|mainmemory\.write|emu\.setregister|client\.setregister',raw)
 setup=f'local probe={quote(raw)}\nlocal romhash="{ROM}"\nlocal words='+'{'+','.join(f'[{a}]={b}' for a,b in words.items())+'}\n'
 runner=host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+fixture()))('','','')
 result=dict(status='CHILD_EVENT_PRODUCER_LUA_QA_PASS',probe_sha256=sha(raw),rom_sha256=ROM,exec_hooks=5,write_watches=2,cases=3,ordinary_events=[0,1,2],first_invalid_event=5,callback=hex(0x083723E0),caller=hex(0x08372410),observed_actor=hex(0x020112B0),input='Right2 then none',bound=1800,guest_write_api_absent=True,emulator_launched=False,scope='Author fixture; real native caller still requires root replay')
 args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
