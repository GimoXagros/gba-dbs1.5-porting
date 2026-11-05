"""Exercise the actual Lua route with mocked native state; no emulator/save I/O."""
import ctypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tools/bizhawk_probe_result_languages.lua").read_text(encoding="utf-8")
CHECK = r'''
local buttons={"Up","Down","Left","Right","A","B","L","R","Start","Select","Power"}
local function check(language,kind)
 local callbacks,files,ops={},{},{}
 local frame,mode,title_row,options_row,pending,err,tag=1,0,0,0,0,0,0x20
 local title_callback=0x08090C7C
 local keys,previous={},{}
 local battle_frame,result_frame
 local exited=false
 local prompt_start_count,ignored_prompt_a=0,0
 local expected=({0x080B8210,0x08651AE0,0x086DA640,0x087DFC20})[language+1]
 local title=({0x0808FD08,0x0863A800,0x0863D000,0x0863E000})[language+1]
 local object=0x02013000
 local registers={R5=object,R15=0x080899F4}
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(key) return ({output="W:/build/mock-result",language=language,frames=2500,start_frame=0})[key] end}
 env.io={open=function(path,mode_)
  assert(path:match("^W:/build/mock%-result/"))
  assert(not files["W:/build/mock-result/result-done.txt"],"write after final marker")
  if mode_~="a" then files[path]="" end
  ops[#ops+1]="open:"..path
  return {write=function(_,s) files[path]=(files[path] or "")..s end,
   close=function() ops[#ops+1]="close:"..path end}
 end}
 local function task_slot(address)
  for slot=0,51 do
   local at=0x10000+slot*0x118
   if address>=at and address<at+0x18 then return slot,address-at end
  end
 end
 env.memory={
  read_u8=function(a,d)
   assert(d=="IWRAM")
   if a==0x112F then return tag end
   if a==0x2C5E then return title_row end
   return 0
  end,
  read_u16_le=function(a,d)
   if d=="IWRAM" then
    if a==0x2310 then return mode end
    if a==0x473E then return options_row end
    return 0
   end
   assert(d=="EWRAM")
   local slot,offset=task_slot(a)
   if offset==0x10 then return (slot==0 or slot==1 and mode==3 or slot==2 and mode==14) and 2 or 0 end
   if a==0x10248 then return pending end
   if a==0x1024A then return 0 end
   if a==0x1024C then return err end
   if a==0x1300E then return language==3 and 3 or 0 end
   return 0
  end,
  read_u32_le=function(a,d)
   if d=="ROM" then return assert(({[0x652FC4]=0x080B8210,[0x652FC8]=0x08651AE0,[0x652FCC]=0x086DA640,[0x652FD0]=0x087DFC20})[a]) end
   if d=="IWRAM" then
    if a==0x11E0 then return tag end
    for index=0,4 do if a==0x2A78+index*0x50+0x48 then return title end end
    return 0
   end
   assert(d=="EWRAM")
   local slot,offset=task_slot(a)
   if offset==4 then return ({[0]=0,[1]=0x1000,[2]=0x1500})[slot] or 0 end
   if offset==0 then return slot==1 and title_callback or 0x08015AB4 end
   if a==0x13048 then return expected end
   if a==0x13044 then return 0x080B9004 end
   if a==0x1304C then return 0x080B9144 end
   return 0
  end,
  read_bytes_as_binary_string=function(a,n,d)
   if d=="System Bus" then assert(a==0x04000000 and n==0x60)
   else assert(a==0 and n==({ROM=0x800000,IWRAM=0x8000,EWRAM=0x40000,VRAM=0x18000,PALRAM=0x400,OAM=0x400})[d]) end
   return "mock"
  end}
 env.event={on_bus_exec=function(fn,address) assert(not callbacks[address]);callbacks[address]=fn end}
 env.joypad={set=function(value)
  keys=value
  for _,button in ipairs(buttons) do assert(type(value[button])=="boolean","incomplete controller state") end
 end}
 env.emu={getsystemid=function() return "GBA" end,framecount=function() return frame end,getregisters=function() return registers end,
  frameadvance=function()
   local function down(button) return keys[button] and not previous[button] end
   if down("Start") then
    if mode==0 then mode=3
    elseif mode==3 and title_callback==0x08090C7C then title_callback=0x08090FA0;prompt_start_count=prompt_start_count+1 end
   end
   if down("Down") then
    if mode==3 and title_callback==0x08090FA0 then title_row=(title_row+1)%4 end
    if mode==14 then options_row=(options_row+1)%6 end
   end
   if down("Up") and mode==3 then title_row=(title_row+3)%4 end
   if mode==14 then
    if down("Right") then pending=math.min(3,pending+1) end
    if down("Left") then pending=math.max(0,pending-1) end
   end
   if down("A") then
    if mode==3 then
     if title_callback==0x08090C7C then ignored_prompt_a=ignored_prompt_a+1 -- native TST20 ignores A40
     elseif title_row==2 then mode=14
     elseif title_row==0 then mode=4 end
    elseif mode==14 and options_row==4 then
     callbacks[0x0801FC5C]()
     if kind=="io-error" then err=1
     else tag=0xA0+pending;mode=3;title_callback=0x08090C7C;title_row=0 end
    elseif mode==4 then mode=5
    elseif mode==5 then mode=7;battle_frame=frame end
   end
   if mode==7 and kind~="bounded" and frame-battle_frame>=60 then
    mode=8;result_frame=frame;callbacks[0x080899F0]()
   end
   if mode==8 and frame-result_frame>=5 then
    callbacks[language==3 and 0x0808B19C or 0x0808B0AC]()
   end
   previous={};for k,v in pairs(keys) do previous[k]=v end
   frame=frame+1
  end}
 env.client={speedmode=function() end,
  screenshot=function(path) ops[#ops+1]="screen:"..path end,
  exit=function()
   exited=true
   for _,button in ipairs(buttons) do assert(keys[button]==false,"buttons held at exit") end
   assert(ops[#ops]=="close:W:/build/mock-result/result-done.txt","marker not final flushed operation")
  end}
 assert(load(probe_source,"result-observer","t",env))()
 local trace=assert(files["W:/build/mock-result/trace.txt"])
 local done=assert(files["W:/build/mock-result/result-done.txt"])
 assert(exited)
 if kind=="io-error" then assert(done=="failure:native-commit-error")
 elseif kind=="bounded" then assert(done=="bounded-no-result")
 else
  assert(done=="result-label-observed",done)
  assert(prompt_start_count>=2 and ignored_prompt_a==0,"native prompt requires Start, menu requires A")
  assert(trace:find("committed=true title=true battle=true result=true label=true",1,true))
  assert(trace:find("plus120=true plus300=true",1,true))
  assert(trace:find("last_chance="..tostring(language==3),1,true))
  for _,name in ipairs({"options-staged","options-committed","title-committed","battle-enter","result-enter","result-first-label","result-plus120","result-plus300"}) do
   assert(files["W:/build/mock-result/"..name.."-iwram.bin"]=="mock",name)
  end
 end
end
for language=0,3 do check(language,"success") end
check(2,"io-error")
check(2,"bounded")
'''


def main():
    lua = ctypes.CDLL(str(ROOT / "local/BizHawk-2.11.1/dll/lua54.dll"))
    ptr, integer = ctypes.c_void_p, ctypes.c_int
    for name, result, args in [
        ("luaL_newstate", ptr, []), ("luaL_openlibs", None, [ptr]),
        ("luaL_loadbufferx", integer, [ptr, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]),
        ("lua_pcallk", integer, [ptr, integer, integer, integer, ctypes.c_ssize_t, ptr]),
        ("lua_tolstring", ctypes.c_char_p, [ptr, integer, ptr]), ("lua_close", None, [ptr]),
    ]:
        fn = getattr(lua, name)
        fn.restype, fn.argtypes = result, args
    state = lua.luaL_newstate()
    assert state
    try:
        lua.luaL_openlibs(state)
        script = ("local probe_source=[=[\n" + SOURCE + "]=]\n" + CHECK).encode("utf-8")
        status = lua.luaL_loadbufferx(state, script, len(script), b"result-language-self-check", b"t")
        if status == 0:
            status = lua.lua_pcallk(state, 0, 0, 0, 0, None)
        if status != 0:
            raise AssertionError(lua.lua_tolstring(state, -1, None).decode("utf-8"))
    finally:
        lua.lua_close(state)
    print("PASS: four language routes, native-I/O error, bounded no-result, captures, explicit release and post-flush marker; mocked APIs only")


if __name__ == "__main__":
    main()
