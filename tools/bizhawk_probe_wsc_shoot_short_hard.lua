-- Fresh ordinary-input variant. Frozen observer and collector files are read,
-- never rewritten. The launcher must hash-check both dependencies and this file.
local hard_path="W:/tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua"
local collect_path="W:/tools/bizhawk_probe_wsc_shoot_collect_v2.lua"
local release_keys=joypad.set
local function read(path)
 local f=assert(io.open(path,"rb"));local text=assert(f:read("*a"));f:close()
 return text:gsub("\r\n","\n")
end
local function replace_once(text,old,new)
 local a,b=text:find(old,1,true)
 assert(a,"frozen observer anchor missing: "..old)
 assert(not text:find(old,b+1,true),"ambiguous frozen observer anchor")
 return text:sub(1,a-1)..new..text:sub(b+1)
end
local hard=read(hard_path)
hard=replace_once(hard,'local tile_writes, lower_hits = 0, 0',
 'local tile_writes, lower_hits = 0, 0\nlocal short_timer_seen,shoot_irq_hits,shoot_row_hits=false,0,0')
hard=replace_once(hard,'score=mainmemory.read_u16_le(at+0x52),held=',
 'hp=mainmemory.read_u16_le(at+0x50),score=mainmemory.read_u16_le(at+0x52),held=')
hard=replace_once(hard,'hard_seen=true;ui_phase="exit-options";ui_button=nil',
 'hard_seen=true;ui_phase="short-time";ui_button=nil')
hard=replace_once(hard,' if ui_phase=="exit-options" and mode==3 then',[[
 if ui_phase=="short-time" and mode==14 and word(0x5E)==0 then
  short_timer_seen=true;ui_phase="exit-options";ui_button=nil
  log("short_hard timer0-confirmed frame="..frame);snapshot("options-short-hard")
 end
 if ui_phase=="exit-options" and mode==3 then]])
hard=replace_once(hard,'  elseif ui_phase=="exit-options" and mode==14 then ui_button="P1 B" end',[[
  elseif ui_phase=="short-time" and mode==14 then
   local row=mainmemory.read_u16_le(0x3118)
   ui_button=row==0 and "P1 X4" or "P1 X1"
  elseif ui_phase=="exit-options" and mode==14 then ui_button="P1 B" end]])
hard=replace_once(hard,'assert(options_seen and hard_seen and memory.read_u8(0x5D,"SRAM")==3,"natural hard route required")',
 'assert(options_seen and hard_seen and short_timer_seen and word(0x5E)==0 and memory.read_u8(0x5D,"SRAM")==3,"natural short-hard route required")')
hard=replace_once(hard,'  if label == "final-IRQ-DI" then irq_hits = irq_hits + 1 end',[[
  if label == "final-IRQ-DI" then
   irq_hits=irq_hits+1
   if memory.read_u8(0x5C,"SRAM")==11 then shoot_irq_hits=shoot_irq_hits+1 end
  end]])
hard=replace_once(hard,'  if label == "row-clear-live-in" then terminal_hits = terminal_hits + 1 end',[[
  if label == "row-clear-live-in" then
   terminal_hits=terminal_hits+1
   if memory.read_u8(0x5C,"SRAM")==11 then shoot_row_hits=shoot_row_hits+1 end
  end]])
hard=replace_once(hard,' if frame%300==0 and first and other then',[[
 if frame%300==0 and first and other then
  log(string.format("short_hard actors relative=%d stage=%d mode=%d timer_selector=%d timer=%d p1hp=%d p2hp=%d p1score=%d p2score=%d",
   frame,stage,mode,word(0x5E),word(0x3CE),first.hp,other.hp,first.score,other.score))]])
hard=replace_once(hard,' emu.frameadvance()\nend',[[
 if shoot_row_hits>0 and shoot_irq_hits>0 and shoot_frames>=300 then
  log(string.format("short_hard early-stop relative=%d shoot_frames=%d shoot_row_hits=%d shoot_irq_hits=%d",frame,shoot_frames,shoot_row_hits,shoot_irq_hits))
  break
 end
 emu.frameadvance()
end]])
hard=replace_once(hard,'assert(options_seen and hard_seen and battle_seen,"hard UI route did not reach a verified battle")',
 'assert(options_seen and hard_seen and short_timer_seen and battle_seen,"short-hard UI route did not reach a verified battle")')
hard=replace_once(hard,'joypad.set(release)','short_hard_release(release)')
local collect=read(collect_path)
-- Stage7 is an HP boss: collecting its dropped score orbs must not suppress B.
collect=replace_once(collect,'if mode==7 and stage~=11 and player>=0x24',
 'if mode==7 and stage~=7 and stage~=11 and player>=0x24')
local environment=setmetatable({dofile=function(path)
 assert(path==hard_path,"unexpected observer dependency")
 local hard_environment=setmetatable({short_hard_release=release_keys},{__index=_ENV})
 return assert(load(hard,"@short-hard-expanded","t",hard_environment))()
end},{__index=_ENV})
return assert(load(collect,"@short-hard-collector","t",environment))()
