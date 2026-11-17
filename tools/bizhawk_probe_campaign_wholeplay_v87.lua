-- Rebind the verified full-play observer to the source-correct child-contact ROM.
local f=assert(io.open("W:/tools/bizhawk_probe_campaign_wholeplay_v86.lua","rb"))
local source=assert(f:read("*a"));assert(f:close())
local count
source,count=source:gsub("574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76",
 "5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC")
assert(count==1,"single reviewed ROM binding")
assert(load(source,"@wholeplay-v87-ROM-binding","t",_ENV))()
