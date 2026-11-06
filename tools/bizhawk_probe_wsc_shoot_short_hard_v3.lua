-- Host-only minimum A hold, applied after frozen collector and wall recovery.
-- Evolved Agumon needs A through input sample9 of an uninterrupted startup.
local root="W:/tools/"
local v2_path=root.."bizhawk_probe_wsc_shoot_short_hard_v2.lua"
local collect_path=root.."bizhawk_probe_wsc_shoot_collect_v2.lua"
local function read(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close()
 return s:gsub("\r\n","\n")
end
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a,"frozen jump anchor missing")
 assert(not s:find(old,b+1,true),"ambiguous jump anchor")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local policy=[=[
local jump_hold={}
local function full_jump(keys)
 local mode=memory.read_u16_le(0x4E,"SRAM")
 local stage=memory.read_u8(0x5C,"SRAM")
 local player=memory.read_u16_le(0x65C,"SRAM")
 local frame=emu.framecount()
 if mode~=7 or stage==11 or player<0x24 or player>0x3654 or (player-0x24)%0x110~=0 then
  jump_hold={};return keys
 end
 if jump_hold.stage~=stage or jump_hold.player~=player or jump_hold.frame~=frame-1 then
  jump_hold={stage=stage,player=player,remaining=0,previous=false}
 end
 jump_hold.frame=frame
 local requested=keys["P1 A"]==true
 if requested and not jump_hold.previous and jump_hold.remaining==0 then jump_hold.remaining=12 end
 jump_hold.previous=requested
 if jump_hold.remaining>0 then
  keys["P1 A"]=true;keys["P1 B"]=false
  jump_hold.remaining=jump_hold.remaining-1
 end
 return keys
end
]=]
local collect=once(read(collect_path),'joypad.set=function(keys,...)',policy..'joypad.set=function(keys,...)')
-- v2 inserts wall_escape inside this argument, so full_jump sees its final keys.
collect=once(collect,'return set_keys(keys,...)','return set_keys(full_jump(keys),...)')
local v2=once(read(v2_path),"'return set_keys(keys,...)','return set_keys(wall_escape(keys),...)'",
 "'return set_keys(full_jump(keys),...)','return set_keys(full_jump(wall_escape(keys)),...)'")
local proxy=setmetatable({open=function(path,mode)
 if path==collect_path then
  assert(mode=="rb","jump dependency is read-only")
  return {read=function(_,kind)assert(kind=="*a");return collect end,close=function()end}
 end
 return io.open(path,mode)
end},{__index=io})
local environment=setmetatable({io=proxy},{__index=_ENV})
return assert(load(v2,"@short-hard-v3-parent","t",environment))()
