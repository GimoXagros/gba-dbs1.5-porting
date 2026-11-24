-- Normal controller inputs and read-only observations on an isolated emulator.
local out=assert(userdata.get("output"))
local lang=assert(userdata.get("language"))
local cold=assert(userdata.get("cold"))==1
local fixed=assert(userdata.get("fixed"))
local boss=assert(userdata.get("boss"))
local expected=fixed+1+boss*1024
local function log(s)local f=assert(io.open(out.."/trace.txt","a"));f:write(s.."\n");f:close()end
local function dump(name,d,at,size)local f=assert(io.open(out.."/"..name,"wb"));f:write(memory.read_bytes_as_binary_string(at,size,d));f:close()end
local function w(a)return memory.read_u16_le(a,"System Bus")end
local function b(a)return memory.read_u8(a,"System Bus")end
local function u(a)return memory.read_u32_le(a,"System Bus")end
local function mode()return w(0x03002310)end
local function task(pri)
 for i=0,51 do local h=0x02010000+i*0x118
  if w(h+0x10)&2~=0 and u(h+4)==pri then return h end
 end
end
local function wait(n,key)
 for _=1,n do local p={}
  for _,k in ipairs({"Up","Down","Left","Right","L","R","A","B","Start","Select","Power"})do p[k]=k==key end
  joypad.set(p);emu.frameadvance()
 end
end
local function press(k)wait(2,k);wait(13)end
local function shot(n)
 client.screenshot(out.."/"..n..".png")
 dump(n.."-oam.bin","OAM",0,1024)
 log(n.." core="..emu.framecount().." mode="..mode().." cursor="..w(0x0300473e).." difficulty="..b(0x0300231f))
end
local function options()
 for i=1,160 do
  if mode()==14 and task(0x1500)then wait(60);return end
  local t=mode()==3 and task(0x1000)
  if t and u(t)==0x08090c7c then press("Start")
  elseif t and u(t)==0x08dfe048 and b(t+0x1c)==0 then
   if b(t+0x1d)==2 then press("A")else press("Down")end
  else wait(15)end
 end
 error("could not enter options title callback="..string.format("%08x",task(0x1000)and u(task(0x1000))or 0).." mode="..mode())
end
local function row(i)
 for n=1,10 do if w(0x0300473e)==i then return end;press("Down")end
 error("Options row unreachable "..i)
end
local function payload()return assert(task(0x1500))+0x18 end
local function return_title()
 for i=1,150 do if mode()==3 then return end;wait(5)end
 error("no return to title")
end
local function enter()
 row(5);assert(b(payload()+249)==0)
 shot("main-assist");press("A");assert(b(payload()+248)==1,"did not enter assists")
end
local function settings()return w(payload()+250)end
local function getrow(i)assert(b(payload()+252)==i,"incorrect assist row")end
client.speedmode(800)
dump("loaded-rom.bin","ROM",0,0x1000000)
local writes=0
event.on_bus_exec(function()
 local r=emu.getregisters();if r.R0==34 then writes=writes+1;log("settings-write@"..emu.framecount())end
end,0x0837db54,"owned-single-block-write")
local ok,err=pcall(function()
 wait(3000);options()
 if not cold then
  row(1)
  for i=1,3 do if b(0x0300231f)~=2 then press("Right")end end
  assert(b(0x0300231f)==2,"HARD")
  row(4)
  for i=1,lang do press("Right")end
  assert(w(payload())==lang,"language staged");press("A");return_title();options()
 end
 assert(b(0x0300112f)==0xa0+lang,"saved language")
 enter();getrow(0);shot("initial")
 if cold then
  assert(settings()==expected,"cold settings");assert(b(0x0300231f)==1,"native default difficulty on cold boot");assert(writes==0)
 else
  assert(settings()==0,"OFF defaults")
  press("Right");assert(settings()==1,"fixed zero distinct from OFF");shot("zero")
  press("Left");assert(settings()==0,"left at fixed zero restores OFF")
  press("R");assert(settings()==100,"right shoulder +100")
  press("L");assert(settings()==0,"left shoulder -100")
  press("Right");press("Down");getrow(1);press("Right");assert(settings()==0x401)
  press("B");assert(b(payload()+248)==0 and writes==0,"B cancels old state")
  enter();assert(settings()==0)
  if fixed==999 then for n=1,11 do press("R")end else assert(fixed==0);press("Right")end
  assert(settings()==fixed+1,"numeric target")
  press("Down");getrow(1);if boss==1 then press("Right")end;assert(settings()==expected)
  shot("enabled")
  press("Down");getrow(2);press("A")
  assert(b(payload()+248)==0 and writes==1,"single commit")
  press("Down");assert(b(payload()+249)==1,"seventh row");shot("return");press("A");return_title()
  wait(60)
 end
 log("PASS writes="..writes)
end)
if not ok then log("FAIL "..tostring(err));shot("failure")end
local f=assert(io.open(out.."/done.txt","w"));f:write(ok and "PASS" or "FAIL");f:close()
client.exit()
