-- Approach the observed left-side arrival before Calumon becomes collectible.
assert(userdata.get("target_song")==0x6C,"6C-only ordinary approach")
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_music_three.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before="  if collectible then"
local after="  if not collectible then keys.Left=signed(p+0x34)>0x600\n  elseif collectible then"
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique inactive-contact input")
source=source:sub(1,a-1)..after..source:sub(b+1)
assert(load(source,"@reviewed-6C-ordinary-approach","t",_ENV))()
