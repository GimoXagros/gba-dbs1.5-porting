-- Same frozen approved run/input policy, with a safe-frame Shoot checkpoint.
local observer
local advances,last_keys=0,{}
local base_set,base_advance=joypad.set,emu.frameadvance
local input=setmetatable({set=function(keys,...)
 last_keys={};for k,v in pairs(keys)do last_keys[k]=v end
 return base_set(keys,...)
end},{__index=joypad})
local clock=setmetatable({frameadvance=function(...)
 local before=emu.framecount()
 local result=base_advance(...)
 if observer then observer.after_frame({relative=advances,core_before=before,keys=last_keys})end
 advances=advances+1
 return result
end},{__index=emu})
local original_dofile=dofile
local function module(path)
 local result=original_dofile(path)
 if path=="W:/tools/bizhawk_wsc_score999.lua" then
  assert(not observer,"boundary observer installs once")
  -- Frozen A0AC has completed the full authorized-copy startup guard here.
  observer=original_dofile("W:/tools/bizhawk_observe_wsc_shoot_boundary.lua")
  observer.tick()
  return {tick=result.tick,status=result.status,finish=function()
   observer.finish()
   return result.finish()
  end}
 end
 return result
end
local path="W:/tools/bizhawk_probe_wsc_saved_boss_hp1.lua"
local f=assert(io.open(path,"rb"));local source=assert(f:read("*a"));f:close()
local environment=setmetatable({joypad=input,emu=clock,dofile=module},{__index=_ENV})
return assert(load(source,"@shoot-boundary-frozen-boss-driver","t",environment))()
