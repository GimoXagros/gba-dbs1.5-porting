-- Rapidly enumerate WSC character-select entries before the core's long-run instability.

local output_dir = "W:/evidence/bizhawk-wsc-roster-scan-run1"
local log_path = output_dir .. "/scan.log"

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then handle:write(line .. "\n"); handle:close() end
end

local function advance(count)
	for _ = 1, count do emu.frameadvance() end
end

local function tap(button, held_frames, settle_frames)
	joypad.set({ [button] = true })
	advance(held_frames or 3)
	joypad.set({})
	advance(settle_frames or 8)
	log("tap=" .. button .. " frame=" .. emu.framecount())
end

client.speedmode(800)
log("system=" .. emu.getsystemid())
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)
client.screenshot(output_dir .. "/00-default.png")

local directions = {
	"P1 X3", "P1 X3", "P1 X3", "P1 X3", "P1 X3", "P1 X3",
	"P1 X3", "P1 X3", "P1 X3", "P1 X3", "P1 X3", "P1 X3"
}
for index, button in ipairs(directions) do
	tap(button, 2, 7)
	client.screenshot(string.format("%s/%02d-down.png", output_dir, index))
end

log("complete frame=" .. emu.framecount())
client.exit()
