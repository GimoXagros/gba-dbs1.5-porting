-- Explicitly approved original-reference HP1 once, then a real engine hit.
-- The frozen saved-score driver retains startup verification and all input policy.
assert(userdata.get("boss_hp1_approval")=="user-approved-original-reference-once",
 "explicit one-time original boss HP approval required")
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
local boss,pending,hit,victory=nil,nil,nil,false
local installed,root_seen,cancelled,finalized=false,false,false,false
local function log(line)
 local f=assert(io.open(out.."/boss-hit-observer.txt","a"));f:write(line.."\n");f:close()
end
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function ram(a)return mainmemory.read_u16_le(a)end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function active(p)return math.floor(ram(0xC000+p-6)/2)%2==1 end
local function pair()
 if word(0x4E)~=7 or word(0x50)~=0 or word(0x3D0)~=2 or memory.read_u8(0x5C,"SRAM")~=7 then return end
 local first,second=word(0x65C),word(0x65E)
 if not valid(first) or not valid(second) or first==second or not active(first) or not active(second) then return end
 local a,b=0xC000+first,0xC000+second
 if ram(a+4)%16~=0 or mainmemory.read_u8(a+0x10)~=0 or ram(a+0x14)~=second
  or ram(b+4)%16~=3 or mainmemory.read_u8(b+0x10)~=1 or mainmemory.read_u8(b+0x11)~=15
  or ram(b+0x14)~=first then return end
 return first,second
end
local function pin(at,bytes)
 for i,v in ipairs(bytes)do assert(memory.read_u8(at+i-1,"ROM")==v,"boss observation source pin")end
end
local function site(raw,address)
 local r=emu.getregisters()
 assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000,
  "boss observation opcode calibration")
 return r
end
local function snapshot(label)
 for domain,size in pairs({RAM=0x10000,SRAM=0x8000})do
  local f=assert(io.open(out.."/boss-hit-"..label.."-"..domain..".bin","wb"))
  f:write(memory.read_bytes_as_binary_string(0,size,domain));f:close()
 end
end
local function install()
 assert(not installed and boss,"boss observer installs once after startup guard")
 local old=io.open(out.."/boss-hit-observer.txt","rb")
 if old then old:close();error("fresh boss observation output required")end
 pin(0x760177,{0x33,0xC0,0x8A,0x46,0xFC,0xF7,0x44,0x08,0x00,0x40,0x74,0x02,0xD1,0xE8,
  0x29,0x45,0x50,0x83,0x7D,0x50,0x00})
 pin(0x7417E6,{0x26,0x8B,0x1E,0x5E,0x06,0x83,0x7F,0x50,0x00,0x7F,0x0D,
  0x6A,0x05,0x9A,0x00,0x00,0xF0,0x71,0x83,0xC4,0x02})
 pin(0x7417C7,{0x26,0x8B,0x1E,0x5C,0x06,0x83,0x7F,0x50,0x00,0x75,0x14,
  0x83,0xBF,0xA4,0x00,0x3E,0x75,0x0D,0x6A,0x04,0x9A,0x00,0x00,0xF0,0x71})
 local function observe(raw,label,fn)
  event.on_bus_write(function(address)
   if not finalized then fn(site(raw,address))end
  end,raw-0x700000,"approved-boss-hit-"..label,"System Bus")
 end
 observe(0x760185,"pre",function(r)
  if hit or cancelled or not boss.status().applied then return end
  local first,second=pair()
  if not first or r.DS0~=0x0C00 or r.IY~=second or ram(0xC000+second+0x50)~=1
   or r.AW<=0 or r.AW>255 then return end
  assert(not pending,"unpaired prior boss damage")
  pending={first=first,second=second,ps=r.PS,pc=r.PC,ds=r.DS0,si=r.IX,di=r.IY,sp=r.SP,damage=r.AW}
  pending.direct_first=r.IX==first
  log(string.format("hit_pre frame=%d PS:PC=%04X:%04X DS=%04X SI=%04X DI=%04X SP=%04X AX=%04X bossHP=1 source=760185 direct_first=%s",
   emu.framecount(),r.PS,r.PC,r.DS0,r.IX,r.IY,r.SP,r.AW,tostring(pending.direct_first)))
  if valid(r.IX) then
   local attacker=0xC000+r.IX
   log(string.format("attacker_context callback=%04X:%04X kind=%d index10=%d id11=%d ownership_beyond_direct_first=unproven",
    ram(attacker+2),ram(attacker),ram(attacker+4)%16,mainmemory.read_u8(attacker+0x10),mainmemory.read_u8(attacker+0x11)))
  else log("attacker_context valid_payload=false ownership=unproven")end
  snapshot("pre")
 end)
 observe(0x760188,"post",function(r)
  if not pending then return end
  local p=pending
  assert(r.PS==p.ps and r.PC==(p.pc+3)%0x10000 and r.DS0==p.ds and r.IX==p.si and r.IY==p.di
   and r.SP==p.sp and r.AW==p.damage,"boss damage instruction/owner changed")
  local hp=ram(0xC000+p.second+0x50)
  assert(hp==(1-p.damage)%0x10000 and (hp==0 or hp>=0x8000),"actual positive hit must produce signed lethal HP")
  hit=p;hit.after=hp;pending=nil
  log(string.format("hit_post frame=%d PS:PC=%04X:%04X FIRST=%04X SECOND=%04X damage=%d HP=%04X signed_lethal=true direct_first=%s",
   emu.framecount(),r.PS,r.PC,p.first,p.second,p.damage,hp,tostring(p.direct_first)))
  snapshot("post")
 end)
 observe(0x7417F3,"root5",function(r)
  if root_seen or not boss.status().applied then return end
  local first,second=pair()
  if not first or r.DS0~=0x0C00 or r.DS1~=0x1000 or r.BW~=second then return end
  local hp=ram(0xC000+second+0x50)
  if hp~=0 and hp<0x8000 then return end
  root_seen=true
  victory=not cancelled and hit~=nil and hit.first==first and hit.second==second
  log(string.format("root5 frame=%d PS:PC=%04X:%04X FIRST=%04X SECOND=%04X HP=%04X native_HP_victory=true engine_hit_confirmed=%s prior_root4_cancelled=%s",
   emu.framecount(),r.PS,r.PC,first,second,hp,tostring(victory),tostring(cancelled)))
  snapshot("root5")
 end)
 observe(0x7417DB,"root4",function(r)
  if cancelled or victory or not boss.status().applied then return end
  local first,second=pair()
  if not first or r.DS0~=0x0C00 or r.DS1~=0x1000 or r.BW~=first
   or ram(0xC000+first+0x50)~=0 or ram(0xC000+first+0xA4)~=0x3E then return end
  cancelled=true
  log(string.format("root4 frame=%d FIRST=%04X SECOND=%04X hit_retained=%s attempt_victory_cancelled=true never_rearm=true",
   emu.framecount(),first,second,tostring(hit~=nil)))
 end)
 installed=true
 log("enabled user_approved_HP1_once=true actual_damage_observer=owned_SECOND_victim source_callbacks=4 max_pairs=1 max_root5=1 max_root4=1 guest_writes=none_in_observer")
end
local function evidence_ready()
 if not boss then return false end
 local s=boss.status()
 return s.applied and s.writes==1 and hit~=nil and victory and not cancelled and not pending
end
local original_dofile=dofile
local function module(path)
 if path=="W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua" then return original_dofile(path)end
 assert(path=="W:/tools/bizhawk_wsc_score999.lua","unexpected saved-driver module")
 local score=original_dofile(path)
 assert(not boss,"duplicate boss module")
 -- This call is reached only after A0AC's full normalized32KiB startup equality.
 boss=original_dofile("W:/tools/bizhawk_wsc_boss_hp1_once.lua")
 install();boss.tick()
 return {tick=score.tick,status=score.status,finish=function()
  local bs=boss.finish()
  assert(not pending,"observation ended between real damage hooks")
  log(string.format("finished one_shot_written=%s boss_writes=%d engine_lethal_hit=%s native_root5_seen=%s normal_victory_after_hit=%s prior_root4_cancelled=%s",
   tostring(bs.applied),bs.writes,tostring(hit~=nil),tostring(root_seen),tostring(victory),tostring(cancelled)))
  finalized=true
  return score.finish()
 end}
end
local f=assert(io.open("W:/tools/bizhawk_probe_wsc_saved_score999.lua","rb"))
local source=assert(f:read("*a")):gsub("\r\n","\n");f:close()
local old='return s.terminal_observed and s.actual_final_irq_observed and s.paired_reads>0 and not s.pending'
local a,b=source:find(old,1,true);assert(a and not source:find(old,b+1,true),"frozen A0AC completion anchor")
source=source:sub(1,a-1)..old..' and boss_evidence_ready()'..source:sub(b+1)
local environment=setmetatable({dofile=module,boss_evidence_ready=evidence_ready},{__index=_ENV})
return assert(load(source,"@approved-boss-saved-score-parent","t",environment))()
