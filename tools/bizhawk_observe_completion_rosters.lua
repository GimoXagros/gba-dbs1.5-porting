-- Independent saves, ordinary cold boot, and only controller input on both systems.
local out=assert(userdata.get("output"))
local wsc=emu.getsystemid()=="WSWAN"
local function write(n,b)
 local f=assert(io.open(out.."/"..n,"wb"));f:write(b);f:close()
end
local function log(s)
 local f=assert(io.open(out.."/trace.txt","a"));f:write(emu.framecount()," ",s,"\n");f:close()
end
local function b(d,a)return memory.read_u8(a,d)end
local function w(d,a)return memory.read_u16_le(a,d)end
local function snapshot(n)
 client.screenshot(out.."/"..n..".png")
 if wsc then write(n.."-ram.bin",memory.read_bytes_as_binary_string(0,0x10000,"RAM"))
 else write(n.."-vram.bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize("VRAM"),"VRAM"))end
end
local function task(cb)
 for s=0,51 do local h=0x10000+s*0x118
  if b("EWRAM",h+16)&2~=0 and memory.read_u32_le(h,"EWRAM")==cb then return h end
 end
end
local function run()
 client.speedmode(800)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize("ROM"),"ROM"))
 if wsc then write("initial-sram.bin",memory.read_bytes_as_binary_string(0,32768,"SRAM")) end
 local current,changed,entered,observed=nil,nil,nil,{}
 local count=0
 if not wsc then event.on_bus_exec(function()
  if w("IWRAM",0x2310)==4 then
   current=emu.getregisters().R1;changed=emu.framecount()
  end
 end,0x084a5c70,"actual-portrait-id") end
 for frame=0,9500 do
  local key=nil
  local mode=wsc and w("SRAM",0x4e) or w("IWRAM",0x2310)
  if wsc then
   if frame>=3900 and frame<3904 then key="P1 Start" end
   if frame>=4120 and frame<4124 then key="P1 A" end
  elseif mode==3 then
   if task(0x08090c7c) and frame>600 and frame%30<3 then key="Start" end
   local h=task(0x08dfe048)
   if h and frame%30<3 then assert(b("EWRAM",h+28)<=1 and b("EWRAM",h+29)==0);key="A" end
  end
  if mode==4 then
   if not entered then entered=frame;log("entered ordinary 1P selection")end
   if frame-entered>160 then
    if wsc then
     assert(b("SRAM",0x67)&0x30==0x30 and b("SRAM",0x73)&1==0)
     local i=w("RAM",0x3116)
     assert(i<=14,"source selector index "..i)
     local value=w("RAM",0x30ea+2*i)
     if value~=current then current=value;changed=emu.framecount()end
    else assert(w("IWRAM",0x2328)&0x3030==0x3000 and w("IWRAM",0x1132)&0x30==0x30)end
    if current and emu.framecount()>=changed+6 and not observed[current] then
     assert(current>=0 and current<=14)
     observed[current]=true;count=count+1;log("selected "..current)
     snapshot("id-"..current)
     if count==15 then return end
    end
    if (frame-entered)%25<2 then key=wsc and "P1 X3" or "Down" end
   end
  end
  local keys={}
  if key then keys[key]=true end
  joypad.set(keys)
  emu.frameadvance()
 end
 error("timeout, visible identities "..count)
end
local ok,err=pcall(run)
if not ok then log(tostring(err)) end
write("done.txt",ok and "ordinary-15-pass" or "failure")
client.exit()

