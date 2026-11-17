-- Ordinary input lead for the measured event57 startup; all hit/save guards stay frozen.
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua","rb"))
local source=assert(f:read("*a"));assert(f:close())
source=source:gsub("\r\n","\n")
local before=[=[ local horizontal=forward>=96 and forward<=384
 local vertical=dy>=128 and dy<=256]=]
local after=[=[ local vx=signed(w(q+0x34))-signed(w(q+0x38))
 local vy=signed(w(q+0x36))-signed(w(q+0x3A))
 local lead_dx=dx+15*vx
 local lead_dy=dy+15*vy
 local lead_forward=right and lead_dx or -lead_dx
 local horizontal=lead_forward>=128 and lead_forward<=576
 local vertical=lead_dy>=-384 and lead_dy<=64]=]
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique measured input lead replacement")
source=source:sub(1,a-1)..after..source:sub(b+1)
assert(load(source,"@shoot-checkpoint-event57-lead","t",_ENV))()
