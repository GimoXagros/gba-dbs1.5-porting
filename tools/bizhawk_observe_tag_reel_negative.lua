local out=assert(userdata.get("output"))
local f=assert(io.open(out.."/trace.txt","wb"))
local function log(s)f:write(emu.framecount()," ",s,"\n");f:flush()end
local function d(a)return memory.read_u32_le(a,"IWRAM")end
local request=tonumber(assert(userdata.get("request")))
local count=0
event.on_bus_exec(function()
 local r=emu.getregisters()
 if r.R0~=request then return end
 assert(r.R2==0x03006c90 and r.R0==request)
 if count<5 then log(string.format("conditional stop compare wanted=%08X owning=%08X flags=%08X",r.R0,r.R1,d(0x6c94)))end
 assert(r.R1==0x083876f0)
 count=count+1
end,0x0837c364,"stop-owner-compare")
local last
for i=0,1050 do
 local state=string.format("%08X %08X",d(0x6c90),d(0x6c94))
 if state~=last then log("mplay3 "..state);last=state end
 if i==1040 then log("completed stop comparisons="..count) end
 emu.frameadvance()
end
f:close()
