-- Separate score-assisted normal campaign; preserves the frozen contact probe.
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_music_three.lua","rb"))
local probe=assert(f:read("*a"));f:close()
local function replace(s,before,after)
 local a,b=s:find(before,1,true)
 assert(a and not s:find(before,b+1,true),"unique campaign anchor: "..before)
 return s:sub(1,a-1)..after..s:sub(b+1)
end
local campaign=[=[
assert(target==0x6F,"CPU11 campaign is only for remaining 6F")
assert(userdata.get("score_authorization")=="user-approved-development-score999","score assist authorization")
local campaign_round,campaign_samples,score_writes=0,0,0
local score_file=assert(io.open(music_out.."/score999-writes.txt","wb"))
assert(score_file:write("development_assist=P1-score999-only no_HP_stage_mode_unlock_register_writes=true\n"));score_file:flush()
local function campaign_input(stage,mode)
 if stage~="battle" or mode~=7 then return end
 local progress=music_read(0x0300232E,1)
 local physical=music_read(0x0300231E,1)
 local p,q=music_read(0x0300489C,4),music_read(0x030048A0,4)
 if music_read(0x0300231F,1)~=1 then pause.failure="campaign-not-Normal";return end
 if music_read(0x03004502,2)~=0 or (music_read(0x03004529,1)&7)~=0 then return end
 if not actor(p) or not actor(q) or p==q or (music_read(p+4,2)&0xF)~=0 or (music_read(q+4,2)&0xF)~=0 or
  music_read(p+0x10,1)~=0 or music_read(q+0x10,1)~=1 or music_read(p+0x11,1)~=0 or
  music_read(p+0x14,4)~=p or music_read(q+0x14,4)~=q or music_read(p+0x18,4)~=q or music_read(q+0x18,4)~=p then return end
 local hp,qhp=music_read(p+0x64,2),music_read(q+0x64,2)
 if hp==0 or hp>=0x8000 or qhp==0 or qhp>=0x8000 then return end
 local old=music_read(p+0x66,2)
 if old~=999 then
  if score_writes>=512 then pause.failure="score-write-budget";return end
  score_writes=score_writes+1
  local adjacent=music_read(p+0x68,4)
  memory.write_u16_le(p+0x66-0x02000000,999,"EWRAM")
  assert(music_read(p+0x66,2)==999 and music_read(p+0x64,2)==hp and music_read(q+0x64,2)==qhp and music_read(p+0x68,4)==adjacent,"isolated score write")
  assert(score_file:write(string.format("write=%d core=%d round=%d progress=%d stage=%d p1=%08X p2=%08X address=%08X width=2 before=%d after=999 hp=%d qhp=%d cpu=%d\n",
   score_writes,emu.framecount(),campaign_round,progress,physical,p,q,p+0x66,old,hp,qhp,music_read(q+0x11,1))));score_file:flush()
 end
 if emu.framecount()%120==0 and campaign_samples<500 then
  campaign_samples=campaign_samples+1
  assert(music_file:write(string.format("campaign core=%d round=%d progress=%d stage=%d flags=%02X mode=%d difficulty=%d p1=%08X p2=%08X p1id=%d p2id=%d hp=%d qhp=%d score=%d callback=%08X qcallback=%08X\n",
   emu.framecount(),campaign_round,progress,physical,music_read(0x0300232A,1),mode,music_read(0x0300231F,1),p,q,music_read(p+0x11,1),music_read(q+0x11,1),hp,qhp,music_read(p+0x66,2),music_read(p,4),music_read(q,4))));music_file:flush()
 end
end
music_hook(0x0808B694,"campaign-cpu11-selection",function(r,label)music_log(label,r,string.format("progress=%d stage=%d flags=%02X cpu=%d",music_read(0x0300232E,1),music_read(0x0300231E,1),music_read(0x0300232A,1),music_read(0x0300231C,1)))end)
]=]
probe=replace(probe,'local function music_contact(keys,stage,mode)',campaign..'local function music_contact(keys,stage,mode)')
probe=replace(probe,'chosen=target==0x6C and 5 or target==0x6D and 3 or (unlock&0x20)~=0 and 12 or (unlock&0x10)~=0 and 11 or nil','chosen=0')
probe=replace(probe,'source_categories[id+1]==category and','source_categories[id+1]==category and id==11 and side==1 and r.R4==music_read(0x030048A0,4) and')
probe=replace(probe,'if pause.phase=="waiting" then music_contact(keys,stage,mode);return end','if pause.phase=="waiting" then campaign_input(stage,mode);return end')
probe=replace(probe,'local limit=math.min(userdata.get("frames") or 24000,24000)','local limit=math.min(userdata.get("frames") or 60000,60000)')
probe=replace(probe,'hook_count=16 per_label_limit=32 max_event_rows=576','hook_count=17 per_label_limit=32 max_event_rows=608')
probe=replace(probe,'music_log(label,r);music_lifetime_finish()','music_log(label,r);score_file:close();music_lifetime_finish()')
local result_before=[=[
 elseif stage=="result" then
  local age=emu.framecount()-result_frame
  if label_seen and not first_visible_frame then first_visible_frame=emu.framecount();capture("result-first-label") end
  if mode==8 then
   if age>=120 and not result_120 then result_120=true;capture("result-plus120") end
   if age>=300 and not result_300 then result_300=true;capture("result-plus300") end
   if result_300 and label_seen then outcome="result-label-observed" end
  else
   capture("result-exited");outcome=label_seen and "result-label-observed-early-exit" or "failure:result-exited-before-label"
  end
 end
]=]
local result_after=[=[
 elseif stage=="result" then
  if mode==8 or mode==5 or mode==6 then pulse("A",frame)
  elseif mode==7 then
   campaign_round=campaign_round+1
   objects,drawn={},{};label_seen,last_seen=false,false
   result_frame,first_visible_frame=nil,nil;result_120,result_300=false,false
   capture("battle-enter");state("battle",frame)
  elseif mode==9 then fail("campaign-continue")
  elseif mode==3 then fail("campaign-returned-title") end
 end
]=]
local anchor='assert(load("local music_pause_observe\\n"..telemetry..policy..source,"@reviewed-evolution-music-pause","t",_ENV))()'
local edits='source=replace(source,'..string.format("%q",result_before)..','..string.format("%q",result_after)..')\n'
 ..'source=replace(source,\'local function capture(name)\',\'local function capture(name)\\n name="round"..campaign_round.."-"..name\')\n'
 ..'source=replace(source,\'music_lifetime_finish()\\nlocal f=assert(io.open(out.."/result-done.txt","w"));\',\'score_file:close()\\nmusic_lifetime_finish()\\nlocal f=assert(io.open(out.."/result-done.txt","w"));\')\n'
probe=replace(probe,anchor,edits..anchor)
assert(load(probe,"@reviewed-evolution-music-campaign-wrapper","t",_ENV))()
