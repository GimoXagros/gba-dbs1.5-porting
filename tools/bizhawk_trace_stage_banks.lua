-- Trace Ver. 1.5 stage-bank reads during a clean Patamon battle route.
-- No external or supplied SaveRAM is loaded.

local output_dir = "../QAStageReadTrace1"
local log_path = output_dir .. "/trace.log"
local touched = {}
local read_count = 0

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

event.onmemoryread(function(address, value, flags)
	if address >= 0x4B0000 and address < 0x4E0000 then
		local block = address - (address % 0x20)
		if not touched[block] then
			local r = emu.getregisters()
			touched[block] = {
				frame = emu.framecount(),
				pc = r.PS * 16 + r.PC,
			}
		end
		read_count = read_count + 1
	end
end, nil, "stage-bank-any-read", "ROM")

tap("P1 A", 4, 4)
advance(600)
client.screenshot(output_dir .. "/battle.png")

local blocks = {}
for block, _ in pairs(touched) do table.insert(blocks, block) end
table.sort(blocks)
local index = 1
while index <= #blocks do
	local first = blocks[index]
	local last = first
	while index + 1 <= #blocks and blocks[index + 1] == last + 0x20 do
		index = index + 1
		last = blocks[index]
	end
	local hit = touched[first]
	log(string.format("range=0x%06X..0x%06X blocks=%d first_frame=%d first_pc=0x%05X",
		first, last + 0x1F, ((last - first) // 0x20) + 1, hit.frame, hit.pc))
	index = index + 1
end
log(string.format("complete unique_blocks=%d reads=%d frame=%d", #blocks, read_count, emu.framecount()))
client.exit()
