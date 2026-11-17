-- Observe the corrected ROM with the frozen assisted campaign and predecessor hooks.
local OLD="933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775"
local NEW="75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F"
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"one corrected campaign substitution")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local f=assert(io.open("W:/tools/bizhawk_probe_type8_event_provenance.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,OLD,NEW)
local ring="local ring,counts,serial,closed={}, {},0,false"
source=replace(source,ring,ring.."\n"..[[
local first_window,first_chain={},{}
local chain_candidate,chain_core,chain_record
]])
local record="r.R0,r.R1,r.R3,r.R4,r.R5,r.R8,r.R14,r.R15,r.CPSR,detail)"
source=replace(source,record,record.."\n"..[[
 local core,line=emu.framecount(),ring[(serial-1)%256+1]
 if core>=8667 and core<=8673 and #first_window<256 then
  first_window[#first_window+1]=line
 end
 if #first_chain==0 then
  if kind=="type8-air-selector" and (r.CPSR&0x40000000)==0 then
   chain_candidate,chain_core,chain_record={line},core,false
  elseif chain_candidate and core<=chain_core+1 and #chain_candidate<32 then
   chain_candidate[#chain_candidate+1]=line
   if kind=="damage-record-selected" then
    local subtype=rd(0x03004D26,1)
    chain_record=subtype>=0 and subtype<4 and r.R1==0x0836C2AC+subtype*32
   end
   if kind=="event-store" and chain_record and r.R3==0x16 then first_chain=chain_candidate end
  end
 end
]])
local save=[=[ for n=math.max(1,serial-255),serial do assert(file:write(ring[(n-1)%256+1].."\n"))end]=]
source=replace(source,save,[=[
 assert(file:write(string.format("first-window frames=8667..8673 count=%d\n",#first_window)))
 for _,line in ipairs(first_window)do assert(file:write("first "..line.."\n"))end
 assert(file:write(string.format("first-chain count=%d\n",#first_chain)))
 for _,line in ipairs(first_chain)do assert(file:write("chain "..line.."\n"))end
]=]..save)
local parent_read='local source=assert(f:read("*a"));f:close()'
source=replace(source,parent_read,parent_read..';source=corrected_campaign_parent(source)')
local env=setmetatable({corrected_campaign_parent=function(parent)return replace(parent,OLD,NEW)end},{__index=_ENV})
assert(load(source,"@frozen-provenance-corrected-rom","t",env))()
