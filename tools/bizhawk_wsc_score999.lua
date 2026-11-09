-- Explicitly authorized original-reference cheat: only active P1 score WORD=999.
local output=assert(userdata.get("output"))
assert(output:match("^W:/build/[%w%-%_/]+$"),"isolated source output required")
assert(userdata.get("callback_order")=="bizhawk2111-rew","calibrated source opcode binding required")
local installed,finished,hits,eligible,writes=false,false,0,0,0
local hook_raw,hook_bus=0x7417A1,0x417A1
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function byte(a)return memory.read_u8(a,"SRAM")end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function active(p)
 return math.floor(mainmemory.read_u16_le(0xC000+p-6)/2)%2==1
end
local function ledger(line)
 local f=assert(io.open(output.."/score999-writes.txt","a"))
 f:write(line.."\n");f:close()
end
local function status()
 return {enabled=installed,finished=finished,hits=hits,eligible=eligible,writes=writes,
  value=999,bytes_per_write=2,hook_raw=hook_raw}
end
local function apply(address)
 if finished then return end
 hits=hits+1
 local r=emu.getregisters()
 assert(address==hook_bus and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000,
  "score hook must be the calibrated original opcode")
 local stage=byte(0x5C)
 if word(0x4E)~=7 or word(0x50)~=0 or word(0x3D0)~=0 or stage>10 or stage==7
  or byte(0x3CC)~=0 or byte(0x3CD)%8~=0 then return end
 local first,second=word(0x65C),word(0x65E)
 if not valid(first) or not valid(second) or first==second or not active(first) then return end
 local at,other=0xC000+first,0xC000+second
 if mainmemory.read_u16_le(at+4)%16~=0 or mainmemory.read_u8(at+0x10)~=0
  or mainmemory.read_u16_le(at+0x14)~=second then return end
 eligible=eligible+1
 local before=mainmemory.read_u16_le(at+0x52)
 if before==999 then return end
 local hp=mainmemory.read_u16_le(at+0x50)
 local adjacent=mainmemory.read_u16_le(at+0x54)
 local opponent=mainmemory.read_u16_le(other+0x52)
 -- After orb clamping, before HUD and timeout; no other game field is written.
 mainmemory.write_u16_le(at+0x52,999)
 assert(mainmemory.read_u16_le(at+0x52)==999 and mainmemory.read_u16_le(at+0x50)==hp
  and mainmemory.read_u16_le(at+0x54)==adjacent and mainmemory.read_u16_le(other+0x52)==opponent,
  "score-only write/readback contract")
 writes=writes+1
 ledger(string.format("write=%d frame=%d stage=%d p1=%04X address=%04X bytes=2 before=%d after=999 hp=%d adjacent54=%d p2score=%d",
  writes,emu.framecount(),stage,first,at+0x52,before,hp,adjacent,opponent))
end
local function tick()
 if installed then return status() end
 assert(not finished,"finished score module cannot install")
 event.on_bus_write(apply,hook_bus,"authorized-P1-score999","System Bus")
 installed=true
 ledger("enabled original-reference-only hook=7417A1 value=999 width=2; ordinary single-player stages0..10 excluding7; results export low byte231")
 return status()
end
local function finish()
 if not finished then
  finished=true
  ledger(string.format("finished hits=%d eligible=%d writes=%d bytes_per_write=2 value=999",hits,eligible,writes))
 end
 return status()
end
return {tick=tick,status=status,finish=finish}
