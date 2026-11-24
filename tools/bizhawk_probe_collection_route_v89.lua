-- Resume the measured stage 11 route, then follow the normal Collection menu.
local out=assert(userdata.get("output"))
local rom="9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5"
assert(userdata.get("probe_sha256")==rom)
local function file(path)
 local f=assert(io.open(path,"rb"));local data=f:read("*a");f:close();return data
end
local function log(text)
 local f=assert(io.open(out.."/collection-trace.txt","a"));f:write(emu.framecount()," ",text,"\n");f:close()
end
local function mode()return memory.read_u16_le(0x2310,"IWRAM")end
local function payload()
 for slot=0,51 do
  local h=0x10000+slot*0x118
  if memory.read_u16_le(h+16,"EWRAM")&2~=0 and memory.read_u32_le(h+4,"EWRAM")==0x1000 then return h end
 end
end
local function snap(name)
 client.screenshot(out.."/"..name..".png")
 for _,r in ipairs({{"IWRAM",0x8000},{"EWRAM",0x40000},{"VRAM",0x18000},{"OAM",0x400},{"PALRAM",0x400}})do
  local f=assert(io.open(out.."/"..name.."-"..r[1]..".bin","wb"));f:write(memory.read_bytes_as_binary_string(0,r[2],r[1]));f:close()
 end
end
local ok,why=pcall(function()
 local observed={}
 local watch={[0x08D8D258]="eligible-clear-writer",[148576748]="scene-create",[148580720]="scene-playing",[148580612]="failure-exit",[148580684]="success-exit"}
 for pc,name in pairs(watch)do event.on_bus_exec(function()
  if not observed[name]then observed[name]=emu.framecount();log(name.." mode="..mode())end
 end,pc,name)end
 local original=file("W:/tools/bizhawk_probe_gba_shoot_checkpoint_results_v88r4.lua")
 local count
 original,count=original:gsub("E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C",rom)
 assert(count==1)
 local first=setmetatable({client=setmetatable({exit=function()end},{__index=client})},{__index=_ENV})
 assert(load(original,"@reviewed-r4-relative-to-installed-rom","t",first))()
 assert(file(out.."/shoot-checkpoint-aim-done.txt"):match("^shoot%-checkpoint%-aim%-terminal%-results%-title"))
 assert(observed["eligible-clear-writer"],"missing eligible clear save producer")
 assert(savestate.save(out.."/ordinary-clear-title.State",true))
 local previous,started,returned,entry,sub,playing=false,false,false,false,false,false
 local nextInput=60
 for frame=0,20000 do
  local m=mode();local button=nil
  if m~=previous then log("mode="..m);previous=m end
  if m==3 then
   local h=payload()
   if h then
    local cb=memory.read_u32_le(h,"EWRAM")
    if cb==0x08090C7C then
     if returned then assert(observed["scene-playing"] and (observed["failure-exit"] or observed["success-exit"]));snap("collection-return");return end
     if not started then snap("clear-title");started=true end
     button="Start"
    elseif cb==0x08DFE048 then
     local tree=memory.read_u8(h+0x1C,"EWRAM");local choice=memory.read_u8(h+0x1D,"EWRAM")
     assert(memory.read_u32_le(h+0x34,"EWRAM")==1,"title read of ordinary EEPROM eligibility")
     if tree==0 then button=choice==4 and "A" or "Down"
     elseif tree==2 then
      assert(memory.read_u16_le(0x2AC8+14,"IWRAM")==9,"unlocked Shoot row")
      if not sub then snap("collection-eligible");sub=true end
      button=choice==1 and "A" or "Down"
     else error("unexpected title subtree "..tree)end
    end
   end
  elseif m==4 then assert(sub);button="A"
  elseif m==23 then
   assert(sub,"entered from unlocked submenu")
   if observed["scene-create"] and not entry then snap("shoot-entry");entry=true end
   if observed["scene-playing"] and not playing then snap("shoot-playing");playing=true end
   if frame%40==0 then button="A"end
   if frame%300==0 then
    local active={}
    for i=0,51 do local h=0x10000+i*0x118;if memory.read_u16_le(h+16,"EWRAM")&2~=0 then active[#active+1]=string.format("%08X",memory.read_u32_le(h,"EWRAM"))end end
    log("callbacks="..table.concat(active,","))
   end
  elseif m==20 and entry then
   if not returned then snap("shoot-exit");returned=true end
  else error("unexpected mode "..m)end
  local keys={}
  for _,k in ipairs({"A","B","Start","Select","Up","Down","Left","Right","L","R","Power"})do keys[k]=false end
  if button and frame>=nextInput then keys[button]=true;nextInput=frame+18 end
  joypad.set(keys);emu.frameadvance()
 end
 error("bounded Collection route")
end)
if not ok then log(tostring(why));snap("collection-failure")end
local done=assert(io.open(out.."/collection-done.txt","w"));done:write(ok and "collection-shoot-returned" or "failure");done:close()
client.exit()
