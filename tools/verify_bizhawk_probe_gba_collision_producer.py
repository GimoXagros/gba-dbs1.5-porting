"""Run the producer observer against mocked Lua APIs; no emulator or ROM I/O."""
import ctypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/bizhawk_probe_gba_collision_producer.lua").read_text(encoding="utf-8")
CHECK = r'''
local function check(kind)
 local hooks,writes,files={},{},{}
 local regs={R0=15,R1=0x030048C8,R4=0x08377704,R15=0x08353D2C}
 local frame=6000
 local actual=15
 local sets,exited=0,false
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k) return ({output="W:/build/mock-producer",combat_profile="approach-jump"})[k] end}
 env.io={open=function(path,mode)
  assert(path:match("^W:/build/mock%-producer/"))
  if mode~="a" then files[path]="" end
  return {write=function(_,s) files[path]=(files[path] or "")..s end,close=function() end}
 end}
 env.event={on_bus_exec=function(fn,address) assert(not hooks[address]);hooks[address]=fn end,
  on_bus_write=function(fn,address) assert(not writes[address]);writes[address]=fn end}
 env.memory={read_u8=function(a,d) assert(d=="IWRAM");return 0 end,
  read_u16_le=function(a,d)
   if a==0x2310 then return 7 end
   if a==0x4D20 then return actual end
   if a==0x377704 and d=="ROM" then return regs.R0 end
   return 0
  end,
  read_u32_le=function(a,d) if a==0x48C8 and d=="IWRAM" then return 0x02010000 end;return 0 end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(a==0 and n==({IWRAM=0x8000,EWRAM=0x40000})[d]);return "snapshot"
  end}
 env.emu={framecount=function() return frame end,getregisters=function() return regs end}
 env.joypad={set=function(keys)
  sets=sets+1
  if sets==1 then assert(keys.Right and not keys.Left and keys.Up==false and keys.A==false and keys.B==false)
  else for _,v in pairs(keys) do assert(v==false) end end
 end}
 env.client={exit=function() assert(files["W:/build/mock-producer/producer-done.txt"]=="producer-journal-complete"); exited=true end}
 env.dofile=function(path)
  assert(path=="W:/tools/bizhawk_probe_gba_collision.lua")
  local count=0;for _ in pairs(writes) do count=count+1 end;assert(count==25)
  frame=12000 -- relative6000 exercises the altered ordinary-input path.
  env.joypad.set({})
  if kind=="invalid-producer" then regs.R0=0xE5
  elseif kind=="overflow" then regs.R1=0x030048C8+12*20 end
  hooks[0x08353D24]()
  writes[0x030048CC](0x030048CC,0,0) -- unsupported write values must not trigger.
  writes[0x03004D20](0x03004D20,0,0)
  regs.R4=0x030048C8
  if kind=="changed" then regs.R0=14 end
  hooks[0x0836E370]()
  if kind=="scratch" then actual=0xE5 end
  hooks[0x0836EB58]()
  for i=1,160 do writes[0x03004D20](0x03004D20,i,0) end
  env.client.exit()
 end
 assert(load(probe_source,"producer-probe","t",env))()
 local trace=assert(files["W:/build/mock-producer/producer-trace.txt"])
 assert(exited and sets==2)
 if kind=="valid" then
  assert(not trace:find("capture=",1,true))
  assert(trace:find("captured=false",1,true))
  local n=0;for _ in trace:gmatch("seq=") do n=n+1 end;assert(n==128)
 else
  local reasons={ ["invalid-producer"]="invalid-producer-type",overflow="producer-list-geometry",changed="list-type-changed-after-producer",scratch="invalid-actual-scratch-type"}
  assert(trace:find("capture="..reasons[kind],1,true))
  assert(files["W:/build/mock-producer/producer-failure-iwram.bin"]=="snapshot")
  assert(files["W:/build/mock-producer/producer-failure-ewram.bin"]=="snapshot")
  local n=0;for _ in trace:gmatch("capture=") do n=n+1 end;assert(n==1)
 end
 assert(trace:find("source_type=",1,true) or kind=="valid")
end
for _,kind in ipairs({"valid","invalid-producer","overflow","changed","scratch"}) do check(kind) end
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
    assert state
    try:
        lua.luaL_openlibs(state)
        script = ("local probe_source=[=[\n" + SOURCE + "]=]\n" + CHECK).encode("utf-8")
        status = lua.luaL_loadbufferx(state, script, len(script), b"producer-self-check", b"t")
        if status == 0:
            status = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if status != 0:
            raise AssertionError(lua.lua_tolstring(state, -1, None).decode("utf-8"))
    finally:
        lua.lua_close(state)
    print("PASS: valid + invalid producer/overflow/overwrite/scratch; 128-entry ring; explicit release; mocked APIs only")


if __name__ == "__main__":
    main()
