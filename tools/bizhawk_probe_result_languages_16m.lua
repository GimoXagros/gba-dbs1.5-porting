-- Preserve ordinary result input/observations; capture the complete16MiB image.
assert(memory.getmemorydomainsize("ROM")==0x1000000,"reviewed sixteen MiB ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_result_languages.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before='dump("loaded-rom.bin","ROM",0,0x800000)'
local after='dump("loaded-rom.bin","ROM",0,0x1000000)'
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique frozen full-ROM capture")
source=source:sub(1,a-1)..after..source:sub(b+1)
assert(load(source,"@reviewed-result-sixteen-MiB-capture","t",_ENV))()
