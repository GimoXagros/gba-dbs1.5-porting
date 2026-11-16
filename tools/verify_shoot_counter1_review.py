"""Independent narrow counter1 observer review; never launches the host."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import types
import check_gba_shoot_counter1_probe as author
from verify_shoot_attack_dispatch import Machine

ROOT=Path(__file__).resolve().parents[1]
BASE_LUA='C625D710C9B2DE44D128D1846066B4F5C2326E7EC37B6875FFF98805B0A59C6C'
BASE_CHECK='4A188C9F387FE4CEBA105C3F6248AC9C3EB45AE38A4BF5420AC229C6526EF2A5'
BASE_HOST='7A52BBA2968423FC4520ED5854BC3F7FB50DD6725B262B8E0693EF2F4E570448'
V2_LUA='053FD747027B9B5ED68769643EBA138BB5313249DFBAC4384427375F6F4F64A6'
V2_HOST='D7D1627BF2B0CCAD089C3128F764D7953D466BAD499B124DA0F1A965D632735D'
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)

def cross_frame_harness(expect_accept):
    check=author.CHECK
    begin=check.index('   for i,offset in ipairs({0,2,4,7,10,13,17,21})do')
    end=check.index('  end},{__index=',begin)
    completion=check[begin:end]
    check=check.replace("   if mode=='never-target'or m.advances~=2 then return end",
        "   if mode=='cross-frame-cycle' and m.advances==3 then\n"+completion+
        "\n    return end\n   if mode=='never-target'or m.advances~=2 then return end")
    check=check.replace('   compare(0,1,0,0)\n',
                        "   compare(0,1,0,0)\n   if mode=='cross-frame-cycle' then return end\n")
    if expect_accept:
        check=check.replace("if mode=='positive'or mode=='midcycle-ignore'then",
                            "if mode=='positive'or mode=='midcycle-ignore'or mode=='cross-frame-cycle'then")
        check=check.replace('m.advances==2)',"m.advances==(mode=='cross-frame-cycle' and 3 or 2))")
    check=check.replace("{'positive','missing-first','deadline-late','midcycle-ignore','wrong-owner','never-target'}",
                        "{'cross-frame-cycle'}")
    return check

def lua(source,check):
    helper=types.FunctionType(author.lua_host.lua_check.__code__,dict(author.lua_host.__dict__,CHECK=check),
                              argdefs=author.lua_host.lua_check.__defaults__)
    helper(source,'','')

def compose(wrapper,old):
    before='  if not target then ignored=ignored+1;return end\n'
    after=before+'  if not need(target.core==emu.framecount(),"target-cycle-core",r)then return end\n'
    need(old.count(before)==6 and old.count('pending and pending.index==matches')==1,'exact six hooks and unique store')
    expected=old.replace(before,after).replace('pending and pending.index==matches',
                         'pending and pending.core==emu.framecount()and pending.index==matches')
    check=r'''
local captured
local env=setmetatable({},{__index=_G})
env.userdata={get=function(k)assert(k=='probe_sha256');return '280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'end}
env.io={open=function(path,mode)
 assert(path=='W:/tools/bizhawk_probe_gba_shoot_counter1.lua'and mode=='rb')
 return{read=function(_,fmt)assert(fmt=='*a');return hard_source end,close=function()end}
end}
env.load=function(body,name,mode,e)
 assert(name=='@reviewed-counter1-samecore-v2'and mode=='t'and e==env and not captured)
 captured=body;return function()end
end
assert(load(wrapper_source,'@actual-v2-composition','t',env))()
assert(captured==collect_source,'whole effective probe differs from seven exact insertions')
'''
    helper=types.FunctionType(author.lua_host.lua_check.__code__,dict(author.lua_host.__dict__,CHECK=check),
                              argdefs=author.lua_host.lua_check.__defaults__)
    helper(wrapper,old,expected)
    return expected

def readonly_host_preflight(path):
    # Only execute the pinned host prefix preceding its first output-directory
    # assignment. The prefix verifies immutable inputs and parses genuine Core;
    # it neither allocates output nor constructs a PrivateDesktopProcess.
    tree=ast.parse(path.read_text(encoding='utf-8'));prefix=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='out' for t in node.targets):break
        prefix.append(node)
    else:raise ValueError('missing host side-effect boundary')
    source=ast.unparse(ast.Module(body=prefix,type_ignores=[]))
    need('mkdir' not in source and 'PrivateDesktopProcess(' not in source and 'write_bytes' not in source,
         'read-only prefix only')
    env={'__file__':str(path),'__name__':'counter1_readonly_prefix'}
    exec(compile(ast.Module(body=prefix,type_ignores=[]),str(path),'exec'),env)
    need(env['parsed']['frame']==69935 and sha(env['source_core'])=='32A904634D2E9F941853496BE03431EBE276234A1C7E28A9DAD3129387C05583',
         'genuine exact checkpoint Core')
    rom=env['rom']
    need(rom[0xC4C:0xC58]==bytes.fromhex('0183a0e3b400d8e11eff2fe1'),'actual DISPSTAT helper instructions')
    for programmed in range(256):
        m=Machine(rom);m.r[14]=0x09000000
        m.put(0x04000004,(programmed<<8)|5,2);m.put(0x04000006,255-programmed,2)
        m.run(0x08000C4C,{0x09000000})
        need(m.r[0]==(programmed<<8)|5,'actual helper reads DISPSTAT, independently of VCOUNT')
    return dict(frame=69935,core_sha256=sha(env['source_core']),rom_sha256=sha(rom),
                all_five_source_RAM_embedded_equal=all(env['parsed']['compared_regions'].values()),
                actual_DISPSTAT_cases=256,host_executed=False,
                restore_contract='Host records whole Core equality and every differing byte; requires CPU bank, native extensions, managed suffix and all5RAM. Whole Core equality is not preclaimed.')

def main():
    p=argparse.ArgumentParser()
    for key in ('wrapper','host','report'):p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    baseline=ROOT/'tools/bizhawk_probe_gba_shoot_counter1.lua'
    oldhost=ROOT/'build/run_gba_shoot_counter1_20261110.py'
    need(sha(baseline.read_bytes())==BASE_LUA and sha(Path(author.__file__).read_bytes())==BASE_CHECK and sha(oldhost.read_bytes())==BASE_HOST,'immutable review baseline')
    need(sha(a.wrapper.read_bytes())==V2_LUA and sha(a.host.read_bytes())==V2_HOST,'frozen v2 wrapper and host')
    old=baseline.read_text(encoding='utf-8');new=compose(a.wrapper.read_text(encoding='utf-8'),old)
    lua(old,cross_frame_harness(True))
    lua(new,author.CHECK)
    lua(new,cross_frame_harness(False))
    need(not re.search(r'(?:memory|mainmemory)\.write|emu\.setregister',new),'no guest-write APIs')
    host=a.host.read_text(encoding='utf-8');old_host=oldhost.read_text(encoding='utf-8')
    # Apart from new wrapper pin/path and output destination, the reviewed
    # host including Core qualification must remain byte-for-byte equivalent.
    normalized=host.replace(a.wrapper.name,baseline.name).replace(sha(a.wrapper.read_bytes()),BASE_LUA)
    extra_assert="assert h((r/'tools/bizhawk_probe_gba_shoot_counter1.lua').read_bytes())=='"+BASE_LUA+"'\n"
    need(normalized.count(extra_assert)==1,'new immutable-base assertion')
    normalized=normalized.replace(extra_assert,'')
    extra_pin="(script,r/'tools/bizhawk_probe_gba_shoot_counter1.lua',"
    need(normalized.count(extra_pin)==1,'new base file in post-run pins')
    normalized=normalized.replace(extra_pin,'(script,')
    old_output=re.search(r"out=r/'([^']+)'",old_host).group(1)
    new_output=re.search(r"out=r/'([^']+)'",host).group(1)
    normalized=normalized.replace(new_output,old_output)
    need(normalized==old_host,'complete narrowly normalized host identity')
    preflight=readonly_host_preflight(a.host.resolve())
    report=dict(status='COUNTER1_INDEPENDENT_FRESH_CYCLE_PREFLIGHT_PASS',
                wrapper_sha256=sha(a.wrapper.read_bytes()),host_sha256=sha(a.host.read_bytes()),
                verifier_sha256=sha(Path(__file__).read_bytes()),
                effective_probe_sha256=sha(new.encode()),exact_composition_insertions=7,
                baseline_cross_frame_false_acceptance_reproduced=True,
                revised_cross_frame_false_acceptance_rejected=True,
                retained_actual_Lua54_cases=6,preflight=preflight,
                limits=['No emulator launch or actual counter1 timing witnessed here.',
                        'Actual8matches/stores/final and first VCOUNT deadline await root run.',
                        'Post-load whole Core differences require explicit later capture qualification.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(sha(a.report.read_bytes()))

if __name__=='__main__':main()
