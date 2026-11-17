"""Check the composed ID14 render-tail observer in Lua 5.4 without a game core."""

import argparse
import hashlib
import json
import re
import struct
import types
from pathlib import Path

import verify_wsc_shoot_short_hard as lua_host

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 'bizhawk_probe_id14_render_tail.lua'
OBSERVER = 'bizhawk_observe_render_tail.lua'
BASE = 'bizhawk_probe_evolution_id14_r2.lua'
PINS = {
    ENTRY: '4E21AD268FB047824C506C66146DBD81D8CB4A1465B0B1510FBD3F1F40052999',
    OBSERVER: 'C8F15736FEAEBEA90DA8414E297C624B8724B715EAAF8BF95CA5AA6267AFDBD6',
    BASE: 'A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA',
    'bizhawk_probe_evolution_id14.lua': 'DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B',
    'bizhawk_probe_evolution_music_three.lua': 'B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881',
    'bizhawk_probe_result_music_lifetime.lua': 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
    'bizhawk_probe_result_languages.lua': '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
    'bizhawk_observe_evolution_event_queue.lua': 'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
    'bizhawk_observe_collision_alignment.lua': 'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C',
}
HOOKS = {0x08352998: 0xE7895101, 0x083734F0: 0xE92D4000, 0x0837354C: 0xE92D4000,
         0x083735BC: 0xE92D4000, 0x08012C30: 0xE5954044, 0x03000200: 0xE92D403F,
         0x03000358: 0xE5C20000}

CHECK = r'''
local function between(source,first,last)
 local a,b=assert(source:find(first,1,true))
 local c=assert(source:find(last,b+1,true))
 assert(not source:find(first,b+1,true),first)
 return source:sub(a,c-1)
end
local function replace(source,old,new)
 local a,b=assert(source:find(old,1,true))
 assert(not source:find(old,b+1,true),old)
 return source:sub(1,a-1)..new..source:sub(b+1)
end
local function compose(entry)
 local captured,context,observer
 local hooks,lines,closed,now,corrupt={},{},false,100,nil
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)if k=='target_song' then return 108 end return 'W:/build/tail-fixture' end}
 env.memory={getmemorydomainsize=function()return 0x1000000 end,
  read_u8=function()return 0 end,read_u16_le=function()return 0 end,
  read_u32_le=function(offset,domain)
   local at=offset+(domain=='ROM' and 0x08000000 or 0x03000000)
   return at==corrupt and 0 or opcodes[at]or 0
  end}
 env.io={open=function(path,mode)
  if mode=='rb' then assert(sources[path],path);return{read=function()return sources[path]end,close=function()end}end
  assert(mode=='wb' and path=='W:/build/tail-fixture/render-tail.txt',path)
  return{write=function(_,line)assert(not closed);lines[#lines+1]=line;return true end,
   flush=function()assert(not closed)end,close=function()assert(not closed);closed=true end}
 end}
 env.event={on_bus_exec=function(fn,at,label)
  assert(opcodes[at] and not hooks[at] and label:match('^render%-tail%-'));hooks[at]=fn
 end}
 env.emu={framecount=function()return now end,getregisters=function()
  return {R15=0,R14=0,R0=0,R1=0,R2=0,R4=0,R5=0}
 end}
 env.load=function(source,name,mode,child)
  local compiled=assert(load(source,name,mode,child))
  if name=='@ID14-event-witness' or name=='@ID14-collision-witness' then return function()return{finish=function()end}end end
  if name=='@render-tail-observer' then return function()observer=compiled();return observer end end
  if name=='@reviewed-evolution-music-pause' then
   assert(not captured);captured,context=source,child;return function()end
  end
  return compiled
 end
 assert(load(sources['W:/tools/'..entry],'@independent-entry','t',env))()
 assert(captured)
 if observer then
  assert(context.render_tail==observer,'observer reaches final child environment')
  local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==7)
  corrupt=0x03000200
  hooks[corrupt]();assert(#lines==1,'inactive observer skipped live check')
  local ok=pcall(observer.frame,1);assert(not ok)
  observer.frame(0);assert(lines[2]:find('snapshot=armed core=100',1,true) and lines[3]:find('snapshot=age-0 core=100',1,true))
  local bad,msg=pcall(hooks[corrupt]);assert(not bad and msg:find('live opcode render',1,true))
  corrupt=nil
  for _=1,9 do hooks[0x03000200]()end
  assert(#lines==11,'per-label per-core limit is eight')
  now=101;hooks[0x03000200]();observer.frame(1)
  assert(#lines==13 and lines[12]:find('core=101',1,true))
  assert(not pcall(observer.frame,121))
  observer.finish();local n=#lines
  assert(table.concat(lines):find('event=render observed=10 suppressed=1',1,true))
  observer.finish();hooks[0x03000200]();assert(closed and #lines==n)
 end
 return captured
end
local original=compose(base_entry)
local composed=compose(tail_entry)
local first=' local pause_outcome=music_pause_outcome()\n'
local old=between(original,first,' if outcome then break end')
local new=between(composed,first,' if outcome then break end')
local declarations=between(composed,'local render_tail_start\n','\nlocal ')
-- Remove the three intended extensions and require equality of the whole Lua body.
local inverse=replace(composed,'\n'..declarations,'')
inverse=replace(inverse,new,old)
inverse=replace(inverse,'\nrender_tail.finish()\nlocal f=','\nlocal f=')
assert(inverse==original,'unexpected effective-code changes')
local input=between(composed,'local function music_pause_input(', 'local function music_pause_outcome()')
local loop=between(composed,first,' local active={};')
local function trial(failure)
 local env=setmetatable({shots={},ages={},keys={},at=100,failure=failure},{__index=_G})
 env.capture=function(name)table.insert(env.shots,name..'@'..env.at)end
 env.render_tail={frame=function(age)table.insert(env.ages,age)end}
 env.emu={framecount=function()return env.at end}
 env.joypad={set=function(keys)
  for _,value in pairs(keys)do assert(not value,'held button through observation')end
  table.insert(env.keys,env.at)
 end}
 local fixture=[=[
local outcome,stage,mode,press='','battle',7,'Right'
outcome=nil
local buttons={'Up','Down','Left','Right','A','B','L','R','Start','Select','Power'}
local pause={phase='running',first=0}
local function music_pause_outcome()
 if failure and at==100+failure then return 'failure:fixture' end
 return 'evolution-pause-resume-stage-return'
end
]=]
 local run=assert(load(fixture..declarations..'\n'..input..'\nfor frame=100,250 do at=frame\n'..loop..
  '\nend\nreturn outcome','@actual-tail-loop','t',env))
 assert(run()==(failure and 'failure:fixture' or 'evolution-pause-resume-stage-return'))
 local frames=failure or 120
 assert(#env.keys==frames and #env.ages==frames+(failure and 0 or 1))
 for k,frame in ipairs(env.keys)do assert(frame==99+k)end
 for k,age in ipairs(env.ages)do assert(age==k-1)end
 local expected={}
 for _,age in ipairs({0,1,2,4,8,16,32,64,120})do
  if not failure or age<failure then expected[#expected+1]='render-tail-'..age..'@'..(100+age)end
 end
 expected[#expected+1]='pause-end@'..(100+frames)
 assert(table.concat(env.shots,',')==table.concat(expected,','),'snapshot schedule')
end
trial(nil)
trial(8)
trial(0)
'''


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def quote(data):
    return '"' + ''.join(f'\\{byte:03d}' for byte in data) + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    scripts = {name: (ROOT / 'tools' / name).read_bytes() for name in PINS}
    assert {name: sha(data) for name, data in scripts.items()} == PINS
    assert all(not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister', scripts[name])
               for name in (ENTRY, OBSERVER))
    capture = ROOT / 'build/bizhawk-id14-evolution-20261116-c'
    rom = (capture / 'loaded-rom.bin').read_bytes()
    iram = (capture / 'pause-end-iwram.bin').read_bytes()
    assert sha(rom) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    for address, opcode in HOOKS.items():
        memory, base = (rom, 0x08000000) if address >= 0x08000000 else (iram, 0x03000000)
        assert struct.unpack_from('<I', memory, address - base)[0] == opcode
    source_table = ','.join(f'[{quote(("W:/tools/" + name).encode())}]={quote(data)}'
                            for name, data in scripts.items())
    opcode_table = ','.join(f'[{address}]={opcode}' for address, opcode in HOOKS.items())
    prefix = (f'local sources={{{source_table}}}\nlocal opcodes={{{opcode_table}}}\n'
              f'local base_entry="{BASE}"\nlocal tail_entry="{ENTRY}"\n')
    run = types.FunctionType(lua_host.lua_check.__code__, dict(lua_host.__dict__, CHECK=prefix + CHECK))
    run('', '', '')
    result = dict(status='ID14_RENDER_TAIL_LUA_QA_PASS', dependency_sha256=PINS,
                  checker_sha256=sha(Path(__file__).read_bytes()), bound_hook_opcodes=len(HOOKS),
                  effective_lua_inverse=True, neutral_advances=120, snapshot_ages=[0, 1, 2, 4, 8, 16, 32, 64, 120],
                  failure_ages=[0, 8], live_opcode_mismatch_rejected=True, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
