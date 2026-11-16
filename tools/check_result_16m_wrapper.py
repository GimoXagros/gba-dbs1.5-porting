"""Tiny actual Lua54 composition/binding gate for the 16MiB result observer."""
import argparse
import hashlib
import json
from pathlib import Path
import types
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
BASE='928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
WRAPPER='5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF'
BEFORE='dump("loaded-rom.bin","ROM",0,0x800000)'
AFTER=BEFORE.replace('0x800000','0x1000000')
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
quoted=lambda b:'"'+''.join('\\'+f'{x:03d}' for x in b)+'"'


def check(wrapper,original):
    assert original.count(BEFORE.encode())==1
    body=r'''
for _,mode in ipairs({'valid','wrong-size','missing','duplicate','missing-file','failed-read'})do
 local payload=hard_source;local reads,loads,runs=0,0,0
 if mode=='missing'then payload=collect_source end
 if mode=='duplicate'then payload=payload..'\n-- '..OLD end
 local env=setmetatable({},{__index=_G})
 env.memory={getmemorydomainsize=function(d)assert(d=='ROM');return mode=='wrong-size'and 0x800000 or 0x1000000 end}
 env.io={open=function(path,access)
  reads=reads+1;assert(path=='W:/tools/bizhawk_probe_result_languages.lua'and access=='rb')
  if mode=='missing-file'then return nil end
  return{read=function(_,kind)assert(kind=='*a');return mode~='failed-read'and payload or nil end,close=function()end}
 end}
 env.load=function(text,name,kind,scope)
  loads=loads+1;assert(mode=='valid'and text==collect_source and name=='@reviewed-result-sixteen-MiB-capture'and kind=='t'and scope==env,'entirebaseonlyROMextentchange')
  assert(load(text,name,kind,scope),'actualcomposedsyntax')
  return function()runs=runs+1 end
 end
 local ok=pcall(assert(load(wrapper_source,'@wrapper','t',env)))
 if mode=='valid'then assert(ok and loads==1 and runs==1)
 else assert(not ok and loads==0 and runs==0,'invalidbindingneverloads:'..mode)end
 if mode=='wrong-size'then assert(reads==0)end
end
'''.replace('OLD',quoted(BEFORE.encode()))
    code='hard_source='+quoted(original)+'\ncollect_source='+quoted(original.replace(BEFORE.encode(),AFTER.encode()))+'\n'+body
    fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__)
    fn(wrapper,'','')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();assert not args.report.exists()
    base=(ROOT/'tools/bizhawk_probe_result_languages.lua').read_bytes();wrapper=(ROOT/'tools/bizhawk_probe_result_languages_16m.lua').read_bytes()
    assert sha(base)==BASE and sha(wrapper)==WRAPPER;check(wrapper.decode(),base)
    rejected=[]
    for label,before,after in (
        ('wrong-extent',"local after='"+AFTER+"'","local after='"+BEFORE+"'"),
        ('duplicate-accepted','assert(a and not source:find(before,b+1,true),','assert(a,'),
        ('suffix-dropped','..after..source:sub(b+1)','..after'),
    ):
        text=wrapper.decode();assert text.count(before)==1
        try:check(text.replace(before,after),base)
        except ValueError:rejected.append(label)
        else:raise AssertionError('control survived:'+label)
    report=dict(status='RESULT_16M_WRAPPER_LUA54_COMPOSITION_PASS',wrapper_sha256=WRAPPER,base_sha256=BASE,effective_sha256=sha(base.replace(BEFORE.encode(),AFTER.encode())),exact_entire_base_only_ROM_dump8_to16MiB=True,actual_Lua54_composed_syntax=True,binding_scenarios=6,semantic_controls_rejected=rejected,ordinary_flow_rerun=False,emulator_launched=False,verifier_sha256=sha(Path(__file__).read_bytes()))
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],sha(args.report.read_bytes()))


if __name__=='__main__':main()
