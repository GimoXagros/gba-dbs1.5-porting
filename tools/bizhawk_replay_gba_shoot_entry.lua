-- Resume a genuine approved boss checkpoint; no new guest-memory cheat writes.
local args={}
for _,key in ipairs({"output","checkpoint_dir","frames","probe_sha256","score_authorization","boss_authorization"})do
 args[key]=assert(userdata.get(key),"missing replay argument: "..key)
end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$") and reference:match("^W:/build/[%w%-%_/]+$") and out~=reference)
local budget=assert(tonumber(args.frames));assert(budget%1==0 and budget>=1 and budget<=8000)
assert(emu.getsystemid()=="GBA" and #args.probe_sha256==64 and args.probe_sha256:match("^%x+$"))
local function read(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(data);f:close()
end
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a and not s:find(old,b+1,true),"unique replay anchor: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function replay()
local metadata=read(reference.."/stage7-hp1.txt")
local captured,relative=metadata:match("^core=(%d+) input_relative=(%d+) stage7_consumed=true ")
captured,relative=assert(tonumber(captured)),assert(tonumber(relative))
assert(captured==64230 and relative==64229,"reviewed checkpoint epoch required")
local epoch=captured-relative
assert(read(reference.."/stage7-hp1.State"):sub(1,4)=="PK\003\004")
assert(savestate.load(reference.."/stage7-hp1.State",true)==true,"genuine checkpoint load failed")
userdata.clear()
for key,value in pairs(args)do userdata.set(key,value);assert(userdata.get(key)==value)end
assert(emu.framecount()==captured,"restored core frame mismatch")
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},{"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local function check_memory()
 for _,r in ipairs(regions)do
  assert(memory.getmemorydomainsize(r[2])==r[3])
  assert(memory.read_bytes_as_binary_string(0,r[3],r[2])==read(reference.."/05-stage7-checkpoint-"..r[1]..".bin"),"restored "..r[1].." mismatch")
 end
end
check_memory()
assert(savestate.save(out.."/restored.State",true)==true,"restored state export failed")
assert(emu.framecount()==captured);check_memory()
write("replay.txt",string.format("restored_core=%d input_epoch=%d next_input_relative=%d frames=%d guest_writes=none historical_stage7_consumed=true new_boss_writes=0 target_rom=%s\n",captured,epoch,relative,budget,args.probe_sha256))

local module=read("W:/tools/bizhawk_gba_shoot_entry_observer.lua"):gsub("\r\n","\n")
module=once(module,'local PROBE="D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C"','local PROBE="'..args.probe_sha256..'"')
module=once(module,"local initial=emu.framecount()","local initial="..epoch)
module=once(module,"local consumed={}","local consumed={[7]=true}")
module=once(module,"local boss_checkpoint=false","local boss_checkpoint=true")
local driver=read("W:/tools/bizhawk_probe_gba_shoot_entry.lua"):gsub("\r\n","\n")
driver=once(driver,"local initial=emu.framecount()","local initial="..epoch)
driver=once(driver,'local menu="title-options"','local menu="battle"')
driver=once(driver,"local battle=false","local battle=true")
local env=setmetatable({}, {__index=_ENV})
env._ENV=env
env.memory=setmetatable({write_u16_le=function()error("replay guest write forbidden")end},{__index=memory})
local observer
env.dofile=function(path)
 assert(path=="W:/tools/bizhawk_gba_shoot_entry_observer.lua","unexpected replay module")
 observer=assert(load(module,"@reviewed-native-observer-replay","t",env))()
 local p,q=observer.pair(true)
 assert(p and observer.live() and observer.read(0x0300231E,1)==7
  and observer.read(p+0x64,2)==8 and observer.read(q+0x64,2)==1,"typed genuine boss checkpoint required")
 return observer
end
-- The reused driver owns its bounded loop, safe captures, final key release and exit.
assert(load(driver,"@reviewed-native-input-replay","t",env))()
end
local ok,err=pcall(replay)
if not ok then
 write("replay-failure.txt",tostring(err).."\n")
 write("shoot-entry-done.txt","failure:replay-preflight")
 client.exit()
end
