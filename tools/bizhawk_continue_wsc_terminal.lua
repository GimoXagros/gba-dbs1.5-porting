-- Read-only neutral continuation of the already observed actual terminal chain.
local f=assert(io.open("W:/tools/bizhawk_replay_wsc_shoot_checkpoint.lua","rb"))
local source=assert(f:read("*a")):gsub("\r\n","\n");f:close()
local function once(s,old,new)
 local a,b=s:find(old,1,true);assert(a and not s:find(old,b+1,true),"unique terminal-tail loader anchor: "..old)
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local ending=assert(source:find('log("replay_begin core="',1,true));assert(not source:find('log("replay_begin core="',ending+1,true))
source=source:sub(1,ending-1)
source=once(source,'budget<=3000','budget<=512')
source=once(source,'"final.State","done.txt"','"final.State","terminal-tail.txt","tile0-writes.txt","bg1-refills.txt","done.txt"')
local begin=assert(source:find('local metadata=read(reference.."/shoot-preactivation.txt")',1,true))
local state=assert(source:find('assert(read(state_path):sub(1,4)',begin,true))
assert(not source:find('local metadata=read(reference.."/shoot-preactivation.txt")',begin+1,true)
 and not source:find('assert(read(state_path):sub(1,4)',state+1,true))
source=source:sub(1,begin-1)..[=[
local metadata=read(reference.."/replay.txt")
local _,count=metadata:gsub("state_export name=final core=%d+ bytes=%d+","");assert(count==1)
local captured=assert(tonumber(metadata:match("state_export name=final core=(%d+) bytes=%d+")))
local expected_ram=read(reference.."/final-ram.bin")
local expected_sram=read(reference.."/final-sram.bin")
assert(#expected_ram==0x10000 and #expected_sram==0x8000)
local state_path=reference.."/final.State"
]=]..source:sub(state)
source=once(source,'assert(memory.read_u8(0x5C,"SRAM")==11 and math.floor(memory.read_u16_le(0x3D8,"SRAM")/4)%2==0,"checkpoint is not preactivation Shoot")',[=[
assert(memory.read_u8(0x5C,"SRAM")==11 and math.floor(memory.read_u16_le(0x3D8,"SRAM")/0x400)%2==1,
 "checkpoint must be actual Shoot0400 terminal continuation")]=])
source=source..[=[
local function word(a)return memory.read_u16_le(a,"SRAM")end
local function ram(a)return memory.read_u16_le(a,"RAM")end
local function append(name,line)local f=assert(io.open(out.."/"..name,"a"));f:write(line.."\n");f:close()end
local function pin(at,values)for i,v in ipairs(values)do assert(memory.read_u8(at+i-1,"ROM")==v,"terminal tail source pin")end end
pin(0x77E18F,{0x26,0x89,0x45,0x1C,0x53,0x06,0x57,0x9A,0x67,0x33,0xFF,0x4F,0x83,0xC4,0x06})
local di=dofile("W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua")
local initial_mode=word(0x4E)
local finished,overflow=false,false
local reads,snapshots,writes,refills,omitted_snapshots=0,0,0,0,0
local seen,pending={},nil
local first_visible,visible_picture=nil,false
local function site(raw,address)
 local r=emu.getregisters();assert(address==raw-0x700000 and (r.PS*16+r.PC)%0x100000==address+1,"terminal tail opcode calibration");return r
end
local function context(r)
 local h=ram(0xC008)
 local valid=h>=0x14 and h<=0x3644 and (h-0x14)%0x110==0
 return string.format("PS:PC=%04X:%04X DS=%04X ES=%04X SI=%04X DI=%04X AX=%04X SP=%04X current_header=%04X current_callback=%04X:%04X",
  r.PS,r.PC,r.DS0,r.DS1,r.IX,r.IY,r.AW,r.SP,h,valid and ram(0xC000+h+2)or 0,valid and ram(0xC000+h)or 0)
end
event.on_bus_write(function(address)
 if finished then return end
 local r=site(0x75FC98,address)
 if memory.read_u8(0x5C,"SRAM")~=11 then return end
 reads=reads+1;if reads>512 then overflow=true;append("terminal-tail.txt","read_limit_exceeded=512 complete_ledger=false");return end
 assert(r.DS1==0x300,"real final IRQ ES0300")
 local fields={};local values={}
 for i=0,6 do values[i+1]=ram(0x30EA+i*2);fields[#fields+1]=string.format("%04X",values[i+1])end
 local k=(values[3]-values[4])%0x10000
 local flags=word(0x3D8)
 local potential=values[4]==8 and k>=1 and k<=114 and math.floor(flags/0x800)%2==0
 local key=table.concat(fields,":")
 local label="none"
 if not seen[key] then
  seen[key]=true
  if snapshots<128 then
   snapshots=snapshots+1;label=string.format("terminal-irq-%03d",snapshots)
   write(label.."-ram.bin",memory.read_bytes_as_binary_string(0,0x10000,"RAM"))
   write(label.."-sram.bin",memory.read_bytes_as_binary_string(0,0x8000,"SRAM"))
  else omitted_snapshots=omitted_snapshots+1 end
 end
 append("terminal-tail.txt",string.format("read=%d core=%d EA=%s old_k=%d expected_final_compare=%d flags=%04X potential_visible=%s snapshot=%s snapshot_cap=%s %s",
  reads,emu.framecount(),key,k,(k+29)%256,flags,tostring(potential),label,tostring(snapshots>=128),context(r)))
 if potential and not first_visible then first_visible={core=emu.framecount(),k=k,read=reads}end
end,0x5FC98,"terminal-tail-operand","System Bus")
-- Pinned managed R,W,E -> native R,E,W: on_bus_exec observes CPU writes.
-- Native DMA writes bypass that CPU hook; DMA exclusion remains a separate proof.
for at=0x4000,0x401F do
 local target=at
 event.on_bus_exec(function(address)
  if finished or overflow then return end
  assert(address==target,"blank tile write address")
  writes=writes+1
  if writes>4096 then overflow=true;append("tile0-writes.txt","write_limit_exceeded=4096 complete_ledger=false");return end
  local r=emu.getregisters()
  append("tile0-writes.txt",string.format("write=%d core=%d address=%04X backing_byte_at_callback=%02X callback_value_not_used=true %s",
   writes,emu.framecount(),address,memory.read_u8(address,"RAM"),context(r)))
 end,target,"terminal-tile0-byte-"..target,"System Bus")
end
local function camera_dump(label)
 local descriptor=memory.read_bytes_as_binary_string(0x20E,0x40,"SRAM")
 local map=memory.read_bytes_as_binary_string(0x800,0x800,"RAM")
 write(label.."-descriptor.bin",descriptor);write(label.."-map.bin",map)
 return descriptor,map
end
event.on_bus_write(function(address)
 if finished or overflow then return end
 local r=site(0x77E196,address)
 if memory.read_u8(0x5C,"SRAM")~=11 then return end
 refills=refills+1
 if refills>512 then overflow=true;append("bg1-refills.txt","call_limit_exceeded=512 complete_ledger=false");return end
 assert(not pending and r.DS1==0x1000 and r.IY==0x20E,"actual BG1 descriptor owner")
 local label=string.format("bg1-call-%03d",refills)
 local d,m=camera_dump(label.."-pre")
 pending={ps=r.PS,pc=r.PC,sp=r.SP,es=r.DS1,di=r.IY,label=label,descriptor=d,map=m,core=emu.framecount(),mode=r.BW}
 append("bg1-refills.txt",string.format("pre call=%d core=%d mode=%04X %s",refills,pending.core,r.BW,context(r)))
end,0x7E196,"terminal-bg1-pre","System Bus")
event.on_bus_write(function(address)
 if finished or not pending then return end
 local r=site(0x77E19B,address);local p=pending
 assert(r.PS==p.ps and r.PC==(p.pc+5)%0x10000 and r.SP==p.sp,"paired real BG1 call return")
 local d,m=camera_dump(p.label.."-post")
 local cells,bytes,descriptor_bytes=0,0,0
 for i=1,#m do if m:byte(i)~=p.map:byte(i)then bytes=bytes+1 end end
 for i=1,#m,2 do if m:sub(i,i+1)~=p.map:sub(i,i+1)then cells=cells+1 end end
 for i=1,#d do if d:byte(i)~=p.descriptor:byte(i)then descriptor_bytes=descriptor_bytes+1 end end
 append("bg1-refills.txt",string.format("post call=%d core=%d changed_map_cells=%d changed_map_bytes=%d changed_descriptor_bytes=%d interior_write_restore_not_excluded=true",
  refills,emu.framecount(),cells,bytes,descriptor_bytes))
 pending=nil
end,0x7E19B,"terminal-bg1-post","System Bus")
append("terminal-tail.txt","begin inherited_terminal_flag=false parent_chain=launcher_pinned_manifest neutral_inputs=true max_reads=512 max_full_snapshots=128 plus_frozen_DI_distinct_max16=true")
append("tile0-writes.txt","begin fixed_addresses=4000..401F maximum_events=4096 cpu_write_observer=true DMA_writes_not_observed=true")
append("bg1-refills.txt","begin owner=1000:020E map=0800..0FFF maximum_calls=512 paired_completed_footprint_only=true")
local buttons={"P1 X1","P1 X2","P1 X3","P1 X4","P1 Y1","P1 Y2","P1 Y3","P1 Y4","P1 A","P1 B","P1 Start","Power","Rotate"}
local keys={};for _,name in ipairs(buttons)do keys[name]=false end
local exited=false
for relative=0,budget-1 do
 local before=emu.framecount();assert(before==captured+relative)
 joypad.set(keys);emu.frameadvance();assert(emu.framecount()==before+1)
 if first_visible and not visible_picture then
  client.screenshot(out.."/first-potential-visible.png");visible_picture=true
  append("terminal-tail.txt",string.format("potential_visible_picture event_core=%d capture_core=%d read=%d old_k=%d actual_LCD_line_not_read=true",
   first_visible.core,emu.framecount(),first_visible.read,first_visible.k))
 end
 exited=memory.read_u8(0x5C,"SRAM")~=11 or word(0x4E)~=initial_mode
 if exited or overflow then break end
end
assert(not pending,"tail ended inside actual BG1 call")
local ds=di.finish();finished=true
save("final")
append("terminal-tail.txt",string.format("finished core=%d reads=%d snapshots=%d snapshot_cap_reached=%s omitted_counter_snapshots=%d tile0_writes=%d BG1_calls=%d ledger_overflow=%s actual_stage_or_mode_exit=%s stage=%d mode=%d flags=%04X DI_pairs=%d inherited_terminal_not_faked=true",
 emu.framecount(),reads,snapshots,tostring(snapshots>=128),omitted_snapshots,writes,refills,tostring(overflow),tostring(exited),memory.read_u8(0x5C,"SRAM"),word(0x4E),word(0x3D8),ds.paired_reads))
joypad.set(keys)
write("done.txt",exited and not overflow and "terminal-continuation-exit-observed"or "terminal-continuation-bounded-complete")
client.exit()
]=]
return assert(load(source,"@neutral-terminal-reviewed-checkpoint-loader","t",_ENV))()
