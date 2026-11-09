-- Input-only interception wrapper; frozen observer, restore checks and hit gates unchanged.
local target="1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC"
assert(userdata.get("probe_sha256")==target,"reviewed child rectangle ROM required")
local f=assert(io.open("W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua","rb"))
local source=assert(f:read("*a"));f:close()
source=source:gsub("\r\n","\n") -- Lua long-string anchors use normalized line endings.
local function replace_once(old,new,label)
 local a,b=source:find(old,1,true)
 assert(a and not source:find(old,b+1,true),"unique frozen "..label)
 source=source:sub(1,a-1)..new..source:sub(b+1)
end
replace_once("6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331",target,"ROM binding")
local old=[=[   -- Neutral jump, followed by repeated separate attack edges; no Up/Down variants.
   keys.A=(frame-1)%60==0;keys.B=frame>=7 and (frame-7)%12==0
   local dx=signed(w(Q+0x34))-signed(w(P+0x34))
   if frame>6 and math.abs(dx)>0x180 then keys.Right=dx>0;keys.Left=dx<0 end]=]
local policy=[=[   -- Orient while grounded and free, then one B edge at the observed crossing.
   local cb=read(P,4)
   local ready=(cb==0x0835620C or cb==0x083562B4 or cb==0x083562E4) and w(P+6)&1==0 and w(P+0x76)==0
   if ready then
    if w(P+0xB4)&0x4000==0 then keys.Right=true
    else
     local dx=signed(w(Q+0x34))-signed(w(P+0x34))
     local dy=signed(w(Q+0x36))-signed(w(P+0x36))
     local ev=w(Q+0xBA)
     keys.B=w(P+0x2C)&0x80==0 and (ev==1 or ev==4 or ev==5) and dx>=96 and dx<=384 and dy>=128 and dy<=256
    end
   end]=]
replace_once(old,policy,"ordinary-input policy")
assert(load(source,"@reviewed-positive-hit-ground-interception","t",_ENV))()
