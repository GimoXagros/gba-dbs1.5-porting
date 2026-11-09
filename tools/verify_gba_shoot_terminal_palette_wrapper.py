"""Independent ROM-only terminal wrapper/host delta QA; no old43-case rerun."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import types

import verify_gba_shoot_terminal_lua as prior
import verify_wsc_shoot_short_hard as lua_host

ROOT=Path(__file__).resolve().parents[1]
OLD='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
NEW='FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
WRAPPER='F0FB2E3164A69F666756C4CB51B0FDAE416BA2624A93BDA95D650C6303D6B278'
HOST='F6EC291569166A3BA996AD46325DD4BB2203F8520FEB0E7A087BE7C03A168502'
PINS='42A3FE105E0005AE0D67B2A7CE1369B008CC8DE3ED1EA78BF0E31229059C6E0D'

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def quoted(b):return '"'+''.join('\\'+f'{x:03d}'for x in b)+'"'
def execute(wrapper,original,body):
 code='hard_source='+quoted(original)+'\ncollect_source='+quoted(original.replace(OLD.encode(),NEW.encode()))+'\n'+body
 fn=types.FunctionType(lua_host.lua_check.__code__,dict(lua_host.__dict__,CHECK=code),argdefs=lua_host.lua_check.__defaults__)
 fn(wrapper,'','')

def actual_rebind(wrapper,original):
 body=prior.harness();assert body.count("probe_sha256='"+OLD+"'")==1
 body=body.replace("probe_sha256='"+OLD+"'","probe_sha256='"+NEW+"'")
 anchor=' env.io={open=function(path,access)';assert body.count(anchor)==1
 body=body.replace(anchor,' reference["W:/tools/bizhawk_probe_gba_shoot_terminal.lua"]=hard_source\n'+anchor)
 anchor=" local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))";assert body.count(anchor)==1
 replacement=''' local native_load=load;local rebinds=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and name=='@reviewed-terminal-palette-call-repair'and kind=='t'and scope==env,'entireobserveronlyuniqueROMliteralchanges')
  rebinds=rebinds+1;return native_load(text,name,kind,scope)
 end
'''+anchor+"\n assert(rebinds==1,'oneactualcomposedobserverload')"
 body=body.replace(anchor,replacement)
 execute(wrapper,original,body+"\ntest('success')\n")

ANCHORS=r'''
for _,mode in ipairs({'wrong-token','missing','duplicate','missing-file','missing-read'})do
 local reads,loads,executes=0,0,0;local payload=hard_source
 if mode=='missing'then payload=collect_source end
 if mode=='duplicate'then payload=payload..'\n-- OLD'end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='probe_sha256');return mode=='wrong-token'and'OLD'or'NEW'end}
 env.io={open=function(path,access)
  assert(path=='W:/tools/bizhawk_probe_gba_shoot_terminal.lua'and access=='rb');reads=reads+1
  if mode=='missing-file'then return nil end
  return{read=function()return mode~='missing-read'and payload or nil end,close=function()end}
 end}
 env.load=function()loads=loads+1;return function()executes=executes+1 end end
 assert(not pcall(assert(load(wrapper_source,'@binding-test','t',env))),'invalidbindingrefused:'..mode)
 assert(loads==0 and executes==0,'badbindingneverexecutes')
 if mode=='wrong-token'then assert(reads==0)end
end
'''.replace('OLD',OLD).replace('NEW',NEW)

def check_lua():
 assert sha(Path(prior.__file__).read_bytes())=='85CE28F03298A43A6335F6BDE05A9935D2826D45C22A3967F707DA77D830C728'
 wrapper=(ROOT/'tools/bizhawk_probe_gba_shoot_terminal_palette.lua').read_bytes();original=(ROOT/'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()
 assert sha(wrapper)==WRAPPER and sha(original)==prior.LUA
 assert original.count(OLD.encode())==1 and NEW.encode()not in original
 actual_rebind(wrapper.decode(),original);execute(wrapper.decode(),original,ANCHORS)
 rejected=[]
 for label,old,new,check in(
  ('wrongROMtarget',NEW,OLD,actual_rebind),
  ('duplicatedbindingaccepted','assert(a and not source:find(old,b+1,true),','assert(a,',lambda w,o:execute(w,o,ANCHORS)),
  ('observersuffixlost','..target..source:sub(b+1)','..target',actual_rebind)):
  text=wrapper.decode();assert text.count(old)==1
  try:check(text.replace(old,new),original)
  except ValueError:rejected.append(label)
  else:raise AssertionError('controlsurvived:'+label)
 assert sha((ROOT/'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes())==prior.LUA
 return dict(wrapper_sha256=WRAPPER,original_sha256=prior.LUA,effective_sha256=sha(original.replace(OLD.encode(),NEW.encode())),affected_actual_Lua54_scenarios=1,binding_refusals=5,semantic_controls_rejected=rejected,exact_entire_body_ROM_only=True,original_LF=original.count(b'\n'),original_CRLF=original.count(b'\r\n'),old43_case_suite_rerun=False)

def host_preflight():
 path=ROOT/'build/run_gba_shoot_terminal_palette_20261109.py';blob=path.read_bytes();assert sha(blob)==HOST
 assert sha((ROOT/'build/gba-shoot-terminal-palette-pins-20261109.json').read_bytes())==PINS
 parent=(ROOT/'build/run_gba_shoot_terminal_20261109.py').read_bytes();assert sha(parent)==prior.HOST
 code=blob.decode();expected=parent.decode()
 replacements=(
  ('"""Observe one real positive Shoot hit and natural flash expiry."""','"""Repeat the frozen terminal test with the source-bound palette-call repair."""'),
  ('bizhawk-gba-shoot-terminal-20261109-[a-z]','bizhawk-gba-shoot-terminal-palette-20261109-[a-z]'),
  ('build/gba-shoot-terminal-pins-20261109.json','build/gba-shoot-terminal-palette-pins-20261109.json'),
  ("assert set(pins) == {'tools/bizhawk_probe_gba_shoot_terminal.lua',","assert set(pins) == {'tools/bizhawk_probe_gba_shoot_terminal_palette.lua', 'tools/bizhawk_probe_gba_shoot_terminal.lua',"),
  ('build/shoot-child-attack-rectangle-20261109/component.gba','build/shoot-palette-project-calls-20261109/component.gba'),
  (OLD,NEW),('--lua=W:/tools/bizhawk_probe_gba_shoot_terminal.lua','--lua=W:/tools/bizhawk_probe_gba_shoot_terminal_palette.lua'))
 for old,new in replacements:assert expected.count(old)==1,old;expected=expected.replace(old,new)
 anchor='assert bytes(expected) == rom_data and source_rom[0xA0:0xB0] == rom_data[0xA0:0xB0]'
 block="""assert sha(bytes(expected)) == 'OLD'
for at, word in ((0x5C6F4C, 0x1B000020), (0x5C6F5C, 0x1B00001C),
                 (0x5C6F88, 0x1B000011), (0x5C6FBC, 0x1B000004)):
    assert struct.unpack_from('<I', expected, at)[0] == 0x1BFFFFFE
    struct.pack_into('<I', expected, at, word)
""".replace('OLD',OLD)
 assert expected.count(anchor)==1;expected=expected.replace(anchor,block+anchor)
 assert expected==code,'onlyreviewedROMwrapperpathand4worddelta'
 prefix=code.split("\nout = root / 'build' / name",1);assert len(prefix)==2
 tree=ast.parse(prefix[0]);compile(code,str(path),'exec')
 for node in ast.walk(tree):
  if isinstance(node,ast.Call):
   name=node.func.attr if isinstance(node.func,ast.Attribute)else node.func.id if isinstance(node.func,ast.Name)else ''
   assert name not in {'mkdir','write_text','write_bytes','copyfile','PrivateDesktopProcess'}
 argv=sys.argv[:]
 try:
  sys.argv=[str(path),'bizhawk-gba-shoot-terminal-palette-20261109-z'];env={'__file__':str(path),'__name__':'__readonly__'}
  exec(compile(tree,str(path)+':readonlyprefix','exec'),env)
 finally:sys.argv=argv
 return dict(host_sha256=HOST,pins_sha256=PINS,parent_delta_groups=8,readonly_prefix_executed=True,checkpoint_frame=env['parsed']['frame'],source_Core_sha256=sha(env['source_core']),same_healthy_checkpoint_policy_approval_ledger_and_180sec_bound=True,component_sha256=sha(env['rom_data']),paths_created=False,emulator_launched=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 report=dict(status='TERMINAL_PALETTE_WRAPPER_HOST_DELTA_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),Lua=check_lua(),host=host_preflight(),actual_terminal_completion_claim=False,synthetic_acceptance_not_actual_aux_transition=True)
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print('PASS actualLuaROMonlycomposition/bindingcontrols/read-onlyhost4wordpreflight')

if __name__=='__main__':main()
