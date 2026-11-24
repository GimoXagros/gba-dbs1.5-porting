-- Capture the four language settings by following the same menu branches in each run.
local out = assert(userdata.get("output"))
local language = assert(userdata.get("language"))
local function write(name, data)
    local f = assert(io.open(out .. "/" .. name, "wb"))
    f:write(data)
    f:close()
end
local function log(s)
    local f = assert(io.open(out .. "/trace.txt", "a"))
    f:write(string.format("%d %s\n", emu.framecount(), s))
    f:close()
end
local function iw(off) return memory.read_u16_le(off, "IWRAM") end
local function byte(off) return memory.read_u8(off, "EWRAM") end
local function word(off) return memory.read_u32_le(off, "EWRAM") end
local function task(prio)
    for i=0,51 do
        local h=0x10000+i*0x118
        if byte(h+16)&2~=0 and word(h+4)==prio then return h end
    end
end
local function frames(n,key)
    for i=1,n do
        local keys={}
        for _,b in ipairs({"A","B","Start","Select","Up","Down","Left","Right","L","R","Power"}) do keys[b]=(b==key) end
        joypad.set(keys)
        emu.frameadvance()
    end
end
local function tap(key) frames(2,key); frames(15) end
local function waitfor(label,fn,limit)
    for i=1,limit or 420 do if fn() then return end;frames(1) end
    error("timeout: "..label.." mode="..iw(0x2310))
end
local function enabled()
    local n=0
    for j=0,127 do if memory.read_u16_le(j*8,"OAM")&0x300~=0x200 then n=n+1 end end
    return n
end
local function menu(tree)
    local t=task(0x1000)
    if iw(0x2310)==3 and t and word(t)==0x08DFE048 and byte(t+28)==tree then return t end
end
local function prompt()
    local t=task(0x1000)
    return iw(0x2310)==3 and t and word(t)==0x08090C7C
end
local function shot(name)
    log("capture "..name.." mode="..iw(0x2310).." language="..(iw(0x112E)>>8))
    client.screenshot(out.."/"..name..".png")
end
local function selectrow(tree,n)
    waitfor("menu "..tree,function() return menu(tree) end)
    for i=0,8 do
        local t=menu(tree)
        if t and byte(t+29)==n then tap("A");return end
        tap("Down")
    end
    error("no row "..n)
end
local function mode(n) waitfor("mode "..n,function()return iw(0x2310)==n end) end
local rootstate=out.."/root.State"
local function root()
    assert(savestate.load(rootstate,true))
    assert(menu(0))
    frames(2)
end
local function capture_portraits()
    local current,changed,seen,count=0,0,{},0
    event.on_bus_exec(function()
        if iw(0x2310)==4 then
            current=emu.getregisters().R1
            assert(current>=0 and current<=14)
            changed=emu.framecount()
        end
    end,0x084a5c70,"selection-portrait")
    selectrow(0,0);mode(4);frames(150)
    assert(iw(0x2328)&0x3030==0x3000 and iw(0x1132)&0x30==0x30)
    for step=1,200 do
        if not seen[current] and emu.framecount()-changed>=8 then
            local name=string.format("fighter-%02d",current)
            shot(name)
            write(name.."-tiles.bin",memory.read_bytes_as_binary_string(0x5780,6144,"VRAM"))
            write(name.."-palette.bin",memory.read_bytes_as_binary_string(32,32,"PALRAM"))
            seen[current]=true
            count=count+1
            if count==15 then return end
        end
        frames(2,"Down");frames(24)
    end
    error("only "..count.." physical portraits were selected")
end
local ok,err=pcall(function()
    client.speedmode(800)
    write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    waitfor("boot prompt",prompt,6500); frames(65); tap("Start")
    selectrow(0,2); mode(14)
    waitfor("options init",function()return task(0x1500)end); frames(95)
    for i=1,8 do if iw(0x473E)==4 then break end;tap("Down") end
    assert(iw(0x473E)==4)
    for i=1,5 do
        local current=memory.read_u16_le(task(0x1500)+24,"EWRAM")
        if current==language then break end
        tap(current<language and "Right" or "Left")
    end
    assert(memory.read_u16_le(task(0x1500)+24,"EWRAM")==language)
    tap("A")
    waitfor("committed prompt",prompt)
    assert(iw(0x112E)>>8==0xA0+language)
    frames(45)
    waitfor("visible Start",function()
        for j=0,127 do
            local a=memory.read_u16_le(j*8,"OAM")
            if a&0x300~=0x200 and a&255>=98 and a&255<=119 then return true end
        end
    end)
    for _,region in ipairs({{"oam","OAM",0x400},{"palette","PALRAM",0x400},{"vram","VRAM",0x18000}}) do
        write("title-"..region[1]..".bin",memory.read_bytes_as_binary_string(0,region[3],region[2]))
    end
    shot("title");tap("Start")
    waitfor("five menu rows",function()return menu(0) and enabled()==110 end)
    frames(2);shot("main");assert(savestate.save(rootstate,true))
    write("root-oam.bin",memory.read_bytes_as_binary_string(0,0x400,"OAM"))
    if userdata.get("portraits") then capture_portraits();return end
    selectrow(0,1)
    waitfor("versus paint",function()return menu(1) and enabled()>=44 end);frames(1);shot("versus")
    root();selectrow(0,4)
    waitfor("collection paint",function()return menu(2) and enabled()>=44 end);frames(1)
    assert(iw(0x2A86)==8 and iw(0x2AD6)==9,"both Collection rows earned/available")
    shot("collection")
    selectrow(2,0);mode(22);frames(100);shot("tag")
    root();selectrow(0,4);selectrow(2,1);mode(4);frames(150);shot("shoot-select")
    root();selectrow(0,0);mode(4);frames(150);shot("solo-select")
    root();selectrow(0,3)
    waitfor("D-ARK destination",function()return iw(0x2310)~=3 end)
    frames(145);shot("dark")
    root();selectrow(0,2);mode(14);frames(140);shot("options")
    for i=1,6 do if iw(0x473E)==2 then break end;tap("Down") end
    assert(iw(0x473E)==2);tap("A");frames(40);shot("sound")
    root();selectrow(0,2);mode(14);frames(110)
    for i=1,6 do if iw(0x473E)==3 then break end;tap("Down") end
    assert(iw(0x473E)==3);tap("A");frames(40);shot("erase")
end)
if not ok then log(tostring(err));shot("failure") end
write("done.txt",ok and "PASS" or tostring(err))
client.exit()
