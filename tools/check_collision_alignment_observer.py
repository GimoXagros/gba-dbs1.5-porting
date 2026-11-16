"""Exercise the read-only alignment observer through Lua54, without an emulator."""
import argparse, hashlib, json, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'local/pydeps'))
import verify_wsc_shoot_short_hard as host
CHECK=r"""
for _,case in ipairs({'aligned','odd','stale','e5','bad-opcode'})do
 local frame=100;local ram={[0x0836E37C]=0xE1D130B2,[0x0836E380]=0xE1D120B4,[0x0836EB58]=0xE1D810B0,[0x0836EBA4]=0xE12FFF19}
 local hooks,files={},{};local r={};for i=0,15 do r['R'..i]=0 end
 r.R1=case=='aligned'and 0x080D2920 or 0x080D2921;r.R4=0x030048C8
 ram[r.R4+0x10]=r.R1;ram[r.R4]=0x02011710;ram[r.R4+4]=8;ram[0x03004D20]=8;ram[0x080D2922]=0x2004
 if case=='bad-opcode'then ram[0x0836E37C]=0 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/alignment-author'end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 local domain={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[domain[d]+a]or 0 end
 env.memory=setmetatable({read_u16_le=rd,read_u32_le=rd,read_bytes_as_binary_string=function(a,n,d)assert(a==0 and n==({IWRAM=0x8000,EWRAM=0x40000})[d]);return d end},{__index=function(_,k)error('unplanned memory API '..k)end})
 env.io={open=function(path,mode)
  assert(mode=='wb'or mode=='w');assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 local ok,api=pcall(assert(load(wrapper_source,'@alignment','t',env)))
 if case=='bad-opcode'then assert(not ok)else
  assert(ok);hooks[0x0836E37C]()
  if case=='stale'then frame=101 end
  r.R3=0x04000020;hooks[0x0836E380]()
  if case=='e5'then ram[0x03004D20]=0xE5 end
  local hit,err=pcall(hooks[0x0836EB58])
  if case=='e5'then
   assert(not hit and err:find('observed-collision-e5',1,true))
   local marker=files['W:/build/alignment-author/result-done.txt'];assert(marker.closed and marker.data=='failure:observed-collision-e5')
   assert(files['W:/build/alignment-author/collision-e5-iwram.bin'].closed)
  else assert(hit);hooks[0x0836EBA4]();api.finish();api.finish()end
  local f=files['W:/build/alignment-author/collision-alignment.txt'];assert(f.closed)
  assert(f.data:find('metadata=1 odd='..(case=='aligned'and 0 or 1)..' confirmed='..((case=='aligned'or case=='stale')and 0 or 1),1,true))
  if case=='odd'then assert(f.data:find('r3=04000020',1,true)and f.data:find('event=odd-branch',1,true))end
  if case=='aligned'then assert(not files['W:/build/alignment-author/collision-first-odd-iwram.bin'])end
 end
end
"""
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 source=(ROOT/'tools/bizhawk_observe_collision_alignment.lua').read_bytes()
 assert hashlib.sha256(source).hexdigest().upper()=='B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C'
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=CHECK),argdefs=host.lua_check.__defaults__)
 fn(source.decode(),'','')
 report=dict(status='PASS',cases=5,emulator_launched=False,observer_sha256=hashlib.sha256(source).hexdigest().upper(),scope='actual Lua composition/hooks/guards/file ordering; no gameplay or root-cause claim')
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
if __name__=='__main__':main()
