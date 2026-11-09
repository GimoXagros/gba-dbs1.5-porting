-- Reuse the frozen collision frame loop without changing global APIs or old files.
local out=assert(userdata.get("output"))
local limit=userdata.get("frames") or 120000
assert(type(limit)=="number" and limit%1==0 and limit>=1 and limit<=120000,"bounded frame budget required")
local observer=dofile("W:/tools/bizhawk_gba_shoot_entry_observer.lua")
local initial=emu.framecount()
local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local menu="title-options"
local press,press_end,next_press=nil,0,0
local battle=false
local STOP={}
local function pulse(button,frame)
 if not press and frame>=next_press then press=button;press_end=frame+4;next_press=frame+30 end
end
local function title_callback()
 for slot=0,51 do
  local h=0x02010000+slot*0x118
  if observer.read(h+0x10,2)&2~=0 and observer.read(h+4,4)==0x1000 then return observer.read(h,4)end
 end
end
local function select_input(keys)
 for _,b in ipairs(buttons)do keys[b]=false end
 local frame=emu.framecount()-initial
 if press and frame>=press_end then press=nil end
 local mode=observer.read(0x03002310,2)
 if frame<(userdata.get("start_frame") or 2970)then return end
 if mode==9 and battle then observer.fail("continue-reached",observer.state());return end
 if menu=="title-options" and mode==3 then
  local cb=title_callback()
  if cb==0x08090C7C then pulse("Start",frame)
  elseif cb==0x08090FA0 then pulse(observer.read(0x03002C5E,1)==2 and "A" or "Down",frame)end
 elseif menu=="title-options" and mode==14 then menu="difficulty";press=nil;next_press=frame+24
 elseif menu=="difficulty" and mode==14 then
  local row,diff=observer.read(0x0300473E,2),observer.read(0x0300231F,1)
  if row~=1 then pulse("Down",frame)
  elseif diff==2 then menu="leave-options";press=nil;next_press=frame+24
  else pulse("Right",frame)end
 elseif menu=="leave-options" then
  if mode==14 then pulse("B",frame)
  elseif mode==3 then menu="title-battle";press=nil;next_press=frame+24 end
 elseif menu=="title-battle" and mode==3 then
  local cb=title_callback()
  if cb==0x08090C7C then pulse("Start",frame)
  elseif cb==0x08090FA0 then pulse(observer.read(0x03002C5E,1)==0 and "A" or "Up",frame)end
 elseif mode==4 or mode==5 or mode==6 then
  menu="selection"
  if observer.read(0x0300231A,1)~=0 or observer.read(0x0300231B,1)~=0 then
   observer.fail("nondefault-selection",observer.state());return
  end
  pulse("A",frame)
 elseif mode==7 then
  if not battle then
   if observer.read(0x0300231A,1)~=0 or observer.read(0x0300231B,1)~=0 or observer.read(0x0300231F,1)~=2 then
    observer.fail("nondefault-battle",observer.state());return
   end
   battle=true;menu="battle";press=nil
  end
  if observer.live() and observer.read(0x0300231E,1)~=11 then
   keys.A=frame%97<7;keys.B=frame%29<7
   keys.Right=frame<6150 or frame%720<300
   keys.Left=frame>=6150 and frame%720>=360 and frame%720<660
  end
 elseif mode==8 and battle then pulse("A",frame)end
 if press then keys[press]=true end
end
local env=setmetatable({}, {__index=_ENV})
env.userdata={get=function(key)if key=="frames"then return limit end;return userdata.get(key)end}
env.event={on_bus_exec=function(callback,address,name)
 assert(name=="overlap-type-observer" or name=="dispatch-target-observer","unexpected frozen callback")
 -- Their older >=1A filter rejects valid Shoot1A/1B; the new observer owns these sites.
end}
env.joypad={set=function(keys)select_input(keys);joypad.set(keys)end}
env.emu=setmetatable({frameadvance=function()
 if observer.stopped()then error(STOP)end
 emu.frameadvance();observer.flush()
 if observer.stopped()then error(STOP)end
end},{__index=emu})
env.client=setmetatable({exit=function()end},{__index=client})
local ok,err=pcall(assert(loadfile("W:/tools/bizhawk_probe_gba_collision.lua","t",env)))
if not ok and err~=STOP then observer.fail("observer-error",tostring(err))end
local released={};for _,b in ipairs(buttons)do released[b]=false end;joypad.set(released)
observer.finish()
client.exit()
