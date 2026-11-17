"""Independently check final nested open-bus composition without a game core."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import verify_wsc_shoot_short_hard as host

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('bizhawk_probe_id14_openbus.lua', 'bizhawk_observe_collision_openbus.lua',
         'bizhawk_probe_evolution_id14_r2.lua', 'bizhawk_probe_evolution_id14.lua',
         'bizhawk_probe_evolution_music_three.lua', 'bizhawk_probe_result_music_lifetime.lua',
         'bizhawk_probe_result_languages.lua', 'bizhawk_observe_evolution_event_queue.lua',
         'bizhawk_observe_collision_alignment.lua')
CHECK = r'''
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true))
 return s:sub(1,a-1)..new..s:sub(b+1)
end
local function compose(entry)
 local captured,context
 local observer={outcome=function()return 'fixture'end,finish=function()end}
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)if k=='target_song'then return 108 end return 'W:/build/openbus-fixture'end}
 env.memory={getmemorydomainsize=function()return 0x1000000 end}
 env.io={open=function(path,mode)
  assert(mode=='rb' and sources[path],path)
  return {read=function()return sources[path]end,close=function()end}
 end}
 env.load=function(source,name,mode,child)
  local compiled=assert(load(source,name,mode,child))
  if name=='@ID14-event-witness'or name=='@ID14-collision-witness'then return function()return{finish=function()end}end end
  if name=='@openbus-observer'then return function()return observer end end
  if name=='@reviewed-evolution-music-pause'then
   assert(not captured);captured,context=source,child;return function()end
  end
  return compiled
 end
 assert(load(sources['W:/tools/'..entry],'@independent-entry','t',env))()
 assert(captured)
 if entry=='bizhawk_probe_id14_openbus.lua'then assert(context.openbus_evidence==observer)end
 return captured
end
local original=compose('bizhawk_probe_evolution_id14_r2.lua')
local modified=compose('bizhawk_probe_id14_openbus.lua')
local oldout=' local pause_outcome=music_pause_outcome()'
local newout=' local pause_outcome=openbus_evidence.outcome() or music_pause_outcome()'
local oldguard='if outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then'
local newguard='if outcome~="collision-openbus-producer-observed" and outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then'
local oldfinish='music_lifetime_finish()\nid14_evidence_finish()\nlocal f='
local newfinish='music_lifetime_finish()\nid14_evidence_finish()\nopenbus_evidence.finish()\nlocal f='
local inverse=replace(replace(replace(modified,newout,oldout),newguard,oldguard),newfinish,oldfinish)
assert(inverse==original,'exact three-site effective inverse')
local a=assert(modified:find(newout,1,true))
local b=assert(modified:find(' local active={};',a,true))
local step=modified:sub(a,b-1)
local c,d=assert(modified:find(newguard,1,true))
local e=assert(modified:find('\nlog(string.format("summary outcome=',d+1,true))
local guard=modified:sub(c,e-1)
local finishstart=assert(modified:find(newfinish,1,true))
local finish=modified:sub(finishstart)
for _,case in ipairs({'observed','music-success','music-failure','bounded'})do
 local env=setmetatable({case=case,seen=false,advances=0,shots={},order={}},{__index=_G})
 env.capture=function(name)table.insert(env.shots,name)end
 env.joypad={set=function()end}
 env.openbus_evidence={outcome=function()return env.seen and 'collision-openbus-producer-observed'or nil end,
  finish=function()table.insert(env.order,'observer')end}
 env.music_lifetime_finish=function()table.insert(env.order,'music')end
 env.id14_evidence_finish=function()table.insert(env.order,'id14')end
 env.io={open=function(path,mode)
  assert(path=='fixture/result-done.txt'and mode=='w')
  assert(table.concat(env.order,',')=='music,id14,observer','all observers closed before completion marker')
  return{write=function(_,value)env.marker=value end,close=function()table.insert(env.order,'marker')end}
 end}
 env.client={exit=function()table.insert(env.order,'exit')end}
 local fixture=[=[
 local outcome,stage,mode,press=nil,'battle',7,nil
 local buttons={'A','Start'}
 local out='fixture'
 local function music_pause_input()end
 local function music_pause_outcome()
  if advances==0 then return nil end
  if case=='music-success'then return 'evolution-pause-resume-stage-return'end
  if case=='music-failure'then return 'failure:fixture'end
 end
 for frame=0,2 do
 ]=]..step..[=[
 advances=advances+1
 -- A producer hook runs during frameadvance; result is consumed only next boundary.
 if case=='observed'then seen=true end
 end
 ]=]..guard..'\n'..finish
 assert(load(fixture,'@actual-boundary-tail','t',env))()
 local expected=case=='observed'and 'collision-openbus-producer-observed'or case=='music-success'and 'evolution-pause-resume-stage-return'or case=='music-failure'and 'failure:fixture'or 'failure:pause-target-not-completed'
 assert(env.marker==expected)
 assert(env.advances==(case=='bounded'and 3 or 1),'first result stops at following boundary')
 assert(table.concat(env.order,',')=='music,id14,observer,marker,exit')
 assert(env.shots[1]==(case=='bounded'and 'bounded-end'or 'pause-end'))
end
'''


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def quote(data):
    return '"'+''.join(f'\\{b:03d}' for b in data)+'"'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    scripts = {n: (ROOT/'tools'/n).read_bytes() for n in NAMES}
    assert sha(scripts[NAMES[1]]) == '2E92FCF81D391E558AC72E1D0D65A23661382DAFFB48B61AEFD13D1A77C43C88'
    table = ','.join(f'[{quote(("W:/tools/"+n).encode())}]={quote(s)}' for n, s in scripts.items())
    check = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK='local sources={'+table+'}\n'+CHECK),
                               argdefs=host.lua_check.__defaults__)
    check('', '', '')
    result = dict(status='ID14_OPENBUS_COMPOSITION_PASS', dependency_sha256={n: sha(s) for n, s in scripts.items()},
                  exact_effective_inverse=True, boundary_cases=4, marker_after_observer_finish=True,
                  game_core_executed=False, scope='Final nested Lua source and completion-boundary control; observer hook logic checked separately.')
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
