-- Capture deterministic character-select states and RAM snapshots.
-- This script deliberately does not load any battery save data.

local output_dir = "evidence/mgba-character-select-run4"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/trace.log"
local all_keys = (1 << 10) - 1
local state = "wait_title"
local anchor = nil
local finished = false

local function append_log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

local function write_binary(path, data)
	local handle = io.open(path, "wb")
	if not handle then
		append_log("failed_to_open=" .. path)
		return false
	end
	handle:write(data)
	handle:close()
	return true
end

local function capture(label, save_state)
	emu:screenshot(output_dir .. "/" .. label .. ".png")
	write_binary(output_dir .. "/" .. label .. "-ewram.bin",
		emu:readRange(0x02000000, 0x40000))
	write_binary(output_dir .. "/" .. label .. "-iwram.bin",
		emu:readRange(0x03000000, 0x8000))
	if save_state then
		emu:saveStateFile(output_dir .. "/" .. label .. ".ss1")
	end
	append_log(string.format("capture=%s frame=%d", label, emu:currentFrame()))
end

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then
		return 1 << key
	end
	return 0
end

callbacks:add("frame", function()
	local frame = emu:currentFrame()
	emu:clearKeys(all_keys)

	if state == "wait_title" and frame > 500 then
		local screen = emu:screenshotToImage()
		local prompt = screen:getPixel(150, 109) & 0xFFFFFF
		local logo_a = screen:getPixel(120, 80) & 0xFFFFFF
		local logo_b = screen:getPixel(120, 60) & 0xFFFFFF
		if prompt == 0 and logo_a == 0x5A0000 and logo_b == 0x00298C then
			anchor = frame
			state = "route"
			append_log(string.format("title_detected_frame=%d", frame))
		end
	end

	if state == "route" then
		local mask = 0
		mask = mask | pulse(frame, anchor, C.GBA_KEY.START)
		mask = mask | pulse(frame, anchor + 160, C.GBA_KEY.A)
		mask = mask | pulse(frame, anchor + 320, C.GBA_KEY.DOWN)
		mask = mask | pulse(frame, anchor + 560, C.GBA_KEY.DOWN)
		mask = mask | pulse(frame, anchor + 800, C.GBA_KEY.UP)
		if mask ~= 0 then
			emu:addKeys(mask)
		end

		local delta = frame - anchor
		if delta == 280 then
			capture("select-00", true)
		elseif delta == 520 then
			capture("select-01", false)
		elseif delta == 760 then
			capture("select-02", false)
		elseif delta == 1000 then
			capture("select-01-return", false)
		elseif delta >= 1040 and not finished then
			finished = true
			emu:setKeys(0)
			local marker = io.open(marker_path, "w")
			if marker then
				marker:write("complete\n")
				marker:close()
			end
		end
	end
end)
