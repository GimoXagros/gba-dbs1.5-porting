-- Original WSC observations only: ordinary controller input, no guest writes.
local out = assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
local limit = userdata.get("frames") or 30000
assert(userdata.get("callback_order") == "bizhawk2111-rew", "hash-checked BizHawk 2.11.1 callback contract required")
local initial = emu.framecount()
local callbacks, accesses, shoot_frames, terminal_hits, irq_hits, calibrated = 0, 0, 0, 0, 0, 0
local tile_writes, lower_hits = 0, 0
local memory_calibration = {read=0,write=0}
local function log(line)
 local f = assert(io.open(out .. "/trace.txt", "a")); f:write(line .. "\n"); f:close()
end
local function dump(name, domain, start, length)
 local f = assert(io.open(out .. "/" .. name, "wb"))
 f:write(memory.read_bytes_as_binary_string(start, length, domain)); f:close()
end
local function registers()
 local r = emu.getregisters()
 return r, string.format("PS:PC=%04X:%04X DS=%04X ES=%04X BX=%04X SI=%04X DI=%04X AX=%04X CX=%04X SP=%04X",
  r.PS,r.PC,r.DS0,r.DS1,r.BW,r.IX,r.IY,r.AW,r.CW,r.SP)
end
local function word(address)
 return memory.read_u16_le(address, "SRAM")
end
local function actor(handle)
 local offset=word(handle)
 -- Source allocator's 52 normal payloads: 0024 + 0110*n in DS0C00.
 if offset < 0x24 or offset > 0x3654 or (offset-0x24)%0x110~=0 then return nil end
 local at=0xC000+offset
 return {at=at,x=mainmemory.read_u16_le(at+0x26),y=mainmemory.read_u16_le(at+0x28),
  score=mainmemory.read_u16_le(at+0x52),held=mainmemory.read_u16_le(at+0x1E),edge=mainmemory.read_u16_le(at+0x20)}
end
local function chase(keys,first,other,frame,stationary)
 local dx=other.x-first.x
 keys["P1 X2"]=dx>0x40
 keys["P1 X4"]=dx < -0x40
 -- Source80 is the attack edge,40 jump. Chase the opponent to collect drops.
 keys["P1 A"]=(other.y+0x100<first.y or stationary>120 and math.abs(dx)>0x200) and frame%90<8
 keys["P1 B"]=math.abs(dx)<0x300 and math.abs(other.y-first.y)<0x200 and not keys["P1 A"] and frame%18<12
end
do
 local keys={}
 chase(keys,{x=0x400,y=0xC00},{x=0x600,y=0xC00},4500,0)
 assert(keys["P1 X2"] and not keys["P1 X4"] and keys["P1 B"] and not keys["P1 A"])
 chase(keys,{x=0x800,y=0xC00},{x=0x400,y=0xA00},4500,0)
 assert(keys["P1 X4"] and not keys["P1 X2"] and keys["P1 A"] and not keys["P1 B"])
 chase(keys,{x=0x800,y=0xC00},{x=0x800,y=0xC00},4512,0)
 assert(not keys["P1 X4"] and not keys["P1 X2"] and not keys["P1 B"] and not keys["P1 A"])
 chase(keys,{x=0x400,y=0xC00},{x=0x1000,y=0xC00},4500,0)
 assert(keys["P1 X2"] and not keys["P1 B"] and not keys["P1 A"])
end
local function snapshot(label)
 dump(label .. "-ram.bin", "RAM", 0, 0x10000)
 dump(label .. "-sram.bin", "SRAM", 0, 0x8000)
 client.screenshot(out .. "/" .. label .. ".png")
end
assert(emu.getsystemid() == "WSWAN", "original WSC core required")
assert(memory.getmemorydomainsize("ROM") == 0x800000)
assert(memory.getmemorydomainsize("SRAM") == 0x8000)
log("system=WSWAN guest_writes=none savestate=none supplied_save=none input=joypad-only")
log("initial_core_frame=" .. initial .. " schedule=relative-to-script-start")
-- 2.11.1 managed R,W,E is passed to native R,E,W. These are observers, not writes.
local observe_execute, observe_write = event.on_bus_write, event.on_bus_exec
log("backend_callback_adaptation=managed-RWE/native-REW execute=on_bus_write write=on_bus_exec read=unchanged")
local bus_scope = false
for _, scope in pairs(event.availableScopes()) do log("scope=" .. scope); if scope == "System Bus" then bus_scope=true end end
assert(bus_scope, "System Bus callback scope required")
dump("loaded-rom.bin", "ROM", 0, 0x800000)
for _, operation in ipairs({"read","write"}) do
 local register = operation == "read" and event.on_bus_read or observe_write
 register(function(at,value,flags)
  memory_calibration[operation] = memory_calibration[operation]+1
  if memory_calibration[operation]<=2 then
   local _,text=registers()
   log(string.format("calibration_%s frame=%d address=%05X value=%X flags=%X %s",operation,emu.framecount(),at,value or 0,flags or 0,text))
  end
 end,0x1005C,"stage-calibration-" .. operation,"System Bus")
end
-- Observe the backing bytes, so all C1 bank selections and 32 KiB aliases count.
for _, alias in ipairs({0x13CD8,0x1BCD8}) do
for address = alias, alias + 3 do
 for _, operation in ipairs({"read", "write"}) do
  local register = operation == "read" and event.on_bus_read or observe_write
  register(function(at, value, flags)
   accesses = accesses + 1
   local _, text = registers()
   log(string.format("storage_%s frame=%d address=%05X backing_value=%X callback_value=%X flags=%X %s",
    operation, emu.framecount(), at, memory.read_u8(at % 0x8000,"SRAM"), value or 0, flags or 0, text))
  end, address, string.format("shoot-storage-%s-%05X", operation,address), "System Bus")
 end
end
end
local sites = {
 {0x747A68,"initializer"}, {0x747CE2,"storage-clear"},
 {0x772DEA,"scene-entry"}, {0x773650,"terminal-entry"},
 {0x7738CA,"row-clear-live-in"}, {0x75FC90,"final-IRQ-DI"},
 {0x750EBD,"frame-wait-calibration"},
 {0x7497F3,"lower-8EF3-spatial"},
}
for address=0x4000,0x401F do
 observe_write(function(at)
  tile_writes=tile_writes+1
  if memory.read_u8(0x5C,"SRAM")==11 or tile_writes<=64 then
   local _,text=registers()
   log(string.format("tile0_write frame=%d address=%04X after=%02X stage=%d %s",emu.framecount(),at,mainmemory.read_u8(at),memory.read_u8(0x5C,"SRAM"),text))
  end
 end,address,"common-tile0-write-"..address,"System Bus")
end
for _, site in ipairs(sites) do
 local raw, label, count = site[1], site[2], 0
 observe_execute(function(address)
  count = count + 1
  callbacks = callbacks + 1
  local r, text = registers()
  local physical = (r.PS * 16 + r.PC) % 0x100000
  -- A callback scope mismatch must not turn into claimed source execution.
  -- FETCHOP increments PC while forming the callback argument, before execution.
  assert(address == raw - 0x700000 and physical == (address+1)%0x100000, "System Bus fetch address/register mismatch")
  if label == "frame-wait-calibration" then calibrated = calibrated + 1 end
  if label == "frame-wait-calibration" and count > 2 then return end
  if label == "row-clear-live-in" then terminal_hits = terminal_hits + 1 end
  if label == "final-IRQ-DI" then irq_hits = irq_hits + 1 end
  if label == "lower-8EF3-spatial" then
   assert(r.DS0==0x0C00 and r.IX+0x8E<=0x4000,"lower object RAM domain")
   lower_hits=lower_hits+1
   log(string.format("lower_spatial frame=%d X=%04X capturedY=%04X",emu.framecount(),mainmemory.read_u16_le(0xC000+r.IX+0x26),mainmemory.read_u16_le(0xC000+r.IX+0x8C)))
  end
  if count <= 256 then
   log(string.format("exec label=%s frame=%d count=%d raw=%06X camera=%04X flags=%04X %s",
    label,emu.framecount(),count,raw,word(0x1E0),word(0x3D8),text))
  end
 end, raw - 0x700000, label, "System Bus")
end
client.speedmode(800)
local buttons = {"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local presses = {{3900,4,"P1 Start"}}
-- Source title ready callback 7FFB:067B; payload begins header+10.
local function title_selection()
 for slot=0,51 do
  local at=0xC014+slot*0x110
  if mainmemory.read_u16_le(at)==0x067B and mainmemory.read_u16_le(at+2)==0x7FFB then
   return mainmemory.read_u8(at+0x14),mainmemory.read_u8(at+0x15)
  end
 end
end
local ui_phase,ui_button,options_seen,hard_seen,battle_seen="title-options",nil,false,false,false
local function hard_ui(keys,mode,frame)
 local difficulty=memory.read_u8(0x5D,"SRAM")
 if ui_phase=="title-options" and mode==14 then
  options_seen=true;ui_phase="difficulty";ui_button=nil
  log("hard_ui options-enter frame="..frame);snapshot("options-enter")
 end
 if ui_phase=="difficulty" and difficulty==3 then
  hard_seen=true;ui_phase="exit-options";ui_button=nil
  log("hard_ui difficulty3 frame="..frame);snapshot("options-hard")
 end
 if ui_phase=="exit-options" and mode==3 then
  ui_phase="campaign";ui_button=nil
  log("hard_ui title-return frame="..frame)
 end
 if ui_phase=="campaign" then return false end
 if frame%60==0 then
  ui_button=nil
  if ui_phase=="title-options" and mode==3 then
   local tree,row=title_selection()
   log(string.format("hard_ui title-ready frame=%d tree=%s row=%s",frame,tostring(tree),tostring(row)))
   if tree==0 then ui_button=row==2 and "P1 A" or "P1 X3" end
  elseif ui_phase=="difficulty" and mode==14 then
   local row=mainmemory.read_u16_le(0x3118)
   log(string.format("hard_ui options frame=%d row=%d difficulty=%d",frame,row,difficulty))
   ui_button=row==1 and "P1 X2" or "P1 X3"
  elseif ui_phase=="exit-options" and mode==14 then ui_button="P1 B" end
 end
 if frame%60<4 and ui_button then keys[ui_button]=true end
 return true
end
local prior_input, prior_stage, sampled_terminal, window_x, stationary = "", -1, 0, nil, 0
for frame = 0, limit - 1 do
 local keys = {}
 for _, button in ipairs(buttons) do keys[button] = false end
 for _, p in ipairs(presses) do
  if frame >= p[1] and frame < p[1] + p[2] then keys[p[3]] = true end
 end
 local stage = memory.read_u8(0x5C,"SRAM")
 local mode=word(0x4E)
 local first,other=actor(0x65C),actor(0x65E)
 local configuring=frame>=3960 and hard_ui(keys,mode,frame)
 if frame >= 3960 and not configuring then
  if mode==7 and first and other then
   assert(options_seen and hard_seen and memory.read_u8(0x5D,"SRAM")==3,"natural hard route required")
   if not battle_seen then battle_seen=true;log("hard_ui battle-confirmed frame="..frame);snapshot("hard-battle") end
   if frame%90==0 then
    stationary=window_x and math.abs(window_x-first.x)<0x80 and stationary+90 or 0
    window_x=first.x
   end
   chase(keys,first,other,frame,stationary)
  elseif mode==3 then
   local tree,row=title_selection()
   if tree==0 then
    keys[row==0 and "P1 A" or "P1 X1"]=frame%90<4
   else keys["P1 Start"]=frame%90<4 end
  else
   keys["P1 A"]=frame%90<4
  end
 end
 joypad.set(keys)
 local active = {}
 for _, button in ipairs(buttons) do if keys[button] then active[#active+1] = button end end
 local input = table.concat(active,",")
 if input ~= prior_input then log("input relative=" .. frame .. " core=" .. emu.framecount() .. " keys=" .. input); prior_input=input end
 if stage == 11 then shoot_frames = shoot_frames + 1 end
 if stage ~= prior_stage or frame % 600 == 0 then
  log(string.format("state relative=%d core=%d stage=%d difficulty=%d progress=%04X camera=%04X flags=%04X callbacks=%d accesses=%d RAM5C=%04X",
   frame,emu.framecount(),stage,memory.read_u8(0x5D,"SRAM"),word(0x68),word(0x1E0),word(0x3D8),callbacks,accesses,mainmemory.read_u16_le(0x5C)))
  prior_stage=stage
 end
 if frame%300==0 and first and other then
  log(string.format("actors relative=%d mode=%d p1=%04X,%04X score=%d held=%04X edge=%04X p2=%04X,%04X score=%d",frame,mode,first.x,first.y,first.score,first.held,first.edge,other.x,other.y,other.score))
 end
 if frame==4600 or frame==6000 or frame==9000 then snapshot("progress-"..frame) end
 if terminal_hits > sampled_terminal then snapshot("terminal-" .. terminal_hits); sampled_terminal=terminal_hits end
 emu.frameadvance()
end
local release = {}; for _, button in ipairs(buttons) do release[button]=false end; joypad.set(release)
snapshot("final")
assert(options_seen and hard_seen and battle_seen,"hard UI route did not reach a verified battle")
assert(calibrated > 0, "no frame-wait execution calibration; observation invalid")
assert(memory_calibration.read > 0 and memory_calibration.write > 0, "no stage read/write calibration; storage observation invalid")
log(string.format("memory_calibration reads=%d writes=%d",memory_calibration.read,memory_calibration.write))
log(string.format("extra_observers tile0_writes=%d lower_spatial_hits=%d",tile_writes,lower_hits))
log(string.format("complete frame=%d callbacks=%d storage_accesses=%d shoot_frames=%d terminal_hits=%d final_irq_hits=%d calibrated=%d",emu.framecount(),callbacks,accesses,shoot_frames,terminal_hits,irq_hits,calibrated))
local f=assert(io.open(out .. "/done.txt","w"));f:write("observation-complete");f:close()
client.exit()
