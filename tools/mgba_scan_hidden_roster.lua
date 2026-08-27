-- Reveal existing GBA roster indices in RAM only, without modifying the ROM
-- or loading battery save data. This identifies occupied indices before porting.

local output_dir = "evidence/mgba-hidden-roster-id11-run1"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/roster.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = nil
local finished = false
local next_index = 1

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, 11)
		emu:write16(0x03004740, 1)
		emu:screenshot(output_dir .. "/index-00.png")
		append_log(string.format("state_loaded=%s anchor=%d max_index=%d", tostring(loaded), anchor, 1))
		return
	end

	local frame = emu:currentFrame()
	if next_index <= 1 then
		local press_at = anchor + 30 + (next_index - 1) * 180
		if frame >= press_at and frame < press_at + 4 then
			emu:addKey(C.GBA_KEY.DOWN)
		end
		if frame == press_at + 150 then
			local label = string.format("index-%02d", next_index)
			emu:screenshot(output_dir .. "/" .. label .. ".png")
			append_log(string.format("capture=%s selected=%d mirror=%d frame=%d",
				label, emu:read16(0x0300473C), emu:read16(0x0300473E), frame))
			next_index = next_index + 1
		end
	elseif not finished then
		finished = true
		local marker = io.open(marker_path, "w")
		if marker then
			marker:write("complete\n")
			marker:close()
		end
	end
end)
