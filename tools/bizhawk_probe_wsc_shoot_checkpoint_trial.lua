-- Genuine healthy Shoot checkpoint; approved stage11 HP1 once and actual terminal evidence.
assert(userdata.get("shoot_boss_hp1_approval")=="user-approved-original-stage11-boss-once",
 "explicit original stage11 boss HP1 approval required")
local function read(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s:gsub("\r\n","\n")
end
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a and not s:find(old,b+1,true),"unique frozen trial anchor: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local base=read("W:/tools/bizhawk_replay_wsc_shoot_checkpoint.lua")
base=once(base,'{"output","checkpoint_dir","frames","source_sha256","callback_order"}',
 '{"output","checkpoint_dir","frames","source_sha256","callback_order","shoot_boss_hp1_approval"}')
base=once(base,'budget<=3000','budget<=6000')
local metadata_begin=assert(base:find('local metadata=read(reference.."/shoot-preactivation.txt")',1,true))
local state_begin=assert(base:find('assert(read(state_path):sub(1,4)',metadata_begin,true))
assert(not base:find('local metadata=read(reference.."/shoot-preactivation.txt")',metadata_begin+1,true)
 and not base:find('assert(read(state_path):sub(1,4)',state_begin+1,true))
base=base:sub(1,metadata_begin-1)..[=[
local metadata=read(reference.."/healthy-shoot.txt")
local _,count=metadata:gsub("capture_core=%d+","");assert(count==1)
local captured=assert(tonumber(metadata:match("capture_core=(%d+)")))
local scene_payload=assert(tonumber(metadata:match("scene_payload=(%x+)"),16))
local saved_HP=assert(tonumber(metadata:match("saved_HP=(%d+)")))
assert(saved_HP>0 and saved_HP<0x8000,"positive actual saved incoming HP required")
local expected_ram=read(reference.."/healthy-shoot-ram.bin")
local expected_sram=read(reference.."/healthy-shoot-sram.bin")
assert(#expected_ram==0x10000 and #expected_sram==0x8000)
local state_path=reference.."/healthy-shoot.State"
]=]..base:sub(state_begin)
base=once(base,'local function save(name)',[=[
assert(scene_payload>=0x24 and scene_payload<=0x3654 and (scene_payload-0x24)%0x110==0
 and math.floor(memory.read_u16_le(0xC000+scene_payload-6,"RAM")/2)%2==1
 and memory.read_u16_le(0xC000+scene_payload-0xE,"RAM")==0x71F0
 and memory.read_u16_le(0xC000+scene_payload+0x46,"RAM")==saved_HP,"actual retained healthy scene owner")
local function save(name)]=])
-- Reuse the frozen four-hook engine-hit observer without its old driver/cheat.
local old=read("W:/tools/bizhawk_probe_wsc_saved_boss_hp1.lua")
local begin=assert(old:find("local boss,pending,hit,victory=",1,true))
local ending=assert(old:find("local original_dofile=dofile",begin,true))
assert(not old:find("local boss,pending,hit,victory=",begin+1,true)
 and not old:find("local original_dofile=dofile",ending+1,true))
local observer=old:sub(begin,ending-1)
observer=once(observer,'memory.read_u8(0x5C,"SRAM")~=7','memory.read_u8(0x5C,"SRAM")~=11')
observer=once(observer,' return first,second\nend',[=[
 if mainmemory.read_u8(a+0x11)~=0 or ram(b+0xC6)~=0 or ram(b+0xC8)~=0x2F41 or ram(b+0xCA)~=0xBC
  or ram(b+0xCC)~=0 or ram(b+0xCE)~=0x25F8 or ram(b+0xD0)~=0xBD then return end
 return first,second
end]=])
observer=once(observer,'  assert(not pending,"unpaired prior boss damage")',[=[
  local aux=ram(0xC000+second+0x1C)
  if not valid(aux) or aux==first or aux==second or not active(aux) then return end
  local body=0xC000+aux
  if ram(body+4)%16~=6 or ram(body+0x1C)~=second or ram(body+0x14)~=first
   or ram(body+0xC6)~=0 or ram(body+0xC8)~=0x2D73 or ram(body+0xCA)~=0xBB then return end
  assert(not pending,"unpaired prior boss damage")]=])
observer=once(observer,'  pending.direct_first=r.IX==first','  pending.aux=aux\n  pending.direct_first=r.IX==first')
observer=once(observer,'  local hp=ram(0xC000+p.second+0x50)',[=[
  local first,second=pair()
  assert(first==p.first and second==p.second and ram(0xC000+p.second+0x1C)==p.aux,
   "same stage11 upper/aux owner through actual SUB")
  local hp=ram(0xC000+p.second+0x50)]=])
observer=observer..[=[
local terminal_seen,terminal_linked,terminal_pairs=false,false,0
local di
local function ready()
 if not di or not terminal_linked or not evidence_ready()then return false end
 local s=di.status()
 return s.terminal_observed and s.paired_reads>terminal_pairs and not s.pending
end
return {
 enable=function(module,irq)
  assert(not boss);boss=module;di=irq;install()
  pin(0x773650,{0xB8,0x00,0x0C,0x8E,0xD8,0xB8,0x00,0x10,0x8E,0xC0})
  event.on_bus_write(function(address)
   if finalized or terminal_seen then return end
   local r=site(0x773650,address)
   if memory.read_u8(0x5C,"SRAM")~=11 then return end
   terminal_seen=true;terminal_linked=evidence_ready();terminal_pairs=di.status().paired_reads
   log(string.format("stage11_terminal frame=%d PS:PC=%04X:%04X linked_actual_hit_root5=%s DI_pairs_at_entry=%d",
    emu.framecount(),r.PS,r.PC,tostring(terminal_linked),terminal_pairs))
   snapshot("stage11-terminal")
  end,0x73650,"approved-shoot-terminal","System Bus")
  boss.tick()
 end,
 ready=ready,
 victory=evidence_ready,
 finish=function()
  assert(not pending,"trial ended between actual damage hooks")
  local result=ready();local s=boss.finish();finalized=true
  log(string.format("trial_finished writes=%d actual_lethal_hit=%s native_root5=%s cancelled_root4=%s terminal_linked=%s later_DI_pair=%s",
   s.writes,tostring(hit~=nil),tostring(victory),tostring(cancelled),tostring(terminal_linked),tostring(result)))
  return result
 end
}
]=]
local out=assert(userdata.get("output"))
local environment=setmetatable({},{__index=_ENV})
local evidence=assert(load('local out='..string.format('%q',out)..'\n'..observer,"@stage11-frozen-hit-observer","t",environment))()
local original_dofile=dofile
local di,boundary,completed
local function module(path)
 if path=="W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua"then
  assert(not di);di=original_dofile(path);return di
 end
 assert(path=="W:/tools/bizhawk_observe_wsc_shoot_boundary.lua" and di and not boundary)
 boundary=original_dofile(path)
 return {after_frame=boundary.after_frame,tick=function()
  boundary.tick()
  local boss=original_dofile("W:/tools/bizhawk_wsc_shoot_boss_hp1_once.lua")
  evidence.enable(boss,di)
 end,finish=function()
  local result=boundary.finish();completed=evidence.finish();return result
 end}
end
local steps,stage_exit=0,false
local function step(relative,core,stage,actor,keys)
 steps=steps+1
 local q=memory.read_u16_le(0x65E,"SRAM")
 local upper="upper=invalid"
 if q>=0x24 and q<=0x3654 and (q-0x24)%0x110==0 then
  local a=0xC000+q;local function w(o)return memory.read_u16_le(a+o,"RAM")end
  upper=string.format("upper=%04X callback=%04X:%04X X=%04X Y=%04X eventA4=%04X body_offsetB8=%04X flags4=%04X HP=%04X",q,w(2),w(0),w(0x26),w(0x28),w(0xA4),w(0xB8),w(4),w(0x50))
 end
 local f=assert(io.open(out.."/trial-inputs.txt","a"))
 f:write(string.format("trial relative=%d core=%d stage=%d keys=%s %s %s\n",relative,core,stage,keys,actor,upper));f:close()
 stage_exit=stage~=11
 return evidence.ready()or stage_exit
end
base=once(base,'log("replay_begin core="..captured.." relative="..next_relative.." frames="..budget.." source_records="..#records.." guest_writes=none policy_locals_reconstructed=false approval_modules_loaded=false")',
 'log("trial_begin core="..captured.." frames="..budget.." saved_HP="..saved_HP.." guest_writes=approved_stage11_HP1_once input=source_state_controller")')
local policy_source=read("W:/tools/bizhawk_probe_wsc_healthy_shoot_entry.lua")
local policy_begin=assert(policy_source:find('local hold_jump,previousA,previousB=',1,true))
local policy_end=assert(policy_source:find('local function keytext(keys)',policy_begin,true))
assert(not policy_source:find('local hold_jump,previousA,previousB=',policy_begin+1,true)
 and not policy_source:find('local function keytext(keys)',policy_end+1,true))
local policy=policy_source:sub(policy_begin,policy_end-1)
policy=once(policy,'healthy_hit.ready()','trial_victory()')
policy=once(policy,'memory.read_u8(0x5C,"SRAM")~=7','memory.read_u8(0x5C,"SRAM")~=11')
policy=once(policy,' local p,q=word(0x65C),word(0x65E)',[=[
 if math.floor(word(0x3D8)/4)%2~=1 or not task(word(0x3DE),0x07FA)or not task(word(0x3E0),0x0D0B)then return keys end
 local p,q=word(0x65C),word(0x65E)]=])
local loop_begin=assert(base:find('for i=1,budget do',1,true))
local loop_end=assert(base:find('save("final")',loop_begin,true))
assert(not base:find('for i=1,budget do',loop_begin+1,true)and not base:find('save("final")',loop_end+1,true))
base=base:sub(1,loop_begin-1)..[=[
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function byte(a)return memory.read_u8(a,"RAM")end
local function active(p)return valid(p)and math.floor(ram(0xC000+p-6)/2)%2==1 end
local function positive(v)return v>0 and v<0x8000 end
local function signed(v)return v>=0x8000 and v-0x10000 or v end
local function task(h,callback)return active(h+0x10)and ram(0xC000+h)==callback and ram(0xC000+h+2)==0x4090 end
local buttons={"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
]=]..policy..[=[
for relative=0,budget-1 do
 local keys=choose();previousA,previousB=keys["P1 A"],keys["P1 B"]
 local before=emu.framecount();assert(before==captured+relative)
 joypad.set(keys);emu.frameadvance();assert(emu.framecount()==before+1)
 boundary.after_frame({relative=relative,core_before=before,keys=keys})
 local fields={};for _,name in ipairs(buttons)do fields[#fields+1]=name.."="..tostring(keys[name])end
 if trial_step(relative,emu.framecount(),memory.read_u8(0x5C,"SRAM"),current_actor(),table.concat(fields,";"))then break end
end
]=]..base:sub(loop_end)
local finish_begin=assert(base:find('local matched_exit=',1,true))
local release_begin=assert(base:find('local release={}',finish_begin,true))
assert(not base:find('local matched_exit=',finish_begin+1,true) and not base:find('local release={}',release_begin+1,true))
base=base:sub(1,finish_begin-1)..[=[log("trial_finish frames="..trial_steps().." actual_terminal_chain="..tostring(trial_complete())
 .." terminal="..tostring(irq.terminal_observed).." DI_pairs="..irq.paired_reads.." baseline_equality_not_claimed=true")
]=]..base:sub(release_begin)
base=once(base,'write("done.txt","checkpoint-input-replay-complete")',
 'write("done.txt",trial_complete()and "checkpoint-trial-terminal-observed"or trial_stage_exit()and "checkpoint-trial-failed"or "checkpoint-trial-bounded-complete")')
local run=setmetatable({dofile=module,trial_step=step,trial_victory=evidence.victory,trial_steps=function()return steps end,
 trial_complete=function()return completed==true end,trial_stage_exit=function()return stage_exit end},{__index=_ENV})
return assert(load(base,"@stage11-approved-checkpoint-trial-parent","t",run))()
