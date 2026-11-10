-- Controlled terminal replay with the reviewed palette calls and reciprocal owner field.
local target="46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B"
assert(userdata.get("probe_sha256")==target,"reviewed reciprocal-owner ROM required")
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
assert(load(source,"@reviewed-terminal-reciprocal-owner-repair","t",_ENV))()
