-- Route the clean WSC reference to Patamon and capture the following battle load.

local output_dir = "W:/evidence/bizhawk-wsc-patamon-battle-run2"
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

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
for _ = 1, 11 do tap("P1 X3", 2, 5) end
advance(24)
client.screenshot(output_dir .. "/00-patamon-selected.png")
log(string.format("selected cursor=%d id=%d frame=%d", mainmemory.read_u16_le(0x3116), mainmemory.read_u16_le(0x30EA + 11 * 2), emu.framecount()))
tap("P1 A", 4, 4)
for index = 1, 30 do
	advance(20)
	client.screenshot(string.format("%s/%02d-after-confirm-%03d.png", output_dir, index, index * 20))
end
log("complete frame=" .. emu.framecount())
client.exit()
