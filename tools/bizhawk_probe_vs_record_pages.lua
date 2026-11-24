-- A cold unattended title advances its native attract counter to the five VS RECORD pages.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$") and emu.getsystemid()=="GBA")
local function log(s)
 local f=assert(io.open(out.."/trace.txt","a"));f:write(s.."\n");f:close()
end
local function dump(name,domain,address,size)
 local f=assert(io.open(out.."/"..name,"wb"))
 f:write(memory.read_bytes_as_binary_string(address,size,domain));f:close()
end
local function mode()return memory.read_u16_le(0x2310,"IWRAM")end
local function counter()return memory.read_u8(0x2330,"IWRAM")end
local expected={{0,1,2},{3,4,5},{6,7,8},{9,10,13},{14,11,12}}
local bases,portraits,stats,entered,captured,exited,lastmode={},{},{},false,{},false,-1
local wanted,lastbase
local function page()
 local task=memory.read_u32_le(0x133c,"IWRAM")
 assert(task>=0x02010000 and task<0x02015000)
 return memory.read_u16_le(task-0x02000000+0x18,"EWRAM")
end
event.on_bus_exec(function()
 if mode()==3 then
  local old=counter()
  log(string.format("title timeout frame=%d old=%d",emu.framecount(),old))
  bases[#bases+1]=old
 end
end,0x080915AC,"attract-source-counter")
event.on_bus_exec(function()
 assert(mode()==19 and counter()%4==3)
 entered=true;log("entered VS RECORD frame="..emu.framecount())
end,0x0833EB2C,"native-vs-entry")
for i,at in ipairs({0x0833EE78,0x0833EF80,0x0833F088})do
 local slot=i
 event.on_bus_exec(function()
  local start=page();local id=emu.getregisters().R2
  assert(expected[1+start//3][slot]==id,"portrait identity")
  portraits[start]=portraits[start] or {};portraits[start][slot]=id
 end,at,"portrait-"..i)
end
for i,at in ipairs({0x0833F36C,0x0833F4C0,0x0833F614})do
 local slot=i
 event.on_bus_exec(function()
  local start=page();local id=expected[1+start//3][slot];local r=emu.getregisters()
  local base=memory.read_u32_le(0x133c,"IWRAM")
  local dest=id<12 and (0x030011ae+4*id) or (base+0x18+244+4*(id-12))
  assert(r.R1==dest,"VS record identity")
  stats[start]=stats[start] or {};stats[start][slot]=r.R1
  if slot==3 and not captured[start] and lastbase~=start then
   wanted={base=start,frame=emu.framecount()+15};lastbase=start
  end
 end,at,"stat-"..i)
end
local buttons={Up=false,Down=false,Left=false,Right=false,A=false,B=false,L=false,R=false,Start=false,Select=false,Power=false}
dump("loaded-rom.bin","ROM",0,0x1000000)
client.speedmode(800)
local ok,why=pcall(function()
 for frame=0,45000 do
  local md=mode()
  if md~=lastmode then log(string.format("mode=%d frame=%d counter=%d",md,emu.framecount(),counter()));lastmode=md end
  if wanted and emu.framecount()>=wanted.frame then
   local n=wanted.base;local name="page-"..tostring(n//3+1)
   assert(md==19 and portraits[n] and #portraits[n]==3 and stats[n] and #stats[n]==3,"three paired rows")
   client.screenshot(out.."/"..name..".png")
   dump(name.."-vram.bin","VRAM",0,0x18000)
   dump(name.."-palette.bin","PALRAM",0,0x400)
   dump(name.."-oam.bin","OAM",0,0x400)
   log(string.format("captured=%s frame=%d ids=%d,%d,%d stats=%08X,%08X,%08X",name,emu.framecount(),portraits[n][1],portraits[n][2],portraits[n][3],stats[n][1],stats[n][2],stats[n][3]))
   captured[n]=true;wanted=nil
  end
  if entered and md~=19 then exited=true;break end
  joypad.set(buttons);emu.frameadvance()
 end
 assert(entered and exited and #bases>=3,"normal attract entry and exit")
 for n=0,12,3 do assert(captured[n],"uncaptured page "..n) end
end)
if not ok then log("ERROR "..tostring(why))end
local f=assert(io.open(out.."/done.txt","w"));f:write(ok and "ordinary-vs-record-complete" or "failure");f:close()
client.exit()

