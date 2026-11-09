-- Authorized original-only save-copy observation, using ordinary input only.
local out = assert(userdata.get("output"))
local phase = assert(userdata.get("phase"))
assert(out:match("^W:/build/bizhawk%-wsc%-saved%-20261109%-%w+$"))
assert(phase == "calibration" or phase == "menu")
assert(emu.getsystemid() == "WSWAN")
assert(memory.getmemorydomainsize("ROM") == 0x800000)
assert(memory.getmemorydomainsize("SRAM") == 0x8000)
assert(memory.getmemorydomainsize("iEEPROM") == 1024)
local function write(name, data)
 local f = assert(io.open(out .. "/" .. name, "wb")); f:write(data); f:close()
end
local function dump(name, domain, size)
 write(name, memory.read_bytes_as_binary_string(0, size, domain))
end
local function log(line)
 local f = assert(io.open(out .. "/trace.txt", "a")); f:write(line .. "\n"); f:close()
end
local function snapshot(name)
 dump(name .. "-ram.bin", "RAM", 0x10000)
 dump(name .. "-sram.bin", "SRAM", 0x8000)
 client.screenshot(out .. "/" .. name .. ".png")
 log(string.format("snapshot=%s core=%d mode=%04X stage=%d", name, emu.framecount(),
  memory.read_u16_le(0x4E, "SRAM"), memory.read_u8(0x5C, "SRAM")))
end
dump("loaded-rom.bin", "ROM", 0x800000)
dump("initial-sram.bin", "SRAM", 0x8000)
dump("internal-eeprom.bin", "iEEPROM", 1024)
log("phase=" .. phase .. " initial_core=" .. emu.framecount() .. " input=joypad-only guest_writes=none")
if phase == "menu" then
 local f = assert(io.open(out .. "/authorized-cartridge-copy.bin", "rb"))
 local expected = f:read("*a"); f:close()
 assert(expected == memory.read_bytes_as_binary_string(0, 0x8000, "SRAM"), "actual loaded cartridge save must equal authorized copy before inputs")
 log("initial_cartridge_copy_exact=true")
 client.speedmode(800)
 for frame=0,4200 do
  if frame==3900 or frame==3904 then log("input relative=" .. frame .. " core=" .. emu.framecount() .. " Start=" .. tostring(frame==3900)) end
  joypad.set({["P1 Start"]=frame>=3900 and frame<3904})
  if frame==3900 then snapshot("title") end
  if frame==4200 then snapshot("menu") end
  emu.frameadvance()
 end
 joypad.set({})
end
write("done.txt", phase .. "-complete")
client.exit()
