-- Keep the frozen counter1 probe, binding its entire target cycle to one core.
assert(userdata.get("probe_sha256")=="280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7","same reviewed ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_counter1.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before="  if not target then ignored=ignored+1;return end\n"
local after=before..'  if not need(target.core==emu.framecount(),"target-cycle-core",r)then return end\n'
local parts,cursor,count={},1,0
while true do
 local a,b=source:find(before,cursor,true)
 if not a then break end
 parts[#parts+1]=source:sub(cursor,a-1)..after;cursor=b+1;count=count+1
end
assert(count==6,"six frozen target-cycle hooks required")
parts[#parts+1]=source:sub(cursor);source=table.concat(parts)
local old="pending and pending.index==matches"
local new="pending and pending.core==emu.framecount()and pending.index==matches"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen pending-store predicate")
source=source:sub(1,a-1)..new..source:sub(b+1)
assert(load(source,"@reviewed-counter1-samecore-v2","t",_ENV))()
