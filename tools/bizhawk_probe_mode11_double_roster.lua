-- Earn a SPECIAL tag, start another campaign and observe both ending award portraits.
local out=assert(userdata.get("output"))
local hash=assert(userdata.get("probe_sha256"))
local source=assert(io.open("W:/tools/bizhawk_probe_terminal_hidden_promotion_v91.lua","rb"))
local driver=source:read("*a"):gsub("\r\n","\n");source:close()
local settings={}
for _,key in ipairs({"output","probe_sha256","score_authorization","boss_authorization"})do settings[key]=assert(userdata.get(key))end
local function log(s)local f=assert(io.open(out.."/rank-start.txt","a"));f:write(emu.framecount()," ",s,"\n");f:close()end
local function readw(offset)return memory.read_u16_le(offset,"IWRAM")end
local function eb(o)return memory.read_u8(o,"EWRAM")end
local function ed(o)return memory.read_u32_le(o,"EWRAM")end
local function task(cb)
 for s=0,51 do local h=0x10000+s*0x118;if eb(h+16)&2~=0 and ed(h)==cb then return h end end
end
local function press(key)
 local keys={};for _,k in ipairs({"Start","A","B","Up","Down","Left","Right","L","R","Select","Power"})do keys[k]=k==key end
 joypad.set(keys);emu.frameadvance()
end
local function replace(text,old,new)
 local a,b=text:find(old,1,true);assert(a and not text:find(old,b+1,true))
 return text:sub(1,a-1)..new..text:sub(b+1)
end
local function snapshot(name)
 client.screenshot(out.."/"..name..".png")
 for _,d in ipairs({"IWRAM","EWRAM","VRAM","OAM","PALRAM"})do
  local f=assert(io.open(out.."/"..name.."-"..d..".bin","wb"))
  f:write(memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(d),d));f:close()
 end
end
local function run()
 assert(savestate.load(out.."/pre-ending.State",true))
 assert(emu.framecount()==101990 and readw(0x2310)==13 and readw(0x2328)==0 and readw(0x2332)==2311)
 client.speedmode(800)
 local rank,earned,initial=false,false,nil
 event.on_bus_exec(function()
  local r=emu.getregisters()
  if not rank then assert(r.R0==0x800a);rank=true;log("initial earned SPECIAL 10") end
 end,148704292,"earned-special")
 for n=0,8000 do
  local m=readw(0x2310);local key=nil
  if m==11 then assert(readw(0x2328)==0);if n%30<4 then key="A"end
  elseif m==3 then
   if not earned then assert(rank);snapshot("rank-title");assert(savestate.save(out.."/rank-title.State",true));earned=true;log("returned both roster flags zero") end
   if task(0x08090c7c) then key="Start" end
   local h=task(0x08dfe048)
   if h then assert(eb(h+28)<=1 and eb(h+29)==0);key="A"end
   if n%18~=0 then key=nil end
  elseif m==4 or m==5 or m==6 then if n%18==0 then key="A"end
  elseif m==7 then
   assert(earned and readw(0x2328)==0)
   initial=emu.framecount();assert(savestate.save(out.."/campaign.State",true));log("new campaign, no roster flags");break
  else assert(m==13 or m==20,"unexpected pre-campaign mode "..m) end
  press(key)
 end
 assert(initial)
 driver=replace(driver,"6F7B7D942BCDE6F9EFC223150D54672D352606988C1C31471799EFD7C16FA116",hash)
 driver=replace(driver,'first==209311 and memory.read_u16_le(0x2328,"IWRAM")==16','first=='..initial..' and memory.read_u16_le(0x2328,"IWRAM")==0')
 driver=replace(driver,"for frame=0,35000 do","for frame=0,150000 do")
 driver=replace(driver,'read(0x03001132,1)&16~=0','read(0x03001132,1)&48==48')
 driver=replace(driver,'read(0x03002329,1)&16~=0 and read(0x03002328,1)&16==0','read(0x03002329,1)&48==48 and read(0x03002328,1)&48==0')
 local rows,draws={},0
 event.on_bus_exec(function()
  local r=emu.getregisters();local id=(r.R5-0x084a80f8)//32
  assert(id==11 or id==12);rows[id]=true;log("display portrait ID="..id.." slot="..r.R3)
 end,0x080bf754,"live-award-roster-row")
 driver=replace(driver,"if m==9 then capture",[[if m==11 and award_portraits_ready() then
    if capture_visible_award() then log("two portraits captured")end
   end
   if m==9 then capture]])
 local env=setmetatable({
   userdata={get=function(k)return settings[k]end},
   award_portraits_ready=function()return rows[11] and rows[12]end,
   capture_visible_award=function()
    draws=draws+1
    if draws==60 then snapshot("two-portraits");return true end
   end
 },{__index=_ENV})
 assert(load(driver,"@source-verified-campaign-driver","t",env))()
end
local ok,err=pcall(run)
if not ok then log(tostring(err));local f=assert(io.open(out.."/collection-done.txt","w"));f:write("failure");f:close();client.exit()end
