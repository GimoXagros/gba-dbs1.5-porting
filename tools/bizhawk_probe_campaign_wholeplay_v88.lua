-- Fresh campaign with the measured Shoot input lead and source final Results route.
local f=assert(io.open("W:/tools/bizhawk_probe_campaign_wholeplay_v86.lua","rb"))
local source=assert(f:read("*a"));assert(f:close())
source=source:gsub("\r\n","\n")
local function once(old,new)
 local a,b=source:find(old,1,true)
 assert(a and not source:find(old,b+1,true),"unique v88 full-play replacement")
 source=source:sub(1,a-1)..new..source:sub(b+1)
end
once("574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76",
 "E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C")
once([=[local function select_tail(keys,which)
 if not healthy then return false end
 if done or observer.stopped()then return true end
 local core=emu.framecount()
 if which==7 and not hit then
  if not require_fact(same_live_pair() and positive(w(p2+0x64)),"live-aim-owner")then return true end
  local cb=read(p1,4)
  if (cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(p1+6)&1==0 and w(p1+0x76)==0 then
   if w(p1+0xB4)&0x4000==0 then keys.Right=true
   else
    local dx=signed(w(p2+0x34))-signed(w(p1+0x34))
    local dy=signed(w(p2+0x36))-signed(w(p1+0x36))
    local ev=w(p2+0xBA)
    local fresh=w(p1+0x2C)&0x80==0
    if fresh and (ev==1 or ev==4 or ev==5) and dx>=96 and dx<=384 and dy>=128 and dy<=256 then
     keys.B=consumed or hp1()
    end
   end
  end
 elseif (which==8 or which==11) and menu_ready and menu_ready.mode==which and menu_ready.core>=core-1 then
  local entry=which==8 and result_mode or ending_mode
  if entry and core-entry>=120 and (core-entry)%30<4 then keys.A=true end
 end
 return true
end
]=],[=[local function select_tail(keys,which)
 if not healthy then return false end
 if done or observer.stopped()then return true end
 local core=emu.framecount()
 if which==7 and not hit then
  if not require_fact(same_live_pair() and positive(w(p2+0x64)),"live-aim-owner")then return true end
  local cb=read(p1,4)
  local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(p1+6)&1==0 and w(p1+0x76)==0
  if ready then
   local dx=signed(w(p2+0x34))-signed(w(p1+0x34))
   local dy=signed(w(p2+0x36))-signed(w(p1+0x36))
   local right=w(p1+0xB4)&0x4000~=0
   local held=w(p1+0x2C)
   if math.abs(dx)>=96 and (dx>0)~=right then
    if dx>0 and held&2==0 then keys.Right=true
    elseif dx<0 and held&8==0 then keys.Left=true end
   else
    local ev=w(p2+0xBA)
    local vx=signed(w(p2+0x34))-signed(w(p2+0x38))
    local vy=signed(w(p2+0x36))-signed(w(p2+0x3A))
    local lead_dx=dx+15*vx
    local lead_dy=dy+15*vy
    local lead_forward=right and lead_dx or -lead_dx
    if held&0x80==0 and (ev==1 or ev==4 or ev==5) and lead_forward>=128 and lead_forward<=576 and lead_dy>=-384 and lead_dy<=64 then
     keys.B=consumed or hp1()
    end
   end
  end
 elseif (which==8 or which==11) and menu_ready and menu_ready.mode==which and menu_ready.core>=core-1 then
  local entry=which==8 and result_mode or ending_mode
  if entry and core-entry>=120 and (core-entry)%30<4 then keys.A=true end
 end
 return true
end
]=])
once(' hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)',[=[
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
 hook(0x080CBCC0,0xE8BD0020,"mode13-request",function(r)
  if require_fact(mode()==13 and seen["mode13-constructor"] and w(0x03002314)==1
   and w(0x03002316)==0 and w(0x03002318)==0,"mode13-exit",r)then
   record("mode13-request","request=1,0,0",r,true)
  end
 end)
 hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)]=])
once('require_fact(result_mode,"ending-before-results",r)',
 'require_fact(result_mode and seen["mode13-request"],"ending-before-mode13-exit",r)')
assert(load(source,"@wholeplay-v88-source-results-and-input","t",_ENV))()
