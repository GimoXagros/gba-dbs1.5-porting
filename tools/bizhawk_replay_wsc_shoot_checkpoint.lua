-- Replay only recorded final keys from a genuine original-source checkpoint.
-- No old policy, approval-bearing driver, cheat module or guest-write API.
local args={}
for _,key in ipairs({"output","checkpoint_dir","frames","source_sha256","callback_order"})do
 args[key]=assert(userdata.get(key),"missing replay argument: "..key)
end
local out,reference=args.output,args.checkpoint_dir
assert(out:match("^W:/build/[%w%-%_/]+$") and reference:match("^W:/build/[%w%-%_/]+$") and out~=reference)
local budget=assert(tonumber(args.frames));assert(budget%1==0 and budget>=1 and budget<=3000)
assert(args.source_sha256=="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
assert(args.callback_order=="bizhawk2111-rew" and emu.getsystemid()=="WSWAN")
local function read(path)
 local f=assert(io.open(path,"rb"));local data=assert(f:read("*a"));f:close();return data
end
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(data);f:close()
end
local function log(line)
 local f=assert(io.open(out.."/replay.txt","a"));f:write(line.."\n");f:close()
end
for _,name in ipairs({"replay.txt","restored.State","final.State","done.txt","loaded-rom.bin","initial-sram.bin"})do
 local f=io.open(out.."/"..name,"rb");if f then f:close();error("fresh replay output required")end
end
local metadata=read(reference.."/shoot-preactivation.txt")
local captured,next_relative=metadata:match("checkpoint hook_core=%d+ capture_core=(%d+) relative_next=(%d+) bytes=%d+")
captured,next_relative=assert(tonumber(captured)),assert(tonumber(next_relative))
local expected_ram=read(reference.."/shoot-preactivation-ram.bin")
local expected_sram=read(reference.."/shoot-preactivation-sram.bin")
assert(#expected_ram==0x10000 and #expected_sram==0x8000)
local records,exit_core,exit_relative={},nil,nil
local buttons={"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local allowed={};for _,name in ipairs(buttons)do allowed[name]=true end
for line in read(reference.."/shoot-inputs.txt"):gmatch("[^\r\n]+")do
 if line:match("^input ")then
  assert(not exit_core and #records<3000,"record after exit or input limit")
  local relative,before,after,stage,tail=line:match("^input relative=(%d+) core_before=(%d+) core_after=(%d+) stage_after=(%d+) keys=(.+)$")
  assert(tail,"malformed input header")
  local keys,actor=tail:match("^(.-) (payload=.+)$")
  if not keys then keys,actor=tail:match("^(.-) (invalid_payload=.+)$")end
  relative,before,after,stage=tonumber(relative),tonumber(before),tonumber(after),tonumber(stage)
  assert(relative and before and after and stage and keys and actor,"malformed replay record")
  assert(relative==next_relative+#records and before==captured+#records and after==before+1,"noncontiguous replay stream")
  local pressed={};local count=0
  for field in (keys..";"):gmatch("(.-);")do
   local name,value=field:match("^(.+)=(%a+)$")
   assert(name and allowed[name] and pressed[name]==nil and (value=="true"or value=="false"),"invalid key record")
   pressed[name]=value=="true";count=count+1
  end
  assert(count==#buttons,"complete final key table required")
  records[#records+1]={relative=relative,before=before,after=after,stage=stage,keys=pressed,actor=actor}
 elseif line:match("^stage11_exit ")then
  local a,b=line:match("^stage11_exit core=(%d+) relative_next=(%d+)$")
  exit_core,exit_relative=tonumber(a),tonumber(b)
  assert(exit_core and exit_relative and #records>0 and exit_core==records[#records].after
   and exit_relative==records[#records].relative+1 and records[#records].stage~=11,"invalid exit record")
 elseif line~="input_limit_reached=3000 replay_stream_truncated=true"then error("unknown replay record")end
end
assert(budget<=#records,"budget exceeds complete recorded inputs")
local state_path=reference.."/shoot-preactivation.State"
assert(read(state_path):sub(1,4)=="PK\003\004","full checkpoint ZIP required")
for domain,size in pairs({ROM=0x800000,RAM=0x10000,SRAM=0x8000})do assert(memory.getmemorydomainsize(domain)==size)end
write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x800000,"ROM"))
local initial_sram=memory.read_bytes_as_binary_string(0,0x8000,"SRAM")
write("initial-sram.bin",initial_sram)
local authorized=read(out.."/authorized-cartridge-copy.bin")
assert(#authorized==0x8000,"authorized cartridge copy length")
local function boot_byte(data,offset,value)
 return data:sub(1,offset)..string.char(value)..data:sub(offset+2)
end
-- Same complete boot guard as frozen A0AC: exact source stores, no byte masks.
authorized=boot_byte(boot_byte(authorized,0x4E,1),0x73,0)
assert(initial_sram==authorized,"entire actual save after two exact source startup stores")
log("initial_cartridge_copy_exact_after_source_boot=true stores=004E:01,0073:00 initial_core="..emu.framecount())
-- This call executes at the outer Lua boundary, before any callback installation.
assert(savestate.load(state_path,true)==true,"checkpoint load failed")
-- A full state can replace UserBag. Keep only this new replay's explicit args;
-- do not revive the checkpoint's approval token, old output or old frame budget.
userdata.clear()
for key,value in pairs(args)do userdata.set(key,value);assert(userdata.get(key)==value)end
for domain,size in pairs({ROM=0x800000,RAM=0x10000,SRAM=0x8000})do assert(memory.getmemorydomainsize(domain)==size)end
assert(emu.framecount()==captured,"restored core frame mismatch")
assert(memory.read_bytes_as_binary_string(0,0x10000,"RAM")==expected_ram,"restored RAM mismatch")
assert(memory.read_bytes_as_binary_string(0,0x8000,"SRAM")==expected_sram,"restored SRAM mismatch")
assert(memory.read_u8(0x5C,"SRAM")==11 and math.floor(memory.read_u16_le(0x3D8,"SRAM")/4)%2==0,"checkpoint is not preactivation Shoot")
local function save(name)
 local core=emu.framecount()
 local rp=memory.read_bytes_as_binary_string(0,0x10000,"RAM")
 local sp=memory.read_bytes_as_binary_string(0,0x8000,"SRAM")
 local path=out.."/"..name..".State"
 assert(savestate.save(path,true)==true,"replay state export failed")
 local data=read(path);assert(#data>4 and data:sub(1,4)=="PK\003\004","fresh full state export required")
 assert(emu.framecount()==core and memory.read_bytes_as_binary_string(0,0x10000,"RAM")==rp
  and memory.read_bytes_as_binary_string(0,0x8000,"SRAM")==sp,"state export changed guest/frame")
 write(name.."-ram.bin",rp);write(name.."-sram.bin",sp)
 client.screenshot(out.."/"..name..".png")
 log("state_export name="..name.." core="..core.." bytes="..#data)
end
save("restored")
log("replay_begin core="..captured.." relative="..next_relative.." frames="..budget.." source_records="..#records.." guest_writes=none policy_locals_reconstructed=false approval_modules_loaded=false")
log("boundary_attach initializer_checkpoint_HP_write_fallback=inactive activation_loss_jump_hooks=active")
local di=dofile("W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua")
local boundary=dofile("W:/tools/bizhawk_observe_wsc_shoot_boundary.lua");boundary.tick()
local function ram(a)return memory.read_u16_le(a,"RAM")end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function current_actor()
 local p=memory.read_u16_le(0x65C,"SRAM")
 if not valid(p) or ram(0xC000+p+4)%16~=0 or memory.read_u8(0xC000+p+0x10,"RAM")~=0 then p=0 end
 if not valid(p)then return "invalid_payload="..p end
 local a=0xC000+p
 return string.format("payload=%04X callback=%04X:%04X kind=%d index10=%d id11=%d link14=%04X owner16=%04X HP=%04X held=%04X edge=%04X X=%04X Y=%04X flags6=%04X flags8=%04X",
  p,ram(a+2),ram(a),ram(a+4)%16,memory.read_u8(a+0x10,"RAM"),memory.read_u8(a+0x11,"RAM"),
  ram(a+0x14),ram(a+0x16),ram(a+0x50),ram(a+0x1E),ram(a+0x20),ram(a+0x26),ram(a+0x28),ram(a+6),ram(a+8))
end
for i=1,budget do
 local r=records[i]
 assert(emu.framecount()==r.before,"replay pre-frame mismatch")
 joypad.set(r.keys)
 emu.frameadvance()
 boundary.after_frame({relative=r.relative,core_before=r.before,keys=r.keys})
 assert(emu.framecount()==r.after,"replay post-frame mismatch")
 assert(memory.read_u8(0x5C,"SRAM")==r.stage,"recorded stage diverged")
 assert(current_actor()==r.actor,"recorded FIRST context diverged at "..r.relative)
 log("matched relative="..r.relative.." core="..r.after.." stage="..r.stage.." FIRST_context=true")
end
save("final")
local observed=boundary.finish();local irq=di.finish()
local matched_exit=budget==#records and exit_core~=nil and emu.framecount()==exit_core
log("replay_finish records="..budget.." matched_recorded_exit="..tostring(matched_exit).." activation="..tostring(observed.activation)
 .." loss="..observed.loss.." terminal="..tostring(irq.terminal_observed).." DI_pairs="..irq.paired_reads
 .." full_core_equality_requires_independent_container_comparison=true")
local release={};for _,name in ipairs(buttons)do release[name]=false end;joypad.set(release)
write("done.txt","checkpoint-input-replay-complete")
client.exit()
