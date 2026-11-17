-- Ordinary ID13 menu selection and one jump; stop at the eligible fall caller.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local file=assert(io.open(out.."/id13-fall-entry.txt","wb"))
local function rd(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d)end
 if n==2 then return memory.read_u16_le(o,d)end
 return memory.read_u32_le(o,d)
end
local function actor(p)
 return p>=0x02010018 and p<=0x02010018+51*0x118 and (p-0x02010018)%0x118==0 and (rd(p-8,2)&2)~=0
end
local function emit(s)assert(file:write(s.."\n"));file:flush()end
local phase,until_frame,fall_core="waiting",nil,nil
local function live()
 local p,q=rd(0x0300489C,4),rd(0x030048A0,4)
 if not(actor(p)and actor(q)and rd(p+0x10,1)==0 and rd(p+0x11,1)==13 and
  rd(p+0x14,4)==p and rd(p+0x18,4)==q and rd(q+0x18,4)==p and (rd(p+4,2)&0xF)==0)then return nil end
 return p
end
for _,at in ipairs({0x08357054,0x0835732C,0x083578D4})do
 assert(rd(at,4)==0xE1D482BC,"reviewed original common-fall input load")
 event.on_bus_exec(function()
  local r=emu.getregisters();local p=live()
  if fall_core or phase~="released" or not p or r.R4~=p or r.R5~=p+0xAC or rd(0x03002310,2)~=7 then return end
  local vy=rd(p+0x44,2)
  if not(vy>0 and vy<0x8000 and (rd(p+0xA6,2)&1)==0 and (rd(p+8,2)&0x4100)==0)then return end
  fall_core=emu.framecount()
  emit(string.format("event=eligible-fall core=%d site=%08X pc=%08X actor=%08X presentation=%08X phase=%s cb=%08X f4=%04X f6=%04X f8=%04X vy=%04X ay=%04X A6=%04X A8=%04X AA=%04X held=%04X",fall_core,at,r.R15,p,r.R5,phase,rd(p,4),rd(p+4,2),rd(p+6,2),rd(p+8,2),vy,rd(p+0x48,2),rd(p+0xA6,2),rd(p+0xA8,2),rd(p+0xAA,2),rd(p+0x2C,2)))
  for _,v in ipairs({{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000}})do
   local f=assert(io.open(out.."/id13-fall-before-"..v[1]..".bin","wb"))
   assert(f:write(memory.read_bytes_as_binary_string(0,v[3],v[2])));f:close()
  end
 end,at,"ID13-fall-entry-"..string.format("%X",at))
end
local function selection()
 local unlock=rd(0x03002329,1)&0x30
 local cursor,mirror,maximum=rd(0x0300473C,2),rd(0x0300473E,2),rd(0x03004740,2)
 assert(maximum>=12 and maximum<=14 and cursor<=maximum and mirror<=maximum,"native roster bounds")
 if cursor~=mirror then return nil end
 for i=0,maximum do if rd(0x08628000+unlock*2+i*2,2)==13 then return cursor==i and "A" or "Down" end end
 error("ID13 absent from actual roster")
end
local function input(keys,stage,mode)
 if stage~="battle" or mode~=7 then return end
 for k in pairs(keys)do keys[k]=false end
 local p=live();if not p or (rd(0x03004529,1)&0xF)~=0 then return end
 local now=emu.framecount()
 if phase=="waiting" and rd(p,4)==0x0835620C and (rd(p+6,2)&0x61)==0 and
  (rd(p+0xA,2)&0x1000)==0 and (rd(p+8,2)&0x4000)==0 and (rd(p+0x2C,2)&0x40)==0 then
  phase="held";until_frame=now+20;emit("event=jump-start core="..now)
 end
 if phase=="held" then
  if now<until_frame then keys.A=true else phase="released";emit("event=jump-release core="..now)end
 end
end
local function read(name)local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s end
local function replace(s,before,after)
 local a,b=s:find(before,1,true);assert(a and not s:find(before,b+1,true),"unique ID13 fall boundary")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local source=read("bizhawk_probe_result_languages.lua")
source=replace(source,'dump("loaded-rom.bin","ROM",0,0x800000)','dump("loaded-rom.bin","ROM",0,0x1000000)')
source=replace(source,'local limit=userdata.get("frames") or 24000','local limit=math.min(userdata.get("frames") or 14000,14000)')
source=replace(source,'  if mode==4 or mode==5 or mode==6 then pulse("A",frame)',
 '  if mode==4 then local button=id13_selection();if button then pulse(button,frame)end\n  elseif mode==5 or mode==6 then pulse("A",frame)')
source=replace(source,' joypad.set(keys)',' id13_input(keys,stage,mode)\n joypad.set(keys)')
source=replace(source,' if outcome then break end',' if id13_outcome() then outcome="id13-eligible-fall-observed";capture("id13-fall-after") end\n if outcome then break end')
source=replace(source,'local f=assert(io.open(out.."/result-done.txt","w"));','id13_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));')
local env=setmetatable({id13_selection=selection,id13_input=input,
 id13_outcome=function()return fall_core and emu.framecount()>fall_core end,
 id13_finish=function()emit("complete=true phase="..phase.." observed="..tostring(fall_core~=nil));file:close()end},{__index=_ENV})
emit("start readonly=true ordinary_input=true target_id=13 hooks=3")
assert(load(source,"@ID13-ordinary-fall-entry","t",env))()
