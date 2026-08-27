-- Re-enter character selection from a clean-ROM state so the patched roster
-- initializer runs without waiting through the opening duel.

local output_dir = "evidence/mgba-roster-reentry-run2"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then return 1 << key end
	return 0
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		return
	end
	local frame = emu:currentFrame()
	local mask = pulse(frame, anchor + 30, C.GBA_KEY.B)
	mask = mask | pulse(frame, anchor + 240, C.GBA_KEY.START)
	mask = mask | pulse(frame, anchor + 400, C.GBA_KEY.A)
	if mask ~= 0 then emu:addKeys(mask) end
	local delta = frame - anchor
	if delta == 180 then emu:screenshot(output_dir .. "/after-exit.png") end
	if delta == 680 then
		emu:screenshot(output_dir .. "/after-reentry.png")
		local max_index = emu:read16(0x03004740)
		local values = {}
		for index = 0, max_index do
			values[#values + 1] = tostring(emu:read16(0x03004710 + index * 2))
		end
		local h = io.open(output_dir .. "/roster.log", "w")
		if h then h:write(string.format("max_index=%d roster=%s\n", max_index,
			table.concat(values, ","))); h:close() end
	elseif delta >= 700 then
		local h = io.open(marker_path, "w")
		if h then h:write("complete\n"); h:close() end
	end
end)
