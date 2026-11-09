#!/usr/bin/env python3
"""Exact source/core contracts and actual DI observer Lua under read-only mocks."""
import argparse
import ctypes
import json
from pathlib import Path
import re
from analyze_shoot_lifetime_consumers import exact, need, sha, SOURCE_SHA

ROOT = Path(__file__).resolve().parents[1]
CORE = {
    'BizSwan.cs': '0889F0173BBD93082439ABC2BDD9651D5851C83CE0694585A0CF43DC84807EAA',
    'WonderSwan.cs': '73E5D28F50F2180FE56966349E2E72758DABFD75846EB4DCDCE8303DCEAC2C29',
    'memory.cpp': 'F4BA9ACFD24372C08F67A554E5836FD3F8640A08F00E49F2BDEBE5B00FD5C7D4',
    'v30mz.h': '05CCBE35E54D7CE3806892AF10B474C801283009282623832BF35A8720C0AED4',
    'v30mz.cpp': 'C6DF2310688FAA755313A9BA04287DD96E4ECE99594493F6B8A96A100CB24DE4',
    'v30mz-private.h': '9C4F0C037202FC6BAA0C60C5196442F1E2A0A717554828744739B9FBF17A2DAD',
    'v30mz-modrm.inc': 'BB92604F1E65F97D4F65BDB9AEA5274B5854992AC4CB7DD18EC0900E8E6BC690',
}

CHECK = r'''
local function check(kind)
 local callbacks,files={},{}
 local stage,frame=11,20
 local regs={PS=0,PC=0,DS0=0xC00,DS1=0x300,IX=0xBAD,IY=0,AW=0xEEEE,BW=0xEA,SP=0xF000}
 local count=0
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)return ({output='W:/build/mock-di-v3',callback_order=kind=='backend' and 'bad' or 'bizhawk2111-rew',
  source_sha256=kind=='hash' and 'bad' or 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'})[k]end}
 local function byte(a,d)
  if d=='ROM' then local v=assert(rom[a]);if kind=='opcode' and a==0x75FC98 then return 0 end;return v end
  assert(d=='RAM' or d=='SRAM','nonexistent domain')
  if d=='SRAM' and a==0x5C then return stage end
  return (a*7+(d=='RAM' and 3 or 83))%256
 end
 env.memory={read_u8=byte,read_u16_le=function(a,d)return byte(a,d)+256*byte(a+1,d)end,
  getmemorydomainsize=function(d)return ({ROM=0x800000,RAM=kind=='domain' and 0x8000 or 0x10000,SRAM=0x8000})[d]end,
  read_bytes_as_binary_string=function(a,n,d)assert(a==0 and n==({RAM=0x10000,SRAM=0x8000})[d]);return d end}
 env.io={open=function(p,m)
  assert(p:match('^W:/build/mock%-di%-v3/'))
  if m=='rb' then if kind=='existing' then return {close=function()end} else return nil end end
  if m=='wb' then assert(not files[p],'snapshot overwritten');files[p]='' end
  return {write=function(_,s)files[p]=(files[p]or'')..s end,close=function()end}
 end}
 env.emu={getsystemid=function()return 'WSWAN'end,framecount=function()return frame end,getregisters=function()return regs end}
 env.event={availableScopes=function()return {'System Bus'}end,on_bus_write=function(fn,a,n,scope)
  assert(scope=='System Bus' and not callbacks[n]);callbacks[n]={fn=fn,address=a};count=count+1
 end}
 local observer=assert(load(observer_source,'@actual-observer','t',env))()
 assert(count==4,'fixed callback count')
 local function fire(label,badpc,badaddress)
  local cb=assert(callbacks['shoot-di-v3-'..label]);regs.PS=math.floor(cb.address/16);regs.PC=cb.address%16+1+(badpc and 1 or 0)
  cb.fn(cb.address+(badaddress and 1 or 0))
 end
 if kind=='bad-pc' then fire('calibration',true);return end
 if kind=='bad-address' then fire('calibration',false,true);return end
 if kind~='uncalibrated' then fire('calibration');fire('calibration');fire('calibration') end
 if kind=='empty' then
  local st=observer.finish();assert(st.paired_reads==0 and not st.actual_final_irq_observed and not st.terminal_observed);return
 end
 fire('terminal');fire('terminal')
 if kind=='orphan-post' then fire('post');return end
 local function physical_byte(a)
  if a<0x10000 then return byte(a,'RAM') end
  return byte(a-0x10000,'SRAM') -- fixtures stay below18000; independent explicit backing
 end
 local function pair(di,lo,hi)
  regs.IY=di;regs.DS1=kind=='wrong-es' and 0xC00 or 0x300
  fire('pre')
  if kind=='repeated-pre' then fire('pre') end
  if kind=='pending-finish' then observer.finish() end
  regs.AW=physical_byte(lo)+256*physical_byte(hi)
  if kind=='wrong-word' then regs.AW=(regs.AW+256)%65536 end
  if kind=='changed-di' then regs.IY=(regs.IY+1)%65536 end
  fire('post');frame=frame+1
 end
 for _,v in ipairs({{0,0x300A,0x300B},{0xCFF5,0xFFFF,0x10000},{0xCFF6,0x10000,0x10001},
  {0xD000,0x1000A,0x1000B},{0xFFF5,0x12FFF,0x13000},{0xFFF6,0x3000,0x3001},{0xFFFF,0x3009,0x300A}})do
  pair(table.unpack(v));if kind~='success' then return end
 end
 for i=1,505 do pair(i,0x300A+i,0x300B+i)end
 local st=observer.status();assert(st.paired_reads==512 and st.distinct_snapshots==16 and st.calibrated==2)
 for i=1,10 do pair(i,0x300A+i,0x300B+i)end
 assert(observer.status().paired_reads==512 and count==4)
 local snapshots=0;for p in pairs(files)do if p:match('%.bin$')then snapshots=snapshots+1 end end
 assert(snapshots==34,'first terminal plus16distinct, two domains each')
 stage=7;fire('pre');fire('post');assert(observer.status().paired_reads==512)
 st=observer.finish();assert(st.finished and st.actual_final_irq_observed and st.terminal_observed)
 local before=files['W:/build/mock-di-v3/di-observer-v3.txt'];fire('pre');fire('post')
 assert(before==files['W:/build/mock-di-v3/di-observer-v3.txt'])
 assert(before:find('low=1000A:SRAM:000A:',1,true))
 assert(before:find('high=13000:SRAM:3000:',1,true))
 assert(before:find('peek_matches_consumed=true',1,true))
end
check('success');check('empty')
for _,kind in ipairs({'backend','hash','opcode','domain','existing','bad-pc','bad-address','uncalibrated',
 'orphan-post','wrong-es','repeated-pre','pending-finish','wrong-word','changed-di'})do
 assert(not pcall(check,kind),'negative control accepted: '..kind)
end
'''


def run_lua(text, source):
    lua = ctypes.CDLL(str(ROOT/'local/BizHawk-2.11.1/dll/lua54.dll'))
    ptr, num = ctypes.c_void_p, ctypes.c_int
    for name, result, args in [('luaL_newstate',ptr,[]),('luaL_openlibs',None,[ptr]),
        ('luaL_loadbufferx',num,[ptr,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]),
        ('lua_pcallk',num,[ptr,num,num,num,ctypes.c_ssize_t,ptr]),
        ('lua_tolstring',ctypes.c_char_p,[ptr,num,ptr]),('lua_close',None,[ptr])]:
        f=getattr(lua,name);f.restype=result;f.argtypes=args
    spans=[(0x75FC8C,23),(0x773650,10),(0x750EBD,7)]
    rom=','.join(f'[{a+i}]={source[a+i]}' for a,n in spans for i in range(n))
    code=('local rom={'+rom+'}\nlocal observer_source=[==[\n'+text+']==]\n'+CHECK).encode()
    state=lua.luaL_newstate();need(bool(state),'Lua state')
    try:
        lua.luaL_openlibs(state)
        status=lua.luaL_loadbufferx(state,code,len(code),b'di-v3-mock',b't')
        if status==0:status=lua.lua_pcallk(state,0,0,0,0,None)
        if status:raise ValueError(lua.lua_tolstring(state,-1,None).decode())
    finally:lua.lua_close(state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--core-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh report required')
    s=a.source.read_bytes();need(sha(s)==SOURCE_SHA,'exact original source')
    exact(s,0x75FC90,['mov bx, 0x300','mov es, bx','mov bx, 0xea',
        'mov ax, word ptr es:[di + 0xa]','out 0x10, al','popf','pop es','pop bx','pop ax','retf'])
    for name,digest in CORE.items():need(sha((a.core_source/name).read_bytes())==digest,'official2.11.1 '+name)
    observer=ROOT/'tools/bizhawk_observe_wsc_shoot_di_v3.lua';text=observer.read_text(encoding='utf8')
    need(not re.search(r'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.(?:setregister|frameadvance)|\bjoypad\.',text),
        'observer-only API boundary')
    run_lua(text,s)
    negative=[]
    for label,old,new in [
        ('64KiB alias','local low=(es*16+offset)%0x100000','local low=(es*16+offset)%0x10000'),
        ('high offset rewrap','(low+1)%0x100000','(es*16+(offset+1)%0x10000)%0x100000'),
        ('SI instead of DI','operand(r.DS1,r.IY)','operand(r.DS1,r.IX)'),
        ('SRAM as RAM','return memory.read_u8(backing,"SRAM")','return memory.read_u8(backing,"RAM")'),
        ('unchecked consumed word','assert(match,"pre-read','assert(true,"pre-read'),
        ('unbounded pairs','pairs_done>=MAX_PAIRS','pairs_done>MAX_PAIRS'),
        ('extra snapshot','distinct<MAX_DISTINCT','distinct<=MAX_DISTINCT'),
        ('no PC calibration','and (r.PS*16+r.PC)%0x100000==(address+1)%0x100000',''),
    ]:
        need(old in text,'mutation target '+label)
        try:run_lua(text.replace(old,new),s)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective mutation '+label)
    report=dict(status='PASS',source_sha256=SOURCE_SHA,observer_sha256=sha(observer.read_bytes()),
        core_source_sha256=CORE,mocked_paired_reads=512,boundary_selfchecks=7,
        rejected_invalid_scenarios=14,rejected_mutations=negative,fixed_callbacks=4,
        max_snapshot_files=34,emulator_launched=False,actual_Shoot_observed=False,
        mapping='DS1=ES,IY=DI; uint16 EO then20bit physical; high byte physical+1; RAM/SRAM backing peeks; actualAWpost')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS actualLua512pairs/7boundaries/14invalidscenarios/8mutations; no emulator')


if __name__=='__main__':main()
