-- Dump video state for the internally integrated Tailmon battle probe.
-- This uses a clean selector state and never opens or loads the supplied SRAM.

local output_dir = "evidence/mgba-id14-battle-video-run4-staggered-abi"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/video.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false

local function write_binary(path, data)
	local handle = io.open(path, "wb")
	if handle then
		handle:write(data)
		handle:close()
	end
end

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then
		return 1 << key
	end
	return 0
end

local function dump_state(delta)
	local stem = string.format("frame-%04d", delta)
	emu:screenshot(output_dir .. "/" .. stem .. ".png")
	write_binary(output_dir .. "/" .. stem .. "-palette.bin",
		emu:readRange(0x05000000, 0x400))
	write_binary(output_dir .. "/" .. stem .. "-vram.bin",
		emu:readRange(0x06000000, 0x18000))
	write_binary(output_dir .. "/" .. stem .. "-oam.bin",
		emu:readRange(0x07000000, 0x400))
	write_binary(output_dir .. "/" .. stem .. "-ewram.bin",
		emu:readRange(0x02000000, 0x40000))
	write_binary(output_dir .. "/" .. stem .. "-iwram.bin",
		emu:readRange(0x03000000, 0x8000))
	append_log(string.format("dump delta=%d frame=%d pc=%08X", delta,
		emu:currentFrame(), emu:readRegister("pc")))
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, 13)
		emu:write16(0x03004714, 14)
		emu:write16(0x03004740, 2)
		emu:write16(0x0300473C, 0)
		emu:write16(0x0300473E, 0)
		append_log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		return
	end

	local frame = emu:currentFrame()
	local mask = 0
	mask = mask | pulse(frame, anchor + 30, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 210, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 390, C.GBA_KEY.A)
	if mask ~= 0 then emu:addKeys(mask) end

	local delta = frame - anchor
	if delta == 750 or delta == 900 or delta == 1050 then
		dump_state(delta)
	elseif delta >= 1070 and not finished then
		finished = true
		local marker = io.open(marker_path, "w")
		if marker then marker:write("complete\n"); marker:close() end
	end
end)
