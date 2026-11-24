-- Capture original cue dispatch and native player status on the private audio fixture.
local out=assert(userdata.get("output"))
local kind=assert(userdata.get("platform"))
local f=assert(io.open(out.."/trace.txt","wb"))
local function state(frame,fields)f:write(frame," ",fields,"\n");f:flush()end
if kind=="wsc" then
 local slot=assert(tonumber(userdata.get("slot")))
 local last={}
 for i=1,645 do
  if i>=517 and i<625 then
   local addr=0x59a+slot
   local h=memory.read_bytes_as_binary_string(addr,42,"RAM")
   local s=h:gsub(".",function(c)return string.format("%02x",string.byte(c))end)
   state(emu.framecount(),s)
  end
  emu.frameadvance()
 end
else
 local player=assert(tonumber(userdata.get("slot")))
 for i=1,645 do
  if i>=515 and i<=630 then state(emu.framecount(),string.format("%08x %08x",
   memory.read_u32_le(player,"IWRAM"),memory.read_u32_le(player+4,"IWRAM")))end
  emu.frameadvance()
 end
end
f:close()

