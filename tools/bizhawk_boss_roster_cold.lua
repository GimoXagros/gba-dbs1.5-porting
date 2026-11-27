-- Check the clear mask loaded by the normal cartridge boot, in a new process.
local out = assert(userdata.get("out"))
local expected = assert(tonumber(userdata.get("mask")))
local function write(name, value)
    local f = assert(io.open(out .. "/" .. name, "wb"))
    f:write(value)
    f:close()
end
local function halfword(offset)
    return memory.read_u16_le(offset, "IWRAM")
end
local ok, message = pcall(function()
    assert(emu.framecount() < 4 and emu.getsystemid() == "GBA")
    local checks = 0
    event.on_bus_exec(function()
        local r = emu.getregisters()
        if r.R10 == r.R9 then checks = checks + 1 end
    end, 0x0801FCF0, "native checksum accepted")
    for frame = 0, 7000 do
        if checks > 0 and halfword(0x2310) == 3 then
            local record, live = halfword(0x1130), halfword(0x232C)
            write("observed.txt", string.format("%04X %04X %d %d", record, live, checks, emu.framecount()))
            assert(record == expected and live == expected, "record/config clear mask differs")
            return
        end
        joypad.set({})
        emu.frameadvance()
    end
    error("cold cartridge did not validate save and reach title")
end)
write("done", ok and "PASS" or tostring(message))
client.exit()
