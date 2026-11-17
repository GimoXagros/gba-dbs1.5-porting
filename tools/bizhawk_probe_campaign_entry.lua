-- Observe a fresh ordinary campaign without changing game memory or input.
local out=assert(userdata.get("output"))
local file=assert(io.open(out.."/campaign-entry.txt","wb"))
local function read(a,n)
 local domain,offset
 if a>=0x02000000 and a+n<=0x02040000 then domain,offset="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then domain,offset="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then domain,offset="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(offset,domain) end
 if n==2 then return memory.read_u16_le(offset,domain) end
 return memory.read_u32_le(offset,domain)
end
local function emit(s)assert(file:write(s.."\n"));file:flush()end
local counts={producer=0,public=0,legacy=0}
local first,stable,ready,streak= nil,0,nil,nil
local function state()
 return string.format("core=%d mode=%d progress=%d row=%d stage=%d cpu=%d color=%d p1id=%d flags=%02X",
  emu.framecount(),read(0x03002310,2),read(0x0300232E,1),read(0x0300232F,1),
  read(0x0300231E,1),read(0x0300231C,1),read(0x0300231D,1),read(0x0300231A,1),read(0x0300232A,1))
end
local function hook(at,word,label,check)
 assert(read(at,4)==word,"campaign observation instruction")
 event.on_bus_exec(function()
  if read(0x0300232E,1)~=0 or (label~="producer" and not first) then return end
  local r=emu.getregisters()
  assert(read(0x0300231E,1)==8 and read(0x0300231C,1)==13,"first source campaign stage and CPU")
  assert(read(0x0300232F,1)<8 and read(0x0300231A,1)==0,"ordinary initial configuration")
  check(r)
  counts[label]=counts[label]+1
  first=first or emu.framecount()
  if counts[label]<=16 then emit(string.format("event=%s %s r0=%08X r4=%08X r8=%08X lr=%08X",label,state(),r.R0,r.R4,r.R8,r.R14))end
 end,at,"campaign-entry-"..label)
end
hook(0x0808B70C,0xE8BD4013,"producer",function(r)assert(r.R4==0x03002310 and read(0x0300231D,1)==0,"producer owner/color")end)
hook(0x08582C70,0xE12FFF1E,"public",function(r)assert(r.R8==0x03002310 and r.R0==8,"public physical stage")end)
hook(0x08584A38,0x012FFF1E,"legacy",function(r)assert(r.R8==0x03002310 and r.R0==0,"legacy stage8 analog")end)
local function active(p)
 return p>=0x02010018 and p<0x02010018+52*0x118 and (p-0x02010018)%0x118==0
  and (read(p-8,2)&2)~=0 and read(p+0x14,4)==p
end
local function observe(capture)
 if not first then return end
 local p,q=read(0x0300489C,4),read(0x030048A0,4)
 local live=read(0x03002310,2)==7 and read(0x0300232E,1)==0 and read(0x0300231E,1)==8
  and read(0x03004502,2)==0 and (read(0x03004529,1)&7)==0
  and active(p) and active(q) and p~=q and read(p+0x18,4)==q and read(q+0x18,4)==p
  and read(p+0x10,1)==0 and read(q+0x10,1)==1 and (read(p+4,2)&15)==0 and (read(q+4,2)&15)==1
  and read(p+0x11,1)==0 and read(q+0x11,1)==13
 if not live then stable=0;streak=nil;return end
 streak=streak or emu.framecount()
 if not ready then ready=emu.framecount();capture("campaign-first-live");emit("event=first-live "..state())end
 stable=stable+1
 if stable==121 then
  assert(counts.producer>0 and counts.public>0 and counts.legacy>0,"actual producer and both consumers")
  capture("campaign-stable-live");emit("event=stable-live "..state().." streak_start="..streak)
  return "campaign-first-stage8-cpu13-observed"
 end
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true);assert(a and not s:find(before,b+1,true),"unique campaign observer boundary")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local f=assert(io.open("W:/tools/bizhawk_probe_result_languages.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,'dump("loaded-rom.bin","ROM",0,0x800000)','dump("loaded-rom.bin","ROM",0,0x1000000)')
source=replace(source,'local limit=userdata.get("frames") or 24000','local limit=math.min(userdata.get("frames") or 14000,14000)')
source=replace(source,' if outcome then break end',' outcome=outcome or campaign_observe(capture)\n if outcome then break end')
source=replace(source,'local f=assert(io.open(out.."/result-done.txt","w"));','campaign_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));')
local env=setmetatable({campaign_observe=observe,campaign_finish=function()
 emit(string.format("summary %s producer=%d public=%d legacy=%d first=%s first_live=%s stable=%d guest_writes=none",state(),counts.producer,counts.public,counts.legacy,tostring(first),tostring(ready),stable));file:close()
end},{__index=_ENV})
emit("start readonly=true ordinary_input=unchanged expected_first_stage=8 expected_cpu=13 stable_boundaries=121")
assert(load(source,"@campaign-first-entry-observation","t",env))()
