-- Cold boot and select D-ARK twice using controller input only.
local out = assert(userdata.get("out"))
local ws = emu.getsystemid()=="WSWAN"
local lang, fighter = tonumber(userdata.get("lang")), tonumber(userdata.get("fighter"))
local domain, modeAt = ws and "SRAM" or "IWRAM", ws and 0x4e or 0x2310
local function h(a) return memory.read_u16_le(a,domain) end
local function mode() return h(modeAt) end
local function write(name, data)
    local f=assert(io.open(out.."/"..name,"wb"))
    f:write(data);f:close()
end
local trace=assert(io.open(out.."/events.txt","w"))
local function log(msg) trace:write(emu.framecount().." "..msg.."\n");trace:flush() end
local function shot(name) client.screenshot(out.."/"..name..".png");log("capture "..name) end
local last
local function frame(key)
    if ws then key=({Start="P1 Start",Down="P1 X3",Right="P1 X2",Left="P1 X4",A="P1 A",B="P1 B"})[key] end
    joypad.set(key and {[key]=true} or {});emu.frameadvance()
    local m=mode()
    if m~=last then log("mode "..m.." flags "..h(modeAt+26));last=m end
end
local function frames(n,key) for i=1,n do frame(key) end end
local function tap(key) frames(3,key);frames(31) end
local function waitmode(m,limit)
    for i=1,limit do if mode()==m then return end;frame() end
    error("wanted "..m.." got "..mode())
end
local root_visits=0
local function root()
    waitmode(3,6100);frames(175);root_visits=root_visits+1;shot("title-ref-"..root_visits);tap("Start");frames(142)
end
local function option()
    tap("Down");tap("Down");tap("A");waitmode(14,400);frames(120)
    for i=1,8 do if h(0x473e)==4 then break end;tap("Down") end
    assert(h(0x473e)==4)
    local addr
    for i=0,51 do
        local a=0x10000+i*0x118
        if memory.read_u32_le(a+4,"EWRAM")==0x1500 and memory.read_u8(a+16,"EWRAM")&2~=0 then addr=a+24;break end
    end
    assert(addr)
    for i=1,6 do
        local l=memory.read_u16_le(addr,"EWRAM")
        if l==lang then break end
        tap(l<lang and "Right" or "Left")
    end
    assert(memory.read_u16_le(addr,"EWRAM")==lang)
    tap("A");root();assert(h(0x112e)>>8==lang+0xa0)
end
local function open_scene(pass)
    local save
    if not ws then save=memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize("SRAM"),"SRAM") end
    for i=1,3 do tap("Down") end
    if not ws then
        local found=false
        for i=0,51 do
            local a=0x10000+i*0x118
            if memory.read_u8(a+16,"EWRAM")&2~=0 and memory.read_u32_le(a,"EWRAM")==0x08dfe048 then
                assert(memory.read_u8(a+28,"EWRAM")==0 and memory.read_u8(a+29,"EWRAM")==3)
                found=true
            end
        end
        assert(found)
    end
    shot("d-ark-"..pass);tap("A");waitmode(4,260);assert(h(modeAt+26)&2~=0);frames(145)
    local order={0,1,2,3,4,5,6,7,8,9,10,13,14,11,12}
    if ws then
        for i=1,fighter do tap("Down");frames(35) end
    else
        for i=1,17 do
            if order[h(0x473c)+1]==fighter then break end
            tap("Down");frames(40)
        end
        assert(order[h(0x473c)+1]==fighter)
    end
    frames(95);shot("selected-"..pass);frames(3,"A");waitmode(18,200)
    local start=emu.framecount();assert(memory.read_u8(modeAt+10,domain)==fighter)
    local stable=ws and 115 or 95
    frames(stable);assert(mode()==18);shot("wait-"..pass)
    for i=1,6 do frames(3);shot("motion-"..pass.."-"..i) end
    tap("A");frames(260);assert(mode()==18 and memory.read_u8(modeAt+10,domain)==fighter)
    if not ws then assert(h(0x112e)>>8==lang+0xa0) end
    shot("wait-after-a-"..pass);local cancel=emu.framecount();frames(3,"B");waitmode(20,80)
    log("B retirement "..(emu.framecount()-cancel).." wait "..(cancel-start))
    waitmode(3,230);frames(105);shot("return-"..pass)
    if not ws then
        local now=memory.read_bytes_as_binary_string(0,#save,"SRAM")
        assert(save==now,"EEPROM changed during disconnected D-ARK")
        log("unchanged save bytes "..#save)
    end
end
local ok,err=pcall(function()
    client.speedmode(800)
    write("loaded.bin",memory.read_bytes_as_binary_string(0,ws and 0x800000 or 0x1000000,"ROM"))
    root();if not ws then option() end
    open_scene(1);root();open_scene(2)
end)
if not ok then log(tostring(err));shot("failed") end
trace:close();write("done",ok and "PASS" or tostring(err));client.exit()
