"""Check the fresh-menu campaign entry observer in Lua 5.4 without a game core."""

import argparse
import json
import re
import struct
import types
from pathlib import Path

import check_id14_openbus_wrapper as existing

WRAPPER_SHA = '087629A9C2AAB4AAECBD79C2C32CCE6991F22374A78B6994E2BF1CE9CBC985D3'
BASE_SHA = '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
COMPONENT_SHA = 'ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9'
OPS = {0x0808B70C: 0xE8BD4013, 0x08582C70: 0xE12FFF1E, 0x08584A38: 0x012FFF1E}

CHECK = r'''
local p,q=0x02011710,0x02011828
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)
end
local function fixture(skip_legacy)
 local frame,body,policy,closed=100,nil,nil,false
 local hooks,records,shots={},{},{}
 local owner=0x03002310
 local ram={[owner]=6,[0x0300231E]=8,[0x0300231C]=13,[0x0300232F]=7,[0x0300489C]=p,[0x030048A0]=q,
  [p-8]=2,[q-8]=2,[p+0x14]=p,[q+0x14]=q,[p+0x18]=q,[q+0x18]=p,[q+0x10]=1,[q+4]=1,[q+0x11]=13}
 local r={R0=8,R4=owner,R8=owner,R14=0x08000000}
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/campaign-entry-fixture'end}
 local base={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(off,region)local a=base[region]+off;return ram[a]or ops[a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd},
  {__index=function(_,key)error('unplanned memory API '..key)end})
 env.io={open=function(path,mode)
  if mode=='rb'then
   assert(path=='W:/tools/bizhawk_probe_result_languages.lua')
   return{read=function()return old end,close=function()end}
  end
  assert(mode=='wb' and path=='W:/build/campaign-entry-fixture/campaign-entry.txt')
  return{write=function(_,line)assert(not closed);records[#records+1]=line;return true end,
   flush=function()assert(not closed)end,close=function()assert(not closed);closed=true end}
 end}
 env.event={on_bus_exec=function(fn,at,label)
  assert(ops[at]and not hooks[at] and label:find('campaign-entry-',1,true)==1);hooks[at]=fn
 end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.load=function(source,name,mode,ctx)
  assert(load(source,name,mode,ctx));assert(not body and name=='@campaign-first-entry-observation')
  body,policy=source,ctx;return function()end
 end
 assert(load(wrapper,'@reviewed-campaign-probe','t',env))()
 local inverse=replace(body,'dump("loaded-rom.bin","ROM",0,0x1000000)','dump("loaded-rom.bin","ROM",0,0x800000)')
 inverse=replace(inverse,'local limit=math.min(userdata.get("frames") or 14000,14000)','local limit=userdata.get("frames") or 24000')
 inverse=replace(inverse,' outcome=outcome or campaign_observe(capture)\n if outcome then break end',' if outcome then break end')
 inverse=replace(inverse,'campaign_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));','local f=assert(io.open(out.."/result-done.txt","w"));')
 assert(inverse==old,'exact whole-body inverse and unchanged native menu/key/advance')
 local function sample(core)
  frame=core;return policy.campaign_observe(function(name)shots[#shots+1]=name..'@'..frame end)
 end
 hooks[0x08582C70]();hooks[0x08584A38]();assert(#records==1 and not sample(100))
 ram[0x0300231E]=9;assert(not pcall(hooks[0x0808B70C]));ram[0x0300231E]=8
 ram[0x0300231C]=14;assert(not pcall(hooks[0x0808B70C]));ram[0x0300231C]=13
 ram[0x0300232F]=8;assert(not pcall(hooks[0x0808B70C]));ram[0x0300232F]=7
 ram[0x0300231D]=1;assert(not pcall(hooks[0x0808B70C]));ram[0x0300231D]=0
 r.R4=0;assert(not pcall(hooks[0x0808B70C]));r.R4=owner
 hooks[0x0808B70C]();assert(#records==2)
 r.R0=0;assert(not pcall(hooks[0x08582C70]));r.R0=8;hooks[0x08582C70]()
 assert(not pcall(hooks[0x08584A38]));r.R0=0
 if not skip_legacy then hooks[0x08584A38]()end
 local guards={{owner,6},{0x0300232E,1},{0x0300231E,9},{0x03004502,2},{0x03004529,1},
  {p-8,0},{q+0x14,0},{p+0x18,0},{q+0x10,0},{p+4,3},{q+4,0},{q+0x11,14}}
 ram[owner]=7
 for i,g in ipairs(guards)do
  local addr,val=g[1],g[2];local prev=ram[addr];ram[addr]=val
  assert(not sample(100+i) and #shots==0)
  ram[addr]=prev
 end
 local fake=q+4
 ram[0x030048A0]=fake;ram[p+0x18]=fake;ram[fake-8]=2
 ram[fake+0x14]=fake;ram[fake+0x18]=p;ram[fake+0x10]=1;ram[fake+4]=1;ram[fake+0x11]=13
 assert(not sample(113) and #shots==0,'unaligned actor rejected despite valid fields')
 ram[0x030048A0]=q;ram[p+0x18]=q;ram[q+4]=1;ram[q+0x14]=q;ram[q+0x18]=p
 for now=120,179 do assert(not sample(now))end
 ram[owner]=6;assert(not sample(180));ram[owner]=7
 for now=181,300 do assert(not sample(now))end
 if skip_legacy then assert(not pcall(sample,301) and #shots==1)
 else
  assert(sample(301)=='campaign-first-stage8-cpu13-observed')
  assert(table.concat(shots,',')=='campaign-first-live@120,campaign-stable-live@301')
  assert(table.concat(records):find('streak_start=181',1,true))
 end
 policy.campaign_finish();assert(closed)
 assert(records[#records]:find('stable=121 guest_writes=none',1,true))
end
fixture(false);fixture(true)
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    root = existing.ROOT
    wrapper = (root / 'tools/bizhawk_probe_campaign_entry.lua').read_bytes()
    old = (root / 'tools/bizhawk_probe_result_languages.lua').read_bytes()
    assert existing.sha(wrapper) == WRAPPER_SHA and existing.sha(old) == BASE_SHA
    assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister|\bjoypad\.set', wrapper)
    rom = (root / 'build/campaign-stage-progression-v80-20261117/component.gba').read_bytes()
    assert existing.sha(rom) == COMPONENT_SHA
    assert all(struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode for address, opcode in OPS.items())
    setup = (f'local wrapper={existing.quote(wrapper)}\nlocal old={existing.quote(old)}\nlocal ops={{' +
             ','.join(f'[{address}]={opcode}' for address, opcode in OPS.items()) + '}\n')
    host = existing.host
    run = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=setup + CHECK))
    run('', '', '')
    data = dict(status='CAMPAIGN_ENTRY_PROBE_LUA_QA_PASS', wrapper_sha256=WRAPPER_SHA, base_sha256=BASE_SHA,
                component_sha256=COMPONENT_SHA, checker_sha256=existing.sha(Path(__file__).read_bytes()),
                exact_effective_inverse=True, bound_hook_opcodes=len(OPS), live_snapshots=121,
                inactive_wrong_role_and_unaligned_rejected=True, requires_all_three_hooks=True,
                input_unchanged=True, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(data, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(data['status'], existing.sha(payload))


if __name__ == '__main__':
    main()
