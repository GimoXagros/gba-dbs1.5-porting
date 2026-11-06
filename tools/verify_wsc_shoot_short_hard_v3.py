#!/usr/bin/env python3
"""Source jump startup and actual Lua final-key hold checks; no emulator."""
import argparse,json,struct,types
from pathlib import Path
import verify_wsc_shoot_short_hard_v2 as v2
from analyze_shoot_terminal_bx import exact,need,SOURCE
from build_character_p0_completion import source_pointer
sha=v2.sha
ROOT=Path(__file__).resolve().parents[1]
V2='85D7F25E2C6A8AA4C24AFBCDB95A51E7F9A3414FA3E97635FCD7C9EC3436ADE4'

def contracts(s):
    exact(s,0x768001,['test word ptr [si + 0x1e], 0x40','jne 0x768015',
        'test word ptr [si + 6], 0x80','jne 0x768015','mov word ptr [si + 0x8c], 1'])
    exact(s,0x768076,['mov dx, 8','cmp word ptr [si + 0x8c], 1','je 0x768091',
        'mov ax, word ptr es:[bx + 4]','mov word ptr [si + 0x34], ax',
        'mov ax, word ptr es:[bx + 6]','mov word ptr [si + 0x38], ax','mov dx, 5'])
    exact(s,0x768068,['mov ax, word ptr es:[bx + 0x14]','mov word ptr [si + 0x34], ax',
        'mov ax, word ptr es:[bx + 0x16]','mov word ptr [si + 0x38], ax'])
    exact(s,0x752885,['mov ax, word ptr [bp + 0xa]','sub byte ptr es:[di + 0x15], al',
        'cmp byte ptr es:[di + 0x15], 0','jl 0x752896','jmp 0x7529f5'])
    exact(s,0x7528A9,['test word ptr es:[di + 0xa], 1','jne 0x7528c3',
        'dec word ptr es:[di + 0x18]','xor byte ptr es:[di + 0x14], 1',
        'or word ptr es:[di + 0xa], 0x2000','jmp 0x7529f5'])
    exact(s,0x7528F6,['mov al, byte ptr [bx]','cmp al, 2','jae 0x7528fe','mov al, 2',
        'add byte ptr es:[di + 0x15], al'])
    events=[]
    for record,wanted in [(0,[1,3]),(30,[3,3])]:
        b=source_pointer(s,0x740000+record*32+6)
        n,o=struct.unpack_from('<2H',s,b+4+4*8)
        duration=[struct.unpack_from('<H',s,b+o+12*i)[0] for i in range(n)]
        need(duration==[0xFF00+d for d in wanted],'actual default jump startup rows')
        # Event setter is edge frame0. Animation becomes complete one update
        # after sum durations; actor observes it on the following callback.
        index,left,updates=0,wanted[0],0
        while index<len(wanted):
            updates+=1;left-=1
            if left<0:
                index+=1
                if index<len(wanted):left+=max(2,wanted[index])
        events.append(dict(record=record,raw=hex(b+o),durations=wanted,
            animation_updates=updates,launch_frame=updates+1,minimum_held_samples=updates+2))
    need([x['minimum_held_samples'] for x in events]==[7,9],'startup launch timing')
    stats=struct.unpack_from('<13h',s,0x3B8460+0x6E)
    need((stats[2],stats[3],stats[10],stats[11])==(-804,16,-512,20),'captured evolved jump vectors')
    return dict(events=events,evolved_full=[-804,16],evolved_short=[-512,20],
        scope='Unpaused uninterrupted default-character startup; no guarantee against hit/pause or successful navigation.')

EDGE=r'''
local p=assert(wrapper_source:match('local policy=%[=%[(.-)%]=%]'))
local function setup()
 local state={frame=89,mode=7,stage=1,player=0x24,target=0x134}
 local env=setmetatable({memory={read_u16_le=function(a)return a==0x4E and state.mode or a==0x65C and state.player or state.target end,
  read_u8=function()return state.stage end},emu={framecount=function()return state.frame end}},{__index=_G})
 local f=assert(load(p..'\nreturn full_jump','@actual-hold','t',env))()
 return state,f
end
for _,pulse in ipairs({1,5,8,12,20})do
 local s,f=setup()
 for age=0,24 do
  s.frame=89+age;s.target=age<3 and 0x134 or 0x244
  local k=f({['P1 A']=age<pulse,['P1 B']=true,['P1 X2']=true})
  assert(k['P1 A']==(age<math.max(12,pulse)),'late-window/orb-change continuous hold')
  assert(k['P1 B']==(age>=12),'attack suppression only bounded extension')
  assert(k['P1 X2'],'direction preserved')
 end
end
for _,kind in ipairs({'mode','shoot','player','frame','invalid-low','invalid-high','invalid-align','stage'})do
 local s,f=setup();assert(f({['P1 A']=true})['P1 A']);s.frame=s.frame+1
 if kind=='mode'then s.mode=3 elseif kind=='shoot'then s.stage=11 elseif kind=='player'then s.player=0x134
 elseif kind=='frame'then s.frame=s.frame+1 elseif kind=='stage'then s.stage=2
 elseif kind=='invalid-low'then s.player=0x23 elseif kind=='invalid-high'then s.player=0x3655 else s.player=0x25 end
 local k=f({['P1 A']=false,['P1 B']=true});assert(not k['P1 A'] and k['P1 B'],'reset boundary')
 if kind=='mode' or kind=='shoot' or kind:find('invalid',1,true) then
  s.frame=s.frame+1;f({['P1 A']=true});s.frame=s.frame+1
  assert(not f({['P1 A']=false})['P1 A'],'invalid-domain input cannot arm extender')
 end
end
local s,f=setup()
for age=0,35 do
 s.frame=age;local request=age==0 or age==16
 assert(f({['P1 A']=request})['P1 A']==(age<12 or age>=16 and age<28),'bounded release and retrigger')
end
'''

def run(wrapper,parent,prior,hard,collect):
    check=v2.mock(parent)
    check=v2.once(check,'env.io={open=function(path,mode_)',"env.io={open=function(path,mode_)\n if path=='W:/tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua' then assert(mode_=='rb');return {read=function()return v2_source end,close=function()end}end")
    check=v2.once(check,"assert(k['P1 A']==(age>=4 and age<12)and not k['P1 B'],'single8frame jump pulse without attacks')",
        "assert(not k['P1 B'],'no attacks during recovery');if age>=4 and age<12 then assert(k['P1 A'],'original jump requests retained')end")
    check=v2.once(check,'return frame,boss_attacks',r'''
 if boss_start then
  local held=0
  for t=boss_start+1,(shoot_start or frame)-1 do
   if journal[t]['P1 A'] then held=held+1
   elseif held>0 then assert(held>=12,'final-key jump pulse must survive collector and recovery');held=0 end
  end
 end
 return frame,boss_attacks''')
    check='local v2_source=[==[\n'+prior+']==]\n'+check+EDGE
    fn=types.FunctionType(v2.prior.lua_check.__code__,dict(v2.prior.__dict__,CHECK=check),argdefs=v2.prior.lua_check.__defaults__)
    fn(wrapper,hard,collect)

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh output');s=a.source.read_bytes();need(sha(s)==SOURCE,'source identity')
    proof=contracts(s)
    names=['bizhawk_probe_wsc_shoot_short_hard_v3.lua','bizhawk_probe_wsc_shoot_short_hard.lua',
        'bizhawk_probe_wsc_shoot_short_hard_v2.lua','bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua','bizhawk_probe_wsc_shoot_collect_v2.lua']
    blobs=[(ROOT/'tools'/n).read_bytes()for n in names]
    need([sha(x)for x in blobs[1:]]==[v2.PARENT,V2,v2.prior.HARD,v2.prior.COLLECT],'frozen dependencies')
    texts=[b.decode('utf8')for b in blobs];run(*texts);negative=[]
    for old,new,label in [('remaining=12','remaining=8','short hold'),('jump_hold.remaining-1','jump_hold.remaining','unbounded hold'),
        ('mode~=7 or stage==11','mode~=7 or stage==99','Shoot leak'),('keys["P1 B"]=false','keys["P1 B"]=true','attack interruption'),
        ('full_jump(wall_escape(keys))','wall_escape(full_jump(keys))','incorrect final-key ordering')]:
        need(texts[0].count(old)==1,'negative anchor '+label)
        bad=list(texts);bad[0]=bad[0].replace(old,new)
        try:run(*bad)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective negative '+label)
    for at in (0x768005,0x76807E,0x3B8460+0x72,0x3ACCFC):
        bad=bytearray(s);bad[at]^=1
        try:contracts(bad)
        except ValueError:negative.append(hex(at))
        else:raise ValueError('ineffective source mutation')
    result=dict(status='PASS',source=proof,full_mock_routes=22,hold_edge_scenarios=14,
        negative_controls=negative,dependency_sha256={n:sha(b)for n,b in zip(names,blobs)},
        runtime_executed=False,successful_navigation_claimed=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS22 full Lua routes +14 hold edge scenarios;9 negatives')
if __name__=='__main__':main()
