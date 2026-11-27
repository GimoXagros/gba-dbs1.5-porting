-- Replay a game-earned, post-hit Zeed checkpoint. No writes to guest memory.
local out = assert(userdata.get("output"))
local fighter = assert(tonumber(userdata.get("fighter")))
local capture_only = userdata.get("style")=="podium"
local function file(name, contents, mode)
    local stream = assert(io.open(out .. "/" .. name, mode or "wb"))
    stream:write(contents)
    stream:close()
end
local function log(line)
    file("play.txt", emu.framecount() .. " " .. line .. "\n", "ab")
end
local function b(a) return memory.read_u8(a, "System Bus") end
local function w(a) return memory.read_u16_le(a, "System Bus") end
local function d(a) return memory.read_u32_le(a, "System Bus") end
local function screenshot(name) client.screenshot(out .. "/" .. name .. ".png") end
local function run()
    assert(emu.getsystemid()=="GBA" and emu.framecount()<4)
    file("loaded-rom.bin", memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    client.speedmode(3200)
    assert(savestate.load(out .. "/entry.State", true))
    local p, q = d(0x0300489C), d(0x030048A0)
    assert(w(0x03002310)==7 and b(0x0300231E)==11)
    assert(b(p+0x11)==fighter and b(q+0x11)==15)
    local hp = w(q+0x64)
    assert(hp==0 or hp>=0x8000)
    log(string.format("restore player %d, boss HP %04X",fighter,hp))
    local seen, cursor, rejected, result, final, title = {}, 0, 0, false, false, false
    for _, addr in ipairs({0x086FFAC4,0x086FFACC,0x086FFB64,0x086FFB94,0x085CD740,0x080BF1D0}) do
        local pc = addr
        event.on_bus_exec(function()
            cursor=pc
            if not seen[pc] then
                log(string.format("entered %08X player %d resources %08X %08X",
                     pc,b(p+0x11),d(p+0xF4),d(p+0xF0)))
                seen[pc]=true
            end
            if pc==0x080BF1D0 then final=true end
        end,pc,"ending " .. pc)
    end
    event.on_bus_exec(function()
        if cursor==0x086FFAC4 then rejected=rejected+1 end
        cursor=0
    end,0x086FFD3C,"guard rejection")
    local last, podium, winner, resource, form
    event.on_bus_exec(function()
        local r=emu.getregisters()
        winner=r.R0
        assert(winner==fighter and b(r.R5+0xA)==fighter)
        form=b(r.R5+0xB)
        log("native podium winner "..winner.." palette "..form)
    end,0x080BB320,"podium winner ID")
    event.on_bus_exec(function()
        local r=emu.getregisters()
        assert(winner==fighter and r.R5==0x084A80F8+fighter*32)
        assert(r.R1==r.R5+(form==0 and 0 or 4))
        resource=d(r.R5)
        log(string.format("podium row %08X art %08X",r.R5,resource))
    end,0x080BB358,"podium resource row")
    for elapsed=0,7000 do
        local mode=w(0x03002310)
        if mode~=last then
            last=mode
            log("mode " .. mode .. " elapsed " .. elapsed)
            if mode==12 then podium=elapsed end
            if mode==8 then result=true; screenshot("result") end
            if mode==3 and final then title=true; screenshot("title"); break end
            if final and mode==20 then screenshot("ending") end
        end
        if podium and elapsed==podium+400 and mode==12 then
            assert(winner==fighter and resource)
            screenshot("podium")
            if capture_only then return "PASS" end
        end
        if elapsed==240 or elapsed==1440 or elapsed==2999 then screenshot("frame-"..elapsed) end
        if elapsed==3000 and not result then
            log("same battlefield after 3000 frames, ID check rejections " .. rejected)
            return "STALLED"
        end
        joypad.set({A=mode~=7 and elapsed%32<3})
        emu.frameadvance()
    end
    assert(seen[0x086FFB94] and seen[0x085CD740] and result and final and title)
    return "PASS"
end
local ok, outcome=pcall(run)
if not ok then log(tostring(outcome)) end
file("done.txt", tostring(outcome))
client.exit()
