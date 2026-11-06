-- Host-only finite recovery layered over the frozen E382 short-hard observer.
-- No game writes, save/state load, terrain planner, or active-file modification.
local parent_path="W:/tools/bizhawk_probe_wsc_shoot_short_hard.lua"
local collect_path="W:/tools/bizhawk_probe_wsc_shoot_collect_v2.lua"
local function read(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close()
 return s:gsub("\r\n","\n")
end
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a,"frozen recovery anchor missing")
 assert(not s:find(old,b+1,true),"ambiguous recovery anchor")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local policy=[=[
local escape,captures={},0
local function wall_escape(keys)
 local mode=memory.read_u16_le(0x4E,"SRAM")
 local stage=memory.read_u8(0x5C,"SRAM")
 local player=memory.read_u16_le(0x65C,"SRAM")
 local target=memory.read_u16_le(0x65E,"SRAM")
 local frame=emu.framecount()
 local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
 if mode~=7 or stage==11 or not valid(player) or not valid(target) then escape={};return keys end
 local at,other=0xC000+player,0xC000+target
 local x,y=signed(mainmemory.read_u16_le(at+0x26)),signed(mainmemory.read_u16_le(at+0x28))
 local tx,ty=signed(mainmemory.read_u16_le(other+0x26)),signed(mainmemory.read_u16_le(other+0x28))
 if escape.stage~=stage or escape.player~=player or escape.target~=target or escape.last_frame~=frame-1 then
  escape={stage=stage,player=player,target=target,last_frame=frame,anchor=x,stuck=0,cooldown=0,remaining=0}
 end
 escape.last_frame=frame
 local function note(kind)
  local f=assert(io.open(output.."/escape.txt","a"))
  f:write(string.format("%s frame=%d stage=%d p1=%04X,%04X target=%04X,%04X away=%d remaining=%d cooldown=%d\n",
   kind,frame,stage,x%65536,y%65536,tx%65536,ty%65536,escape.away or 0,escape.remaining,escape.cooldown));f:close()
 end
 if escape.remaining==0 and escape.cooldown>0 then
  escape.cooldown=escape.cooldown-1;escape.stuck=0;escape.anchor=x
  return keys
 end
 if escape.remaining==0 then
  local direction=keys["P1 X4"] and not keys["P1 X2"] and -1 or keys["P1 X2"] and not keys["P1 X4"] and 1 or 0
  local eligible=y-ty>0x300 and math.abs(tx-x)>0x100 and direction*(tx-x)>0
  if not eligible then escape.stuck=0;escape.anchor=x;escape.direction=direction;return keys end
  if escape.direction~=direction or math.abs(x-escape.anchor)>0x20 then
   escape.stuck=0;escape.anchor=x;escape.direction=direction
  end
  escape.stuck=escape.stuck+1
  if escape.stuck<180 then return keys end
  escape.remaining=60;escape.away=-direction;escape.stuck=0
  note("escape-start")
  if captures<3 then
   captures=captures+1
   local name=string.format("%s/escape-%d-stage-%d-frame-%d",output,captures,stage,frame)
   client.screenshot(name..".png")
   local f=assert(io.open(name.."-ram.bin","wb"))
   f:write(mainmemory.read_bytes_as_binary_string(0,0x10000));f:close()
  end
 end
 local age=60-escape.remaining
 keys["P1 X2"]=escape.away==1;keys["P1 X4"]=escape.away==-1
 keys["P1 A"]=age>=4 and age<12;keys["P1 B"]=false
 escape.remaining=escape.remaining-1
 if escape.remaining==0 then escape.cooldown=360;escape.anchor=x;note("escape-end")end
 return keys
end
]=]
local collect=read(collect_path)
collect=once(collect,'joypad.set=function(keys,...)',policy..'joypad.set=function(keys,...)')
collect=once(collect,'return set_keys(keys,...)','return set_keys(wall_escape(keys),...)')
local proxy=setmetatable({open=function(path,mode)
 if path==collect_path then
  assert(mode=="rb","collector dependency is read-only")
  return {read=function(_,kind)assert(kind=="*a");return collect end,close=function()end}
 end
 return io.open(path,mode)
end},{__index=io})
local environment=setmetatable({io=proxy},{__index=_ENV})
return assert(load(read(parent_path),"@short-hard-v2-parent","t",environment))()
