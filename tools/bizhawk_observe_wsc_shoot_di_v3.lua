-- Install read-only hooks only. The caller owns launch, input and save provenance.
-- dofile returns status()/finish(); no frame loop or input policy is installed.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
assert(userdata.get("callback_order")=="bizhawk2111-rew","pinned callback backend required")
assert(userdata.get("source_sha256")=="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
 "launcher must verify exact original source hash")
assert(emu.getsystemid()=="WSWAN")
for domain,size in pairs({ROM=0x800000,RAM=0x10000,SRAM=0x8000}) do
 assert(memory.getmemorydomainsize(domain)==size,"unexpected memory domain: "..domain)
end
local has_scope=false
for _,scope in pairs(event.availableScopes()) do if scope=="System Bus" then has_scope=true end end
assert(has_scope,"System Bus callback scope required")
local function pin(at,bytes)
 for i,v in ipairs(bytes) do assert(memory.read_u8(at+i-1,"ROM")==v,string.format("source pin %06X",at+i-1)) end
end
pin(0x75FC8C,{0x50,0x53,0x06,0x9C,0xBB,0x00,0x03,0x8E,0xC3,0xBB,0xEA,0x00,
 0x26,0x8B,0x45,0x0A,0xE6,0x10,0x9D,0x07,0x5B,0x58,0xCB})
pin(0x773650,{0xB8,0x00,0x0C,0x8E,0xD8,0xB8,0x00,0x10,0x8E,0xC0})
pin(0x750EBD,{0x50,0x1E,0xE4,0xB2,0x0C,0x40,0xE6})

-- V30MZ EA_105 truncates EO before adding ES. ReadWord increments physical EA;
-- the high byte does NOT wrap the segmented offset a second time.
local function operand(es,di)
 local offset=(di+0xA)%0x10000
 local low=(es*16+offset)%0x100000
 return offset,low,(low+1)%0x100000
end
for _,t in ipairs({
 {0x300,0xCFF5,0xCFFF,0x0FFFF,0x10000},
 {0x300,0xCFF6,0xD000,0x10000,0x10001},
 {0x300,0xD000,0xD00A,0x1000A,0x1000B},
 {0x300,0xFFF5,0xFFFF,0x12FFF,0x13000},
 {0x300,0xFFF6,0x0000,0x03000,0x03001},
 {0x300,0xFFFF,0x0009,0x03009,0x0300A},
 {0xFFFF,0x0005,0x000F,0xFFFFF,0x00000},
}) do
 local offset,low,high=operand(t[1],t[2])
 assert(offset==t[3] and low==t[4] and high==t[5],"segmented operand selfcheck")
end
-- This core has a System Bus callback scope but NO System Bus memory domain.
-- Its managed read callback also supplies value=0, not the consumed byte.
-- For pinned ES0300 all operand bytes are in RAM or 32KiB SRAM. Native Read20
-- maps SRAM with (offset | C1<<16)&7FFF, so C1 cannot alter this backing offset.
local function peek(physical)
 assert(physical>=0 and physical<0x20000,"operand outside proved RAM/SRAM mapping")
 if physical<0x10000 then return memory.read_u8(physical,"RAM"),"RAM",physical end
 local backing=physical%0x8000
 return memory.read_u8(backing,"SRAM"),"SRAM",backing
end
local path=out.."/di-observer-v3.txt"
local old=io.open(path,"rb")
if old then old:close();error("fresh DI output required") end
local function log(line)
 local f=assert(io.open(path,"a"));f:write(line.."\n");f:close()
end
local function snapshot(label)
 for domain,size in pairs({RAM=0x10000,SRAM=0x8000}) do
  local f=assert(io.open(out.."/di-v3-"..label.."-"..domain..".bin","wb"))
  f:write(memory.read_bytes_as_binary_string(0,size,domain));f:close()
 end
end
local MAX_PAIRS,MAX_DISTINCT=512,16
local calibrated,pairs_done,terminal_hits,distinct=0,0,0,0
local pending,finished=nil,false
local seen={}
local function context(r)
 return string.format("PS:PC=%04X:%04X DS=%04X ES=%04X SI=%04X DI=%04X BX=%04X AX=%04X SP=%04X irq=%04X:%04X",
  r.PS,r.PC,r.DS0,r.DS1,r.IX,r.IY,r.BW,r.AW,r.SP,
  memory.read_u16_le(0xF760,"RAM"),memory.read_u16_le(0xF75E,"RAM"))
end
local function at_site(raw,address)
 local r=emu.getregisters()
 assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000,
  "System Bus fetch address/register mismatch")
 return r
end
-- Pinned 2.11.1 managed R,W,E -> native R,E,W: on_bus_write observes execute.
local function install(raw,label,fn)
 event.on_bus_write(function(address)
  if finished then return end
  fn(at_site(raw,address))
 end,raw-0x700000,"shoot-di-v3-"..label,"System Bus")
end
log("observer=shoot-di-v3 guest_writes=none input=caller-owned save_provenance=caller-owned runtime_claim=none")
log("source_sha256="..userdata.get("source_sha256").." max_pairs=512 max_distinct_snapshots=16 callbacks=4")
log("read_kind=backing-domain-peek consumed_value=post-instruction-AW callback_value_not_used=true")
install(0x750EBD,"calibration",function(r)
 if calibrated<2 then calibrated=calibrated+1;log("calibration="..calibrated.." "..context(r)) end
end)
install(0x773650,"terminal",function(r)
 if memory.read_u8(0x5C,"SRAM")~=11 then return end
 assert(calibrated>0,"execute callback calibration missing")
 if terminal_hits==0 then
  terminal_hits=1;log("terminal frame="..emu.framecount().." "..context(r));snapshot("terminal-first")
 end
end)
install(0x75FC98,"pre",function(r)
 if memory.read_u8(0x5C,"SRAM")~=11 or pairs_done>=MAX_PAIRS then return end
 assert(calibrated>0,"execute callback calibration missing")
 assert(not pending,"unpaired prior DI operand")
 assert(r.DS1==0x0300,"pinned final IRQ must establish ES0300")
 local offset,low,high=operand(r.DS1,r.IY)
 local lo,ld,la=peek(low)
 local hi,hd,ha=peek(high)
 pending={es=r.DS1,di=r.IY,ps=r.PS,pc=r.PC,word=lo+256*hi,frame=emu.framecount()}
 log(string.format("pre pair=%d frame=%d offset=%04X low=%05X:%s:%04X:%02X high=%05X:%s:%04X:%02X peek_word=%04X %s",
  pairs_done+1,pending.frame,offset,low,ld,la,lo,high,hd,ha,hi,pending.word,context(r)))
 local key=string.format("%04X-%04X",r.DS1,r.IY)
 if not seen[key] and distinct<MAX_DISTINCT then
  seen[key]=true;distinct=distinct+1;snapshot(string.format("distinct-%02d-%s",distinct,key))
 end
end)
install(0x75FC9C,"post",function(r)
 if not pending then
  assert(memory.read_u8(0x5C,"SRAM")~=11 or pairs_done>=MAX_PAIRS,"post without matching pre")
  return
 end
 assert(r.DS1==pending.es and r.IY==pending.di,"operand registers changed across MOV")
 assert(r.PS==pending.ps and r.PC==(pending.pc+4)%0x10000,"instruction stream changed across MOV")
 local match=r.AW==pending.word
 log(string.format("post pair=%d frame=%d AX=%04X AL=%02X peek_matches_consumed=%s %s",
  pairs_done+1,emu.framecount(),r.AW,r.AW%256,tostring(match),context(r)))
 assert(match,"pre-read backing bytes differ from actual consumed AX")
 pending=nil;pairs_done=pairs_done+1
 if pairs_done==MAX_PAIRS then log("pair_limit_reached=512") end
end)
local function status()
 return {calibrated=calibrated,paired_reads=pairs_done,terminal_observed=terminal_hits==1,
  distinct_snapshots=distinct,pending=pending~=nil,finished=finished,
  actual_final_irq_observed=pairs_done>0}
end
local function finish()
 assert(not finished,"observer already finished")
 assert(not pending,"observer finished between operand hooks")
 finished=true
 log(string.format("finish calibrated=%d paired_reads=%d terminal_observed=%s distinct_snapshots=%d actual_final_irq_observed=%s",
  calibrated,pairs_done,tostring(terminal_hits==1),distinct,tostring(pairs_done>0)))
 return status()
end
return {status=status,finish=finish}
