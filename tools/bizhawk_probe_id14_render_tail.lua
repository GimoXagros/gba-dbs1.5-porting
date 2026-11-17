-- Observe the previously uncaptured 120 neutral frames after music returns.
local function read(name)
 local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true)
 assert(a and not s:find(before,b+1,true),"unique render-tail boundary")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local env=setmetatable({},{__index=_ENV})
local observer=assert(load(read("bizhawk_observe_render_tail.lua"),"@render-tail-observer","t",env))()
env.render_tail=observer
local composed=0
env.load=function(source,name,mode,context)
 if name=="@reviewed-evolution-music-pause" then
  composed=composed+1;assert(composed==1,"single final render-tail composition")
  source=replace(source,'local outcome','local outcome\nlocal render_tail_start\nlocal render_tail_captures={[0]=true,[1]=true,[2]=true,[4]=true,[8]=true,[16]=true,[32]=true,[64]=true,[120]=true}')
  local before=' local pause_outcome=music_pause_outcome()\n if pause_outcome then outcome=pause_outcome;capture("pause-end") end'
  local after=[=[ local pause_outcome=music_pause_outcome()
 if pause_outcome=="evolution-pause-resume-stage-return" then
  render_tail_start=render_tail_start or emu.framecount()
  local age=emu.framecount()-render_tail_start
  assert(age>=0 and age<=120,"bounded post-return observation")
  render_tail.frame(age)
  if render_tail_captures[age] then capture("render-tail-"..age) end
  if age<120 then pause_outcome=nil end
 end
 if pause_outcome then outcome=pause_outcome;capture("pause-end") end]=]
  source=replace(source,before,after)
  source=replace(source,'music_lifetime_finish()\nid14_evidence_finish()\nlocal f=',
   'music_lifetime_finish()\nid14_evidence_finish()\nrender_tail.finish()\nlocal f=')
 end
 return load(source,name,mode,context)
end
assert(load(read("bizhawk_probe_evolution_id14_r2.lua"),"@ID14-render-tail","t",env))()
