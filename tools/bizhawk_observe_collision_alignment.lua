-- Read-only upstream collision metadata witness; no game-state correction.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local file=assert(io.open(out.."/collision-alignment.txt","wb"))
local counts={metadata=0,odd=0,confirmed=0,dispatch=0,e5=0}
local sequence,pending,last_odd=0,nil,nil
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==2 then return memory.read_u16_le(o,d)end
 return memory.read_u32_le(o,d)
end
for a,w in pairs({[0x0836E37C]=0xE1D130B2,[0x0836E380]=0xE1D120B4,[0x0836EB58]=0xE1D810B0,[0x0836EBA4]=0xE12FFF19})do
 assert(read(a,4)==w,"collision observation opcode")
end
local function line(label,r,extra)
 assert(file:write(string.format("event=%s core=%d sequence=%d pc=%08X lr=%08X sp=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X r8=%08X r9=%08X scratch=%04X %s\n",
 label,emu.framecount(),sequence,r.R15,r.R14,r.R13,r.R0,r.R1,r.R2,r.R3,r.R4,r.R5,r.R8,r.R9,read(0x03004D20,2),extra or "")))
 file:flush()
end
local function snapshot(prefix)
 for _,v in ipairs({{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000}})do
  local f=assert(io.open(out.."/"..prefix.."-"..v[1]..".bin","wb"))
  assert(f:write(memory.read_bytes_as_binary_string(0,v[3],v[2])));f:close()
 end
end
local finished=false
local function finish()
 if finished then return end;finished=true
 assert(file:write(string.format("summary metadata=%d odd=%d confirmed=%d dispatch=%d e5=%d\n",counts.metadata,counts.odd,counts.confirmed,counts.dispatch,counts.e5)))
 file:close()
end
local function hook(a,name,fn)event.on_bus_exec(function()fn(emu.getregisters())end,a,"collision-alignment-"..name)end
hook(0x0836E37C,"metadata",function(r)
 counts.metadata=counts.metadata+1;sequence=sequence+1;pending=nil
 if r.R1&1==0 then return end
 counts.odd=counts.odd+1
 pending={pointer=r.R1,frame=emu.framecount(),sequence=sequence}
 last_odd=pending
 if counts.odd<=16 then
  local a=r.R1&~1
  line("odd-before",r,string.format("metadata=%08X attack_owner=%08X type=%04X a0=%04X a2=%04X a4=%04X",read(r.R4+0x10,4),read(r.R4,4),read(r.R4+4,2),read(a,2),read(a+2,2),read(a+4,2)))
 end
 if counts.odd==1 then snapshot("collision-first-odd")end
end)
hook(0x0836E380,"loaded",function(r)
 if pending and pending.frame==emu.framecount() and pending.pointer==r.R1 then
  counts.confirmed=counts.confirmed+1
  if counts.confirmed<=16 then line("odd-after",r)end
 end
 pending=nil
end)
hook(0x0836EB58,"dispatch",function(r)
 counts.dispatch=counts.dispatch+1
 if read(0x03004D20,2)==0xE5 then
  counts.e5=counts.e5+1;line("e5-before-dispatch",r);snapshot("collision-e5");finish()
  local f=assert(io.open(out.."/result-done.txt","w"));assert(f:write("failure:observed-collision-e5"));f:close()
  error("observed-collision-e5")
 elseif last_odd and last_odd.sequence==sequence and last_odd.frame==emu.framecount() and counts.odd<=16 then line("odd-dispatch",r)end
end)
hook(0x0836EBA4,"branch",function(r)
 if last_odd and last_odd.sequence==sequence and last_odd.frame==emu.framecount() and counts.odd<=16 then line("odd-branch",r)end
end)
assert(file:write("start readonly=true hooks=4 odd_rows_limit=16 absence_is_not_root_cause=true\n"));file:flush()
return {finish=finish}
