-- Original WSC observations only: ordinary controller input, no guest writes.
local out = assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
local limit = userdata.get("frames") or 30000
assert(userdata.get("callback_order") == "bizhawk2111-rew", "hash-checked BizHawk 2.11.1 callback contract required")
local initial = emu.framecount()
local callbacks, accesses, shoot_frames, terminal_hits, irq_hits, calibrated = 0, 0, 0, 0, 0, 0
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
}
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
  if count <= 256 then
   log(string.format("exec label=%s frame=%d count=%d raw=%06X camera=%04X flags=%04X %s",
    label,emu.framecount(),count,raw,word(0x1E0),word(0x3D8),text))
  end
 end, raw - 0x700000, label, "System Bus")
end
client.speedmode(800)
local buttons = {"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local presses = {{3900,4,"P1 Start"},{3994,4,"P1 A"},{4143,4,"P1 A"}}
local prior_input, prior_stage, sampled_terminal = "", -1, 0
for frame = 0, limit - 1 do
 local keys = {}
 for _, button in ipairs(buttons) do keys[button] = false end
 for _, p in ipairs(presses) do
  if frame >= p[1] and frame < p[1] + p[2] then keys[p[3]] = true end
 end
 local stage = memory.read_u8(0x5C,"SRAM")
 if frame >= 4500 then
  -- Ordinary attack/jump pulses and horizontal sweeps; success is observed, never forced.
  keys["P1 B"] = frame % 45 < 5
  keys["P1 A"] = frame % 121 < 5
  keys["P1 X2"] = frame % 600 < 180
  keys["P1 X4"] = frame % 600 >= 300 and frame % 600 < 480
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
 if terminal_hits > sampled_terminal then snapshot("terminal-" .. terminal_hits); sampled_terminal=terminal_hits end
 emu.frameadvance()
end
local release = {}; for _, button in ipairs(buttons) do release[button]=false end; joypad.set(release)
snapshot("final")
assert(calibrated > 0, "no frame-wait execution calibration; observation invalid")
assert(memory_calibration.read > 0 and memory_calibration.write > 0, "no stage read/write calibration; storage observation invalid")
log(string.format("memory_calibration reads=%d writes=%d",memory_calibration.read,memory_calibration.write))
log(string.format("complete frame=%d callbacks=%d storage_accesses=%d shoot_frames=%d terminal_hits=%d final_irq_hits=%d calibrated=%d",emu.framecount(),callbacks,accesses,shoot_frames,terminal_hits,irq_hits,calibrated))
local f=assert(io.open(out .. "/done.txt","w"));f:write("observation-complete");f:close()
client.exit()
