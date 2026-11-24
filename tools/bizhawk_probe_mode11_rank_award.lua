-- Genuine campaign name acceptance, then a separate process loads only its EEPROM.
local out=assert(userdata.get("output"))
local phase=assert(userdata.get("phase"))
local result_pc=tonumber(assert(userdata.get("result_pc")))
local function dump(name,bytes)local f=assert(io.open(out.."/"..name,"wb"));f:write(bytes);f:close()end
local function log(msg)local f=assert(io.open(out.."/trace.txt","a"));f:write(emu.framecount().." "..msg.."\n");f:close()end
local function iw(n)return memory.read_u16_le(n,"IWRAM")end
local function ew(n)return memory.read_u32_le(n,"EWRAM")end
local function eb(n)return memory.read_u8(n,"EWRAM")end
local function task(cb)
 for i=0,51 do local h=0x10000+i*0x118
  if eb(h+16)&2~=0 and ew(h)==cb then return h end
 end
end
local function frame(key)
 local keys={}
 for _,k in ipairs({"A","B","Start","Select","Up","Down","Left","Right","L","R","Power"})do keys[k]=k==key end
 joypad.set(keys);emu.frameadvance()
end
local function capture(name)
 client.screenshot(out.."/"..name..".png")
 for _,d in ipairs({"EWRAM","IWRAM","VRAM","PALRAM","OAM"})do
  dump(name.."-"..d..".bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(d),d))
 end
end
local ok,err=pcall(function()
 client.speedmode(800)
 dump("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 if phase=="award"then
  assert(savestate.load(out.."/earned-campaign.State",true))
  assert(emu.framecount()==225116 and iw(0x2310)==11)
  local rank, count=nil,0
  event.on_bus_exec(function()
   local regs=emu.getregisters()
   rank=regs.R0;count=count+1
   log(string.format("award score=%d difficulty=%d result=%04X count=%d",iw(0x3d02),memory.read_u8(0x231f,"IWRAM"),rank,count))
  end,result_pc,"native-earned-tag")
  local saved=false
  for i=0,12000 do
   local m=iw(0x2310)
   if rank and not saved then
    assert(rank==0x800a and count==1);capture("earned");assert(savestate.save(out.."/earned.State",true));saved=true
   end
   if saved and m==3 then
    assert(count==1);capture("returned-title");assert(savestate.save(out.."/earned-title.State",true));log("successful-title-return")
    return
   end
   frame(m==11 and i%30<4 and "A" or nil)
  end
  error("positive score callback not reached")
 end
 assert(phase=="cold" and emu.framecount()<4)
 local entered,exiting=nil,false
 for i=0,12000 do
  local m=iw(0x2310)
  if m==22 then
   local h=task(0x08f7a71c)
   if h then
    if not entered then entered=i end
    if i==entered+90 then
     assert(eb(h+0x18+26)==4 and memory.read_u16_le(h+0x18+24,"EWRAM")==1,"special counter view")
     capture("cold-special");log("rank10=1 special branch=4")
    end
    if i>=entered+95 and i%20==0 then exiting=true;frame("B") else frame() end
   else frame() end
  elseif exiting and (m==3 or m==20)then
   capture("cold-exit");log("viewer exit mode="..m);return
  else
   local k=nil
   if m==3 then
    if task(0x08090c7c) and i>600 then k="Start" end
    local t=task(0x08dfe048)
    if t then
     local tree,idx=eb(t+28),eb(t+29)
     if tree==0 then k=idx==4 and "A" or "Down"
     elseif tree==2 then k=idx==0 and "A" or "Up" end
    end
   end
   frame(i%21==0 and k or nil)
  end
 end
 error("cold viewer route timed out")
end)
if not ok then log(tostring(err))end
dump("done.txt",ok and phase.."-pass" or tostring(err))
client.exit()
