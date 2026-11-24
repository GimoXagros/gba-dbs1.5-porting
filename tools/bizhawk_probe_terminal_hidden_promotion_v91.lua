-- Start at the new campaign entered after a won Shoot game, on the same core.
local out=assert(userdata.get("output"))
local rom="6F7B7D942BCDE6F9EFC223150D54672D352606988C1C31471799EFD7C16FA116"
assert(userdata.get("probe_sha256")==rom)
local settings={}
for _,key in ipairs({"output","probe_sha256","score_authorization","boss_authorization"})do
 settings[key]=assert(userdata.get(key))
end
local function write(name,data,how)
 local f=assert(io.open(out.."/"..name,how or "wb"));f:write(data);f:close()
end
local function log(s)write("promotion-trace.txt",emu.framecount().." "..s.."\n","ab")end
local function capture(name,state)
 for _,spec in ipairs({{"IWRAM",0x8000},{"EWRAM",0x40000}}) do
  write(name.."-"..spec[1]..".bin",memory.read_bytes_as_binary_string(0,spec[2],spec[1]))
 end
 client.screenshot(out.."/"..name..".png")
 if state then assert(savestate.save(out.."/"..name..".State",true))end
end
local function run()
 assert(savestate.load(out.."/campaign.State",true))
 local first=emu.framecount()
 assert(first==209311 and memory.read_u16_le(0x2328,"IWRAM")==16)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 local f=assert(io.open("W:/tools/bizhawk_gba_shoot_entry_observer.lua","rb"))
 local src=f:read("*a");f:close()
 src=src:sub(1,assert(src:find('hook(0x0836E5E4,"boss-damage-pre"',1,true))-1)
 src=src:gsub("D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C",rom)
 src=src..[[
return {read=read,pair=pair,live=live,positive=positive,word=word,
  boss11=function(p,q)
   assert(not consumed[11] and pair(true)==p and live() and positive(word(p+0x64)) and word(q+0x64)>1 and positive(word(q+0x64)))
   consumed[11]=true;write_word(q+0x64,1,"boss",p,q,regs())
  end,
  flush=function(fn) for _,e in ipairs(write_ledger)do fn(e)end;write_ledger={}end}
]]
 local env=setmetatable({userdata={get=function(key)return settings[key]end}},{__index=_ENV})
 local obs=assert(load(src,"@typed-campaign-assists","t",env))()
 local read,w=obs.read,obs.word
 local function stage()return read(0x0300231E,1)end
 local events={}
 local misses={}
 event.on_bus_exec(function()
  if w(0x0300450A)&0x400~=0 then local r=emu.getregisters()
   local q=r.R6
   local a=read(q+0xBA,2)
   if not misses[a]then log(string.format("guard-hidden event=%d auxKind=%04X R0=%08X queue=%d",a,w(q+4),r.R0,w(0x0300482A)));misses[a]=true end
  end
 end,0x086FFBF0,"guard-hidden")
 event.on_bus_exec(function()local r=emu.getregisters();if r.R4==read(0x0300489C,4) and r.R5==read(0x030048A0,4) then log(string.format("real-P1-hit P2-before=%d after=%d",w(r.R5+0x64),r.R8&65535))end end,0x0836E5E4,"actual-hit")
 for pc,n in pairs({[0x08373688]="root4",[0x083736B0]="root5",[0x085CD000]="terminal-entry",[0x085CD340]="terminal-middle",[0x085CD740]="terminal-final",[0x08340C54]="cleanup-entry"}) do event.on_bus_exec(function()if not events[n] then events[n]=true;log(n)end end,pc,"terminal-"..n)end
 for pc,label in pairs({[0x080BF1D0]="ending-entry",[0x080BF58C]="pending-probe",
  [0x085B1100]="selected-mask-commit",[0x080BF698]="after-permanent-commit",
  [0x080BF6BC]="record-or",[0x080C0D28]="name-accepted",[0x080C0E04]="ff-bypass"})do
  event.on_bus_exec(function()
   if not events[label]then
    events[label]=true;local r=emu.getregisters()
    log(string.format("%s pending=%02X permanent=%02X saved=%02X R0=%08X R1=%08X",
     label,read(0x03002328,1),read(0x03002329,1),read(0x03001132,1),r.R0,r.R1))
   end
  end,pc,label)
 end
 for _,a in ipairs({0x03002328,0x03002329,0x03001132})do
  event.on_bus_write(function(addr,val,flags)
   log(string.format("config-write address=%08X prior=%04X value=%04X pc=%08X",addr,w(addr),val&65535,emu.getregisters().R15))
  end,a,"write-"..a)
 end
 local function signed(v)return v>=32768 and v-65536 or v end
 local previous,prevstage,transformed,assisted=-1,-1,false,false
 local lastsave=false
 local initialKeys={"A","B","Start","Select","Up","Down","Left","Right","L","R","Power"}
 for frame=0,35000 do
  local m=w(0x03002310);local st=stage()
  if m~=previous or st~=prevstage then
   log("mode="..m.." stage="..st.." flags="..w(0x03002328).." progression="..read(0x0300232E,1))
   if m==7 then capture("campaign-stage-"..st,true)end
   previous=m;prevstage=st
  end
  if frame==5600 then capture("idle-sample",true)end
  if frame%5000==0 then log("live="..tostring(obs.live()).." clock="..w(0x03004500))end
  if m==9 then capture("continue",true);error("campaign continue")end
  if events["after-permanent-commit"] and not lastsave and read(0x03001132,1)&16~=0 then
   lastsave=true;capture("permanent-award",true)
  end
  if m==3 and events["ff-bypass"] then
   assert(lastsave and read(0x03002329,1)&16~=0 and read(0x03002328,1)&16==0)
   capture("permanent-title",true);return
  end
  local keys={};for _,key in ipairs(initialKeys)do keys[key]=false end
  if m==7 and obs.live()then
   if st~=11 then
    keys.A=frame%97<7;keys.B=frame%29<7
    keys.Right=frame%720<300;keys.Left=frame%720>=360 and frame%720<660
   else
    local p,q=obs.pair(true)
    if p and obs.positive(w(p+0x64)) and obs.positive(w(q+0x64)) then
     local cb=read(p,4);local held=w(p+0x2C);local right=w(p+0xB4)&0x4000~=0
     local dx=signed(w(q+0x34))-signed(w(p+0x34))
     local dy=signed(w(q+0x36))-signed(w(p+0x36))
     local vx=signed(w(q+0x34))-signed(w(q+0x38))
     local vy=signed(w(q+0x36))-signed(w(q+0x3A))
     local fwd=(right and 1 or -1)*(dx+15*vx)
     local vert=dy+15*vy
     local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(p+6)&1==0 and w(p+0x76)==0
     local ev=w(q+0xBA)
     if not transformed and ready then capture('activation',true);transformed=true end
     if frame%37==0 then log(string.format('aim cb=%08X qcb=%08X x=%d y=%d dx=%d dy=%d face=%s hp=%d qhp=%d ev=%d ready=%s',cb,read(q,4),signed(w(p+0x34)),signed(w(p+0x36)),dx,dy,tostring(right),w(p+0x64),w(q+0x64),ev,tostring(ready)))end
     if cb==0x0835620C and math.abs(dx)>600 then keys.Right=dx>0;keys.Left=dx<0 end
     if ready and math.abs(dx)>=96 and (dx>0)~=right then
      keys.Right=dx>0 and held&2==0;keys.Left=dx<0 and held&8==0
     elseif ready and held&0x80==0 and (ev==1 or ev==4 or ev==5) then
      if not assisted then obs.boss11(p,q);assisted=true end
      keys.B=true
     end
    end
   end
  elseif m==8 or m==11 or m==4 or m==5 or m==6 then keys.A=frame%30<4 end
  joypad.set(keys);emu.frameadvance()
  obs.flush(function(e)write("assist-ledger.txt",e.."\n","ab")end)
 end
 error("bounded campaign")
end
local ok,err=pcall(run)
if not ok then log(tostring(err))end
write("collection-done.txt",ok and "permanent-award-title" or "failure")
client.exit()
