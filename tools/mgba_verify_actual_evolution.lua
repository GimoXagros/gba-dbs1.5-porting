-- Verify the real mid-battle evolution path on the integrated Patamon build.
-- This uses a clean GBA selector state and never reads the supplied WSC SRAM.

local output_dir = "evidence/mgba-actual-evolution-id13-run4-position-sweep"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/probe.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false
local loader_hits = 0
local evolution_hits = 0

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function pulse(frame, at, duration, key)
	return frame >= at and frame < at + duration and (1 << key) or 0
end

local function loader_break(info)
	loader_hits = loader_hits + 1
	local sp = emu:readRegister("sp")
	-- The breakpoint fires before the routine's six-register prologue push.
	-- Its three stack arguments are therefore still at SP+0, SP+4, and SP+8.
	local group = emu:read32(sp)
	local character = emu:read32(sp + 4)
	local side = emu:read32(sp + 8)
	log(string.format(
		"loader hit=%d frame=%d group=%08X id=%08X side=%08X r4=%08X sp=%08X",
		loader_hits, emu:currentFrame(), group, character, side,
		emu:readRegister("r4"), sp))
	if group ~= 0 and character == 13 then evolution_hits = evolution_hits + 1 end
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if finished then return end
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, 13)
		emu:write16(0x03004740, 1)
		emu:write16(0x0300473C, 0)
		emu:write16(0x0300473E, 0)
		emu:setBreakpoint(loader_break, 0x08353304)
		log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		return
	end

	local frame = emu:currentFrame()
	local delta = frame - anchor
	local keys = pulse(frame, anchor + 30, 4, C.GBA_KEY.DOWN)
	keys = keys | pulse(frame, anchor + 210, 4, C.GBA_KEY.A)
	if delta >= 850 then
		-- Activation-only intervention: sweep Patamon through the playable
		-- coordinate space while holding the CPU actor at the corner.  The game
		-- still has to spawn Calumon, detect the collision, and invoke group 1.
		emu:write16(0x02011710 + 0xAC, 8 + ((delta * 7) % 224))
		emu:write16(0x02011710 + 0xAE, 16 + ((delta * 11) % 128))
		emu:write16(0x02011828 + 0xAC, 0)
		emu:write16(0x02011828 + 0xAE, 0)
		local phase = ((delta - 850) // 180) % 2
		keys = keys | (1 << (phase == 0 and C.GBA_KEY.RIGHT or C.GBA_KEY.LEFT))
		if ((delta - 850) % 90) < 4 then
			keys = keys | (1 << C.GBA_KEY.B)
		end
		if ((delta - 850) % 150) < 4 then
			keys = keys | (1 << C.GBA_KEY.A)
		end
	end
	if keys ~= 0 then emu:addKeys(keys) end

	if delta == 760 or (delta >= 1200 and delta <= 6600 and delta % 600 == 0) then
		emu:screenshot(output_dir .. string.format("/frame-%04d.png", delta))
	end
	if evolution_hits > 0 and delta % 30 == 0 then
		emu:screenshot(output_dir .. string.format("/evolution-%04d.png", delta))
		finished = true
	elseif delta >= 6800 then
		finished = true
	end
	if finished then
		log(string.format("complete delta=%d loader_hits=%d evolution_hits=%d",
			delta, loader_hits, evolution_hits))
		local marker = io.open(marker_path, "w")
		if marker then marker:write(string.format("evolution_hits=%d\n", evolution_hits)); marker:close() end
	end
end)
