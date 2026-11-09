-- Bounded development observer. CPU hooks retain facts; outer frames export captures.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"fresh isolated output required")
local PROBE="D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C"
assert(emu.getsystemid()=="GBA" and userdata.get("probe_sha256")==PROBE,"development probe pin required")
assert(userdata.get("score_authorization")=="user-approved-development-score999","score approval required")
assert(userdata.get("boss_authorization")=="user-approved-development-boss-once-per-stage","boss approval required")
local initial=emu.framecount()
local pending,seen,ring,last,write_ledger={}, {}, {}, {}, {}
local serial,captures,score_writes,boss_writes=0,0,0,0
local consumed={}
local outcome,scene,root5,restored,activation,hit_pre,hit
local boss_checkpoint=false
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x08800000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d) elseif n==2 then return memory.read_u16_le(o,d) end
 return memory.read_u32_le(o,d)
end
local function word(a)return read(a,2)end
local function byte(a)return read(a,1)end
local function positive(v)return v>0 and v<0x8000 end
local function dead(v)return v==0 or v>=0x8000 end
local function active_header(p)
 return p>=0x02010000 and p<=0x02010000+51*0x118 and (p-0x02010000)%0x118==0 and word(p+0x10)&2~=0
end
local function active(p)return active_header(p-0x18)end
local function task(global,callback)
 local p=read(global,4)
 return active_header(p) and read(p,4)==callback
end
local function pair(boss)
 local p,q=read(0x0300489C,4),read(0x030048A0,4)
 if not active(p) or not active(q) or p==q then return end
 if word(p+4)%16~=0 or byte(p+0x10)~=0 or byte(p+0x11)~=0
  or read(p+0x14,4)~=p or read(q+0x14,4)~=q
  or read(p+0x18,4)~=q or byte(q+0x10)~=1 or read(q+0x18,4)~=p then return end
 if boss then
  local stage=byte(0x0300231E)
  local kind,qp1,qp0,ap1,ap0
  if stage==7 then kind,qp1,qp0,ap1,ap0=3,0x0834DFE0,0x0834E27C,0x08341C00,0x08341E70
  elseif stage==11 then kind,qp1,qp0,ap1,ap0=6,0x085D0000,0x085D1000,0x085D029C,0x085D1100
  else return end
  local a=read(0x03004D3C,4)
  if word(q+4)%16~=3 or byte(q+0x11)~=15 or not active(a) or a==p or a==q
   or word(a+4)%16~=kind or read(q+0x28,4)~=a or read(a+0x28,4)~=q or read(a+0x18,4)~=p
   or read(q+0xF0,4)~=qp1 or read(q+0xF4,4)~=qp0
   or read(a+0xF0,4)~=ap1 or read(a+0xF4,4)~=ap0 then return end
 end
 return p,q
end
local function live()
 local stage=byte(0x0300231E)
 local kind=(stage==7 or stage==11) and 2 or 0
 return word(0x03002310)==7 and word(0x03004502)==kind and byte(0x03004529)&7==0
  and task(0x03004510,0x08374FF4) and task(0x03004514,0x083735BC)
end
local function regs()
 local r={};for k,v in pairs(emu.getregisters())do r[k]=v end;return r
end
local function journal(kind,detail,r)
 serial=serial+1
 ring[(serial-1)%256+1]=string.format("seq=%d core=%d kind=%s %s",serial,emu.framecount(),kind,detail or "")
 return r or regs()
end
local function queue(name,detail,r)
 if seen[name] then return end
 seen[name]=true
 pending[#pending+1]={name=name,detail=detail or "",r=r or regs(),frame=emu.framecount(),timing=r and "before-instruction" or "outer-frame-boundary"}
end
local function fail(name,detail,r)
 if outcome then return end
 outcome="failure:"..name;queue(name,detail,r)
 -- Scalar first-failure evidence must survive a core stall before the next frame.
 local f=assert(io.open(out.."/shoot-entry-first-failure.txt","w"))
 f:write(string.format("outcome=%s core=%d timing=%s detail=%s\n",outcome,emu.framecount(),r and "before-instruction" or "outer-frame-boundary",detail or ""))
 f:write(string.format("mode=%d stage=%d difficulty=%d progress=%04X FIRST=%08X SECOND=%08X flags=%04X\n",word(0x03002310),byte(0x0300231E),byte(0x0300231F),word(0x0300232A),read(0x0300489C,4),read(0x030048A0,4),word(0x0300450A)))
 for k,v in pairs(r or regs())do f:write(string.format("reg %s=%08X\n",k,v))end
 for n=math.max(1,serial-255),serial do f:write(ring[(n-1)%256+1].."\n")end
 f:close()
end
local function hook(a,name,fn)
 event.on_bus_exec(function()fn(regs(),a)end,a,"shoot-entry-"..name)
end
local function state()
 local p,q=read(0x0300489C,4),read(0x030048A0,4)
 return string.format("mode=%d stage=%d difficulty=%d progress=%04X flags=%04X FIRST=%08X SECOND=%08X P1HP=%d P2HP=%d fighter=%d base=%d input_task=%08X battle_task=%08X",word(0x03002310),byte(0x0300231E),byte(0x0300231F),word(0x0300232A),word(0x0300450A),p,q,word(p+0x64),word(q+0x64),byte(p+0x11),word(p+8)>>8&1,read(0x03004510,4),read(0x03004514,4))
end
local function write_word(a,value,kind,p,q,r)
 local before=word(a)
 local hp,score,left,right=word(p+0x64),word(p+0x66),word(a-2),word(a+2)
 local entry=string.format("core=%d kind=%s address=%08X bytes=2 before=%d requested=%d stage=%d FIRST=%08X SECOND=%08X P1HP=%d P1score_before=%d neighbor_left=%d neighbor_right=%d",emu.framecount(),kind,a,before,value,byte(0x0300231E),p,q,hp,score,left,right)
 local index=#write_ledger+1;write_ledger[index]=entry.." verified=false"
 memory.write_u16_le(a-0x02000000,value,"EWRAM")
 assert(word(a)==value and word(p+0x64)==hp and word(a-2)==left and word(a+2)==right,"authorized WORD and adjacent invariants")
 if kind=="boss" then assert(word(p+0x66)==score,"player score preserved")end
 write_ledger[index]=entry.." after="..word(a).." verified=true"
 journal("authorized-write",entry,r)
 queue(kind=="boss" and "stage7-boss-hp1" or "first-score999",state(),r)
end
hook(0x08373638,"postcollision-preHUD",function(r)
 if outcome or not live() then return end
 local stage=byte(0x0300231E)
 local p,q=pair(stage==7 or stage==11)
 if not p then queue("typed-owner-refusal",state(),r);return end
 if not positive(word(p+0x64)) or byte(0x0300231F)~=2 then return end
 if not seen["first-battle"] then queue("first-battle",state(),r)end
 if stage<=10 and stage~=7 and word(q+4)%16==1 and positive(word(q+0x64)) and word(p+0x66)~=999 then
  score_writes=score_writes+1;write_word(p+0x66,999,"score",p,q,r)
 elseif stage==7 and not consumed[stage] and positive(word(q+0x64)) and word(q+0x64)>1 then
  consumed[stage]=true -- Consume before write, including failures; never rearm on Continue.
  boss_writes=boss_writes+1;write_word(q+0x64,1,"boss",p,q,r)
 end
end)
hook(0x0836E5E4,"boss-damage-pre",function(r)
 local p,q=pair(true)
 if consumed[7] and byte(0x0300231E)==7 and p and r.R4==p and r.R5==q
  and positive(word(p+0x64)) and word(q+0x64)==1 and dead(r.R8&0xFFFF) then
  hit_pre={first=p,second=q,hp=word(p+0x64),after=r.R8&0xFFFF,frame=emu.framecount()}
  queue("boss-hit-pre",string.format("actual_attacker=%08X victim=%08X before=1 computed=%04X damage=%d %s",r.R4,r.R5,r.R8&0xFFFF,r.R0,state()),r)
 end
end)
hook(0x0836E5E8,"boss-damage-post",function(r)
 if hit_pre and emu.framecount()==hit_pre.frame and r.R4==hit_pre.first and r.R5==hit_pre.second
  and word(r.R5+0x64)==hit_pre.after and positive(word(r.R4+0x64)) then
  hit=hit_pre;hit_pre=nil;queue("boss-hit-post",state(),r)
 end
end)
hook(0x083736B0,"root5",function(r)
 local p,q=pair(true)
 if p and hit and hit.first==p and hit.second==q and byte(0x0300231E)==7
  and positive(word(p+0x64)) and dead(word(q+0x64)) and consumed[7] then
  root5={hp=word(p+0x64),first=p,second=q};queue("healthy-root5",state(),r)
 end
end)
hook(0x08373688,"root4",function(r)queue("root4-loss",state(),r)end)
hook(0x0833FD04,"case5-predicate",function(r)
 local stage,diff,progress=byte(0x0300231E),byte(0x0300231F),word(0x0300232A)
 local eligible=stage~=11 and (diff==3 or (diff~=0 and progress&0x400==0))
 queue("case5-predicate",state().." eligible="..tostring(eligible),r)
 if stage==7 and not eligible then fail("case5-ineligible",state(),r)end
end)
hook(0x0833FD08,"case5-selected",function(r)queue("case5-selected",string.format("selected=%08X %s",r.R8,state()),r)end)
hook(0x085C8000,"scene-entry",function(r)queue("scene-entry",state(),r)end)
hook(0x085C8070,"saved-health",function(r)
 scene={owner=r.R4,hp=r.R0,first=r.R5}
 queue("scene-saved-health",string.format("owner=%08X saved=%d %s",scene.owner,scene.hp,state()),r)
end)
hook(0x085C853C,"initializer-call",function(r)queue("initializer-call",state(),r)end)
hook(0x085C8540,"initializer-return",function(r)queue("initializer-return",state(),r)end)
hook(0x085C8B2C,"saved-health-restore",function(r)
 restored={owner=r.R4,hp=r.R0};queue("saved-health-restore",string.format("owner=%08X restored=%d %s",r.R4,r.R0,state()),r)
end)
hook(0x085C8D50,"activation-tail",function(r)
 activation={owner=r.R4};queue("activation-tail",state(),r)
end)
local function producer(a,base,count)
 hook(a,"producer-"..string.format("%X",a),function(r)
  local i=(r.R1-base)/20
  local actor=read(r.R1,4);local presentation=actor+0xAC
  local detail=string.format("pc=%08X dst=%08X index=%g count=%d type=%X B=%08X source_type=%X actor=%08X selector_A0=%X event=%X command_index=%X command_count=%X command_base=%X command=%X A=%X event_B=%X P1=%X",a,r.R1,i,byte(count),r.R0,r.R4,word(r.R4),actor,word(actor+0xA0),word(presentation+0x0E),word(presentation+0x1A),word(presentation+0x1C),read(presentation+0x20,4),read(presentation+0x24,4),read(presentation+0x28,4),read(presentation+0x2C,4),read(presentation+0x44,4))
  journal("producer",detail,r);last[r.R1]={type=r.R0,frame=emu.framecount(),detail=detail}
  if r.R0<0 or r.R0>0x1B then fail("first-invalid-producer",detail,r)
  elseif i<0 or i>=12 or i%1~=0 or i~=byte(count)then fail("producer-geometry",detail,r)end
 end)
end
producer(0x08353C70,0x030049B8,0x03004C4E)
producer(0x08353D24,0x030048C8,0x03004C4D)
producer(0x083776E4,0x030048C8,0x03004C4D)
hook(0x0836E370,"overlap",function(r)
 local origin=last[r.R4]
 local detail=string.format("record=%08X type=%X origin=%s",r.R4,r.R0,origin and origin.detail or "unobserved")
 journal("overlap",detail,r)
 if r.R0<0 or r.R0>0x1B then fail("invalid-overlap-type",detail,r)
 elseif origin and origin.frame==emu.framecount() and origin.type~=r.R0 then fail("producer-overwrite",detail,r)end
end)
hook(0x0836EBA4,"dispatch-target",function(r)
 if r.R1<0 or r.R1>34 or r.R1%2~=0 or r.R8~=0x0836EBA8 or r.R9~=read(0x0836EBA8+r.R1*2,4)then
  fail("invalid-dispatch-target",string.format("index=%X table=%08X target=%08X",r.R1,r.R8,r.R9),r)
 end
end)
for _,base in ipairs({0x030048C8,0x030049B8})do
 for slot=0,11 do
  local a=base+slot*20+4
  event.on_bus_write(function(address,value,flags)
   journal("list-type-write",string.format("address=%08X value=%X flags=%X old=%X",address,value,flags,word(a)))
  end,a,"shoot-entry-list-type-"..string.format("%X",a))
 end
end
event.on_bus_write(function(a,v,f)
 journal("scratch-write",string.format("address=%08X value=%X flags=%X old=%X",a,v,f,word(0x03004D20)))
end,0x03004D20,"shoot-entry-scratch-writer")
hook(0x0836EB58,"scratch-consumer",function(r)
 local t=word(0x03004D20);journal("scratch-read",string.format("actual_type=%X",t),r)
 if t>0x1B then fail("invalid-scratch-type",string.format("type=%X",t),r)end
end)
hook(0x08354FB8,"generic-grab",function(r)
 queue("generic-grab-event48",string.format("event=%X presentation=%08X",read(r.R13,4),read(r.R13+8,4)),r)
end)
for _,a in ipairs({0x080128A4,0x080128BC})do
 hook(a,"frame-consumer-"..string.format("%X",a),function(r)
  if r.R3==0x48 and read(r.R5+0x44,4)==0x085D0000 then
   local frame=a==0x080128A4 and read(r.R1+4,4) or r.R1
   queue("upper-event48-"..string.format("%X",a),string.format("table=%08X frame_pointer=%08X presentation=%08X",r.R1,frame,r.R5),r)
   if frame==0 then fail("upper-event48-null-frame",string.format("consumer=%08X presentation=%08X",a,r.R5),r)end
  end
 end)
end
hook(0x085CC1C0,"8EF3-refusal",function(r)
 queue("8EF3-refusal",string.format("targetY=%04X lowerX=%04X %s",word(r.R4+0xA2),word(r.R4+0x34),state()),r)
end)
local function log(s)local f=assert(io.open(out.."/shoot-entry-trace.txt","a"));f:write(s.."\n");f:close()end
local function capture(e)
 captures=captures+1
 local name=string.format("%02d-%s",captures,e.name)
 log(string.format("capture=%s observed_core=%d export_core=%d registers=%s memory=outer-frame-boundary %s",name,e.frame,emu.framecount(),e.timing,e.detail))
 for k,v in pairs(e.r)do log(string.format("capture=%s reg %s=%08X",name,k,v))end
 for _,v in ipairs({{"iwram","IWRAM",0,0x8000},{"ewram","EWRAM",0,0x40000},{"vram","VRAM",0,0x18000},{"palette","PALRAM",0,0x400},{"oam","OAM",0,0x400},{"display","System Bus",0x04000000,0x60}})do
  local f=assert(io.open(out.."/"..name.."-"..v[1]..".bin","wb"));f:write(memory.read_bytes_as_binary_string(v[3],v[4],v[2]));f:close()
 end
 client.screenshot(out.."/"..name..".png")
end
local function checkpoint(name)
 local ok,saved=pcall(savestate.save,out.."/"..name..".State",true)
 if not ok or saved~=true then fail("checkpoint-save-failed",name..":"..tostring(saved));return false end
 local f=assert(io.open(out.."/"..name..".txt","w"))
 f:write(string.format("core=%d input_relative=%d stage7_consumed=%s %s\n",emu.framecount(),emu.framecount()-initial,tostring(consumed[7]==true),state()));f:close()
 return true
end
local function flush()
 for _,entry in ipairs(write_ledger)do
  local f=assert(io.open(out.."/shoot-entry-writes.txt","a"));f:write(entry.."\n");f:close()
 end;write_ledger={}
 if boss_writes==1 and not boss_checkpoint and not outcome then
  boss_checkpoint=true
  local p,q=pair(true)
  if p and byte(0x0300231E)==7 and live() and positive(word(p+0x64)) and word(q+0x64)==1 then
   if checkpoint("stage7-hp1") then queue("stage7-checkpoint",state())end
  else fail("stage7-checkpoint-contract",state())end
 end
 if activation and not outcome then
  local p,q=pair(true)
  if scene and not active(scene.owner) and p and root5 and restored and positive(scene.hp)
   and root5.hp==scene.hp and restored.hp==scene.hp and restored.owner==scene.owner
   and activation.owner==scene.owner and p==scene.first and p==root5.first
   and word(scene.owner+0x54)==scene.hp and word(p+0x64)==scene.hp and live()
   and byte(0x0300231E)==11 and word(0x0300450A)&4~=0 then
   if checkpoint("healthy-activation") then outcome="healthy-native-shoot-activation";queue("healthy-activation",state())end
  else fail("activation-contract",state())end
 end
 for _,e in ipairs(pending)do capture(e)end;pending={}
end
local function finish()
 flush()
 local failure_saved=false
 if outcome and outcome:match("^failure:") then
  local ok,saved=pcall(checkpoint,"failure-observed");failure_saved=ok and saved==true
 end
 for n=math.max(1,serial-255),serial do log(ring[(n-1)%256+1])end
 outcome=outcome or "bounded-no-activation"
 log("failure_checkpoint_saved="..tostring(failure_saved))
 log(string.format("summary outcome=%s score_writes=%d boss_writes=%d stage7_consumed=%s stage11_writes=0 initial_core=%d final_core=%d %s",outcome,score_writes,boss_writes,tostring(consumed[7]==true),initial,emu.framecount(),state()))
 local f=assert(io.open(out.."/shoot-entry-done.txt","w"));f:write(outcome);f:close()
 return outcome
end
log("probe_sha256_host_pin="..PROBE.." input_profile=approach-jump-no-up captures=queued-outer-frame authorized_writes=ordinary-scoreWORD999,stage7-bossWORD1-once stage11_writes=disabled")
return {flush=flush,finish=finish,stopped=function()return outcome~=nil end,read=read,task=task,pair=pair,live=live,queue=queue,fail=fail,state=state}
