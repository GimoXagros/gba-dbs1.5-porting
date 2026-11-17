-- One ordinary late jump; observe the real airborne return without editing state.
local f=assert(io.open("W:/tools/bizhawk_probe_evolution_id14_r2.lua","rb"))
local source=assert(f:read("*a"));f:close()
local policy=[==[
local air={state="unarmed"}
local function music_air_input(keys,stage,mode)
 if stage~="battle" or mode~=7 or (music_read(0x03004529,1)&0xF)~=0 then return end
 local p,q=music_read(0x0300489C,4),music_read(0x030048A0,4)
 if not(actor(p) and actor(q) and music_read(p+0x10,1)==0 and music_read(q+0x10,1)==1 and
  music_read(p+0x11,1)==14 and music_read(p+0x14,4)==p and music_read(p+0x18,4)==q and
  music_read(q+0x18,4)==p and (music_read(p+4,2)&0xF)==0 and (music_read(p+8,2)&0x4000)~=0)then return end
 local now,t=emu.framecount(),signed(p+0x6A)
 if air.actor and air.actor~=p then return end
 if air.state=="unarmed" and t>48 then air.actor=p;air.state="armed" end
 if air.state=="armed" and t>=47 and t<=48 then air.state="window" end
 if (air.state=="armed" or air.state=="window") and t<47 then
  air.state="missed";music_log("air-jump-missed",emu.getregisters(),"timer="..t)
 end
 if air.state=="window" and t>=47 and t<=48 then
  music_log("air-jump-window",emu.getregisters(),string.format("actor=%08X timer=%d callback=%08X flags6=%04X flagsA=%04X held=%04X",p,t,music_read(p,4),music_read(p+6,2),music_read(p+0xA,2),music_read(p+0x2C,2)))
 end
 if air.state=="window" and t>=47 and t<=48 and music_read(p,4)==0x0835620C and
  (music_read(p+6,2)&0x61)==0 and (music_read(p+0xA,2)&0x1000)==0 and (music_read(p+0x2C,2)&0x40)==0 then
  air.state="held";air.until_frame=now+20
  music_log("air-jump-trigger",emu.getregisters(),string.format("actor=%08X timer=%d flags6=%04X callback=%08X",p,t,music_read(p+6,2),music_read(p,4)))
 end
 if air.state=="held" then
  for key in pairs(keys)do keys[key]=false end
  if now<air.until_frame then keys.A=true else
   air.state="done";music_log("air-jump-release",emu.getregisters(),"timer="..t)
  end
 end
end
]==]
local before='local function music_pause_input(keys,stage,mode)'
local code='source=replace(source,'..string.format('%q',before)..','..string.format('%q',policy..before)..')\n'
before=' music_pause_input(keys,stage,mode)\\n joypad.set(keys)'
local after=' music_pause_input(keys,stage,mode)\\n music_air_input(keys,stage,mode)\\n joypad.set(keys)'
code=code..'source=replace(source,'..string.format('%q',before)..','..string.format('%q',after)..')\n'
local anchor=']=]\nlocal a,b=source:find(before,1,true)'
local a,b=source:find(anchor,1,true)
assert(a and not source:find(anchor,b+1,true),"unique held-jump extension boundary")
source=source:sub(1,a-1)..code..source:sub(a)
assert(load(source,"@reviewed-ID14-air-return","t",_ENV))()
