#!/usr/bin/env python3
"""Reused actual-Lua v2 route checks with only recovery A extended to12."""
import argparse,json,types
from pathlib import Path
import verify_wsc_shoot_short_hard_v2 as v2
import verify_wsc_wall_escape_edges as edge
from analyze_shoot_terminal_bx import exact,SOURCE
from analyze_shoot_lifetime_consumers import need,sha
ROOT=Path(__file__).resolve().parents[1]
V2='85D7F25E2C6A8AA4C24AFBCDB95A51E7F9A3414FA3E97635FCD7C9EC3436ADE4'
V2_CHECK='1FF0ABF8FCF259719DA7F57ADD82CE613761B36303BD49277F4375277BA0A667'

def contracts(s):
    for at in (0x767A3D,0x767AA9):
        need(s[at:at+5]==bytes.fromhex('9a24028e66'),'ground callback attack poll')
    exact(s,0x767A5B,['lcall 0x668e, 0x1d6','or ax, ax','je 0x767a65','retf'])
    exact(s,0x767AC7,['lcall 0x668e, 0x1d6','or ax, ax','je 0x767ad1','retf'])
    exact(s,0x766AB6,['xor ax, ax','test word ptr [si + 0x20], 0x40','je 0x766b03',
        'mov word ptr [si], 0x16e8','mov word ptr [si + 2], 0x668e','mov ax, 4'])
    exact(s,0x766B04,['push bx','xor ax, ax','test word ptr [si + 0x20], 0x80','jne 0x766b11','jmp 0x766b98'])
    exact(s,0x766C4D,['xor ax, ax','test word ptr [si + 0x1e], 4','je 0x766c77'])
    exact(s,0x766A55,['push dx','xor ax, ax','test word ptr [si + 0x20], 0x40','je 0x766ab4',
        'test word ptr [si + 0x1e], 4','je 0x766ab4'])
    return dict(callback_segment=0x668E,callbacks=[0x115D,0x11C9],identity=0,
        guard='airbornebit clear, form100 clear, down not held; B suppressed',
        limitation='state sampling cannot exclude a later external hit/pause before acceptance')

def run(wrapper,parent,old,hard,collect):
    check=v2.mock(parent)
    check=v2.once(check,'env.io={open=function(path,mode_)',"env.io={open=function(path,mode_)\n if path=='W:/tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua' then assert(mode_=='rb');return {read=function()return v2_source end,close=function()end}end")
    check=v2.once(check,"assert(k['P1 A']==(age>=4 and age<12)and not k['P1 B'],'single8frame jump pulse without attacks')",
        "assert(k['P1 A']==(age>=4 and age<16)and not k['P1 B'],'single12frame recovery jump without attacks')")
    check=v2.once(check,'if a==0x3118 then return row end', 'if a==0xC024 then return 0x115D elseif a==0xC026 then return 0x668E end\n  if a==0x3118 then return row end')
    check='local v2_source=[==[\n'+old+']==]\n'+check
    fn=types.FunctionType(v2.prior.lua_check.__code__,dict(v2.prior.__dict__,CHECK=check),argdefs=v2.prior.lua_check.__defaults__)
    fn(wrapper,hard,collect)

def edge_run(wrapper,old):
    check=edge.CHECK.split('local scenarios=0')[0]
    check=v2.once(check,"local p={mode=7", "local p={callback=0x115D,segment=0x668E,flags=0,form=0,identity=0,mode=7")
    check=v2.once(check,'if a==0xC000+p.player+0x26 then',
        'if a==0xC000+p.player then return p.callback elseif a==0xC000+p.player+2 then return p.segment elseif a==0xC000+p.player+6 then return p.flags elseif a==0xC000+p.player+8 then return p.form elseif a==0xC000+p.player+0x26 then')
    check=v2.once(check,'end,read_bytes_as_binary_string=function(a,n)',
        'end,read_u8=function(a)assert(a==0xC000+p.player+0x11);return p.identity end,read_bytes_as_binary_string=function(a,n)')
    expand=r'''
local expanded
local e=setmetatable({io={open=function(path,mode)assert(path=='W:/tools/bizhawk_probe_wsc_shoot_short_hard_v2.lua' and mode=='rb');return {read=function()return old_source end,close=function()end}end},
 load=function(s)expanded=s;return function()end end},{__index=_G})
assert(load(wrapper_source,'@actual-v4-expansion','t',e))()
wrapper_source=assert(expanded:match('local policy=%[=%[(.-)%]=%]'))
'''
    tests=r'''
local cases=0
for _,landing in ipairs({0,13,48,49,99})do
 local p=scenario();p.run(179)
 for age=0,59 do
  p.callback=age<landing and 0x19D0 or 0x115D;p.flags=age<landing and 1 or 0
  local k=p.step();local start=math.max(4,landing)
  assert(k['P1 A']==(start<=48 and age>=start and age<start+12),'ground delay and bounded twelve samples')
  assert(k['P1 X2'] and not k['P1 X4'] and not k['P1 B'],'unchanged60backaway')
 end
 local notes=0;for _,n in ipairs(p.notes)do if n:find('escape-jump',1,true)then notes=notes+1 end end
 assert(notes==(landing<=48 and 1 or 0),'at most one pulse')
 for _=1,360 do local k=p.step();assert(k['P1 X4'] and k['P1 B'],'same cooldown')end
 p.callback=0x115D;p.flags=0;p.run(179);local k=p.step();assert(p.starts()[2]==778)
 for age=1,15 do k=p.step();assert(k['P1 A']==(age>=4),'new recovery resets pulse')end
 cases=cases+1
end
for _,field in ipairs({'callback','segment','flags','form','identity','down'})do
 local p=scenario();p.run(179)
 if field=='callback'then p.callback=0x19D0 elseif field=='segment'then p.segment=0x80EA
 elseif field=='flags'then p.flags=1 elseif field=='form'then p.form=0x100 elseif field=='identity'then p.identity=1 end
 for _=0,59 do local k=p.step({['P1 X4']=true,['P1 X3']=field=='down',['P1 B']=true});assert(not k['P1 A'],'acceptance guard')end
 cases=cases+1
end
for _,form in ipairs({0,0x4000})do
 local p=scenario();p.callback=0x11C9;p.form=form;p.run(179)
 for age=0,59 do assert(p.step()['P1 A']==(age>=4 and age<16),'base/evolved walk acceptance')end;cases=cases+1
end
for _,field in ipairs({'mode','stage','player','frame'})do
 local p=scenario();p.run(184) -- includes first held sample
 if field=='mode'then p.mode=3 elseif field=='stage'then p.stage=11 elseif field=='player'then p.player=0x134 else p.frame=p.frame+1 end
 assert(not p.step()['P1 A'],'existing reset cancels pulse');cases=cases+1
end
assert(cases==17)
'''
    check='local old_source=[==[\n'+old+']==]\n'+expand+check+tests
    fn=types.FunctionType(v2.prior.lua_check.__code__,dict(v2.prior.__dict__,CHECK=check),argdefs=v2.prior.lua_check.__defaults__)
    fn(wrapper,'','')

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh output');source=a.source.read_bytes();need(sha(source)==SOURCE,'source identity');proof=contracts(source)
    need(sha(Path(v2.__file__).read_bytes())==V2_CHECK,'frozen v2 test harness')
    names=['bizhawk_probe_wsc_shoot_short_hard_v4.lua','bizhawk_probe_wsc_shoot_short_hard.lua',
        'bizhawk_probe_wsc_shoot_short_hard_v2.lua','bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua','bizhawk_probe_wsc_shoot_collect_v2.lua']
    blobs=[(ROOT/'tools'/n).read_bytes()for n in names]
    need([sha(x)for x in blobs[1:]]==[v2.PARENT,V2,v2.prior.HARD,v2.prior.COLLECT],'frozen dependencies')
    text=[b.decode('utf8')for b in blobs];run(*text);edge_run(text[0],text[2]);negative=[]
    for old,new,label in [('age<escape.jump_age+12','age<escape.jump_age+8','short pulse'),
        ('age>=4 and age<=48','age>=0 and age<=48','no initial release'),('age<=48','age<=49','late clipped pulse'),
        ('callback==0x115D','callback==0x19D0','airborne callback accepted'),
        ('escape.stuck=0;escape.jump_age=nil','escape.stuck=0','stale pulse next recovery')]:
        need(text[0].count(old)==1,'negative anchor');bad=text[0].replace(old,new)
        try:edge_run(bad,text[2])
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective negative '+label)
    for at in (0x767A5C,0x767AC8,0x766ABC):
        bad=bytearray(source);bad[at]^=1
        try:contracts(bad)
        except ValueError:negative.append(hex(at))
        else:raise ValueError('ineffective source negative')
    result=dict(status='PASS',mocked_routes=22,recovery_acceptance_scenarios=17,source=proof,negative_controls=negative,
        dependency_sha256={n:sha(b)for n,b in zip(names,blobs)},
        change='one12sample recovery pulse begins only in default ground callback, age4..48, within original60',
        normal_chase_and_collector_unchanged=True,pre_first_escape_input_policy_unchanged=True,
        runtime_executed=False,successful_navigation_claimed=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS22 actualLua routes;17 recovery acceptance scenarios;8 negatives')
if __name__=='__main__':main()
