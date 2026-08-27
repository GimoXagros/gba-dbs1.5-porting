-- Trace resource-construction calls for Tailmon and its opponent.
-- Uses only a clean selector state.

local output_dir = "evidence/mgba-id14-resource-calls-run3-all-references"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/calls.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false
local hits = 0

local function append_log(line)
	local h = io.open(log_path, "a")
	if h then h:write(line .. "\n"); h:close() end
end

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then return 1 << key end
	return 0
end

local function trace(label)
	return function(info)
		if hits >= 40 then return end
		hits = hits + 1
		local sp = emu:readRegister("sp")
		local values = {}
		for index = 0, 15 do values[#values + 1] = string.format("%08X", emu:read32(sp + index * 4)) end
		append_log(string.format("%s hit=%d frame=%d r0=%08X r1=%08X r2=%08X r3=%08X sp=%08X stack=%s",
			label, hits, emu:currentFrame(), emu:readRegister("r0"), emu:readRegister("r1"),
			emu:readRegister("r2"), emu:readRegister("r3"), sp, table.concat(values, ",")))
	end
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
		emu:setBreakpoint(trace("central"), 0x08353304)
		emu:setBreakpoint(trace("construct"), 0x080127E4)
		emu:setBreakpoint(trace("palette"), 0x080132EC)
		emu:setBreakpoint(trace("behavior"), 0x08358254)
		append_log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		return
	end
	local frame = emu:currentFrame()
	local mask = 0
	mask = mask | pulse(frame, anchor + 30, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 210, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 390, C.GBA_KEY.A)
	if mask ~= 0 then emu:addKeys(mask) end
	if frame >= anchor + 800 and not finished then
		finished = true
		append_log(string.format("complete hits=%d", hits))
		local h = io.open(marker_path, "w")
		if h then h:write("complete\n"); h:close() end
	end
end)
