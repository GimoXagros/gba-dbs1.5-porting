#!/usr/bin/env python3
"""Source Options contracts and actual Lua wrapper under mocked read-only APIs."""
import argparse
import ctypes
import json
from pathlib import Path
import re
import struct
from analyze_shoot_lifetime_consumers import exact, need, sha, SOURCE_SHA
ROOT=Path(__file__).resolve().parents[1]
HARD='0CC9B17CAE00E7B7EFA33976788B1A66F595F15473EE78A597A77ADF68F42D69'
COLLECT='2AD5BB33BB5FA85A654E5A36ECDF002195076CC85FB62C4E7A7033797BA37A17'


def contracts(s):
    exact(s,0x77609F,['push 0x1200','push 0x7564','push 0x12c3',
        'lcall 0x4fff, 0x980','add sp, 6','add ax, 0x10',
        'mov ds, dx','mov si, ax','mov word ptr [si], 0'])
    exact(s,0x776994,['mov bx, word ptr es:[di + 0x10]',
        'test cx, 8','jne 0x7769a7','test cx, 2','jne 0x7769af',
        'jmp 0x776a0b','or bx, bx','je 0x7769c8','dec bx',
        'jmp 0x7769b5','cmp bx, 2','je 0x7769c8','inc bx'])
    exact(s,0x7769C8,['mov word ptr es:[di + 0x10], bx'])
    exact(s,0x740C62,['mov bx, word ptr [0x5e]','shl bx, 1',
        'jmp word ptr cs:[bx + 0x36d]'])
    need(struct.unpack_from('<3H',s,0x740C6D)==(0x373,0x379,0x37F),'three actual timer choices')
    for a,v in [(0x740C73,6750),(0x740C79,9000),(0x740C7F,13500)]:
        exact(s,a,[f'mov ax, 0x{v:x}'])
    exact(s,0x740CA1,['mov word ptr [0x3ce], 0x4650',
        'mov word ptr [0x3d2], 0x4628','add ax, 2'])
    exact(s,0x7417E6,['mov bx, word ptr es:[0x65e]',
        'cmp word ptr [bx + 0x50], 0','jg 0x7417fe','push 5',
        'lcall 0x71f0, 0'])
    exact(s,0x7417FE,['cmp word ptr es:[0x3ce], 0','jns 0x74181a',
        'mov word ptr es:[0x3ce], 0','push 0','lcall 0x71f0, 0'])
    return dict(timer_row=0,selector='SRAM005E',choices_updates=[6750,9000,13500],
        difficulty_row=1,difficulty='SRAM005D=3',boss_updates=18000,
        boss_clear='upperHP<=0 invokes root5; timer expiration invokes root0',
        direct_timer_mutation=False)


CHECK=r'''
local function check(initial_timer,initial_difficulty,kind)
 local bounded=kind~='success'
 local frame,mode,stage,row,title_row=0,3,0,0,0
 local timer,difficulty=initial_timer,initial_difficulty
 local battle_start,boss_start,shoot_start=nil,nil,nil
 local hp,keys,previous=2000,{},{}
 local files,callbacks={},{}
 local regs={PS=0,PC=0,DS0=0xC00,DS1=0x1000,BW=0,IX=0x24,IY=0,AW=0,CW=0,SP=0xF000}
 local exited,boss_attacks,collected=false,0,0
 local env=setmetatable({},{__index=_G})
 local function u16(a,domain)
  if domain=='SRAM' then
   if a==0x4E then return mode elseif a==0x5E then return timer
   elseif a==0x65C then return 0x24 elseif a==0x65E then return 0x134
   elseif a==0x60C then return 0x234 elseif a==0x3CE then return stage==7 and 18000 or ({6750,9000,13500})[timer+1]
   else return 0 end
  end
  if a==0x3118 then return row end
  if a==0xC014 then return 0x067B elseif a==0xC016 then return 0x7FFB end
  if a==0xC248 then return 7 end
  for _,at in ipairs({0xC024,0xC134,0xC244}) do
   if a==at+0x26 then return at==0xC024 and 0x800 or 0x880 end
   if a==at+0x28 then return 0xC00 end
   if a==at+0x50 then return at==0xC134 and hp or 8 end
   if a==at+0x52 then return at==0xC024 and 10 or 0 end
   if a==at+0x1E then return 0 end
   if a==at+0x20 then return 0 end
  end
  return 0
 end
 local function u8(a,domain)
  if domain=='SRAM' then
   if a==0x5C then return stage elseif a==0x5D then return difficulty
   elseif a>=0x640 and a<0x64F then return a==0x640 and 0 or 0xFF end
   return 0
  end
  if a==0xC028 then return 0 elseif a==0xC029 then return title_row
  elseif a==0xC254 then return 1 end
  return 0
 end
 env.userdata={get=function(k)return ({output='W:/build/mock-short-hard',frames=bounded and 6000 or 12000,callback_order='bizhawk2111-rew'})[k]end}
 env.memory={read_u16_le=u16,read_u8=u8,getmemorydomainsize=function(d)return d=='ROM' and 0x800000 or 0x8000 end,
  read_bytes_as_binary_string=function()return 'mock' end}
 env.mainmemory={read_u16_le=function(a)return u16(a,'RAM')end,read_u8=function(a)return u8(a,'RAM')end,
  read_bytes_as_binary_string=function()return 'mock' end}
 env.io={open=function(path,mode_)
  if path=='W:/tools/bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua' or path=='W:/tools/bizhawk_probe_wsc_shoot_collect_v2.lua' then
   assert(mode_=='rb');return {read=function()return path:find('collect',1,true) and collect_source or hard_source end,close=function()end}
  end
  assert(path:match('^W:/build/mock%-short%-hard/'),path)
  if mode_~='a' then files[path]='' end
  return {write=function(_,s)files[path]=(files[path]or'')..s end,close=function()end}
 end}
 env.event={availableScopes=function()return {'System Bus'}end}
 for _,op in ipairs({'on_bus_read','on_bus_write','on_bus_exec'}) do
  env.event[op]=function(fn,address,name,scope)assert(scope=='System Bus');callbacks[name]={fn=fn,address=address};return name end
 end
 local function fire(name)
  local cb=assert(callbacks[name],name);regs.PS=math.floor(cb.address/16);regs.PC=cb.address%16+1
  cb.fn(cb.address,0,0)
 end
 env.emu={getsystemid=function()return 'WSWAN'end,framecount=function()return frame end,getregisters=function()return regs end}
 env.joypad={set=function(k)
  keys=k
  if mode==7 and stage==7 and k['P1 B']then boss_attacks=boss_attacks+1 end
  if mode==7 and stage==0 and k['P1 X2'] and not k['P1 B']then collected=collected+1 end
 end}
 env.client={speedmode=function()end,screenshot=function(path)files[path]='mock'end,exit=function()exited=true end}
 env.emu.frameadvance=function()
  local function edge(k)return keys[k] and not previous[k]end
  if frame>=3960 then
   if mode==3 then
    if edge('P1 X3')then title_row=(title_row+1)%5 end
    if edge('P1 X1')then title_row=(title_row+4)%5 end
    if edge('P1 A')and title_row==2 then mode=14;row=0
    elseif edge('P1 A')and title_row==0 then mode=7;battle_start=frame end
   elseif mode==14 then
    if edge('P1 X3')then row=(row+1)%5 end
    if edge('P1 X1')then row=(row+4)%5 end
    if row==1 and edge('P1 X2')then difficulty=math.min(3,difficulty+1)end
    if row==0 and edge('P1 X4')then timer=math.max(0,timer-1)end
    if edge('P1 B')then assert(timer==0 and difficulty==3);mode=3;title_row=0 end
   elseif mode==7 then
    assert(timer==0 and difficulty==3)
    if kind~='ordinary-orb' and stage==0 and frame-battle_start>=90 then stage=7;boss_start=frame end
    if stage==7 then
     if keys['P1 B']then hp=hp-1 end
     if kind~='boss-bounded' and frame-boss_start>=650 then stage=11;shoot_start=frame end
    end
   end
  end
  previous={};for k,v in pairs(keys)do previous[k]=v end
  frame=frame+1
  fire('stage-calibration-read');fire('stage-calibration-write');fire('frame-wait-calibration')
  if stage==7 and frame-boss_start==10 then fire('row-clear-live-in');fire('final-IRQ-DI') end
  if stage==11 then
   if kind~='no-shoot-irq' then fire('final-IRQ-DI');fire('terminal-owner-7732376') end --75FC98
   if kind~='no-shoot-clear' and frame-shoot_start==40 then fire('row-clear-live-in');fire('terminal-owner-7813322') end --7738CA, once
  end
 end
 assert(load(wrapper_source,'@actual-wrapper','t',env))()
 assert(exited and files['W:/build/mock-short-hard/done.txt']=='observation-complete')
 assert(files['W:/build/mock-short-hard/options-short-hard-sram.bin']=='mock')
 assert(timer==0 and difficulty==3 and collected>0)
 if kind~='ordinary-orb' then assert(boss_attacks>0) end
 for _,v in pairs(keys)do assert(not v,'final input release')end
 local trace=files['W:/build/mock-short-hard/trace.txt']
 assert(trace:find('timer0-confirmed',1,true)and trace:find('p2hp=',1,true))
 assert(callbacks['terminal-owner-7813322'] and callbacks['lower-8EF3-spatial'])
 if bounded then assert(not trace:find('early-stop',1,true)and frame==6000)
 else assert(trace:find('early-stop',1,true)and frame<12000 and frame-shoot_start>=299)
  assert(trace:find('shoot_row_hits=1',1,true),'single actual Shoot clear suffices')
  assert(files['W:/build/mock-short-hard/terminal-owners.txt'])end
 return frame,boss_attacks
end
for t=0,2 do for d=0,3 do check(t,d,'success')end end
for _,kind in ipairs({'boss-bounded','ordinary-orb','no-shoot-clear','no-shoot-irq'})do check(1,1,kind)end
'''


def lua_check(wrapper,hard,collect):
    # Run Lua in-process against explicit mock APIs; never start BizHawk/core.
    dll=ROOT/'local/BizHawk-2.11.1/dll/lua54.dll';lua=ctypes.CDLL(str(dll))
    ptr,num=ctypes.c_void_p,ctypes.c_int
    for name,result,args in [('luaL_newstate',ptr,[]),('luaL_openlibs',None,[ptr]),
        ('luaL_loadbufferx',num,[ptr,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]),
        ('lua_pcallk',num,[ptr,num,num,num,ctypes.c_ssize_t,ptr]),
        ('lua_tolstring',ctypes.c_char_p,[ptr,num,ptr]),('lua_close',None,[ptr])]:
        f=getattr(lua,name);f.restype=result;f.argtypes=args
    code=('local wrapper_source=[==[\n'+wrapper+']==]\nlocal hard_source=[==[\n'+hard+
        ']==]\nlocal collect_source=[==[\n'+collect+']==]\n'+CHECK).encode()
    state=lua.luaL_newstate();need(bool(state),'Lua state')
    try:
        lua.luaL_openlibs(state)
        status=lua.luaL_loadbufferx(state,code,len(code),b'short-hard-mock',b't')
        if status==0:status=lua.lua_pcallk(state,0,0,0,0,None)
        if status:raise ValueError(lua.lua_tolstring(state,-1,None).decode())
    finally:lua.lua_close(state)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh report required');s=a.source.read_bytes()
    need(sha(s)==SOURCE_SHA,'exact original WSC');proof=contracts(s)
    paths=[ROOT/'tools'/n for n in ('bizhawk_probe_wsc_shoot_short_hard.lua',
        'bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua','bizhawk_probe_wsc_shoot_collect_v2.lua')]
    blobs=[p.read_bytes()for p in paths]
    need([sha(b)for b in blobs[1:]]==[HARD,COLLECT],'frozen observer and collector')
    texts=[b.decode('utf8')for b in blobs]
    need(not re.search(r'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister',texts[0]),'wrapper has no guest mutation API')
    lua_check(*texts)
    negative=[]
    for label,old,new in [('wrong timer direction','row==0 and "P1 X4"','row==0 and "P1 X2"'),
        ('boss collector override','stage~=7 and stage~=11','stage~=11'),
        ('premature completion','shoot_row_hits>0 and shoot_irq_hits>0 and shoot_frames>=300','terminal_hits>=0'),
        ('collector overrides release','short_hard_release(release)','joypad.set(release)'),
        ('repeated clear requirement','shoot_row_hits>0 and shoot_irq_hits>0','shoot_row_hits>=2 and shoot_irq_hits>0')]:
        need(old in texts[0],'negative target');bad=texts[0].replace(old,new)
        try:lua_check(bad,*texts[1:])
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective Lua negative '+label)
    report=dict(status='PASS',source=proof,mocked_routes=16,negative_controls_rejected=negative,
        dependency_sha256={p.name:sha(b)for p,b in zip(paths,blobs)},
        runtime_executed=False,actual_Shoot_entry_observed=False,
        mock_scope='Actual wrapper and both frozen dependencies under mocked APIs; normal orb collection, boss attacks, timer/difficulty, telemetry, early and bounded completion, input release, terminal hook retention.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS16 mocked ordinary-input routes; source timer/boss contracts;5mutations; no emulator execution')


if __name__=='__main__':main()
