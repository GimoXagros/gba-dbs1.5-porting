local out=assert(userdata.get("output"))
local ws=emu.getsystemid()=="WSWAN"
local skip=@@SKIP@@
local limit=@@LIMIT@@
local detail=@@DETAIL@@
local known={@@SYMBOLS@@}
local cache=nil
local last=-1
local changes,choices,initial_title=0,{},nil
local current_index,current_start,pressed,released=-1,nil,nil,false
local function save(name,blob) local f=assert(io.open(out.."/"..name,"wb")); f:write(blob);f:close() end
local function log(line) local f=assert(io.open(out.."/trace.txt","a"));f:write(line.."\n");f:close() end
local function mode()
 return ws and memory.read_u16_le(0x4e,"SRAM") or memory.read_u16_le(0x2310,"IWRAM")
end
local function start_state()
 return ws and (memory.read_u8(0x6e,"SRAM")>>4) or (memory.read_u8(0x2330,"IWRAM")>>4)
end
local function callback(f)
 if ws then
  if cache then
   local at,d=cache[1],cache[2]
   if memory.read_u16_le(at+2,d)==0x558c then
    local index=known[memory.read_u16_le(at,d)]
    if index then return index end
   end
  end
  if f%4~=0 then return end
  for _,d in ipairs({"RAM","SRAM"}) do
   local raw=memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize(d),d)
   local i=1
   while true do
    local at=raw:find(string.char(0x8c,0x55),i,true)
    if not at then break end
    i=at+2
    if at>2 then
     local id=raw:byte(at-2)+256*raw:byte(at-1)
     if known[id] then cache={at-3,d};return known[id] end
    end
   end
  end
 else
  if cache then
   if memory.read_u16_le(cache+16,"EWRAM")&2~=0 then
    local index=known[memory.read_u32_le(cache,"EWRAM")]
    if index then return index end
   end
  end
  if f%4~=0 then return end
  for i=0,51 do
   local at=0x10000+i*0x118
   local index=known[memory.read_u32_le(at,"EWRAM")]
   if index and memory.read_u16_le(at+16,"EWRAM")&2~=0 then cache=at;return index end
  end
 end
end
local function capture(index,f)
 client.screenshot(string.format("%s/frame-%05d-step%02d.png",out,f,index))
end
local function play()
 client.speedmode(1000)
 save("loaded-rom.bin",memory.read_bytes_as_binary_string(0,memory.getmemorydomainsize("ROM"),"ROM"))
 for _=1,limit do
  local f=emu.framecount();local m=mode()
  if m~=last then
   log(string.format("mode frame=%d id=%d choice=%d",f,m,start_state()));last=m
   if m==3 and changes>0 then
    initial_title=initial_title or f
    capture(26,f)
    if skip or (detail and choices[23]) or (choices[19] and choices[20] and choices[21] and choices[22] and choices[23]) then
     save("finished.txt","title");return
    end
   end
  end
  local index=nil
  if m~=3 then index=callback(f) end
  if index and index~=current_index then
   changes=changes+1;current_index=index;current_start=f
   log(string.format("callback frame=%d id=%d state=%d mode=%d owner=%s",f,index,start_state(),m,ws and string.format("%s@%04X",cache[2],cache[1]) or string.format("EWRAM@%05X",cache)))
   if index>=19 and index<=23 then choices[index]=true end
  end
  if detail and current_start and current_index==23 and m==2 then
   local age=f-current_start
   for _,k in ipairs({8,10,16,20,32,40,48,60,64,80}) do
    if age==k then
     local prefix=string.format("choice3-%02d",age)
     client.screenshot(out.."/"..prefix..".png")
     if ws then
      save(prefix.."-ram.bin",memory.read_bytes_as_binary_string(0,65536,"RAM"))
     else
      save(prefix.."-oam.bin",memory.read_bytes_as_binary_string(0,1024,"OAM"))
      save(prefix.."-palette.bin",memory.read_bytes_as_binary_string(0,1024,"PALRAM"))
      save(prefix.."-vram.bin",memory.read_bytes_as_binary_string(0,98304,"VRAM"))
     end
    end
   end
  end
  if detail and skip and pressed and f-pressed<=110 and m==2 then
   local d=ws and "RAM" or "IWRAM"
   local at=ws and 0x3916 or 0x267c
   log(string.format("fade frame=%d step=%d limit=%d elapsed=%d",f,current_index,memory.read_u16_le(at,d),memory.read_u16_le(at+2,d)))
  end
  if current_start and f==current_start+8 and m~=3 then capture(current_index,f) end
  if skip and not pressed and current_index==8 and f-current_start>=15 then
   pressed=f;log("Start frame="..f.." callback="..current_index)
  end
  local held=pressed and f-pressed<4 or false
  joypad.set({[ws and "P1 Start" or "Start"]=held})
  if f%2000==0 then log("progress frame="..f.." mode="..m.." callback="..current_index) end
  emu.frameadvance()
 end
 save("finished.txt",initial_title and "bounded-after-title" or "bounded-before-title")
end
local ok,message=pcall(play)
if not ok then log("error "..tostring(message));save("finished.txt","error") end
client.exit()
