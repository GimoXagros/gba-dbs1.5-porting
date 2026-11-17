-- Run the frozen bounded palette witness over the source-correct outer dispatch.
local OLD="3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F"
local NEW="574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique palette positive repin")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local f=assert(io.open("W:/tools/bizhawk_probe_iraira_palette_witness.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,OLD,NEW)
source=replace(source,"0x080D0BD0,0xEB12CF8A","0x080D0BD0,0xEB32EA9A")
local read_parent='local source=assert(f:read("*a"));f:close()'
source=replace(source,read_parent,read_parent..';source=bind_palette_positive_rom(source)')
local env=setmetatable({bind_palette_positive_rom=function(parent)return replace(parent,OLD,NEW)end},{__index=_ENV})
assert(load(source,"@frozen-iraira-palette-witness-positive-rom","t",env))()
