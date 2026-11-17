-- Retain native AI parameter and selector provenance in the frozen 75BD campaign.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"isolated output required")
assert(userdata.get("probe_sha256")=="75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F","frozen corrected ROM")
local FIRST,SECOND,OWNER,TABLE=0x0300489C,0x030048A0,0x03003D50,0x080C65F4
local init,ring,serial,closed={}, {},0,false
local function rd(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d) end
 if n==2 then return memory.read_u16_le(o,d) end
 return memory.read_u32_le(o,d)
end
local function bytes(a,n)
 local row={}
 for i=0,n-1 do row[#row+1]=string.format("%02X",rd(a+i,1)&255) end
 return table.concat(row)
end
local function scoped()
 return not closed and rd(0x0300231E,1)==9 and rd(0x0300231C,1)==14 and rd(0x0300232E,1)==2
end
local function record(kind,r,detail,keep_initial)
 serial=serial+1
 local line=string.format("seq=%d core=%d kind=%s mode=%d progress=%d stage=%d cpu=%d FIRST=%08X SECOND=%08X reported_pc=%08X lr=%08X cpsr=%08X r0=%08X r1=%08X r2=%08X r4=%08X r5=%08X r8=%08X r9=%08X %s",
  serial,emu.framecount(),kind,rd(0x03002310,2),rd(0x0300232E,1),rd(0x0300231E,1),rd(0x0300231C,1),
  rd(FIRST,4),rd(SECOND,4),r.R15,r.R14,r.CPSR,r.R0,r.R1,r.R2,r.R4,r.R5,r.R8,r.R9,detail)
 ring[(serial-1)%128+1]=line
 if keep_initial and not init[kind] then init[kind]={seq=serial,line=line} end
end
local function hook(at,opcode,name,fn)
 assert(rd(at,4)==opcode,"AI probe opcode "..name)
 event.on_bus_exec(function()
  if scoped() then fn(emu.getregisters()) end
 end,at,"ai-producer-"..name)
end
local function attach(observer)
 hook(0x080C6D60,0xE350000B,"raw-id",function(r)
  record("raw-id",r,string.format("config_cpu_address=0300231C raw_id=%d",r.R0),true)
 end)
 hook(0x080C6D70,0xE0010190,"row-index",function(r)
  record("row-index",r,string.format("effective_id=%d stride=%d",r.R0,r.R1),true)
 end)
 hook(0x080C6D7C,0xE19100B8,"first-read",function(r)
  local src=r.R8+r.R1
  record("first-read",r,string.format("row_base=%08X offset=%d src=%08X halfword=%04X row17=%s",
   r.R8,r.R1,src,rd(src,2),bytes(src,17)),true)
 end)
 hook(0x080C6D84,0xE1C800B2,"first-copy",function(r)
  local dst=r.R8+2
  record("first-copy",r,string.format("dst=%08X prior=%04X value=%04X",dst,rd(dst,2),r.R0&65535),true)
 end)
 hook(0x080C6EB0,0xE3A00000,"parameter-copies-complete",function(r)
  record("parameter-copies-complete",r,"params_03004D88="..bytes(0x03004D88,0x26),true)
 end)
 hook(0x080C65AC,0xE92D4020,"collider-entry",function(r)
  record("collider-entry",r,string.format("selector=%04X motion=%04X",rd(OWNER,2),rd(0x03003D68,2)))
 end)
 event.on_bus_write(function(address,value,flags)
  if scoped() then
   record("selector-write",emu.getregisters(),string.format("address=%08X old=%04X value=%04X bus_flags=%X",
    address,rd(OWNER,2),value&65535,flags),(value&65535)==15)
  end
 end,OWNER,"ai-producer-selector-write")
 hook(0x080C65EC,0xE7989105,"selector-load",function(r)
  local addr=r.R8+4*r.R5
  record("selector-load",r,string.format("selector=%04X index=%02X table=%08X slot=%08X word=%08X",
   rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4)))
 end)
 hook(0x080C65F0,0xE12FFF19,"target",function(r)
  local addr=r.R8+4*r.R5
  local detail=string.format("pc=080C65F0 selector=%04X index=%02X table=%08X slot=%08X word=%08X target=%08X",
   rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4),r.R9)
  record("target",r,detail)
  if not observer.stopped() and (r.R5<0 or r.R5>=12 or r.R8~=TABLE or r.R9~=rd(addr,4)) then
   observer.fail("first-invalid-ai-collider-target",detail,r)
  end
 end)
end
local function finish()
 assert(not closed,"AI journal closes once")
 closed=true
 local f=assert(io.open(out.."/ai-producer-provenance.txt","wb"))
 assert(f:write(string.format("summary core=%d serial=%d guest_writes=none input=frozen-parent\n",emu.framecount(),serial)))
 local initial={}
 for _,row in pairs(init) do initial[#initial+1]=row end
 table.sort(initial,function(a,b)return a.seq<b.seq end)
 for _,row in ipairs(initial) do assert(f:write("first "..row.line.."\n")) end
 for n=math.max(1,serial-127),serial do assert(f:write(ring[(n-1)%128+1].."\n")) end
 assert(f:close())
end
local function replace(s,old,new)
 local a,b=s:find(old,1,true)
 assert(a and not s:find(old,b+1,true),"unique AI observer insertion")
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function instrument(parent)
 local binding=' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
 parent=replace(parent,binding,binding.."\n attach_ai_probe(observer)")
 local marker='  local f=assert(io.open(out.."/campaign-complete-done.txt","w"))'
 return replace(parent,marker,"  finish_ai_probe()\n"..marker)
end
local f=assert(io.open("W:/tools/bizhawk_probe_type8_corrected_campaign.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=replace(source,"return replace(parent,OLD,NEW)end","return instrument_ai_campaign(replace(parent,OLD,NEW))end")
local env=setmetatable({instrument_ai_campaign=instrument,attach_ai_probe=attach,finish_ai_probe=finish},{__index=_ENV})
assert(load(source,"@frozen-corrected-campaign-ai-provenance","t",env))()
