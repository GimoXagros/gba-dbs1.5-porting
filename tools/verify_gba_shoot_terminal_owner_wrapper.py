"""Independent reciprocal-owner wrapper/host delta QA; synthetic Lua54, no emulator."""
import argparse
import ast
import json
from pathlib import Path
import sys
import types

import verify_gba_shoot_terminal_palette_wrapper as palette

ROOT = Path(__file__).resolve().parents[1]
OLD = palette.OLD
NEW = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
WRAPPER = '1F9E5F52D486A8C9646988B9164CA9D6DD65C4F475D0A944DF540B84E051BECB'
HOST = 'B1595A5B1DF397FF01DF83776904BCE804E74ECBB0F9561473938641B481CC0E'
PINS = 'C98E217BC26FACC838B140D43549A034F1F0684A174FCA91082D4AACCE69F54C'
BEFORE = 'if read(Q+0x28,4)~=AUX or read(AUX+0x18,4)~=Q then return "native-guard-aux18-not-upper"end'
AFTER = BEFORE.replace('AUX+0x18', 'AUX+0x28').replace('aux18-not-upper', 'aux28-not-upper')
sha = palette.sha


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def composed(original):
    assert original.count(OLD.encode()) == 1 and original.count(BEFORE.encode()) == 1
    return original.replace(OLD.encode(), NEW.encode()).replace(BEFORE.encode(), AFTER.encode())


def execute(wrapper, original, body):
    code = 'hard_source=' + palette.quoted(original) + '\ncollect_source=' + palette.quoted(composed(original)) + '\n' + body
    fn = types.FunctionType(palette.lua_host.lua_check.__code__, dict(palette.lua_host.__dict__, CHECK=code), argdefs=palette.lua_host.lua_check.__defaults__)
    fn(wrapper, '', '')


def actual_rebind(wrapper, original):
    body = replace_once(palette.prior.harness(), "probe_sha256='" + OLD + "'", "probe_sha256='" + NEW + "'")
    body = replace_once(body, ' env.io={open=function(path,access)', ' reference["W:/tools/bizhawk_probe_gba_shoot_terminal.lua"]=hard_source\n env.io={open=function(path,access)')
    body = replace_once(body, "  if mode~='actual-aux-FIRST'then m.put(AUX+0x18,Q,4)end", """  assert(m.get(AUX+0x18,4)==P and m.get(AUX+0x28,4)==Q and m.get(Q+0x28,4)==AUX,'actualFIRSTopponentSECONDownerlinks')
  if mode=='bad-aux-owner'then m.put(AUX+0x28,P,4)end
  if mode=='bad-upper-aux'then m.put(Q+0x28,P,4)end""")
    body = body.replace("mode=='actual-aux-FIRST'", "(mode=='bad-aux-owner'or mode=='bad-upper-aux')")
    assert body.count('native-guard-aux18-not-upper') == 2
    body = body.replace('native-guard-aux18-not-upper', 'native-guard-aux28-not-upper')
    body = replace_once(body, "local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))", """local native_load=load;local rebinds=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and name=='@reviewed-terminal-reciprocal-owner-repair'and kind=='t'and scope==env,'entireobserveronlyROMandownerpredicatechange')
  rebinds=rebinds+1;return native_load(text,name,kind,scope)
 end
 local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))
 assert(rebinds==1,'oneactualcomposedobserverload')""")
    body = replace_once(body, ' return m\nend', """ local trace=assert(m.files[out..'/terminal-trace.txt'])
 if mode=='success'then
  assert(not trace:find('kind=guard-refusal',1,true),'actualownerlinksaccepted')
  assert(trace:find('kind=queue-substitution',1,true)and trace:find('kind=irq-match',1,true),'affectedguardandIRQroute')
 else
  assert(trace:find('native-guard-aux28-not-upper',1,true),'wrongownerrefusal')
  assert(not trace:find('kind=queue-substitution',1,true),'wrongownerneverselected')
 end
 return m
end""")
    execute(wrapper, original, body + "\ntest('success')\ntest('bad-aux-owner')\ntest('bad-upper-aux')\n")


def bindings(wrapper, original):
    body = r'''
for _,mode in ipairs({'wrong-token','missing-ROM','duplicate-ROM','missing-owner','duplicate-owner','missing-file','missing-read'})do
 local reads,loads,executes=0,0,0;local payload=hard_source
 if mode=='missing-ROM'then payload=collect_source end
 if mode=='duplicate-ROM'then payload=payload..'\n-- OLD'end
 if mode=='missing-owner'then local a,b=assert(payload:find(BEFORE,1,true));payload=payload:sub(1,a-1)..payload:sub(b+1)end
 if mode=='duplicate-owner'then payload=payload..'\n-- '..BEFORE end
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
'''.replace('OLD', OLD).replace('NEW', NEW)
    execute(wrapper, original, 'BEFORE=' + palette.quoted(BEFORE.encode()) + '\n' + body)


def check_lua():
    assert sha(Path(palette.__file__).read_bytes()) == 'B6D3AB33F5ED9F5B2570ACCE7BFCC594AE4581C1D846257552661B3F93994894'
    assert sha(Path(palette.prior.__file__).read_bytes()) == '85CE28F03298A43A6335F6BDE05A9935D2826D45C22A3967F707DA77D830C728'
    prior_report = (ROOT / 'build/gba-shoot-terminal-palette-wrapper-qa-20261109/final-report.json').read_bytes()
    assert sha(prior_report) == 'EE0CEB4C1BD8D781E66117D97C491FEDB63F10E84515287E4DA696D73C015AF9'
    actual = (ROOT / 'build/gba-shoot-terminal-palette-capture-qa-20261109/report.json').read_bytes()
    assert sha(actual) == '91E07B23E25ABC5510B77B7D1F3C8D6930D51807A2D91D7A870E39E2B6018096'
    actual_data = json.loads(actual)
    owner = next(v for v in actual_data.values() if isinstance(v, dict) and v.get('reason') == 'native-guard-aux18-not-upper')
    assert owner['core'] == 69932 and owner['aux18'] == '02011710' and owner['aux28'] == '02011828'
    original = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()
    wrapper = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal_owner.lua').read_bytes()
    assert sha(original) == palette.prior.LUA and sha(wrapper) == WRAPPER
    text = wrapper.decode(); actual_rebind(text, original); bindings(text, original)
    rejected = []
    for label, old, new, check in (
        ('wrong-ROM', NEW, OLD, actual_rebind),
        ('duplicate-ROM-accepted', 'assert(a and not source:find(old,b+1,true),', 'assert(a,', bindings),
        ('duplicate-owner-accepted', 'assert(x and not source:find(before,y+1,true),', 'assert(x,', bindings),
        ('ROM-suffix-dropped', '..target..source:sub(b+1)', '..target', actual_rebind),
        ('owner-suffix-dropped', '..after..source:sub(y+1)', '..after', actual_rebind),
        ('wrong-owner-field', "local after='" + AFTER + "'", "local after='" + BEFORE + "'", actual_rebind),
    ):
        changed = replace_once(text, old, new)
        try:
            check(changed, original)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('control survived:' + label)
    assert sha((ROOT / 'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()) == palette.prior.LUA
    return dict(wrapper_sha256=WRAPPER, original_sha256=palette.prior.LUA, effective_sha256=sha(composed(original)), exact_entire_body_ROM_and_stationary_owner_only=True, actual_Lua54_routes=3, positive_fixture_aux18='FIRST02011710', positive_fixture_aux28='SECOND02011828', wrong_owner_routes=['aux28-FIRST', 'upper28-FIRST'], binding_refusals=7, semantic_controls_rejected=rejected, actual_prior_guard_core=owner['core'], actual_prior_capture_report_sha256=sha(actual), original_LF=original.count(b'\n'), original_CRLF=original.count(b'\r\n'), old43_case_suite_rerun=False)


def host_preflight():
    path = ROOT / 'build/run_gba_shoot_terminal_owner_20261109.py'
    blob = path.read_bytes(); assert sha(blob) == HOST
    assert sha((ROOT / 'build/gba-shoot-terminal-owner-pins-20261109.json').read_bytes()) == PINS
    parent = (ROOT / 'build/run_gba_shoot_terminal_palette_20261109.py').read_bytes()
    assert sha(parent) == palette.HOST
    expected = parent.decode()
    for old, new in (
        ('source-bound palette-call repair.', 'source-bound palette and reciprocal-owner repairs.'),
        ('bizhawk-gba-shoot-terminal-palette-20261109-[a-z]', 'bizhawk-gba-shoot-terminal-owner-20261109-[a-z]'),
        ('build/gba-shoot-terminal-palette-pins-20261109.json', 'build/gba-shoot-terminal-owner-pins-20261109.json'),
        ('build/shoot-palette-project-calls-20261109/component.gba', 'build/shoot-terminal-owner-link-20261109/component.gba'),
        (palette.NEW, NEW),
    ):
        expected = replace_once(expected, old, new)
    assert expected.count('bizhawk_probe_gba_shoot_terminal_palette.lua') == 2
    expected = expected.replace('bizhawk_probe_gba_shoot_terminal_palette.lua', 'bizhawk_probe_gba_shoot_terminal_owner.lua')
    anchor = 'assert bytes(expected) == rom_data and source_rom[0xA0:0xB0] == rom_data[0xA0:0xB0]'
    block = "assert sha(bytes(expected)) == '" + palette.NEW + "'\nassert struct.unpack_from('<I', expected, 0x6FFC00)[0] == 0xE5960018\nstruct.pack_into('<I', expected, 0x6FFC00, 0xE5960028)\n"
    expected = replace_once(expected, anchor, block + anchor)
    code = blob.decode(); assert expected == code, 'onlyreviewedownerhostdelta'
    prefix = code.split("\nout = root / 'build' / name", 1); assert len(prefix) == 2
    tree = ast.parse(prefix[0]); compile(code, str(path), 'exec')
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
            assert name not in {'mkdir', 'write_text', 'write_bytes', 'copyfile', 'PrivateDesktopProcess'}
    argv = sys.argv[:]
    try:
        sys.argv = [str(path), 'bizhawk-gba-shoot-terminal-owner-20261109-z']
        env = {'__file__': str(path), '__name__': '__readonly__'}
        exec(compile(tree, str(path) + ':readonlyprefix', 'exec'), env)
    finally:
        sys.argv = argv
    return dict(host_sha256=HOST, pins_sha256=PINS, parent_host_sha256=palette.HOST, exact_parent_delta_only=True, readonly_prefix_executed=True, checkpoint_frame=env['parsed']['frame'], source_Core_sha256=sha(env['source_core']), component_sha256=sha(env['rom_data']), added_ROM_word_offset='006FFC00', before='E5960018', after='E5960028', same_healthy_checkpoint_input_approval_onewrite_ledger_and_180sec_private_bound=True, strict_whole_Core_qualification_unchanged=True, paths_created=False, emulator_launched=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = dict(status='TERMINAL_OWNER_WRAPPER_HOST_DELTA_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), Lua=check_lua(), host=host_preflight(), actual_terminal_completion_claim=False, synthetic_acceptance_not_actual_IRQ_or_cleanup_proof=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print('PASS actualLua54 real-owner-link fixture/negativeowners/exactcomposition/read-onlyhostdelta')


if __name__ == '__main__':
    main()
