-- One recovery jump after default Agumon reaches a source ground-input callback.
-- Frozen v2 controls before recovery and its60-frame/cooldown bounds are retained.
local path="W:/tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua"
local f=assert(io.open(path,"rb"));local source=assert(f:read("*a"));f:close()
source=source:gsub("\r\n","\n")
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a,"frozen recovery anchor missing")
 assert(not s:find(old,b+1,true),"ambiguous recovery anchor")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
source=once(source,'escape.remaining=60;escape.away=-direction;escape.stuck=0',
 'escape.remaining=60;escape.away=-direction;escape.stuck=0;escape.jump_age=nil')
source=once(source,'keys["P1 A"]=age>=4 and age<12;keys["P1 B"]=false',[=[
 if escape.jump_age==nil and age>=4 and age<=48 then
  local callback=mainmemory.read_u16_le(at)
  local segment=mainmemory.read_u16_le(at+2)
  local flags=mainmemory.read_u16_le(at+6)
  local form=mainmemory.read_u16_le(at+8)
  local identity=mainmemory.read_u8(at+0x11)
  -- 668E:115D idle and11C9 walk both poll fresh jump edge40 before movement.
  if segment==0x668E and (callback==0x115D or callback==0x11C9) and identity==0
   and flags%2==0 and math.floor(form/0x100)%2==0 and not keys["P1 X3"] then
   escape.jump_age=age;note("escape-jump")
  end
 end
 keys["P1 A"]=escape.jump_age~=nil and age>=escape.jump_age and age<escape.jump_age+12
 keys["P1 B"]=false
]=])
return assert(load(source,"@short-hard-v4-parent","t",_ENV))()
