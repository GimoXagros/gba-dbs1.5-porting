-- Extend the frozen first-entry observation through the running input task.
local out=assert(userdata.get("output"))
local file=assert(io.open(out.."/campaign-control-tail.txt","wb"))
local function read(a,n)
 local domain,offset
 if a>=0x02000000 and a+n<=0x02040000 then domain,offset="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then domain,offset="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then domain,offset="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(offset,domain) end
 if n==2 then return memory.read_u16_le(offset,domain) end
 return memory.read_u32_le(offset,domain)
end
local function emit(s)assert(file:write(s.."\n"));file:flush()end
local t={clock_calls=0,input_calls=0,streak=0}
local function running()
 local h=read(0x03004510,4)
 return h>=0x02010000 and h<0x02010000+52*0x118 and (h-0x02010000)%0x118==0
  and (read(h+0x10,2)&2)~=0 and read(h,4)==0x08374FF4
  and read(0x03002310,2)==7 and read(0x0300231E,1)==8 and read(0x0300232E,1)==0
  and read(0x03004502,2)==0 and (read(0x03004529,1)&7)==0
end
local function p1()
 local p=read(0x0300489C,4)
 if p<0x02010018 or p>=0x02010018+52*0x118 or (p-0x02010018)%0x118~=0 then return end
 if (read(p-8,2)&2)~=0 and read(p+0x14,4)==p and read(p+0x10,1)==0
  and (read(p+4,2)&15)==0 and read(p+0x11,1)==0 then return p end
end
local function hook(at,word,fn)
 assert(read(at,4)==word,"running-tail hook instruction")
 event.on_bus_exec(function()if t.setup then fn(emu.getregisters())end end,at,"campaign-running-"..string.format("%X",at))
end
hook(0x08377B88,0xE28DD010,function(r)
 assert(running(),"READY transition installed running task")
 t.transition=t.transition or emu.framecount()
 emit(string.format("event=ready-transition core=%d task=%08X callback=%08X clock=%d",emu.framecount(),read(0x03004510,4),0x08374FF4,read(0x03004500,2)))
end)
hook(0x0837501C,0xE59F8150,function(r)
 assert(running() and t.transition and r.R8==0x03004500,"actual running clock owner")
 local value=read(0x03004500,2)
 assert(value==(r.R9&0xFFFF) and value>0 and value<7200,"positive decremented round clock")
 t.clock_calls=t.clock_calls+1;t.clock=value;t.clock_frame=emu.framecount()
 t.first_clock=t.first_clock or t.clock_frame
 if t.clock_calls<=16 then emit(string.format("event=clock-store core=%d clock=%d task=%08X",t.clock_frame,value,read(0x03004510,4)))end
end)
hook(0x0837513C,0xE1C412BE,function(r)
 if not t.first_clock or r.R4~=p1() then return end
 assert(running() and read(r.R4+0x2C,2)==(r.R0&0xFFFF),"actual P1 input store")
 t.input_calls=t.input_calls+1
 if (r.R0&0x40)~=0 then
  assert(t.press and emu.framecount()>=t.press and emu.framecount()<=t.press+1,"A came from the bounded ordinary pulse")
  t.accepted=t.accepted or emu.framecount()
  emit(string.format("event=A-accepted core=%d p1=%08X held=%04X edge=%04X callback=%08X clock=%d",emu.framecount(),r.R4,r.R0&0xFFFF,r.R1&0xFFFF,read(r.R4,4),read(0x03004500,2)))
 end
end)
local function input(keys)
 if not t.first_clock then return end
 t.press=t.press or emu.framecount()
 keys.A=emu.framecount()==t.press
 if keys.A then emit("event=A-press core="..t.press)end
end
local function observe(capture)
 if not t.accepted then return end
 local now=emu.framecount()
 if not running() or not p1() or t.clock_frame~=now-1 or (t.previous_clock and t.clock>=t.previous_clock)then
  t.streak=0;t.streak_start=nil;t.previous_clock=nil;return
 end
 t.streak_start=t.streak_start or now;t.previous_clock=t.clock;t.streak=t.streak+1
 if not t.captured then t.captured=true;capture("campaign-running-input");emit("event=running-input-boundary core="..now)end
 if t.streak==121 then
  capture("campaign-running-stable")
  emit(string.format("event=running-stable core=%d streak_start=%d clock=%d input_calls=%d",now,t.streak_start,t.clock,t.input_calls))
  return "campaign-running-input-and-clock-tail-observed"
 end
end
local function finish()
 emit(string.format("summary core=%d transition=%s first_clock=%s press=%s accepted=%s clock=%s clock_calls=%d input_calls=%d stable=%d guest_writes=none",
  emu.framecount(),tostring(t.transition),tostring(t.first_clock),tostring(t.press),tostring(t.accepted),tostring(t.clock),t.clock_calls,t.input_calls,t.streak));file:close()
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true);assert(a and not s:find(before,b+1,true),"unique running-tail extension")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local f=assert(io.open("W:/tools/bizhawk_probe_campaign_entry.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,'return "campaign-first-stage8-cpu13-observed"','tail_setup()')
source=replace(source,'campaign_observe=observe','campaign_observe=function(capture) observe(capture);return tail_observe(capture)end')
source=replace(source,'file:close()\nend},{__index=_ENV})','file:close();tail_finish()\nend},{__index=_ENV})')
source=replace(source,'local env=setmetatable({campaign_observe=',
 'source=replace(source,\' joypad.set(keys)\',\' tail_input(keys)\\n joypad.set(keys)\')\nlocal env=setmetatable({campaign_observe=')
emit("start readonly=true ordinary_A_pulse=one_frame after_actual_clock=true required_running_boundaries=121")
local env=setmetatable({tail_setup=function()t.setup=true end,tail_observe=observe,tail_input=input,tail_finish=finish},{__index=_ENV})
assert(load(source,"@campaign-running-tail-extension","t",env))()
