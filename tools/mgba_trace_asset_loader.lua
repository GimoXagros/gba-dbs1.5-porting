-- Trace the central indexed asset-loader call after choosing Guilmon.
-- Uses a clean-ROM savestate and does not load battery save data.

local output_dir = "evidence/mgba-asset-loader-variant-run1"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local log_path = output_dir .. "/loader.log"
local marker_path = output_dir .. "/done.txt"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = nil
local finished = false
local hits = 0

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

local function loader_break(info)
	if hits >= 80 then
		return
	end
	hits = hits + 1
	local sp = emu:readRegister("sp")
	append_log(string.format(
		"hit=%d frame=%d pc=%08X sp=%08X r0=%08X r1=%08X r2=%08X r3=%08X s0=%08X s1=%08X s2=%08X s6=%08X s7=%08X s8=%08X",
		hits, emu:currentFrame(), emu:readRegister("pc"), sp,
		emu:readRegister("r0"), emu:readRegister("r1"),
		emu:readRegister("r2"), emu:readRegister("r3"),
		emu:read32(sp), emu:read32(sp + 4), emu:read32(sp + 8),
		emu:read32(sp + 24), emu:read32(sp + 28), emu:read32(sp + 32)))
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		append_log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		emu:setBreakpoint(loader_break, 0x08353304)
		return
	end

	local frame = emu:currentFrame()
	if frame >= anchor + 30 and frame < anchor + 34 then
		emu:addKey(C.GBA_KEY.RIGHT)
	end
	if frame == anchor + 210 then
		emu:screenshot(output_dir .. "/variant-selected.png")
		append_log(string.format("variant selected=%04X mirror=%04X",
			emu:read16(0x0300473C), emu:read16(0x0300473E)))
	end
	if frame >= anchor + 240 and frame < anchor + 244 then
		emu:addKey(C.GBA_KEY.A)
	end
	if frame == anchor + 850 then
		emu:screenshot(output_dir .. "/after-select.png")
	end
	if frame >= anchor + 880 and not finished then
		finished = true
		emu:setKeys(0)
		append_log(string.format("complete hits=%d", hits))
		local marker = io.open(marker_path, "w")
		if marker then
			marker:write("complete\n")
			marker:close()
		end
	end
end)
