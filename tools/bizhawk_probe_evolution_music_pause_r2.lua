-- Ordinary flow until actual 6E playback; one bounded Start pause/resume pair.
local function read_source(name)
 local f=assert(io.open("W:/tools/"..name,"rb"));local s=assert(f:read("*a"));f:close();return s
end
local function replace(s,before,after)
 local a,b=s:find(before,1,true)
 assert(a and not s:find(before,b+1,true),"unique pause-probe anchor: "..before)
 return s:sub(1,a-1)..after..s:sub(b+1)
end
assert(memory.getmemorydomainsize("ROM")==0x1000000,"reviewed sixteen MiB ROM required")
local lifetime=read_source("bizhawk_probe_result_music_lifetime.lua")
local a,b=lifetime:find("local telemetry=[=[\n",1,true);assert(a and not lifetime:find("local telemetry=[=[\n",b+1,true))
local c=lifetime:find("]=]",b+1,true);assert(c)
local telemetry=lifetime:sub(b+1,c-1)
telemetry=replace(telemetry,' music_counts[label]=(music_counts[label] or 0)+1',' music_pause_observe(label,r)\n music_counts[label]=(music_counts[label] or 0)+1')
telemetry=replace(telemetry,'policy=unchanged hook_count=10 per_label_limit=32 max_event_rows=320','policy=ordinary-until-6E-then-Start-pair hook_count=14 per_label_limit=32 max_event_rows=512')
local policy=[=[
local pause={phase="waiting"}
local evo=music_read(0x08D33000+0x6E*8,4)
local stage_header=music_read(0x08D33000+0x10*8,4)
assert(evo==0x08D75728 and stage_header==0x08384BF8,"observed 6E and stage10 headers")
local function active()
 return music_read(0x03004E98,4)==0x6E and music_read(0x03006B40,4)==evo
end
music_pause_observe=function(label,r)
 local now=emu.framecount()
 if label=="player-zero-start" then
  if pause.first and (not pause.devolution or r.R1~=stage_header) then pause.failure="unexpected-player-zero-restart" end
  pause.request=r.R1
 elseif label=="player-zero-start-return" then
  if pause.phase=="waiting" and pause.request==evo and active() then pause.phase="armed";pause.armed=now end
  if pause.devolution and now>pause.devolution and now-pause.devolution<=2 and pause.request==stage_header and
   music_read(0x03004E98,4)==0x10 and music_read(0x03006B40,4)==stage_header then pause.returned=now end
 elseif label=="devolution-return-site" and pause.resume_boundary and pause.phase=="running" and active() and
  (music_read(0x03006B44,4)&0x80000000)==0 and (music_read(0x03004506,2)&0x80)==0 then pause.devolution=now
 elseif active() then
  if label=="pause-entry" and pause.phase=="pause-press" then pause.native_pause=now
  elseif label=="resume-entry" and pause.phase=="resume-press" then pause.native_resume=now
  elseif label=="pause-header-compare" and r.R0==evo and r.R1==evo and pause.native_pause==now then pause.compare_pause=now
  elseif label=="resume-header-compare" and r.R0==evo and r.R1==evo and pause.native_resume==now then pause.compare_resume=now
  elseif label=="mplay-stop" and r.R0==0x03006B40 and r.R14==0x0837C36F and pause.compare_pause==now and pause.phase=="pause-press" then pause.stopped=now
  elseif label=="mplay-resume" and r.R0==0x03006B40 and r.R14==0x0837C3A3 and pause.compare_resume==now and pause.phase=="resume-press" then pause.resumed=now end
 end
end
music_hook(0x0837C9C8,"mplay-stop",function(r,label)if r.R0==0x03006B40 then music_log(label,r)end end)
music_hook(0x0837C1A8,"mplay-resume",function(r,label)if r.R0==0x03006B40 then music_log(label,r)end end)
music_hook(0x03000D00,"iwram-alias-request",function(r,label)
 music_log(label,r);pause.failure="copied-request-entry-executed"
end)
music_hook(0x03000D0C,"iwram-alias-cache",function(r,label)
 music_log(label,r);music_lifetime_finish()
 local f=assert(io.open(music_out.."/result-done.txt","w"))
 assert(f:write("failure:copied-cache-branch-executed"));f:close()
 error("copied-cache-branch-executed")
end)
local function music_pause_input(keys,stage,mode)
 local now=emu.framecount()
 if pause.phase=="waiting" then return end
 if pause.phase=="armed" then
  if stage~="battle" or mode~=7 or not active() then pause.failure="6E-outside-battle";return end
  pause.phase="pause-press";pause.first=now
 end
 for key in pairs(keys)do keys[key]=false end
 local age=now-pause.first
 if age<4 then keys.Start=true
 elseif age<34 then
  pause.phase="hold"
  if not pause.stopped or not active() or (music_read(0x03006B44,4)&0x80000000)==0 then pause.failure="pause-not-held" end
  if age==4 or age==33 then music_log("pause-boundary",emu.getregisters(),"age="..age) end
 elseif age<38 then pause.phase="resume-press";keys.Start=true
 else
  if pause.phase~="running" then
   if not pause.resumed or not active() or (music_read(0x03006B44,4)&0x80000000)~=0 then pause.failure="resume-not-active" end
   music_log("resume-boundary",emu.getregisters(),"age="..age)
   pause.resume_boundary=not pause.failure
  end
  pause.phase="running"
 end
end
local function music_pause_outcome()
 if pause.failure then return "failure:"..pause.failure end
 if pause.returned and pause.stopped and pause.resumed and pause.resume_boundary and pause.phase=="running" then return "evolution-pause-resume-stage-return" end
 if pause.armed and emu.framecount()-pause.armed>=3000 then return "failure:pause-return-deadline" end
end
]=]
local source=read_source("bizhawk_probe_result_languages.lua")
source=replace(source,'dump("loaded-rom.bin","ROM",0,0x800000)','dump("loaded-rom.bin","ROM",0,0x1000000)')
source=replace(source,'local limit=userdata.get("frames") or 24000','local limit=math.min(userdata.get("frames") or 15000,15000)')
source=replace(source,' joypad.set(keys)',' music_pause_input(keys,stage,mode)\n joypad.set(keys)')
source=replace(source,' if outcome then break end',' local pause_outcome=music_pause_outcome()\n if pause_outcome then outcome=pause_outcome;capture("pause-end") end\n if outcome then break end')
source=replace(source,'if not outcome then outcome="bounded-no-result";capture("bounded-end") end','if outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then outcome="failure:pause-target-not-completed";capture("bounded-end") end')
source=replace(source,'local f=assert(io.open(out.."/result-done.txt","w"));','music_lifetime_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));')
assert(load("local music_pause_observe\n"..telemetry..policy..source,"@reviewed-evolution-music-pause","t",_ENV))()
