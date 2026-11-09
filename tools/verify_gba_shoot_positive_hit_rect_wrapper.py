"""Narrow ROM-binding delta QA; reuse one affected Lua route, not prior suite."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import types

import verify_gba_shoot_positive_hit_lua as previous
import verify_wsc_shoot_short_hard as lua_host

ROOT=Path(__file__).resolve().parents[1]
OLD='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
NEW='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
WRAPPER='619AA09DD23411642801EF403459FB76B08FC07D3C21E8E2E982E3B22D50EB43'
HOST='03CAD24CCD2FCB46C5DBC5DF6F2E37BF577B1C7CEF4B91F3F5D4C49F2E6AF434'

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def execute(wrapper,original,check):
 fn=types.FunctionType(lua_host.lua_check.__code__,dict(lua_host.__dict__,CHECK=check),
  argdefs=lua_host.lua_check.__defaults__)
 fn(wrapper,original,'')

def check_rebind(wrapper,original):
 # Reuse the actual old host fixture definition only, running its success route once.
 prefix,tail=previous.CHECK.split("test('success');test('legal-types');test('bounded')",1)
 assert tail and prefix.count("probe_sha256='"+OLD+"'")==1
 prefix=prefix.replace("probe_sha256='"+OLD+"'","probe_sha256='"+NEW+"'")
 anchor=' env.io={open=function(path,access)'
 assert prefix.count(anchor)==1
 prefix=prefix.replace(anchor,' reference["W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua"]=hard_source\n'+anchor)
 anchor=" local ok,err=pcall(assert(load(wrapper_source,'@actual-positive-hit','t',env)))"
 assert prefix.count(anchor)==1
 replacement=r'''
 local expected=hard_source:gsub("OLD_ROM","NEW_ROM")
 local rebinds=0;local native_load=load
 env.load=function(text,name,kind,scope)
  assert(text==expected and name=='@reviewed-positive-hit-rectangle-repair' and kind=='t' and scope==env,'only unique ROM literal changes')
  rebinds=rebinds+1;return native_load(text,name,kind,scope)
 end
'''.replace('OLD_ROM',OLD).replace('NEW_ROM',NEW)+anchor+"\n assert(rebinds==1,'exactly one actual probe load')"
 prefix=prefix.replace(anchor,replacement)
 execute(wrapper,original,prefix+"\ntest('success')\n")

ANCHORS=r'''
local target='NEW_ROM'
for _,mode in ipairs({'wrong-token','missing','duplicate','missing-file','missing-read'})do
 local reads,loads,executes=0,0,0
 local payload=hard_source
 if mode=='missing'then payload=payload:gsub('OLD_ROM',target)end
 if mode=='duplicate'then payload=payload..'\n-- OLD_ROM'end
 local env=setmetatable({},{__index=_G});env._ENV=env
 env.userdata={get=function(k)assert(k=='probe_sha256');return mode=='wrong-token' and 'OLD_ROM' or target end}
 env.io={open=function(path,access)
  assert(path=='W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua' and access=='rb');reads=reads+1
  if mode=='missing-file'then return nil end
  return {read=function()return mode~='missing-read' and payload or nil end,close=function()end}
 end}
 env.load=function()loads=loads+1;return function()executes=executes+1 end end
 assert(not pcall(assert(load(wrapper_source,'@actual-wrapper','t',env))),'bad binding refused: '..mode)
 assert(loads==0 and executes==0,'bad binding never executes a probe')
 if mode=='wrong-token'then assert(reads==0,'wrong token refused before any file access')end
end
'''.replace('OLD_ROM',OLD).replace('NEW_ROM',NEW)

def host_delta(old,new):
 replacements=[
  ('bizhawk-gba-shoot-positive-hit-20261109-[a-z]','bizhawk-gba-shoot-positive-hit-rect-20261109-[a-z]'),
  ('build/gba-shoot-positive-hit-pins-20261109.json','build/gba-shoot-positive-hit-rect-pins-20261109.json'),
  ("assert set(pins) == {'tools/bizhawk_probe_gba_shoot_positive_hit.lua',",
   "assert set(pins) == {'tools/bizhawk_probe_gba_shoot_positive_hit_rect.lua', 'tools/bizhawk_probe_gba_shoot_positive_hit.lua',"),
  ('build/shoot-stage11-runtime-probe-20261109/component.gba','build/shoot-child-attack-rectangle-20261109/component.gba'),
  (OLD,NEW),
  ('--lua=W:/tools/bizhawk_probe_gba_shoot_positive_hit.lua','--lua=W:/tools/bizhawk_probe_gba_shoot_positive_hit_rect.lua'),
  ('genuine-healthy-Shoot-positive-hit-and-flash-expiry','genuine-healthy-Shoot-child-rectangle-repair-positive-hit-and-flash-expiry')]
 result=old
 for a,b in replacements:
  assert result.count(a)==1,'unique host delta anchor '+a
  result=result.replace(a,b)
 anchor="assert bytes(expected) == rom_data and source_rom[0xA0:0xB0] == rom_data[0xA0:0xB0]"
 block="""assert sha(bytes(expected)) == 'OLD_ROM'
for at in range(0x5B90A4, 0x5B9115, 0x10):
    assert expected[at:at+4] == bytes.fromhex('38043508')
    expected[at:at+4] = bytes.fromhex('80915B08')
assert expected[0x5B9180:0x5B918A] == b'\\xff'*10
expected[0x5B9180:0x5B918A] = bytes.fromhex('190000000000D000D000')
""".replace('OLD_ROM',OLD)
 assert result.count(anchor)==1
 result=result.replace(anchor,block+anchor)
 assert result==new,'entire host differs only in reviewed ROM/wrapper identity and exact new delta checks'
 return len(replacements)+1

def preflight(host):
 # The previously reviewed read-only prefix runner needs only the new allowed run name.
 code=inspect.getsource(previous.preflight)
 old="'bizhawk-gba-shoot-positive-hit-20261109-z'"
 assert code.count(old)==1
 code=code.replace(old,"'bizhawk-gba-shoot-positive-hit-rect-20261109-z'")
 namespace=dict(previous.__dict__)
 exec(compile(code,'@new-run-name-only-preflight','exec'),namespace)
 return namespace['preflight'](host)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists(),'fresh report'
 wrapper_path=ROOT/'tools/bizhawk_probe_gba_shoot_positive_hit_rect.lua'
 original_path=ROOT/'tools/bizhawk_probe_gba_shoot_positive_hit.lua'
 wrapper_blob,original_blob=wrapper_path.read_bytes(),original_path.read_bytes()
 assert sha(wrapper_blob)==WRAPPER and sha(original_blob)==previous.LUA_PIN
 assert sha(Path(previous.__file__).read_bytes())=='D38F5BCB6EBB15D9304A573C65803E03C6F8D6F849DD467C93F04317F1608BE1'
 wrapper,original=wrapper_blob.decode(),original_blob.decode()
 assert original.count(OLD)==1 and NEW not in original
 check_rebind(wrapper,original);execute(wrapper,original,ANCHORS)
 negatives=[]
 for label,x,y,fn in(
  ('wrong target',NEW,OLD,check_rebind),
  ('duplicate anchor accepted','assert(a and not source:find(old,b+1,true),','assert(a,',
   lambda w,o:execute(w,o,ANCHORS)),
  ('original suffix lost','..target..source:sub(b+1)','..target',check_rebind)):
  assert wrapper.count(x)==1,label
  try:fn(wrapper.replace(x,y),original)
  except ValueError:negatives.append(label)
  else:raise AssertionError('semantic mutation survived '+label)
 host=ROOT/'build/run_gba_shoot_positive_hit_rect_20261109.py'
 old_host=ROOT/'build/run_gba_shoot_positive_hit_20261109.py'
 assert sha(host.read_bytes())==HOST and sha(old_host.read_bytes())==previous.HOST_PIN
 deltas=host_delta(old_host.read_text(),host.read_text());prepared=preflight(host)
 pins=ROOT/'build/gba-shoot-positive-hit-rect-pins-20261109.json'
 assert sha(original_path.read_bytes())==previous.LUA_PIN and sha(wrapper_path.read_bytes())==WRAPPER
 report=dict(status='RECTANGLE_WRAPPER_HOST_DELTA_PASS',verifier_sha256=sha(Path(__file__).read_bytes()),
  wrapper_sha256=WRAPPER,original_observer_sha256=sha(original_blob),host_sha256=HOST,
  host_pins_sha256=sha(pins.read_bytes()),actual_Lua_composed_success_routes=1,
  anchor_refusal_cases=5,semantic_mutations_rejected=negatives,generated_observer_only_ROM_literal_changed=True,
  original_9F12_unchanged=True,reviewed_host_delta_groups=deltas,host_readonly_preflight=prepared,
  old_48_scenarios_rerun=False,input_policy_changed=False,guest_write_APIs_added=False,
  emulator_or_actual_state_load=False,rectangle_component_QA='Separate native_entry_qa responsibility',
  runtime_positive_hit_claim=False)
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
 print('PASS one actual Lua composed route,5 anchor refusals,3 controls and read-only new host preflight')

if __name__=='__main__':main()
