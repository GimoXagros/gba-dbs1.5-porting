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
 assert(savestate.load(out.."/campaign.State",true))
 local initial=emu.framecount();assert(initial==187835 and readw(0x2328)==0)
 client.speedmode(800)
 assert(initial)
 driver=replace(driver,"6F7B7D942BCDE6F9EFC223150D54672D352606988C1C31471799EFD7C16FA116",hash)
 driver=replace(driver,'first==209311 and memory.read_u16_le(0x2328,"IWRAM")==16','first=='..initial..' and memory.read_u16_le(0x2328,"IWRAM")==0')
 driver=replace(driver,"for frame=0,35000 do","for frame=0,150000 do")
 driver=replace(driver,'read(0x03001132,1)&16~=0','read(0x03001132,1)&48==48')
 driver=replace(driver,'read(0x03002329,1)&16~=0 and read(0x03002328,1)&16==0','read(0x03002329,1)&48==48 and read(0x03002328,1)&48==0')
 driver=replace(driver,"joypad.set(keys);emu.frameadvance()",[[
  if not searched and m==7 and st==11 and obs.live() then
   local player,boss=obs.pair(true)
   if player and obs.positive(w(player+0x64)) and obs.positive(w(boss+0x64)) then
    if not assisted then obs.boss11(player,boss);assisted=true end
    obs.flush(function(e)write("assist-ledger.txt",e.."\n","ab")end)
    local restore=out.."/after-single-hp-assist.State"
    assert(savestate.save(restore,true));local won=false
    for attempt=0,39 do
     assert(savestate.load(restore,true))
     log("ordinary-control attempt="..attempt)
     local previousKeys={}
     for step=0,11000 do
      local p,q=obs.pair(true)
      if not p or not obs.live() or not obs.positive(w(p+0x64)) then break end
      if w(q+0x64)==0 or w(q+0x64)>=0x8000 then break end
      local dx=signed(w(q+0x34))-signed(w(p+0x34))
      local dy=signed(w(q+0x36))-signed(w(p+0x36))
      local px=signed(w(p+0x34));local right=w(p+0xB4)&0x4000~=0
      local target=({4352,5400,3100,4100,3600})[attempt%5+1]
      local sx=step<100+attempt%7*20 and target-px or dx
      local limit=({320,700,160,480,880})[attempt%5+1]
      local k={Right=sx>limit,Left=sx< -limit}
      if math.abs(dx)>95 and (dx>0)~=right and not previousKeys.Left and not previousKeys.Right then k.Right=dx>0;k.Left=dx<0 end
      local phase=attempt//5
      if phase==0 or phase==1 then
       k.B=step%(31+attempt%5*4)<4
       k.A=phase==1 and dy<=-256 and step%70<6
      elseif phase==2 or phase==3 then
       k.B=step%17<3;k.A=phase==3 and step%61<6
       k.Up=step%100<45
      elseif phase==4 or phase==5 then
       k.A=dy<256 and step%53<9;k.B=step%23<3
       k.Down=phase==5 and step%91<35
      else
       k.B=step%43<8;k.A=step%71<13
       k.Up=phase==7 and step%120<65
      end
      previousKeys=k;joypad.set(k);emu.frameadvance()
      if w(q+0x64)==0 or w(q+0x64)>=0x8000 then
       log("HP1 became zero through controller attempt="..attempt.." step="..step)
       assert(savestate.save(out.."/genuine-hit.State",true))
       won=true;break
      end
     end
     if won then break end
    end
    assert(won,"ordinary controller search exhausted")
    searched=true
   end
  end
  joypad.set(keys);emu.frameadvance()]])
 driver=replace(driver,"local lastsave=false","local lastsave,searched=false,false")
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
