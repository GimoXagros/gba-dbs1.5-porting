-- Read-only isolated audio fixture request discovery; no state or input injection.
local out=assert(userdata.get("output"))
local platform=assert(userdata.get("platform"))
assert(platform=="WSC" or platform=="GBA")
local domain=platform=="WSC" and "RAM" or "IWRAM"
local base=platform=="WSC" and 0xF90E or 0x22F0
local function u16(a)return memory.read_u16_le(a,domain)end
local function u8(a)return memory.read_u8(a,domain)end
local f=assert(io.open(out.."/music-requests.txt","wb"))
assert(platform=="WSC", "source driver phase diagnostic is WSC-only")
local phase_log=assert(io.open(out.."/audio-driver-phase.txt","wb"))
local last=nil
for step=0,4399 do
 local fields={string.format("id=%04X type=%04X flags=%04X",u16(base+2),u16(base+14),u16(base+16))}
 if platform=="WSC"then
  for n=0,7 do local at=0x59A+42*n;fields[#fields+1]=string.format("slot%d=%04X/ch%d",n,u16(at+3),u8(at+2))end
 end
 local value=table.concat(fields," ")
 if value~=last then assert(f:write(string.format("frame=%d %s\n",emu.framecount(),value)));f:flush();last=value end
 local raw={};for at=0x0642,0x06E9 do raw[#raw+1]=string.format("%02X",u8(at))end
 assert(phase_log:write(string.format("frame=%d phase=%02X flags=%04X states=%s\n",emu.framecount(),u8(0x06EE),u16(0xF91E),table.concat(raw))))
 phase_log:flush()
 emu.frameadvance()
end
f:close()
phase_log:close()
