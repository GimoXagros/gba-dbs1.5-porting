"""Check the campaign control tail's actual Lua composition and timed guards."""

import argparse
import json
import re
import struct
import types
from pathlib import Path

import check_id14_openbus_wrapper as existing

ENTRY = 'bizhawk_probe_campaign_control_tail.lua'
CAMPAIGN = 'bizhawk_probe_campaign_entry.lua'
PARENT = 'bizhawk_probe_result_languages.lua'
PINS = {
    ENTRY: 'F1F8303200D33299E86057DBDC63E3FFCAF6364A13CE9CE58CBED78329EA30BB',
    CAMPAIGN: '087629A9C2AAB4AAECBD79C2C32CCE6991F22374A78B6994E2BF1CE9CBC985D3',
    PARENT: '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
}
OPS = {0x0808B70C: 0xE8BD4013, 0x08582C70: 0xE12FFF1E, 0x08584A38: 0x012FFF1E,
       0x08377B88: 0xE28DD010, 0x0837501C: 0xE59F8150, 0x0837513C: 0xE1C412BE}

CHECK = r'''
local h,p=0x02011D88,0x02011710
local ready,clock,held=0x08377B88,0x0837501C,0x0837513C
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)
end
local function compose(entry)
 local frame,r,hooks,files=100,{R0=0,R1=0,R4=p,R8=0x03004500,R9=7200},{},{}
 local ram={[0x03002310]=7,[0x0300231E]=8,[0x03004510]=h,[0x0300489C]=p,[h]=0x08374E6C,
  [h+0x10]=2,[p-8]=2,[p+0x14]=p,[0x03004500]=7200}
 local context,final,nested
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/control-tail-fixture'end}
 local base={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)local at=base[d]+a;return ram[at]or ops[at]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd},
  {__index=function(_,k)error('unplanned memory API '..k)end})
 env.io={open=function(path,mode)
  if mode=='rb'then assert(sources[path],path);return{read=function()return sources[path]end,close=function()end}end
  assert(mode=='wb' and not files[path]);local f={text='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.text=self.text..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 env.event={on_bus_exec=function(fn,a,label)assert(ops[a] and not hooks[a]);hooks[a]=fn end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.load=function(code,name,mode,ctx)
  local executable=assert(load(code,name,mode,ctx))
  if name=='@campaign-running-tail-extension'then nested=code end
  if name=='@campaign-first-entry-observation'then
   assert(not final);context,final=ctx,code;return function()end
  end
  return executable
 end
 assert(load(sources['W:/tools/'..entry],'@qa-control-tail','t',env))()
 assert(final)
 if nested then
  local inverse=replace(nested,'tail_setup()','return "campaign-first-stage8-cpu13-observed"')
  inverse=replace(inverse,'campaign_observe=function(capture) observe(capture);return tail_observe(capture)end','campaign_observe=observe')
  inverse=replace(inverse,'file:close();tail_finish()\nend},{__index=_ENV})','file:close()\nend},{__index=_ENV})')
  inverse=replace(inverse,[=[source=replace(source,' joypad.set(keys)',' tail_input(keys)\n joypad.set(keys)')
]=],'')
  assert(inverse==sources['W:/tools/'..campaign_name],'exact four initial edits')
  local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==6)
 end
 return final,context,hooks,ram,r,function(value)frame=value end,files
end

local original=compose(campaign_name)
local modified=compose(entry_name)
assert(replace(modified,' tail_input(keys)\n joypad.set(keys)',' joypad.set(keys)')==original,'exact whole parent inverse')

local function trial(ack)
 local _,policy,hook,ram,r,at,files=compose(entry_name)
 local shots={}
 local function sample(now)
  at(now);return policy.tail_observe(function(name)shots[#shots+1]=name..'@'..now end)
 end
 local function set_clock(now,value)
  at(now);ram[0x03004500]=value;r.R9=value;hook[clock]()
 end
 hook[ready]();hook[clock]();assert(not sample(101) and #shots==0)
 policy.tail_setup()
 assert(not pcall(hook[ready]),'READY callback is excluded')
 ram[h]=0x08374FF4
 ram[0x03004510]=h+4;ram[h+4]=0x08374FF4;ram[h+0x14]=2
 assert(not pcall(hook[ready]),'active but misaligned task header excluded')
 ram[0x03004510]=h;ram[h+0x10]=0;assert(not pcall(hook[ready]));ram[h+0x10]=2
  ram[0x03004502]=2;assert(not pcall(hook[ready]));ram[0x03004502]=0
 at(200);hook[ready]()
 local keys={Right=true};policy.tail_input(keys);assert(keys.Right and not keys.A)
 r.R8=0;assert(not pcall(hook[clock]));r.R8=0x03004500
 assert(not pcall(hook[clock]),'initial7200 is not decremented')
 ram[0x03004500]=7199;r.R9=7198;assert(not pcall(hook[clock]))
 set_clock(201,7199);at(202);keys={Right=true};policy.tail_input(keys);assert(keys.A and keys.Right)
 set_clock(202,7198)
 if ack then
  local bad=0x02011A60+4
  ram[0x0300489C]=bad;ram[bad-8]=2;ram[bad+0x14]=bad;ram[bad+0x2C]=0x40
  r.R4=bad;r.R0=0x40;hook[held]();assert(not sample(203) and #shots==0,'unaligned P1 actor rejected')
  ram[0x0300489C]=p;r.R4=p;at(202);assert(not pcall(hook[held]),'wrong held RAM rejected')
  ram[p+0x2C]=0x40;hook[held]();assert(not sample(203) and #shots==1)
 end
 at(203);keys={A=true,Right=true};policy.tail_input(keys);assert(not keys.A and keys.Right)
 r.R0=0;ram[p+0x2C]=0;hook[held]()
 local value=7198
 for now=203,214 do value=value-1;set_clock(now,value);assert(not sample(now+1))end
 -- A pause transition invalidates even an earlier valid clock store.
 value=value-1;set_clock(215,value)
 ram[0x03004529]=1;assert(not sample(216));ram[0x03004529]=0
 assert(not sample(217)) -- Missing clock core.
 set_clock(217,value);assert(not sample(218));set_clock(218,value);assert(not sample(219)) -- Non-decreasing counter.
 for now=219,338 do value=value-1;set_clock(now,value);assert(not sample(now+1))end
 value=value-1;set_clock(339,value)
 if ack then
  assert(sample(340)=='campaign-running-input-and-clock-tail-observed')
  assert(table.concat(shots,',')=='campaign-running-input@203,campaign-running-stable@340')
 else
  assert(not sample(340) and #shots==0,'running clock alone cannot prove input acceptance')
  r.R0=0x40;ram[p+0x2C]=0x40;assert(not pcall(hook[held]),'A acceptance after press+1 is rejected')
 end
 policy.tail_finish()
 local log=files['W:/build/control-tail-fixture/campaign-control-tail.txt']
 assert(log.closed and select(2,log.text:gsub('event=A%-press core=',''))==1)
 if ack then assert(log.text:find('streak_start=220',1,true) and log.text:find('stable=121',1,true))end
end
trial(true);trial(false)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    root = existing.ROOT
    scripts = {name: (root / 'tools' / name).read_bytes() for name in PINS}
    assert {name: existing.sha(data) for name, data in scripts.items()} == PINS
    assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister', scripts[ENTRY])
    rom = (root / 'build/campaign-stage-progression-v80-20261117-r2/component.gba').read_bytes()
    assert existing.sha(rom) == '933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
    assert all(struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode for address, opcode in OPS.items())
    sources = ','.join(f'[{existing.quote(("W:/tools/" + name).encode())}]={existing.quote(data)}' for name, data in scripts.items())
    opcode_table = ','.join(f'[{address}]={opcode}' for address, opcode in OPS.items())
    setup = (f'local sources={{{sources}}}\nlocal ops={{{opcode_table}}}\n'
             f'local entry_name="{ENTRY}"\nlocal campaign_name="{CAMPAIGN}"\n')
    host = existing.host
    run = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=setup + CHECK))
    run('', '', '')
    result = dict(status='CAMPAIGN_CONTROL_TAIL_LUA_QA_PASS', dependency_sha256=PINS,
                  checker_sha256=existing.sha(Path(__file__).read_bytes()), component_sha256=existing.sha(rom),
                  bound_hook_opcodes=len(OPS), exact_nested_inverse=True, ordinary_A_frames=1,
                  requires_accepted_A=True, rejects_late_A_and_paused_boundary=True,
                  consecutive_clock_boundaries=121, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(result['status'], existing.sha(payload))


if __name__ == '__main__':
    main()
