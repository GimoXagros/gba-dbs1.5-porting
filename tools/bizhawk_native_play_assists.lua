-- Play using only controller buttons. Observe native option stores and real boss damage.
local out=assert(userdata.get("output"))
local fixed=assert(tonumber(userdata.get("fixed")))
local full=userdata.get("route")=="campaign"
local score_pc=assert(tonumber(userdata.get("score_pc")))
local boss_pc=assert(tonumber(userdata.get("boss_pc")))
local function file(name,value,mode)
    local f=assert(io.open(out.."/"..name,mode or "wb"));f:write(value);f:close()
end
local function log(s) file("play.txt",emu.framecount().." "..s.."\n","ab") end
local function shot(name) client.screenshot(out.."/"..name..".png") end
local function iw(n) return memory.read_u16_le(n,"IWRAM") end
local function ib(n) return memory.read_u8(n,"IWRAM") end
local function ip(n) return memory.read_u32_le(n,"IWRAM") end
local function ew(p,n) return memory.read_u16_le(p-0x02000000+n,"EWRAM") end
local function ed(p,n) return memory.read_u32_le(p-0x02000000+n,"EWRAM") end
local function sx(v) return v>=32768 and v-65536 or v end
local function actor(n)
    local p=ip(n)
    if p>=0x02010018 and p<=0x02013900 then return p end
end
local function task(prio)
    for i=0,51 do
        local p=0x02010000+i*0x118
        if ew(p,16)&2~=0 and ed(p,4)==prio then return p end
    end
end
local seen,hit,boss,first={},{},{},{}
local writes,samples=0,0
local function run()
    assert(emu.framecount()<4 and emu.getsystemid()=="GBA")
    file("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    client.speedmode(800)
    event.on_bus_exec(function()
        local r=emu.getregisters()
        assert(r.R4==actor(0x489c) and r.R0==fixed and ew(r.R4,0x66)~=fixed)
        writes=writes+1
    end,score_pc,"native D-Spirit assignment")
    event.on_bus_exec(function()
        local r=emu.getregisters();local stage=ib(0x231e)
        assert(full and (stage==7 or stage==11) and not boss[stage] and r.R5==actor(0x48a0) and r.R0==1)
        assert(sx(ew(r.R5,0x64))>0);boss[stage]=true;log("boss assist "..stage)
    end,boss_pc,"native boss assignment")
    event.on_bus_exec(function()
        local r=emu.getregisters();local stage=ib(0x231e)
        if boss[stage] and r.R4==actor(0x489c) and r.R5==actor(0x48a0) and ew(r.R5,0x64)==1 and sx(r.R8&65535)<=0 then
            hit[stage]=true;log("real hit "..stage)
        end
    end,0x0836e5e4,"boss damage")
    event.on_bus_exec(function()
        local p,q=actor(0x489c),actor(0x48a0)
        if iw(0x2310)==7 and iw(0x4502)==0 and ib(0x4529)&7==0 and p and q and sx(ew(p,0x64))>0 and sx(ew(q,0x64))>0 and ew(q,4)&15==1 then
            if fixed>=0 then assert(ew(p,0x66)==fixed,"D-Spirit read after native assignment") end
            samples=samples+1
        end
    end,0x0837363c,"post-collision observation")
    local ending=false
    event.on_bus_exec(function() ending=true;log("ending") end,0x080bf1d0,"ending")
    local before,configured=-1,not full
    local prior={}
    for step=0,145000 do
        local m,s=iw(0x2310),ib(0x231e)
        if m~=before then log("mode "..m.." stage "..s);before=m end
        assert(m~=9,"Continue reached at stage "..s)
        local k={}
        local pulse=step%32<3
        if not full and samples>=400 and (fixed<0 or writes>0) then
            assert(fixed>=0 or writes==0)
            shot("score");log("sampled "..samples.." native score writes "..writes);return
        end
        if m==3 and step>600 then
            if ending then
                for i=1,11 do assert(seen[i],"missing stage "..i) end
                assert(hit[7] and hit[11] and samples>1000 and writes>0)
                shot("return-title");log("campaign sampled "..samples.." native score writes "..writes);return
            end
            local h=task(0x1000);local cb=h and ed(h,0) or 0
            if cb==0x08090c7c then k.Start=pulse
            elseif cb==0x08dfe048 then
                local goal=configured and 0 or 2
                k[ew(h,28)>>8==goal and "A" or "Down"]=pulse
            end
        elseif m==14 and task(0x1500) then
            if iw(0x473e)~=1 then k.Down=pulse
            elseif ib(0x231f)~=2 then k.Right=pulse
            else configured=true;k.B=pulse end
        elseif m==4 or m==5 or m==6 or m==8 or m==11 or m==12 or m==13 then k.A=pulse
        elseif m==7 and ib(0x4529)&7==0 then
            local p,q=actor(0x489c),actor(0x48a0)
            local input,battle=ip(0x4510),ip(0x4514)
            if p and q and input>=0x02010000 and battle>=0x02010000 and ed(input,0)==0x08374ff4 and ed(battle,0)==0x083735bc then
                if full then assert(configured and ib(0x231f)==2,"HARD campaign") end
                if not seen[s] then seen[s]=true;log("live stage "..s) end
                if s~=11 then
                    local t=step
                    if s==7 then
                        first[s]=first[s] or step;t=87296+step-first[s]
                    end
                    k.A=t%97<7;k.B=t%29<7;k.Right=t%720<300;k.Left=t%720>=360 and t%720<660
                    if s==7 and step-first[s]>250 then
                        local dx=sx(ew(q,0x34))-sx(ew(p,0x34));local dy=sx(ew(q,0x36))-sx(ew(p,0x36))
                        k.Left=dx< -320;k.Right=dx>320;k.A=dy<32 and t%61<6;k.B=t%17<5
                    end
                elseif sx(ew(p,0x64))>0 and sx(ew(q,0x64))>0 and ew(q,4)&15==3 and boss[s] then
                    first[s]=first[s] or step
                    local age=step-first[s];local x=sx(ew(p,0x34));local dx=sx(ew(q,0x34))-x
                    local dir=age<100 and 4352-x or dx
                    k.Right=dir>320;k.Left=dir< -320
                    if math.abs(dx)>95 and (dx>0)~=(ew(p,0xb4)&0x4000~=0) and not prior.Left and not prior.Right then
                        k.Right=dx>0;k.Left=dx<0
                    end
                    k.B=age%31<4
                end
            end
        end
        prior=k;joypad.set(k);emu.frameadvance()
    end
    error("frame limit")
end
local ok,err=pcall(run)
if not ok then log(tostring(err));shot("last-frame") end
file("done.txt",ok and "PASS" or tostring(err))
client.exit()
