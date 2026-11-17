-- Positive ID14 entry witness, bounded to the first following frame.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local f=assert(io.open(out.."/evolution-entry-provenance.txt","wb"))
local selected,initialized,saved,closed=nil,false,false,false
local counts={}
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
local function active(p)return selected and p==selected.p and emu.framecount()<=selected.frame+1 end
local function log(label,r,extra)
 counts[label]=(counts[label]or 0)+1;if counts[label]>8 then return end
 local p=selected.p;local resource=rd(p+0x44,4)
 local row=(rd(resource,4)+selected.event*16)&0xFFFFFFFF
 local command=rd(p+0x24,4)
 assert(f:write(string.format("event=%s core=%d pc=%08X r0=%08X r1=%08X r4=%08X r5=%08X r8=%08X actor=%08X presentation=%08X selected=%X actor_flags4=%X actor_flags8=%X present_flags=%X live_event=%X index=%X count=%X base=%X command=%X A=%X event_B=%X P1=%X event_row=%X row_count=%X row_command=%X row_A=%X row_B=%X command_B=%X %s\n",
 label,emu.framecount(),r.R15,r.R0,r.R1,r.R4,r.R5,r.R8,selected.actor,p,selected.event,rd(selected.actor+4,2),rd(selected.actor+8,2),rd(p+0xC,2),rd(p+0xE,2),rd(p+0x1A,2),rd(p+0x1C,2),rd(p+0x20,4),command,rd(p+0x28,4),rd(p+0x2C,4),resource,row,rd(row,4),rd(row+4,4),rd(row+8,4),rd(row+12,4),rd(command+12,4),extra or "")))
 f:flush()
end
local function hook(a,w,label,fn)
 assert(rd(a,4)==w,"entry provenance opcode "..label)
 event.on_bus_exec(function()fn(emu.getregisters())end,a,"entry-provenance-"..label)
end
hook(0x0835A1EC,0xE92D0020,"selected",function(r)
 if not selected and rd(r.R4+0x11,1)==14 then
  selected={actor=r.R4,p=r.R5,event=r.R0,frame=emu.framecount()};log("selected",r)
 end
end)
hook(0x0835A1FC,0xE28DD00C,"initialized",function(r)
 if active(r.R5)and r.R4==selected.actor then initialized=true;log("initialized",r)end
end)
hook(0x08352830,0xE1D480B4,"actor-gate",function(r)
 if active(r.R4+0xAC)then log("actor-gate",r)end
end)
hook(0x08353C98,0xE594800C,"B-lookup-before",function(r)
 if active(r.R5)then log("B-lookup-before",r)end
end)
hook(0x08353C9C,0xE3580000,"B-lookup-after",function(r)
 if active(r.R5)then log("B-lookup-after",r,string.format("actual_B=%08X",r.R8))end
end)
hook(0x08353CA8,0xE59F10D4,"B-after",function(r)
 if active(r.R5)then log("B-after",r,string.format("actual_B=%08X",r.R4))end
end)
for _,site in ipairs({{0x08353C70,"event-type"},{0x08353D24,"command-type"}})do
 hook(site[1],0xE1C100B4,site[2],function(r)
  if active(r.R5)then log(site[2],r,string.format("dst=%08X B=%08X loaded=%08X stored=%04X",r.R1,r.R4,r.R0,r.R0&0xFFFF))end
 end)
end
local function outcome()
 if not initialized or emu.framecount()<=selected.frame then return nil end
 if not saved then
  for _,v in ipairs({{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000}})do
   local b=assert(io.open(out.."/evolution-entry-boundary-"..v[1]..".bin","wb"))
   assert(b:write(memory.read_bytes_as_binary_string(0,v[3],v[2])));b:close()
  end
  assert(f:write(string.format("boundary core=%d selected_core=%d\n",emu.framecount(),selected.frame)));f:flush();saved=true
 end
 return "evolution-entry-provenance-observed"
end
local function finish()
 if closed then return end;closed=true
 for _,name in ipairs({"selected","initialized","actor-gate","B-lookup-before","B-lookup-after","B-after","event-type","command-type"})do
  assert(f:write(string.format("summary event=%s count=%d\n",name,counts[name]or 0)))
 end
 assert(f:write("complete=true boundary_saved="..tostring(saved).."\n"));f:close()
end
assert(f:write("start readonly=true hooks=8 target_id=14 row_limit=8 stop=first-frame-after-initialized-entry\n"));f:flush()
return {outcome=outcome,finish=finish}
