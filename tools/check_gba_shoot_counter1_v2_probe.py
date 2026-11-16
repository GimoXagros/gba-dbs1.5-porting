"""Small author gate for immutable counter1 composition and same-core refusal."""
import argparse
import hashlib
import json
from pathlib import Path
import types

import check_gba_shoot_counter1_probe as prior

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'tools/bizhawk_probe_gba_shoot_counter1.lua'
WRAPPER=ROOT/'tools/bizhawk_probe_gba_shoot_counter1_v2.lua'
BASE_SHA='C625D710C9B2DE44D128D1846066B4F5C2326E7EC37B6875FFF98805B0A59C6C'
WRAPPER_SHA='053FD747027B9B5ED68769643EBA138BB5313249DFBAC4384427375F6F4F64A6'
sha=lambda b:hashlib.sha256(b).hexdigest().upper()


def once(text,before,after):
    assert text.count(before)==1,before
    return text.replace(before,after)


def quoted(blob):return '"'+''.join('\\'+f'{b:03d}'for b in blob)+'"'


def composed(blob):
    text=blob.decode();before='  if not target then ignored=ignored+1;return end\n'
    assert text.count(before)==6
    text=text.replace(before,before+'  if not need(target.core==emu.framecount(),"target-cycle-core",r)then return end\n')
    return once(text,'pending and pending.index==matches','pending and pending.core==emu.framecount()and pending.index==matches')


def harness():
    code=prior.CHECK
    begin='   for i,offset in ipairs({0,2,4,7,10,13,17,21})do'
    end='   m.put(0x04000006,38);m.fire(FINAL)'
    first,last=code.index(begin),code.index(end)+len(end)
    finish=code[first:last]
    code=code[:first]+'   finish_cycle()'+code[last:]
    code=once(code,' env.emu=setmetatable(', ' local function finish_cycle()\n'+finish+'\n end\n env.emu=setmetatable(')
    code=once(code,"   if mode=='never-target'or m.advances~=2 then return end", "   if mode=='cross-frame'and m.advances==3 then finish_cycle();return end\n   if mode=='never-target'or m.advances~=2 then return end")
    code=once(code,'   compare(0,1,0,0)\n   finish_cycle()',"   compare(0,1,0,0)\n   if mode=='cross-frame'then return end\n   finish_cycle()")
    code=once(code," if mode=='never-target'then assert(m.advances==200", " if mode=='cross-frame'then assert(m.advances==3 and done=='failure:target-cycle-core\\n')end\n if mode=='never-target'then assert(m.advances==200")
    code=once(code,"'wrong-owner','never-target'})do test(mode)end", "'wrong-owner','never-target','cross-frame'})do test(mode)end")
    return code


def execute(source,code):
    helper=prior.lua_host
    fn=types.FunctionType(helper.lua_check.__code__,dict(helper.__dict__,CHECK=code),argdefs=helper.lua_check.__defaults__)
    fn(source,'','')


def actual_wrapper(wrapper,base,effective):
    code=once(harness(),' env.io={open=function(path,access)', ' fixture["W:/tools/bizhawk_probe_gba_shoot_counter1.lua"]=hard_source\n env.io={open=function(path,access)')
    code=once(code," assert(load(wrapper_source,'@actual-counter1-probe','t',env))()", """ local native_load=load;local loads=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and name=='@reviewed-counter1-samecore-v2'and kind=='t'and scope==env,'onlysixsamecorechecksandpendingcore')
  loads=loads+1;return native_load(text,name,kind,scope)
 end
 assert(load(wrapper_source,'@actual-counter1-probe','t',env))()
 assert(loads==1)""")
    execute(wrapper,'hard_source='+quoted(base)+'\ncollect_source='+quoted(effective.encode())+'\n'+code)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();assert not args.output.exists()
    base=BASE.read_bytes();wrapper=WRAPPER.read_bytes()
    assert sha(base)==BASE_SHA and sha(wrapper)==WRAPPER_SHA
    assert sha(Path(prior.__file__).read_bytes())=='4A188C9F387FE4CEBA105C3F6248AC9C3EB45AE38A4BF5420AC229C6526EF2A5'
    effective=composed(base);actual_wrapper(wrapper.decode(),base,effective)
    execute(effective,harness())
    controls=[]
    weakened=effective.replace('need(target.core==emu.framecount(),"target-cycle-core",r)','need(true,"target-cycle-core",r)').replace('pending.core==emu.framecount()and ','')
    try:execute(weakened,harness())
    except ValueError:controls.append('cross-frame-remainder-falsely-accepted')
    else:raise AssertionError('samecorecontrolsurvived')
    assert BASE.read_bytes()==base
    report=dict(status='COUNTER1_V2_SAME_CORE_AUTHOR_LUA54_PASS',base_sha256=BASE_SHA,wrapper_sha256=WRAPPER_SHA,effective_sha256=sha(effective.encode()),verifier_sha256=sha(Path(__file__).read_bytes()),exact_delta_six_target_core_checks_and_pending_core=True,retained_six_prior_affected_cases=True,cross_frame_first69937_rest69938_refused=True,semantic_controls_rejected=controls,base_unchanged=True,new_hooks=False,new_guest_writes=False,emulator_launched=False,actual_counter1_timing_claim=False,old_full_suite_rerun=False)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS actualLua54 immutablecomposition/sevenaffectedcases/crossframerefusal')


if __name__=='__main__':main()
