-- Poll the confirmed cursor after every executed instruction for two input frames.

local output_dir = "W:/evidence/bizhawk-wsc-cursor-instruction-run1"
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
tap("P1 A", 4, 10)
advance(125)

local previous = mainmemory.read_u8(0x3116)
log(string.format("start cursor=%d frame=%d", previous, emu.framecount()))
event.onmemoryexecuteany(function(address, value, flags)
	local current = mainmemory.read_u8(0x3116)
	if current ~= previous then
		local registers = emu.getregisters()
		log(string.format(
			"change old=%d new=%d callback_addr=0x%X PS:PC=%04X:%04X physical=0x%05X frame=%d",
			previous, current, address, registers.PS, registers.PC,
			registers.PS * 16 + registers.PC, emu.framecount()
		))
		previous = current
	end
end, "cursor-instruction-trace")

tap("P1 X3", 2, 6)
log(string.format("complete cursor=%d frame=%d", mainmemory.read_u8(0x3116), emu.framecount()))
client.exit()
