"""Independent bounded AI observer delta, hook ABI and first-bad-target gate."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua

ROOT=Path(__file__).resolve().parents[1]
PIN='4A2AE9672BAF2C1BC53EE3B8A6F891DCB66B7EE77C0163966CA2F123F15C4C30'
ROM='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
OPS={0x080C6D60:0xE350000B,0x080C6D70:0xE0010190,0x080C6D7C:0xE19100B8,0x080C6D84:0xE1C800B2,
     0x080C6EB0:0xE3A00000,0x080C65AC:0xE92D4020,0x080C65EC:0xE7989105,0x080C65F0:0xE12FFF19}
CHECK=r'''
local env=setmetatable({},{__index=_G})
local ram,regs,hooks,buses,files,context={},{},{},{},{},nil
for i=0,15 do regs['R'..i]=0 end;regs.CPSR=0
local function put(a,v,n)for i=0,n-1 do ram[a+i]=(v>>(8*i))&255 end end
local function rd(a,n)
 local v=0;for i=0,n-1 do
  local b=ram[a+i]
  if b==nil and a+i>=0x080C6500 and a+i<0x080C6F00 then b=romblock:byte(a+i-0x080C6500+1)end
  v=v|((b or 0)<<(8*i))
 end;return v
end
local function denied(_,key)error('forbidden '..key)end
local base={ROM=0x08000000,EWRAM=0x02000000,IWRAM=0x03000000}
env.memory=setmetatable({read_u8=function(a,d)return rd(a+base[d],1)end,
 read_u16_le=function(a,d)return rd(a+base[d],2)end,read_u32_le=function(a,d)return rd(a+base[d],4)end},{__index=denied})
for _,name in ipairs({'mainmemory','joypad','client','savestate'})do env[name]=setmetatable({},{__index=denied})end
env.userdata={get=function(k)if k=='output'then return 'W:/build/ai-delta-fixture'end;assert(k=='probe_sha256');return romhash end}
env.emu=setmetatable({framecount=function()return 20165 end,getregisters=function()return regs end},{__index=denied})
env.event={on_bus_exec=function(fn,at,name)assert(opcodes[at]and not hooks[at]);hooks[at]=fn end,
 on_bus_write=function(fn,at,name)assert(at==0x03003D50 and not buses[at]);buses[at]=fn end}
env.io={open=function(path,mode)
 if mode=='rb'then assert(path=='W:/tools/bizhawk_probe_type8_corrected_campaign.lua');return{read=function()return corrected end,close=function()end}end
 assert(mode=='wb'and path=='W:/build/ai-delta-fixture/ai-producer-provenance.txt'and not files[path])
 local f={data='',closed=false};files[path]=f
 function f:write(s)assert(not self.closed);self.data=self.data..s;return true end
 function f:close()assert(not self.closed);self.closed=true;return true end
 return f
end}
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)
end
env.load=function(code,name,mode,ctx)
 assert(name=='@frozen-corrected-campaign-ai-provenance'and mode=='t'and not context)
 assert(code==replace(corrected,'return replace(parent,OLD,NEW)end','return instrument_ai_campaign(replace(parent,OLD,NEW))end'))
 context=ctx;return function()end
end
assert(load(observer,'@independent-AI-delta','t',env))()
local binding=' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
local marker='  local f=assert(io.open(out.."/campaign-complete-done.txt","w"))'
local want=replace(replace(parent,binding,binding..'\n attach_ai_probe(observer)'),marker,'  finish_ai_probe()\n'..marker)
assert(context.instrument_ai_campaign(parent)==want,'only two effective parent insertions')
local failures={};local api={stopped=function()return #failures>0 end,fail=function(reason,detail,r)failures[#failures+1]={reason,detail,r.R15}end}
context.attach_ai_probe(api)
local n=0;for _ in pairs(hooks)do n=n+1 end;assert(n==8)
local function fire(at,changes)
 for k,v in pairs(changes or{})do regs[k]=v end;regs.R15=at+4;hooks[at]()
end
put(0x0300231E,1,1);fire(0x080C6D60,{R0=14})
put(0x0300231E,9,1);put(0x0300231C,14,1);put(0x0300232E,2,1);put(0x03002310,4,2)
fire(0x080C6D60,{R0=14}) -- Initialization must not require an active actor pair.
fire(0x080C6D70,{R0=14,R1=17})
fire(0x080C6D7C,{R1=238,R8=0x080C6C7C})
fire(0x080C6D84,{R8=0x03004D88,R0=rd(0x080C6D6A,2)})
put(0x03004D8A,rd(0x080C6D6A,2),2)
fire(0x080C6EB0)
put(0x03002310,7,2);put(0x0300489C,0x02011710,4);put(0x030048A0,0x02011828,4)
for _=1,140 do fire(0x080C65AC,{R4=0x02011828})end
local function selector(n)
 buses[0x03003D50](0x03003D50,n,0x2000);put(0x03003D50,n,2)
 fire(0x080C65EC,{R8=0x080C65F4,R5=n})
 fire(0x080C65F0,{R9=rd(0x080C65F4+n*4,4)})
end
selector(2);assert(#failures==0,'valid native target continues')
selector(15);assert(#failures==1 and failures[1][1]=='first-invalid-ai-collider-target')
assert(failures[1][2]:find('slot=080C6630 word=E3A00000 target=E3A00000',1,true))
assert(failures[1][3]==0x080C65F4,'reported PC is before-instruction PC+4')
assert(regs.R9==0xE3A00000,'observer does not inhibit or redirect target')
context.finish_ai_probe()
local f=files['W:/build/ai-delta-fixture/ai-producer-provenance.txt'];assert(f.closed)
assert(f.data:find('serial=151 ',1,true))
assert(f.data:find('first seq=1 core=20165 kind=raw-id mode=4',1,true))
assert(f.data:find('src=080C6D6A halfword=E92D row17=2DE91110A0E3900101E0C4839FE5008088',1,true))
assert(f.data:find('dst=03004D8A prior=0000 value=E92D',1,true))
local first,tail=0,0;for line in f.data:gmatch('[^\n]+')do
 if line:find('^first seq=')then first=first+1 elseif line:find('^seq=')then tail=tail+1 end
end
assert(first==6 and tail==128,'first facts survive ring rollover')
assert(not pcall(context.finish_ai_probe),'close once')
'''

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 paths=['bizhawk_probe_ai_producer_provenance.lua','bizhawk_probe_type8_corrected_campaign.lua','bizhawk_probe_campaign_complete.lua']
 data=[(ROOT/'tools'/n).read_bytes()for n in paths]
 assert list(map(sha,data))==[PIN,'844C896950AFFDB42B255CB843AEE8F2354A61237E0997506D0A74EAC81B00EC','F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF']
 assert not re.search(rb'\b(?:memory|mainmemory)\.write|\b(?:joypad|savestate|client)\.|\bemu\.(?!framecount|getregisters)',data[0])
 rom=(ROOT/'build/character-type8-tables-r2-20261117/component.gba').read_bytes();assert sha(rom)==ROM
 assert all(struct.unpack_from('<I',rom,at-0x08000000)[0]==op for at,op in OPS.items())
 table=struct.unpack_from('<16I',rom,0xC65F4)
 assert table[:12]==(0x080C669C,0x080C66A0,0x080C66EC,0x080C6728,0x080C6798,0x080C6770,0x080C679C,0x080C67D8,0x080C6630,0x080C6640,0x080C6668,0x080C669C)
 assert table[12:]==(0x03003D68,0x03004D88,0x03003D50,0xE3A00000)
 setup='\n'.join(f'local {n}={lua.quote(b)}'for n,b in zip(('observer','corrected','parent'),data))+'\n'
 setup+=f'local romhash="{ROM}"\nlocal romblock='+lua.quote(rom[0xC6500:0xC6F00])+'\n'
 setup+='local opcodes={'+','.join(f'[{k}]={v}'for k,v in OPS.items())+'}\n'
 runner=lua.host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+CHECK))('','','')
 result=dict(status='AI_PRODUCER_DELTA_INDEPENDENT_PASS',observer_sha256=PIN,rom_sha256=ROM,exec_hooks=8,write_hooks=1,
             initializer_without_active_pair=True,exact_parent_insertions=2,model_events=151,initial_rows_retained=6,ring_rows=128,
             valid_target_continues=True,invalid_target_observed_before_BX=True,guest_target_unchanged=True,
             input_or_guest_writes_added=False,actual_runtime_provenance=False,checker_sha256=sha(Path(__file__).read_bytes()))
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
