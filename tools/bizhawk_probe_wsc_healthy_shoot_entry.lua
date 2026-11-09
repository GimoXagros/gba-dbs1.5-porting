-- One approved stage7 HP1 lifetime; source-grounded inputs and healthy Shoot entry.
assert(userdata.get("boss_hp1_approval")=="user-approved-original-reference-once")
local function read(path)
 local f=assert(io.open(path,"rb"));local s=assert(f:read("*a"));f:close();return s:gsub("\r\n","\n")
end
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a and not s:find(old,b+1,true),"unique healthy-entry anchor: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local source=read("W:/tools/bizhawk_replay_wsc_shoot_checkpoint.lua")
local ending=assert(source:find('log("replay_begin core="',1,true));assert(not source:find('log("replay_begin core="',ending+1,true))
source=source:sub(1,ending-1)
source=once(source,'{"output","checkpoint_dir","frames","source_sha256","callback_order"}',
 '{"output","checkpoint_dir","frames","source_sha256","callback_order","boss_hp1_approval"}')
source=once(source,'budget<=3000','budget<=5000')
source=once(source,'"final.State","done.txt"','"final.State","healthy-shoot.State","healthy-shoot.txt","healthy-inputs.txt","done.txt"')
local begin=assert(source:find('local metadata=read(reference.."/shoot-preactivation.txt")',1,true))
local state=assert(source:find('assert(read(state_path):sub(1,4)',begin,true))
assert(not source:find('local metadata=read(reference.."/shoot-preactivation.txt")',begin+1,true)
 and not source:find('assert(read(state_path):sub(1,4)',state+1,true))
source=source:sub(1,begin-1)..[=[
local metadata=read(reference.."/fresh-boss.txt")
local _,count=metadata:gsub("capture_core=%d+","");assert(count==1)
local captured=assert(tonumber(metadata:match("capture_core=(%d+)")))
local expected_ram=read(reference.."/fresh-boss-ram.bin")
local expected_sram=read(reference.."/fresh-boss-sram.bin")
assert(#expected_ram==0x10000 and #expected_sram==0x8000)
local state_path=reference.."/fresh-boss.State"
]=]..source:sub(state)
source=once(source,'assert(memory.read_u8(0x5C,"SRAM")==11 and math.floor(memory.read_u16_le(0x3D8,"SRAM")/4)%2==0,"checkpoint is not preactivation Shoot")',[=[
assert(memory.read_u16_le(0x4E,"SRAM")==7 and memory.read_u8(0x5C,"SRAM")==7
 and memory.read_u8(0x5D,"SRAM")==3 and memory.read_u16_le(0x3D0,"SRAM")==2,"fresh stage7 checkpoint required")
local fp=memory.read_u16_le(0x65C,"SRAM");local sp=memory.read_u16_le(0x65E,"SRAM")
assert(memory.read_u16_le(0xC000+fp+0x50,"RAM")==8 and memory.read_u16_le(0xC000+sp+0x50,"RAM")==44
 and memory.read_u8(0xC000+fp+0x58,"RAM")==0,"fresh healthy HP8/44 checkpoint required")]=])
local original=read("W:/tools/bizhawk_probe_wsc_saved_boss_hp1.lua")
local a=assert(original:find("local boss,pending,hit,victory=",1,true))
local b=assert(original:find("local original_dofile=dofile",a,true))
assert(not original:find("local boss,pending,hit,victory=",a+1,true)and not original:find("local original_dofile=dofile",b+1,true))
local observer=original:sub(a,b-1)
observer=once(observer,'   or r.AW<=0 or r.AW>255 then return end',
 '   or r.AW<=0 or r.AW>255 or ram(0xC000+first+0x50)==0 or ram(0xC000+first+0x50)>=0x8000 then return end')
observer=once(observer,'  pending.direct_first=r.IX==first',[=[
  pending.p1hp=ram(0xC000+first+0x50)
  log("healthy_hit_pre P1HP="..pending.p1hp)
  pending.direct_first=r.IX==first]=])
observer=once(observer,'  local hp=ram(0xC000+p.second+0x50)',[=[
  assert(ram(0xC000+p.first+0x50)>0 and ram(0xC000+p.first+0x50)<0x8000,"positive player HP through engine hit")
  local hp=ram(0xC000+p.second+0x50)]=])
observer=once(observer,'  if not first or r.DS0~=0x0C00 or r.DS1~=0x1000 or r.BW~=second then return end',[=[
  if not first or r.DS0~=0x0C00 or r.DS1~=0x1000 or r.BW~=second
   or ram(0xC000+first+0x50)==0 or ram(0xC000+first+0x50)>=0x8000 then return end
  log("healthy_root5 P1HP="..ram(0xC000+first+0x50))]=])
observer=observer..[=[
return {enable=function(module)assert(not boss);boss=module;install();boss.tick()end,
 ready=evidence_ready,finish=function()
  assert(not pending,"healthy entry ended between real damage hooks")
  local result=evidence_ready();local s=boss.finish();finalized=true
  log("healthy_finish boss_writes="..s.writes.." healthy_hit_root5="..tostring(result).." cancelled="..tostring(cancelled))
  return result
 end}
]=]
local out=assert(userdata.get("output"))
local hit=assert(load('local out='..string.format('%q',out)..'\n'..observer,"@healthy-frozen-hit-observer","t",_ENV))()
source=source..[=[
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function ram(a)return memory.read_u16_le(a,"RAM")end
local function byte(a)return memory.read_u8(a,"RAM")end
local function valid(p)return p>=0x24 and p<=0x3654 and (p-0x24)%0x110==0 end
local function active(p)return valid(p)and math.floor(ram(0xC000+p-6)/2)%2==1 end
local function positive(v)return v>0 and v<0x8000 end
local function signed(v)return v>=0x8000 and v-0x10000 or v end
local function pin(at,values)for i,v in ipairs(values)do assert(memory.read_u8(at+i-1,"ROM")==v,"healthy source pin")end end
pin(0x772E37,{0x26,0x8B,0x3E,0x5C,0x06,0x8B,0x45,0x50,0x89,0x44,0x46,0xC7,0x45,0x50,0x01,0x00,0x26,0x81,0x26,0xD4,0x03,0xFF,0xFB})
pin(0x747A68,{0x55,0x8B,0xEC,0x83,0xC4,0xF8})
pin(0x766AB6,{0x33,0xC0,0xF7,0x44,0x20,0x40,0x00,0x74,0x44,0xC7,0x04,0xE8,0x16,0xC7,0x44,0x02,0x8E,0x66})
local scene,initializer,finished=nil,nil,false
local function site(raw,address)
 local r=emu.getregisters();assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==address+1,"healthy opcode calibration");return r
end
local boss=dofile("W:/tools/bizhawk_wsc_boss_hp1_once.lua");healthy_hit.enable(boss)
event.on_bus_write(function(address)
 if finished or scene then return end
 local r=site(0x772E42,address)
 assert(healthy_hit.ready()and r.DS0==0xC00 and r.DS1==0x1000 and r.IY==word(0x65C)
  and r.IX==ram(0xC008)+0x10 and active(r.IX) and ram(0xC000+r.IX-0x10)==0x0EEA
  and ram(0xC000+r.IX-0xE)==0x71F0 and positive(r.AW) and ram(0xC000+r.IY+0x50)==r.AW
  and ram(0xC000+r.IX+0x46)==r.AW,"actual positive saved scene HP after healthy victory")
 scene={payload=r.IX,hp=r.AW,core=emu.framecount()}
 log(string.format("scene_saved_HP core=%d owner=%04X FIRST=%04X saved=%d source=772E42 stage=%d",scene.core,r.IX,r.IY,r.AW,memory.read_u8(0x5C,"SRAM")))
end,0x72E42,"healthy-scene-HP-save","System Bus")
event.on_bus_write(function(address)
 if finished or initializer then return end
 site(0x747A68,address);assert(scene and healthy_hit.ready(),"healthy scene before Shoot initializer")
 initializer=emu.framecount();log("healthy_initializer core="..initializer)
end,0x47A68,"healthy-shoot-initializer","System Bus")
local buttons={"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local hold_jump,previousA,previousB=false,false,false
local function choose()
 local keys={};for _,name in ipairs(buttons)do keys[name]=false end
 if healthy_hit.ready()or word(0x4E)~=7 or memory.read_u8(0x5C,"SRAM")~=7 or word(0x50)~=0 then return keys end
 local p,q=word(0x65C),word(0x65E)
 assert(active(p)and active(q)and p~=q,"active combat pair")
 local x,y=0xC000+p,0xC000+q
 assert(ram(x+4)%16==0 and byte(x+0x10)==0 and byte(x+0x11)==0 and ram(x+0x14)==q
  and ram(y+4)%16==3 and byte(y+0x10)==1 and byte(y+0x11)==15 and ram(y+0x14)==p,"default controlled owned pair")
 if not positive(ram(x+0x50))or not positive(ram(y+0x50))then return keys end
 local cb,seg=ram(x),ram(x+2)
 local air=ram(x+6)%2==1
 local base=math.floor(ram(x+8)/0x100)%2==0
 local ground=seg==0x668E and (cb==0x115D or cb==0x11C9)and not air and base
 local startup=seg==0x668E and (cb==0x16E8 or cb==0x1721 or cb==0x1743)and base
 local air_input=seg==0x668E and cb==0x1845 and air and base
 local dx=signed(ram(y+0x26))-signed(ram(x+0x26))
 local dy=signed(ram(y+0x28))-signed(ram(x+0x28))
 if ground or startup or air_input then keys["P1 X2"]=dx>0x40;keys["P1 X4"]=dx < -0x40 end
 if hold_jump then
  if air or not startup then hold_jump=false else keys["P1 A"]=true end
 end
 if not hold_jump and ground and dy < -0x100 and not previousA and math.floor(ram(x+0x1E)/0x40)%2==0 then
  hold_jump=true;keys["P1 A"]=true
 end
 local face_right=math.floor(ram(x+0x9E)/0x4000)%2==1
 local aligned=dx==0 or (dx>0)==face_right
 if not keys["P1 A"]and not startup and not previousB and math.floor(ram(x+0x1E)/0x80)%2==0 and math.abs(dx)<0x300
  and (air_input or ground and aligned and math.abs(dy)<0x200)then keys["P1 B"]=true end
 return keys
end
local function keytext(keys)local fields={};for _,name in ipairs(buttons)do fields[#fields+1]=name.."="..tostring(keys[name])end;return table.concat(fields,";")end
local success,failure=false,false
for relative=0,budget-1 do
 local keys=choose();previousA,previousB=keys["P1 A"],keys["P1 B"]
 local before=emu.framecount();assert(before==captured+relative)
 joypad.set(keys);emu.frameadvance();assert(emu.framecount()==before+1)
 local p=word(0x65C);local hp=valid(p)and ram(0xC000+p+0x50)or 0
 local loginput=assert(io.open(out.."/healthy-inputs.txt","a"))
 loginput:write(string.format("input relative=%d core_before=%d core_after=%d keys=%s stage=%d P1HP=%d callback=%04X:%04X flags6=%04X facing=%04X\n",
  relative,before,emu.framecount(),keytext(keys),memory.read_u8(0x5C,"SRAM"),hp,valid(p)and ram(0xC000+p+2)or 0,valid(p)and ram(0xC000+p)or 0,valid(p)and ram(0xC000+p+6)or 0,valid(p)and ram(0xC000+p+0x9E)or 0));loginput:close()
 if initializer and memory.read_u8(0x5C,"SRAM")==11 then
  assert(scene and healthy_hit.ready()and active(scene.payload)and ram(0xC000+scene.payload-0xE)==0x71F0
   and ram(0xC000+scene.payload+0x46)==scene.hp and positive(scene.hp)and active(p)and active(word(0x65E))
   and positive(hp)and math.floor(word(0x3D8)/4)%2==0,"healthy retained scene before Shoot activation")
  save("healthy-shoot")
  write("healthy-shoot.txt",string.format("healthy_shoot scene_save_core=%d initializer_core=%d capture_core=%d relative_next=%d scene_payload=%04X saved_HP=%d FIRST=%04X current_HP=%d source_saved_HP_positive=true healthy_engine_hit_root5=true activation_bit4=false\n",
   scene.core,initializer,emu.framecount(),relative+1,scene.payload,scene.hp,p,hp))
  success=true;break
 end
 if not positive(hp)then failure=true;log("healthy_attempt_failed core="..emu.framecount().." reason=nonpositive_player_HP no_rearm=true");break end
end
healthy_hit.finish();finished=true
if not success then save("final")end
local release={};for _,name in ipairs(buttons)do release[name]=false end;joypad.set(release)
write("done.txt",success and "healthy-shoot-checkpoint-observed"or failure and "healthy-shoot-entry-failed"or "healthy-shoot-entry-bounded-complete")
client.exit()
]=]
return assert(load(source,"@healthy-stage7-reviewed-checkpoint-loader","t",setmetatable({healthy_hit=hit},{__index=_ENV})))()
