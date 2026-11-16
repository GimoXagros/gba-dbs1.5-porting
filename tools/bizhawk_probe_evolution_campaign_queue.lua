-- Preserve the approved input policy and close both read-only witnesses.
local queue=dofile("W:/tools/bizhawk_observe_evolution_event_queue.lua")
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_campaign_alignment_r2.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before='collision_alignment_finish=observer.finish'
local after='collision_alignment_finish=function()observer.finish();evolution_queue_finish()end'
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"unique evidence closing hook")
source=source:sub(1,a-1)..after..source:sub(b+1)
local env=setmetatable({evolution_queue_finish=queue.finish},{__index=_ENV})
assert(load(source,"@reviewed-campaign-event-queue","t",env))()
