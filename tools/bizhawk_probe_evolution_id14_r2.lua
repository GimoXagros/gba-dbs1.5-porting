-- Hold ordinary A through the source-backed native jump preparation window.
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_id14.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before='local source=read("bizhawk_probe_evolution_music_three.lua")'
local after=before..[=[
source=replace(source,'local chosen,diagnostics=nil,0','local chosen,diagnostics=nil,0\nlocal contact_jump_until=-2')
source=replace(source,'  for key in pairs(keys)do keys[key]=false end','  for key in pairs(keys)do keys[key]=false end\n  keys.A=emu.framecount()<contact_jump_until')
source=replace(source,'   keys.Right=dx>0x40;keys.Left=dx< -0x40;keys.A=dy< -0x100 and emu.framecount()%45<4','   keys.Right=dx>0x40;keys.Left=dx< -0x40\n   if dy< -0x100 and (music_read(p+4,2)&0xF)==0 and (music_read(p+6,2)&1)==0 and emu.framecount()>contact_jump_until then\n    contact_jump_until=emu.framecount()+20;keys.A=true\n   end')
]=]
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique ID14 base composition")
source=source:sub(1,a-1)..after..source:sub(b+1)
assert(load(source,"@reviewed-ID14-held-jump","t",_ENV))()
