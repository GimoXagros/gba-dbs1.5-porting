-- Keep the baseline menu/input, then follow the new source-backed air states.
local function read(name)local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s end
local function replace(s,before,after)
 local a,b=s:find(before,1,true);assert(a and not s:find(before,b+1,true),"unique ID13 air boundary")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local env=setmetatable({},{__index=_ENV})
local air=assert(load(read("bizhawk_observe_id13_air_relaunch.lua"),"@ID13-air-observer","t",env))()
env.load=function(source,name,mode,context)
 if name=="@ID13-ordinary-fall-entry" then
  context.id13_air=air
  source=replace(source,' id13_input(keys,stage,mode)\n joypad.set(keys)',' id13_input(keys,stage,mode)\n id13_air.input(keys,stage,mode)\n joypad.set(keys)')
  source=replace(source,' if id13_outcome() then outcome="id13-eligible-fall-observed";capture("id13-fall-after") end',
   ' local air_outcome=id13_air.outcome()\n if air_outcome then outcome=air_outcome;capture("id13-air-end") end')
  source=replace(source,'id13_finish()\nlocal f=','id13_finish()\nid13_air.finish()\nlocal f=')
 end
 return load(source,name,mode,context)
end
local source=read("bizhawk_probe_id13_fall_entry.lua")
source=replace(source,'assert(rd(at,4)==0xE1D482BC,"reviewed original common-fall input load")',
 'local target=({[0x08357054]=0x08D3F100,[0x0835732C]=0x08D3F150,[0x083578D4]=0x08D3F1A0})[at]\n assert(rd(at,4)==(0xEA000000|(((target-at-8)//4)&0xFFFFFF)),"reviewed ID13 fall adapter")')
assert(load(source,"@ID13-air-route","t",env))()
