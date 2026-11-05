-- Read-only producer journal around the existing collision consumer observer.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
local profile=userdata.get("combat_profile") or "approach-jump"
assert(profile=="approach-jump" or profile=="baseline")
local initial=emu.framecount()
local ring,serial,last,totals={ },0,{ },{producer=0,list_write=0,scratch_write=0,overlap=0,read=0}
local failed=false
local function log(s)
 local f=assert(io.open(out.."/producer-trace.txt","a"));f:write(s.."\n");f:close()
end
local function read(address,width)
 local domain,offset
 if address>=0x02000000 and address+width<=0x02040000 then domain,offset="EWRAM",address-0x02000000
 elseif address>=0x03000000 and address+width<=0x03008000 then domain,offset="IWRAM",address-0x03000000
 elseif address>=0x08000000 and address+width<=0x08800000 then domain,offset="ROM",address-0x08000000
 else return -1 end
 if width==2 then return memory.read_u16_le(offset,domain) end
 return memory.read_u32_le(offset,domain)
end
local function journal(kind,r,detail)
 serial=serial+1
 ring[(serial-1)%128+1]=string.format("seq=%d frame=%d kind=%s pc=%08X %s",serial,emu.framecount(),kind,r.R15,detail)
end
local function capture(reason,r)
 if failed then return end
 failed=true
 log("capture="..reason.." timing=before-instruction callback-register-PC-retained")
 for n=math.max(1,serial-127),serial do log(ring[(n-1)%128+1]) end
 for k,v in pairs(r) do log(string.format("reg %s=%08X",k,v)) end
 for _,item in ipairs({{"IWRAM",0x8000},{"EWRAM",0x40000}}) do
  local f=assert(io.open(out.."/producer-failure-"..item[1]:lower()..".bin","wb"))
  f:write(memory.read_bytes_as_binary_string(0,item[2],item[1]));f:close()
 end
end
local function producer(address,base,count_address)
 event.on_bus_exec(function()
  totals.producer=totals.producer+1
  local r=emu.getregisters()
  local index=(r.R1-base)/20
  local count=memory.read_u8(count_address,"IWRAM")
  local actor=read(r.R1,4)
  local p=actor+0xAC
  local detail=string.format("writer=%08X dst=%08X index=%g count=%d type=%04X B=%08X source_type=%X actor=%08X selector_A0=%X event=%X command_index=%X command_count=%X command_base=%X command=%X A=%X event_B=%X P1=%X",
   address,r.R1,index,count,r.R0,r.R4,read(r.R4,2),actor,read(actor+0xA0,2),read(p+0x0E,2),read(p+0x1A,2),read(p+0x1C,2),read(p+0x20,4),read(p+0x24,4),read(p+0x28,4),read(p+0x2C,4),read(p+0x44,4))
  journal("producer",r,detail)
  last[r.R1]={type=r.R0,frame=emu.framecount(),detail=detail}
  if r.R0>=26 then capture("invalid-producer-type",r)
  elseif index<0 or index>=12 or index%1~=0 or index~=count then capture("producer-list-geometry",r) end
 end,address,"producer-"..string.format("%X",address))
end
producer(0x08353C70,0x030049B8,0x4C4E)
producer(0x08353D24,0x030048C8,0x4C4D)
producer(0x083776E4,0x030048C8,0x4C4D)
-- Callback values can be unsupported/zero: preserve raw values, classify actual reads.
for _,base in ipairs({0x030048C8,0x030049B8}) do
 for slot=0,11 do
  local target=base+slot*20+4
  event.on_bus_write(function(address,value,flags)
   totals.list_write=totals.list_write+1
   journal("list-write",emu.getregisters(),string.format("address=%08X value=%X flags=%X old_type=%X",address,value,flags,read(target,2)))
  end,target,"list-type-"..string.format("%X",target))
 end
end
event.on_bus_write(function(address,value,flags)
 totals.scratch_write=totals.scratch_write+1
 journal("scratch-write",emu.getregisters(),string.format("address=%08X value=%X flags=%X old_type=%X",address,value,flags,read(0x03004D20,2)))
end,0x03004D20,"scratch-type-writer")
event.on_bus_exec(function()
 totals.overlap=totals.overlap+1
 local r=emu.getregisters()
 local origin=last[r.R4]
 journal("overlap",r,string.format("record=%08X type=%X origin_frame=%d origin=%s",r.R4,r.R0,origin and origin.frame or -1,origin and origin.detail or "unobserved"))
 if r.R0>=26 then capture("invalid-overlap-type",r)
 elseif origin and origin.frame==emu.framecount() and origin.type~=r.R0 then capture("list-type-changed-after-producer",r) end
end,0x0836E370,"producer-overlap-origin")
event.on_bus_exec(function()
 totals.read=totals.read+1
 local r=emu.getregisters()
 local value=read(0x03004D20,2)
 journal("scratch-read",r,string.format("actual_type=%X",value))
 if value>=26 then capture("invalid-actual-scratch-type",r) end
end,0x0836EB58,"producer-scratch-consumer")
local set=joypad.set
joypad.set=function(keys)
 local frame=emu.framecount()-initial
 if profile=="approach-jump" and frame>=5550 and memory.read_u16_le(0x2310,"IWRAM")==7 then
  keys.A=frame%97<7;keys.B=frame%29<7
  keys.Up=frame%181<9
  keys.Right=frame<6150 or frame%720<300
  keys.Left=frame>=6150 and frame%720>=360 and frame%720<660
 end
 set(keys)
end
local exit=client.exit
client.exit=function()
 local released={}
 for _,button in ipairs({"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}) do released[button]=false end
 set(released)
 log(string.format("summary producer=%d list_write=%d scratch_write=%d overlap=%d read=%d captured=%s",totals.producer,totals.list_write,totals.scratch_write,totals.overlap,totals.read,tostring(failed)))
 if not failed then for n=math.max(1,serial-127),serial do log(ring[(n-1)%128+1]) end end
 local done=assert(io.open(out.."/producer-done.txt","w"));done:write("producer-journal-complete");done:close()
 exit()
end
log("profile="..profile.." ring_capacity=128 guest_writes=none raw-write-values-not-classified")
dofile("W:/tools/bizhawk_probe_gba_collision.lua")
