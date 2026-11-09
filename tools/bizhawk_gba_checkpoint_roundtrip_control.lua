-- Reuse only the reviewed load/resave prefix; execute no game frame or input policy.
local f=assert(io.open("W:/tools/bizhawk_replay_gba_shoot_entry.lua","rb"))
local source=assert(f:read("*a")):gsub("\r\n","\n");f:close()
local function unique(text)
 local a,b=source:find(text,1,true);assert(a and not source:find(text,b+1,true),"unique roundtrip anchor")
 return a,b
end
local cut=unique('local module=read("W:/tools/bizhawk_gba_shoot_entry_observer.lua")')
local tail=unique('end\nlocal ok,err=pcall(replay)')
source=source:sub(1,cut-1)..source:sub(tail)
local a,b=unique('assert(emu.framecount()==captured,"restored core frame mismatch")')
source=source:sub(1,b)..'\nwrite("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))'..source:sub(b+1)
a,b=unique('local ok,err=pcall(replay)')
source=source:sub(1,b)..'\nif ok then write("shoot-entry-done.txt","checkpoint-roundtrip-only");client.exit()end'..source:sub(b+1)
assert(load(source,"@reviewed-native-roundtrip-only","t",_ENV))()
