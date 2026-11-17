"""Exercise the exact positive Shoot contact Lua and its frozen observer in-process."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

from check_campaign_complete_probe import host, quote
from check_sprite_mode_corruption_probe import FIXTURE as SPRITE_FIXTURE
from verify_gba_shoot_entry_capture import ROOT, sha


WRAPPER = 'tools/bizhawk_probe_child_contact_positive.lua'
PARENT = 'tools/bizhawk_probe_child_event_producer.lua'
PIN = 'D5EE2AEEB153946E74ABE43B8B386BC3AFBF5634CF32A3687EDF76B027793BD8'
PARENT_PIN = 'B01A4F35A77D9CB7E24173E73C6D85818FBF8A3563B29FE55E69294EBCA7A9F9'
ROM = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
PATH = 'W:/tools/bizhawk_probe_child_event_producer.lua'
CASES = ('positive', 'wrong-r11', 'wrong-effect-stack', 'missing-wait', 'setter-without-store',
         'different-child', 'dirty-match-flags', 'dirty-target-flags', 'invalid', 'bounded', 'bad-state')
MOCK_STEPS = r'''
 local actor,present,target,sp=0x020112B0,0x0201135C,0x02011828,0x03007E80
 put(present+0x44,0x085B9000,4)
 put(present+0x118+0x44,0x085B9000,4)
 put(actor,0x085B9C00,4);put(actor+4,0x410B,2);put(actor+0x18,target,4)
 put(0x0300133C,actor,4)
 local function setter(value,p,store)
  put(sp,value,4);put(sp+4,0,4);put(sp+8,p,4)
  fire(0x08012874,{R13=sp,R14=0x08D8CA70,R5=p})
  if store then
   fire(0x08012884,{R3=value})
   assert(p==present)
   regs.R15=0x0801288C
   inside=true;hooks[p+0xE](p+0xE,value,0x2000);inside=false
   put(p+0xE,value,2)
  end
 end
 local function step()
  assert(not inside)
  if case~="bounded" and case~="bad-state" then
   if core==89405 then
    fire(0x0836F77C,{R4=actor,R5=present})
    inside=true;hooks[actor](actor,0x08D8C864,0x4000);inside=false
    put(actor,0x08D8C864,4)
   elseif core==89406 then
    fire(0x08D8C864,{R4=actor,R5=present})
    put(target+8,0x8010,2);put(0x0300450A,0x56,2)
    put(sp,3,4);put(sp+4,0,4);put(sp+8,0,4);put(sp+12,0,4)
    put(sp+16,case=="wrong-effect-stack" and actor or target,4)
    fire(0x0835972C,{R13=sp,R14=0x08D8C8AC,R5=target,R11=case=="wrong-r11" and 1 or 0})
    setter(1,present,true)
   elseif core==89407 then
    if case=="invalid" then
     setter(5,present,true)
    else
     if case~="missing-wait" then fire(0x08D8C910,{R4=actor,R5=present})end
     if case=="different-child" then setter(2,present+0x118,false)
     else setter(2,present,case~="setter-without-store")end
     put(target+8,case=="dirty-target-flags" and 0x8810 or 0x8800,2)
    end
   elseif core==89408 then
    fire(0x08D8C980,{R4=actor,R5=present})
    put(0x0300450A,case=="dirty-match-flags" and 0x46 or 6,2)
    fire(0x08D8C9BC,{R4=actor,R5=present})
   end
  end
  core=core+1
 end
'''
MOCK_RESULTS = r'''
 assert(exited and load_count==1 and inputs[#inputs]==false)
 local done=assert(created[out.."/child-contact-done.txt"])
 local trace=created[out.."/child-event-trace.txt"]
 local problem=created[out.."/child-event-error.txt"]
 local expected_error={
  ["wrong-r11"]="source effect ABI", ["wrong-effect-stack"]="source effect ABI",
  ["missing-wait"]="source milestones", ["setter-without-store"]="source milestones",
  ["different-child"]="source milestones",
  ["dirty-match-flags"]="source flags retired", ["dirty-target-flags"]="source flags retired",
  ["bad-state"]="same-epoch restored iwram"
 }
 if expected_error[case] then
  assert(done=="failure:script-error\n" and problem:find(expected_error[case],1,true),case)
  assert(not created[out.."/diagnostic.State"])
  if case=="bad-state" then assert(#inputs==1 and not hooks[0x08012874])
  else assert(inputs[1] and inputs[2]) end
 else
  assert(#created[out.."/loaded-rom.bin"]==0x1000000 and trace)
  assert(inputs[1] and inputs[2])
  for i=3,#inputs do assert(not inputs[i])end
  assert(created[out.."/diagnostic.State"] and created[out.."/diagnostic.png"])
  if case=="positive" then
   assert(done=="source-child-contact-retired\n" and core==89409 and #inputs==5)
   local prior=0
   for _,label in ipairs({"kind=first ","kind=effect ","kind=wait ","old=1 value=2 ","kind=release ","kind=retired "})do
    local next_at=assert(trace:find(label,prior+1,true),label)
    assert(next_at>prior);prior=next_at
   end
   assert(trace:find("target=02011828 flags=0006 target_flags=8800",1,true))
   assert(not created[out.."/child-first-invalid-event.txt"])
  elseif case=="invalid" then
   assert(done=="invalid-child-event-captured\n" and core==89408 and #inputs==4)
   assert(created[out.."/child-first-invalid-event.txt"]:find("old=1 value=5",1,true))
   assert(trace:find("causal_setter",1,true) and not trace:find("kind=retired ",1,true))
  else
   assert(done=="bounded-contact-incomplete\n" and core==91205 and #inputs==1801)
   assert(not created[out.."/child-first-invalid-event.txt"])
  end
 end
end
'''


def replace(data, original, new):
    assert data.count(original) == 1, original
    return data.replace(original, new)


def fixture():
    s = SPRITE_FIXTURE
    quoted_cases = ','.join(f'"{case}"' for case in CASES)
    s = replace(s, '{"invalid","bounded","bad-state"}', '{'+quoted_cases+'}')
    at = s.index(' local function step()')
    end = s.index(' local function read_file(path)', at)
    s = s[:at]+MOCK_STEPS+s[end:]
    s = replace(s, 'inside=true;hooks[at]();inside=false',
                'inside=true;local ok,err=pcall(hooks[at]);inside=false;assert(ok,err)')
    s = replace(s, 'assert(at==0x03002310);hooks[at]=fn',
                'assert(at==0x020112B0 or at==0x0201136A);hooks[at]=fn')
    s = replace(s, '  if mode=="rb"then return',
                '  if path=="'+PATH+'"then\n'
                '   assert(mode=="rb");return {read=function()return parent end,close=function()return true end}\n'
                '  end\n  if mode=="rb"then return')
    s = replace(s, '  if path:match("sprite%-replay%-done.txt$") and case~="bad-state" then',
                '  if path:match("child%-contact%-done.txt$") and (case=="positive" or case=="invalid" or case=="bounded") then')
    s = replace(s, ' assert(load(probe,"@actual-sprite-replay","t",env))()',
                ' env.load=function(code,name,mode,context)\n'
                '  assert(name=="@frozen-child-event-positive" and context==env)\n'
                '  assert(code:find("contact.complete",1,true))\n'
                '  assert(not code:find("memory.write",1,true) and not code:find("emu.setregister",1,true))\n'
                '  return load(code,name,mode,context)\n'
                ' end\n assert(load(probe,"@child-contact-positive-fixture","t",env))()')
    return s.split(' assert(exited and load_count==1', maxsplit=1)[0] + MOCK_RESULTS


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    a = p.parse_args()
    wrapper, parent = ((ROOT / name).read_bytes() for name in (WRAPPER, PARENT))
    assert (sha(wrapper), sha(parent)) == (PIN, PARENT_PIN)
    rom = (ROOT / 'build/shoot-child-contact-20261117/component.gba').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM
    sites = {int(pc, 16): int(op, 16) for pc, op in re.findall(
        rb'(?:hook|milestone)\(0x([0-9A-F]{8}),0x([0-9A-F]{8}),"', parent + b'\n' + wrapper)}
    assert len(sites) == 10 and sites[0x0836F77C] == 0xEA28741F
    assert all(struct.unpack_from('<I', rom, pc-0x08000000)[0] == op for pc, op in sites.items())
    assert not re.search(rb'(?:memory|mainmemory)\.write|(?:emu|client)\.setregister', wrapper+parent)
    setup = f'local probe={quote(wrapper)}\nlocal parent={quote(parent)}\nlocal romhash="{ROM}"\nlocal words='
    setup += '{'+','.join(f'[{pc}]={op}' for pc, op in sites.items())+'}\n'
    runner = host.lua_check
    FunctionType(runner.__code__, dict(runner.__globals__, CHECK=setup+fixture()))('', '', '')
    result = dict(status='CHILD_CONTACT_POSITIVE_LUA_QA_PASS', wrapper_sha256=PIN, parent_sha256=PARENT_PIN,
                  rom_sha256=ROM, checker_sha256=sha(Path(__file__).read_bytes()), native_hook_sites=len(sites),
                  exercised_cases=CASES, actual_owner_bus_event_required=True, guest_write_api_absent=True,
                  controller='Right2 then none; final release', replay_limit=1800,
                  no_emulator_or_live_game_state_used=True)
    assert not a.report.exists()
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
