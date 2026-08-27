-- Final WSC 1.5 reference QA using the user-supplied 32 KiB cartridge save.
-- The original save is never opened for writing; an isolated BizHawk SaveRAM copy is used.

local output_dir = "../QAUserSaveFinal1"
local log_path = output_dir .. "/verification.log"

local function log(line)
	local handle = assert(io.open(log_path, "a"))
	handle:write(line .. "\n")
	handle:close()
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

local function roster_line(max_index)
	local values = {}
	for index = 0, max_index do
		values[#values + 1] = tostring(mainmemory.read_u16_le(0x30EA + index * 2))
	end
	return table.concat(values, ",")
end

client.speedmode(800)
log("system=" .. emu.getsystemid())
advance(3900)
client.screenshot(output_dir .. "/00-title.png")
tap("P1 Start", 4, 10)
advance(70)
client.screenshot(output_dir .. "/01-main-menu.png")
tap("P1 A", 4, 10)
advance(125)

local max_index = mainmemory.read_u16_le(0x311A)
local cursor = mainmemory.read_u16_le(0x3116)
log(string.format("selection max_index=%d count=%d cursor=%d roster=%s frame=%d",
	max_index, max_index + 1, cursor, roster_line(max_index), emu.framecount()))
client.screenshot(output_dir .. "/02-selection-default.png")

for index = 1, max_index do
	tap("P1 X3", 2, 5)
	advance(12)
	local selected_id = mainmemory.read_u16_le(0x30EA + index * 2)
	log(string.format("entry index=%d id=%d cursor=%d frame=%d",
		index, selected_id, mainmemory.read_u16_le(0x3116), emu.framecount()))
	client.screenshot(string.format("%s/entry-%02d-id-%02d.png", output_dir, index, selected_id))
end

log("complete frame=" .. emu.framecount())
client.exit()
