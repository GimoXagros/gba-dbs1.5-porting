-- Dump WSC RAM across the Guilmon baseline battle transition.

local output_dir = "W:/evidence/bizhawk-wsc-guilmon-battle-ram-run1"
local log_path = output_dir .. "/dump.log"

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

local function dump(label)
	local handle = assert(io.open(output_dir .. "/" .. label .. ".ram", "wb"))
	handle:write(mainmemory.read_bytes_as_binary_string(0, 0x10000))
	handle:close()
	log(string.format("dump=%s frame=%d", label, emu.framecount()))
end

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
advance(24)
dump("000-selected")
tap("P1 A", 4, 4)

local previous = 0
for _, target in ipairs({ 60, 160, 400 }) do
	advance(target - previous)
	dump(string.format("%03d-after-confirm", target))
	previous = target
end
log("complete frame=" .. emu.framecount())
client.exit()
