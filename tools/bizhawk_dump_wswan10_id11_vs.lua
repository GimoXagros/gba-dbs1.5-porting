-- Capture the original WSC 1.0 roster's last character at the VS presentation.

local output_dir = "W:/evidence/bizhawk-wsc10-id11-vs-run1"
local function advance(count) for _ = 1, count do emu.frameadvance() end end
local function tap(button, held_frames, settle_frames)
	joypad.set({ [button] = true }); advance(held_frames or 2)
	joypad.set({}); advance(settle_frames or 7)
end
local function dump(label)
	local handle = assert(io.open(output_dir .. "/" .. label .. ".ram", "wb"))
	handle:write(mainmemory.read_bytes_as_binary_string(0, 0x10000)); handle:close()
end

client.speedmode(800)
advance(3900); tap("P1 Start", 4, 10); advance(70); tap("P1 A", 4, 10); advance(125)
for _ = 1, 11 do tap("P1 X3", 2, 5) end
advance(24); client.screenshot(output_dir .. "/00-selected.png")
tap("P1 A", 4, 4); advance(160)
dump("160-after-confirm"); client.screenshot(output_dir .. "/01-vs-160.png")
client.exit()
