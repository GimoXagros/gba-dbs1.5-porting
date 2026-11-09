#!/usr/bin/env python3
"""Execute saved-score driver and frozen policy chain under synthetic Lua APIs.

DI and score modules are interface doubles here; each has separate actual-module
QA. No supplied save is read and no emulator is launched.
"""
import argparse
import json
from pathlib import Path
import re
import types
import verify_wsc_shoot_short_hard as prior
from verify_wsc_shoot_short_hard_v2 import once
from analyze_shoot_lifetime_consumers import SOURCE_SHA, need, sha

ROOT=Path(__file__).resolve().parents[1]
PINS={
 'bizhawk_probe_wsc_shoot_short_hard_v4.lua':'70B73AB398EAEEC83B117EEF06DD5FFFCEF9B7FACDA107C656B5E140F1D08C91',
 'bizhawk_probe_wsc_shoot_short_hard_v2.lua':'85D7F25E2C6A8AA4C24AFBCDB95A51E7F9A3414FA3E97635FCD7C9EC3436ADE4',
 'bizhawk_probe_wsc_shoot_short_hard.lua':'E382D2D1462B7507090483548FD12DBC97A0342BA0C90D617268D6460A63ABD0',
 'bizhawk_probe_wsc_shoot_collect_v2.lua':prior.COLLECT,
 'bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua':prior.HARD,
}


def fixture(texts):
    check=prior.CHECK
    check=once(check,'local files,callbacks={},{}',r'''
 local files,callbacks={},{}
 local enabled,di_finished,score_finished=false,false,false
 local copy=string.rep(string.char(0),0x8000)
 local function setbyte(s,a,v)return s:sub(1,a)..string.char(v)..s:sub(a+2)end
 copy=setbyte(setbyte(copy,0x4E,4),0x73,2)
 local initial=setbyte(setbyte(copy,0x4E,1),0x73,0)
 if kind=='bad-save' then initial=setbyte(initial,0x140,1) end
 if kind=='bad-boot' then initial=setbyte(initial,0x73,2) end
''')
    check=once(check,"callback_order='bizhawk2111-rew'", "callback_order='bizhawk2111-rew',source_sha256='"+SOURCE_SHA+"',save_copy_sha256='051055F0542503C63D77815C2B11F33A3DF420E6DD93D02D92779A430B02E51F'")
    check=once(check,"if a==at+0x52 then return at==0xC024 and 10 or 0 end",
        "if a==at+0x52 then return at==0xC024 and (enabled and mode==7 and stage==0 and 999 or 10) or 0 end")
    check=once(check,"getmemorydomainsize=function(d)return d=='ROM' and 0x800000 or 0x8000 end",
        "getmemorydomainsize=function(d)return ({ROM=0x800000,RAM=0x10000,SRAM=0x8000,iEEPROM=1024})[d]end")
    check=once(check,"read_bytes_as_binary_string=function()return 'mock' end}\n env.mainmemory=",
        "read_bytes_as_binary_string=function(a,n,d)return d=='SRAM' and initial or 'mock' end}\n env.mainmemory=")
    check=once(check,'env.io={open=function(path,mode_)',r'''
 env.io={open=function(path,mode_)
  if policy[path] then assert(mode_=='rb');return {read=function()return policy[path]end,close=function()end}end
  if mode_=='rb' and path=='W:/build/mock-short-hard/authorized-cartridge-copy.bin' then
   return {read=function()return copy end,close=function()end}
  end
  if mode_=='rb' and path:match('^W:/build/mock%-short%-hard/')then return nil end
''')
    check=once(check,'env.joypad={set=function(k)',"env.joypad={set=function(k)assert(enabled,'input before guard/module enablement')")
    check=once(check,'env.emu.frameadvance=function()',r'''
 env.dofile=function(path)
  local function ds()
   local reached=stage==11 and kind~='no-di'
   return {terminal_observed=reached,actual_final_irq_observed=reached,paired_reads=reached and 2 or 0,pending=false}
  end
  assert((files['W:/build/mock-short-hard/saved-score-driver.txt']or''):find('initial_cartridge_copy_exact_after_source_boot=true',1,true))
  if path=='W:/tools/bizhawk_observe_wsc_shoot_di_v3.lua' then
   return {status=ds,finish=function()assert(not di_finished);di_finished=true;return ds()end}
  end
  assert(path=='W:/tools/bizhawk_wsc_score999.lua')
  return {tick=function()assert(not enabled);enabled=true end,status=function()return {}end,
   finish=function()assert(enabled and not score_finished);score_finished=true;return {writes=1,hits=2}end}
 end
 env.emu.frameadvance=function()
''')
    check=once(check,";fire('terminal-owner-7732376')",'')
    check=once(check,";fire('terminal-owner-7813322')",'')
    check=once(check,"assert(load(wrapper_source,'@actual-wrapper','t',env))()",r'''
 local ok,err=pcall(assert(load(wrapper_source,'@actual-driver','t',env)))
 if kind=='bad-save' or kind=='bad-boot' then
  assert(not ok and tostring(err):find('entire actual save',1,true));assert(not enabled and not exited and frame==0)
  assert(not files['W:/build/mock-short-hard/done.txt']);return
 end
 assert(ok,err)
''')
    check=once(check,"assert(exited and files['W:/build/mock-short-hard/done.txt']=='observation-complete')",r'''
 assert(exited and enabled and di_finished and score_finished)
 assert(files['W:/build/mock-short-hard/base-observation-complete.txt']=='observation-complete')
 local reached=stage==11 and kind~='no-di'
 assert(files['W:/build/mock-short-hard/done.txt']==(reached and 'shoot-di-observed' or 'bounded-observation-complete'))
 assert(not callbacks['terminal-owner-7813322'] and not callbacks['terminal-owner-7732376'])
 assert(files['W:/build/mock-short-hard/saved-stage-00.png'])
 if kind~='ordinary-orb' then assert(files['W:/build/mock-short-hard/saved-stage-07.png'])end
 if stage==11 then assert(files['W:/build/mock-short-hard/saved-stage-11.png'])end
''')
    check=once(check,"assert(files['W:/build/mock-short-hard/options-short-hard-sram.bin']=='mock')",
        "assert(files['W:/build/mock-short-hard/options-short-hard-sram.bin']==initial)")
    check=once(check,"assert(callbacks['terminal-owner-7813322'] and callbacks['lower-8EF3-spatial'])",
        "assert(not callbacks['terminal-owner-7813322'] and callbacks['lower-8EF3-spatial'])")
    check=once(check,"assert(files['W:/build/mock-short-hard/terminal-owners.txt'])",
        "assert(not files['W:/build/mock-short-hard/terminal-owners.txt'])")
    check=once(check,"local trace=files['W:/build/mock-short-hard/trace.txt']",r'''
 local trace=files['W:/build/mock-short-hard/trace.txt']
 assert(trace:find('guest_writes=authorized-score999-module-only',1,true))
 assert(trace:find('supplied_save=authorized-copy',1,true))
 assert(not trace:find('supplied_save=none',1,true) and not trace:find('guest_writes=none',1,true))
''')
    check=once(check,"{'boss-bounded','ordinary-orb','no-shoot-clear','no-shoot-irq'}",
        "{'boss-bounded','ordinary-orb','no-shoot-irq','no-shoot-clear','no-di','bad-save','bad-boot'}")
    definitions='local policy={}\n'
    for name in ('bizhawk_probe_wsc_shoot_short_hard_v4.lua','bizhawk_probe_wsc_shoot_short_hard_v2.lua','bizhawk_probe_wsc_shoot_short_hard.lua'):
        definitions+=f'policy["W:/tools/{name}"]=[==[\n{texts[name]}]==]\n'
    return definitions+check


def run(driver,texts):
    fn=types.FunctionType(prior.lua_check.__code__,dict(prior.__dict__,CHECK=fixture(texts)),
        argdefs=prior.lua_check.__defaults__)
    fn(driver,texts['bizhawk_probe_wsc_shoot_lifetime_hard_v2.lua'],texts['bizhawk_probe_wsc_shoot_collect_v2.lua'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh report')
    texts={}
    for name,digest in PINS.items():
        data=(ROOT/'tools'/name).read_bytes();need(sha(data)==digest,'frozen policy '+name);texts[name]=data.decode('utf8')
    path=ROOT/'tools/bizhawk_probe_wsc_saved_score999.lua';text=path.read_text(encoding='utf8')
    need(not re.search(r'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister',text),'driver has no guest mutation API')
    run(text,texts);negative=[]
    for label,old,new in [
        ('unchecked save','assert(expected==actual,','assert(true,'),
        ('old owner hooks','collect:sub(1,a-1)..\'-- Legacy owner hooks removed; DI v3 owns consumed-operand evidence.\\n\'..collect:sub(b)','collect'),
        ('missing DI completion gate','and saved_di_ready() then','then'),
        ('false reached marker','reached and "shoot-di-observed" or "bounded-observation-complete"','"shoot-di-observed"'),
        ('missing score installation','score.tick() --','--score.tick() --'),
        ('missing score finalization','local ss=score.finish()','local ss={writes=1,hits=2}'),
    ]:
        need(old in text,'mutation target '+label)
        try:run(text.replace(old,new),texts)
        except ValueError:negative.append(label)
        else:raise ValueError('ineffective mutation '+label)
    report=dict(status='PASS',driver_sha256=sha(path.read_bytes()),frozen_policy_sha256=PINS,
        mocked_routes=19,negative_controls=negative,actual_driver_and_policy_chain=True,
        score_and_DI_modules='interface doubles; separate module QA required',
        supplied_save_read=False,emulator_launched=False,actual_Shoot_observed=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('PASS actual driver + five frozen Lua policies;19 routes/6 mutations; synthetic save only')


if __name__=='__main__':main()
