-- Capture stable WSC roster screens in two short runs.
-- Set segment to 1 for entries 0..5, 2 for 6..12, or 3 for 13..16.

local segment = 3
local output_dir = "W:/evidence/bizhawk-wsc-roster-names-run3"
local log_path = output_dir .. "/capture.log"

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

local first_index = segment == 1 and 0 or (segment == 2 and 6 or 13)
local last_index = segment == 1 and 5 or (segment == 2 and 12 or 16)
for _ = 1, first_index do tap("P1 X3", 2, 5) end

for index = first_index, last_index do
	advance(24)
	client.screenshot(string.format("%s/entry-%02d.png", output_dir, index))
	log("capture=" .. index .. " frame=" .. emu.framecount())
	if index < last_index then tap("P1 X3", 2, 5) end
end

log("complete frame=" .. emu.framecount())
client.exit()
