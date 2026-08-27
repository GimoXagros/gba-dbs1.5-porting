-- Dump the 64 KiB WSC work RAM for each default roster cursor position.

local output_dir = "W:/evidence/bizhawk-wsc-roster-ram-run1"
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

local function dump(index)
	local path = string.format("%s/entry-%02d.ram", output_dir, index)
	local handle = assert(io.open(path, "wb"))
	handle:write(mainmemory.read_bytes_as_binary_string(0, 0x10000))
	handle:close()
	log(string.format("dump=%d frame=%d", index, emu.framecount()))
end

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
dump(0)
for index = 1, 12 do
	tap("P1 X3", 2, 7)
	dump(index)
end
log("complete frame=" .. emu.framecount())
client.exit()
