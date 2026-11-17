-- Read-only draw provenance; explicitly armed only for the post-return tail.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local f=assert(io.open(out.."/render-tail.txt","wb"))
local active,closed=false,false
local counts,emitted,suppressed={},{},{}
local lastframe=-1
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
local function actor(a)
 if a<0x02000000 or a+0x118>0x02040000 then return string.format("invalid=%08X",a)end
 return string.format("actor=%08X cb=%08X f4=%04X f6=%04X f8=%04X id=%d world=%04X,%04X previous=%04X,%04X present=%04X,%04X pflags=%04X event=%04X frame=%04X command=%08X resource=%08X graphics=%08X",a,rd(a,4),rd(a+4,2),rd(a+6,2),rd(a+8,2),rd(a+0x11,1),rd(a+0x34,2),rd(a+0x36,2),rd(a+0x38,2),rd(a+0x3A,2),rd(a+0xAC,2),rd(a+0xAE,2),rd(a+0xB4,2),rd(a+0xBA,2),rd(a+0xC4,2),rd(a+0xCC,4),rd(a+0xF0,4),rd(a+0xF4,4))
end
local function state()
 return string.format("queue=%d objcount=%d camera=%04X,%04X bgcamera=%04X,%04X P1{%s} P2{%s}",rd(0x0300482A,2),rd(0x030012CA,1),rd(0x0300451C,2),rd(0x0300451E,2),rd(0x03002348,2),rd(0x0300234A,2),actor(rd(0x0300489C,4)),actor(rd(0x030048A0,4)))
end
local function write(line)assert(f:write(line.."\n"));f:flush()end
local hooks={
 {0x08352998,0xE7895101,"enqueue"},
 {0x083734F0,0xE92D4000,"queue-normal"},
 {0x0837354C,0xE92D4000,"queue-paused"},
 {0x083735BC,0xE92D4000,"queue-transition"},
 {0x08012C30,0xE5954044,"dispatch"},
 {0x03000200,0xE92D403F,"render"},
 {0x03000358,0xE5C20000,"render-result"},
}
for _,h in ipairs(hooks)do
 local at,opcode,label=h[1],h[2],h[3]
 if at>=0x08000000 then assert(rd(at,4)==opcode,"render-tail ROM opcode "..label)end
 counts[label],suppressed[label]=0,0
 event.on_bus_exec(function()
  if not active or closed then return end
  assert(rd(at,4)==opcode,"render-tail live opcode "..label)
  local frame=emu.framecount()
  if frame~=lastframe then emitted={};lastframe=frame end
  counts[label]=counts[label]+1
  emitted[label]=(emitted[label]or 0)+1
  if emitted[label]>8 then suppressed[label]=suppressed[label]+1;return end
  local r=emu.getregisters()
  write(string.format("event=%s core=%d pc=%08X lr=%08X r0=%08X r1=%08X r2=%08X r4=%08X r5=%08X %s",label,frame,r.R15,r.R14,r.R0,r.R1,r.R2,r.R4,r.R5,state()))
 end,at,"render-tail-"..label)
end
local function snapshot(label)
 assert(not closed,"render-tail snapshot after close")
 assert(type(label)=="string" and label:match("^[%w%-%_]+$"),"snapshot label")
 write(string.format("snapshot=%s core=%d %s",label,emu.framecount(),state()))
end
local function arm()assert(not closed);active=true;snapshot("armed")end
local function frame(age)
 assert(type(age)=="number" and age>=0 and age<=120 and age%1==0,"bounded tail age")
 if not active then assert(age==0,"tail starts at zero");arm()end
 snapshot("age-"..age)
end
local function finish()
 if closed then return end
 for _,h in ipairs(hooks)do local l=h[3];write(string.format("count event=%s observed=%d suppressed=%d",l,counts[l],suppressed[l]))end
 closed=true;f:close()
end
write("start readonly=true hooks=7 per_label_per_frame_limit=8 active=false no_guest_writes=true")
return {frame=frame,arm=arm,snapshot=snapshot,finish=finish}
