-- Prepend this observer to either shipped Train/ordinary-fight controller.
do
    local wsc = emu.getsystemid() == "WSWAN"
    assert(wsc or emu.getsystemid() == "GBA")
    local globals = wsc and "SRAM" or "System Bus"
    local actors = wsc and "RAM" or "System Bus"
    local out = assert(userdata.get("out"))
    local function word(a, domain) return memory.read_u16_le(a, domain or globals) end
    local function signed(a) return memory.read_s16_le(a, actors) end
    local stats = {}
    local checkpoints = {[-1]={0x1b00,0x16c0,0x1100},[1]={0x600,0xb00,0xf00}}
    local source_y = {[-1]={2560,3009,2307},[1]={2139,2502,2487}}
    local landmark = {[-1]={},[1]={}}
    local finished = false
    local dying,converted = {},{}
    local function register(address, label, callback)
        if wsc then
            event.on_bus_write(function()
                local r=emu.getregisters()
                if (r.PS*16+r.PC)%0x100000 == address+1 then callback(r.IX) end
            end,address,label,"System Bus")
        else
            event.on_bus_exec(function() callback(emu.getregister("R4")) end,address,label)
        end
    end
    register(wsc and 0x650a3 or 0x0836876c,"neutral defeat",function(p)
        local handle = wsc and word(0x6e8) or memory.read_u32_le(0x03004cd0,globals)
        if handle==p then dying[p]=true end
    end)
    register(wsc and 0x45407 or 0x0835b2d4,"neutral converted to item",function(p)
        local address=wsc and p+0xc000 or p
        if dying[p] and word(address+4,actors)==0x9325 then
            converted[#converted+1]=emu.framecount()
            dying[p]=nil
        end
    end)
    local function sample()
        local mode = word(wsc and 0x4e or 0x03002310)
        local stage = memory.read_u8(wsc and 0x5c or 0x0300231e, globals)
        if stage ~= 8 or finished then return end
        if mode == 8 then
            local file=assert(io.open(out.."/roamer.txt","w"))
            for _,dir in ipairs({-1,1}) do
                local s = assert(stats[dir], "missing Train crossing direction")
                file:write(string.format("direction %d x=%d..%d y=%d..%d frames=%d\n",
                           dir,s.minx,s.maxx,s.miny,s.maxy,s.count))
                for _,x in ipairs(checkpoints[dir]) do
                    file:write(string.format("at %d x=%d y=%d\n",dir,x,landmark[dir][x] or -1))
                end
            end
            file:write("same actor converted to item at "..table.concat(converted,",").."\n")
            file:close()
            for _,s in pairs(stats) do
                assert(s.maxx-s.minx>4800 and s.maxy-s.miny>512,
                       "missing original horizontal and vertical flight")
            end
            for dir,targets in pairs(checkpoints) do
                for i,x in ipairs(targets) do
                    local y=assert(landmark[dir][x],"missing Train world landmark")
                    assert(math.abs(y-source_y[dir][i])<=32,"Train flight differs from source")
                end
            end
            assert(#converted>0,"no defeated Train monster reached the item producer")
            finished = true
        end
        if mode ~= 7 then return end
        for i=22,23 do
            local flag=memory.read_u8((wsc and 0x640 or 0x03004810)+i,globals)
            if flag~=255 then
                local p
                if wsc then
                    p=word(0x60c+i*2)+0xc010
                else
                    p=memory.read_u32_le(0x030047a8+i*4,globals)+0x18
                end
                local kind=word(p+4,actors)&15
                if kind==6 then
                    local x=signed(p+(wsc and 0x26 or 0x34))
                    local y=signed(p+(wsc and 0x28 or 0x36))
                    local vx=signed(p+(wsc and 0x32 or 0x42))
                    if math.abs(vx)==(wsc and 200 or 250) and x>=0 and y>=0 then
                        local dir=vx<0 and -1 or 1
                        for _,target in ipairs(checkpoints[dir]) do
                            if math.abs(x-target)<=8 and not landmark[dir][target] then landmark[dir][target]=y end
                        end
                        local s=stats[dir] or {minx=x,maxx=x,miny=y,maxy=y,count=0}
                        s.minx,s.maxx=math.min(s.minx,x),math.max(s.maxx,x)
                        s.miny,s.maxy=math.min(s.miny,y),math.max(s.maxy,y)
                        s.count=s.count+1
                        stats[dir]=s
                    end
                end
            end
        end
    end
    local advance=emu.frameadvance
    emu.frameadvance=function()
        advance()
        sample()
    end
end
