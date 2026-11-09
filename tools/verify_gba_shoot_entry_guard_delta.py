"""Execute only the native owner/checkpoint delta against captured positive RAM."""
import argparse
import hashlib
import json
from pathlib import Path
import types

import verify_gba_shoot_entry_observer as prior

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / 'build/gba-shoot-entry-capture-qa-20261109/frozen-lua'
CAPTURE = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-a'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def literal(data):
    return "'" + ''.join('\\x%02X' % value for value in data) + "'"


EXERCISE = r'''
local P,Q,A=0x02011710,0x02011828,0x02011940
local function actual(options)
 local m=create(options);m.first,m.second,m.aux=P,Q,A
 m.ram=setmetatable({},{__index=backing});m.frame=64230
 m.load_module();return m
end
local function shoot(m)
 m.put(0x0300231E,11,1);m.put(A+4,6)
 m.put(Q+0xF0,0x085D0000,4);m.put(Q+0xF4,0x085D1000,4)
 m.put(A+0xF0,0x085D029C,4);m.put(A+0xF4,0x085D1100,4)
end
local function state_calls(m,name)
 local n=0;for _,entry in ipairs(m.captures)do if entry.kind=='state'and entry.name==name then n=n+1 end end;return n
end
local base='W:/build/native-entry-independent/'
local m=actual();assert(m.module.pair(true)==P,'actual stage7 kind3/resources accepted')
m.fire(0x08373638);assert(#m.writes==1 and m.writes[1].a==Q+0x64 and m.get(Q+0x64)==1,'real captured owned boss receives oneHPword')
assert(state_calls(m,'stage7-hp1')==0,'checkpoint deferred untilouterframe')
m.frame=m.frame+1;m.module.flush()
assert(state_calls(m,'stage7-hp1')==1 and m.files[base..'stage7-hp1.State'],'outer stage7 checkpoint saved')
assert(m.files[base..'stage7-hp1.txt']:find('core=64231 input_relative=1 stage7_consumed=true',1,true),'checkpoint metadata consumed/inputposition')
m.module.flush();m.fire(0x08373638);assert(#m.writes==1 and state_calls(m,'stage7-hp1')==1,'no repeatedwrite/save')
local x=actual();shoot(x);assert(x.module.pair(true)==P,'stage11 kind6 and allShoot resources accepted')
x.fire(0x08373638);assert(#x.writes==0,'stage11 remains readonly')
local rejected=0
for _,stage in ipairs({0,1,6,8,10,12,255})do
 local n=actual();n.put(0x0300231E,stage,1);assert(not n.module.pair(true),'otherstage rejects bossbinding');rejected=rejected+1
end
for _,stage in ipairs({7,11})do
 for _,item in ipairs({{A,4,stage==7 and 6 or 3},{Q,0xF0,0x085D0000},{Q,0xF4,0x085D1000},
                       {A,0xF0,0x085D029C},{A,0xF4,0x085D1100}})do
  local n=actual();if stage==11 then shoot(n)end
  local bad=item[3]
  if stage==11 and item[2]~=4 then
   bad=({[Q+0xF0]=0x0834DFE0,[Q+0xF4]=0x0834E27C,[A+0xF0]=0x08341C00,[A+0xF4]=0x08341E70})[item[1]+item[2]]
  end
  n.put(item[1]+item[2],bad,item[2]==4 and 2 or 4)
  assert(not n.module.pair(true),'crossedstage kind/resource rejected');n.fire(0x08373638);assert(#n.writes==0)
  rejected=rejected+1
 end
end
for _,mode in ipairs({'false','throw','truthy'})do
 local n=actual({save_mode=mode});n.fire(0x08373638);n.frame=n.frame+1;n.module.flush();n.module.finish()
 assert(n.module.stopped() and n.files[base..'shoot-entry-done.txt']=='failure:checkpoint-save-failed','stage7 savefailure surfaced')
 assert(not n.files[base..'stage7-hp1.txt']and not n.files[base..'healthy-activation.txt'],'failed save hasno successmetadata')
 assert(state_calls(n,'stage7-hp1')==1,'savefailure no retry')
end
for _,change in ipairs({function(n)n.put(P+0x64,0)end,function(n)n.put(Q+0x64,2)end,
 function(n)n.put(0x03002310,9)end,function(n)n.put(0x0300231E,11,1)end,
 function(n)n.put(A+0xF0,0,4)end,function(n)n.put(0x030048A0,0,4)end,
 function(n)n.put(0x03004510,0,4)end})do
 local n=actual();n.fire(0x08373638);change(n);n.frame=n.frame+1;n.module.flush()
 assert(n.module.stopped()and state_calls(n,'stage7-hp1')==0,'invalid outercheckpointguard no saveAPI')
 n.module.finish();assert(n.files[base..'shoot-entry-done.txt']=='failure:stage7-checkpoint-contract')
end
local function healthy(options)
 local n=actual(options);n.fire(0x08373638);n.frame=n.frame+1;n.module.flush()
 n.fire(0x0836E5E4,{R4=P,R5=Q,R8=0,R0=1});n.put(Q+0x64,0);n.fire(0x0836E5E8);n.fire(0x083736B0)
 local owner=0x020106A8;n.put(owner-8,2);n.put(owner+0x54,8)
 n.fire(0x085C8070,{R4=owner,R0=8,R5=P});n.fire(0x085C8B2C,{R4=owner,R0=8})
 shoot(n);n.put(Q+0x64,44);n.put(0x0300450A,4);n.fire(0x085C8D50,{R4=owner});n.put(owner-8,0)
 n.frame=n.frame+1;n.module.flush();n.module.finish();return n
end
local h=healthy();assert(h.files[base..'shoot-entry-done.txt']=='healthy-native-shoot-activation','healthy save success')
assert(state_calls(h,'healthy-activation')==1 and h.files[base..'healthy-activation.txt'],'healthy success committed onlyafterstate')
for _,mode in ipairs({'false','throw','truthy'})do
 local n=healthy({fail_name='healthy-activation',save_mode=mode})
 assert(n.files[base..'shoot-entry-done.txt']=='failure:checkpoint-save-failed','healthy false/throw cannot remainhealthy')
 assert(not n.files[base..'healthy-activation.txt'],'no healthy metadata after API failure')
 assert(state_calls(n,'healthy-activation')==1,'healthy failedsave no retries')
end
assert(rejected==17,'finite stage/resource rejection partitions')
for _,mode in ipairs({'true','false','throw'})do
 local n=actual({fail_name='failure-observed',save_mode=mode~='true'and mode or nil})
 n.module.fail('named-test-failure','retained original reason');n.module.finish()
 assert(n.files[base..'shoot-entry-done.txt']=='failure:named-test-failure','diagnostic checkpoint preserves namedfailure')
 assert(state_calls(n,'failure-observed')==1,'failure checkpoint API invokedonce outsidecallback')
 assert(not n.files[base..'healthy-activation.txt'],'failure diagnostic is nothealthy')
 if mode=='true'then
  assert(n.files[base..'failure-observed.State']and n.files[base..'failure-observed.txt'],'genuinefailure checkpointmetadata')
  assert(n.text():find('failure_checkpoint_saved=true',1,true),'diagnostic save success flag')
 else
  assert(not n.files[base..'failure-observed.txt'],'no diagnostic successmetadata forfailureAPI')
  assert(n.text():find('failure_checkpoint_saved=false',1,true),'diagnostic savefailureflag')
 end
end
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'fresh report required'
    assert sha(Path(prior.__file__).read_bytes()) == '77B47BEC9431511605544E6956AEDA141C2C50FFD0435D4CAF5A020B57CA77E3'
    old = (BEFORE / 'bizhawk_gba_shoot_entry_observer.lua').read_bytes()
    new = (ROOT / 'tools/bizhawk_gba_shoot_entry_observer.lua').read_bytes()
    driver = (ROOT / 'tools/bizhawk_probe_gba_shoot_entry.lua').read_bytes()
    assert sha(old) == 'E620B76A96ED09E6E19DED5E3EE8134D14E62A6022A332D899E08E3493FF76FF'
    assert sha(new) == '7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59'
    assert sha(driver) == 'D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D'
    iw = (CAPTURE / '04-typed-owner-refusal-iwram.bin').read_bytes()
    ew = (CAPTURE / '04-typed-owner-refusal-ewram.bin').read_bytes()
    assert sha(iw) == '17727C9E0A7B542781A4B1732B2A3D76C0A239AB550C6D61388E4A13069CD3AF'
    assert sha(ew) == 'BEEBADB0B5A220CA1F4749DD0A91F6C2D09064CDB89909DAF50511C835E5601A'
    fixture = prior.CHECK.replace('0x02010018,0x02010130,0x02010248', '0x02011710,0x02011828,0x02011940')
    fixture = fixture.replace('m.regs.R15=a', 'm.regs.R15=a+4')
    save_old = "env.savestate={save=function(p)assert(not m.callback,'savestate in CPU callback');m.captures[#m.captures+1]={kind='state',frame=m.frame};m.files[p]='STATE';return true end}"
    save_new = r'''env.savestate={save=function(p)
 assert(not m.callback,'savestate in CPU callback');local name=p:match('/([^/]+)%.State$')
 m.captures[#m.captures+1]={kind='state',name=name,frame=m.frame}
 if o.save_mode and (not o.fail_name or o.fail_name==name)then
  if o.save_mode=='truthy'then return 1 end
  if o.save_mode=='throw'then error('synthetic savestate failure')end;return false
 end
 m.files[p]='STATE';return true
end}'''
    assert fixture.count(save_old) == 1
    fixture = fixture.replace(save_old, save_new)
    backing = 'local backing={}\n'
    for base, data in ((0x03000000, iw), (0x02000000, ew)):
        backing += 'do local s=' + literal(data) + ';for i=1,#s do backing[' + str(base) + '+i-1]=s:byte(i)end end\n'
    def run(module, exercise=EXERCISE):
        host = types.FunctionType(prior.execute.__code__, dict(prior.__dict__, CHECK=fixture),
                                  argdefs=prior.execute.__defaults__)
        host(driver.decode(), module, (BEFORE / 'bizhawk_probe_gba_collision.lua').read_text('utf-8'),
             (BEFORE / 'bizhawk_probe_gba_collision_producer.lua').read_text('utf-8'), backing + exercise)
    run(new.decode())
    old_text, new_text = old.decode(), new.decode()
    def block(text, start, stop):
        a, b = text.index(start), text.index(stop, text.index(start))
        return text[a:b]
    normalized = new_text.replace('local boss_checkpoint=false\n', '')
    normalized = normalized.replace(block(normalized, 'local function checkpoint(name)', 'local function flush()'), '')
    for start, stop in [('local function pair(boss)', 'local function live()'),
                        ('local function flush()', 'local function finish()'),
                        ('local function finish()', 'log("probe_sha256_host_pin=')]:
        normalized = normalized.replace(block(normalized, start, stop), block(old_text, start, stop))
    assert normalized == old_text, 'all bytes outside explicitly changed owner/checkpoint functions unchanged'
    controls = [
        ('=3,0x0834DFE0', '=6,0x0834DFE0', 'retained wrong stage7 kind6'),
        ('=6,0x085D0000', '=3,0x085D0000', 'wrong Shoot kind3'),
        ('read(q+0xF0,4)~=qp1', 'false', 'SECOND P1 pin removed'),
        ('read(q+0xF4,4)~=qp0', 'false', 'SECOND P0 pin removed'),
        ('read(a+0xF0,4)~=ap1', 'false', 'aux P1 pin removed'),
        ('read(a+0xF4,4)~=ap0', 'false', 'aux P0 pin removed'),
        ('if not ok or saved~=true then', 'if false then', 'false/throw save accepted'),
        ('if not ok or saved~=true then', 'if not ok or not saved then', 'truthy nonboolean save accepted'),
        ('not boss_checkpoint and not outcome', 'true and not outcome', 'boss checkpoint retry'),
        ('if outcome and outcome:match("^failure:") then', 'if false then', 'failure checkpoint omitted'),
    ]
    rejected = []
    for before, after, name in controls:
        assert new_text.count(before) == 1, 'unique semantic control ' + name
        try:
            run(new_text.replace(before, after))
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('accepted semantic mutant ' + name)
    report = dict(status='NATIVE_ENTRY_OWNER_CHECKPOINT_DELTA_PASS', old_module_sha256=sha(old),
                  module_sha256=sha(new), driver_sha256=sha(driver),
                  verifier_sha256=sha(Path(__file__).read_bytes()),
                  captured_fixture_sha256=dict(iwram=sha(iw), ewram=sha(ew)),
                  actual_fixture_frame=64230, fixture_p1_hp=8, fixture_boss_hp=37,
                  exact_outside_changed_functions_equal=True,
                  changed_functions=['pair', 'flush', 'finish', 'new checkpoint helper and one local flag'],
                  actual_lua_checks=['captured native stage7 kind3+four resources accepts oneHPwrite',
                                     'postwrite checkpoint once at first outer frame with input/consumed metadata',
                                     'stage11 kind6+four Shoot resources accepts ownership but noHPwrite',
                                     '17 stage/crossed-kind/crossed-resource refusals',
                                     '7 invalid outer checkpoint guard refusals before any stage7 save API',
                                     'stage7 and healthy API false/throw/truthy nonboolean refuse success',
                                     'failure-only diagnostic checkpoint true/false/throw preserves original failure'],
                  semantic_mutations_rejected=rejected, emulator_launched=False,
                  existing_old_suites_rerun=False, guest_memory_written=False,
                  limits=['actual Lua with captured RAM is not a new running GBA core',
                          'checkpoint fixture tests API semantics; actual ZIP/native checkpoint remains runtime QA'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(args.output.read_bytes()))


if __name__ == '__main__':
    main()
