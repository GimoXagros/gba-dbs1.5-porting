-- Deterministic baseline capture route for mGBA development builds.
-- It detects the blinking PRESS START text instead of assuming a fixed intro
-- length, because the game's randomly selected opening duel changes timing.

local output_dir = "evidence/mgba-route-run8"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/route.log"
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
		local pixel = screen:getPixel(150, 109) & 0xFFFFFF
		local logo_a = screen:getPixel(120, 80) & 0xFFFFFF
		local logo_b = screen:getPixel(120, 60) & 0xFFFFFF
		if pixel == 0 and logo_a == 0x5A0000 and logo_b == 0x00298C then
			anchor = frame
			state = "route"
			emu:screenshot(output_dir .. "/title-detected.png")
			append_log(string.format("title_detected_frame=%d pixel=0x%06X", frame, pixel))
		end
	end

	if state == "route" then
		local mask = 0
		mask = mask | pulse(frame, anchor, C.GBA_KEY.START)
		mask = mask | pulse(frame, anchor + 160, C.GBA_KEY.A)
		mask = mask | pulse(frame, anchor + 320, C.GBA_KEY.A)
		mask = mask | pulse(frame, anchor + 480, C.GBA_KEY.A)
		if mask ~= 0 then
			emu:addKeys(mask)
		end

		local delta = frame - anchor
		if delta == 120 or delta == 280 or delta == 440 or delta == 600 then
			local name = string.format("after-title-%04d.png", delta)
			emu:screenshot(output_dir .. "/" .. name)
			append_log(string.format("frame=%d delta=%d screenshot=%s", frame, delta, name))
		end
		if delta >= 640 and not finished then
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
