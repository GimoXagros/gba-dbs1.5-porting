-- Fresh boot and ordinary Options input; no guest writes or supplied saves.
local out=assert(userdata.get("output"))
local language=assert(userdata.get("language"))
assert(out:match("^W:/build/[%w%-%_/]+$") and language%1==0 and language>=0 and language<=3)
assert(emu.getsystemid()=="GBA" and memory.getmemorydomainsize("ROM")==0x1000000)
local p0=({149530656,149715360,149326912,148875904})[language+1]
local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 else error("read outside owned RAM") end
 if n==1 then return memory.read_u8(o,d) elseif n==2 then return memory.read_u16_le(o,d) end
 return memory.read_u32_le(o,d)
end
local function log(s)local f=assert(io.open(out.."/trace.txt","a"));f:write(s.."\n");f:close()end
local function dump(n,d,a,s)local f=assert(io.open(out.."/"..n,"wb"));f:write(memory.read_bytes_as_binary_string(a,s,d));f:close()end
local function task(priority)
 local found
 for slot=0,51 do local h=0x02010000+slot*0x118
  if read(h+0x10,2)&2~=0 and read(h+4,4)==priority then assert(not found,"duplicate priority");found=h end
 end
 return found
end
local function capture(name)
 log(string.format("capture=%s frame=%d mode=%d tag=%02X",name,emu.framecount(),read(0x03002310,2),read(0x0300112F,1)))
 for _,r in ipairs({{"iwram","IWRAM",0,0x8000},{"ewram","EWRAM",0,0x40000},{"vram","VRAM",0,0x18000},{"palette","PALRAM",0,0x400},{"oam","OAM",0,0x400},{"display","System Bus",0x04000000,0x60}})do dump(name.."-"..r[1]..".bin",r[2],r[3],r[4])end
 client.screenshot(out.."/"..name..".png")
end
local stage,press,press_end,next_press="options",nil,0,3000
local writers,headers,stage_frame,visible=0,0,0,0
local function state(s,f)stage=s;stage_frame=f;press=nil;next_press=f+24;log("stage="..s.." frame="..emu.framecount())end
local function pulse(b,f)if not press and f>=next_press then press=b;press_end=f+4;next_press=f+30 end end
local function checksum()
 local sum=0;for i=0,0xBF do sum=sum+read(0x03001120+i,1)end
 return sum==read(0x030011E0,4)
end
event.on_bus_exec(function()if stage=="commit" and read(0x03002310,2)==14 then writers=writers+1 end end,0x0801FC5C,"title-language-native-writer")

local function hardware_objects()
 local count=0
 for i=0,127 do
  if memory.read_u16_le(i*8,"OAM")&0x0300~=0x0200 then count=count+1 end
 end
 return count
end
dump("loaded-rom.bin","ROM",0,0x1000000)
log("guest_writes=none supplied_save=false joypad_only=true")
client.speedmode(800)
local initial=emu.framecount()
local ok,err=pcall(function()
 for f=0,8999 do
  if press and f>=press_end then press=nil end
  local mode=read(0x03002310,2);local t=mode==3 and task(0x1000);local cb=t and read(t,4)
  if f>=3000 then
   if stage=="options" then
    if mode==14 then state("row",f)
    elseif cb==0x08090C7C then pulse("Start",f)
    elseif cb==0x08DFE048 then assert(read(t+0x1C,1)==0);pulse(read(t+0x1D,1)==2 and "A" or "Down",f)end
   elseif stage=="row" or stage=="language" or stage=="commit" then
    if mode==14 then
     local o=task(0x1500)
     if o then
      local pending,row=read(o+0x18,2),read(0x0300473E,2)
      assert(pending<=3 and row<=5 and read(o+0x1C,2)==0,"Options bounds or save error")
      if stage=="row" then if row==4 then state("language",f)else pulse("Down",f)end
      elseif stage=="language" then if pending==language then capture("options-staged");state("commit",f)else pulse(pending<language and "Right" or "Left",f)end
      else pulse("A",f)end
     end
    elseif stage=="commit" and mode==3 then
     assert(read(0x0300112F,1)==0xA0+language and writers>0 and checksum(),"normal commit provenance")
     state("prompt",f)
    end
   elseif stage=="prompt" then
    visible=(cb==0x08090C7C and f-stage_frame>40 and hardware_objects()>0) and visible+1 or 0
    if visible>=4 then
     for i=0,4 do assert(read(0x03002A78+i*0x50+0x48,4)==p0,"installed title P0")end
     capture("prompt");state("root",f)
    end
   elseif stage=="root" then
    if cb==0x08090C7C then pulse("Start",f)
    elseif cb==0x08DFE048 and read(t+0x1C,1)==0 then
     assert(read(t+0x1E,1)==5,"five root rows");state("root-settled",f)
    end
   elseif stage=="root-settled" and f-stage_frame>=10 then
    assert(hardware_objects()==110,"visible root slots");capture("root");state("battle",f)
   elseif stage=="battle" then
    if mode==4 then state("portrait",f)
    elseif cb==0x08DFE048 then
     local tree,choice=read(t+0x1C,1),read(t+0x1D,1)
     assert(tree==0 or tree==1,"ordinary battle subtree");pulse(choice==0 and "A" or "Up",f)
    end
   elseif stage=="portrait" and f-stage_frame>=150 then
    assert(mode==4 and read(0x0300112F,1)==0xA0+language,"selected portrait scene")
    capture("portrait");state("move-down",f)
   elseif stage=="move-down" and f-stage_frame>=24 then
    pulse("Down",f);stage="moved";stage_frame=f
   elseif stage=="moved" and f-stage_frame>=90 then
    assert(mode==4);capture("portrait-next");stage="complete";break
   end
  end
  local keys={};for _,b in ipairs(buttons)do keys[b]=false end;if press then keys[press]=true end
  joypad.set(keys);emu.frameadvance()
  if f%600==0 then log("progress="..f.." stage="..stage.." mode="..mode)end
 end
 assert(stage=="complete","bounded incomplete "..stage)
end)
local keys={};for _,b in ipairs(buttons)do keys[b]=false end;joypad.set(keys)
if not ok then log("error="..tostring(err));capture("failure")end
local outcome=ok and "ordinary-language-title-portrait-complete" or "failure"
log("outcome="..outcome.." writers="..writers)
local f=assert(io.open(out.."/done.txt","w"));f:write(outcome);f:close();client.exit()
