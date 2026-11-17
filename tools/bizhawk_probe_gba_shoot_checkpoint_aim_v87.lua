-- Continue the exact current healthy Shoot checkpoint through ordinary inputs.
local ROM="5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC"
local APPROVAL="user-approved-development-stage11-boss-hp1-once"
local SOURCE_CORE,AIM_FRAMES,MAX_FRAMES=89405,1800,8000
local SUCCESS="shoot-checkpoint-aim-terminal-results-title"
local out,ref=assert(userdata.get("output")),assert(userdata.get("checkpoint_dir"))
assert(out:match("^W:/build/[%w%-%_/]+$") and ref:match("^W:/build/[%w%-%_/]+$") and ref~=out)
assert(emu.getsystemid()=="GBA" and userdata.get("probe_sha256")==ROM,"exact current checkpoint ROM")
assert(userdata.get("stage11_boss_authorization")==APPROVAL,"explicit one-shot stage11 boss approval")
local keys={A=false,B=false,Select=false,Start=false,Right=false,Left=false,Up=false,Down=false,R=false,L=false,Power=false}
local regions={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},
               {"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local log,observer
local eligible_b=0
local function release()for k in pairs(keys)do keys[k]=false end end
local function file(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));assert(f:close());return s
end
local function write(name,s)
 local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(s));assert(f:close())
end
local function replaced(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique replay substitution: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function without(s,first,last)
 local a,b=s:find(first,1,true)
 local c,d=s:find(last,1,true)
 assert(a and c and b<c and not s:find(first,b+1,true) and not s:find(last,d+1,true),"unique frozen replay span")
 return s:sub(1,a-1)..s:sub(c)
end
local function decision(p,q)
 local read=observer.read
 local function w(a)return read(a,2)end
 local function signed(v)return v<0x8000 and v or v-0x10000 end
 local cb,upper=read(p,4),read(q,4)
 local freeze,air=w(p+0x76),w(p+6)&1
 local dx=signed(w(q+0x34))-signed(w(p+0x34))
 local dy=signed(w(q+0x36))-signed(w(p+0x36))
 local event=w(q+0xBA)
 local right=w(p+0xB4)&0x4000~=0
 local held=w(p+0x2C)
 local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and air==0 and freeze==0
 local forward=right and dx or -dx
 local target_event=event==1 or event==4 or event==5
 local fresh=held&0x80==0
 local horizontal=forward>=96 and forward<=384
 local vertical=dy>=128 and dy<=256
 local relative=emu.framecount()-SOURCE_CORE
 local reason="eligible"
 if relative>=AIM_FRAMES then reason="aim-bound"
 elseif not ready then reason="ready"
 elseif math.abs(dx)>=96 and (dx>0)~=right then
  if dx>0 and held&2==0 then keys.Right=true
  elseif dx<0 and held&8==0 then keys.Left=true end
  reason=(keys.Right or keys.Left) and "turn-edge" or "turn-release"
 elseif not fresh then reason="held-B"
 elseif not target_event then reason="upper-event"
 elseif not horizontal then reason="horizontal"
 elseif not vertical then reason="vertical" end
 local eligible=reason=="eligible"
 if eligible then eligible_b=eligible_b+1 end
 assert(log:write(string.format(
  "core=%d relative=%d p_cb=%08X q_cb=%08X P1HP=%d P2HP=%d dx=%d dy=%d forward=%d q_dx=%d q_dy=%d freeze=%d air=%d upper_event=%d facing=%s held=%04X ready=%s fresh=%s horizontal=%s vertical=%s event_ok=%s Left=%s Right=%s B_candidate=%s reason=%s\n",
  emu.framecount(),relative,cb,upper,w(p+0x64),w(q+0x64),dx,dy,forward,
  signed(w(q+0x34))-signed(w(q+0x38)),signed(w(q+0x36))-signed(w(q+0x3A)),freeze,air,event,
  right and "right" or "left",held,tostring(ready),tostring(fresh),tostring(horizontal),tostring(vertical),
  tostring(target_event),tostring(keys.Left),tostring(keys.Right),tostring(eligible),reason)))
 assert(log:flush())
 return eligible
end
local function load_observer()
 local s=file("W:/tools/bizhawk_gba_shoot_entry_observer.lua"):gsub("\r\n","\n")
 s=replaced(s,"D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C",ROM)
 s=replaced(s,"0x08800000","0x09000000")
 s=without(s,'assert(userdata.get("score_authorization")','local initial=emu.framecount()')
 s=without(s,"local function write_word(","local function producer(")
 s=without(s," if boss_writes==1 and not boss_checkpoint and not outcome then"," for _,e in ipairs(pending)do capture(e)end;pending={}")
 s=replaced(s,"local function finish()","local function finish(success)")
 s=replaced(s,'outcome=outcome or "bounded-no-activation"','outcome=outcome or success or "bounded-shoot-checkpoint"')
 s=replaced(s,' input_profile=approach-jump-no-up captures=queued-outer-frame authorized_writes=ordinary-scoreWORD999,stage7-bossWORD1-once stage11_writes=disabled',
  ' input_profile=checkpoint-mirrored-aim captures=queued-outer-frame authorized_writes=stage11-boss-only-outside-observer')
 assert(not s:find("memory.write",1,true),"observer has no guest-write path")
 return assert(load(s,"@shoot-checkpoint-readonly-observer","t",_ENV))()
end
local function replay(attach,activation,select_tail,tail_outcome)
 observer=load_observer()
 local read=observer.read
 local function w(a)return read(a,2)end
 local p,q=observer.pair(true)
 assert(p==0x02011710 and q==0x02011828 and observer.live() and read(0x03004D3C,4)==0x02011940
  and read(0x0300231E,1)==11 and w(0x0300450A)==6 and w(p+0x64)==8 and w(q+0x64)==37,
  "exact healthy checkpoint owners and HP")
 assert(w(p+0x2C)==0 and w(p+0x2E)==0 and w(0x03001302)==0 and w(0x03001306)==0,"restored inputs are released")
 attach(observer)
 activation(p,q)
 observer.queue("checkpoint-before",observer.state())
 observer.flush()
 log=assert(io.open(out.."/shoot-checkpoint-aim-decisions.txt","wb"))
 assert(log:write(string.format("source_core=%d aim_frame_cap=%d total_frame_cap=%d\n",SOURCE_CORE,AIM_FRAMES,MAX_FRAMES)))
 client.speedmode(800)
 for frame=1,MAX_FRAMES do
  if observer.stopped() or tail_outcome() then break end
  release()
  local mode=w(0x03002310)
  if mode~=7 and mode~=8 and mode~=11 and mode~=20 and mode~=3 then
   observer.fail("checkpoint-invalid-mode",observer.state());break
  end
  assert(select_tail(keys,mode),"healthy tail active")
  if observer.stopped()then break end
  joypad.set(keys);emu.frameadvance()
  assert(emu.framecount()==SOURCE_CORE+frame,"one advance per input decision")
  observer.flush()
  if frame==AIM_FRAMES and eligible_b==0 and not observer.stopped()then
   observer.fail("bounded-no-eligible-shot",observer.state());break
  end
 end
 if not observer.stopped() and not tail_outcome()then observer.fail("bounded-no-terminal",observer.state())end
 assert(log:close());log=nil
 return observer.finish(tail_outcome())
end
local function restore()
 assert(file(ref.."/healthy-activation.txt"):match(
  "^core=89405 input_relative=89404 stage7_consumed=true mode=7 stage=11 "))
 assert(file(ref.."/healthy-activation.State"):sub(1,4)=="PK\003\004")
 assert(savestate.load(ref.."/healthy-activation.State",true)==true,"checkpoint load")
 userdata.clear()
 for k,v in pairs({output=out,checkpoint_dir=ref,probe_sha256=ROM,stage11_boss_authorization=APPROVAL})do
  userdata.set(k,v);assert(userdata.get(k)==v)
 end
 local function exact()
  assert(emu.framecount()==SOURCE_CORE,"restored checkpoint frame")
  for _,part in ipairs(regions)do
   local name,domain,size=table.unpack(part)
   assert(memory.getmemorydomainsize(domain)==size)
   local expected=file(ref.."/41-healthy-activation-"..name..".bin")
   assert(#expected==size and memory.read_bytes_as_binary_string(0,size,domain)==expected,"restored "..name)
  end
 end
 exact();assert(savestate.save(out.."/restored.State",true)==true);exact()
 assert(memory.getmemorydomainsize("ROM")==0x1000000)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
end
local function run()
 restore()
 local s=file("W:/tools/bizhawk_probe_campaign_wholeplay_v86.lua"):gsub("\r\n","\n")
 s=replaced(s,"574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76",ROM)
 s=replaced(s,'local EXPECTED="campaign-shoot-terminal-results-title"',"local EXPECTED="..string.format("%q",SUCCESS))
 local menu=' elseif (which==8 or which==11)'
 s=without(s,"  local cb=read(p1,4)",menu)
 s=replaced(s,menu,"  if checkpoint_aim_decision(p1,p2) then keys.B=consumed or hp1()end\n"..menu)
 s=replaced(s," if which==7 and not hit then",[[ if not hit and which~=7 then
  require_fact(false,"lost-live-mode-before-hit")
  return true
 end
 if which==7 and not hit then]])
 local start=assert(s:find("local function finish(outcome)",1,true))
 s=s:sub(1,start-1).."return replay_checkpoint(attach,activation,select_tail,tail_outcome)\n"
 local env=setmetatable({checkpoint_aim_decision=decision,replay_checkpoint=replay},{__index=_ENV})
 return assert(load(s,"@shoot-checkpoint-frozen-terminal-tail","t",env))()
end
local ok,result=pcall(run)
release();joypad.set(keys)
if not ok then
 if log then pcall(function()log:close()end)end
 write("shoot-checkpoint-aim-error.txt",tostring(result).."\n")
 if observer then pcall(function()observer.fail("checkpoint-error",tostring(result));observer.finish()end)end
 result="failure:script-error"
end
write("shoot-checkpoint-aim-done.txt",result.."\n")
client.exit()

