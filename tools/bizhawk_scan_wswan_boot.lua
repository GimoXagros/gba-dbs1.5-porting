-- Capture the no-input WSC boot sequence at high speed. No save is loaded.

local output_dir = "W:/evidence/bizhawk-wsc-title-scan-run1"
local log_path = output_dir .. "/scan.log"

local function log(line)
	local handle = io.open(log_path, "a")
	if handle then
		handle:write(line .. "\n")
		handle:close()
	end
end

client.speedmode(800)
log("system=" .. emu.getsystemid())
for frame = 1, 4200 do
	if frame % 300 == 0 then
		client.screenshot(string.format("%s/frame-%04d.png", output_dir, frame))
		log(string.format("capture=%d", frame))
	end
	emu.frameadvance()
end
log("complete")
client.exit()
