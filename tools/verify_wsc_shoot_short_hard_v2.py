#!/usr/bin/env python3
"""Actual Lua v2 wrapper tests, reusing frozen E382 observer mock fixtures."""
import argparse
import json
from pathlib import Path
import types
import verify_wsc_shoot_short_hard as prior
from analyze_shoot_lifetime_consumers import SOURCE_SHA, need, sha
ROOT=Path(__file__).resolve().parents[1]
PRIOR='2479D74DFA73F84E85EBECE0F047171F7401E9448B254DAE1D223EEC7AF3DE83'
PARENT='E382D2D1462B7507090483548FD12DBC97A0342BA0C90D617268D6460A63ABD0'


def once(text,old,new):
    need(text.count(old)==1,'unique frozen mock anchor '+old[:50]);return text.replace(old,new)


def mock(parent):
    check=prior.CHECK
    check=once(check,'local function check(initial_timer,initial_difficulty,kind)',
        "local profile='baseline'\nlocal function check(initial_timer,initial_difficulty,kind)")
    check=once(check,'local files,callbacks={},{}','local files,callbacks={},{}\n local journal={}')
    check=once(check,"if a==at+0x26 then return at==0xC024 and 0x800 or 0x880 end",r'''
   if a==at+0x26 then
    if profile=='baseline' then return at==0xC024 and 0x800 or 0x880 end
    if at==0xC024 then
     if profile=='moving' then return 0x2E0+(frame%1000)*4 end
     if profile=='release-active' and frame<5800 then return 0x2E0+(frame%300)*4 end
     return profile=='right-wall' and 0x1A00 or 0x2E0
    end
    return profile=='right-wall' and 0x1C80 or 0x60
   end''')
    check=once(check,"if a==at+0x28 then return 0xC00 end",r'''
   if a==at+0x28 then
    if profile=='baseline' then return 0xC00 end
    if at==0xC024 then return 0x1100 end
    return profile=='small-gap' and 0x1000 or 0x400
   end''')
    check=once(check,'env.io={open=function(path,mode_)',r'''
 env.io={open=function(path,mode_)
  if path=='W:/tools/bizhawk_probe_wsc_shoot_short_hard.lua' then
   assert(mode_=='rb');return {read=function()return parent_source end,close=function()end}
  end''')
    check=once(check,'env.joypad={set=function(k)',r'''
 env.joypad={set=function(k)
  journal[frame]={};for name,value in pairs(k)do journal[frame][name]=value end''')
    check=once(check,"frame-boss_start>=650", "frame-boss_start>=(profile=='cooldown' and 2500 or 650)")
    check=once(check,"if kind~='ordinary-orb' then assert(boss_attacks>0) end",
        "if profile=='baseline' and kind~='ordinary-orb' then assert(boss_attacks>0) end")
    check=once(check,'assert(timer==0 and difficulty==3 and collected>0)',
        "assert(timer==0 and difficulty==3)\n if profile=='baseline' then assert(collected>0)end")
    check=once(check,'return frame,boss_attacks',r'''
 local recovery=files['W:/build/mock-short-hard/escape.txt']or''
 if profile=='baseline' or profile=='moving' or profile=='small-gap' then
  assert(recovery=='','ordinary motion/small gap must not trigger escape')
 else
  local starts={}
  for line in recovery:gmatch('[^\n]+')do
   local at,stage_,away=line:match('escape%-start frame=(%d+) stage=(%d+).-away=(%-?%d+)')
   if at then
    at,stage_,away=tonumber(at),tonumber(stage_),tonumber(away)
    assert(away==(profile=='right-wall' and -1 or 1),'back away from observed wall-facing direction')
    assert(stage_~=11 and at-(stage_==7 and boss_start or battle_start)>=179,'bounded stationary trigger')
    starts[#starts+1]=at
    for age=0,math.min(59,frame-at-1)do
     local k=assert(journal[at+age],'recovery input sample')
     assert(k['P1 X2']==(away==1)and k['P1 X4']==(away==-1),'finite back-away direction')
     assert(k['P1 A']==(age>=4 and age<12)and not k['P1 B'],'single8frame jump pulse without attacks')
    end
   end
  end
  assert(#starts>0,'recovery must trigger in actual stalled fixture')
  local screenshots,dumps=0,0
  for name in pairs(files)do
   if name:find('/escape-',1,true)then
    if name:sub(-4)=='.png'then screenshots=screenshots+1 end
    if name:sub(-8)=='-ram.bin'then dumps=dumps+1 end
   end
  end
  assert(screenshots==math.min(3,#starts)and dumps==screenshots,'bounded first3 PNG/RAM pairs')
  if profile=='cooldown' then
   assert(#starts>=4,'cooldown fixture exercises re-entry and3capture cap')
   for i=2,#starts do assert(starts[i]-starts[i-1]>=599,'inclusive60 recovery+360 cooldown+180 retrigger samples')end
  end
  if profile=='release-active' then
   assert(frame-starts[#starts]<60,'bounded run ends during recovery')
   for _,v in pairs(journal[frame])do assert(not v,'unconditional release during recovery')end
  end
 end
 return frame,boss_attacks''')
    check+=r'''
for _,p in ipairs({'left-wall','right-wall','moving','small-gap','cooldown'})do
 profile=p;check(1,1,'success')
end
profile='release-active';check(1,1,'ordinary-orb')
'''
    return 'local parent_source=[==[\n'+parent+']==]\n'+check


def run(wrapper,parent,hard,collect):
    fn=types.FunctionType(prior.lua_check.__code__,dict(prior.__dict__,CHECK=mock(parent)),
        argdefs=prior.lua_check.__defaults__)
    fn(wrapper,hard,collect)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh output');need(sha(Path(prior.__file__).read_bytes())==PRIOR,'frozen prior mock')
    source=a.source.read_bytes();need(sha(source)==SOURCE_SHA,'original source');source_proof=prior.contracts(source)
    names=['bizhawk_probe_wsc_shoot_short_hard_v2.lua','bizhawk_probe_wsc_shoot_short_hard.lua',
        'bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua','bizhawk_probe_wsc_shoot_collect_v2.lua']
    blobs=[(ROOT/'tools'/n).read_bytes()for n in names]
    need([sha(b)for b in blobs[1:]]==[PARENT,prior.HARD,prior.COLLECT],'frozen three-layer dependencies')
    wrapper,parent,hard,collect=[b.decode('utf8')for b in blobs]
    run(wrapper,parent,hard,collect);negative=[]
    for label,old,new in [('missing recovery application','set_keys(wall_escape(keys),...)','set_keys(keys,...)'),
        ('unbounded trigger','escape.stuck<180','escape.stuck<1'),
        ('wrong direction','escape.away=-direction','escape.away=direction'),
        ('double duration','escape.remaining=60;','escape.remaining=120;'),
        ('no cooldown','escape.cooldown=360','escape.cooldown=0')]:
        need(wrapper.count(old)==1,'negative target');bad=wrapper.replace(old,new)
        try:run(bad,parent,hard,collect)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective negative '+label)
    bad_parent=parent.replace('short_hard_release=release_keys','short_hard_release=joypad.set')
    need(bad_parent!=parent,'release mutation target')
    try:run(wrapper,bad_parent,hard,collect)
    except ValueError:negative.append('collector overrides release during escape')
    else:raise ValueError('release regression accepted')
    out=dict(status='PASS',source=source_proof,mocked_routes=22,negative_controls_rejected=negative,
        dependency_sha256={n:sha(b)for n,b in zip(names,blobs)},prior_mock_sha256=PRIOR,
        recovery=dict(stationary_frames=180,X_tolerance=32,opponent_above_gap_min_exclusive=768,
            horizontal_target_distance_min_exclusive=256,backaway_frames=60,jump_ages=[4,11],cooldown_frames=360),
        runtime_executed=False,actual_recovery_success_claimed=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
    print('PASS22 actualLua mockroutes;6negativecontrols; no emulator or game writes')


if __name__=='__main__':main()
