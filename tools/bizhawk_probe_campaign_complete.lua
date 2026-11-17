-- Fresh, assisted campaign observation. Frozen input and authorized writes stay intact.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"fresh isolated output required")
local ROM="933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775"
assert(userdata.get("probe_sha256")==ROM,"complete 16MiB campaign ROM host pin required")
local function replace(source,before,after)
 local a,b=source:find(before,1,true)
 assert(a and not source:find(before,b+1,true),"unique frozen adaptation")
 return source:sub(1,a-1)..after..source:sub(b+1)
end
local function source(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local log=assert(io.open(out.."/campaign-complete-trace.txt","wb"))
local function emit(s)assert(log:write(s.."\n"));log:flush()end
local initial=emu.framecount()
local observer,highest,row,activation=nil,-1,nil,false
local seen,live_seen,hud_seen={},{},{}
local function read(a,n)
 local domain,offset
 if a>=0x02000000 and a+n<=0x02040000 then domain,offset="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then domain,offset="IWRAM",a-0x03000000
 elseif a>=0x06000000 and a+n<=0x06018000 then domain,offset="VRAM",a-0x06000000
 elseif a>=0x08000000 and a+n<=0x09000000 then domain,offset="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(offset,domain)end
 if n==2 then return memory.read_u16_le(offset,domain)end
 return memory.read_u32_le(offset,domain)
end
local function state()
 return string.format("core=%d relative=%d mode=%d progress=%d row=%d stage=%d cpu=%d cpu_form=%d player=%d difficulty=%d clock=%d runflags=%04X",
  emu.framecount(),emu.framecount()-initial,read(0x03002310,2),read(0x0300232E,1),read(0x0300232F,1),
  read(0x0300231E,1),read(0x0300231C,1),read(0x0300231D,1),read(0x0300231A,1),read(0x0300231F,1),read(0x03004500,2),read(0x0300232A,2))
end
local function require_fact(ok,name,detail,r)
 if ok then return true end
 emit("failure="..name.." "..state().." "..(detail or ""))
 observer.fail(name,detail or state(),r);return false
end
local first={8,1,9,6,10}
local rows={{5,0,3,2,4},{0,3,2,4,5},{3,2,4,5,0},{2,4,5,0,3},
 {4,5,0,3,2},{5,0,3,2,4},{0,3,2,4,5},{2,4,5,0,3}}
local cpus={0,1,2,5,6,4,3,15,13,14,11}
local function expected(progress,rng)
 if progress<5 then return first[progress+1]end
 if progress<10 then return rows[rng+1][progress-4]end
 return 7
end
local function complete()
 if highest~=10 or not hud_seen[9] or not hud_seen[10]then return false end
 for p=0,10 do if not seen[p] or not live_seen[p]then return false end end
 return true
end
local function checkpoint_running()
 if not observer or observer.stopped()then return end
 local p=read(0x0300232E,1)
 if p<=10 and seen[p] and not live_seen[p] and read(0x0300231E,1)==expected(p,row) and observer.live()then
  local a,b=observer.pair(p==10)
  if a and b and read(b+0x11,1)==cpus[expected(p,row)+1]
   and read(b+4,2)%16==(p==10 and 3 or 1)then
   live_seen[p]=emu.framecount()
   emit("event=active-owner progress="..p.." "..state())
   observer.queue(string.format("campaign-active-%02d",p),state())
  end
 end
 if activation then require_fact(complete(),"campaign-proof-incomplete","ordered eleven producers/live owners and progress9/10 HUD required")end
end
local function hook(at,opcode,name,fn)
 assert(read(at,4)==opcode,"campaign hook instruction pin")
 event.on_bus_exec(function()
  if observer.stopped()then return end
  fn(emu.getregisters())
 end,at,"campaign-complete-"..name)
end
local function install()
 -- Check the actual new immutable tables, not only the host identity token.
 for i,v in ipairs(first)do assert(read(0x08D3FB10+i-1,1)==v,"opening table")end
 for n,t in ipairs(rows)do for i,v in ipairs(t)do assert(read(0x08D3FB18+(n-1)*5+i-1,1)==v,"campaign row table")end end
 for i,v in ipairs(cpus)do assert(read(0x08D3FB40+i-1,1)==v,"CPU stage table")end
 hook(0x0808B70C,0xE8BD4013,"producer",function(r)
  local p,rng=read(0x0300232E,1),read(0x0300232F,1)
  if not require_fact(r.R4==0x03002310 and p<=10 and rng<8,"campaign-producer-owner-domain",state(),r)then return end
  if not require_fact(read(0x0300231A,1)==0 and read(0x0300231B,1)==0 and read(0x0300231F,1)==2,
   "campaign-producer-profile",state(),r)then return end
  if not require_fact((highest==-1 and p==0)or p==highest or p==highest+1,"campaign-producer-order",state(),r)then return end
  if not require_fact(row==nil or row==rng,"campaign-rng-row-changed",state(),r)then return end
  local stage=expected(p,rng);local cpu=cpus[stage+1]
  if not require_fact(read(0x0300231E,1)==stage and read(0x0300231C,1)==cpu
   and read(0x0300231D,1)==(cpu==0 and 1 or 0),"campaign-source-row-mismatch",state(),r)then return end
  row=rng
  if not seen[p]then
   highest=p;seen[p]=emu.framecount()
   emit("event=producer "..state())
   observer.queue(string.format("campaign-producer-%02d",p),state(),r)
  end
 end)
 hook(0x080B6054,0xE59F4048,"round-HUD",function(r)
  local p=read(0x0300232E,1)
  if (p~=9 and p~=10)or hud_seen[p]then return end
  if not require_fact(seen[p]~=nil and r.R5==0x0600E820,"campaign-HUD-owner",state(),r)then return end
  local good=true
  if p==9 then
   local values={0x2215,0x2214,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201,0x2201}
   for i,v in ipairs(values)do good=good and read(0x0600E80E+(i-1)*2,2)==v end
  else
   for i=0,15 do good=good and read(0x0600E800+i*2,2)==read(0x080B5FEA+i*2,2)end
  end
  if not require_fact(good,"campaign-HUD-tile-mismatch",state(),r)then return end
  hud_seen[p]=emu.framecount();emit("event=HUD "..state())
  observer.queue(string.format("campaign-HUD-%02d",p),state(),r)
 end)
end
local env=setmetatable({}, {__index=_ENV})
env.dofile=function(path)
 assert(path=="W:/tools/bizhawk_gba_shoot_entry_observer.lua","only frozen Shoot observer")
 local code=source(path)
 code=replace(code,'local PROBE="D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C"','local PROBE="'..ROM..'"')
 code=replace(code,'a+n<=0x08800000','a+n<=0x09000000')
 local module_env=setmetatable({}, {__index=_ENV})
 module_env.event=setmetatable({on_bus_exec=function(fn,at,name)
  if name=="shoot-entry-activation-tail"then
   assert(at==0x085C8D50,"retained activation boundary")
   event.on_bus_exec(function(...)fn(...);activation=true end,at,name)
  else event.on_bus_exec(fn,at,name)end
 end},{__index=event})
 observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()
 local flush,finish=observer.flush,observer.finish
 observer.flush=function()checkpoint_running();flush()end
 observer.finish=function()
  checkpoint_running()
  local result=finish()
  local outcome=result
  if result=="healthy-native-shoot-activation"then
   assert(complete(),"complete campaign evidence before healthy outcome")
   outcome="campaign-eleven-stages-and-healthy-shoot-activation"
  end
  emit("summary outcome="..outcome.." highest="..highest.." "..state().." assisted=true stage11_writes=disabled")
  log:close()
  local f=assert(io.open(out.."/campaign-complete-done.txt","w"));assert(f:write(outcome));f:close()
  return result
 end
 install();return observer
end
env.loadfile=function(path,mode,context)
 assert(path=="W:/tools/bizhawk_probe_gba_collision.lua" and mode=="t","only frozen collision frame loop")
 local code=source(path)
 code=replace(code,'dump("loaded-rom.bin","ROM",0x800000)','dump("loaded-rom.bin","ROM",0x1000000)')
 code=replace(code,'log("system=GBA guest_writes=none input=joypad-only")',
  'log("system=GBA assisted=true guest_writes=guarded-score999-and-stage7-bossHP1 input=frozen-approach-jump-no-up")')
 return load(code,"@frozen-collision-loop-16MiB","t",context)
end
emit("start ROM="..ROM.." assisted=true ordered_producers=0..10 first_live_owners=0..10 HUD=9,10 stage11_writes=disabled frozen_frame_cap=120000")
assert(load(source("W:/tools/bizhawk_probe_gba_shoot_entry.lua"),"@frozen-shoot-entry-driver","t",env))()
