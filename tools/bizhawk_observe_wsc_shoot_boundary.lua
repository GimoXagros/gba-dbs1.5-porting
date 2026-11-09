-- Original-only baseline observation. No input changes or guest-memory writes.
-- The caller invokes after_frame only after emu.frameadvance has returned.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
assert(userdata.get("source_sha256")=="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7")
assert(userdata.get("callback_order")=="bizhawk2111-rew" and emu.getsystemid()=="WSWAN")
local installed,finished,inside,ended=false,false,false,false
local initializer,activation_pre,activation_post,checkpoint,loss=nil,nil,nil,nil,nil
local damage,jump=nil,nil
local jumps,write_count,input_count=0,0,0
local watched,previous_hp,last_write=nil,nil,nil
local input_truncated=false
local active_picture,loss_picture=false,false
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function ram(a)return memory.read_u16_le(a,"RAM")end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function first()
 local p=word(0x65C)
 if valid(p) and ram(0xC000+p+4)%16==0 and memory.read_u8(0xC000+p+0x10,"RAM")==0 then return p end
end
local function stage11()return memory.read_u8(0x5C,"SRAM")==11 end
local function activebit()return math.floor(word(0x3D8)/4)%2==1 end
local function log(line,name)
 local f=assert(io.open(out.."/"..(name or "shoot-boundary.txt"),"a"));f:write(line.."\n");f:close()
end
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(data);f:close()
end
local function snapshot(label)
 write("shoot-"..label.."-ram.bin",memory.read_bytes_as_binary_string(0,0x10000,"RAM"))
 write("shoot-"..label.."-sram.bin",memory.read_bytes_as_binary_string(0,0x8000,"SRAM"))
end
local function actor(p)
 if not valid(p) then return "invalid_payload="..tostring(p)end
 local a=0xC000+p
 return string.format("payload=%04X callback=%04X:%04X kind=%d index10=%d id11=%d link14=%04X owner16=%04X HP=%04X held=%04X edge=%04X X=%04X Y=%04X flags6=%04X flags8=%04X",
  p,ram(a+2),ram(a),ram(a+4)%16,memory.read_u8(a+0x10,"RAM"),memory.read_u8(a+0x11,"RAM"),
  ram(a+0x14),ram(a+0x16),ram(a+0x50),ram(a+0x1E),ram(a+0x20),ram(a+0x26),ram(a+0x28),ram(a+6),ram(a+8))
end
local function controls()
 local a,b=word(0x3DE),word(0x3E0)
 if not valid(a+0x10) or not valid(b+0x10) then return "input_tasks=invalid"end
 return string.format("pre=%04X:%04X post=%04X:%04X flags=%04X timer=%d",
  ram(0xC000+a+2),ram(0xC000+a),ram(0xC000+b+2),ram(0xC000+b),word(0x3D8),word(0x3CE))
end
local function pin(at,bytes)
 for i,v in ipairs(bytes)do assert(memory.read_u8(at+i-1,"ROM")==v,"Shoot boundary source pin")end
end
local function registers(raw,address)
 local r=emu.getregisters()
 assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000,"boundary opcode calibration")
 return r
end
local function hook(raw,label,fn)
 event.on_bus_write(function(address)
  if finished or ended then return end
  inside=true;fn(registers(raw,address));inside=false
 end,raw-0x700000,"shoot-boundary-"..label,"System Bus")
end
local function watch_hp(p)
 assert(not watched,"only first Shoot owner is watched")
 watched=p;previous_hp=ram(0xC000+p+0x50)
 for byte=0,1 do
  local target=0xC000+p+0x50+byte
  -- Calibrated 2.11.1 adaptation: managed on_bus_exec observes native writes.
  event.on_bus_exec(function(address)
   if finished or ended or not stage11() or first()~=watched or write_count>=64 then return end
   inside=true
   assert(address==target,"HP write callback address")
   local r=emu.getregisters()
   write_count=write_count+1
   last_write={frame=emu.framecount(),ps=r.PS,pc=r.PC,address=address,word=ram(0xC000+p+0x50)}
   log(string.format("hp_write count=%d core=%d address=%04X backing_byte_at_callback=%02X backing_word_at_callback=%04X PS:PC=%04X:%04X DS=%04X SI=%04X DI=%04X callback_value_not_used=true",
    write_count,last_write.frame,address,memory.read_u8(address,"RAM"),last_write.word,r.PS,r.PC,r.DS0,r.IX,r.IY))
   inside=false
  end,target,"shoot-first-HP-byte-"..byte,"System Bus")
 end
end
local function tick()
 if installed then return end
 assert(not finished)
 for domain,size in pairs({ROM=0x800000,RAM=0x10000,SRAM=0x8000})do assert(memory.getmemorydomainsize(domain)==size)end
 for _,name in ipairs({"shoot-boundary.txt","shoot-inputs.txt","shoot-preactivation.State"})do
  local f=io.open(out.."/"..name,"rb");if f then f:close();error("fresh boundary output required")end
 end
 pin(0x747A68,{0x55,0x8B,0xEC,0x83,0xC4,0xF8})
 pin(0x77345F,{0x26,0x81,0x0E,0xD8,0x03,0x04,0x00,0x68,0x90,0x40,0x68,0xFA,0x07,0x68,0x00,0x0C,
  0x26,0xFF,0x36,0xDE,0x03,0x9A,0xC7,0x0B,0xFF,0x4F,0x83,0xC4,0x08,0x68,0x90,0x40,0x68,0x0B,0x0D,
  0x68,0x00,0x0C,0x26,0xFF,0x36,0xE0,0x03,0x9A,0xC7,0x0B,0xFF,0x4F,0x83,0xC4,0x08})
 pin(0x74396D,{0x8A,0x44,0x58,0x39,0x44,0x50,0x7D,0x03,0x8B,0x44,0x50,0x0B,0xC0,0x75,0x03,0xE9,0x52,0x01,
  0x26,0x83,0x3E,0xD0,0x03,0x02,0x75,0x15,0x29,0x44,0x50,0x81,0x64,0x0C,0xFF,0xBF})
 pin(0x766AB6,{0x33,0xC0,0xF7,0x44,0x20,0x40,0x00,0x74,0x44,0xC7,0x04,0xE8,0x16,0xC7,0x44,0x02,0x8E,0x66,0xB8,0x04,0x00})
 hook(0x747A68,"initializer",function(r)
  if initializer then return end
  initializer={core=emu.framecount(),ps=r.PS,pc=r.PC}
  log(string.format("initializer_request core=%d PS:PC=%04X:%04X save_deferred_to_outer_frame=true",initializer.core,r.PS,r.PC))
 end)
 hook(0x77345F,"activation-pre",function(r)
  if activation_pre or not stage11()then return end
  assert(r.DS0==0xC00 and r.DS1==0x1000)
  activation_pre=emu.framecount()
  log("activation_pre core="..activation_pre.." "..controls().." "..actor(first()or 0));snapshot("activation-pre")
 end)
 hook(0x77348F,"activation-post",function(r)
  if activation_post or not stage11()then return end
  assert(activation_pre and r.DS0==0xC00 and r.DS1==0x1000 and activebit())
  local a,b=word(0x3DE),word(0x3E0)
  assert(valid(a+0x10) and valid(b+0x10) and ram(0xC000+a)==0x07FA and ram(0xC000+a+2)==0x4090
   and ram(0xC000+b)==0x0D0B and ram(0xC000+b+2)==0x4090,"active input/post owners")
  activation_post=emu.framecount();log("activation_post core="..activation_post.." "..controls().." "..actor(first()or 0));snapshot("activation-post")
 end)
 hook(0x743987,"P1-loss-pre",function(r)
  if loss or not stage11()then return end
  local p=first()
  if not p or r.DS0~=0xC00 or r.DS1~=0x1000 or r.IX~=p or word(0x3D0)~=2 then return end
  local hp=ram(0xC000+p+0x50)
  if hp==0 or hp>=0x8000 or r.AW==0 or r.AW>hp then return end
  assert(not damage)
  damage={ps=r.PS,pc=r.PC,ds=r.DS0,es=r.DS1,si=r.IX,sp=r.SP,amount=r.AW,before=hp}
  local owner=ram(0xC000+p+0x16)
  log(string.format("loss_pre core=%d PS:PC=%04X:%04X victim=%04X HP=%d damage=%d candidate_owner16=%04X %s",
   emu.framecount(),r.PS,r.PC,p,hp,r.AW,owner,actor(p)))
  log("loss_owner_context candidate_only=true "..actor(owner));snapshot("loss-pre")
 end)
 hook(0x74398A,"P1-loss-post",function(r)
  if not damage then return end
  local d=damage
  assert(r.PS==d.ps and r.PC==(d.pc+3)%0x10000 and r.DS0==d.ds and r.DS1==d.es
   and r.IX==d.si and r.SP==d.sp and r.AW==d.amount,"P1 loss instruction/owner pairing")
  local hp=ram(0xC000+d.si+0x50);assert(hp==d.before-d.amount,"actual P1 HP subtraction")
  loss={kind="source3030-paired",core=emu.framecount(),before=d.before,after=hp}
  damage=nil;log(string.format("loss_post core=%d before=%d after=%d actual_source3030=true",loss.core,loss.before,hp));snapshot("loss-post")
 end)
 hook(0x766ABF,"jump-pre",function(r)
  if jumps>=8 or not stage11()or r.DS0~=0xC00 or r.IX~=first()then return end
  assert(not jump and math.floor(ram(0xC000+r.IX+0x20)/0x40)%2==1)
  jump={ps=r.PS,pc=r.PC,si=r.IX};log("jump_accept_pre core="..emu.framecount().." "..actor(r.IX))
 end)
 hook(0x766AC8,"jump-post",function(r)
  if not jump then return end
  assert(r.PS==jump.ps and r.PC==(jump.pc+9)%0x10000 and r.DS0==0xC00 and r.IX==jump.si
   and ram(0xC000+r.IX)==0x16E8 and ram(0xC000+r.IX+2)==0x668E)
  jumps=jumps+1;jump=nil;log("jump_accept_post core="..emu.framecount().." count="..jumps.." takeoff_not_claimed=true "..actor(r.IX))
 end)
 installed=true;log("enabled input_policy=unchanged savestate_load=none guest_writes=none max_input_frames=3000 max_HP_write_events=64 max_jumps=8")
end
local function keys_text(keys)
 local names={};for k in pairs(keys)do names[#names+1]=k end;table.sort(names)
 local parts={};for _,k in ipairs(names)do parts[#parts+1]=k.."="..tostring(keys[k])end
 return table.concat(parts,";")
end
local function after_frame(context)
 assert(not inside,"savestate API forbidden inside memory callbacks")
 if finished or ended then return end
 local captured_now=false
 if initializer and not checkpoint and stage11() and not activation_pre and not activebit() and first()then
  local core=emu.framecount()
  local rp=memory.read_bytes_as_binary_string(0,0x10000,"RAM")
  local sp=memory.read_bytes_as_binary_string(0,0x8000,"SRAM")
  local path=out.."/shoot-preactivation.State"
  assert(savestate.save(path,true)==true,"genuine preactivation savestate save failed")
  local f=assert(io.open(path,"rb"),"savestate API did not create file")
  local signature=f:read(4);local size=assert(f:seek("end"));f:close()
  assert(signature=="PK\003\004" and size>4,"nonempty full savestate ZIP required")
  assert(emu.framecount()==core and memory.read_bytes_as_binary_string(0,0x10000,"RAM")==rp
   and memory.read_bytes_as_binary_string(0,0x8000,"SRAM")==sp,"savestate save changed guest/frame")
  checkpoint={core=core,relative_next=context.relative+1,size=size}
  write("shoot-preactivation-ram.bin",rp);write("shoot-preactivation-sram.bin",sp)
  client.screenshot(out.."/shoot-preactivation.png")
  log(string.format("checkpoint hook_core=%d capture_core=%d relative_next=%d bytes=%d native_full_state=true Lua_policy_state_saved=false %s %s",
   initializer.core,core,checkpoint.relative_next,size,controls(),actor(first())),"shoot-preactivation.txt")
  log("last_consumed_keys="..keys_text(context.keys),"shoot-preactivation.txt")
  log("resume_requires_rebinding_userdata_output_budget_approval=true replay_begins_next_input_record=true","shoot-preactivation.txt")
  watch_hp(first());captured_now=true
 end
 if checkpoint and not captured_now then
  if input_count<3000 then
   input_count=input_count+1
   log(string.format("input relative=%d core_before=%d core_after=%d stage_after=%d keys=%s %s",
    context.relative,context.core_before,emu.framecount(),memory.read_u8(0x5C,"SRAM"),keys_text(context.keys),actor(first()or 0)),"shoot-inputs.txt")
  elseif not input_truncated then input_truncated=true;log("input_limit_reached=3000 replay_stream_truncated=true","shoot-inputs.txt")end
  local p=first()
  if stage11() and p==watched then
   local hp=ram(0xC000+p+0x50)
   if previous_hp and hp<previous_hp and not loss then
    loss={kind="frame-decrease-unpaired",core=emu.framecount(),before=previous_hp,after=hp}
    log(string.format("loss_unpaired core=%d before=%d after=%d last_write_core=%s instruction_owner_not_inferred=true",
     loss.core,previous_hp,hp,last_write and tostring(last_write.frame)or"none"));snapshot("loss-unpaired")
   end
   previous_hp=hp
  end
  if not stage11()then ended=true;log("stage11_exit core="..emu.framecount().." relative_next="..(context.relative+1),"shoot-inputs.txt")end
 end
 if activation_post and not active_picture then
  active_picture=true;client.screenshot(out.."/shoot-active-frame.png");snapshot("active-frame")
  log(string.format("active_visual event_core=%d capture_core=%d relative_next=%d",activation_post,emu.framecount(),context.relative+1))
 end
 if loss and not loss_picture then
  loss_picture=true;client.screenshot(out.."/shoot-loss-frame.png");snapshot("loss-frame")
  log(string.format("loss_visual event_core=%d capture_core=%d relative_next=%d",loss.core,emu.framecount(),context.relative+1))
 end
end
local function finish()
 assert(not damage and not jump,"boundary observation ended between paired source hooks")
 finished=true
 log(string.format("finished checkpoint=%s activation=%s loss=%s jumps=%d HP_write_events=%d input_frames=%d stage11_exit=%s input_truncated=%s",
  tostring(checkpoint~=nil),tostring(activation_post~=nil),loss and loss.kind or"none",jumps,write_count,input_count,tostring(ended),tostring(input_truncated)))
 return {checkpoint=checkpoint~=nil,activation=activation_post~=nil,loss=loss and loss.kind or"none",input_frames=input_count,ended=ended}
end
return {tick=tick,after_frame=after_frame,finish=finish}
