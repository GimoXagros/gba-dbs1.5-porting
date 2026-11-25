-- The pinned WSWAN core reports native execute through managed on_bus_write.
local out=assert(userdata.get("out"))
local function file(n,s,mode)local f=assert(io.open(out.."/"..n,mode or "wb"));f:write(s);f:close()end
local function log(s)file("events.txt",emu.framecount().." "..s.."\n","ab")end
local function word(o)return memory.read_u16_le(o,"SRAM")end
local function stage()return memory.read_u8(0x5c,"SRAM")end
local function run()
    assert(emu.getsystemid()=="WSWAN" and emu.framecount()<4)
    file("loaded.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))
    client.speedmode(800)
    local count={}
    for name,raw in pairs({init=0x76b477,update=0x76a8cc,shake=0x76b3d2}) do
        local label,addr=name,raw-0x700000
        count[label]=0
        event.on_bus_write(function(a)
            local r=emu.getregisters()
            assert(a==addr and (r.PS*16+r.PC)%0x100000==a+1)
            count[label]=count[label]+1
            if count[label]<=2 or label=="shake" then
                log(string.format("%s pc=%04x:%04x ds=%04x stage=%d state=%04x,%04x,%04x,%04x,%04x ret=%04x",label,r.PS,r.PC,r.DS0,stage(),word(0x376),word(0x378),word(0x37a),word(0x37c),word(0x37e),memory.read_u16_le((r.SS*16+r.SP)%0x100000,"System Bus")))
            end
        end,addr,label,"System Bus")
    end
    local mode_before
    for f=0,23000 do
        local mode=word(0x4e)
        if mode~=mode_before then log("mode "..mode.." stage "..stage());mode_before=mode end
        local k={}
        for _,button in ipairs({"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"})do k[button]=false end
        if mode==3 then k["P1 Start"]=f%48==0;k["P1 A"]=f%48==24
        elseif mode==4 or mode==6 or mode==8 then k["P1 A"]=f%27<2
        elseif mode==7 then k["P1 B"]=f%45<5;k["P1 A"]=f%121<20;k["P1 X2"]=f%600<180;k["P1 X4"]=f%600>=300 and f%600<480 end
        if mode==8 and count.update>500 then
            log(string.format("result init=%d update=%d shake=%d",count.init,count.update,count.shake))
            assert(count.init>0);client.screenshot(out.."/result.png");return
        end
        joypad.set(k);emu.frameadvance()
    end
    error("train result timeout")
end
local ok,err=pcall(run);if not ok then log(tostring(err))end
file("done",ok and "PASS" or tostring(err));client.exit()
