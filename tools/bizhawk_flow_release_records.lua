-- Follow the attract-mode VS RECORD path with the post-match EEPROM actually written over cable.
local out=assert(userdata.get("out"))
local function file(n,s,mode)local f=assert(io.open(out.."/"..n,mode or "wb"));f:write(s);f:close()end
local function log(s)file("events.txt",emu.framecount().." "..s.."\n","ab")end
local function w(a)return memory.read_u16_le(a,"System Bus")end
local function d(a)return memory.read_u32_le(a,"System Bus")end
local order={0,1,2,3,4,5,6,7,8,9,10,13,14,11,12}
local function run()
    assert(emu.framecount()<4 and emu.getsystemid()=="GBA")
    file("loaded.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    client.speedmode(800)
    local rows,entries,exits,cancel_at={},0,0,nil
    event.on_bus_exec(function() entries=entries+1;log("entry "..entries) end,0x0833eb2c,"VS record scene")
    for slot,pc in ipairs({0x0833f36c,0x0833f4c0,0x0833f614})do
        local j=slot
        event.on_bus_exec(function()
            local task=d(0x0300133c)
            local start=w(task+0x18)
            local id=assert(order[start+j])
            local ptr=emu.getregister("R1")
            local expected=id<12 and 0x030011ae+id*4 or task+0x18+244+(id-12)*4
            assert(ptr==expected)
            if not rows[id] then rows[id]=true;log("row "..id.." "..w(ptr).." "..w(ptr+2)) end
        end,pc,"native digits "..slot)
    end
    local last=-1
    for f=1,65000 do
        local m=w(0x03002310)
        if m~=last then
            if last==19 and entries>exits then exits=exits+1;log("exit "..exits.." mode "..m) end
            last=m
        end
        if exits==2 and m==3 then
            assert(cancel_at and f-cancel_at<300,"input did not promptly return")
            for _,id in ipairs(order) do assert(rows[id]) end
            log("title after cancellation");return
        end
        local k={}
        if m==19 and entries==2 and exits==1 then
            k.A=f%28<2
            if k.A and not cancel_at then cancel_at=f;log("pressed A to leave VS RECORD") end
        end
        joypad.set(k);emu.frameadvance()
    end
    error("record attract deadline")
end
local ok,err=pcall(run);if not ok then log(tostring(err))end
file("done",ok and "PASS" or tostring(err));client.exit()
