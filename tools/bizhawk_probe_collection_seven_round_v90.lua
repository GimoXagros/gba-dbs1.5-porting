-- Resume the measured stage 11 route, then follow the normal Collection menu.
local out=assert(userdata.get("output"))
local rom="8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869"
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
 local watch={[148583676]="completion-save",[148580648]="final-round-cleared",[0x08D8D258]="eligible-clear-writer",[148576748]="scene-create",[148580720]="scene-playing",[148580612]="failure-exit",[148580684]="success-exit"}
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
 local plan={[0]={{109,8,75,0},{515,216,75,0}},[1]={{1257,8,75,0},{1704,40,75,0}},[2]={{2432,0,77,0},{3061,8,57,0},{3713,96,71,289},{4233,48,45,289},{4706,56,67,289}},[3]={{5452,0,77,289},{6088,16,57,289},{6775,0,71,289},{7437,72,45,289},{7846,248,67,289}},[4]={{8552,240,77,289},{9412,64,57,289},{10109,32,71,289},{10590,64,45,289},{11087,32,67,289},{11556,40,37,289},{12018,80,51,289}},[5]={{12802,0,77,289},{13830,48,57,622},{14742,160,71,622},{15451,72,45,622},{15931,0,67,622},{16392,8,51,960},{16854,24,51,960},{17320,248,63,960},{17785,240,77,960}},[6]={{18506,0,77,960},{19126,24,57,960},{19572,200,71,960}}}
 local currentRound,turn,activeShot=-1,0,nil
 local shifted=0
 local englishCaptured=false
 local nextInput=60
 for frame=0,40000 do
  local m=mode();local button=nil
  if m~=previous then log("mode="..m);previous=m end
  if m==3 then
   local h=payload()
   if h then
    local cb=memory.read_u32_le(h,"EWRAM")
    if cb==0x08090C7C then
     if returned then assert(observed["completion-save"] and observed["success-exit"] and englishCaptured and currentRound==6);snap("collection-return");return end
     if not started then snap("clear-title");started=true end
     button="Start"
    elseif cb==0x08DFE048 then
     local tree=memory.read_u8(h+0x1C,"EWRAM");local choice=memory.read_u8(h+0x1D,"EWRAM")
     assert(memory.read_u32_le(h+0x34,"EWRAM")==1,"title read of ordinary EEPROM eligibility")
     if tree==0 then button=choice==4 and "A" or "Down"
     elseif tree==2 then
      assert(memory.read_u16_le(0x2AC8+14,"IWRAM")==9,"unlocked Shoot row")
      if not sub then snap("collection-eligible");sub=true end
      if choice==1 and not englishCaptured and frame+2<nextInput then snap("english-shoot-selected");englishCaptured=true end
      button=choice==1 and "A" or "Down"
     else error("unexpected title subtree "..tree)end
    end
   end
  elseif m==4 then assert(sub);button="A"
  elseif m==23 then
   assert(sub,"entered from unlocked submenu")
   if observed["scene-create"] and not entry then snap("shoot-entry");entry=true end
   if observed["scene-playing"] and not playing then snap("shoot-playing");playing=true end
   local h=payload()
   if h and observed["scene-playing"] then
    local ctx=h+24
    local cb=memory.read_u32_le(h,"EWRAM")
    local round=memory.read_u8(ctx+0x2A,"EWRAM")
    if round~=currentRound and round<7 then
     assert(round==currentRound+1);currentRound=round;activeShot=nil;turn=0
     log("round="..round)
    end
    local elapsed=emu.framecount()-observed["scene-playing"]
    if cb==0x08DB29DC then
     if not activeShot then
      local shot=assert(plan[round][turn+1],"unexpected human turn")
      assert(elapsed<=shot[1]+1 and elapsed>=shot[1]-2,"decision timing: "..elapsed.." expected="..shot[1])
      if elapsed>=shot[1] then
       turn=turn+1;activeShot=shot;shifted=shot[4];log("round="..round.." turn="..turn.." aim="..shot[2].." power="..shot[3])
      end
     end
     if activeShot then
      local me=memory.read_u32_le(ctx+12,"EWRAM")-0x02000000+24
      local angle=memory.read_u16_le(me+16,"EWRAM")%256
      local target=activeShot[2]
      if angle//8==target//8 then button="A" elseif (target-angle)%256<128 then button="Left" else button="Right" end
      nextInput=frame
     end
    elseif cb==0x08DB2A24 then
     assert(activeShot)
     if memory.read_u8(ctx+0x2F,"EWRAM")>=activeShot[3] then button="A";nextInput=frame;activeShot=nil end
    elseif cb==0x08DB2850 then
     local age=round<=1 and (elapsed+917) or (elapsed-1867+shifted)
     if age%25==0 then button="A";nextInput=frame end
    elseif cb==0x08DB2904 then error("unexpected round defeat") end
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
local done=assert(io.open(out.."/collection-done.txt","w"));done:write(ok and "collection-seven-round-win-returned" or "failure");done:close()
client.exit()
