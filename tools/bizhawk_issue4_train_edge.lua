-- Prepend to the existing release controller for the original Train fight or GBA fighter 0.
-- Coordinates are signed sixteenths of a pixel. The observer never writes game memory.
do
    local out = assert(userdata.get("out"))
    local wsc = emu.getsystemid() == "WSWAN"
    assert(wsc or emu.getsystemid() == "GBA")
    local function trace(s)
        local file = assert(io.open(out.."/edge.txt", "a"))
        file:write(emu.framecount(), " ", s, "\n")
        file:close()
    end
    local function w(a) return memory.read_u16_le(a, wsc and "SRAM" or "System Bus") end
    local function d(a) return memory.read_u32_le(a, "System Bus") end
    local function pos(p, offset)
        if wsc then return mainmemory.read_s16_le(p + 0xc000 + offset) end
        return memory.read_s16_le(p + offset, "System Bus")
    end
    local function fighters()
        if wsc then
            if w(0x4e) == 7 and memory.read_u8(0x5c, "SRAM") == 8 then
                local p,q = w(0x65c),w(0x65e)
                if p>0 and p<0x4000 and q>0 and q<0x4000 then return p,q end
            end
        elseif w(0x03002310)==7 and w(0x03002656)==8 then
            local p,q = d(0x0300489c),d(0x030048a0)
            if p>=0x02010018 and p<=0x02013900 and q>=0x02010018 and q<=0x02013900
                and d(p+0x18)==q and w(0x03004502)==0
                and memory.read_u8(0x03004529,"System Bus") & 7 == 0 then return p,q end
        end
    end
    local first,apex,at_edge,returned = nil,32767,false,false
    local checked_apex,finished=false,false
    local function launch(actor)
        local _,q = fighters()
        if not first and actor==q then
            first=emu.framecount()
            trace("first CPU spring")
        end
    end
    if wsc then
        event.on_bus_write(function()
            local r=emu.getregisters()
            if (r.PS*16+r.PC)%0x100000==0x42e10 then launch(r.IX) end
        end,0x42e0f,"Train spring","System Bus")
    else
        event.on_bus_exec(function() launch(emu.getregister("R4")) end,0x08354c98,"Train spring")
    end
    local set=joypad.set
    joypad.set=function(keys,...)
        local p,q=fighters()
        if p and (wsc or next(keys)) then
            if wsc then
                for button in pairs(keys) do keys[button]=false end
                keys["P1 X2"]=true
            else
                keys={Right=true}
            end
            local offset=wsc and 0x26 or 0x34
            local x,y=pos(q,offset),pos(q,offset+2)
            if first then
                local age=emu.framecount()-first
                if age>=0 and age<96 then apex=math.min(apex,y) end
                if age==96 then
                    checked_apex=true
                    trace("first CPU spring minimum y "..apex)
                    assert(math.abs(apex-1430)<=32,"Train spring trajectory differs from WSC")
                end
            end
            if not at_edge and x==7071 then at_edge=true;trace("CPU reached right edge") end
            if at_edge and not returned and x<6750 then
                returned=true;trace("CPU left right edge")
            end
        end
        return set(keys,...)
    end
    local advance=emu.frameadvance
    emu.frameadvance=function()
        advance()
        local mode=w(wsc and 0x4e or 0x03002310)
        if mode==8 and not finished then
            assert(checked_apex and at_edge and returned,"missing Train spring or CPU edge recovery")
            finished=true
            trace("Train result")
        end
    end
end
