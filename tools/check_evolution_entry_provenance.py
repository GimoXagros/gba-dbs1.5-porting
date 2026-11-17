"""Focused actual-Lua check of the bounded positive entry witness."""
import argparse
import hashlib
import json
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local/pydeps'))
import verify_wsc_shoot_short_hard as host

CHECK=r'''
for _,case in ipairs({'null-B','positive-B','wrong-id','uninitialized','stale','bad-opcode'})do
 local frame=8322;local p=0x020117BC;local actor=p-0xAC
 local ram={[0x0835A1EC]=0xE92D0020,[0x0835A1FC]=0xE28DD00C,[0x08352830]=0xE1D480B4,[0x08353C98]=0xE594800C,[0x08353C9C]=0xE3580000,[0x08353CA8]=0xE59F10D4,[0x08353C70]=0xE1C100B4,[0x08353D24]=0xE1C100B4}
 ram[actor+0x11]=case=='wrong-id'and 13 or 14
 ram[p+0x44]=0x086184A0;ram[0x086184A0]=0x086184A8
 ram[p+0x24]=0x08618C00;ram[p+0x28]=0x0861B000;ram[p+0x2C]=0
 ram[0x08618C0C]=case=='positive-B'and 0x0861B100 or 0
 if case=='bad-opcode'then ram[0x0835A1FC]=0 end
 local hooks,files={},{};local r={};for i=0,15 do r['R'..i]=0 end
 r.R4=actor;r.R5=p;r.R0=115
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/entry-check'end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 local base={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[base[d]+a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd,read_bytes_as_binary_string=function(a,n,d)assert(a==0 and n==({IWRAM=0x8000,EWRAM=0x40000})[d]);return d end},{__index=function(_,k)error('unplanned memory API '..k)end})
 env.io={open=function(path,mode)
  assert(mode=='wb');assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 local ok,api=pcall(assert(load(wrapper_source,'@entry','t',env)))
 if case=='bad-opcode'then assert(not ok)else
  assert(ok and api.outcome()==nil);hooks[0x0835A1EC]()
  if case=='stale'then frame=8324 end
  if case~='uninitialized'then hooks[0x0835A1FC]()end
  hooks[0x08352830]();r.R4=0x08618C00;hooks[0x08353C98]()
  r.R8=ram[0x08618C0C];hooks[0x08353C9C]()
  if case=='positive-B'then r.R4=r.R8;hooks[0x08353CA8]();r.R1=0x030048C8;r.R0=8;hooks[0x08353D24]()end
  assert(api.outcome()==nil)
  frame=8325
  local expected=case=='null-B'or case=='positive-B'
  assert(api.outcome()==(expected and 'evolution-entry-provenance-observed'or nil))
  if expected then assert(api.outcome()=='evolution-entry-provenance-observed')end
  api.finish();api.finish()
  local f=files['W:/build/entry-check/evolution-entry-provenance.txt'];assert(f.closed)
  if case=='null-B'then assert(f.data:find('actual_B=00000000',1,true))end
  if case=='positive-B'then assert(f.data:find('stored=0008',1,true))end
  if expected then assert(files['W:/build/entry-check/evolution-entry-boundary-iwram.bin'].closed)end
  for _,file in pairs(files)do assert(file.closed)end
 end
end
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 module=(ROOT/'tools/bizhawk_observe_evolution_entry_provenance.lua').read_bytes()
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=CHECK),argdefs=host.lua_check.__defaults__)
 fn(module.decode(),'','')
 wrapper=(ROOT/'tools/bizhawk_probe_id14_entry_provenance.lua').read_bytes()
 report=dict(status='PASS',lua_cases=6,module_sha256=hashlib.sha256(module).hexdigest().upper(),wrapper_sha256=hashlib.sha256(wrapper).hexdigest().upper(),scope='Actual module Lua, positive/null B, wrong ID, uninitialized/stale rejection, next-frame snapshots and opcode guards. Full nested composition requires independent check.',emulator_launched=False)
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
