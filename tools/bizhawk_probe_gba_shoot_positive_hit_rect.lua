-- Repeat the frozen ordinary-input probe on the source-relative child rectangle repair.
local target="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
assert(userdata.get("probe_sha256")==target,"reviewed child rectangle ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua","rb"))
local source=assert(f:read("*a"));f:close()
local old="6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen ROM binding")
source=source:sub(1,a-1)..target..source:sub(b+1)
assert(load(source,"@reviewed-positive-hit-rectangle-repair","t",_ENV))()
