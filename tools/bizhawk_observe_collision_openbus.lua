-- Read-only malformed-command to collision-type witness; no guest writes.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local f=assert(io.open(out.."/collision-openbus.txt","wb"))
local counts,rows={},{}
local pending,metadata,result=nil,nil,nil
local captured={}
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
local function malformed(p)
 return rd(p+0x24,4)==0xFFFFFFFF or rd(p+0x28,4)==0xFFFFFFFF or rd(p+0x2C,4)==0xFFFFFFFF
end
local function log(label,r,p,extra)
 counts[label]=(counts[label]or 0)+1
 if counts[label]>32 then return end
 assert(f:write(string.format("event=%s core=%d pc=%08X lr=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X r8=%08X presentation=%08X actor_flags=%X present_flags=%X event_id=%X command_index=%X command_count=%X command_base=%X command=%X A=%X event_B=%X P1=%X %s\n",
 label,emu.framecount(),r.R15,r.R14,r.R0,r.R1,r.R2,r.R3,r.R4,r.R5,r.R8,p,rd(p-0xAC+4,2),rd(p+0xC,2),rd(p+0xE,2),rd(p+0x1A,2),rd(p+0x1C,2),rd(p+0x20,4),rd(p+0x24,4),rd(p+0x28,4),rd(p+0x2C,4),rd(p+0x44,4),extra or "")))
 f:flush()
end
local function snapshot(kind)
 if captured[kind]then return end;captured[kind]=true
 for _,v in ipairs({{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000}})do
  local b=assert(io.open(out.."/collision-openbus-"..kind.."-"..v[1]..".bin","wb"))
  assert(b:write(memory.read_bytes_as_binary_string(0,v[3],v[2])));b:close()
 end
end
local function hook(a,w,label,fn)
 assert(rd(a,4)==w,"collision openbus opcode "..label)
 event.on_bus_exec(function()fn(emu.getregisters())end,a,"collision-openbus-"..label)
end
hook(0x08352830,0xE1D480B4,"actor-gate",function(r)
 local p=r.R4+0xAC
 if malformed(p)then log("actor-gate",r,p)end
end)
hook(0x08353CA4,0xE594400C,"B-before",function(r)
 pending=nil
 if malformed(r.R5)or r.R4==0xFFFFFFFF then
  pending={frame=emu.framecount(),p=r.R5,command=r.R4}
  log("B-before",r,r.R5,string.format("effective_read=%08X",(r.R4+12)&0xFFFFFFFF))
 end
end)
hook(0x08353CA8,0xE59F10D4,"B-after",function(r)
 if pending and pending.frame==emu.framecount()and pending.p==r.R5 then
  log("B-after",r,r.R5,string.format("loaded_B=%08X",r.R4))
 end
 pending=nil
end)
local function produced(label,r)
 local type16=r.R0&0xFFFF
 if malformed(r.R5)or type16>=26 then
  local p=r.R5
  rows[r.R1]={p=p,frame=emu.framecount(),B=r.R4,type=type16}
  log(label,r,p,string.format("dst=%08X B=%08X loaded_type32=%08X stored_type16=%04X x=%X y=%X width=%X height=%X A_record=%X",r.R1,r.R4,r.R0,type16,rd(r.R1+6,2),rd(r.R1+8,2),rd(r.R1+10,2),rd(r.R1+12,2),rd(r.R1+16,4)))
  if type16>=26 then snapshot("first-invalid")end
  if type16==0xE5 then snapshot("first-e5")end
  if label=="command-type"and malformed(p)and not result then
   snapshot("first-command")
   result=string.format("core=%d B=%08X loaded=%08X stored=%04X",emu.framecount(),r.R4,r.R0,type16)
   local marker=assert(io.open(out.."/collision-openbus-produced.txt","wb"))
   assert(marker:write(result.."\n"));marker:close()
  end
 end
end
hook(0x08353C70,0xE1C100B4,"event-type",function(r)produced("event-type",r)end)
hook(0x08353D24,0xE1C100B4,"command-type",function(r)produced("command-type",r)end)
hook(0x0836E370,0xE1C800B0,"overlap",function(r)
 local origin=rows[r.R4]
 if r.R0>=26 or(origin and origin.frame==emu.framecount())then
  log("overlap",r,rd(r.R4,4)+0xAC,string.format("record=%08X receiver=%08X A_record=%X origin_B=%X origin_frame=%d",r.R4,r.R5,rd(r.R4+16,4),origin and origin.B or -1,origin and origin.frame or -1))
  if r.R0>=26 then snapshot("first-invalid")end
  if r.R0==0xE5 then snapshot("first-e5")end
 end
end)
hook(0x0836E37C,0xE1D130B2,"metadata-before",function(r)
 metadata=nil
 if r.R1==0xFFFFFFFF or rd(r.R4+4,2)>=26 then
  metadata={frame=emu.framecount(),pointer=r.R1,p=rd(r.R4,4)+0xAC}
  log("metadata-before",r,metadata.p,string.format("record=%08X metadata=%08X effective_read=%08X",r.R4,r.R1,(r.R1+2)&0xFFFFFFFF))
 end
end)
hook(0x0836E380,0xE1D120B4,"metadata-after",function(r)
 if metadata and metadata.frame==emu.framecount()and metadata.pointer==r.R1 then
  log("metadata-after",r,metadata.p,string.format("metadata=%08X loaded_r3=%08X",r.R1,r.R3))
 end
 metadata=nil
end)
local closed=false
local function finish()
 if closed then return end;closed=true
 for _,name in ipairs({"actor-gate","B-before","B-after","event-type","command-type","overlap","metadata-before","metadata-after"})do
  assert(f:write(string.format("summary event=%s count=%d\n",name,counts[name]or 0)))
 end
 assert(f:write("complete=true invalid_captured="..tostring(captured["first-invalid"]or false).." e5_captured="..tostring(captured["first-e5"]or false).."\n"));f:close()
end
assert(f:write("start readonly=true hooks=8 per_event_row_limit=32 invalid_classification=stored_halfword no_historical_cause_claim=true\n"));f:flush()
return {finish=finish,result=function()return result end,outcome=function()return result and "collision-openbus-producer-observed"or nil end}
