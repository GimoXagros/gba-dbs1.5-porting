"""Small author Lua54 gate for the new readonly natural-counter1 probe."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import types

import verify_wsc_shoot_short_hard as lua_host

ROOT=Path(__file__).resolve().parents[1]
LUA=ROOT/'tools/bizhawk_probe_gba_shoot_counter1.lua'
ROM='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
sha=lambda b:hashlib.sha256(b).hexdigest().upper()

CHECK=r'''
local function test(mode)
 local out,reference='W:/build/counter1-author','W:/build/counter1-reference'
 local m={ram={},hooks={},files={},inputs={},saves={},callback=false,frame=69935,advances=0,loads=0,exits=0}
 function m.put(a,v,n)for i=0,(n or 2)-1 do m.ram[a+i]=(v>>(8*i))&255 end end
 function m.get(a,n)local v=0;for i=0,(n or 2)-1 do v=v|((m.ram[a+i]or 0)<<(8*i))end;return v end
 local P,Q,AUX,S,D,IRQ,FINAL=0x02011710,0x02011828,0x02011940,0x020121E8,0x020120D0,0x086FFE10,0x086FFEBC
 for _,a in ipairs({P-0x18,Q-0x18,AUX-0x18,S,D})do m.put(a+0x10,2)end
 for _,p in ipairs({{P,0x0835620C},{Q,0x085BF200},{AUX,0x085BF600},{S,0x085CD510},{D,0x08352268},{D+4,0xFFFFF000},{Q+0x28,AUX},{AUX+0x18,P},{AUX+0x28,Q},{0x0300489C,P},{0x030048A0,Q},{0x03004D3C,AUX},{0x0300133C,D},{0x03001344,D},{0x03004518,D},{0x030012E0,IRQ}})do m.put(p[1],p[2],4)end
 m.put(0x03002310,7);m.put(0x0300231E,11,1);m.put(0x0300450A,0x1486)
 m.put(0x03004712,141);m.put(0x03004714,145);m.put(0x03004716,3)
 m.config={output=out,checkpoint_dir=reference,probe_sha256='ROM'}
 local regions={IWRAM=0x8000,EWRAM=0x40000,VRAM=0x18000,PALRAM=0x400,OAM=0x400,ROM=0x800000}
 local names={IWRAM='iwram',EWRAM='ewram',VRAM='vram',PALRAM='palette',OAM='oam'}
 local fixture={[reference..'/19-irq-final-install.State']='PKfixture'}
 for d,n in pairs(names)do fixture[reference..'/19-irq-final-install-'..n..'.bin']='opaque-'..d end
 local env=setmetatable({},{__index=_G})
 local function absolute(a,n,d)
  if d=='System Bus'then assert(a>=0x04000000 and a+n<=0x04000400);return a end
  local bases={IWRAM=0x03000000,EWRAM=0x02000000}
  assert(a>=0 and a+n<=regions[d]);return assert(bases[d])+a
 end
 env.userdata={get=function(k)return m.config[k]end,clear=function()m.config={}end,set=function(k,v)m.config[k]=v end}
 env.memory=setmetatable({getmemorydomainsize=function(d)return assert(regions[d])end,
  read_u8=function(a,d)return m.get(absolute(a,1,d),1)end,read_u16_le=function(a,d)return m.get(absolute(a,2,d),2)end,read_u32_le=function(a,d)return m.get(absolute(a,4,d),4)end,
  read_bytes_as_binary_string=function(a,n,d)assert(not m.callback,'callbackbulkforbidden');assert(a==0 and n==regions[d]);return 'opaque-'..d end},
  {__index=function(_,k)error('unapprovedmemoryAPI:'..k)end})
 env.mainmemory=setmetatable({},{__index=function(_,k)error('mainmemoryforbidden:'..k)end})
 env.io={open=function(path,access)
  assert(not m.callback,'callbackIOforbidden')
  if access=='rb'then local value=assert(fixture[path]);return{read=function()return value end,close=function()end}end
  assert(access=='wb'and path:sub(1,#out+1)==out..'/');m.files[path]=''
  return{write=function(_,b)m.files[path]=m.files[path]..b;return true end,close=function()end}
 end}
 env.savestate={load=function(path,suppress)assert(not m.callback and m.loads==0 and not next(m.hooks)and suppress and fixture[path]);m.loads=1;m.config={output='stale'};return true end,
  save=function(path,suppress)assert(not m.callback and suppress);m.saves[#m.saves+1]=path;m.files[path]='PKsaved';return true end}
 env.joypad={set=function(keys)
  assert(not m.callback);local count=0;for _,v in pairs(keys)do count=count+1;assert(v==false,'everyinputneutral')end;assert(count==11);m.inputs[#m.inputs+1]=true
 end}
 env.client={exit=function()m.exits=m.exits+1 end}
 m.regs={};for i=0,15 do m.regs['R'..i]=0 end
 function m.fire(a,r)
  for k,v in pairs(r or {})do m.regs[k]=v end;m.regs.R15=a+4
  m.callback=true;local ok,err=pcall(assert(m.hooks[a]));m.callback=false;assert(ok,err)
 end
 env.event={on_bus_exec=function(fn,a,label)assert(m.loads==1 and not m.hooks[a]);m.hooks[a]=fn end}
 local function compare(line,target,index,offset)
  m.put(0x04000004,(line+8)<<8);m.put(0x04000006,line+8)
  m.fire(0x086FFE48,{R0=line,R1=target,R4=0x03004710,R5=index,R6=offset})
 end
 env.emu=setmetatable({getsystemid=function()return 'GBA'end,framecount=function()return m.frame end,getregisters=function()local r={};for k,v in pairs(m.regs)do r[k]=v end;return r end,
  frameadvance=function()
   assert(not m.callback);m.advances=m.advances+1;assert(m.advances<=200);m.frame=m.frame+1
   if m.advances==1 then
    if mode=='midcycle-ignore'then
     m.put(0x03004714,1);m.put(0x03004716,0);compare(1,1,0,0);m.fire(0x086FFE50)
    else compare(145+7,145+7,3,7)end
    return
   end
   if mode=='never-target'or m.advances~=2 then return end
   m.put(0x03004712,1);m.put(0x04000006,1)
   if mode=='wrong-owner'then m.put(0x03001344,0,4)end
   m.fire(0x086FF75C,{R0=IRQ,R14=0x086FF6EC})
   if mode=='wrong-owner'then return end
   m.put(0x03004712,0);m.put(0x03004714,1);m.put(0x03004716,0)
   m.fire(0x085E74D8,{R5=0x03004710})
   m.put(0x04000006,8);m.fire(IRQ)
   if mode=='missing-first'then m.fire(0x086FFE50,{R0=1,R1=1,R5=0});return end
   if mode=='deadline-late'then compare(2,1,0,0);return end
   compare(0,1,0,0)
   for i,offset in ipairs({0,2,4,7,10,13,17,21})do
    local index=i-1;local line=i+offset
    compare(line,line,index,offset);m.fire(0x086FFE50)
    m.put(0x03004714,i+1);m.put(0x03004716,i);m.fire(0x086FFE74,{R5=i})
   end
   m.fire(0x086FFE84,{R0=0x030012E0,R1=FINAL,R5=8});m.put(0x030012E0,FINAL,4)
   m.put(0x04000006,38);m.fire(FINAL)
  end},{__index=function(_,k)error('unapprovedemuAPI:'..k)end})
 assert(load(wrapper_source,'@actual-counter1-probe','t',env))()
 assert(m.loads==1 and m.exits==1 and #m.inputs==m.advances+1)
 local done=assert(m.files[out..'/counter1-done.txt']);assert(not m.files[out..'/counter1-error.txt'],m.files[out..'/counter1-error.txt'])
 local trace=assert(m.files[out..'/counter1-trace.txt'])
 if mode=='positive'or mode=='midcycle-ignore'then
  assert(done=='earliest-counter1-irq-complete\n'and m.advances==2)
  local function count(kind)local n=0;for s in trace:gmatch('[^\n]+')do if s:find('kind='..kind..' ',1,true)then n=n+1 end end;return n end
  assert(count('IRQ-match')==8 and count('IRQ-match-stored')==8 and count('IRQ-final-called')==1)
  assert(m.files[out..'/counter1-summary.txt']:find('first_compare_VCOUNT=8 first_compare_line=0',1,true))
  assert(not trace:find('core=69936 kind=IRQ-',1,true),'oldcycleignored')
 else assert(done:find('failure:',1,true)==1 and not trace:find('kind=IRQ-final-called',1,true),'negativecannotcomplete')end
 if mode=='never-target'then assert(m.advances==200 and done=='failure:target-first-compare-not-observed\n')end
 if mode=='wrong-owner'then assert(done=='failure:display-owner\n')end
 if mode=='deadline-late'then assert(done=='failure:first-deadline-late\n')end
 if mode=='missing-first'then assert(done=='failure:missing-or-wrong-first-compare\n')end
 local record_count=0;for _ in trace:gmatch('[^\n]+')do record_count=record_count+1 end;assert(record_count<=100)
 assert(m.files[out..'/restored.State']and m.files[out..'/final.State'])
 return done
end
for _,mode in ipairs({'positive','missing-first','deadline-late','midcycle-ignore','wrong-owner','never-target'})do test(mode)end
'''.replace("'ROM'", "'"+ROM+"'",1)


def check(source):
    helper=types.FunctionType(lua_host.lua_check.__code__,dict(lua_host.__dict__,CHECK=CHECK),argdefs=lua_host.lua_check.__defaults__)
    helper(source,'','')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    source=LUA.read_text(encoding='utf8');assert not re.search(r'(?:memory|mainmemory)\.write|emu\.setregister',source)
    check(source)
    rejected=[]
    for label,before,after in (
        ('late-first-accepted','r.R0<=1 and target.VCOUNT<=9','true'),
        ('missing-compare-accepted','compared and target.first_compare and not pending','not pending'),
        ('wrong-display-owner-accepted','owner()and w(0x0300450A)&0x400~=0','true'),
    ):
        assert source.count(before)==1
        try:check(source.replace(before,after))
        except ValueError:rejected.append(label)
        else:raise AssertionError('control survived:'+label)
    report=dict(status='COUNTER1_READONLY_PROBE_AUTHOR_LUA54_PASS',lua_sha256=sha(LUA.read_bytes()),verifier_sha256=sha(Path(__file__).read_bytes()),cases=['counter1-positive','missing-first','deadline-late','midcycle-ignore','wrong-owner','200-frame-never-target'],semantic_controls_rejected=rejected,bound=200,all_buttons_false=True,maximum_scalar_records=100,all_bulk_and_State_and_IO_outside_callbacks=True,new_guest_writes=False,actual_target1_hardware_timing_claim=False,emulator_launched=False,old_terminal_suite_rerun=False)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS actualLua54 readonlycounter1/sixaffectedcases/threecontrols/noemulator')


if __name__=='__main__':main()
