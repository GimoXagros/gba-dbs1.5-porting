"""Independent affected Lua store-passage observer and exact host delta QA."""
import argparse
import ast
import json
from pathlib import Path
import re
import types
import verify_gba_shoot_terminal_display_epoch_wrapper as prior

ROOT=Path(__file__).resolve().parents[1]
WRAPPER='3A18BCE55CA83DF52300375B19BF7F5EAACDD08ED3498D18A0E4DC1D55CF934B'
HOST='9636A1C3A3EAD031B25C2357B5E29DBDA41480B4813B10D5AD6B43F3B258B961'
PINS='499AB2425B36F7749BE07930FA8E034F1086293B7AA5D7491615395685F60A3B'
sha=prior.sha

def lua(code,source=''):
    helper=prior.owner.palette.lua_host
    fn=types.FunctionType(helper.lua_check.__code__,dict(helper.__dict__,CHECK=code),argdefs=helper.lua_check.__defaults__)
    fn(source,'','')

def isolated(block):
    pre=r'''
local function test(mode,value,bus)
 local scroll_pending=value;local scroll_after=false
 local hooks,logs,queued,failures={},{},{},{}
 local shadow=value
 local function b(a)assert(a==0x030012B8);return shadow end
 local function w(a)error('write-only bus read forbidden')end
 local function hook(a,label,fn)assert(not hooks[a]);hooks[a]=fn end
 local function need(ok,label,r)if not ok then failures[#failures+1]=label end;return ok end
 local function log(kind,text,r)logs[#logs+1]=kind end
 local function queue(name,r)queued[#queued+1]=name end
 local function irq_state()return 'raw-MMIO-diagnostic='..bus end
'''
    post=r'''
 local r={R14=0x085E743C,R0=value,R8=0x030012B8,R9=0x04000000,R10=(value-8)&0xFFFF,R5=0x0300456C}
 local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==3)
 if mode=='irrelevant'then scroll_pending=nil;for _,a in ipairs({0x08000F3C,0x08000F40,0x085E743C})do hooks[a](r)end
  assert(#logs==0 and #queued==0 and #failures==0);return end
 if mode=='wrong-R14'then r.R14=0 elseif mode=='wrong-R0'then r.R0=value+1
 elseif mode=='wrong-R8'then r.R8=0 elseif mode=='wrong-R9'then r.R9=0
 elseif mode=='wrong-R10'then r.R10=r.R10+1 elseif mode=='wrong-shadow'then shadow=value+1 end
 if mode~='missing-pre'then hooks[0x08000F3C](r)end
 if mode=='duplicate-pre'then hooks[0x08000F3C](r)end
 if mode=='changed-R10'then r.R10=r.R10+1 elseif mode=='changed-R14'then r.R14=0 end
 if mode~='missing-completed'then hooks[0x08000F40](r)end
 if mode=='duplicate-completed'then hooks[0x08000F40](r)end
 if mode=='wrong-return-owner'then r.R5=0 elseif mode=='changed-shadow'then shadow=value+1 end
 hooks[0x085E743C](r)
 if mode=='success'then
  assert(scroll_after and scroll_pending==nil and #failures==0 and #queued==1)
  assert(#logs==3 and logs[1]=='next-scroll-store-pre'and logs[2]=='next-scroll-store-executed'and logs[3]=='next-display-scroll-post')
  hooks[0x085E743C](r);assert(#queued==1,'witness consumed exactly once')
 else assert(#failures>0,'invalid witness must fail')end
end
for _,v in ipairs({0,7,8,0x70,255})do
 for _,bus in ipairs({0,0x68,0xC000,0x66BB,0xFFFF})do test('success',v,bus)end
end
for _,mode in ipairs({'missing-pre','missing-completed','wrong-R14','wrong-R0','wrong-R8','wrong-R9','wrong-R10','wrong-shadow','changed-R10','changed-R14','wrong-return-owner','changed-shadow','duplicate-pre','duplicate-completed','irrelevant'})do test(mode,0x70,0xC000)end
'''
    lua(pre+block+post)

def audit():
    path=ROOT/'tools/bizhawk_probe_gba_shoot_terminal_display_store.lua'
    blob=path.read_bytes();assert sha(blob)==WRAPPER
    text=blob.decode();blocks=re.findall(r'local (old_scroll|new_scroll)=\[=\[(.*?)\]=\]',text,re.S)
    assert len(blocks)==2;blocks=dict(blocks);oldblock,newblock=blocks['old_scroll'],blocks['new_scroll']
    base=(ROOT/'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()
    assert sha(base)==prior.owner.palette.prior.LUA
    previous=prior.composed(base).decode();assert previous.count(oldblock)==1
    expected=previous.replace(oldblock,newblock)
    # The actual wrapper must produce exactly prior observer plus one block change.
    quote=prior.owner.palette.quoted
    code='local original='+quote(base)+'\nlocal expected='+quote(expected.encode())+r'''
local reads,loads=0,0
local env=setmetatable({},{__index=_G})
env.userdata={get=function()return 'ROM'end}
env.io={open=function(path,mode)assert(path=='W:/tools/bizhawk_probe_gba_shoot_terminal.lua'and mode=='rb');reads=reads+1;return{read=function()return original end,close=function()end}end}
env.load=function(body,name,kind,scope)assert(body==expected and name=='@reviewed-terminal-display-store-observer'and kind=='t'and scope==env);loads=loads+1;return function()end end
assert(load(wrapper_source,'@under-test','t',env))();assert(reads==1 and loads==1)
'''.replace("'ROM'","'"+prior.ROM+"'")
    lua(code,text);isolated(newblock)
    controls=[]
    for label,needle,replacement in (
        ('accept-missing-executed','scroll_store and scroll_store.executed and r.R5','scroll_store and r.R5'),
        ('ignore-store-value','(r.R10&0xFFFF)==((scroll_pending-8)&0xFFFF)','true'),
        ('ignore-return-owner','r.R5==0x0300456C','true')):
        assert newblock.count(needle)==1
        try:isolated(newblock.replace(needle,replacement))
        except ValueError:controls.append(label)
        else:raise AssertionError('control survived '+label)
    hostpath=ROOT/'build/run_gba_shoot_terminal_display_store_20261110.py'
    host=hostpath.read_bytes();assert sha(host)==HOST
    pins_blob=(ROOT/'build/gba-shoot-terminal-display-store-pins-20261110.json').read_bytes();assert sha(pins_blob)==PINS
    pins=json.loads(pins_blob)
    for name,digest in pins.items():assert sha((ROOT/name).read_bytes())==digest
    parent=(ROOT/'build/run_gba_shoot_terminal_display_epoch_20261110.py').read_bytes();assert sha(parent)==prior.HOST
    expected_host=parent.decode().replace('Repeat the frozen terminal test with the reviewed display-epoch repair.','Repeat the same display-epoch ROM with executed write-only scroll-store observation.')
    expected_host=expected_host.replace('bizhawk-gba-shoot-terminal-display-epoch-20261110','bizhawk-gba-shoot-terminal-display-store-20261110').replace('gba-shoot-terminal-display-epoch-pins','gba-shoot-terminal-display-store-pins').replace('bizhawk_probe_gba_shoot_terminal_display_epoch.lua','bizhawk_probe_gba_shoot_terminal_display_store.lua')
    assert expected_host==host.decode(),'host exact description/name-only delta'
    compile(ast.parse(host),str(hostpath),'exec')
    assert 'w(0x04000014)' not in newblock and not re.search(r'write_u|setregister|savestate|read_bytes|frameadvance',newblock)
    return dict(status='TERMINAL_DISPLAY_STORE_WRAPPER_HOST_PASS',wrapper_sha256=WRAPPER,host_sha256=HOST,pins_sha256=PINS,
        effective_observer_sha256=sha(expected.encode()),exact_prior_observer_plus_one_scroll_block=True,
        actual_Lua54_positive_cases=25,negative_cases=14,irrelevant_call_cases=1,semantic_controls_rejected=controls,
        native_store_witness=['08000F3C operands','08000F40 adjacent passage','085E743C shadow and owner'],
        arbitrary_MMIO_diagnostic_values_do_not_fail=True,no_write_only_register_read_assertion=True,
        all_eight_IRQ_conditions_unchanged=True,host_exact_names_description_delta=True,host_not_executed=True,
        ROM_unchanged=prior.ROM,new_guest_writes=False,emulator_launched=False,old_full_suite_rerun=False,
        verifier_sha256=sha(Path(__file__).read_bytes()),actual_store_or_terminal_success_claim=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();r=audit();a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes((json.dumps(r,indent=2)+'\n').encode());print('PASS',sha(a.output.read_bytes()))
if __name__=='__main__':main()
