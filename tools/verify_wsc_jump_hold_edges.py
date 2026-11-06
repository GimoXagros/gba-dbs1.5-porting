#!/usr/bin/env python3
"""Independent final-key jump hold boundary checks in actual Lua; no core."""
import argparse,json,re,types
from pathlib import Path
import verify_wsc_shoot_short_hard as harness
from analyze_shoot_lifetime_consumers import need,sha
ROOT=Path(__file__).resolve().parents[1]
CHECK=r'''
local scenarios=0
local function fresh(first)
 local s={frame=first,mode=7,stage=1,player=0x24,target=0x134}
 local e=setmetatable({memory={read_u16_le=function(a,d)
  assert(d=='SRAM');if a==0x4E then return s.mode elseif a==0x65C then return s.player end
  error('unexpected target-dependent read')end,
  read_u8=function(a,d)assert(a==0x5C and d=='SRAM');return s.stage end},
  emu={framecount=function()return s.frame end}},{__index=_G})
 local f=assert(load(wrapper_source..'\nreturn full_jump','@actual-jump-hold','t',e))()
 function s.step(a)
  local keys={['P1 A']=a,['P1 B']=true,['P1 X2']=true,['P1 X4']=false,other=37}
  local out=f(keys);assert(out==keys and out.other==37 and out['P1 X2'] and not out['P1 X4'])
  s.frame=s.frame+1;return out
 end
 return s
end
-- Every modulo phase and one/two/eight/twelve/long requested pulse.
for phase=0,89 do for _,n in ipairs({1,2,8,12,20})do
 local s=fresh(phase)
 for age=0,39 do
  s.target=age%2==0 and 0x134 or 0x244
  local k=s.step(age<n)
  assert(k['P1 A']==(age<math.max(12,n)),'phase-independent continuous A')
  assert(k['P1 B']==(age>=12),'bounded attack suppression')
 end
 scenarios=scenarios+1
end end
-- A second upstream edge during the active hold cannot make it unbounded.
for edge=1,11 do
 local s=fresh(0)
 for age=0,30 do
  local k=s.step(age==0 or age==edge)
  assert(k['P1 A']==(age<12),'bounded overlapping requests')
 end
 scenarios=scenarios+1
end
-- Release, rearm, and a fresh edge on the first sample after expiration.
for edge=12,24 do
 local s=fresh(0)
 for age=0,49 do
  local k=s.step(age==0 or age==edge)
  assert(k['P1 A']==(age<12 or age>=edge and age<edge+12),'fresh output pulse')
 end
 scenarios=scenarios+1
end
-- Discontinuities cancel an in-flight extension immediately; return is fresh.
for _,change in ipairs({function(s)s.mode=3 end,function(s)s.stage=11 end,
 function(s)s.stage=2 end,function(s)s.player=0x134 end,
 function(s)s.player=0x23 end,function(s)s.player=0x3655 end,function(s)s.player=0x25 end,
 function(s)s.frame=s.frame+1 end,function(s)s.frame=s.frame-1 end})do
 local s=fresh(0);s.step(true);change(s)
 local k=s.step(false);assert(not k['P1 A'] and k['P1 B'],'cancel on boundary')
 s.mode=7;s.stage=1;s.player=0x24
 k=s.step(false);assert(not k['P1 A'] and k['P1 B'],'no stale hold after return')
 for age=0,12 do k=s.step(age==0);assert(k['P1 A']==(age<12))end
 scenarios=scenarios+1
end
-- Valid last task slot and explicit/nil A behave identically.
do local s=fresh(0);s.player=0x3654;s.step(true)
 for age=1,12 do local k=s.step(nil);assert((k['P1 A']==true)==(age<12))end
 scenarios=scenarios+1 end
for _,change in ipairs({function(s)s.mode=3 end,function(s)s.stage=11 end,function(s)s.player=0x25 end})do
 local s=fresh(0);change(s)
 for age=0,14 do local k=s.step(age==0);assert(k['P1 A']==(age==0) and k['P1 B'],'excluded mode is transparent')end
 scenarios=scenarios+1
end
assert(scenarios==487)
'''

def run(policy):
    fn=types.FunctionType(harness.lua_check.__code__,dict(harness.__dict__,CHECK=CHECK),argdefs=harness.lua_check.__defaults__)
    fn(policy,'','')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh output')
    need(sha(Path(harness.__file__).read_bytes())=='2479D74DFA73F84E85EBECE0F047171F7401E9448B254DAE1D223EEC7AF3DE83','frozen Lua harness')
    path=ROOT/'tools/bizhawk_probe_wsc_shoot_short_hard_v3.lua';blob=path.read_bytes()
    found=re.findall(r'local policy=\[=\[(.*?)\]=\]',blob.decode('utf8'),re.S);need(len(found)==1,'unique actual policy')
    policy=found[0];run(policy);negative=[]
    for label,old,new in [('8 samples','remaining=12','remaining=8'),
        ('no countdown','jump_hold.remaining-1','jump_hold.remaining'),
        ('no discontinuity reset','jump_hold.frame~=frame-1','false'),
        ('no Shoot exclusion','stage==11','stage==99'),
        ('retrigger active hold',' and jump_hold.remaining==0',''),
        ('suppresses no attack','keys["P1 B"]=false','keys["P1 B"]=true')]:
        need(policy.count(old)==1,'unique mutation '+label)
        try:run(policy.replace(old,new))
        except ValueError:negative.append(label)
        else:raise ValueError('mutation accepted '+label)
    report=dict(status='PASS',wrapper_sha256=sha(blob),actual_policy_scenarios=487,
        negative_controls_rejected=negative,modulo_start_phases=90,emulator_executed=False,
        scope='Actual final-key policy only; full nested wrapper/release verified separately.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('PASS487 actual Lua policy scenarios;6 semantic negatives; no emulator')
if __name__=='__main__':main()
