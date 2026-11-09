-- Normal Continue only, from a genuine replay-final checkpoint. No cheat modules.
local f=assert(io.open("W:/tools/bizhawk_replay_wsc_shoot_checkpoint.lua","rb"))
local source=assert(f:read("*a")):gsub("\r\n","\n");f:close()
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a and not s:find(old,b+1,true),"unique Continue loader anchor: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local ending=assert(source:find('log("replay_begin core="',1,true))
assert(not source:find('log("replay_begin core="',ending+1,true))
source=source:sub(1,ending-1) -- exact reviewed loader and safe restored-state export
source=once(source,'budget<=3000','budget<=5000')
source=once(source,'"final.State","done.txt"','"final.State","fresh-boss.State","fresh-boss.txt","continue-inputs.txt","done.txt"')
local begin=assert(source:find('local metadata=read(reference.."/shoot-preactivation.txt")',1,true))
local state=assert(source:find('assert(read(state_path):sub(1,4)',begin,true))
assert(not source:find('local metadata=read(reference.."/shoot-preactivation.txt")',begin+1,true)
 and not source:find('assert(read(state_path):sub(1,4)',state+1,true))
source=source:sub(1,begin-1)..[=[
local metadata=read(reference.."/replay.txt")
local _,count=metadata:gsub("state_export name=final core=%d+ bytes=%d+","")
assert(count==1,"one actual final-state export required")
local captured=assert(tonumber(metadata:match("state_export name=final core=(%d+) bytes=%d+")))
local expected_ram=read(reference.."/final-ram.bin")
local expected_sram=read(reference.."/final-sram.bin")
assert(#expected_ram==0x10000 and #expected_sram==0x8000)
local state_path=reference.."/final.State"
]=]..source:sub(state)
source=once(source,'assert(memory.read_u8(0x5C,"SRAM")==11 and math.floor(memory.read_u16_le(0x3D8,"SRAM")/4)%2==0,"checkpoint is not preactivation Shoot")',[=[
assert(memory.read_u16_le(0x4E,"SRAM")==9 and memory.read_u8(0x5C,"SRAM")==7
 and memory.read_u8(0x5D,"SRAM")==3 and memory.read_u16_le(0x52,"SRAM")==0
 and memory.read_u16_le(0x54,"SRAM")==0,"checkpoint is not the observed ordinary Continue entry")]=])
source=source..[=[
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function ram(a)return memory.read_u16_le(a,"RAM")end
local function byte(a)return memory.read_u8(a,"RAM")end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function active(p)return valid(p) and math.floor(ram(0xC000+p-6)/2)%2==1 end
local function task(h,callback)
 return active(h+0x10) and ram(0xC000+h)==callback and ram(0xC000+h+2)==0x4090
end
local function pin(at,values)
 for i,v in ipairs(values)do assert(memory.read_u8(at+i-1,"ROM")==v,"Continue source pin")end
end
pin(0x77F977,{0x68,0x00,0x03,0x51,0x9A,0x4B,0x2A,0xFF,0x4F,0x83,0xC4,0x04,
 0xA9,0x40,0x00,0x75,0x03,0xE9,0x13,0x01,0xF6,0x04,0x01,0x75,0x03,0xE9,0x9C,0x00})
pin(0x76B880,{0x68,0x90,0x40,0x68,0xFA,0x07,0x68,0x00,0x0C,0x26,0xFF,0x36,0xDE,0x03,
 0x9A,0xC7,0x0B,0xFF,0x4F,0x83,0xC4,0x08,0x68,0x90,0x40,0x68,0x0B,0x0D,0x68,0x00,0x0C,
 0x26,0xFF,0x36,0xE0,0x03,0x9A,0xC7,0x0B,0xFF,0x4F,0x83,0xC4,0x08})
local buttons={"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local pressed,menu_header,accepted,activation,finished=false,nil,nil,nil,false
local function site(raw,address)
 local r=emu.getregisters()
 assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==address+1,"Continue opcode calibration")
 return r
end
event.on_bus_write(function(address)
 if finished or accepted then return end
 local r=site(0x77F993,address)
 assert(pressed and menu_header and r.DS0==0xC00 and r.IX==menu_header+0x10+0xC6
  and byte(0xC000+r.IX)==1 and word(0x4E)==9 and memory.read_u8(0x5C,"SRAM")==7,
  "actual default Continue branch ownership")
 accepted=emu.framecount();log("continue_branch core="..accepted.." menu_header="..menu_header.." source=77F993")
end,0x7F993,"normal-continue-accepted","System Bus")
event.on_bus_write(function(address)
 if finished or activation then return end
 local r=site(0x76B8AC,address)
 assert(accepted and r.DS1==0x1000 and word(0x4E)==7 and memory.read_u8(0x5C,"SRAM")==7
  and task(word(0x3DE),0x07FA) and task(word(0x3E0),0x0D0B),"fresh stage7 active callback installation")
 activation=emu.framecount();log("active_callback_install core="..activation.." source=76B8AC")
end,0x6B8AC,"normal-continue-active","System Bus")
local function ready_menu()
 if word(0x4E)~=9 or memory.read_u8(0x5C,"SRAM")~=7 then return end
 local found
 for h=0x14,0x3644,0x110 do
  if active(h+0x10) and ram(0xC000+h)==0x05DA and ram(0xC000+h+2)==0x7F20 then
   assert(not found,"one active Continue menu owner");found=h
  end
 end
 if found then assert(byte(0xC000+found+0x10+0xC6)==1,"default Continue choice changed")end
 return found
end
local function healthy()
 local p,q=word(0x65C),word(0x65E)
 assert(active(p) and active(q) and p~=q,"active fresh fighter pair")
 local a,b=0xC000+p,0xC000+q
 assert(word(0x4E)==7 and word(0x50)==0 and memory.read_u8(0x5C,"SRAM")==7 and word(0x3D0)==2
  and memory.read_u8(0x5D,"SRAM")==3 and word(0x3CE)>0 and word(0x3CE)<=18000,"fresh stage7 battle")
 assert(task(word(0x3DE),0x07FA) and task(word(0x3E0),0x0D0B),"active input/post task owners")
 assert(ram(a+4)%16==0 and byte(a+0x10)==0 and byte(a+0x11)==0 and ram(a+0x14)==q
  and ram(b+4)%16==3 and byte(b+0x10)==1 and byte(b+0x11)==15 and ram(b+0x14)==p,"fresh default owned fighters")
 assert(ram(a+0x50)==8 and ram(b+0x50)==44 and byte(a+0x58)==0,"first active frame is not HP8/44 with zero pending player damage")
 return p,q
end
log("continue_begin core="..captured.." budget="..budget.." guest_writes=none approvals_loaded=false combat_input=none")
local captured_fresh=false
for relative=0,budget-1 do
 local keys={};for _,name in ipairs(buttons)do keys[name]=false end
 if not pressed and relative>0 then
  local h=ready_menu()
  if h then
   assert(math.floor(ram(0x3854)/0x40)%2==0,"A must be released before ordinary Continue edge")
   menu_header=h;pressed=true;keys["P1 A"]=true
  end
 end
 local before=emu.framecount();assert(before==captured+relative)
 joypad.set(keys);emu.frameadvance();assert(emu.framecount()==before+1)
 local input=assert(io.open(out.."/continue-inputs.txt","a"))
 input:write(string.format("input relative=%d core_before=%d core_after=%d A=%s all_other_keys=false mode=%d stage=%d\n",
  relative,before,emu.framecount(),tostring(keys["P1 A"]),word(0x4E),memory.read_u8(0x5C,"SRAM")));input:close()
 if activation then
  assert(not keys["P1 A"] and accepted,"controls released at fresh active checkpoint")
  local p,q=healthy()
  save("fresh-boss")
  write("fresh-boss.txt",string.format("fresh_boss continue_core=%d active_hook_core=%d capture_core=%d relative_next=%d FIRST=%04X SECOND=%04X P1HP=8 bossHP=44 pending_player_damage=0 timer=%d all_keys_released=true combat_inputs_sent=0 no_prior_nonHP_collision_claim=true\n",
   accepted,activation,emu.framecount(),relative+1,p,q,word(0x3CE)))
  captured_fresh=true;break
 end
end
finished=true
if not captured_fresh then save("final");log("continue_bound reached=true accepted="..tostring(accepted~=nil).." active="..tostring(activation~=nil))end
local release={};for _,name in ipairs(buttons)do release[name]=false end;joypad.set(release)
write("done.txt",captured_fresh and "fresh-boss-checkpoint-observed"or "continue-bounded-complete")
client.exit()
]=]
return assert(load(source,"@normal-continue-reviewed-checkpoint-loader","t",_ENV))()
