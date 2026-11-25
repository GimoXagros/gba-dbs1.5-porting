-- Observe selection, Calumon collision, both resource swaps and the actual result transition.
local out=assert(userdata.get("out"))
local fid=assert(tonumber(userdata.get("fighter")))
local function file(n,data,mode)
    local f=assert(io.open(out.."/"..n,mode or "wb"));f:write(data);f:close()
end
local function log(s) file("events.txt",emu.framecount().." "..s.."\n","ab") end
local function shot(n) client.screenshot(out.."/"..n..".png") end
local function b(a) return memory.read_u8(a,"System Bus") end
local function w(a) return memory.read_u16_le(a,"System Bus") end
local function d(a) return memory.read_u32_le(a,"System Bus") end
local function sx(a) local v=w(a);return v>=32768 and v-65536 or v end
local function actor(a)
    local p=d(a)
    if p>=0x02010018 and p<=0x02013900 and (p-0x02010018)%0x118==0 and w(p-8)&2~=0 then return p end
end
local function title()
    for i=0,51 do
        local h=0x02010000+i*0x118
        if w(h+16)&2~=0 and d(h+4)==0x1000 then return h end
    end
end
local function run()
    client.speedmode(800);assert(emu.framecount()<4 and emu.getsystemid()=="GBA")
    file("loaded.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    local evo,back,used,result,selected,vs=false,false,false,false,false,false
    local groups,positions,contacts={}, {}, {}
    local attacks,attack_events,damage=0,{},0
    local first_x,first_y,last_mode,target,n=0,0,-1,nil,0
    local pending_sound,heard={},{}
    event.on_bus_exec(function()
        local r=emu.getregisters()
        if r.R8>=0x5f and r.R8<=0x63 then
            pending_sound={frame=emu.framecount(),state=r.R5,shell=r.R4,cmd=d(r.R5+0x20),cursor=d(r.R5+0x24)}
        end
    end,0x08012ba8,"animation cue request")
    event.on_bus_exec(function()
        local r=emu.getregisters()
        if r.R8>=0x5f and r.R8<=0x63 and not heard[r.R8] then
            local p=actor(0x0300489c)
            if p then
                local q=actor(0x030048a0)
                local context=(r.R14==0x08012bac and pending_sound.frame==emu.framecount()) and pending_sound or {}
                log(string.format("accepted sound %02X caller=%08X player=%d event=%d enemy=%d event=%d shell=%08X cmd=%08X cursor=%08X",r.R8,r.R14,b(p+17),w(p+0xba),q and b(q+17) or -1,q and w(q+0xba) or -1,context.shell or 0,context.cmd or 0,context.cursor or 0))
                heard[r.R8]=true
            end
        end
    end,0x080d15d0,"accepted retail cue")
    event.on_bus_exec(function()
        local r=emu.getregisters()
        local p=actor(0x0300489c)
        if p and r.R4==p and b(p+17)==fid then
            evo=true;log("evolution music selector "..fid)
        end
    end,0x080d14bc,"player evolution")
    event.on_bus_exec(function()
        local r=emu.getregisters()
        if evo and r.R4==actor(0x0300489c) then back=true;log("ordinary devolution") end
    end,0x0835a75c,"player returns")
    event.on_bus_exec(function()
        local s=emu.getregister("R13")
        local group,id,side=d(s),d(s+4),d(s+8)
        if id==fid and side==0 then groups[group]=true;log("player resource group "..group) end
    end,0x08353304,"native actor resource")
    event.on_bus_exec(function()
        local r=emu.getregisters()
        if r.R4==actor(0x0300489c) and r.R5==actor(0x030048a0) then damage=damage+1 end
    end,0x0836e5e4,"player damage")
    for f=1,45000 do
        local m,s=w(0x03002310),b(0x0300231e)
        local k={};local pulse=f%19<2
        if m~=last_mode then log("mode "..m.." stage "..s);last_mode=m end
        if m==3 then
            local h=title()
            if h and d(h)==0x08090c7c then k.Start=pulse
            elseif h and d(h)==0x08dfe048 then k[b(h+29)==0 and "A" or "Up"]=pulse end
        elseif m==4 then
            local cursor,mirror,maximum=w(0x0300473c),w(0x0300473e),w(0x03004740)
            if maximum==14 and cursor==mirror and cursor<=14 then
                local order={0,1,2,3,4,5,6,7,8,9,10,13,14,11,12}
                k[order[cursor+1]==fid and "A" or "Down"]=pulse
                if order[cursor+1]==fid and not selected then selected=true;log("selected "..cursor.." id "..fid);shot("selection") end
            end
        elseif m==6 then
            if result then assert(used);shot("next");log("next VS");return end
            if selected then vs=true;k.A=pulse end
        elseif m==8 then
            if not result then
                assert(used and vs,"missing active battle")
                if fid>=11 then assert(evo and back and groups[1] and attacks>0 and next(attack_events),"missing evolved action/return") end
                result=true;log("result damage "..damage.." attack-input frames "..attacks);shot("result")
            end
            k.A=pulse
        elseif m==9 then
            assert(result,"unexpected Continue")
            k.A=pulse
        elseif m==7 then
            local p,q=actor(0x0300489c),actor(0x030048a0)
            if p and q and b(p+17)==fid and d(p+0x18)==q and w(0x03004502)==0 and b(0x03004529)&7==0 then
                local x,y=sx(p+0x34),sx(p+0x36)
                if not used then used=true;first_x=x;first_y=y;log("player active "..fid.." "..x.." "..y) end
                if not positions[s] then positions[s]=true;shot("stage-"..s) end
                if evo and not back then
                    if not target then
                        target=f;shot("evolution");first_x=x;first_y=y
                        assert(savestate.save(out.."/evolution.State",true))
                    end
                    local age=f-target
                    local phase=age//100%7
                    local dx=sx(q+0x34)-x
                    k.A=(phase>=4 and age%80<23)
                    k.B=phase==3 and age%90<64 or age%26<6
                    k.Up=phase==1 or phase==4
                    k.Down=phase==2 or phase==5
                    k.Left=phase==6 and dx< -128
                    k.Right=phase==6 and dx>128
                    if k.B then attacks=attacks+1 end
                    local ev=w(p+0xba)
                    if not attack_events[ev] then attack_events[ev]=true;log("evolved event "..ev.." at "..x..","..y) end
                elseif fid<11 or back then
                    k.A=f%91<20;k.B=f%29<7;k.Left=f%410<185;k.Right=f%410>=205 and f%410<385
                else
                    local cal=actor(0x03004ce8)
                    local active=cal and w(cal+4)&15==8 and w(cal+4)&0x1000~=0
                    if active then
                        local dx,dy=sx(cal+0x34)-x,sx(cal+0x36)-y
                        k.Right=dx>64;k.Left=dx< -64;k.A=dy< -128 and f%42<21
                        if not contacts.first then contacts.first=true;log("collectible at "..x..","..y.." delta "..dx..","..dy) end
                        if f%240==0 then log("approach "..dx..","..dy) end
                    else
                        k.Left=x>0x18c0;k.Right=x<0x1740
                    end
                end
            end
        elseif m==5 then k.A=pulse end
        joypad.set(k);emu.frameadvance()
    end
    error("frame limit")
end
local ok,err=pcall(run)
if not ok then shot("last");log(tostring(err)) end
file("done",ok and "PASS" or tostring(err))
client.exit()
