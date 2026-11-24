-- Genuine campaign name acceptance, then a separate process loads only its EEPROM.
local out=assert(userdata.get("output"))
local phase=assert(userdata.get("phase"))
local result_pc=tonumber(assert(userdata.get("result_pc")))
local controller=tonumber(assert(userdata.get("controller")))
local function dump(name,bytes)local f=assert(io.open(out.."/"..name,"wb"));f:write(bytes);f:close()end
local function log(msg)local f=assert(io.open(out.."/trace.txt","a"));f:write(emu.framecount().." "..msg.."\n");f:close()end
local function iw(n)return memory.read_u16_le(n,"IWRAM")end
local function ew(n)return memory.read_u32_le(n,"EWRAM")end
local function eb(n)return memory.read_u8(n,"EWRAM")end
local function audio_state(label)
 local function w(addr)return memory.read_u32_le(addr,"IWRAM")end
 log(string.format("audio-state %s p0=%08X/%08X p3=%08X/%08X",label,
  w(0x6b40),w(0x6b44),w(0x6c90),w(0x6c94)))
end
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
  event.on_bus_exec(function()audio_state("before-number-stop")end,0x08E09518,"reel-stop-before")
  event.on_bus_exec(function()audio_state("after-number-stop")end,0x08E0952C,"reel-stop-after")
  event.on_bus_exec(function()
   local regs=emu.getregisters()
   log(string.format("card-cue %02X priority=%d",regs.R0,regs.R1))
  end,0x08EA4ED4,"source-card-cue")
  event.on_bus_exec(function()
   if rank then
    local regs=emu.getregisters()
    log(string.format("native-audio %02X priority=%d delay=%d",regs.R8,regs.R9,regs.R10))
   end
  end,0x080D15C0,"payment-in-game-audio")
  local palwrites={}
  event.on_bus_write(function(a,v,f)
   local n=emu.framecount()
   if n>=226343 and n<=226346 then
    local pc=emu.getregisters().R15
    local k=n.."/"..pc.."/"..v
    if not palwrites[k]then log(string.format("palette0 %08X value=%04X",pc,v));palwrites[k]=true end
   end
  end,0x05000000,"card-backdrop")
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
   local h=task(controller)
   local key=nil
   if h then
    local p=h+0x18
    local phase=memory.read_u16_le(p+2,"EWRAM")
    local elapsed=memory.read_u16_le(p,"EWRAM")
    if phase==0 and elapsed==390 then capture("score")end
    if phase==0 and (elapsed==75 or elapsed==105 or elapsed==250 or elapsed==317 or elapsed==320)then
     audio_state("score-"..elapsed)
    end
    if phase==0 and elapsed==30 then capture("score-fade-in")end
    if phase==0 and elapsed==690 then capture("score-fade-out")end
    if phase==1 and elapsed==140 then capture("card")end
    if phase==1 and elapsed==420 then capture("fighter-arrival")end
    if phase==2 and elapsed==100 then capture("celebration")end
    if phase>=3 then
     local cursor=eb(p+12)
     local ch=eb(p+8+cursor)
     if elapsed==25 then capture("editor") end
     if cursor==3 and eb(p+15)==0 and elapsed%12==0 then capture("name-confirmation")end
     if elapsed%12==0 and elapsed>30 and eb(p+15)==0 then
      local want=({66,67,68,40})[cursor+1]
      assert(want and elapsed<2500,"name cursor stalled")
      if ch==want then key="A"
      elseif ch<want then key="Right"
      else key="Left" end
      log("name "..cursor.." byte="..ch.." key="..key)
     end
     if eb(p+15)==1 and eb(p+14)==35 then capture("edited") end
    end
   elseif m==11 and i%30<4 then key="A" end
   frame(key)
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
     assert(memory.read_bytes_as_binary_string(h+0x18,4,"EWRAM")== "BCD"..string.char(0),"persisted name")
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
