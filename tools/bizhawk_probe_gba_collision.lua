-- Read-only collision observation with ordinary, frame-indexed controller input.
local out = assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"))
local limit = userdata.get("frames") or 18000
local start = userdata.get("start_frame") or 2970
local initial_frame = emu.framecount()
local buttons = {"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local count_addresses = {0x4C4D,0x4C4E,0x4C4C}
local maxima = {0,0,0}
local found, valid, hooks, dispatch_hooks = false, 0, 0, 0
local capture_frame
local function log(s)
 local f=assert(io.open(out.."/trace.txt","a")); f:write(s.."\n"); f:close()
end
local function dump(name, domain, length)
 local f=assert(io.open(out.."/"..name,"wb"));f:write(memory.read_bytes_as_binary_string(0,length,domain));f:close()
end
local function sample_counts()
 for i,address in ipairs(count_addresses) do maxima[i]=math.max(maxima[i],memory.read_u8(address,"IWRAM")) end
end
local function capture(reason, registers, address)
 capture_frame=emu.framecount()
 sample_counts()
 log("capture="..reason.." frame="..capture_frame.." valid="..valid.." hooks="..hooks.." dispatch_hooks="..dispatch_hooks.." timing="..(address and "before-instruction" or "frame-boundary"))
 if address then log(string.format("callback_address=%08X register_R15=%08X",address,registers.R15)) end
 log("collision_count_maxima="..table.concat(maxima,","))
 for k,v in pairs(registers or emu.getregisters()) do log(string.format("reg %s=%08X",k,v)) end
 dump("iwram.bin","IWRAM",0x8000);dump("ewram.bin","EWRAM",0x40000)
 dump("vram.bin","VRAM",0x18000);dump("oam.bin","OAM",0x400);dump("palette.bin","PALRAM",0x400)
end
assert(emu.getsystemid()=="GBA")
log("system=GBA guest_writes=none input=joypad-only")
log("initial_core_frame="..initial_frame.." schedule=relative-to-script-start")
log("exec_callbacks=before-instruction collision_count_order=command,event,world sampling=frame-boundary-and-callback")
dump("loaded-rom.bin","ROM",0x800000)
event.on_bus_exec(function(address)
 hooks=hooks+1
 if found then return end
 sample_counts()
 local r=emu.getregisters()
 if r.R0>=0x1A then found=true;capture("invalid-collision-type",r,address)
 else
  valid=valid+1
  if valid<=8 then log(string.format("overlap frame=%d type=%X callback_address=%08X register_R15=%08X attack=%08X",emu.framecount(),r.R0,address,r.R15,r.R4)) end
 end
end,0x0836E370,"overlap-type-observer")
event.on_bus_exec(function(address)
 dispatch_hooks=dispatch_hooks+1
 if found then return end
 sample_counts()
 local r=emu.getregisters()
 local valid_dispatch=r.R1>=0 and r.R1<=34 and r.R1%2==0 and r.R8==0x0836EBA8
  and r.R9==memory.read_u32_le(0x36EBA8+r.R1*2,"ROM")
 if not valid_dispatch then
  found=true;capture("invalid-collision-target",r,address)
 end
end,0x0836EBA4,"dispatch-target-observer")
client.speedmode(800)
local presses={{start,"Start"},{3300,"A"},{3900,"A"},{4560,"Right"},{4800,"Right"},{5040,"Right"},{5280,"A"},{5460,"Left"}}
for n=0,11 do presses[#presses+1]={3360+n*30,"Down"} end
local previous_input = nil
for frame=0,limit-1 do
 local keys={}
 for _,button in ipairs(buttons) do keys[button]=false end
 for _,p in ipairs(presses) do if frame>=p[1] and frame<p[1]+15 then keys[p[2]]=true end end
 local mode=memory.read_u16_le(0x2310,"IWRAM")
 if frame>=5550 and mode==7 then
  if frame%45<5 then keys.B=true end
  if frame%121<5 then keys.A=true end
  if frame%600<180 then keys.Right=true elseif frame%600>=300 and frame%600<480 then keys.Left=true end
 elseif frame>=5550 and mode==9 and frame%60<5 then keys.A=true end
 joypad.set(keys)
 local active={}
 for _,button in ipairs(buttons) do if keys[button] then active[#active+1]=button end end
 local signature=table.concat(active,",")
 if signature~=previous_input then
  log("input relative="..frame.." core="..emu.framecount().." keys="..signature)
  previous_input=signature
 end
 sample_counts()
 if frame%600==0 then log("relative="..frame.." core="..emu.framecount().." mode="..mode.." fighter="..memory.read_u8(0x231A,"IWRAM").." valid="..valid.." dispatch_hooks="..dispatch_hooks) end
 emu.frameadvance()
 if found then break end
end
local released={}
for _,button in ipairs(buttons) do released[button]=false end
joypad.set(released)
if not found then capture("bounded-no-hit") end
log("screenshot_timing=post-frame frame="..emu.framecount().." capture_frame="..capture_frame.." hooks="..hooks.." dispatch_hooks="..dispatch_hooks)
client.screenshot(out.."/screen.png")
local f=assert(io.open(out.."/done.txt","w"));f:write(found and "invalid-observed" or "bounded-no-hit");f:close()
client.exit()
