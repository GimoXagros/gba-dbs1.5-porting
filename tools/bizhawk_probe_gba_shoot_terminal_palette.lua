-- Controlled terminal replay with only the reviewed palette-call repair.
local target="FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8"
assert(userdata.get("probe_sha256")==target,"reviewed palette-call ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_terminal.lua","rb"))
local source=assert(f:read("*a"));f:close()
local old="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen ROM binding")
source=source:sub(1,a-1)..target..source:sub(b+1)
assert(load(source,"@reviewed-terminal-palette-call-repair","t",_ENV))()
