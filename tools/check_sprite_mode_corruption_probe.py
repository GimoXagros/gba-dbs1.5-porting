"""In-process Lua checks for the current-ROM sprite overflow replay."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

from check_campaign_complete_probe import host, quote
from verify_gba_shoot_entry_capture import ROOT, sha


PIN = 'E281FF8D3CC2D61289A6C6CC1AD6217E6C18F11193AFC2B3935203F68E36EFB9'
ROM = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
PROBE = 'tools/bizhawk_probe_sprite_mode_corruption.lua'
FIXTURE = r'''
for _,case in ipairs({"invalid","bounded","bad-state"})do
 local out,ref="W:/build/sprite-replay-mock","W:/build/current-healthy-reference"
 local data={output=out,checkpoint_dir=ref,probe_sha256=romhash}
 local sizes={ROM=0x1000000,IWRAM=0x8000,EWRAM=0x40000,VRAM=0x18000,PALRAM=0x400,OAM=0x400}
 local bases={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000,VRAM=0x06000000,PALRAM=0x05000000,OAM=0x07000000}
 local mem,created,hooks,inputs={},{},{},{}
 local core,regs,inside,exited,load_count=89405,{},false,false,0
 for n=0,15 do regs["R"..n]=0 end;regs.CPSR=0x60000010
 local function put(a,value,n)for i=0,n-1 do mem[a+i]=(value>>(8*i))&255 end end
 local function get(a,n)local v=0;for i=0,n-1 do v=v|((mem[a+i]or 0)<<(8*i))end;return v end
 local function fire(at,values)
  for k,v in pairs(values)do regs[k]=v end
  regs.R15=at+4;inside=true;hooks[at]();inside=false
 end
 for address,value in pairs(words)do put(address,value,4)end
 put(0x03002310,7,2);put(0x0300231E,11,1);put(0x0300450A,6,2)
 put(0x030012CA,126,1);put(0x03007E7C+28,0x08376ABC,4)
 put(0x020119EC+0x48,0x085DB300,4)
 put(0x085DB400,700,4);put(0x085DB404,0x085DB410,4)
 local function step()
  assert(not inside)
  if case=="invalid" and core==89407 then
   fire(0x08012C44,{R5=0x020119EC,R9=0x086FF240,R13=0x03007E80})
   fire(0x086FEA58,{R12=0x03001428,R0=0x030012CA,R13=0x03007E7C})
   fire(0x086FEAA4,{R0=126,R10=0x085DB400})
   fire(0x086FEAA8,{R2=700})
   for i=126,477 do
    fire(0x086FEAE8,{R0=i,R2=700-i+126,R10=0x085DB410,R12=0x03001428+8*i,R14=0x02000000+32*i,R3=77})
   end
   inside=true;regs.R15=0x086FEAF0;hooks[0x03002310](0x03002310,77,0x2000);inside=false
   put(0x03002310,77,2)
  end
  core=core+1
 end
 local function read_file(path)
  local name=path:match("[^/]+$")
  if name=="healthy-activation.txt" then return "core=89405 input_relative=89404 stage7_consumed=true mode=7 stage=11 P1HP=8 P2HP=37\n"end
  if name=="healthy-activation.State" then return "PK\003\004capture"end
  local domain=({iwram="IWRAM",ewram="EWRAM",vram="VRAM",palette="PALRAM",oam="OAM"})[name:match("41%-healthy%-activation%-(%a+)%.bin")]
  assert(domain,name)
  return string.rep("a",sizes[domain])
 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)return data[k]end,set=function(k,v)data[k]=v end,clear=function()data={}end}
 env.emu={getsystemid=function()return "GBA"end,framecount=function()return core end,frameadvance=step,getregisters=function()return regs end}
 env.event={on_bus_exec=function(fn,at)assert(not hooks[at]);hooks[at]=fn end,on_bus_write=function(fn,at)assert(at==0x03002310);hooks[at]=fn end}
 env.memory={read_u8=function(a,d)return get(bases[d]+a,1)end,read_u16_le=function(a,d)return get(bases[d]+a,2)end,
  read_u32_le=function(a,d)return get(bases[d]+a,4)end,getmemorydomainsize=function(d)return sizes[d]end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(not inside)
   return string.rep(case=="bad-state" and d=="IWRAM" and "b" or "a",n)
  end}
 env.joypad={set=function(keys)
  for k,v in pairs(keys)do assert(k=="Right" or not v)end
  inputs[#inputs+1]=keys.Right==true
 end}
 env.client={screenshot=function(path)assert(not inside);created[path]="PNG"end,speedmode=function(n)assert(n==800)end,
             exit=function()exited=true end}
 env.savestate={load=function(path,quiet)
  assert(path==ref.."/healthy-activation.State" and quiet);load_count=load_count+1;return true
 end,save=function(path,quiet)assert(quiet and not inside);created[path]="STATE";return true end}
 env.io={open=function(path,mode)
  if mode=="rb"then return {read=function()return read_file(path)end,close=function()return true end}end
  assert(mode=="wb" and not created[path])
  if path:match("sprite%-replay%-done.txt$") and case~="bad-state" then
   assert(created[out.."/diagnostic.State"] and created[out.."/diagnostic.png"])
  end
  local f={buffer=""}
  function f:write(bytes) self.buffer=self.buffer..bytes;return true end
  function f:flush()return true end
  function f:close()created[path]=self.buffer;return true end
  return f
 end}
 assert(load(probe,"@actual-sprite-replay","t",env))()
 assert(exited and load_count==1 and inputs[#inputs]==false)
 local done=created[out.."/sprite-replay-done.txt"]
 if case=="bad-state"then
  assert(done=="failure:script-error\n" and not hooks[0x086FEAE8] and #inputs==1)
  assert(created[out.."/renderer-error.txt"]:find("same%-epoch restored iwram"))
 else
  local trace=created[out.."/renderer-trace.txt"]
  assert(#created[out.."/loaded-rom.bin"]==0x1000000 and trace)
  assert(inputs[1] and inputs[2])
  for i=3,#inputs do assert(not inputs[i])end
  if case=="invalid"then
   assert(done=="first-invalid-game-mode\n" and core==89408 and #inputs==4)
   assert(trace:find("first_out_of_bounds_oam") and trace:find("destination=03001828 slot=128"))
   assert(trace:find("loaded_count=700") and trace:find("saved_caller=08376ABC"))
   assert(trace:find("destination=03002310 slot=477") and trace:find("address=03002310 old=7 value=77"))
   local n=0;for _ in trace:gmatch("\nretained ")do n=n+1 end;assert(n==128)
  else
   assert(done=="bounded-no-invalid-mode\n" and core==91205 and #inputs==1801)
   assert(not created[out.."/renderer-first-invalid-mode.txt"])
  end
 end
end
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    raw = (ROOT / PROBE).read_bytes()
    assert sha(raw) == PIN
    rom = (ROOT / 'build/repro-v86-20261117-a/current-candidate.gba').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM
    words = {int(a, 16): int(b, 16) for a, b in re.findall(rb'hook\(0x([0-9A-F]+),0x([0-9A-F]+),', raw)}
    assert len(words) == 5
    words |= {0x086FEBE8: 0x03001428, 0x086FEBEC: 0x030012CA}
    assert all(struct.unpack_from('<I', rom, a-0x08000000)[0] == b for a, b in words.items())
    setup = f'local probe={quote(raw)}\nlocal romhash="{ROM}"\nlocal words='
    setup += '{' + ','.join(f'[{a}]={b}' for a, b in words.items()) + '}\n'
    runner = host.lua_check
    FunctionType(runner.__code__, dict(runner.__globals__, CHECK=setup+FIXTURE))('', '', '')
    result = dict(status='SPRITE_MODE_CORRUPTION_LUA_QA_PASS', wrapper_sha256=PIN, rom=ROM,
                  hooks=5, bound=1800, case_count=3, no_write_api=True, input='Right2 then released',
                  invalid_mode_immediate_scalar_and_next_boundary_snapshot=True, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
