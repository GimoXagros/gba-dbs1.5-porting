"""Check the ID13 fall observer's composed Lua, input, and guards in-process."""

import argparse
import json
import re
import struct
import types
from pathlib import Path

import check_id14_openbus_wrapper as existing

WRAPPER = 'bizhawk_probe_id13_fall_entry.lua'
BASE = 'bizhawk_probe_result_languages.lua'
SITES = (0x08357054, 0x0835732C, 0x083578D4)
WRAPPER_SHA = '57F67564C15C496D47B93FDB1A91266638E830D9D448393E6554AC5670CA438E'

CHECK = r'''
local function replace(s,old,new)
 local first,last=assert(s:find(old,1,true));assert(not s:find(old,last+1,true))
 return s:sub(1,first-1)..new..s:sub(last+1)
end
local function fixture(site)
 local frame,r,files,hooks,composed,policy=100,{},{},{},nil,nil
 local p,q=0x02011710,0x02011828
 local ram={[0x0300489C]=p,[0x030048A0]=q,[0x03002310]=7,[p-8]=2,[q-8]=2,
  [p]=0x0835620C,[p+0x11]=13,[p+0x14]=p,[p+0x18]=q,[q+0x18]=p,[p+0x44]=1,
  [0x0300473C]=10,[0x0300473E]=10,[0x03004740]=12}
 r.R4=p;r.R5=p+0xAC;r.R15=site+4
 local env=setmetatable({},{__index=_G})
 local base={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[base[d]+a]or pinned[base[d]+a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd,
  read_bytes_as_binary_string=function(a,n,d)
   assert(a==0 and n==({IWRAM=0x8000,EWRAM=0x40000})[d]);return d end},
  {__index=function(_,key)error('unplanned memory API '..key)end})
 env.io={open=function(path,mode)
  if mode=='rb'then
   assert(path=='W:/tools/bizhawk_probe_result_languages.lua')
   return {read=function()return original end,close=function()end}
  end
  assert(mode=='wb' and path:find('W:/build/id13-fixture/',1,true)==1 and not files[path])
  local f={bytes='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.bytes=self.bytes..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/id13-fixture'end}
 env.event={on_bus_exec=function(fn,at,name)assert(pinned[at]==0xE1D482BC and not hooks[at]);hooks[at]=fn end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.load=function(body,name,mode,e)
  assert(load(body,name,mode,e));assert(not composed and name=='@ID13-ordinary-fall-entry')
  composed,policy=body,e;return function()end
 end
 assert(load(wrapper,'@reviewed-id13','t',env))()
 local inverse=replace(composed,'dump("loaded-rom.bin","ROM",0,0x1000000)','dump("loaded-rom.bin","ROM",0,0x800000)')
 inverse=replace(inverse,'local limit=math.min(userdata.get("frames") or 14000,14000)','local limit=userdata.get("frames") or 24000')
 inverse=replace(inverse,'  if mode==4 then local button=id13_selection();if button then pulse(button,frame)end\n  elseif mode==5 or mode==6 then pulse("A",frame)','  if mode==4 or mode==5 or mode==6 then pulse("A",frame)')
 inverse=replace(inverse,' id13_input(keys,stage,mode)\n joypad.set(keys)',' joypad.set(keys)')
 inverse=replace(inverse,' if id13_outcome() then outcome="id13-eligible-fall-observed";capture("id13-fall-after") end\n if outcome then break end',' if outcome then break end')
 inverse=replace(inverse,'id13_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));','local f=assert(io.open(out.."/result-done.txt","w"));')
 assert(inverse==original,'only the six intended parent changes')
 assert(policy.id13_selection()=='Down')
 ram[0x0300473C]=11;assert(policy.id13_selection()==nil)
 ram[0x0300473E]=11;assert(policy.id13_selection()=='A')
 hooks[site]();assert(not policy.id13_outcome(),'initial fall ignored')
 local log=files['W:/build/id13-fixture/id13-fall-entry.txt']
 assert(not log.bytes:find('eligible%-fall'))
 local keys={Right=true};policy.id13_input(keys,'menu',7);assert(keys.Right and not keys.A)
 ram[p+0x11]=14;policy.id13_input(keys,'battle',7);assert(not keys.Right and not keys.A)
 ram[p+0x11]=13;ram[0x03004529]=1;policy.id13_input(keys,'battle',7);assert(not keys.A)
 ram[0x03004529]=0;ram[p+0x2C]=0x40;policy.id13_input(keys,'battle',7);assert(not keys.A)
 ram[p+0x2C]=0
 for now=100,119 do
  frame=now;keys={Right=true};policy.id13_input(keys,'battle',7);assert(keys.A and not keys.Right)
  hooks[site]();assert(not log.bytes:find('eligible%-fall'))
 end
 frame=120;keys={};policy.id13_input(keys,'battle',7);assert(not keys.A)
 frame=121;keys={};policy.id13_input(keys,'battle',7);assert(not keys.A)
 local guards={{p+0x44,0},{p+0x44,0x8000},{p+0xA6,1},{p+8,0x100},{p+8,0x4000},
  {0x03002310,6},{p+0x11,14},{p+0x18,0},{q-8,0}}
 for _,guard in ipairs(guards)do
  local addr,value=guard[1],guard[2];local previous=ram[addr]
  ram[addr]=value;hooks[site]();ram[addr]=previous
 end
 r.R4=q;hooks[site]();r.R4=p;r.R5=q+0xAC;hooks[site]();r.R5=p+0xAC
 assert(not log.bytes:find('eligible%-fall'),'every failing eligibility input was ignored')
 hooks[site]();hooks[site]();assert(not policy.id13_outcome())
 assert(select(2,log.bytes:gsub('event=jump%-start core=100',''))==1)
 assert(select(2,log.bytes:gsub('event=jump%-release core=120',''))==1)
 assert(select(2,log.bytes:gsub('event=eligible%-fall core=121',''))==1)
 assert(log.bytes:find('phase=released',1,true))
 frame=122;assert(policy.id13_outcome())
 policy.id13_finish()
 assert(log.closed and log.bytes:find('complete=true phase=released observed=true',1,true))
 for _,label in ipairs({'iwram','ewram'})do
  local f=assert(files['W:/build/id13-fixture/id13-fall-before-'..label..'.bin']);assert(f.closed)
 end
end
for _,address in ipairs(sites)do fixture(address)end
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    tools = existing.ROOT / 'tools'
    wrapper, original = (tools / WRAPPER).read_bytes(), (tools / BASE).read_bytes()
    assert existing.sha(wrapper) == WRAPPER_SHA and existing.sha(original) == '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
    assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister', wrapper)
    rom = (existing.ROOT / 'build/evolution-transition-tables-20261116/component.gba').read_bytes()
    assert existing.sha(rom) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    pinned = {site: struct.unpack_from('<I', rom, site - 0x08000000)[0] for site in SITES}
    assert set(pinned.values()) == {0xE1D482BC}
    for unlock, maximum in ((0, 12), (16, 13), (32, 13), (48, 14)):
        rosters = 0x628000 + unlock * 2
        row = struct.unpack_from(f'<{maximum + 1}H', rom, rosters)
        assert row.index(13) == 11 and row.count(13) == 1
        pinned.update({0x08000000 + rosters + i * 2: actor for i, actor in enumerate(row)})
    words = ','.join(f'[{address}]={value}' for address, value in pinned.items())
    setup = (f'local wrapper={existing.quote(wrapper)}\nlocal original={existing.quote(original)}\n'
             f'local sites={{{",".join(map(str, SITES))}}}\nlocal pinned={{{words}}}\n')
    host = existing.host
    run = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=setup + CHECK))
    run('', '', '')
    data = dict(status='ID13_FALL_ENTRY_LUA_QA_PASS', wrapper_sha256=WRAPPER_SHA,
                checker_sha256=existing.sha(Path(__file__).read_bytes()), exact_effective_inverse=True,
                eligible_sites=[f'{site:08X}' for site in SITES], roster_variants=4, mock_held_A_frames=20,
                waiting_and_held_fall_rejected=True, actual_gameplay_verified=False, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(data['status'], existing.sha(payload))


if __name__ == '__main__':
    main()
