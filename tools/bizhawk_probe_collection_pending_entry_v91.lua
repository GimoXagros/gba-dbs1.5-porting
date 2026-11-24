local output=assert(userdata.get("output"))
local function write(name,data,how)
 local f=assert(io.open(output.."/"..name,how or "wb"));f:write(data);f:close()
end
local function log(text) write("trace.txt",emu.framecount().." "..text.."\n","ab") end
local function iw(x) return memory.read_u16_le(x,"IWRAM") end
local function byte(x) return memory.read_u8(x,"EWRAM") end
local function dword(x) return memory.read_u32_le(x,"EWRAM") end
local function task()
 for p=0x10000,0x10000+51*0x118,0x118 do
  if memory.read_u16_le(p+16,"EWRAM")&2~=0 and dword(p+4)==0x1000 then return p end
 end
end
local function snap(name)
 for _,d in ipairs({{"EWRAM",0x40000},{"IWRAM",0x8000}})do
  write(name.."-"..d[1]..".bin",memory.read_bytes_as_binary_string(0,d[2],d[1]))
 end
 assert(savestate.save(output.."/"..name..".State",true))
end
local ok,err=pcall(function()
 assert(savestate.load(output.."/ordinary-clear-title.State",true))
 assert(emu.framecount()==123361 and iw(0x2310)==23)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 event.on_bus_write(function(addr,val,flags)
  log(string.format("config-write prior=%04X incoming=%08X pc=%08X flags=%X",iw(0x2328),val,emu.getregisters().R15,flags))
 end,0x03002328,"config-write")
 local prev,old,titleReady=-1,-1,false
 local nf=0
 for frame=0,14000 do
  local now=emu.framecount()
  local m=iw(0x2310);local flags=iw(0x2328)
  if prev~=m or old~=flags then log("mode="..m.." flags="..flags);prev=m;old=flags end
  if titleReady and flags==0 then snap("pending-cleared");return "pending-cleared" end
  local k=nil;local h=task()
  if m==23 and h then
   local cb=dword(h);local ctx=h+24
   if cb==0x08DB29DC then
    local me=dword(ctx+12)-0x02000000+24
    local a=memory.read_u16_le(me+16,"EWRAM")%256
    k=a//8==25 and "A" or ((200-a)%256<128 and "Left" or "Right")
    nf=frame
   elseif cb==0x08DB2A24 and byte(ctx+0x2F)>=71 then k="A";nf=frame
   elseif cb==0x08DB2850 and (now-105656+960)%25==0 then k="A";nf=frame end
  elseif m==3 and h then
   local cb=dword(h)
   if cb==0x08090C7C then
    if not titleReady then
     assert(flags==16);snap("postvictory");titleReady=true
    end
    k="Start"
   elseif cb==0x08DFE048 then
    local tree,choice=byte(h+28),byte(h+29)
    assert(tree<2 and choice==0,"fresh Battle Ver1.5 ordinary menu")
    k="A"
   end
  elseif m==4 or m==5 or m==6 then k="A"
  elseif m==7 then assert(titleReady);snap("new-campaign");return "retained-at-new-campaign" end
  local keys={}
  for _,name in ipairs({"Start","A","B","Select","Up","Down","Left","Right","L","R","Power"})do keys[name]=false end
  if k and frame>=nf then keys[k]=true;nf=frame+18 end
  joypad.set(keys);emu.frameadvance()
 end
 error("frame cap")
end)
if not ok then log(err) end
write("collection-done.txt",ok and err or "failure")
client.exit()
