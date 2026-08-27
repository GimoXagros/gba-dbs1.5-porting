local path = "W:/evidence/bizhawk-launch-diagnostic.log"
local handle = assert(io.open(path, "a"))
handle:write("lua-start system=" .. emu.getsystemid() .. " frame=" .. emu.framecount() .. "\n")
handle:close()
emu.frameadvance()
client.exit()
