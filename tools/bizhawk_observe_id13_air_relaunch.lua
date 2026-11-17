-- Ordinary button edges after the real ID13 initializer; no state writes.
local out=assert(userdata.get("output"));assert(out:match("^W:/build/[%w%-%_/]+$"))
local file=assert(io.open(out.."/id13-air-relaunch.txt","wb"))
local INIT,READY,BOOST,SPENT=0x08D3F200,0x08D3F280,0x08D3F500,0x08D3F700
local state={boost={},events={},counts={}}
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
local function live()
 local p,q=rd(0x0300489C,4),rd(0x030048A0,4)
 local function actor(a)return a>=0x02010018 and a<=0x02010018+51*0x118 and (a-0x02010018)%0x118==0 and (rd(a-8,2)&2)~=0 end
 if not(actor(p)and actor(q)and rd(p+0x10,1)==0 and rd(p+0x11,1)==13 and
  rd(p+0x14,4)==p and rd(p+0x18,4)==q and rd(q+0x18,4)==p and (rd(p+4,2)&0xF)==0)then return nil end
 return p
end
local function log(label,p,extra)
 state.counts[label]=(state.counts[label]or 0)+1
 if state.counts[label]>32 then return end
 assert(file:write(string.format("event=%s core=%d actor=%08X cb=%08X f4=%04X f6=%04X f8=%04X x=%04X y=%04X vy=%04X ay=%04X A6=%04X A8=%04X AA=%04X held=%04X event_id=%04X command=%08X %s\n",
  label,emu.framecount(),p,rd(p,4),rd(p+4,2),rd(p+6,2),rd(p+8,2),rd(p+0x34,2),rd(p+0x36,2),rd(p+0x44,2),rd(p+0x48,2),rd(p+0xA6,2),rd(p+0xA8,2),rd(p+0xAA,2),rd(p+0x2C,2),rd(p+0xBA,2),rd(p+0xCC,4),extra or "")));file:flush()
end
for _,row in ipairs({{INIT,"init"},{READY,"ready"},{BOOST,"boost"},{SPENT,"spent"}})do
 local at,label=row[1],row[2];assert(rd(at,4)==0xE52DE004,"ID13 callback prologue")
 event.on_bus_exec(function()
  local r=emu.getregisters();local p=live()
  if not p or r.R4~=p or r.R5~=p+0xAC or rd(0x03002310,2)~=7 then return end
  if label=="init" and not state.actor then state.actor=p;state.start=emu.framecount()end
  if p~=state.actor then return end
  local count=rd(p+0xA8,1)
  if label=="boost" then state.boost[count]=true end
  if label=="spent" then state.spent=count==3;if count~=3 then state.failure="unexpected-spent-count" end end
  log(label,p,"count="..count)
 end,at,"ID13-air-"..label)
end
assert(rd(0x08012874,4)==0xE92D403F,"native event setter")
event.on_bus_exec(function()
 local r=emu.getregisters();local p=live()
 if not p or p~=state.actor or rd(r.R13+8,4)~=p+0xAC or r.R14<INIT or r.R14>=0x08D3FA00 then return end
 local event=rd(r.R13,4);local count=rd(p+0xA8,1)
 if event==0x72 then state.events[count]=true end
 log("set-event",p,string.format("selected=%04X count=%d lr=%08X",event,count,r.R14))
end,0x08012874,"ID13-air-event")
for _,at in ipairs({0x08D3F394,0x08D3F564,0x08D3F768})do
 assert(rd(at,4)==0xE3500000,"landing helper return test")
 event.on_bus_exec(function()
  local r=emu.getregisters();local p=live()
  if p~=state.actor or not p or r.R4~=p or r.R5~=p+0xAC or r.R0==0 then return end
  log("landing-return",p,string.format("result=%08X site=%08X",r.R0,at))
  if state.spent and state.boost[3]and state.events[3]then state.landing=emu.framecount();state.next_callback=rd(p,4)end
 end,at,"ID13-air-land-"..string.format("%X",at))
end
assert(rd(0x083525C4,4)==0xE12FFF18,"actual actor callback dispatch")
event.on_bus_exec(function()
 if not state.landing or state.ordinary or emu.framecount()<=state.landing then return end
 local r=emu.getregisters();local p=live()
 if p==state.actor and r.R4==p and r.R8==state.next_callback and r.R8>=0x08350000 and r.R8<0x08380000 and (r.R8&3)==0 then
  state.ordinary=emu.framecount();log("ordinary-callback",p,string.format("target=%08X",r.R8))
 end
end,0x083525C4,"ID13-air-ordinary-return")
local function input(keys,stage,mode)
 if not state.actor or stage~="battle" or mode~=7 then return end
 for k in pairs(keys)do keys[k]=false end
 local p=live();if p~=state.actor or (rd(0x03004529,1)&0xF)~=0 then return end
 if (rd(p+8,2)&0x4000)~=0 then state.failure="unexpected-evolution";return end
 local count=rd(p+0xA8,1)
 if state.request and count>state.request then
  log("press-ack",p,"requested_after="..state.request);state.request=nil;return
 end
 if state.request then
  if emu.framecount()-state.request_core>60 then state.failure="button-not-acknowledged";return end
  keys.A=true;return
 end
 if rd(p,4)==READY and (rd(p+0xA8,2)&0x100)==0 and count<3 then
  state.request=count;state.request_core=emu.framecount();keys.A=true
  log("press-A",p,"requested_after="..count)
 end
end
local function outcome()
 if state.failure then return "failure:"..state.failure end
 if not state.actor then return nil end
 local p=live()
 if p~=state.actor or rd(0x03002310,2)~=7 then return "failure:ID13-left-battle" end
 if emu.framecount()-state.start>1200 then return "failure:ID13-air-deadline" end
 if state.ordinary and emu.framecount()>state.ordinary and (rd(p+6,2)&1)==0 and rd(p,4)~=INIT and rd(p,4)~=READY and rd(p,4)~=BOOST and rd(p,4)~=SPENT then
  for n=1,3 do if not(state.boost[n]and state.events[n])then return "failure:missing-relaunch-witness" end end
  log("landed",p);return "id13-three-relaunches-and-landing"
 end
end
local function finish()
 local names={};for name in pairs(state.counts)do names[#names+1]=name end;table.sort(names)
 for _,name in ipairs(names)do assert(file:write(string.format("summary event=%s count=%d\n",name,state.counts[name])))end
 assert(file:write("complete=true\n"));file:close()
end
assert(file:write("start readonly=true controller=actual-ready-release-press-ack hooks=9\n"));file:flush()
return{input=input,outcome=outcome,finish=finish}
