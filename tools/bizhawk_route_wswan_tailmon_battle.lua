-- Route a clean WSC 1.5 session to Tailmon, then capture and dump the VS/battle load.

local output_dir = "W:/evidence/bizhawk-wsc-tailmon-battle-run1"
local log_path = output_dir .. "/route.log"

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
for _ = 1, 12 do tap("P1 X3", 2, 5) end
advance(24)
client.screenshot(output_dir .. "/00-tailmon-selected.png")
dump("000-selected")
log(string.format("selected cursor=%d roster_id=%d frame=%d", mainmemory.read_u16_le(0x3116), mainmemory.read_u16_le(0x30EA + 12 * 2), emu.framecount()))

tap("P1 A", 4, 4)
local previous = 0
for index, target in ipairs({ 60, 100, 140, 160, 180, 200, 240, 320, 400, 500, 600 }) do
	advance(target - previous)
	dump(string.format("%03d-after-confirm", target))
	client.screenshot(string.format("%s/%02d-after-confirm-%03d.png", output_dir, index, target))
	previous = target
end
log("complete frame=" .. emu.framecount())
client.exit()
