-- Trace direct reads of WSC-only animation headers during a Patamon battle load.

local output_dir = "W:/evidence/bizhawk-wsc-patamon-asset-read-run1"
local log_path = output_dir .. "/trace.log"
local headers = { 0x23E500, 0x350000, 0x35A860, 0x3624A0, 0x3914E0 }

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function advance(count)
	for _ = 1, count do emu.frameadvance() end
end

local function tap(button, held_frames, settle_frames)
	joypad.set({ [button] = true })
	advance(held_frames or 2)
	joypad.set({})
	advance(settle_frames or 7)
end

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
for _ = 1, 11 do tap("P1 X3", 2, 5) end
advance(24)
log(string.format("selected cursor=%d id=%d frame=%d", mainmemory.read_u16_le(0x3116), mainmemory.read_u16_le(0x3100), emu.framecount()))

for _, header in ipairs(headers) do
	event.onmemoryread(function(address, value, flags)
		local r = emu.getregisters()
		log(string.format(
			"read header=0x%06X callback_addr=0x%X value=0x%X PS:PC=%04X:%04X physical=0x%05X frame=%d",
			header, address, value, r.PS, r.PC, r.PS * 16 + r.PC, emu.framecount()
		))
	end, header, string.format("header-%06X", header), "ROM")
end

tap("P1 A", 4, 4)
advance(600)
log("complete frame=" .. emu.framecount())
client.exit()
