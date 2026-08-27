-- Map WSC Ver. 1.5 stage IDs to late-ROM resource banks from one clean boot.
-- No external SaveRAM is loaded.  A temporary in-memory/file savestate only
-- avoids replaying the title and character-select sequence eleven times.

local output_dir = "W:/evidence/wsc-stage-id-resource-map-run5"
local log_path = output_dir .. "/trace.log"
local state_path = output_dir .. "/selected.State"
local current_stage = -1
local touched = {}
local reads = {}
local replacing_stage_write = false

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function advance(count)
	for _ = 1, count do emu.frameadvance() end
end

local function tap(button, held_frames, settle_frames)
	joypad.set({ [button] = true })
	advance(held_frames or 2)
	joypad.set({})
	advance(settle_frames or 7)
end

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
for _ = 1, 11 do tap("P1 X3", 2, 5) end
advance(24)
log(string.format("selected cursor=%d id=%d frame=%d",
	mainmemory.read_u16_le(0x3116), mainmemory.read_u16_le(0x30EA + 11 * 2), emu.framecount()))
savestate.save(state_path, true)

event.onmemoryread(function(address, value, flags)
	if current_stage >= 0 and address >= 0x400000 and address < 0x4E0000 then
		local bank = address // 0x10000
		reads[current_stage][bank] = (reads[current_stage][bank] or 0) + 1
		local block = address - (address % 0x20)
		if not touched[current_stage][block] then
			local r = emu.getregisters()
			touched[current_stage][block] = {
				frame = emu.framecount(),
				pc = r.PS * 16 + r.PC,
			}
		end
	end
end, nil, "stage-id-resource-read", "ROM")

event.onmemorywrite(function(address, value, flags)
	if current_stage >= 0 and not replacing_stage_write and value ~= current_stage then
		replacing_stage_write = true
		mainmemory.write_u8(0x5C, current_stage)
		replacing_stage_write = false
	end
end, 0x5C, "stage-id-write-override", "RAM")

local diagnostic_stages = { 1, 8, 9, 10 }
for _, stage in ipairs(diagnostic_stages) do
	savestate.load(state_path, true)
	current_stage = stage
	touched[stage] = {}
	reads[stage] = {}
	joypad.set({ ["P1 A"] = true })
	for frame = 1, 4 do
		memory.write_u8(0xF7E2, stage, "System Bus")
		mainmemory.write_u8(0x5C, stage)
		emu.frameadvance()
	end
	joypad.set({})
	for frame = 1, 420 do
		memory.write_u8(0xF7E2, stage, "System Bus")
		mainmemory.write_u8(0x5C, stage)
		emu.frameadvance()
	end
	client.screenshot(string.format("%s/stage-%02d.png", output_dir, stage))
	local bank_rows = {}
	for bank, count in pairs(reads[stage]) do
		local unique = 0
		for block, _ in pairs(touched[stage]) do
			if block // 0x10000 == bank then unique = unique + 1 end
		end
		table.insert(bank_rows, { bank = bank, reads = count, unique = unique })
	end
	table.sort(bank_rows, function(a, b)
		if a.unique ~= b.unique then return a.unique > b.unique end
		return a.bank < b.bank
	end)
	local rendered = {}
	for _, row in ipairs(bank_rows) do
		table.insert(rendered, string.format("%02X:%d/%d", row.bank, row.unique, row.reads))
	end
	log(string.format("stage=%d final_ram=%d frame=%d banks=%s",
		stage, mainmemory.read_u8(0x5C), emu.framecount(), table.concat(rendered, ",")))
end

current_stage = -1
log("complete")
client.exit()
