-- Controlled terminal replay with prospective mapping and live consumption checks.
local target="280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7"
assert(userdata.get("probe_sha256")==target,"reviewed display-epoch ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_terminal.lua","rb"))
local source=assert(f:read("*a"));f:close()
local old="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen ROM binding")
source=source:sub(1,a-1)..target..source:sub(b+1)
local before='if read(Q+0x28,4)~=AUX or read(AUX+0x18,4)~=Q then return "native-guard-aux18-not-upper"end'
local after='if read(Q+0x28,4)~=AUX or read(AUX+0x28,4)~=Q then return "native-guard-aux28-not-upper"end'
local x,y=source:find(before,1,true)
assert(x and not source:find(before,y+1,true),"unique frozen owner predicate")
source=source:sub(1,x-1)..after..source:sub(y+1)
local changes={
 {'w(0x0400000A)&0xDFCC~=0x1E00','w(0x0400000A)&0xCC~=0'},
 {'hook(0x086FF6E8,"guarded-display"','hook(0x086FF75C,"guarded-display"'}
}
for _,change in ipairs(changes)do
 local i,j=source:find(change[1],1,true)
 assert(i and not source:find(change[1],j+1,true),"unique frozen display epoch site")
 source=source:sub(1,i-1)..change[2]..source:sub(j+1)
end
assert(load(source,"@reviewed-terminal-display-epoch-repair","t",_ENV))()
