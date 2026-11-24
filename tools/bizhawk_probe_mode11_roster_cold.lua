-- Cold boot, enter Ver. 1.5 character selection and scroll to both earned identities.
local out=assert(userdata.get("output"))
local function write(name,data)local f=assert(io.open(out.."/"..name,"wb"));f:write(data);f:close()end
local function log(s)local f=assert(io.open(out.."/trace.txt","a"));f:write(emu.framecount()," ",s,"\n");f:close()end
local function w(a)return memory.read_u16_le(a,"IWRAM")end
local function eb(a)return memory.read_u8(a,"EWRAM")end
local function ed(a)return memory.read_u32_le(a,"EWRAM")end
local function snapshot(name)
 client.screenshot(out.."/"..name..".png")
 for _,region in ipairs({"IWRAM","EWRAM","VRAM","OAM","PALRAM"})do
  write(name.."-"..region..".bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(region),region))
 end
end
local function task(cb)
 for slot=0,51 do local h=0x10000+slot*0x118;if eb(h+16)&2~=0 and ed(h)==cb then return h end end
end
local function cold()
 assert(emu.framecount()<4)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 client.speedmode(800)
 local current,seen,change=nil,{},0
 event.on_bus_exec(function()
  if w(0x2310)==4 then
   local id=emu.getregisters().R1
   assert(id>=0 and id<=14);current=id;change=emu.framecount();log("actual-portrait "..id)
  end
 end,0x084a5c70,"cold-portrait")
 local entered
 for frame=0,12000 do
  local mode=w(0x2310);local button=nil
  if mode==3 then
   if task(0x08090c7c) and frame>600 then button="Start" end
   local h=task(0x08dfe048)
   if h then assert(eb(h+28)<=1 and eb(h+29)==0);button="A" end
  elseif mode==4 then
   if not entered then entered=frame;log("both permanent flags on ordinary cold selection") end
   assert(w(0x2328)&0x3030==0x3000 and w(0x1132)&0x30==0x30)
   if current and emu.framecount()>=change+8 and (current==11 or current==12) and not seen[current] then
    log("observed id="..current.." identity-cache="..w(0x472e));snapshot("fighter-"..current);seen[current]=true
    if seen[11] and seen[12]then return end
   end
   if frame-entered>100 then
    local moves={"Right","Down","Left","Up"}
    button=moves[math.floor((frame-entered-100)/750)%4+1]
   end
  end
  local keys={}
  for _,k in ipairs({"Start","A","B","Select","Left","Right","Up","Down","R","L","Power"})do keys[k]=frame%30<3 and k==button end
  joypad.set(keys);emu.frameadvance()
 end
 error("both native portrait IDs were not observed")
end
local ok,err=pcall(cold)
if not ok then log(tostring(err))end
write("done.txt",ok and "both-portraits-loaded" or "failure")
client.exit()
