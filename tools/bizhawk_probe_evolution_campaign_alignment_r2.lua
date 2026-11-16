-- Attach the read-only upstream witness to the approved score-assisted route.
local observer=dofile("W:/tools/bizhawk_observe_collision_alignment.lua")
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_music_campaign_r2.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before=[=[score_file:close()\\nmusic_lifetime_finish()\\nlocal f=]=]
local after=[=[score_file:close()\\nmusic_lifetime_finish()\\ncollision_alignment_finish()\\nlocal f=]=]
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique completed music evidence boundary")
source=source:sub(1,a-1)..after..source:sub(b+1)
before='music_log(label,r);score_file:close();music_lifetime_finish()'
after=before..';collision_alignment_finish()'
a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique alias failure evidence boundary")
source=source:sub(1,a-1)..after..source:sub(b+1)
local env=setmetatable({collision_alignment_finish=observer.finish},{__index=_ENV})
assert(load(source,"@reviewed-campaign-alignment","t",env))()
