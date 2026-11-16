-- New ordinary ID14 contact route, with read-only selector/collision provenance.
assert(userdata.get("target_song")==0x6C,"ID14 requires source category0/song6C")
local function read(name)
 local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true)
 assert(a and not s:find(before,b+1,true),"unique ID14 anchor")
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local source=read("bizhawk_probe_evolution_music_three.lua")
source=replace(source,' chosen=target==0x6C and 5 or target==0x6D and 3 or (unlock&0x20)~=0 and 12 or (unlock&0x10)~=0 and 11 or nil',' chosen=14')
source=replace(source,'  if collectible then','  if not collectible then keys.Left=signed(p+0x34)>0x600\n  elseif collectible then')
source=replace(source,'actor(r.R4) and (side==0 or side==1) and','actor(r.R4) and side==0 and id==14 and')
source=replace(source,'music_lifetime_finish()\\nlocal f=','music_lifetime_finish()\\nid14_evidence_finish()\\nlocal f=')
source=replace(source,'music_log(label,r);music_lifetime_finish()','music_log(label,r);music_lifetime_finish();id14_evidence_finish()')
source=replace(source,'..telemetry..policy..source,','..telemetry.."id14_music_finish=music_lifetime_finish\\n"..policy..source,')
local env=setmetatable({},{__index=_ENV})
local collision,queue
env.id14_evidence_finish=function(include_music)
 if include_music and env.id14_music_finish then env.id14_music_finish()end
 if queue then queue.finish()end
 if collision then collision.finish()end
end
queue=assert(load(read("bizhawk_observe_evolution_event_queue.lua"),"@ID14-event-witness","t",env))()
local witness=read("bizhawk_observe_collision_alignment.lua")
witness=replace(witness,'snapshot("collision-e5");finish()','snapshot("collision-e5");finish();id14_evidence_finish(true)')
collision=assert(load(witness,"@ID14-collision-witness","t",env))()
assert(load(source,"@reviewed-ID14-ordinary-contact","t",env))()
