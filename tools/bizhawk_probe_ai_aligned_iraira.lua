-- Preserve the corrected AI campaign while observing Iraira's native clock and display phase.
local OLD="DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98"
local NEW="3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F"
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"isolated output required")
assert(userdata.get("probe_sha256")==NEW,"frozen AI and Iraira ROM")
local phases,clock={},{}
local phase_count,clock_count,last_core,last_clock=0,0,nil,nil
local function byte(a)return memory.read_u8(a-0x03000000,"IWRAM")end
local function word(a)return memory.read_u16_le(a-0x03000000,"IWRAM")end
local function scoped()
 return byte(0x0300232E)==4 and byte(0x0300231E)==10 and byte(0x0300231C)==11
end
local phase_writer={[0x08D8AF94]="init-clear",[0x086283B4]="display-toggle"}
local function attach(observer)
 for address,opcode in pairs({
  [0x0837501C]=0xE59F8150,[0x08375018]=0xE1C890B0,
  [0x08D8AF8C]=0xE1C100B0,[0x086283A4]=0xE1C010B0,[0x086283AC]=0xE1C320B0
 }) do
  assert(memory.read_u32_le(address-0x08000000,"ROM")==opcode,"Iraira probe opcode")
 end
 event.on_bus_write(function(address,value,flags)
  if not scoped() then return end
  local r=emu.getregisters()
  local role=phase_writer[r.R15]
  if not role then return end
  phase_count=phase_count+1
  if #phases<32 then
   phases[#phases+1]=string.format("phase core=%d role=%s pc=%08X address=%08X old=%04X value=%04X flags=%X",
    emu.framecount(),role,r.R15,address,word(address),value&65535,flags)
  end
 end,0x03002568,"iraira-display-phase-write")
 event.on_bus_exec(function()
  if #clock==121 or not scoped() or not observer.live() then return end
  local r=emu.getregisters()
  local core,value=emu.framecount(),word(0x03004500)
  if r.R8~=0x03004500 or (r.R9&65535)~=value or value>=7200 then
   clock,last_core,last_clock={},nil,nil
   return
  end
  if last_core and (core~=last_core+1 or value~=last_clock-1) then clock={} end
  last_core,last_clock=core,value
  clock_count=clock_count+1
  clock[#clock+1]=string.format("clock core=%d value=%d owner=%08X r9=%08X pc=%08X phase=%04X backdrop=%04X",
   core,value,r.R8,r.R9,r.R15,word(0x03002568),word(0x03002654))
 end,0x0837501C,"iraira-after-native-clock-write")
end
local function finish()
 local f=assert(io.open(out.."/iraira-clock-phase.txt","wb"))
 assert(f:write(string.format("summary core=%d phase_total=%d phase_kept=%d clock_observed=%d clock_streak=%d guest_writes=none input=frozen-parent\n",
  emu.framecount(),phase_count,#phases,clock_count,#clock)))
 for _,line in ipairs(phases) do assert(f:write(line.."\n")) end
 for _,line in ipairs(clock) do assert(f:write(line.."\n")) end
 assert(f:close())
end
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique Iraira observer adaptation")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function extend_ai(source)
 local binding=[=[ parent=replace(parent,binding,binding.."\n attach_ai_probe(observer)")]=]
 source=replace(source,binding,[=[ parent=replace(parent,binding,binding.."\n attach_ai_probe(observer)\n attach_iraira_probe(observer)")]=])
 local marker=[=[ return replace(parent,marker,"  finish_ai_probe()\n"..marker)]=]
 return replace(source,marker,[=[ return replace(parent,marker,"  finish_ai_probe()\n  finish_iraira_probe()\n"..marker)]=])
end
local f=assert(io.open("W:/tools/bizhawk_probe_ai_corrected_campaign.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,OLD,NEW)
local load_ai='local source=assert(f:read("*a"));f:close()\nsource=replace(source,OLD,NEW)'
local extended='local source=assert(f:read("*a"));f:close()\nsource=extend_iraira_ai(source)\nsource=replace(source,OLD,NEW)'
source=replace(source,load_ai,extended)
local env=setmetatable({extend_iraira_ai=extend_ai,attach_iraira_probe=attach,finish_iraira_probe=finish},{__index=_ENV})
assert(load(source,"@frozen-ai-corrected-campaign-with-iraira","t",env))()
