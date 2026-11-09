-- User-approved original-reference action. Standalone and inert without approval token.
-- Original-reference stage11 only: one active SECOND HP WORD reduction to1, never zero.
local SOURCE="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
local approved=userdata.get("shoot_boss_hp1_approval")=="user-approved-original-stage11-boss-once"
local installed,finished,applied,hits,writes=false,false,false,0,0
local output
local upper_callbacks={[0x7DD9]=true,[0x7E8D]=true,[0x7EBB]=true,[0x8069]=true,[0x809C]=true}
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function byte(a)return memory.read_u8(a,"SRAM")end
local function ram(a)return mainmemory.read_u16_le(a)end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function active(p)return math.floor(ram(0xC000+p-6)/2)%2==1 end
local function task(p,callback)
 return valid(p+0x10) and active(p+0x10) and ram(0xC000+p)==callback
  and ram(0xC000+p+2)==0x4090
end
local function ledger(line)
 local f=assert(io.open(output.."/shoot-boss-hp1-once-writes.txt","a"))
 f:write(line.."\n");f:close()
end
local function status()
 return {approved=approved,installed=installed,enabled=installed and not finished and not applied,
  finished=finished,applied=applied,hits=hits,writes=writes,value=1,bytes_per_write=2,hook_raw=0x7417A1}
end
local function apply(address)
 if finished or applied then return end
 hits=hits+1
 local r=emu.getregisters()
 assert(address==0x417A1 and (r.PS*16+r.PC)%0x100000==0x417A2,
  "boss proposal requires calibrated original opcode")
 if word(0x4E)~=7 or word(0x50)~=0 or word(0x3D0)~=2 or byte(0x5C)~=11 or byte(0x5D)~=3
  or math.floor(word(0x3D8)/4)%2~=1
  or byte(0x3CC)~=0 or byte(0x3CD)%8~=0 or word(0x3CE)>=18000 then return end
 if not task(word(0x3DE),0x07FA) or not task(word(0x3E0),0x0D0B) then return end
 local first,second=word(0x65C),word(0x65E)
 if not valid(first) or not valid(second) or first==second
  or not active(first) or not active(second) then return end
 local p1,p2=0xC000+first,0xC000+second
 if ram(p1+4)%16~=0 or mainmemory.read_u8(p1+0x10)~=0 or ram(p1+0x14)~=second
  or ram(p2+4)%16~=3 or mainmemory.read_u8(p2+0x10)~=1
  or mainmemory.read_u8(p2+0x11)~=0x0F or ram(p2+0x14)~=first then return end
 -- Fixed default-ID0 path; the live source resource binds the stage11 upper boss.
 if mainmemory.read_u8(p1+0x11)~=0 or ram(p2+2)~=0x4090 or not upper_callbacks[ram(p2)]
  or ram(p2+0xC6)~=0 or ram(p2+0xC8)~=0x2F41 or ram(p2+0xCA)~=0xBC
  or ram(p2+0xCC)~=0 or ram(p2+0xCE)~=0x25F8 or ram(p2+0xD0)~=0xBD then return end
 local aux=ram(p2+0x1C)
 if not valid(aux) or aux==first or aux==second or not active(aux) then return end
 local body=0xC000+aux
 if ram(body+4)%16~=6 or ram(body+0x1C)~=second or ram(body+0x14)~=first
  or ram(body+0xC6)~=0 or ram(body+0xC8)~=0x2D73 or ram(body+0xCA)~=0xBB then return end
 local hp,before=ram(p1+0x50),ram(p2+0x50)
 if hp==0 or hp>=0x8000 or before<=1 or before>44 then return end
 local p1score,left,right,adjacent=ram(p1+0x52),ram(p2+0x4E),ram(p2+0x52),ram(p2+0x54)
 local quarter,aux56=ram(p2+0x56),ram(body+0x56)
 applied=true -- Consume this module lifetime before the sole write; never retry or hold1.
 mainmemory.write_u16_le(p2+0x50,1)
 writes=writes+1
 assert(ram(p2+0x50)==1 and ram(p1+0x50)==hp and ram(p1+0x52)==p1score
  and ram(p2+0x4E)==left and ram(p2+0x52)==right and ram(p2+0x54)==adjacent and ram(p2+0x56)==quarter and ram(body+0x56)==aux56,
  "one boss HP WORD only")
 ledger(string.format("write=1 frame=%d stage=11 p1=%04X p2=%04X address=%04X bytes=2 before=%d after=1 timer=%d p1hp=%d p1score=%d boss4E=%d boss52=%d boss54=%d boss56=%d aux=%04X aux56=%d permanently_disabled=true",
  emu.framecount(),first,second,p2+0x50,before,word(0x3CE),hp,p1score,left,right,adjacent,quarter,aux,aux56))
end
local function tick()
 if installed or finished or not approved then return status() end
 assert(emu.getsystemid()=="WSWAN" and userdata.get("source_sha256")==SOURCE,
  "pinned original source only; launcher must verify its actual ROM")
 assert(userdata.get("callback_order")=="bizhawk2111-rew","calibrated source binding required")
 output=assert(userdata.get("output"))
 assert(output:match("^W:/build/[%w%-%_/]+$"),"isolated source output required")
 event.on_bus_write(apply,0x417A1,"approved-original-shoot-boss-HP1-once","System Bus")
 installed=true
 ledger("enabled approved-original-reference-only one-shot SECOND+50 WORD=1; active stage11 only; no fixed1/no directzero")
 return status()
end
local function finish()
 if not finished then
  finished=true
  if installed then ledger(string.format("finished hits=%d writes=%d applied=%s",hits,writes,tostring(applied)))end
 end
 return status()
end
return {tick=tick,status=status,finish=finish}
