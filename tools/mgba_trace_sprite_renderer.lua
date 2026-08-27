-- Compare the sprite-renderer setup immediately before battle initialization.
-- Change target_id/output_dir together for a clean control or candidate run.

local target_id = 14
local output_dir = "evidence/mgba-vs-object-watch-id14-run14"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/trace.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local hits = 0
local finished = false
local watch_hits = 0

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function pulse(frame, at, key)
	if frame >= at and frame < at + 4 then return 1 << key end
	return 0
end

local function renderer_break(info)
	if emu:currentFrame() < anchor + 450 or hits >= 20 then return end
	hits = hits + 1
	log(string.format(
		"hit=%d frame=%d pc=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X r6=%08X r7=%08X r8=%08X r9=%08X r10=%08X r11=%08X r12=%08X sp=%08X lr=%08X",
		hits, emu:currentFrame(), emu:readRegister("pc"),
		emu:readRegister("r0"), emu:readRegister("r1"), emu:readRegister("r2"), emu:readRegister("r3"),
		emu:readRegister("r4"), emu:readRegister("r5"), emu:readRegister("r6"), emu:readRegister("r7"),
		emu:readRegister("r8"), emu:readRegister("r9"), emu:readRegister("r10"), emu:readRegister("r11"),
		emu:readRegister("r12"), emu:readRegister("sp"), emu:readRegister("lr")))
	local object = emu:readRegister("r5")
	log(string.format(
		"object=%08X p20=%08X p24=%08X p48=%08X p4C=%08X p60=%08X",
		object, emu:read32(object + 0x20), emu:read32(object + 0x24),
		emu:read32(object + 0x48), emu:read32(object + 0x4C), emu:read32(object + 0x60)))
	log(string.format(
		"slots c78_p20=%08X c78_p48=%08X cc8_p20=%08X cc8_p48=%08X",
		emu:read32(0x03002C98), emu:read32(0x03002CC0),
		emu:read32(0x03002CE8), emu:read32(0x03002D10)))
end

local function object_watch(info)
	watch_hits = watch_hits + 1
	if watch_hits <= 80 then
		log(string.format(
			"watch hit=%d frame=%d addr=%08X old=%08X new=%08X pc=%08X lr=%08X",
			watch_hits, emu:currentFrame(), info.address, info.oldValue, info.newValue,
			emu:readRegister("pc"), emu:readRegister("lr")))
	end
end

callbacks:add("frame", function()
	emu:clearKeys(all_keys)
	if not initialized then
		initialized = true
		local loaded = emu:loadStateFile(state_path)
		anchor = emu:currentFrame()
		emu:write16(0x03004710, 0)
		emu:write16(0x03004712, target_id)
		emu:write16(0x03004740, 1)
		emu:write16(0x0300473C, 0)
		emu:write16(0x0300473E, 0)
		emu:setWatchpoint(object_watch, 0x03002CE8, C.WATCHPOINT_TYPE.WRITE_CHANGE)
		emu:setWatchpoint(object_watch, 0x03002CEC, C.WATCHPOINT_TYPE.WRITE_CHANGE)
		log(string.format("loaded=%s anchor=%d target_id=%d", tostring(loaded), anchor, target_id))
		return
	end

	local frame = emu:currentFrame()
	local mask = pulse(frame, anchor + 30, C.GBA_KEY.DOWN)
	mask = mask | pulse(frame, anchor + 210, C.GBA_KEY.A)
	if mask ~= 0 then emu:addKeys(mask) end
	local delta = frame - anchor
	if delta >= 430 and delta <= 620 and delta % 10 == 0 then
		log(string.format(
			"global delta=%d b08=%02X b09=%02X b0A=%02X b0B=%02X b0C=%02X b0D=%02X b0E=%02X b0F=%02X",
			delta, emu:read8(0x03002318), emu:read8(0x03002319),
			emu:read8(0x0300231A), emu:read8(0x0300231B),
			emu:read8(0x0300231C), emu:read8(0x0300231D),
			emu:read8(0x0300231E), emu:read8(0x0300231F)))
	end
	if delta == 300 or delta == 450 or delta == 520 or delta == 600 then
		emu:screenshot(string.format("%s/frame-%03d.png", output_dir, delta))
	end
	if delta >= 700 and not finished then
		finished = true
		log(string.format("complete hits=%d", hits))
		local marker = io.open(marker_path, "w")
		if marker then marker:write("complete\n"); marker:close() end
	end
end)
