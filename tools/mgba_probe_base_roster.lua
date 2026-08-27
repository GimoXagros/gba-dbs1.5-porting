-- Internal fresh-state probe for the candidate base ID-13/14 integration.
-- It loads a clean-ROM selector state and never loads the user-supplied SRAM.

local output_dir = "evidence/mgba-base-roster-probe-run12-battle"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/probe.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false
local loader_hits = 0
local selection_hits = 0
local dma_hits = 0
local cursor_watch_hits = 0

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

local function loader_break(info)
	if loader_hits >= 40 then return end
	loader_hits = loader_hits + 1
	local sp = emu:readRegister("sp")
	append_log(string.format(
		"loader hit=%d frame=%d r0=%08X r1=%08X r2=%08X r3=%08X s0=%08X s1=%08X s2=%08X s6=%08X s7=%08X",
		loader_hits, emu:currentFrame(), emu:readRegister("r0"),
		emu:readRegister("r1"), emu:readRegister("r2"), emu:readRegister("r3"),
		emu:read32(sp), emu:read32(sp + 4), emu:read32(sp + 8),
		emu:read32(sp + 24), emu:read32(sp + 28)))
end

local function selection_break(info)
	if selection_hits >= 80 then return end
	selection_hits = selection_hits + 1
	append_log(string.format(
		"portrait hit=%d frame=%d id=%08X lr=%08X cursor=%04X mirror=%04X",
		selection_hits, emu:currentFrame(), emu:readRegister("r1"),
		emu:readRegister("lr"), emu:read16(0x0300473C), emu:read16(0x0300473E)))
end

local function dma_break(info)
	if emu:currentFrame() < anchor + 380 or dma_hits >= 240 then return end
	dma_hits = dma_hits + 1
	append_log(string.format("dma hit=%d frame=%d pc=%08X src=%08X dst=%08X words=%08X",
		dma_hits, emu:currentFrame(), emu:readRegister("pc"),
		emu:readRegister("r4"), emu:readRegister("r5"), emu:readRegister("r2")))
end

local function cursor_watch(info)
	cursor_watch_hits = cursor_watch_hits + 1
	append_log(string.format(
		"cursor_write hit=%d frame=%d old=%04X new=%04X pc=%08X lr=%08X sp=%08X",
		cursor_watch_hits, emu:currentFrame(), info.oldValue, info.newValue,
		emu:readRegister("pc"), emu:readRegister("lr"), emu:readRegister("sp")))
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
		emu:setBreakpoint(loader_break, 0x08353304)
		emu:setBreakpoint(selection_break, 0x084A5C40)
		emu:setWatchpoint(cursor_watch, 0x0300473C, C.WATCHPOINT_TYPE.WRITE_CHANGE)
		emu:screenshot(output_dir .. "/00-id00.png")
		append_log(string.format(
			"state_loaded=%s anchor=%d roster=%d,%d,%d max=%d",
			tostring(loaded), anchor,
			emu:read16(0x03004710), emu:read16(0x03004712),
			emu:read16(0x03004714), emu:read16(0x03004740)))
		return
	end

	local frame = emu:currentFrame()
	local mask = 0
	mask = mask | pulse(frame, anchor + 30, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 210, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 390, C.GBA_KEY.A)
	if mask ~= 0 then
		emu:addKeys(mask)
	end

	local delta = frame - anchor
	if delta >= 450 and delta <= 800 and delta % 20 == 0 then
		append_log(string.format(
			"frame_state delta=%d pc=%08X lr=%08X sp=%08X cursor=%04X state2d68=%08X",
			delta, emu:readRegister("pc"), emu:readRegister("lr"), emu:readRegister("sp"),
			emu:read16(0x0300473C), emu:read32(0x03002D68)))
	end
	if delta == 170 then
		emu:screenshot(output_dir .. "/01-id13-selected.png")
		append_log(string.format("selected cursor=%04X mirror=%04X",
			emu:read16(0x0300473C), emu:read16(0x0300473E)))
	elseif delta == 350 then
		emu:screenshot(output_dir .. "/02-id14-selected.png")
		append_log(string.format("selected cursor=%04X mirror=%04X",
			emu:read16(0x0300473C), emu:read16(0x0300473E)))
	elseif delta == 450 or delta == 500 or delta == 600 or delta == 750 or delta == 900 or delta == 1050 or delta == 1200 then
		local name = string.format("02-after-confirm-%04d.png", delta)
		emu:screenshot(output_dir .. "/" .. name)
		append_log(string.format("delta=%d cursor=%04X mirror=%04X", delta,
			emu:read16(0x0300473C), emu:read16(0x0300473E)))
	elseif delta >= 1220 and not finished then
		finished = true
		append_log(string.format("complete loader_hits=%d selection_hits=%d dma_hits=%d",
			loader_hits, selection_hits, dma_hits))
		local marker = io.open(marker_path, "w")
		if marker then
			marker:write("complete\n")
			marker:close()
		end
	end
end)
