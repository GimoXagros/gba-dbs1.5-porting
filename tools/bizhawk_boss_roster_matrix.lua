-- Select the player in the ordinary roster. Reuse only the earned final-round index.
local out=assert(userdata.get("out"))
local fid=assert(tonumber(userdata.get("fighter")))
local form=assert(tonumber(userdata.get("form")))
local round=assert(tonumber(userdata.get("progress")))
local function file(n,s,mode)local f=assert(io.open(out.."/"..n,mode or "wb"));f:write(s);f:close()end
local function log(s)file("events.txt",emu.framecount().." "..s.."\n","ab")end
local function b(a)return memory.read_u8(a,"System Bus")end
local function w(a)return memory.read_u16_le(a,"System Bus")end
local function d(a)return memory.read_u32_le(a,"System Bus")end
local function signed(v)return v>=32768 and v-65536 or v end
local function actor(addr)
    local v=d(addr)
    if v>=0x02010018 and v<=0x02013900 and (v-0x02010018)%280==0 and w(v-8)&2~=0 then return v end
end
local function task(priority)
    for i=0,51 do
        local h=0x02010000+i*280
        if w(h+16)&2~=0 and d(h+4)==priority then return h end
    end
end
local function run()
    assert(emu.framecount()<4 and emu.getsystemid()=="GBA")
    file("loaded.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
    client.speedmode(3200)
    local configured,selected,advanced,ending=false,false,false,false
    local started,ko,active,entry,save={}, {}, {}, {}, {}
    local strategy=tonumber(userdata.get("first_strategy")) or 0
    local attempt={[7]=strategy,[11]=0}
    local function checkpoint(s) return out.."/live-"..s..".State" end
    local resume=tonumber(userdata.get("resume"))
    local postko=tonumber(userdata.get("postko"))==1
    local recorded_strategy=tonumber(userdata.get("variant")) or 0
    if resume then
        assert(savestate.load(out.."/entry.State",true))
        assert(w(0x03002310)==7 and b(0x0300231a)==fid and b(0x0300231e)==resume)
        assert(b(0x0300232e)==round and b(0x0300231f)==2)
        local hero,enemy=assert(actor(0x0300489c)),assert(actor(0x030048a0))
        assert(b(hero+17)==fid and b(enemy+17)==15)
        if postko then
            assert(resume==11 and signed(w(enemy+0x64))<=0 and d(enemy)==0x085bdd00)
            ko[11]=emu.framecount()-1
            log("restored first frame after genuine KO of stage 11")
        else
            assert(w(enemy+0x64)==1)
            assert(savestate.save(checkpoint(resume),true))
        end
        configured,selected,advanced=true,true,true
        active[resume],started[resume]=true,1
        if resume==11 then entry.phase7=true end
        attempt[resume]=math.max(attempt[resume],recorded_strategy)
        log("restored genuine stage "..resume.." fighter "..fid.." attempt "..attempt[resume])
    end
    local last,state={},{}
    event.on_bus_exec(function()
        if selected and not advanced then
            assert(b(0x0300231a)==fid and b(0x0300232e)==0 and b(0x0300231f)==2)
            memory.write_u8(0x232e,round,"IWRAM")
            advanced=true;log("selected fighter "..fid.." palette "..b(0x0300231b).." earned final round "..round)
        end
    end,0x0808b638,"reuse earned final-round index")
    event.on_bus_exec(function()
        if advanced and b(0x0300231e)==7 then
            local r=emu.getregisters()
            log(string.format("native stage7 initial HP %d for fighter %d",r.R10&65535,b(r.R5+17)))
        end
    end,0x0836fd44,"native stage 7 starting HP")
    event.on_bus_exec(function()
        local stage=b(0x0300231e)
        local r=emu.getregisters()
        local p,q=actor(0x0300489c),actor(0x030048a0)
        if active[stage] and r.R5==q and w(q+0x64)==1 and signed(r.R8&65535)<=0 and not ko[stage] then
            assert(p and b(p+17)==fid and b(q+17)==15)
            ko[stage]=emu.framecount()
            log(string.format("KO stage=%d hitter=%08X player=%08X boss=%08X hp_before=1 damage_result=%d boss_cb=%08X anim=%d",stage,r.R4,p,q,signed(r.R8&65535),d(q),w(q+0xba)))
        end
    end,0x0836e5e4,"genuine lethal hit")
    event.on_bus_exec(function()
        if ko[11] then
            local r=emu.getregisters()
            log(string.format("result decision mode=%d fighter=%d flags=%04X prior=%04X continued=%04X clear=%04X",
                w(0x03002310),fid,r.R0&0xffff,r.R3&0xffff,w(0x0300232a),w(0x0300232c)))
        end
    end,0x08089534,"actual native win decision")
    event.on_bus_exec(function()
        if ko[11] then log(string.format("native clear record %04X",w(0x0300232c))) end
    end,0x0808b360,"physical clear candidate")
    event.on_bus_exec(function()
        if ko[11] then
            log(string.format("save operation=%d selector=%d core-clear=%04X record-clear=%04X",
                d(emu.getregister("R13")),d(emu.getregister("R13")+4),w(0x0300232c),w(0x03001130)))
        end
    end,0x0801fbd0,"normal save call")
    event.on_bus_exec(function()
        if ko[11] then ending=true;log("native ending") end
    end,0x080bf1d0,"ending")
    event.on_bus_exec(function()
        if ko[11] then
            local block=emu.getregister("R0")&65535
            if block==2 then log(string.format("writing clear block %04X",w(emu.getregister("R1")))) end
            if not save[block] then save[block]=true;log("post-KO EEPROM block "..block) end
        end
    end,0x0837db54,"EEPROM write")
    local sequence={0,1,2,3,4,5,6,7,8,9,10,13,14,11,12}
    local previous=-1
    local prior={}
    for f=1,100000 do
        local m,s=w(0x03002310),b(0x0300231e)
        if m~=previous or state.stage~=s then
            log("mode "..m.." stage "..s)
            if m==8 and ko[11] then log("KO to result "..(emu.framecount()-ko[11]).." frames");entry.result=true end
            previous=m;state.stage=s
        end
        local k={};local pulse=f%17<2
        if m==3 then
            if ending then
                assert((ko[7] or entry.phase7) and ko[11] and entry.result,"missing ending path")
                log("post-KO EEPROM block writes "..(next(save) and "seen" or "none"))
                client.screenshot(out.."/title.png");log("title after ending");return
            end
            local h=task(0x1000)
            if h and d(h)==0x08090c7c then k.Start=pulse
            elseif h and d(h)==0x08dfe048 then
                local goal=configured and 0 or 2
                k[b(h+29)==goal and "A" or "Down"]=pulse
            end
        elseif m==14 and task(0x1500) then
            if w(0x0300473e)~=1 then k.Down=pulse
            elseif b(0x0300231f)~=2 then k.Right=pulse
            else configured=true;k.B=pulse end
        elseif m==4 then
            local cursor=w(0x0300473c)
            if w(0x03004740)==14 and cursor==w(0x0300473e) and cursor<=14 then
                local wanted=sequence[cursor+1]==fid
                if wanted then
                    if form==1 and not state.alternate then
                        if pulse then k.Right=true;state.alternate=true end
                    else selected=true;k.A=pulse end
                else k.Down=pulse end
            end
        elseif m==7 then
            local p,q=actor(0x0300489c),actor(0x030048a0)
            if fid==14 and s==7 and p and q and b(p+17)==14 and b(q+17)==15 and d(q)==0x08371e74 and w(q+0x64)==0 and not active[s] then
                state.zero=(state.zero or 0)+1
                if state.zero>=30 then
                    log(string.format("active stage7 boss HP zero at %08X before player input; player HP %d",d(q),w(p+0x64)))
                    error("zero initial stage7 HP")
                end
            end
            if f%1000==0 and not ko[s] then
                log(string.format("tracking stage=%d active=%s p=%08X id=%d xy=%d,%d hp=%d enemy=%08X id=%d xy=%d,%d hp=%d input=%08X flags=%d",s,tostring(active[s]),
                    p or 0,p and b(p+17) or -1,p and signed(w(p+0x34)) or 0,p and signed(w(p+0x36)) or 0,p and signed(w(p+0x64)) or 0,
                    q or 0,q and b(q+17) or -1,q and signed(w(q+0x34)) or 0,q and signed(w(q+0x36)) or 0,q and signed(w(q+0x64)) or 0,d(0x03004510),b(0x03004529)))
            end
            if p and q and (s==7 or s==11) and b(p+17)==fid and b(q+17)==15 and d(p+0x18)==q and d(q+0x18)==p then
                if ko[s] then
                    local age=emu.framecount()-ko[s]
                    if age==1 then assert(savestate.save(out.."/after-ko-"..s..".State",true)) end
                    local info=string.format("%08X:%04X:%04X",d(q),w(q+0xba),w(q+0x64))
                    if last[s]~=info then log("after KO "..s.." "..info);last[s]=info end
                    if age==120 or age==1200 or age==2700 then client.screenshot(out.."/post-ko-"..s.."-"..age..".png") end
                    assert(age<4400,"boss stayed in battle 4400 frames after lethal hit")
                else
                    local input,battle=d(0x03004510),d(0x03004514)
                    if b(0x03004529)&7==0 and input>=0x02010000 and battle>=0x02010000 and d(input)==0x08374ff4 and d(battle)==0x083735bc and w(q+4)&15==3 and signed(w(p+0x64))>0 and signed(w(q+0x64))>0 then
                        if not active[s] then
                            active[s]=true;started[s]=f
                            log(string.format("live stage %d player %d hp %d boss %d hp %d form %d",s,b(p+17),w(p+0x64),b(q+17),w(q+0x64),b(0x0300231b)))
                            memory.write_u16_le(q-0x02000000+0x64,1,"EWRAM")
                            assert(w(q+0x64)==1)
                            assert(savestate.save(checkpoint(s),true))
                        end
                        local age=f-started[s]
                        local x=signed(w(p+0x34))
                        local dx=signed(w(q+0x34))-x
                        local dy=signed(w(q+0x36))-signed(w(p+0x36))
                        local dir=(s==11 and age<100) and 4352-x or dx
                        k.Right=dir>240;k.Left=dir< -240
                        if math.abs(dx)>95 and (dx>0)~=(w(p+0xb4)&0x4000~=0) and not prior.Left and not prior.Right then k.Right=dx>0;k.Left=dx<0 end
                        local variant=attempt[s]
                        if s==7 and variant==0 and age<=250 then
                            local t=87296+age
                            k.A=t%97<7;k.B=t%29<7;k.Right=t%720<300;k.Left=t%720>=360 and t%720<660
                        elseif s==7 and variant==0 then
                            local t=87296+age
                            k.Left=dx< -320;k.Right=dx>320;k.A=dy<32 and t%61<6;k.B=t%17<5
                        elseif variant==0 then
                            k.B=age%31<4
                            if age>800 then k.A=dy<120 and age%59<9 end
                            if age>1200 then k.Up=age%400<135;k.Down=age%400>=285 end
                        else
                            local reach=({320,700,160,480,880})[variant%5+1]
                            local target=({4352,5400,3100,4100,3600})[variant%5+1]
                            local tx=age<100+variant%7*20 and target-x or dx
                            k.Left=tx< -reach;k.Right=tx>reach
                            if math.abs(dx)>95 and (dx>0)~=(w(p+0xb4)&0x4000~=0) and not prior.Left and not prior.Right then k.Right=dx>0;k.Left=dx<0 end
                            local phase=variant//5
                            k.B=age%(31+variant%5*4)<5
                            if phase>=1 then k.A=dy<160 and age%61<7 end
                            if phase>=2 then k.Up=age%100<48;k.B=age%17<4 end
                            if phase>=3 then k.Down=age%103<35 end
                            if s==7 and variant>=8 then
                                -- Jump before attacking. A ground attack can consume the jump press.
                                local ledge=({1960,5230,1810,5390})[(variant-8)%4+1]
                                local climb=age%(590+variant%4*71)<(240+variant%5*48)
                                local tx=climb and ledge-x or dx
                                k.Left=tx< -128;k.Right=tx>128
                                k.A=age%(46+variant%5*6)<33
                                k.B=signed(w(p+0x36))<3910 and age%(17+variant%4*6)<5
                                k.Up=variant%3~=2 and k.B;k.Down=variant%4==3 and k.B
                            end
                        end
                    end
                end
            end
        elseif m==9 then
            assert(active[s] and not ko[s],"unexpected Continue")
            attempt[s]=attempt[s]+1
            assert(attempt[s]<25,"could not land a surviving hit across controller retries")
            assert(savestate.load(checkpoint(s),true))
            started[s]=f;last[s]=nil;prior={}
            log("input retry "..s.." "..attempt[s])
        elseif m==5 or m==6 or m==8 or m==11 or m==12 or m==13 then k.A=pulse end
        prior=k;joypad.set(k);emu.frameadvance()
    end
    error("frame limit")
end
local ok,err=pcall(run)
if not ok then log(tostring(err));client.screenshot(out.."/last.png") end
file("done",ok and "PASS" or tostring(err))
client.exit()
