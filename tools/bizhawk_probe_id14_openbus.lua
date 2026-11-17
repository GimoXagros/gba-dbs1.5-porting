-- Reuse ordinary contact solely to observe the malformed collision producer.
local function read(name)
 local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true)
 assert(a and not s:find(before,b+1,true),"unique openbus boundary")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local env=setmetatable({},{__index=_ENV})
local observer=assert(load(read("bizhawk_observe_collision_openbus.lua"),"@openbus-observer","t",env))()
env.openbus_evidence=observer
local composed=0
env.load=function(source,name,mode,context)
 if name=="@reviewed-evolution-music-pause" then
  composed=composed+1;assert(composed==1,"single final openbus composition")
  source=replace(source,' local pause_outcome=music_pause_outcome()',
   ' local pause_outcome=openbus_evidence.outcome() or music_pause_outcome()')
  source=replace(source,'if outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then',
   'if outcome~="collision-openbus-producer-observed" and outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then')
  source=replace(source,'music_lifetime_finish()\nid14_evidence_finish()\nlocal f=',
   'music_lifetime_finish()\nid14_evidence_finish()\nopenbus_evidence.finish()\nlocal f=')
 end
 return load(source,name,mode,context)
end
assert(load(read("bizhawk_probe_evolution_id14_r2.lua"),"@ID14-openbus","t",env))()
