-- Trace the instructions that change the two confirmed character-index bytes.
-- Uses a savestate created from the clean GBA ROM without loading battery data.

local output_dir = "evidence/mgba-character-index-watch-run1"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local log_path = output_dir .. "/watch.log"
local marker_path = output_dir .. "/done.txt"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = nil
local finished = false

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

local function watch_index(info)
	append_log(string.format(
		"watch address=%08X width=%d old=%d new=%d access=%d pc=%08X lr=%08X frame=%d",
		info.address, info.width, info.oldValue, info.newValue, info.accessType,
		emu:readRegister("pc"), emu:readRegister("lr"), emu:currentFrame()))
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)

	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		append_log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		emu:setWatchpoint(watch_index, 0x0300473C, C.WATCHPOINT_TYPE.WRITE_CHANGE)
		emu:setWatchpoint(watch_index, 0x0300473E, C.WATCHPOINT_TYPE.WRITE_CHANGE)
		return
	end

	local frame = emu:currentFrame()
	if frame >= anchor + 30 and frame < anchor + 34 then
		emu:addKey(C.GBA_KEY.DOWN)
	end
	if frame == anchor + 230 then
		emu:screenshot(output_dir .. "/after-down.png")
	end
	if frame >= anchor + 260 and not finished then
		finished = true
		emu:setKeys(0)
		local marker = io.open(marker_path, "w")
		if marker then
			marker:write("complete\n")
			marker:close()
		end
	end
end)
