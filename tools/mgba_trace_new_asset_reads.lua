-- Trace candidate ID-13 P0/P1 reads from a clean selector state.

local output_dir = "evidence/mgba-new-asset-read-trace-run1"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local log_path = output_dir .. "/trace.log"
local marker_path = output_dir .. "/done.txt"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false
local hits = 0

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function watched(info)
	if hits >= 400 then return end
	hits = hits + 1
	append_log(string.format(
		"hit=%d frame=%d addr=%08X width=%d pc=%08X lr=%08X r0=%08X r1=%08X r2=%08X r3=%08X",
		hits, emu:currentFrame(), info.address, info.width,
		emu:readRegister("pc"), emu:readRegister("lr"),
		emu:readRegister("r0"), emu:readRegister("r1"),
		emu:readRegister("r2"), emu:readRegister("r3")))
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, 13)
		emu:write16(0x03004740, 1)
		for address = 0x08400000, 0x08400100, 4 do
			emu:setWatchpoint(watched, address, C.WATCHPOINT_TYPE.READ)
		end
		for address = 0x084A2180, 0x084A2300, 4 do
			emu:setWatchpoint(watched, address, C.WATCHPOINT_TYPE.READ)
		end
		append_log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		return
	end
	local frame = emu:currentFrame()
	if frame >= anchor + 30 and frame < anchor + 34 then
		emu:addKey(C.GBA_KEY.DOWN)
	end
	if frame == anchor + 200 then
		emu:screenshot(output_dir .. "/after-down.png")
	end
	if frame >= anchor + 240 and not finished then
		finished = true
		append_log(string.format("complete hits=%d", hits))
		local marker = io.open(marker_path, "w")
		if marker then marker:write("complete\n"); marker:close() end
	end
end)
