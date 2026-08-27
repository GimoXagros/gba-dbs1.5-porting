-- Capture a battle using one evolution-as-base internal smoke ROM.
-- Uses only the clean selector state.

local output_dir = os.getenv("DIGIMON_PROBE_OUTPUT") or "evidence/mgba-evolution-smoke-default"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local down_count = tonumber(os.getenv("DIGIMON_DOWN_COUNT") or "2")
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false

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
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, 13)
		emu:write16(0x03004714, 14)
		emu:write16(0x03004740, 2)
		emu:write16(0x0300473C, 0)
		emu:write16(0x0300473E, 0)
		return
	end
	local frame = emu:currentFrame()
	local mask = 0
	if down_count >= 1 then mask = mask | pulse(frame, anchor + 30, C.GBA_KEY.DOWN) end
	if down_count >= 2 then mask = mask | pulse(frame, anchor + 210, C.GBA_KEY.DOWN) end
	mask = mask | pulse(frame, anchor + 390, C.GBA_KEY.A)
	if frame >= anchor + 800 and frame < anchor + 804 then
		mask = mask | (1 << C.GBA_KEY.RIGHT)
	end
	if frame >= anchor + 880 and frame < anchor + 884 then
		mask = mask | (1 << C.GBA_KEY.A)
	end
	if mask ~= 0 then emu:addKeys(mask) end
	local delta = frame - anchor
	if delta == 750 or delta == 900 or delta == 1050 then
		emu:screenshot(output_dir .. string.format("/frame-%04d.png", delta))
	elseif delta >= 1070 and not finished then
		finished = true
		local h = io.open(marker_path, "w")
		if h then h:write("complete\n"); h:close() end
	end
end)
