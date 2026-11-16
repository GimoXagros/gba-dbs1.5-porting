"""Small author Lua54 composition and scalar telemetry check; no emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import types
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
quote=lambda b:'"'+''.join('\\'+f'{v:03d}' for v in b)+'"'

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 paths=[ROOT/'tools'/n for n in ('bizhawk_probe_result_music_lifetime.lua','bizhawk_probe_result_languages_16m.lua','bizhawk_probe_result_languages.lua')]
 blobs=[p.read_bytes() for p in paths];wrapper,mid,base=blobs
 assert sha(mid)=='5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF'
 assert sha(base)=='928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
 prefix=re.search(rb'local telemetry=\[=\[\n(.*?)\]=\]',wrapper,re.S).group(1)
 body=base.replace(b'dump("loaded-rom.bin","ROM",0,0x800000)',b'dump("loaded-rom.bin","ROM",0,0x1000000)')
 expected=prefix+body.replace(b'client.exit()',b'music_lifetime_finish()\nclient.exit()')
 test=r'''
local hooks,lines={},{}
local frame=99
local regs={R0=0,R1=0,R2=0,R3=0,R4=0x02011710,R8=0,R13=0x03007F00,R14=0x0835A454,R15=0}
local ram={
 [0x0837B458]=0x5A280AD8,[0x08D7DFC0]=0xE358006C,[0x08D7DFC8]=0xE3580070,
 [0x0837FBB4]=0x03006B40,[0x03007F00]=2,[0x02011721]=2,[0x03006B40]=0x08D41000,
 [0x03004E98]=0x6E,
}
for id=0x6C,0x6F do ram[0x08D33000+id*8]=0x08D40000+id*32 end
local env=setmetatable({},{__index=_G})
env.userdata={get=function(k)assert(k=='output');return 'W:/build/music-test'end}
env.memory={getmemorydomainsize=function()return 0x1000000 end}
local function read(at,domain)
 local bases={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 assert(bases[domain]);return ram[bases[domain]+at]or 0
end
env.memory.read_u8=read;env.memory.read_u16_le=read;env.memory.read_u32_le=read
env.emu={framecount=function()return frame end,getregisters=function()return regs end}
env.event={on_bus_exec=function(fn,pc,name)assert(not hooks[pc]);hooks[pc]=fn end}
env.io={open=function(path,mode)
 if mode=='rb'then
  local text=path=='W:/tools/bizhawk_probe_result_languages_16m.lua'and hard_source or path=='W:/tools/bizhawk_probe_result_languages.lua'and collect_source
  assert(text);return{read=function()return text end,close=function()end}
 end
 assert(path=='W:/build/music-test/music-lifetime.txt'and mode=='wb')
 return{write=function(_,s)lines[#lines+1]=s;return true end,flush=function()end,close=function()end}
end}
local final=false
env.load=function(source,name,mode,scope)
 assert(scope==env and mode=='t')
 if name~='@reviewed-result-music-lifetime'then return load(source,name,mode,scope)end
 assert(source==expected_source,'whole base plus exactly prefix and pre-exit finish')
 assert(load(source,name,mode,scope),'actual entire effective syntax')
 final=true
 return function()
  local exercise=[[
   assert(music_counts['evolution-selector']==0)
   TEST_HOOKS[0x080D14BC]()
   TEST_REGS.R8=0x6E
   for i=1,70 do TEST_HOOKS[0x0837B44C]()end
   TEST_REGS.R0=0x03006B40;TEST_REGS.R1=0x08D40000+0x6E*32
   TEST_HOOKS[0x0837C298]();TEST_HOOKS[0x0837C29C]()
   TEST_REGS.R0=123;TEST_REGS.R1=124;TEST_HOOKS[0x0837C364]()
   TEST_REGS.R1=123;TEST_HOOKS[0x0837C398]()
   music_lifetime_finish()
  ]]
  env.TEST_HOOKS=hooks;env.TEST_REGS=regs
  assert(load(prefix_source..exercise,'@scalar-exercise','t',env))()
 end
end
assert(load(wrapper_source,'@wrapper','t',env))()
assert(final)
local all=table.concat(lines)
assert(all:find('evolution_entries=1 starts6C=0 starts6D=0 starts6E=1 starts6F=0',1,true))
assert(all:find('count event=music-request observed=70 emitted=32',1,true))
assert(all:find('equal=false',1,true)and all:find('equal=true',1,true))
local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==10)
'''
 code='local expected_source='+quote(expected)+'\nlocal prefix_source='+quote(prefix)+'\n'+test
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__)
 fn(wrapper.decode(),mid.decode(),base.decode())
 report=dict(result='PASS_AUTHOR_LUA54',wrapper_sha256=sha(wrapper),mid_sha256=sha(mid),base_sha256=sha(base),
  effective_sha256=sha(expected),exact_ordinary_body_delta='prepend telemetry and one finish before client.exit',
  hooks=10,max_event_rows=320,separate_file=True,actual_Lua54_composition_and_callbacks=True,
  cases=['entry identity','appended6E actual player start','70 requests capped32 withtotal70','unequal and equal header comparisons'],
  emulator_executed=False,checker_sha256=sha(Path(__file__).read_bytes()))
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(sha(a.report.read_bytes()))

if __name__=='__main__':main()
