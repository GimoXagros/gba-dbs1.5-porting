-- Trace the instruction that initializes the WSC selection maximum at RAM 0x311A.

local output_dir = "W:/evidence/bizhawk-wsc-roster-init-run2"
local log_path = output_dir .. "/trace.log"

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

local previous = mainmemory.read_u16_le(0x311A)
log(string.format("before-a max=%d frame=%d", previous, emu.framecount()))
event.onmemoryexecuteany(function(address, value, flags)
	local current = mainmemory.read_u16_le(0x311A)
	if current ~= previous then
		local r = emu.getregisters()
		log(string.format(
			"change old=%d new=%d callback_addr=0x%X PS:PC=%04X:%04X physical=0x%05X " ..
			"AW=%04X BW=%04X CW=%04X DW=%04X IX=%04X IY=%04X BP=%04X SP=%04X",
			previous, current, address, r.PS, r.PC, r.PS * 16 + r.PC,
			r.AW, r.BW, r.CW, r.DW, r.IX, r.IY, r.BP, r.SP
		))
		previous = current
	end
end, "roster-init-trace")

tap("P1 A", 4, 20)
advance(120)
log(string.format("complete max=%d cursor=%d frame=%d", mainmemory.read_u16_le(0x311A), mainmemory.read_u16_le(0x3116), emu.framecount()))
client.exit()
