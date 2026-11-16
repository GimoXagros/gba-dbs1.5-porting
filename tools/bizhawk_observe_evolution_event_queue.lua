-- Read-only provenance for extended evolution events and accepted music requests.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local f=assert(io.open(out.."/evolution-event-queue.txt","wb"))
local counts={selection=0,tick04=0,queue=0,stack=0}
local function rd(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d)end
 if n==2 then return memory.read_u16_le(o,d)end
 return memory.read_u32_le(o,d)
end
for a,w in pairs({[0x0835A1EC]=0xE92D0020,[0x0835A558]=0xE92D0020,[0x08012BA8]=0xEB02FA84,[0x080D15D0]=0xE1C680B2,[0x080D157C]=0xE1C400B2})do assert(rd(a,4)==w,"evolution queue opcode")end
local function log(label,r)
 assert(f:write(string.format("event=%s core=%d pc=%08X lr=%08X sp=%08X r0=%08X r1=%08X r4=%08X r5=%08X r8=%08X r9=%08X r10=%08X id=%d p1=%08X selected=%04X command=%08X cursor=%08X desc0=%08X desc4=%08X queueid=%04X queuetype=%04X\n",label,emu.framecount(),r.R15,r.R14,r.R13,r.R0,r.R1,r.R4,r.R5,r.R8,r.R9,r.R10,rd(r.R4+0x11,1),rd(r.R5+0x44,4),rd(r.R5+0xE,2),rd(r.R5+0x20,4),rd(r.R5+0x24,4),rd(r.R1,4),rd(r.R1+4,4),rd(0x030022F2,2),rd(0x030022FE,2))))
 f:flush()
end
local function hook(a,label,fn)event.on_bus_exec(function()fn(emu.getregisters(),label)end,a,"evolution-event-queue-"..label)end
for _,a in ipairs({0x0835A1EC,0x0835A558})do hook(a,"selected-"..string.format("%X",a),function(r,label)
 local id=rd(r.R4+0x11,1)
 if id>=11 and id<=14 then counts.selection=counts.selection+1;log(label,r)end
end)end
hook(0x08012BA8,"tick04",function(r,label)if r.R8==4 then counts.tick04=counts.tick04+1;log(label,r)end end)
hook(0x080D15D0,"accepted",function(r,label)counts.queue=counts.queue+1;if r.R8==4 or r.R8==0x6F then log(label,r)end end)
hook(0x080D157C,"stack-accepted",function(r,label)counts.stack=counts.stack+1;if r.R0==4 or r.R0==0x6F then log(label,r)end end)
local closed=false
local function finish()
 if closed then return end;closed=true
 assert(f:write(string.format("summary selections=%d tick04=%d queue=%d stack=%d\n",counts.selection,counts.tick04,counts.queue,counts.stack)));f:close()
end
assert(f:write("start readonly=true hooks=5 selection_ids=11..14 queue_ids=04,6F\n"));f:flush()
return {finish=finish}
