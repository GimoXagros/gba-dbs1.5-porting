-- Trace writes to the confirmed WSC character-select cursor at RAM 0x3116.

local output_dir = "W:/evidence/bizhawk-wsc-cursor-watch-run2"
local log_path = output_dir .. "/watch.log"

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
	advance(settle_frames or 10)
end

local function cursor_write(address, value, flags)
	local registers = emu.getregisters()
	log(string.format(
		"write addr=0x%X value=0x%X flags=0x%X PS:PC=%04X:%04X physical=0x%05X frame=%d",
		address, value, flags, registers.PS, registers.PC,
		registers.PS * 16 + registers.PC, emu.framecount()
	))
end
event.onmemorywrite(cursor_write, 0x3116, "roster-cursor-ram", "RAM")

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
log(string.format("at-selection cursor=%d frame=%d", mainmemory.read_u8(0x3116), emu.framecount()))
tap("P1 X3", 2, 20)
tap("P1 X3", 2, 20)
tap("P1 X1", 2, 20)
log(string.format("complete cursor=%d frame=%d", mainmemory.read_u8(0x3116), emu.framecount()))
client.exit()
