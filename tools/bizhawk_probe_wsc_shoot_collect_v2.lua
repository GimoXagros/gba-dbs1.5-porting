-- Ordinary input policy for the existing fresh-boot, read-only lifetime observer.
local output=assert(userdata.get("output"))
assert(output:match("^W:/build/[%w%-%_/]+$"))
local set_keys=joypad.set
local previous=-1
for _,raw in ipairs({0x7738CA,0x773859,0x75FC98,0x75FD36,0x75FD87,0x753357,0x77E196}) do
 local count=0
 event.on_bus_write(function(address)
  if memory.read_u8(0x5C,"SRAM")~=11 then return end
  count=count+1
  if count>512 then return end
  local r=emu.getregisters()
  assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000)
  local f=assert(io.open(output.."/terminal-owners.txt","a"))
  f:write(string.format("frame=%d raw=%06X DS=%04X ES=%04X SI=%04X DI=%04X BX=%04X CX=%04X SP=%04X camera=%04X saved=%04X diA=%02X\n",
   emu.framecount(),raw,r.DS0,r.DS1,r.IX,r.IY,r.BW,r.CW,r.SP,
   memory.read_u16_le(0x1E0,"SRAM"),mainmemory.read_u16_le(0xFA16),mainmemory.read_u8((0x3000+r.IY+10)%0x10000)))
  f:close()
  if raw==0x7738CA or raw==0x75FD36 or raw==0x75FC98 and count==1 then
   local p=assert(io.open(string.format("%s/owner-%06X-%d-ram.bin",output,raw,count),"wb"))
   p:write(mainmemory.read_bytes_as_binary_string(0,0x10000));p:close()
  end
 end,raw-0x700000,"terminal-owner-"..raw,"System Bus")
end
local function choose(px,py,owner,orbs)
 local selected,distance=nil,math.huge
 for _,orb in ipairs(orbs) do
  -- Source742B48 compares orb+10 with collector+10 before awarding a point.
  if orb.owner~=owner then
   local d=math.abs(orb.x-px)+2*math.abs(orb.y-py)
   if d<distance then selected,distance=orb,d end
  end
 end
 return selected
end
assert(choose(0,0,0,{{owner=0,x=0,y=0},{owner=1,x=10,y=0}}).x==10)
assert(choose(0,0,0,{{owner=0,x=0,y=0}})==nil)
assert(choose(0,0,0,{{owner=1,x=10,y=0},{owner=1,x=0,y=10}}).x==10)
local function signed(value)return value<0x8000 and value or value-0x10000 end
joypad.set=function(keys,...)
 local mode=memory.read_u16_le(0x4E,"SRAM")
 local stage=memory.read_u8(0x5C,"SRAM")
 local player=memory.read_u16_le(0x65C,"SRAM")
 if mode==7 and stage~=11 and player>=0x24 and player<=0x3654 and (player-0x24)%0x110==0 then
  local at=0xC000+player
  local orbs={}
  for slot=0,14 do
   if memory.read_u8(0x640+slot,"SRAM")~=0xFF then
    local header=memory.read_u16_le(0x60C+2*slot,"SRAM")
    if header>=0x14 and header<=0x3644 and (header-0x14)%0x110==0 then
     local orb=0xC000+header+0x10
     if mainmemory.read_u16_le(orb+4)%16==7 then
      orbs[#orbs+1]={slot=slot,owner=mainmemory.read_u8(orb+0x10),
       x=signed(mainmemory.read_u16_le(orb+0x26)),y=signed(mainmemory.read_u16_le(orb+0x28))}
     end
    end
   end
  end
  local x,y=signed(mainmemory.read_u16_le(at+0x26)),signed(mainmemory.read_u16_le(at+0x28))
  local target=choose(x,y,mainmemory.read_u8(at+0x10),orbs)
  if target then
   local dx=target.x-x
   keys["P1 X2"]=dx>0x30;keys["P1 X4"]=dx< -0x30
   keys["P1 A"]=target.y+0x100<y and emu.framecount()%45<5
   keys["P1 B"]=false
   if target.slot~=previous then
    local f=assert(io.open(output.."/collect.txt","a"))
    f:write(string.format("frame=%d slot=%d owner=%d p1=%04X,%04X target=%04X,%04X\n",
     emu.framecount(),target.slot,target.owner,x%65536,y%65536,target.x%65536,target.y%65536));f:close()
    previous=target.slot
   end
  else previous=-1 end
 end
 return set_keys(keys,...)
end
dofile("W:/tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua")
