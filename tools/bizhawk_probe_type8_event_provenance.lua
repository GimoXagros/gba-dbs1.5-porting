-- Read-only predecessor journal; the frozen campaign owns all input and writes.
local out=assert(userdata.get("output"))
assert(out:match("^W:/build/[%w%-%_/]+$"),"isolated output required")
assert(userdata.get("probe_sha256")=="933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775","frozen ROM")
local file=assert(io.open(out.."/type8-event-provenance.txt","wb"))
local ring,counts,serial,closed={}, {},0,false
local function rd(a,n)
 local d,o
 if a>=0x02000000 and a+n<=0x02040000 then d,o="EWRAM",a-0x02000000
 elseif a>=0x03000000 and a+n<=0x03008000 then d,o="IWRAM",a-0x03000000
 elseif a>=0x08000000 and a+n<=0x09000000 then d,o="ROM",a-0x08000000
 else return -1 end
 if n==1 then return memory.read_u8(o,d)end
 if n==2 then return memory.read_u16_le(o,d)end
 return memory.read_u32_le(o,d)
end
local function owner()
 if rd(0x03002310,2)~=7 or rd(0x0300231E,1)~=8 then return nil end
 local p,q=rd(0x0300489C,4),rd(0x030048A0,4)
 local function actor(a)return a>=0x02010018 and a<=0x02010018+51*0x118 and (a-0x02010018)%0x118==0 and (rd(a-8,2)&2)~=0 end
 if actor(p)and actor(q)and rd(q+0x10,1)==1 and rd(q+0x11,1)==13
  and rd(q+0x18,4)==p and rd(p+0x18,4)==q and (rd(q+4,2)&15)==1 then return q end
end
local function words(a,n)
 local t={};for i=0,n-1 do t[#t+1]=string.format("%08X",rd(a+i*4,4))end
 return table.concat(t,",")
end
local function record(kind,r,q,detail)
 serial=serial+1;counts[kind]=(counts[kind]or 0)+1
 ring[(serial-1)%256+1]=string.format("seq=%d core=%d kind=%s actor=%08X cb=%08X saved_cb=%08X event=%04X P1=%08X flags6=%04X flags8=%04X r0=%08X r1=%08X r3=%08X r4=%08X r5=%08X r8=%08X lr=%08X pc=%08X cpsr=%08X %s",
  serial,emu.framecount(),kind,q,rd(q,4),rd(q+0x84,4),rd(q+0xBA,2),rd(q+0xF0,4),rd(q+6,2),rd(q+8,2),
  r.R0,r.R1,r.R3,r.R4,r.R5,r.R8,r.R14,r.R15,r.CPSR,detail)
end
local function hook(at,opcode,name,fn)
 assert(rd(at,4)==opcode,"provenance opcode "..name)
 event.on_bus_exec(function()
  if closed then return end
  local q=owner();if not q then return end
  fn(emu.getregisters(),q)
 end,at,"type8-provenance-"..name)
end
hook(0x08012874,0xE92D403F,"setter-entry",function(r,q)
 if rd(r.R13+8,4)==q+0xAC then
  record("setter-entry",r,q,string.format("selected=%08X stack=%s",rd(r.R13,4),words(r.R13,3)))
 end
end)
hook(0x08012884,0xE1C530BE,"event-store",function(r,q)
 if r.R5==q+0xAC then
  record("event-store",r,q,string.format("selected=%08X saved_lr=%08X table=%08X row=%s",r.R3,rd(r.R13+0x18,4),rd(r.R4,4),words(rd(r.R4,4)+r.R3*16,4)))
 end
end)
hook(0x083555D0,0xE92D4008,"metadata-entry",function(r,q)
 if r.R4==q and r.R5==q+0xAC then record("metadata-entry",r,q,"record="..words(r.R1,8))end
end)
hook(0x083525C4,0xE12FFF18,"actor-dispatch",function(r,q)
 if r.R4==q then record("actor-dispatch",r,q,string.format("target=%08X",r.R8))end
end)
hook(0x0836A69C,0xE92D4013,"hitstop-entry",function(r,q)
 if rd(r.R13+0x10,4)==q then record("hitstop-entry",r,q,"stack="..words(r.R13,5))end
end)
hook(0x0836EC90,0x159F1B20,"type8-air-selector",function(r,q)
 if r.R5==q then record("type8-air-selector",r,q,string.format("conditional_NE=%s literal=%08X scratch=%s",tostring((r.CPSR&0x40000000)==0),rd(0x0836F7B8,4),words(0x03004D20,4)))end
end)
hook(0x0836F3B8,0xE5D50011,"damage-table-entry",function(r,q)
 if r.R5==q then record("damage-table-entry",r,q,string.format("id=%d table=%08X indexed=%08X subtype=%d",rd(q+0x11,1),r.R1,rd(r.R1+rd(q+0x11,1)*4,4),rd(0x03004D26,1)))end
end)
hook(0x0836F3CC,0xE92D0010,"damage-record-selected",function(r,q)
 if r.R5==q then record("damage-record-selected",r,q,"record="..words(r.R1,8))end
end)
local function finish()
 assert(not closed,"provenance closes once");closed=true
 assert(file:write(string.format("summary serial=%d core=%d timing=before-instruction guest_writes=none input=frozen-parent\n",serial,emu.framecount())))
 local names={};for k in pairs(counts)do names[#names+1]=k end;table.sort(names)
 for _,k in ipairs(names)do assert(file:write(string.format("count %s=%d\n",k,counts[k])))end
 for n=math.max(1,serial-255),serial do assert(file:write(ring[(n-1)%256+1].."\n"))end
 assert(file:close())
end
local f=assert(io.open("W:/tools/bizhawk_probe_campaign_complete.lua","rb"))
local source=assert(f:read("*a"));f:close()
local before="  log:close()"
local a,b=source:find(before,1,true)
assert(a and not source:find(before,b+1,true),"one frozen close insertion")
local code=source:sub(1,a-1)..before..";finish_provenance()"..source:sub(b+1)
local env=setmetatable({finish_provenance=finish},{__index=_ENV})
assert(load(code,"@frozen-campaign-with-readonly-provenance","t",env))()
