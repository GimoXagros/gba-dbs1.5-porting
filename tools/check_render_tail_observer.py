"""Check the new read-only observer using the installed Lua54 runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import verify_wsc_shoot_short_hard as host

ROOT = Path(__file__).resolve().parents[1]
CHECK = r'''
for _,case in ipairs({'normal','bad-ROM','bad-RAM','bad-age'})do
 local now=9708
 local ram={[0x08352998]=0xE7895101,[0x083734F0]=0xE92D4000,[0x0837354C]=0xE92D4000,
 [0x083735BC]=0xE92D4000,[0x08012C30]=0xE5954044,[0x03000200]=0xE92D403F,[0x03000358]=0xE5C20000,
 [0x0300489C]=0x02011710,[0x030048A0]=0x02011828}
 if case=='bad-ROM'then ram[0x08352998]=0 end
 local hooks,files={},{}
 local regs={};for i=0,15 do regs['R'..i]=0 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/render-author'end}
 env.emu={framecount=function()return now end,getregisters=function()return regs end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 local domains={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[domains[d]+a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd},{__index=function(_,k)error('unexpected memory API '..k)end})
 env.io={open=function(path,mode)
  assert(mode=='wb');assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 local ok,api=pcall(assert(load(wrapper_source,'@render-tail','t',env)))
 if case=='bad-ROM'then assert(not ok)else
  assert(ok);local f=files['W:/build/render-author/render-tail.txt']
  hooks[0x03000200]();assert(not f.data:find('event=render',1,true))
  if case=='bad-age'then assert(not pcall(api.frame,1))else
   api.frame(0)
   if case=='bad-RAM'then ram[0x03000200]=0;assert(not pcall(hooks[0x03000200]))else
    for i=1,10 do hooks[0x03000200]()end
    now=9709;api.frame(1);hooks[0x03000200]()
    for age=2,120 do now=9708+age;api.frame(age)end
    assert(not pcall(api.frame,121))
   end
  end
  api.finish();api.finish();assert(f.closed)
  hooks[0x03000200]()
  if case=='normal'then
   assert(f.data:find('count event=render observed=11 suppressed=2',1,true))
   assert(f.data:find('snapshot=age-120 core=9828',1,true))
   local _,n=f.data:gsub('event=render core=','');assert(n==9)
  end
 end
end
'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists(), 'fresh output'
    observer = (ROOT / 'tools/bizhawk_observe_render_tail.lua').read_bytes()
    check = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=CHECK),
                               argdefs=host.lua_check.__defaults__)
    check(observer.decode(), '', '')
    result = dict(status='RENDER_TAIL_OBSERVER_PASS', cases=4,
                  observer_sha256=hashlib.sha256(observer).hexdigest().upper(),
                  checked=['inactive hooks', 'ROM opcode rejection', 'live RAM opcode rejection',
                           'tail start/end bounds', 'per-frame throttle and total counts',
                           'all 121 frame boundaries', 'idempotent finish', 'no guest-write API'],
                  emulator_launched=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
