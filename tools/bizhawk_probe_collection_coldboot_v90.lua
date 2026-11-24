-- Read the ordinary post-victory EEPROM in a fresh game process.
local out=assert(userdata.get("output"))
assert(emu.getsystemid()=="GBA" and memory.getmemorydomainsize("ROM")==0x1000000)
local function write(name,bytes)local f=assert(io.open(out.."/"..name,"wb"));f:write(bytes);f:close()end
local function w(offset)return memory.read_u16_le(offset,"IWRAM")end
local function d(offset)return memory.read_u32_le(offset,"EWRAM")end
write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
local starting=emu.framecount()
local observed=false
local success,err=pcall(function()
 for i=0,8000 do
  local key=nil
  if w(0x2310)==3 then
   for slot=0,51 do
    local h=0x10000+slot*0x118
    if memory.read_u16_le(h+16,"EWRAM")&2~=0 and d(h+4)==0x1000 then
     local cb=d(h)
     if cb==0x08090C7C and i>600 then key="Start"
     elseif cb==0x08DFE048 then
      assert(d(h+52)==1,"cold title did not load saved eligibility")
      local tree=memory.read_u8(h+28,"EWRAM");local choice=memory.read_u8(h+29,"EWRAM")
      if tree==2 then
       assert(w(0x2AC8+14)==9 and w(0x2A78+14)==10)
       write("cold-iwram.bin",memory.read_bytes_as_binary_string(0,0x8000,"IWRAM"))
       write("cold-ewram.bin",memory.read_bytes_as_binary_string(0,0x40000,"EWRAM"))
       client.screenshot(out.."/cold-collection.png")
       write("frames.txt",starting.." "..emu.framecount())
       observed=true;return
      else assert(tree==0);key=choice==4 and "A" or "Down" end
     end
    end
   end
  end
  local keys={};for _,k in ipairs({"A","B","Start","Select","Right","Left","Up","Down","R","L","Power"})do keys[k]=false end
  if i%21==0 and key then keys[key]=true end
  joypad.set(keys);emu.frameadvance()
 end
 error("bounded cold load")
end)
write("done.txt",success and observed and "cold-collection-loaded" or tostring(err));client.exit()
