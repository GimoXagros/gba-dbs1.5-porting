local out=assert(userdata.get("output"))
local function w(a)return memory.read_u16_le(a,"IWRAM")end
local function write(n,s,mode)local f=assert(io.open(out.."/"..n,mode or "wb"));f:write(s);f:close()end
local function log(s)write("rank-start.txt",emu.framecount().." "..s.."\n","ab")end
local function cap(n)
 client.screenshot(out.."/"..n..".png")
 for _,d in ipairs({"IWRAM","EWRAM","VRAM","OAM","PALRAM"})do write(n.."-"..d..".bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(d),d))end
end
local function run()
 assert(savestate.load(out.."/campaign.State",true) and emu.framecount()==202221)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 local once={}
 for _,a in ipairs({0x080bf754,0x080c0858,0x080c08bc,0x080c0c70,0x080c0d28,0x080c0e04})do
  event.on_bus_exec(function()
   local r=emu.getregisters()
   if not once[a] or a==0x080bf754 then log(string.format("pc=%08X R0=%08X R3=%08X R5=%08X",a,r.R0,r.R3,r.R5))end
   once[a]=true
  end,a,"name-"..a)
 end
 client.speedmode(800)
 for n=0,13000 do
  local m=w(0x2310)
  if m==3 then assert(once[0x080c0e04] and w(0x2328)==0x3000);cap("permanent-title");assert(savestate.save(out.."/permanent-title.State",true));return end
  if n==180 or n==400 or n==1000 or n==2600 then cap("ending-"..n)end
  if n%150==0 then
   local tasks={}
   for i=0,51 do local h=0x10000+280*i;if memory.read_u8(h+0x10,"EWRAM")&2~=0 then tasks[#tasks+1]=string.format("%08X:%04X",memory.read_u32_le(h,"EWRAM"),memory.read_u16_le(h+0x18,"EWRAM"))end end
   log(string.format("m=%d callbacks=%s event=%04X count=%d keys=%04X",m,table.concat(tasks,","),w(0x3d00),w(0x3cf4),w(0x130a)))
  end
  local k={}
  for _,b in ipairs({"Start","A","B","Up","Down","Left","Right","L","R","Select","Power"})do k[b]=false end
  if n>250 then
   local key="A"
   if n>=1300 and n<1360 or n>=2600 and n<2660 then key="Start"
   elseif n>=1800 and n<1920 then key="Right"
   elseif n>=3000 and n<3080 then key="B" end
   if n%22<2 then k[key]=true end
  end
  joypad.set(k);emu.frameadvance()
 end
 error("name-entry observation exhausted")
end
local ok,er=pcall(run);if not ok then log(tostring(er))end
write("collection-done.txt",ok and "permanent-award-title" or "failure");client.exit()
