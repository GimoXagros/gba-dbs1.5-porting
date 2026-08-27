-- Capture the WSC title-to-menu route without loading user SaveRAM.

local output_dir = "W:/evidence/bizhawk-wsc-menu-route-run1"
local log_path = output_dir .. "/route.log"

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

local function advance(count)
	for _ = 1, count do
		emu.frameadvance()
	end
end

local function tap(button, held_frames)
	joypad.set({ [button] = true })
	advance(held_frames or 3)
	joypad.set({})
	advance(12)
	log("tap=" .. button .. " frame=" .. emu.framecount())
end

client.speedmode(800)
log("system=" .. emu.getsystemid())

advance(3900)
client.screenshot(output_dir .. "/00-title.png")
tap("P1 Start", 4)

for index = 1, 12 do
	advance(60)
	client.screenshot(string.format("%s/%02d-after-start-%04d.png", output_dir, index, index * 60))
end

log("complete frame=" .. emu.framecount())
client.exit()
