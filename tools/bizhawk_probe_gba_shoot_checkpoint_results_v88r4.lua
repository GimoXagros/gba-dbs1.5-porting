-- Source final-results route with measured input lead and autonomous native modes12/13.
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
local function once(old,new)
 local a,b=source:find(old,1,true)
 assert(a and not source:find(old,b+1,true),"unique source ending adaptation: "..old)
 source=source:sub(1,a-1)..new..source:sub(b+1)
end
once("5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC",
 "E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C")
once("mode~=7 and mode~=8 and mode~=11 and mode~=20 and mode~=3",
 "mode~=7 and mode~=8 and mode~=12 and mode~=13 and mode~=11 and mode~=20 and mode~=3")
once(' local start=assert(s:find("local function finish(outcome)",1,true))',[==[
 s=replaced(s,' hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)',[=[
 hook(0x080BBC24,0xE92D403F,"mode12-constructor",function(r)
  if require_fact(mode()==12 and seen["results-constructor"],"mode12-before-results",r)then
   record("mode12-constructor",observer.state(),r,true)
  end
 end)
 hook(0x080BD8E8,0xE8BD0020,"mode12-request",function(r)
  if require_fact(mode()==12 and seen["mode12-constructor"] and w(0x0201D29C)==0
   and w(0x03002314)==1 and w(0x03002316)==0 and w(0x03002318)==0,"mode12-exit",r)then
   record("mode12-request","timer=0 request=1,0,0",r,true)
  end
 end)
 hook(0x080CA24C,0xE92D403F,"mode13-constructor",function(r)
  if require_fact(mode()==13 and seen["mode12-request"],"mode13-before-mode12-exit",r)then
   record("mode13-constructor",observer.state(),r,true)
  end
 end)
 hook(0x080C1018,0xE59F50D0,"ending-card-ready",function(r)
  local h=read(0x0300133C,4)
  if require_fact(mode()==11 and ending_mode and active(h) and read(h,4)==0x080C0F40
   and r.R1==h+0x18 and w(r.R1+8)&3==1 and w(r.R1+0xA)==75,"ending-card-owner",r)then
   menu_ready={mode=11,core=emu.framecount()}
   record("ending-card-ready",string.format("owner=%08X flags=%04X timer=%d",h,w(r.R1+8),w(r.R1+0xA)),r,true)
  end
 end)
 hook(0x080C10CC,0xEBFD43D7,"ending-card-request",function(r)
  if require_fact(mode()==11 and seen["ending-card-ready"] and w(0x03002314)==1
   and w(0x03002316)==0 and w(0x03002318)==0,"ending-card-exit",r)then
   record("ending-card-request","request=1,0,0",r,true)
  end
 end)
 hook(0x080CA39C,0xE8BD0020,"mode13-normal-request",function(r)
  if require_fact(mode()==13 and seen["mode13-constructor"] and w(0x03003DA2)>=22
   and w(0x03004270)==0x3F and w(0x03002314)==1 and w(0x03002316)==0
   and w(0x03002318)==0,"mode13-normal-exit",r)then
   record("mode13-normal-request","cursor="..w(0x03003DA2).." complete=003F request=1,0,0",r,true)
   seen["mode13-request"]=true
  end
 end)
 hook(0x080CBCC0,0xE8BD0020,"mode13-request",function(r)
  if require_fact(mode()==13 and seen["mode13-constructor"] and w(0x03002314)==1
   and w(0x03002316)==0 and w(0x03002318)==0,"mode13-exit",r)then
   record("mode13-request","request=1,0,0",r,true)
  end
 end)
 hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)]=])
 s=replaced(s,'require_fact(result_mode,"ending-before-results",r)',
  'require_fact(result_mode and seen["mode13-request"],"ending-before-mode13-exit",r)')
 s=replaced(s,'require_fact(ending_mode,"mode20-before-ending",r)',
  'require_fact(ending_mode and seen["ending-card-request"],"mode20-before-card-exit",r)')
 s=replaced(s,'read(owner+4,4)==0xF100','read(owner+4,4)==0xFFFFF100')
 local start=assert(s:find("local function finish(outcome)",1,true))]==])
once("SOURCE_CORE,AIM_FRAMES,MAX_FRAMES=89405,1800,8000",
 "SOURCE_CORE,AIM_FRAMES,MAX_FRAMES=89405,1800,16000")
assert(load(source,"@shoot-checkpoint-source-results-route","t",_ENV))()
