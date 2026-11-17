-- Keep the frozen campaign and AI guards on the source-corrected ROM.
local OLD="75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F"
local NEW="DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98"
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique corrected AI adaptation")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local f=assert(io.open("W:/tools/bizhawk_probe_ai_producer_provenance.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,OLD,NEW)
local load_parent='local source=assert(f:read("*a"));f:close()'
source=replace(source,load_parent,load_parent..';source=bind_corrected_ai_rom(source)')
local load_witness='rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4)))'
source=replace(source,load_witness,'rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4)),true)')
source=replace(source,'record("target",r,detail)','record("target",r,detail,true)')
local ledger='address,rd(OWNER,2),value&65535,flags),(value&65535)==15)'
source=replace(source,ledger,ledger.."\n"..[[
   local r=emu.getregisters()
   if not init["action-first-copy"] and r.R14==0x080C69B8 and r.R5==OWNER then
    local src=r.R4-2
    record("action-first-copy",r,string.format("src=%08X ordinal=%04X word=%04X bank=%04X rng=%04X action18=%s",
     src,rd(0x03003D68,2),value&65535,rd(0x03004D92,2),rd(0x03004DB2,2),bytes(src,18)),true)
   end
]])
local env=setmetatable({bind_corrected_ai_rom=function(parent)return replace(parent,OLD,NEW)end},{__index=_ENV})
assert(load(source,"@frozen-ai-provenance-corrected-rom","t",env))()
