-- Trace the instruction that transfers Patamon runtime ID 13 into battle state.

local output_dir = "W:/evidence/bizhawk-wsc-battle-id-trace-run1"
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
for _ = 1, 11 do tap("P1 X3", 2, 5) end
advance(24)

local previous = mainmemory.read_u16_le(0x312A)
log(string.format("before-confirm battle_id=%d cursor=%d selected_id=%d frame=%d", previous, mainmemory.read_u16_le(0x3116), mainmemory.read_u16_le(0x3100), emu.framecount()))
event.onmemoryexecuteany(function(address, value, flags)
	local current = mainmemory.read_u16_le(0x312A)
	if current ~= previous then
		local r = emu.getregisters()
		log(string.format(
			"change old=%d new=%d callback_addr=0x%X PS:PC=%04X:%04X physical=0x%05X " ..
			"AW=%04X BW=%04X CW=%04X DW=%04X IX=%04X IY=%04X BP=%04X SP=%04X frame=%d",
			previous, current, address, r.PS, r.PC, r.PS * 16 + r.PC,
			r.AW, r.BW, r.CW, r.DW, r.IX, r.IY, r.BP, r.SP, emu.framecount()
		))
		previous = current
	end
end, "battle-id-trace")

tap("P1 A", 4, 4)
advance(80)
log(string.format("complete battle_id=%d frame=%d", mainmemory.read_u16_le(0x312A), emu.framecount()))
client.exit()
