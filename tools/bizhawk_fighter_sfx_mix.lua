-- Read the original music, C6 player and hardware wave owner while the real mixer runs.
local out=assert(userdata.get("output"))
local f=assert(io.open(out.."/mix.txt","wb"))
for frame=1,790 do
 if frame>521 then
  local function d(a)return memory.read_u32_le(a,"IWRAM") end
  local function b(a)return memory.read_u8(a,"IWRAM") end
  f:write(string.format("%04d %08X %08X %04X %08X %08X %02X %08X %08X\n",emu.framecount(),
   d(0x6b40),d(0x6b44),d(0x6b4c),d(0x6c00),d(0x6c04),b(0x6a80),d(0x6a80+0x2c),d(0x6a80+0x24)))
 end
 emu.frameadvance()
end
f:close()

