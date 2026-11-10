-- Controlled46B3 replay: two transition frames of scalar BG ownership telemetry.
local target="46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B"
assert(userdata.get("probe_sha256")==target,"reviewed reciprocal-owner ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_terminal.lua","rb"))
local source=assert(f:read("*a"));f:close()
local old="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
local a,b=source:find(old,1,true)
assert(a and not source:find(old,b+1,true),"unique frozen ROM binding")
source=source:sub(1,a-1)..target..source:sub(b+1)
local before='if read(Q+0x28,4)~=AUX or read(AUX+0x18,4)~=Q then return "native-guard-aux18-not-upper"end'
local after='if read(Q+0x28,4)~=AUX or read(AUX+0x28,4)~=Q then return "native-guard-aux28-not-upper"end'
local x,y=source:find(before,1,true)
assert(x and not source:find(before,y+1,true),"unique frozen owner predicate")
source=source:sub(1,x-1)..after..source:sub(y+1)
local telemetry=[=[
 local bg_epoch_first,bg_epoch_seen=nil,{}
 local function bg_epoch(label,r)
  if not scene or w(0x03002310)~=7 or b(0x0300231E)~=11 or w(0x0300450A)&0x400==0 then return end
  local core=emu.framecount()
  if not bg_epoch_first then bg_epoch_first=core end
  if core<bg_epoch_first or core>bg_epoch_first+1 then return end
  local key=label..":"..core
  if bg_epoch_seen[key]then return end
  bg_epoch_seen[key]=true
  local planned="none"
  if label:sub(1,4)=="map-"then
   planned=string.format("%04X",(w(0x0400000A)&0xFF)|(read(0x08001030+(r.R0&7),1)<<8))
  end
  log("bg-epoch",string.format("point=%s first_core=%d velocities=%04X,%04X,%04X,%04X map_selector=%02X BG0CNT=%04X planned_BG1CNT=%s %s %s",label,bg_epoch_first,w(0x03002354),w(0x03002356),w(0x030023A4),w(0x030023A6),b(0x030012CE),w(0x04000008),planned,state(),irq_state()),r)
 end
 for _,point in ipairs({
  {0x085E716C,"shake-before"},{0x085E7170,"shake-after"},
  {0x086FF9C0,"guard"},{0x086FF698,"guard-return"},
  {0x080C97B8,"fallback"},
  {0x080D0C18,"clear-before"},{0x080D0C1C,"clear-between"},{0x080D0C20,"clear-after"}
 })do
  local address,label=point[1],point[2]
  hook(address,"bg-epoch-"..label,function(r)bg_epoch(label,r)end)
 end
 for _,point in ipairs({{0x08000FEC,"map-call"},{0x08001010,"map-before"},{0x08001014,"map-after"}})do
  local address,label=point[1],point[2]
  hook(address,"bg-epoch-"..label,function(r)
   if r.R0==0x12 or r.R0==0x21 then bg_epoch(label,r)end
  end)
 end
]=]
local anchor="local function install()\n"
local i,j=source:find(anchor,1,true)
assert(i and not source:find(anchor,j+1,true),"unique frozen hook installation")
source=source:sub(1,j)..telemetry..source:sub(j+1)
assert(load(source,"@reviewed-terminal-BG-epoch-telemetry","t",_ENV))()
