-- Verify the integrated clean-save roster from boot without loading SRAM.

local output_dir = "evidence/mgba-roster-policy-run1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/roster.log"
local all_keys = (1 << 10) - 1
local state = "wait_title"
local anchor = 0
local finished = false

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then return 1 << key end
	return 0
end

callbacks:add("frame", function()
	local frame = emu:currentFrame()
	emu:clearKeys(all_keys)
	if state == "wait_title" and frame > 500 then
		local screen = emu:screenshotToImage()
		if (screen:getPixel(150, 109) & 0xFFFFFF) == 0
			and (screen:getPixel(120, 80) & 0xFFFFFF) == 0x5A0000
			and (screen:getPixel(120, 60) & 0xFFFFFF) == 0x00298C then
			anchor = frame
			state = "route"
		end
	end
	if state == "route" then
		local mask = 0
		mask = mask | pulse(frame, anchor, C.GBA_KEY.START)
		mask = mask | pulse(frame, anchor + 160, C.GBA_KEY.A)
		if mask ~= 0 then emu:addKeys(mask) end
		local delta = frame - anchor
		if delta == 280 then
			emu:screenshot(output_dir .. "/character-select.png")
			local max_index = emu:read16(0x03004740)
			local values = {}
			for index = 0, max_index do
				values[#values + 1] = tostring(emu:read16(0x03004710 + index * 2))
			end
			local h = io.open(log_path, "w")
			if h then
				h:write(string.format("max_index=%d roster=%s\n", max_index,
					table.concat(values, ",")))
				h:close()
			end
		elseif delta >= 300 and not finished then
			finished = true
			local h = io.open(marker_path, "w")
			if h then h:write("complete\n"); h:close() end
		end
	end
end)
