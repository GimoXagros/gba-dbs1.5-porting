-- Record WSC memory domains and CPU registers at character selection.

local output_dir = "W:/evidence/bizhawk-wsc-memory-probe-run2"
local log_path = output_dir .. "/probe.log"

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
	advance(settle_frames or 8)
end

client.speedmode(800)
advance(3900)
tap("P1 Start", 4, 10)
advance(70)
tap("P1 A", 4, 10)
advance(125)

log("system=" .. emu.getsystemid())
log(string.format("current_domain=%s size=0x%X", memory.getcurrentmemorydomain(), memory.getcurrentmemorydomainsize()))
log(string.format("main_domain=%s size=0x%X", mainmemory.getname(), mainmemory.getcurrentmemorydomainsize()))
for _, domain in ipairs(memory.getmemorydomainlist()) do
	log(string.format("domain=%s size=0x%X", domain, memory.getmemorydomainsize(domain)))
end
for name, value in pairs(emu.getregisters()) do
	log(string.format("register=%s value=0x%X", name, value))
end
client.screenshot(output_dir .. "/selection.png")
log("complete frame=" .. emu.framecount())
client.exit()
