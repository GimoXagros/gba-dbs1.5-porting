-- Observe only existing end-of-stage state and source task owners, with normal input.
local out=assert(userdata.get("output"))
local function u(a,d)return memory.read_u16_le(a,d)end
local function put(n,b)local f=assert(io.open(out.."/"..n,"wb"));f:write(b);f:close()end
local function log(v)local f=assert(io.open(out.."/trace.txt","a"));f:write(emu.framecount().." "..v.."\n");f:close()end
local function cap(n)
 client.screenshot(out.."/"..n..".png")
 put(n.."-ram.bin",memory.read_bytes_as_binary_string(0,0x10000,"RAM"))
 put(n.."-sram.bin",memory.read_bytes_as_binary_string(0,0x8000,"SRAM"))
end
local ok,err=pcall(function()
 client.speedmode(800);assert(savestate.load(out.."/source.State",true))
 local lastmode,lasttasks,first,vis=nil,nil,nil,{}
 for f=0,12000 do
  local mode,flags=u(0x4e,"SRAM"),u(0x68,"SRAM")
  local tasks={};local relevant=false
  for h=0x14,0x3644,0x110 do
   if u(0xc000+h+10,"RAM")&2~=0 then
    local off,seg=u(0xc000+h,"RAM"),u(0xc000+h+2,"RAM")
    if seg==0x73d3 or seg==0x79f5 then
     local tag=string.format("%04x-%04x",seg,off);tasks[#tasks+1]=tag
     if seg==0x73d3 then relevant=true end
     if not vis[tag]then vis[tag]=emu.framecount();cap("task-"..tag)end
    end
   end
  end
  local names=table.concat(tasks,",")
  if mode~=lastmode or names~=lasttasks then
   log(string.format("mode=%d flags=%04x stage=%d score=%d rank=%04x tasks=%s",mode,flags,memory.read_u8(0x5c,"SRAM"),u(0x74,"SRAM"),u(0x71,"SRAM"),names));lastmode=mode;lasttasks=names
  end
  if relevant then
   if not first then first=emu.framecount()end
   local relative=emu.framecount()-first
   if relative%30==0 and relative<=1500 then cap(string.format("presentation-%04d",relative))end
  end
  if mode==3 and f>300 then cap("returned");break end
  joypad.set({["P1 A"]=f%40<3,["P1 B"]=false,["P1 Start"]=false});emu.frameadvance()
 end
end)
put("done.txt",ok and "complete" or tostring(err));client.exit()
