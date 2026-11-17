-- Reuse the frozen read-only checkpoint/input observer and add source-contact milestones.
local f=assert(io.open("W:/tools/bizhawk_probe_child_event_producer.lua","rb"))
local source=assert(f:read("*a"));f:close()
local function replace(old,new)
 local a,b=source:find(old,1,true)
 assert(a and not source:find(old,b+1,true),"unique contact adaptation: "..old)
 source=source:sub(1,a-1)..new..source:sub(b+1)
end
replace('local ROM="574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76"',
 'local ROM="5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC"')
replace('local function install()',[[
local contact={first=false,wait=false,release=false,effect=false,event2=false,complete=false}
local function install()
 local function milestone(pc,opcode,name)
  hook(pc,opcode,name,function(r)
   if r.R4~=ACTOR_OWNER or not child(r.R5)then return end
   if not contact[name]then emit("contact "..keep(name,r,owner_detail(r.R5)))end
   contact[name]=true
  end)
 end
 milestone(0x08D8C864,0xE92D5FFF,"first")
 milestone(0x08D8C910,0xE92D5FFF,"wait")
 milestone(0x08D8C980,0xE92D5FFF,"release")
 hook(0x0835972C,0xE92D403B,"effect-constructor",function(r)
  if r.R14~=0x08D8C8AC then return end
  local target=read(ACTOR_OWNER+0x18,4)
  assert(r.R5==target and r.R11==0 and read(r.R13,4)==3 and read(r.R13+4,4)==0
   and read(r.R13+8,4)==0 and read(r.R13+12,4)==0 and read(r.R13+16,4)==target,"source effect ABI")
  contact.effect=true
  emit("contact "..keep("effect",r,string.format("target=%08X flags=%04X",target,read(target+8,2))))
 end)
 hook(0x08D8C9BC,0xE8BD5FFF,"retirement-complete",function(r)
  if r.R4~=ACTOR_OWNER then return end
  local target=read(ACTOR_OWNER+0x18,4)
  assert(contact.first and contact.wait and contact.release and contact.effect and contact.event2,"source milestones")
  assert(read(0x0300450A,2)&0x50==0 and read(target+8,2)&0x10==0,"source flags retired")
  contact.complete=true
  emit("contact "..keep("retired",r,string.format("target=%08X flags=%04X target_flags=%04X",target,read(0x0300450A,2),read(target+8,2))))
 end)
]])
replace('  local value=v&0xFFFF;local r=emu.getregisters()',
 '  local value=v&0xFFFF;local r=emu.getregisters()\n  if value==2 then contact.event2=true end')
replace('hook(0x0836F77C,0xE59F8108,"legacy-child-route"','hook(0x0836F77C,0xEA28741F,"source-child-route"')
replace('  if invalid or phase()>20 then break end','  if invalid or phase()>20 or contact.complete then break end')
replace(' local outcome=invalid and "invalid-child-event-captured" or (phase()>20 and "unexpected-invalid-game-mode" or "bounded-no-invalid-child-event")',
 ' local outcome=invalid and "invalid-child-event-captured" or (phase()>20 and "unexpected-invalid-game-mode" or (contact.complete and "source-child-contact-retired" or "bounded-contact-incomplete"))')
-- Only the two marker writes change; the snapshot and input cleanup order is retained.
local count
source,count=source:gsub('child%-event%-done%.txt','child-contact-done.txt');assert(count==2)
assert(load(source,"@frozen-child-event-positive","t",_ENV))()
