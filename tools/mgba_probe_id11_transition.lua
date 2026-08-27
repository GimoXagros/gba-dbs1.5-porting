-- Control transition probe using built-in runtime ID 11 and a clean state.

local output_dir = "evidence/mgba-id11-transition-control-run2-dma"
local state_path = "evidence/mgba-character-select-run4/select-00.ss1"
local marker_path = output_dir .. "/done.txt"
local log_path = output_dir .. "/probe.log"
local all_keys = (1 << 10) - 1
local initialized = false
local anchor = 0
local finished = false
local loader_hits = 0
local dma_hits = 0

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function pulse(frame, at, key)
	return frame >= at and frame < at + 4 and (1 << key) or 0
end

local function loader_break(info)
	loader_hits = loader_hits + 1
	log(string.format("loader hit=%d frame=%d", loader_hits, emu:currentFrame()))
end

local function dma_break(info)
	if emu:currentFrame() < anchor + 200 or dma_hits >= 240 then return end
	dma_hits = dma_hits + 1
	log(string.format("dma hit=%d frame=%d pc=%08X src=%08X dst=%08X words=%08X",
		dma_hits, emu:currentFrame(), emu:readRegister("pc"),
		emu:readRegister("r4"), emu:readRegister("r5"), emu:readRegister("r2")))
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
		emu:write16(0x0300473C, 0)
		emu:write16(0x0300473E, 0)
		emu:setBreakpoint(loader_break, 0x08353304)
		emu:setBreakpoint(dma_break, 0x08000B84)
		emu:setBreakpoint(dma_break, 0x08000BC8)
		log(string.format("state_loaded=%s anchor=%d", tostring(loaded), anchor))
		return
	end
	local frame = emu:currentFrame()
	local keys = pulse(frame, anchor + 30, C.GBA_KEY.DOWN)
	keys = keys | pulse(frame, anchor + 210, C.GBA_KEY.A)
	if keys ~= 0 then emu:addKeys(keys) end
	local delta = frame - anchor
	if delta == 170 then
		emu:screenshot(output_dir .. "/id11-selected.png")
	elseif delta == 300 or delta == 450 or delta == 600 or delta == 800 then
		emu:screenshot(output_dir .. string.format("/after-confirm-%04d.png", delta))
	elseif delta >= 900 and not finished then
		finished = true
		log(string.format("complete loader_hits=%d dma_hits=%d", loader_hits, dma_hits))
		local marker = io.open(marker_path, "w")
		if marker then marker:write("complete\n"); marker:close() end
	end
end)
