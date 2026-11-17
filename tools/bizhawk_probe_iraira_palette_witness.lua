-- Read-only Iraira palette data through the first uninterrupted 121 native timer writes.
local ROM="3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F"
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"isolated output required")
assert(userdata.get("probe_sha256")==ROM,"frozen Iraira ROM")
local hooks={
 {0x080C4CC4,0xEA33189D,"palette-dispatch"},{0x08D8AF40,0xE92D4101,"palette-route"},
 {0x08D8AF60,0x0AFFFF66,"palette-route-branch"},{0x08D8AD00,0xE92D47FF,"projector-enter"},
 {0x08D8AD5C,0xE1C200B0,"source-store-42"},{0x08D8AD8C,0xE1C200B0,"source-store-62"},
 {0x08D8ADBC,0xE1C200B0,"source-store-82"},{0x08D8ADEC,0xE1C200B0,"source-store-A2"},
 {0x08D8AE1C,0xE1C200B0,"source-store-C2"},{0x08D8AE2C,0xE8BD47FF,"projector-exit"},
 {0x08D8AC00,0xE92D4007,"cycle"},{0x080136F0,0xE92D403F,"queued-flush"},
 {0x080D1228,0xE8BD4000,"queued-flush-return"},{0x080D0BD0,0xEB12CF8A,"legacy-stage-getter"},{0x080D0BD4,0xE1A01000,"legacy-stage-return"},
 {0x080D0BE4,0xE12FFF19,"legacy-stage-branch"},{0x080D0ED0,0xE92D4000,"retail-stage3-handler"},
 {0x080C932C,0xE1C810B0,"retail-gradient-backdrop"},{0x08377928,0xE1C800B0,"transition-backdrop"},{0x08377BF8,0xE1C800B0,"ready-backdrop"}
}
local palette_ports={0,0x42,0x82,0xC2}
local counts,active_counts,first,last,ring,samples={}, {}, {}, {}, {}, {}
local front_by_stage={}
local serial,ready,closed=0,false,false
local function byte(a)return memory.read_u8(a,"IWRAM")end
local function word(a)return memory.read_u16_le(a,"IWRAM")end
local function scoped()
 return not closed and byte(0x232E)==4 and byte(0x231E)==10 and byte(0x231C)==11
end
local function palette(a)return memory.read_u16_le(a,"PALRAM")end
local function values()
 return string.format("clock=%d phase=%04X gates=%04X,%02X,%02X counters=%d,%d,%d,%d,%d shadow=%04X colors=%04X,%04X,%04X,%04X queue=%04X legacy2568=%04X,%04X legacy4668=%04X",
  word(0x4500),word(0x2568),word(0x4506),byte(0x260B),byte(0x4529),word(0x3D30),word(0x3D32),word(0x3D34),
  word(0x3D36),word(0x3D38),word(0x2654),palette(0),palette(0x42),palette(0x82),palette(0xC2),
  word(0x1D68),word(0x2578),word(0x2580),word(0x4678))
end
local function record(kind,r,detail)
 serial=serial+1
 counts[kind]=(counts[kind]or 0)+1
 if #samples>0 then active_counts[kind]=(active_counts[kind]or 0)+1 end
 local line=string.format("seq=%d core=%d kind=%s pc=%08X lr=%08X cpsr=%08X r0=%08X r1=%08X r2=%08X r3=%08X r4=%08X r5=%08X r8=%08X r9=%08X %s %s",
  serial,emu.framecount(),kind,r.R15,r.R14,r.CPSR,r.R0,r.R1,r.R2,r.R3,r.R4,r.R5,r.R8,r.R9,values(),detail or "")
 ring[(serial-1)%256+1]=line
 if not first[kind] then first[kind]={seq=serial,line=line} end
 last[kind]=string.format("%d:%08X:%08X",emu.framecount(),r.R15,r.R14)
end
local function install(observer)
 local stopped=observer.stopped
 observer.stopped=function()return stopped() or ready end
 for _,hook in ipairs(hooks) do
  local address,opcode,kind=table.unpack(hook)
  assert(memory.read_u32_le(address-0x08000000,"ROM")==opcode,"palette witness opcode "..kind)
  event.on_bus_exec(function()
   if not closed and kind=="palette-dispatch" then
    local stage=byte(0x231E)
    if stage<=11 then front_by_stage[stage]=(front_by_stage[stage]or 0)+1 end
   end
   if scoped() then record(kind,emu.getregisters()) end
  end,address,"iraira-palette-"..kind)
 end
 for _,port in ipairs(palette_ports) do
  local kind=string.format("write-%02X",port)
  event.on_bus_write(function(address,value,flags)
   if scoped() then record(kind,emu.getregisters(),string.format("address=%08X old=%04X value=%04X flags=%X",
    address,palette(port),value&65535,flags)) end
  end,0x05000000+port,"iraira-palette-"..kind)
 end
end
local function sample(index,core)
 if index==1 then samples={};active_counts={} end
 local stamp={}
 for _,port in ipairs(palette_ports) do stamp[#stamp+1]=last[string.format("write-%02X",port)] or "none" end
 samples[index]=string.format("sample index=%d core=%d %s last_writers=%s",index,core,values(),table.concat(stamp,","))
 if index==121 then ready=true end
end
local function finish(outcome)
 assert(not closed,"palette journal closes once")
 closed=true
 local path=out.."/iraira-palette-witness"
 local f=assert(io.open(path..".txt","wb"))
 assert(f:write(string.format("summary core=%d serial=%d samples=%d disposition=%s guest_writes=none input=frozen-parent\n",
  emu.framecount(),serial,#samples,outcome)))
 for stage=0,11 do
  assert(f:write(string.format("frontdoor stage=%d total=%d\n",stage,front_by_stage[stage]or 0)))
 end
 local keys={}
 for kind in pairs(counts) do keys[#keys+1]=kind end;table.sort(keys)
 for _,kind in ipairs(keys) do assert(f:write(string.format("count kind=%s total=%d after_first_clock=%d\n",
  kind,counts[kind],active_counts[kind] or 0))) end
 local start={}
 for _,row in pairs(first) do start[#start+1]=row end
 table.sort(start,function(a,b)return a.seq<b.seq end)
 for _,row in ipairs(start) do assert(f:write("first "..row.line.."\n")) end
 for _,line in ipairs(samples) do assert(f:write(line.."\n")) end
 for n=math.max(1,serial-255),serial do assert(f:write(ring[(n-1)%256+1].."\n")) end
 assert(f:close())
 local done=assert(io.open(path.."-done.txt","w"))
 assert(done:write(ready and outcome=="bounded-no-activation" and "palette-witness-121-frames" or "palette-witness-incomplete"))
 assert(done:close())
end
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique palette witness insertion")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function finish_parent(parent)
 local marker='  local f=assert(io.open(out.."/campaign-complete-done.txt","w"));assert(f:write(outcome));f:close()'
 return replace(parent,marker,marker.."\n  finish_palette_probe(outcome)")
end
local function finish_binding(source)
 local marker=[=[ return replace(parent,marker,"  finish_ai_probe()\n  finish_iraira_probe()\n"..marker)]=]
 return replace(source,marker,[=[ return finish_palette_parent(replace(parent,marker,"  finish_ai_probe()\n  finish_iraira_probe()\n"..marker))]=])
end
local f=assert(io.open("W:/tools/bizhawk_probe_ai_aligned_iraira.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,"local function attach(observer)\n","local function attach(observer)\n install_palette_probe(observer)\n")
local clock_tail="core,value,r.R8,r.R9,r.R15,word(0x03002568),word(0x03002654))"
source=replace(source,clock_tail,clock_tail.."\n  sample_palette_clock(#clock,core)")
local hook_return=[==[ return replace(source,marker,[=[ return replace(parent,marker,"  finish_ai_probe()\n  finish_iraira_probe()\n"..marker)]=])]==]
source=replace(source,hook_return,[==[ return bind_palette_finish(replace(source,marker,[=[ return replace(parent,marker,"  finish_ai_probe()\n  finish_iraira_probe()\n"..marker)]=]))]==])
local env=setmetatable({install_palette_probe=install,sample_palette_clock=sample,finish_palette_probe=finish,
 finish_palette_parent=finish_parent,bind_palette_finish=finish_binding},{__index=_ENV})
assert(load(source,"@frozen-aligned-iraira-with-palette-witness","t",env))()
