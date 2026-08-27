-- Baseline WonderSwan Color boot probe. No save file is loaded.

local output_dir = "W:/evidence/bizhawk-wsc-boot-run3"
local log_path = output_dir .. "/probe.log"

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

log("system=" .. emu.getsystemid())
local buttons = joypad.get()
for name, value in pairs(buttons) do
	log(string.format("button=%s value=%s", name, tostring(value)))
end

for frame = 1, 1200 do
	if frame == 300 or frame == 600 or frame == 900 or frame == 1200 then
		client.screenshot(string.format("%s/frame-%04d.png", output_dir, frame))
		log(string.format("capture=%d", frame))
	end
	emu.frameadvance()
end

log("complete")
client.exit()
