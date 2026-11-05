-- Ordinary-input Options commit -> title -> 1P battle -> natural result.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local language=assert(userdata.get("language"))
assert(language%1==0 and language>=0 and language<=3)
local limit=userdata.get("frames") or 24000
local start=userdata.get("start_frame") or 2970
local initial=emu.framecount()
local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local result_p0=({0x080B8210,0x08651AE0,0x086DA640,0x087DFC20})[language+1]
local title_p0=({0x0808FD08,0x0863A800,0x0863D000,0x0863E000})[language+1]
local stage="boot"
local press,press_end,next_press=nil,0,0
local mode_previous,signature_previous
local writer_calls,init_calls,draw_calls=0,0,0
local objects,drawn={},{}
local commit_seen,title_seen,battle_seen,label_seen,last_seen=false,false,false,false,false
local result_frame,first_visible_frame
local result_120,result_300=false,false
local outcome
local function log(s)
 local f=assert(io.open(out.."/trace.txt","a"));f:write(s.."\n");f:close()
end
local function u16(a) return memory.read_u16_le(a,"IWRAM") end
local function read(a,width)
 local domain,offset
 if a>=0x02000000 and a+width<=0x02040000 then domain,offset="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+width<=0x03008000 then domain,offset="IWRAM",a-0x03000000
 else return -1 end
 if width==2 then return memory.read_u16_le(offset,domain) end
 return memory.read_u32_le(offset,domain)
end
local function task(priority)
 local found
 for slot=0,51 do
  local at=0x10000+slot*0x118
  if memory.read_u16_le(at+0x10,"EWRAM")&2~=0 and memory.read_u32_le(at+4,"EWRAM")==priority then
   assert(not found,"duplicate task priority")
   found=0x02000000+at
  end
 end
 return found
end
local function state(next_stage,frame)
 log("stage="..next_stage.." relative="..frame.." core="..emu.framecount())
 stage=next_stage;press=nil;next_press=frame+24
end
local function pulse(button,frame)
 if not press and frame>=next_press then press=button;press_end=frame+4;next_press=frame+30 end
end
local function dump(name,domain,address,size)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(memory.read_bytes_as_binary_string(address,size,domain));f:close()
end
local function presentation(address)
 return string.format("object=%08X P1=%08X P0=%08X P2=%08X event=%d layout=%d flags=%04X x=%04X y=%04X",address,
  read(address+0x44,4),read(address+0x48,4),read(address+0x4C,4),read(address+0x0E,2),read(address+0x18,2),
  read(address+8,2),read(address,2),read(address+2,2))
end
local function capture(name)
 log(string.format("capture=%s core=%d mode=%d tag=%02X result_age=%d timing=frame-boundary",name,emu.framecount(),u16(0x2310),memory.read_u8(0x112F,"IWRAM"),result_frame and emu.framecount()-result_frame or -1))
 local sorted={};for address in pairs(objects) do sorted[#sorted+1]=address end;table.sort(sorted)
 for _,address in ipairs(sorted) do log(presentation(address)) end
 for _,v in ipairs({{"iwram","IWRAM",0,0x8000},{"ewram","EWRAM",0,0x40000},{"vram","VRAM",0,0x18000},{"palette","PALRAM",0,0x400},{"oam","OAM",0,0x400},{"display","System Bus",0x04000000,0x60}}) do
  dump(name.."-"..v[1]..".bin",v[2],v[3],v[4])
 end
 client.screenshot(out.."/"..name..".png")
end
local function checksum_ok()
 local sum=0
 for i=0,0xBF do sum=sum+memory.read_u8(0x1120+i,"IWRAM") end
 return sum==memory.read_u32_le(0x11E0,"IWRAM")
end
local function fail(reason)
 if not outcome then outcome="failure:"..reason;capture("failure") end
end
assert(emu.getsystemid()=="GBA")
for index,pointer in ipairs({0x080B8210,0x08651AE0,0x086DA640,0x087DFC20}) do
 assert(memory.read_u32_le(0x652FC4+(index-1)*4,"ROM")==pointer,"result component selector table")
end
event.on_bus_exec(function()
 if stage=="options-commit" and u16(0x2310)==14 then
  writer_calls=writer_calls+1
  log(string.format("native-writer-entry core=%d tag=%02X",emu.framecount(),memory.read_u8(0x112F,"IWRAM")))
 end
end,0x0801FC5C,"result-language-native-commit")
for _,address in ipairs({0x0808998C,0x080899F0,0x08089C00,0x08089C64,0x08089DA0,0x08089F38}) do
 event.on_bus_exec(function()
  if u16(0x2310)~=8 then return end
  local r=emu.getregisters();init_calls=init_calls+1
  objects[r.R5]=true
  log(string.format("initialized core=%d callback=%08X exposed_PC=%08X %s",emu.framecount(),address,r.R15,presentation(r.R5)))
  if read(r.R5+0x48,4)~=result_p0 then outcome="failure:wrong-result-resource" end
 end,address,"result-language-init-"..string.format("%X",address))
end
for _,address in ipairs({0x0808B0AC,0x0808B170,0x0808B19C}) do
 event.on_bus_exec(function()
  if u16(0x2310)~=8 then return end
  local r=emu.getregisters();draw_calls=draw_calls+1
  local p0,event=read(r.R5+0x48,4),read(r.R5+0x0E,2)
  local key=string.format("%X:%X:%X",address,r.R5,event)
  if not drawn[key] then
   drawn[key]=true
   log(string.format("text-draw core=%d callback=%08X exposed_PC=%08X %s",emu.framecount(),address,r.R15,presentation(r.R5)))
  end
  if p0==result_p0 and (event==0 or event==1 or event==3) then
   label_seen=true
   if event==3 then last_seen=true end
  end
 end,address,"result-language-draw-"..string.format("%X",address))
end
log(string.format("language=%d expected_tag=%02X result_P0=%08X initial_core=%d guest_writes=none input=joypad-only",language,0xA0+language,result_p0,initial))
dump("loaded-rom.bin","ROM",0,0x800000)
client.speedmode(800)
for frame=0,limit-1 do
 if press and frame>=press_end then press=nil end
 local mode=u16(0x2310)
 if mode~=mode_previous then
  log("mode="..mode.." relative="..frame.." core="..emu.framecount());mode_previous=mode
 end
 if stage=="boot" and frame>=start+180 then state("title-options",frame) end
 if stage=="title-options" then
  if mode==14 then state("options-row",frame)
  elseif mode==3 then
   local t=task(0x1000);local callback=t and read(t,4)
   if callback==0x08090C7C then pulse("Start",frame)
   elseif callback==0x08090FA0 then
    local row=memory.read_u8(0x2C5E,"IWRAM")
    if row==2 then pulse("A",frame) else pulse("Down",frame) end
   end
  end
 elseif stage=="options-row" or stage=="options-language" or stage=="options-commit" then
  if mode==14 then
   local t=task(0x1500)
   if t then
    local pending,entry,err=read(t+0x18,2),read(t+0x1A,2),read(t+0x1C,2)
    local row=u16(0x473E)
    if pending>3 or entry>3 or row>5 then fail("invalid-options-state")
    elseif err~=0 then fail("native-commit-error")
    elseif stage=="options-row" then
     if row==4 then state("options-language",frame) else pulse("Down",frame) end
    elseif stage=="options-language" then
     if pending==language then
      log(string.format("options-staged pending=%d entry=%d error=%d row=%d",pending,entry,err,row))
      capture("options-staged");state("options-commit",frame)
     elseif pending<language then pulse("Right",frame) else pulse("Left",frame) end
    else pulse("A",frame) end
   end
  elseif stage=="options-commit" and mode==3 then
   if memory.read_u8(0x112F,"IWRAM")~=0xA0+language or writer_calls==0 or not checksum_ok() then fail("commit-not-proved")
   else commit_seen=true;capture("options-committed");state("title-battle",frame) end
  end
 elseif stage=="title-battle" and mode==3 then
  local t=task(0x1000);local callback=t and read(t,4)
  if callback==0x08090C7C or callback==0x08090FA0 then
   if not title_seen then
    local correct=memory.read_u8(0x112F,"IWRAM")==0xA0+language
    for index=0,4 do correct=correct and memory.read_u32_le(0x2A78+index*0x50+0x48,"IWRAM")==title_p0 end
    if not correct then fail("wrong-title-language")
    else title_seen=true;capture("title-committed") end
   end
   if callback==0x08090C7C then pulse("Start",frame)
   elseif memory.read_u8(0x2C5E,"IWRAM")==0 then pulse("A",frame) else pulse("Up",frame) end
  end
 elseif stage=="title-battle" and (mode==4 or mode==5 or mode==6) then
  state("battle-select",frame)
 elseif stage=="battle-select" then
  if mode==4 or mode==5 or mode==6 then pulse("A",frame)
  elseif mode==7 then battle_seen=true;capture("battle-enter");state("battle",frame) end
 elseif stage=="battle" then
  if mode==8 then result_frame=emu.framecount();capture("result-enter");state("result",frame)
  elseif mode==9 then fail("continue-before-result") end
 elseif stage=="result" then
  local age=emu.framecount()-result_frame
  if label_seen and not first_visible_frame then first_visible_frame=emu.framecount();capture("result-first-label") end
  if mode==8 then
   if age>=120 and not result_120 then result_120=true;capture("result-plus120") end
   if age>=300 and not result_300 then result_300=true;capture("result-plus300") end
   if result_300 and label_seen then outcome="result-label-observed" end
  else
   capture("result-exited");outcome=label_seen and "result-label-observed-early-exit" or "failure:result-exited-before-label"
  end
 end
 if frame%600==0 then log(string.format("progress relative=%d stage=%s mode=%d tag=%02X init=%d draw=%d",frame,stage,mode,memory.read_u8(0x112F,"IWRAM"),init_calls,draw_calls)) end
 if outcome then break end
 local keys={};for _,button in ipairs(buttons) do keys[button]=false end
 if stage=="boot" and frame>=start and frame<start+15 then keys.Start=true end
 if press then keys[press]=true end
 joypad.set(keys)
 local active={};for _,button in ipairs(buttons) do if keys[button] then active[#active+1]=button end end
 local signature=table.concat(active,",")
 if signature~=signature_previous then log("input relative="..frame.." keys="..signature);signature_previous=signature end
 emu.frameadvance()
end
local released={};for _,button in ipairs(buttons) do released[button]=false end;joypad.set(released)
if not outcome then outcome="bounded-no-result";capture("bounded-end") end
log(string.format("summary outcome=%s language=%d committed=%s title=%s battle=%s result=%s label=%s last_chance=%s plus120=%s plus300=%s writer_calls=%d init_calls=%d draw_calls=%d",outcome,language,tostring(commit_seen),tostring(title_seen),tostring(battle_seen),tostring(result_frame~=nil),tostring(label_seen),tostring(last_seen),tostring(result_120),tostring(result_300),writer_calls,init_calls,draw_calls))
-- The host must wait on this marker, which is written after every capture/log.
local f=assert(io.open(out.."/result-done.txt","w"));f:write(outcome);f:close()
client.exit()
