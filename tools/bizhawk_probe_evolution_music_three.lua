-- Ordinary menu/contact input for one of the three remaining evolution songs.
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
telemetry=replace(telemetry,'policy=unchanged hook_count=10 per_label_limit=32 max_event_rows=320','policy=ordinary-target-contact-then-Start-pair hook_count=16 per_label_limit=32 max_event_rows=576')
local policy=[=[
local pause={phase="waiting"}
local target=assert(userdata.get("target_song"))
assert(target==0x6C or target==0x6D or target==0x6F,"remaining evolution song only")
local category=target-0x6C
local evo=music_read(0x08D33000+target*8,4)
assert(evo==({[0x6C]=0x08D43CAC,[0x6D]=0x08D47D64,[0x6F]=0x08D782CC})[target],"target header")
local categories=music_read(0x080D14A8,4)
local source_categories={2,2,2,1,1,0,0,0,0,1,1,3,3,0,0,2}
for id=0,15 do assert(music_read(categories+id,1)==source_categories[id+1],"source category map")end
local stage_id,stage_header,stage_candidate,stage_candidate_core,stage_return_core,stage_verified
local chosen,diagnostics=nil,0
local function actor(p)
 return p>=0x02010018 and p<=0x02010018+51*0x118 and (p-0x02010018)%0x118==0 and (music_read(p-8,2)&2)~=0
end
local function signed(a)local v=music_read(a,2);return v<0x8000 and v or v-0x10000 end
local function music_selection()
 local unlock=music_read(0x03002329,1)&0x30
 chosen=target==0x6C and 5 or target==0x6D and 3 or (unlock&0x20)~=0 and 12 or (unlock&0x10)~=0 and 11 or nil
 if not chosen then pause.failure="target-character-locked";return end
 local cursor,mirror,maximum=music_read(0x0300473C,2),music_read(0x0300473E,2),music_read(0x03004740,2)
 if maximum<12 or maximum>14 or cursor>maximum or mirror>maximum then pause.failure="unexpected-selection-state";return end
 if cursor~=mirror then return end
 local list=0x08628000+unlock*2
 for i=0,maximum do
  if music_read(list+i*2,2)==chosen then return cursor==i and "A" or "Down" end
 end
 pause.failure="target-not-in-roster"
end
local function music_contact(keys,stage,mode)
 if stage~="battle" or mode~=7 then return end
 local p=music_read(0x0300489C,4)
 local q=music_read(0x030048A0,4)
 local cal=music_read(0x03004CE8,4)
 local valid=actor(p) and actor(q) and music_read(p+0x10,1)==0 and music_read(q+0x10,1)==1 and
  music_read(p+0x11,1)==chosen and music_read(p+0x14,4)==p and music_read(p+0x18,4)==q and music_read(q+0x18,4)==p
 local collectible=actor(cal) and (music_read(cal+4,2)&0xF)==8 and music_read(cal+0x10,1)==2 and (music_read(cal+4,2)&0x1000)~=0
 if valid then
  for key in pairs(keys)do keys[key]=false end
  if collectible then
   local dx,dy=signed(cal+0x34)-signed(p+0x34),signed(cal+0x36)-signed(p+0x36)
   keys.Right=dx>0x40;keys.Left=dx< -0x40;keys.A=dy< -0x100 and emu.framecount()%45<4
  end
 end
 if emu.framecount()%120==0 and diagnostics<200 then
  diagnostics=diagnostics+1
  assert(music_file:write(string.format("contact core=%d target=%02X chosen=%d stage=%d p1=%08X p2=%08X calumon=%08X valid=%s collectible=%s p1id=%d p2id=%d p1xy=%d,%d calxy=%d,%d calcb=%08X calflags=%04X\n",
   emu.framecount(),target,chosen or -1,music_read(0x0300231E,1),p,q,cal,tostring(valid),tostring(collectible),music_read(p+0x11,1),music_read(q+0x11,1),signed(p+0x34),signed(p+0x36),signed(cal+0x34),signed(cal+0x36),music_read(cal,4),music_read(cal+4,2))))
  music_file:flush()
 end
end
local function active()
 return music_read(0x03004E98,4)==target and music_read(0x03006B40,4)==evo
end
music_pause_observe=function(label,r)
 local now=emu.framecount()
 if label=="stage-selector-queue" and r.R8>=0xF and r.R8<=0x18 and r.R9==4 then
  stage_candidate=r.R8;stage_candidate_core=now;stage_return_core=nil
 elseif label=="stage-selector-return" and stage_candidate_core==now and music_read(0x030022F2,2)==stage_candidate and music_read(0x030022FE,2)==4 and (music_read(0x03002300,2)&0x100)~=0 then
  stage_return_core=now
  if pause.devolution and stage_candidate==stage_id then pause.stage_queue=now else stage_verified=nil end
 elseif label=="evolution-selector" then
  local id=music_read(r.R4+0x11,1)
  local side=music_read(r.R4+0x10,1)
  if pause.phase=="waiting" and actor(r.R4) and (side==0 or side==1) and music_read(r.R13,4)==id and id>=0 and id<16 and source_categories[id+1]==category and
   stage_verified and music_read(0x03004E98,4)==stage_id and music_read(0x03006B40,4)==stage_header then
   pause.actor=r.R4;pause.identity=id;pause.side=side;pause.selector=now
  end
 elseif label=="music-request" and pause.devolution and pause.stage_queue and r.R8==stage_id then pause.stage_request=now
 elseif label=="player-zero-start" then
  if pause.first and (not pause.devolution or r.R1~=stage_header) then pause.failure="unexpected-player-zero-restart" end
  pause.request=r.R1
 elseif label=="player-zero-start-return" then
  if pause.phase=="waiting" and stage_candidate and stage_return_core==stage_candidate_core and now-stage_candidate_core<=4 and pause.request==music_read(0x08D33000+stage_candidate*8,4) and music_read(0x03004E98,4)==stage_candidate then
   stage_id=stage_candidate;stage_header=pause.request;stage_verified=now
  end
  if pause.phase=="waiting" and pause.selector and now-pause.selector<=4 and pause.request==evo and active() then pause.phase="armed";pause.armed=now end
  if pause.devolution and pause.stage_request==now and now>pause.devolution and now-pause.devolution<=2 and pause.request==stage_header and
   music_read(0x03004E98,4)==stage_id and music_read(0x03006B40,4)==stage_header then pause.returned=now end
 elseif label=="devolution-return-site" and r.R4==pause.actor and music_read(r.R4+0x11,1)==pause.identity and music_read(r.R4+0x10,1)==pause.side and pause.resume_boundary and pause.phase=="running" and active() and
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
music_hook(0x080D149C,"stage-selector-queue",function(r,label)music_log(label,r)end)
music_hook(0x080D14A0,"stage-selector-return",function(r,label)music_log(label,r)end)
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
 if pause.phase=="waiting" then music_contact(keys,stage,mode);return end
 if pause.phase=="armed" then
  if stage~="battle" or mode~=7 or not active() then pause.failure="target-outside-battle";return end
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
source=replace(source,'local limit=userdata.get("frames") or 24000','local limit=math.min(userdata.get("frames") or 24000,24000)')
source=replace(source,'  if mode==4 or mode==5 or mode==6 then pulse("A",frame)','  if mode==4 then local button=music_selection();if button then pulse(button,frame)end\n  elseif mode==5 or mode==6 then pulse("A",frame)')
source=replace(source,' joypad.set(keys)',' music_pause_input(keys,stage,mode)\n joypad.set(keys)')
source=replace(source,' if outcome then break end',' local pause_outcome=music_pause_outcome()\n if pause_outcome then outcome=pause_outcome;capture("pause-end") end\n if outcome then break end')
source=replace(source,'if not outcome then outcome="bounded-no-result";capture("bounded-end") end','if outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then outcome="failure:pause-target-not-completed";capture("bounded-end") end')
source=replace(source,'local f=assert(io.open(out.."/result-done.txt","w"));','music_lifetime_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));')
assert(load("local music_pause_observe\n"..telemetry..policy..source,"@reviewed-evolution-music-pause","t",_ENV))()
