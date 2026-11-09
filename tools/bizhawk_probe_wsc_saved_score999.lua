-- Original-only authorized save-copy development observation.
-- The score module alone owns the explicitly permitted P1 score=999 write.
-- All input and stage/boss progression reuse the frozen v4 ordinary policy.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
assert(userdata.get("source_sha256")=="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
assert(userdata.get("save_copy_sha256")=="051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F")
assert(userdata.get("callback_order")=="bizhawk2111-rew")
assert(emu.getsystemid()=="WSWAN")
for domain,size in pairs({ROM=0x800000,RAM=0x10000,SRAM=0x8000,iEEPROM=1024}) do
 assert(memory.getmemorydomainsize(domain)==size,"unexpected domain "..domain)
end
local frames=assert(userdata.get("frames"),"explicit bounded frame budget required")
assert(type(frames)=="number" and frames>0 and frames==math.floor(frames) and frames<=180000)
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(data);f:close()
end
local function log(line)
 local f=assert(io.open(out.."/saved-score-driver.txt","a"));f:write(line.."\n");f:close()
end
for _,name in ipairs({"saved-score-driver.txt","done.txt"}) do
 local old=io.open(out.."/"..name,"rb")
 if old then old:close();error("fresh run output required") end
end
-- Keep failed startup evidence, but never enable the cheat or input before equality.
local actual=memory.read_bytes_as_binary_string(0,0x8000,"SRAM")
write("initial-sram.bin",actual)
write("internal-eeprom.bin",memory.read_bytes_as_binary_string(0,1024,"iEEPROM"))
local f=assert(io.open(out.."/authorized-cartridge-copy.bin","rb"))
local expected=assert(f:read("*a"));f:close()
assert(#expected==0x8000,"authorized cartridge copy length")
local function boot_byte(data,offset,value)
 return data:sub(1,offset)..string.char(value)..data:sub(offset+2)
end
-- Exact original startup stores74FC1F and74FC4A, not ignored-byte masks.
expected=boot_byte(boot_byte(expected,0x4E,1),0x73,0)
assert(expected==actual,"entire actual save after two exact source startup stores")
log("original_only=true development_observation=true final_QA=false save_copy_sha256="..userdata.get("save_copy_sha256"))
log("initial_cartridge_copy_exact_after_source_boot=true stores=004E:01,0073:00 initial_core="..emu.framecount())
log("authorized_cheat=P1_D_Spirit_999 score_module_only=true input=frozen_v4 ordinary_stage_progression=true frame_budget="..frames)

local di=dofile("W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua")
local score=dofile("W:/tools/bizhawk_wsc_score999.lua")
assert(type(di.status)=="function" and type(di.finish)=="function")
assert(type(score.tick)=="function" and type(score.status)=="function" and type(score.finish)=="function")
local function ready()
 local s=di.status()
 return s.terminal_observed and s.actual_final_irq_observed and s.paired_reads>0 and not s.pending
end
local paths={
 v4="W:/tools/bizhawk_probe_wsc_shoot_short_hard_v4.lua",
 parent="W:/tools/bizhawk_probe_wsc_shoot_short_hard.lua",
 collect="W:/tools/bizhawk_probe_wsc_shoot_collect_v2.lua",
 hard="W:/tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua",
}
local function read(path)
 local p=assert(io.open(path,"rb"));local text=assert(p:read("*a"));p:close()
 return text:gsub("\r\n","\n")
end
local function once(text,old,new)
 local a,b=text:find(old,1,true);assert(a,"frozen composition anchor missing: "..old)
 assert(not text:find(old,b+1,true),"ambiguous frozen composition anchor")
 return text:sub(1,a-1)..new..text:sub(b+1)
end
local changed={}
local collect=read(paths.collect)
local start='for _,raw in ipairs({0x7738CA,0x773859,0x75FC98,0x75FD36,0x75FD87,0x753357,0x77E196}) do'
local stop='local function choose(px,py,owner,orbs)'
local a=assert(collect:find(start,1,true));local b=assert(collect:find(stop,a,true))
assert(not collect:find(start,a+#start,true) and not collect:find(stop,b+#stop,true))
assert(collect:sub(a,b-1):find('mainmemory.read_u8((0x3000+r.IY+10)%0x10000)',1,true),"old operand hook signature")
changed[paths.collect]=collect:sub(1,a-1)..'-- Legacy owner hooks removed; DI v3 owns consumed-operand evidence.\n'..collect:sub(b)
assert(not changed[paths.collect]:find('diA=',1,true))
local hard=read(paths.hard)
hard=once(hard,'log("system=WSWAN guest_writes=none savestate=none supplied_save=none input=joypad-only")',
 'log("system=WSWAN guest_writes=authorized-score999-module-only savestate=none supplied_save=authorized-copy input=frozen-v4-joypad development_observation=true final_QA=false")')
hard=once(hard,'local f=assert(io.open(out .. "/done.txt","w"))',
 'local f=assert(io.open(out .. "/base-observation-complete.txt","w"))')
hard=once(hard,'local prior_input, prior_stage, sampled_terminal, window_x, stationary = "", -1, 0, nil, 0',
 'local saved_stage_seen,saved_stage_count={},0\nlocal prior_input, prior_stage, sampled_terminal, window_x, stationary = "", -1, 0, nil, 0')
hard=once(hard,' if stage ~= prior_stage or frame % 600 == 0 then',[[
 if mode==7 and first and stage>=0 and stage<=11 and not saved_stage_seen[stage] and saved_stage_count<12
  and (stage==7 or stage==11 or first.score==999) then
  saved_stage_seen[stage]=true;saved_stage_count=saved_stage_count+1
  log(string.format("saved_score stage_capture relative=%d stage=%d score=%d authorized_score_cheat=true",frame,stage,first.score))
  snapshot(string.format("saved-stage-%02d",stage))
 end
 if stage ~= prior_stage or frame % 600 == 0 then]])
changed[paths.hard]=hard
changed[paths.parent]=once(read(paths.parent),
 'if shoot_row_hits>0 and shoot_irq_hits>0 and shoot_frames>=300 then',
 'if shoot_row_hits>0 and shoot_irq_hits>0 and shoot_frames>=300 and saved_di_ready() then')
log("legacy_collector_owner_hooks=removed legacy_hard_register_logs=context_only consumed_operand_owner=DI_v3")
local proxy_io=setmetatable({open=function(path,mode)
 if changed[path] then
  assert(mode=="rb","frozen policy dependencies read-only")
  return {read=function(_,kind)assert(kind=="*a");return changed[path] end,close=function()end}
 end
 return io.open(path,mode)
end},{__index=io})
local finalized=false
local proxy_client=setmetatable({exit=function(...)
 assert(not finalized,"duplicate driver completion")
 local reached=ready()
 local ds=di.finish()
 local ss=score.finish()
 assert(type(ss)=="table","score finish must return status")
 log(string.format("complete reached_shoot_di=%s paired_reads=%d terminal_observed=%s score_writes=%d score_hits=%d",
  tostring(reached),ds.paired_reads,tostring(ds.terminal_observed),ss.writes,ss.hits))
 write("done.txt",reached and "shoot-di-observed" or "bounded-observation-complete")
 finalized=true
 return client.exit(...)
end},{__index=client})
local environment=setmetatable({io=proxy_io,client=proxy_client,saved_di_ready=ready},{__index=_ENV})
score.tick() -- installs exactly the score module's guarded source-site hook
return assert(load(read(paths.v4),"@saved-score999-v4","t",environment))()
