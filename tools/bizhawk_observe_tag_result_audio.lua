-- Read-only M4A player state from an isolated boot-row audio rendering fixture.
local out=assert(userdata.get("output"))
local player=assert(tonumber(userdata.get("player")))
local want=assert(tonumber(userdata.get("song")))
local f=assert(io.open(out.."/player.txt","wb"))
local previous
for n=0,1300 do
 local header=memory.read_u32_le(player,"IWRAM")
 local flags=memory.read_u32_le(player+4,"IWRAM")
 local sample=string.format("%08X %08X",header,flags)
 if sample~=previous then
  f:write(emu.framecount()," ",sample,"\n");f:flush();previous=sample
 end
 emu.frameadvance()
end
f:close()
