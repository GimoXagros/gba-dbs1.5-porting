#!/usr/bin/env python3
"""Independent actual-policy edge tests; host Lua only, no emulator/core."""
import argparse,json,re,types
from pathlib import Path
import verify_wsc_shoot_short_hard as harness
from analyze_shoot_lifetime_consumers import need,sha
ROOT=Path(__file__).resolve().parents[1]
CHECK=r"""
local function scenario()
 local p={mode=7,stage=0,player=0x24,target=0x134,x=0x2E0,y=0x1100,tx=0x60,ty=0x400,frame=0,notes={},images=0,dumps=0}
 local e={output='review',signed=function(v)return v>=32768 and v-65536 or v end}
 e.memory={read_u16_le=function(a,d)
  assert(d=='SRAM')
  if a==0x4E then return p.mode elseif a==0x65C then return p.player elseif a==0x65E then return p.target end
  error('unexpected guest read')
 end,read_u8=function(a,d)assert(a==0x5C and d=='SRAM');return p.stage end}
 e.mainmemory={read_u16_le=function(a)
  if a==0xC000+p.player+0x26 then return p.x%65536 elseif a==0xC000+p.player+0x28 then return p.y%65536
  elseif a==0xC000+p.target+0x26 then return p.tx%65536 elseif a==0xC000+p.target+0x28 then return p.ty%65536 end
  error('unexpected actor read')
 end,read_bytes_as_binary_string=function(a,n)assert(a==0 and n==65536);return string.rep('0',n)end}
 e.emu={framecount=function()return p.frame end}
 e.io={open=function(path,mode)
  if path=='review/escape.txt' then assert(mode=='a');return {write=function(_,s)p.notes[#p.notes+1]=s end,close=function()end}end
  assert(path:match('^review/escape%-%d%-stage%-%d+%-frame%-%d+%-ram%.bin$') and mode=='wb')
  return {write=function(_,s)assert(#s==65536);p.dumps=p.dumps+1 end,close=function()end}
 end}
 e.client={screenshot=function(path)assert(path:match('^review/escape%-%d%-stage%-%d+%-frame%-%d+%.png$'));p.images=p.images+1 end}
 setmetatable(e,{__index=_G})
 local apply=assert(load(wrapper_source..'\nreturn wall_escape','@actual-escape-policy','t',e))()
 function p.step(keys)
  keys=keys or {['P1 X4']=true,['P1 X2']=false,['P1 A']=false,['P1 B']=true}
  local result=apply(keys);p.frame=p.frame+1;return result
 end
 function p.run(n,keys)for _=1,n do p.step(keys and {['P1 X4']=keys[1],['P1 X2']=keys[2],['P1 B']=true})end end
 function p.starts()local out={}for _,s in ipairs(p.notes)do local f=s:match('escape%-start frame=(%d+)');if f then out[#out+1]=tonumber(f)end end;return out end
 return p
end
local scenarios=0
-- Exact continuous sequence proves inclusive boundaries and full cooldown.
do local p=scenario();p.run(179);assert(#p.starts()==0)
 for age=0,59 do local k=p.step();assert(k['P1 X2'] and not k['P1 X4'] and not k['P1 B']);assert(k['P1 A']==(age>=4 and age<12))end
 assert(p.starts()[1]==179)
 for _=1,360 do local k=p.step();assert(k['P1 X4'] and not k['P1 X2'] and k['P1 B'])end
 p.run(179);assert(#p.starts()==1);p.step();assert(p.starts()[2]==778);scenarios=scenarios+1 end
-- Every guard independently prevents recovery for a full eligible-sized run.
for _,mutate in ipairs({function(p)p.mode=3 end,function(p)p.stage=11 end,
 function(p)p.player=0x25 end,function(p)p.target=0x23 end,
 function(p)p.ty=p.y-0x300 end,function(p)p.tx=p.x-0x100 end,
 function(p)p.ty=p.y+0x500 end})do local p=scenario();mutate(p);p.run(400);assert(#p.starts()==0);scenarios=scenarios+1 end
for _,keys in ipairs({{false,false},{true,true},{false,true}})do local p=scenario();p.run(400,keys);assert(#p.starts()==0);scenarios=scenarios+1 end
-- Small sustained motion must reset the anchor before a stationary trigger.
do local p=scenario();for _=1,600 do p.x=p.x+1;p.step()end;assert(#p.starts()==0);scenarios=scenarios+1 end
-- Direction reversal resets 179 accumulated samples.
do local p=scenario();p.run(179);p.tx=p.x+0x300;p.run(179,{false,true});assert(#p.starts()==0);local k=p.step({['P1 X2']=true});assert(k['P1 X4'] and not k['P1 X2']);scenarios=scenarios+1 end
-- Stage/mode/handle/frame discontinuity cancels active recovery immediately.
for _,mutate in ipairs({function(p)p.mode=3 end,function(p)p.stage=11 end,
 function(p)p.player=0x244 end,function(p)p.target=0x354 end, function(p)p.target=0x25 end,function(p)p.frame=p.frame+1 end})do
 local p=scenario();p.run(180);assert(#p.starts()==1);mutate(p)
 local k=p.step();assert(k['P1 X4'] and not k['P1 X2'] and k['P1 B']);scenarios=scenarios+1
end
-- Returning from a foreign stage starts a fresh 180-sample window.
do local p=scenario();p.run(180);p.stage=11;p.step();p.stage=0;p.run(179);assert(#p.starts()==1);p.step();assert(#p.starts()==2);scenarios=scenarios+1 end
-- Signed negative actor coordinates retain the symmetric right-wall behavior.
do local p=scenario();p.x=-1024;p.tx=-512;p.y=-128;p.ty=-1024;p.run(179,{false,true});local k=p.step({['P1 X2']=true});assert(k['P1 X4'] and not k['P1 X2']);scenarios=scenarios+1 end
do local p=scenario();p.run(2600);assert(#p.starts()>=4 and p.images==3 and p.dumps==3);scenarios=scenarios+1 end
assert(scenarios==22)
"""
def run(policy):
    fn=types.FunctionType(harness.lua_check.__code__,dict(harness.__dict__,CHECK=CHECK),argdefs=harness.lua_check.__defaults__)
    fn(policy,'','')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh report')
    need(sha(Path(harness.__file__).read_bytes())=='2479D74DFA73F84E85EBECE0F047171F7401E9448B254DAE1D223EEC7AF3DE83','frozen host Lua harness')
    path=ROOT/'tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua';blob=path.read_bytes();wrapper=blob.decode('utf8')
    matches=re.findall(r'local policy=\[=\[(.*?)\]=\]',wrapper,re.S);need(len(matches)==1,'unique actual policy')
    policy=matches[0];run(policy);negative=[]
    for label,old,new in [('missing stage exclusion','stage==11','stage==10'),
        ('no anchor movement reset','math.abs(x-escape.anchor)>0x20','math.abs(x-escape.anchor)>0x2000'),
        ('no continuity reset','escape.last_frame~=frame-1','false'),
        ('gap equality admitted','y-ty>0x300','y-ty>=0x300')]:
        need(policy.count(old)==1,'unique mutation');bad=policy.replace(old,new)
        try:run(bad)
        except ValueError:negative.append(label)
        else:raise ValueError('mutation accepted '+label)
    report=dict(status='PASS',wrapper_sha256=sha(blob),actual_policy_scenarios=22,
        negative_controls_rejected=negative,continuous_start_frames=[179,778],
        scope='Actual extracted policy edge semantics; full nested wrapper and completion use separate22-route mock.',
        emulator_executed=False,guest_writes=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('PASS22 actual-policy scenarios;4 semantic negatives; no emulator')
if __name__=='__main__':main()
