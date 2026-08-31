-- Capture a no-input WSC boot/intro reference without loading a save.
-- The launcher supplies an ASCII-only ignored output path and runs BizHawk on
-- a hidden/non-displaying launcher so no emulator window appears on the user's
-- monitor.

local output_dir = assert(os.getenv("CODEX_WSC_CAPTURE_DIR"),
	"CODEX_WSC_CAPTURE_DIR is required")
local log_path = output_dir .. "/capture.log"
local targets = {
	[300] = true, [600] = true, [900] = true, [1200] = true,
	[1500] = true, [1800] = true, [2100] = true, [2400] = true,
	[2700] = true, [3000] = true, [3300] = true, [3600] = true,
	[3900] = true, [4200] = true,
}

local function log(line)
	local handle = assert(io.open(log_path, "a"))
	handle:write(line .. "\n")
	handle:close()
end

local function dump_ram(frame)
	local path = string.format("%s/frame-%04d.ram", output_dir, frame)
	local handle = assert(io.open(path, "wb"))
	handle:write(mainmemory.read_bytes_as_binary_string(0, 0x10000))
	handle:close()
end

client.speedmode(800)
log("system=" .. emu.getsystemid())
for frame = 1, 4200 do
	if targets[frame] then
		client.screenshot(string.format("%s/frame-%04d.png", output_dir, frame))
		dump_ram(frame)
		log(string.format("capture=%d", frame))
	end
	emu.frameadvance()
end
log("complete")
client.exit()
