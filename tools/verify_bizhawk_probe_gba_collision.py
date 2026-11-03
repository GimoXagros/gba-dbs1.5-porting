"""Exercise the actual Lua probe with mocked APIs; no emulator, ROM, or save I/O."""
import ctypes
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/bizhawk_probe_gba_collision.lua").read_text(encoding="utf-8")
assert "]=]" not in SOURCE
CHECK = r'''
local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local targets={}
for i=1,18 do targets[i]=0x08360000+i*0x100 end
local function registers(index)
 return {R0=8,R1=index*2,R4=0x030048C8,R8=0x0836EBA8,R9=targets[index+1],R15=0x0836EBAC}
end
local function check(hits,reason,callback_address)
 local files,callbacks,keys,regs={},{},nil,nil
 local frame,phase,sets,reads=10,"frame-boundary",0,0
 local dump_phase,screenshot,exited
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k) return ({output="W:/build/mock-collision",frames=1,start_frame=0})[k] end}
 env.io={open=function(path,mode)
  assert(path:match("^W:/build/mock%-collision/"))
  if mode~="a" then files[path]="" end
  return {write=function(_,s) files[path]=(files[path] or "")..s end,close=function() end}
 end}
 env.event={on_bus_exec=function(fn,address)
  assert(address==0x0836E370 or address==0x0836EBA4)
  assert(not callbacks[address]);callbacks[address]=fn
 end}
 env.memory={
  read_u8=function(address,domain)
   assert(domain=="IWRAM")
   return assert(({[0x4C4D]=3,[0x4C4E]=4,[0x4C4C]=5,[0x231A]=14})[address])
  end,
  read_u16_le=function(address,domain) assert(address==0x2310 and domain=="IWRAM");return 7 end,
  read_u32_le=function(address,domain)
   assert(domain=="ROM");reads=reads+1
   return assert(targets[(address-0x36EBA8)/4+1])
  end,
  read_bytes_as_binary_string=function(address,length,domain)
   assert(address==0)
   assert(length==({ROM=0x800000,IWRAM=0x8000,EWRAM=0x40000,VRAM=0x18000,OAM=0x400,PALRAM=0x400})[domain])
   if domain=="IWRAM" then dump_phase=phase end
   return "mock"
  end}
 env.emu={getsystemid=function() return "GBA" end,framecount=function() return frame end,
  getregisters=function() return regs or registers(0) end,
  frameadvance=function()
   phase="before-instruction"
   for _,hit in ipairs(hits) do regs=hit[2];callbacks[hit[1]](hit[1],0,0) end
   frame=frame+1;phase="post-frame"
  end}
 env.joypad={set=function(value)
  sets=sets+1;keys=value
  for _,button in ipairs(buttons) do
   assert(value[button]==(sets==1 and button=="Start"),"incomplete controller reset: "..button)
  end
 end}
 env.client={speedmode=function() end,exit=function() exited=true end,
  screenshot=function() assert(phase=="post-frame" and sets==2);screenshot=true end}
 assert(load(probe_source,"collision-probe","t",env))()
 local trace=assert(files["W:/build/mock-collision/trace.txt"])
 assert(trace:find("capture="..reason,1,true))
 assert(trace:find("collision_count_maxima=3,4,5",1,true))
 assert(trace:find("screenshot_timing=post-frame frame=11",1,true))
 assert(exited and screenshot and sets==2)
 if callback_address then
  assert(dump_phase=="before-instruction")
  assert(trace:find("timing=before-instruction",1,true))
  assert(trace:find(string.format("callback_address=%08X register_R15=%08X",callback_address,regs.R15),1,true))
  assert(files["W:/build/mock-collision/done.txt"]=="invalid-observed")
 else
  assert(dump_phase=="post-frame")
  assert(trace:find("valid=18 hooks=18 dispatch_hooks=18",1,true))
  assert(files["W:/build/mock-collision/done.txt"]=="bounded-no-hit")
 end
 return reads
end
local hits={}
for index=0,17 do
 hits[#hits+1]={0x0836E370,registers(index)}
 hits[#hits+1]={0x0836EBA4,registers(index)}
end
assert(check(hits,"bounded-no-hit")==18)
for _,index in ipairs({-2,1,33,35,36,0x1BA}) do
 local r=registers(0);r.R1=index
 assert(check({{0x0836EBA4,r}},"invalid-collision-target",0x0836EBA4)==0)
end
local r=registers(0);r.R8=r.R8+4
assert(check({{0x0836EBA4,r}},"invalid-collision-target",0x0836EBA4)==0)
r=registers(0);r.R9=targets[2]
assert(check({{0x0836EBA4,r}},"invalid-collision-target",0x0836EBA4)==1)
r=registers(0);r.R9=0xE28DD00C
assert(check({{0x0836EBA4,r}},"invalid-collision-target",0x0836EBA4)==1)
r=registers(0);r.R0=0xE5;r.R15=0x0836E378
assert(check({{0x0836E370,r}},"invalid-collision-type",0x0836E370)==0)
'''


def main():
    lua = ctypes.CDLL(str(ROOT / "local/BizHawk-2.11.1/dll/lua54.dll"))
    ptr, integer = ctypes.c_void_p, ctypes.c_int
    for name, result, args in [
        ("luaL_newstate", ptr, []),
        ("luaL_openlibs", None, [ptr]),
        ("luaL_loadbufferx", integer, [ptr, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]),
        ("lua_pcallk", integer, [ptr, integer, integer, integer, ctypes.c_ssize_t, ptr]),
        ("lua_tolstring", ctypes.c_char_p, [ptr, integer, ptr]),
        ("lua_close", None, [ptr]),
    ]:
        fn = getattr(lua, name)
        fn.restype, fn.argtypes = result, args
    state = lua.luaL_newstate()
    assert state, "could not allocate Lua state"
    try:
        lua.luaL_openlibs(state)
        script = ("local probe_source=[=[\n" + SOURCE + "]=]\n" + CHECK).encode("utf-8")
        status = lua.luaL_loadbufferx(state, script, len(script), b"collision-self-check", b"t")
        if status == 0:
            status = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if status != 0:
            raise AssertionError(lua.lua_tolstring(state, -1, None).decode("utf-8"))
    finally:
        lua.lua_close(state)
    print("PASS: 18 dispatch rows, 10 invalid cases, counts/reset/capture timing; mocked APIs only")


if __name__ == "__main__":
    main()
