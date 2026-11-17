-- Inspect the current native Shoot renderer from our own healthy campaign checkpoint.
local ROM="574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"
local out,ref=assert(userdata.get("output")),assert(userdata.get("checkpoint_dir"))
assert(out:match("^W:/build/[%w%-%_/]+$") and ref:match("^W:/build/[%w%-%_/]+$") and out~=ref)
assert(emu.getsystemid()=="GBA" and userdata.get("probe_sha256")==ROM)
local SOURCE_CORE,MAX_FRAMES=89405,1800
local SHADOW,END_SHADOW,TILES=0x03001428,0x03001828,0x02000000
local REF_NAME="41-healthy-activation"
local fields={{"iwram","IWRAM",0x8000},{"ewram","EWRAM",0x40000},{"vram","VRAM",0x18000},
              {"palette","PALRAM",0x400},{"oam","OAM",0x400}}
local buttons={"A","B","Select","Start","Right","Left","Up","Down","R","L","Power"}
local keys={}
local seen,ring,last={}, {}, {}
local log,invalid,first_out,first_large
local serial,entry=0,0
local function read_file(path)
 local f=assert(io.open(path,"rb"));local data=assert(f:read("*a"));assert(f:close());return data
end
local function write(name,data)
 local f=assert(io.open(out.."/"..name,"wb"));assert(f:write(data));assert(f:close())
end
local function read(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d)end
 if n==2 then return memory.read_u16_le(o,d)end
 return memory.read_u32_le(o,d)
end
local function phase()return read(0x03002310,2)end
local function emit(line)
 assert(log:write(line.."\n"));assert(log:flush())
end
local function registers(r)
 local result={}
 for i=0,15 do result[#result+1]=string.format("r%d=%08X",i,r["R"..i])end
 result[#result+1]=string.format("cpsr=%08X spsr=%08X",r.CPSR,r.SPSR or 0)
 return table.concat(result," ")
end
local function keep(kind,r,detail)
 serial=serial+1
 local row=string.format("seq=%d entry=%d core=%d kind=%s mode=%d stage=%d %s %s",
  serial,entry,emu.framecount(),kind,phase(),read(0x0300231E,1),detail or "",registers(r))
 ring[(serial-1)%128+1]=row
 last[kind]=row
 return row
end
local function retain(name,line)
 if seen[name]then return end
 seen[name]=true
 emit("first_"..name.." "..line)
end
local function address_hex(a)return string.format("%08X",a&0xFFFFFFFF)end
local function all_words(at,words)
 local hex={}
 for i=0,words-1 do hex[#hex+1]=address_hex(read(at+4*i,4))end
 return table.concat(hex,",")
end
local function detail(r)
 local p=r.R5
 return string.format("presentation=%08X flags=%04X tile=%04X event=%04X layout=%04X command=%04X command_base=%s p1=%s p0=%s words=%s",
  p,read(p+8,2)&0xFFFF,read(p+0x14,2)&0xFFFF,read(p+0xE,2)&0xFFFF,
  read(p+0x18,2)&0xFFFF,read(p+0x1A,2)&0xFFFF,address_hex(read(p+0x20,4)),
  address_hex(read(p+0x44,4)),address_hex(read(p+0x48,4)),all_words(p,20))
end
local function predecessor(name)
 for _,label in ipairs({"dispatch","count-load","layout-load","layout-ready","sprite-write","outside-oam"})do
  if last[label] then emit(name.." "..last[label])end
 end
end
local function hook(pc,opcode,name,callback)
 assert(read(pc,4)==opcode,"opcode "..name)
 event.on_bus_exec(function()
  if invalid or phase()~=7 or read(0x0300231E,1)~=11 then return end
  callback(emu.getregisters())
 end,pc,"shoot-renderer-diagnostic-"..name)
end
local function install()
 assert(read(0x086FEBE8,4)==SHADOW and read(0x086FEBEC,4)==0x030012CA)
 hook(0x08012C44,0xE12FFF19,"dispatch",function(r)
  entry=entry+1
  keep("dispatch",r,string.format("selected=%08X saved_caller=%s %s",r.R9,
   address_hex(read(r.R13+24,4)),detail(r)))
 end)
 hook(0x086FEA58,0xE5D00000,"count-load",function(r)
  keep("count-load",r,string.format("cursor_base=%08X cursor_owner=%08X cursor_initial=%d saved_caller=%s presentation=%08X",
   r.R12,r.R0,read(r.R0,1),address_hex(read(r.R13+28,4)),r.R5))
 end)
 hook(0x086FEAA4,0xE59A2000,"layout-load",function(r)
  keep("layout-load",r,string.format("layout_entry=%08X source_count=%s part_pointer=%s presentation=%08X",
   r.R10,address_hex(read(r.R10,4)),address_hex(read(r.R10+4,4)),r.R5))
 end)
 hook(0x086FEAA8,0xE59AA004,"layout-ready",function(r)
  local raw=string.format("layout_entry=%08X loaded_count=%d part_pointer=%s presentation=%08X oam_cursor=%d",
   r.R10,r.R2,address_hex(read(r.R10+4,4)),r.R5,r.R0)
  local row=keep("layout-ready",r,raw)
  if not first_large and r.R2>127-r.R0 then
   first_large=row;retain("count_exceeds_capacity",row);predecessor("count_context")
  end
 end)
 hook(0x086FEAE8,0xE1CC30B0,"sprite-write",function(r)
  local ptr=r.R12
  local slot=(ptr-SHADOW)//8
  local native_tiles=TILES+slot*32
  local raw=string.format("destination=%08X slot=%d y=%d tile_destination=%08X native_tiles=%08X remaining=%d presentation=%08X display_count=%d",
   ptr,slot,r.R3&0xFFFF,r.R14,native_tiles,r.R2,r.R5,r.R0)
  if ptr<SHADOW or ptr>=END_SHADOW or (ptr-SHADOW)%8~=0 then
   local row=keep("outside-oam",r,raw)
   if not first_out then first_out=row;retain("out_of_bounds_oam",row);predecessor("overflow_context")end
  elseif slot>=126 then
   keep("sprite-write",r,raw)
  end
 end)
 event.on_bus_write(function(a,v,f)
  local value=v&0xFFFF
  if invalid or value<=20 then return end
  local r=emu.getregisters()
  local raw=string.format("address=%08X old=%d value=%d width_flags=%X",a,phase(),value,f)
  invalid={core=emu.framecount(),value=value}
  local row=keep("invalid-mode-write",r,raw)
  write("renderer-first-invalid-mode.txt",row.."\n")
  emit("first_invalid_mode "..row)
  predecessor("mode_context")
 end,0x03002310,"shoot-renderer-diagnostic-mode-write")
end
local function restored()
 assert(emu.framecount()==SOURCE_CORE,"campaign checkpoint frame")
 for _,part in ipairs(fields)do
  local name,domain,size=table.unpack(part)
  assert(memory.getmemorydomainsize(domain)==size,"restored domain extent")
  local expected=read_file(ref.."/"..REF_NAME.."-"..name..".bin")
  assert(#expected==size and memory.read_bytes_as_binary_string(0,size,domain)==expected,"same-epoch restored "..name)
 end
end
local function dump(prefix)
 for _,part in ipairs(fields)do
  write(prefix.."-"..part[1]..".bin",memory.read_bytes_as_binary_string(0,part[3],part[2]))
 end
 write(prefix.."-display.bin",memory.read_bytes_as_binary_string(0x04000000,0x60,"System Bus"))
 client.screenshot(out.."/"..prefix..".png")
end
local function run()
 assert(read_file(ref.."/healthy-activation.txt"):match("^core=89405 input_relative=89404 stage7_consumed=true mode=7 stage=11 "))
 assert(read_file(ref.."/healthy-activation.State"):sub(1,4)=="PK\003\004")
 assert(savestate.load(ref.."/healthy-activation.State",true)==true)
 userdata.clear()
 for k,v in pairs({output=out,checkpoint_dir=ref,probe_sha256=ROM})do userdata.set(k,v);assert(userdata.get(k)==v)end
 restored();assert(savestate.save(out.."/restored.State",true)==true);restored()
 assert(memory.getmemorydomainsize("ROM")==0x1000000)
 write("loaded-rom.bin",memory.read_bytes_as_binary_string(0,0x1000000,"ROM"))
 assert(phase()==7 and read(0x0300231E,1)==11 and read(0x0300450A,2)==6 and read(0x03001302,2)==0 and read(0x03001306,2)==0)
 dump("restored")
 log=assert(io.open(out.."/renderer-trace.txt","wb"))
 emit(string.format("source_core=%d frame_budget=%d input=Right2-then-none guest_writes=none",SOURCE_CORE,MAX_FRAMES))
 install()
 client.speedmode(800)
 for frame=1,MAX_FRAMES do
  for _,key in ipairs(buttons)do keys[key]=false end;keys.Right=frame<=2
  if frame<=3 then emit(string.format("input core=%d relative=%d right=%s",emu.framecount(),frame-1,tostring(keys.Right)))end
  joypad.set(keys);emu.frameadvance()
  assert(emu.framecount()==SOURCE_CORE+frame,"single-frame replay")
  if invalid or phase()>20 then break end
 end
 local outcome=invalid and "first-invalid-game-mode" or (phase()>20 and "invalid-game-mode-unattributed" or "bounded-no-invalid-mode")
 for n=math.max(1,serial-127),serial do emit("retained "..ring[(n-1)%128+1])end
 emit(string.format("summary outcome=%s core=%d game_mode=%d first_outside=%s oversized_layout=%s",
  outcome,emu.framecount(),phase(),tostring(first_out~=nil),tostring(first_large~=nil)))
 assert(log:close());log=nil
 dump("diagnostic");assert(savestate.save(out.."/diagnostic.State",true)==true)
 write("sprite-replay-done.txt",outcome.."\n")
end
local ok,err=pcall(run)
for _,key in ipairs(buttons)do keys[key]=false end;joypad.set(keys)
if not ok then
 if log then pcall(function()log:close()end)end
 write("renderer-error.txt",tostring(err).."\n")
 write("sprite-replay-done.txt","failure:script-error\n")
end
client.exit()
