"""Independent prospective mapping/display consumption observer and host delta QA."""
import argparse
import ast
import json
from pathlib import Path
import sys
import types

import verify_gba_shoot_terminal_owner_wrapper as owner

ROOT = Path(__file__).resolve().parents[1]
ROM = '280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
WRAPPER = '5CEA6EB9B5013FCAF3433090A863035FF1D2E8BD726A2A7032DFF64DAC52DE0F'
HOST = 'C34160EBD57DE3E26BF7BCFA2FDEE85631CC674FE5F74973B8A4819D8F56A8DC'
PINS = '4A44DCDEFD574207E1F950EDDB0CF68E84C075864F22EF4D2710A8B9A5D065CE'
MAP_BEFORE, MAP_AFTER = 'w(0x0400000A)&0xDFCC~=0x1E00', 'w(0x0400000A)&0xCC~=0'
HOOK_BEFORE, HOOK_AFTER = 'hook(0x086FF6E8,"guarded-display"', 'hook(0x086FF75C,"guarded-display"'
sha, replace_once = owner.sha, owner.replace_once
SPANS = ((0x6FF6E8, '449ffbeb', '0c0000eb'),
         (0x6FF720, 'ff'*72, '0103a0e3b010d0e1070011e3f0ffff1aba10d0e1cc0011e3edffff1a1c009fe5001090e5000051e3e9ffff1a501090e5000051e3e6ffff1a04009fe5279ffbea5423000310fe6f08'),
         (0x6FFDE8, 'ccdf0000', 'cc000000'), (0x6FFDEC, '001e0000', '00000000'))


def composed(original):
    text = original.decode()
    for before, after in ((owner.OLD, ROM), (owner.BEFORE, owner.AFTER), (MAP_BEFORE, MAP_AFTER), (HOOK_BEFORE, HOOK_AFTER)):
        text = replace_once(text, before, after)
    return text.encode()


def execute(source, original, body):
    code = 'hard_source=' + owner.palette.quoted(original) + '\ncollect_source=' + owner.palette.quoted(composed(original)) + '\n' + body
    helper = owner.palette.lua_host
    fn = types.FunctionType(helper.lua_check.__code__, dict(helper.__dict__, CHECK=code), argdefs=helper.lua_check.__defaults__)
    fn(source, '', '')


def actual_routes(source, original):
    body = replace_once(owner.palette.prior.harness(), "probe_sha256='" + owner.OLD + "'", "probe_sha256='" + ROM + "'")
    body = replace_once(body, ' env.io={open=function(path,access)', ' reference["W:/tools/bizhawk_probe_gba_shoot_terminal.lua"]=hard_source\n env.io={open=function(path,access)')
    body = replace_once(body, 'm.put(0x0400000A,0x1E00)', 'm.put(0x0400000A,0x1F03)')
    body = replace_once(body, "  if mode~='actual-aux-FIRST'then m.put(AUX+0x18,Q,4)end", """  assert(m.get(AUX+0x18,4)==P and m.get(AUX+0x28,4)==Q,'actualopponentandownerlinks')
  if mode=='bad-lowbyte'then m.put(0x0400000A,0x1F07)end
  if mode:sub(1,9)=='velocity-'then m.put(tonumber(mode:sub(10),16),1)end""")
    body = body.replace("mode=='actual-aux-FIRST'", "(mode=='bad-lowbyte'or mode:sub(1,9)=='velocity-')")
    body = replace_once(body, "m.files[out..'/terminal-trace.txt']:find('native-guard-aux18-not-upper',1,true)", "m.files[out..'/terminal-trace.txt']:find('kind=guard-refusal '..(mode=='bad-lowbyte'and'hardware-BG-mapping'or'BG-velocity')..' ',1,true)")
    body = replace_once(body, 'm.fire(0x086FF6E8,{R0=0x086FFE10});m.put(0x030012E0,0x086FFE10,4)', """if mode=='consumption-refused'then return end
   m.fire(0x086FF75C,{R0=0x086FFE10,R14=0x086FF6EC});m.put(0x030012E0,0x086FFE10,4)""")
    body = replace_once(body, " local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))", """ local native_load=load;local rebinds=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and name=='@reviewed-terminal-display-epoch-repair'and kind=='t'and scope==env,'entire964Bonlyfourreviewedchanges')
  rebinds=rebinds+1;return native_load(text,name,kind,scope)
 end
 local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))
 assert(rebinds==1,'onecomposedobserverload')""")
    body = replace_once(body, ' return m\nend', """ local trace=assert(m.files[out..'/terminal-trace.txt'])
 assert(m.hooks[0x086FF75C]and not m.hooks[0x086FF6E8],'onlyactualstubsuccessPCobserved')
 if mode=='success'then
  assert(trace:find('kind=guarded-display',1,true)and trace:find('kind=irq-match',1,true),'actualsuccesshookrequired')
 elseif mode=='consumption-refused'then
  assert(trace:find('kind=queue-substitution',1,true),'earlyselectionoccurred')
  assert(not trace:find('kind=guarded-display',1,true)and not trace:find('kind=irq-entry',1,true),'earlyselectionnotdisplayorIRQ')
 else assert(not trace:find('kind=queue-substitution',1,true),'allfourvelocitiesandlowbytefailclosed')end
 return m
end""")
    cases = ('success', 'bad-lowbyte', 'velocity-03002354', 'velocity-03002356', 'velocity-030023A4', 'velocity-030023A6', 'consumption-refused')
    execute(source, original, body + '\n' + '\n'.join("test('" + mode + "')" for mode in cases))


def bindings(source, original):
    needles = (owner.OLD, owner.BEFORE, MAP_BEFORE, HOOK_BEFORE)
    body = 'local needles={' + ','.join(owner.palette.quoted(s.encode()) for s in needles) + '}\n'
    body += r'''
local modes={'wrong-token','missing-file','missing-read'}
for i=1,#needles do modes[#modes+1]='missing-'..i;modes[#modes+1]='duplicate-'..i end
for _,mode in ipairs(modes)do
 local payload=hard_source;local reads,loads=0,0
 local kind,index=mode:match('^(%a+)%-(%d+)$')
 if index then local needle=needles[tonumber(index)];local a,b=assert(payload:find(needle,1,true))
  if kind=='missing'then payload=payload:sub(1,a-1)..payload:sub(b+1)else payload=payload..'\n-- '..needle end
 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function()return mode=='wrong-token'and'wrong'or'ROM'end}
 env.io={open=function()
  reads=reads+1;if mode=='missing-file'then return nil end
  return{read=function()return mode~='missing-read'and payload or nil end,close=function()end}
 end}
 env.load=function()loads=loads+1;return function()end end
 assert(not pcall(assert(load(wrapper_source,'@binding-test','t',env))),'invalidbindingrefused:'..mode)
 assert(loads==0,'invalidbindingneverloads');if mode=='wrong-token'then assert(reads==0)end
end
'''.replace("'ROM'", "'" + ROM + "'")
    execute(source, original, body)


def check_lua():
    assert sha(Path(owner.__file__).read_bytes()) == '0D39EBF680CABA0D88B73933B64673C8EB07A91DBDF7F0C3C2FE8021CF54AF7F'
    original = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()
    blob = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal_display_epoch.lua').read_bytes()
    assert sha(original) == owner.palette.prior.LUA and sha(blob) == WRAPPER
    source = blob.decode(); actual_routes(source, original); bindings(source, original)
    rejected = []
    for label, old, new, check in (
        ('wrong-ROM', ROM, owner.NEW, actual_routes),
        ('duplicate-ROM-accepted', 'assert(a and not source:find(old,b+1,true),', 'assert(a,', bindings),
        ('duplicate-owner-accepted', 'assert(x and not source:find(before,y+1,true),', 'assert(x,', bindings),
        ('duplicate-display-site-accepted', 'assert(i and not source:find(change[1],j+1,true),', 'assert(i,', bindings),
        ('wrong-prospective-mask', "'" + MAP_AFTER + "'", "'" + MAP_BEFORE + "'", actual_routes),
        ('premature-display-hook', "'" + HOOK_AFTER + "'", "'" + HOOK_BEFORE + "'", actual_routes),
        ('observer-suffix-dropped', '..target..source:sub(b+1)', '..target', actual_routes),
    ):
        try:
            check(replace_once(source, old, new), original)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('control survived:' + label)
    return dict(wrapper_sha256=WRAPPER, base_sha256=sha(original), effective_sha256=sha(composed(original)), exact_entire964B_only_ROM_aux28_prospective_mask_and_success_hook=True, affected_actual_Lua54_routes=7, positive_prior_high_BG1CNT='1F03', low_byte_violation_refuses=True, each_of_four_velocities_refuses=True, real_aux18_FIRST_aux28_SECOND_retained=True, early_queue_selection_without_success_hook_cannot_complete=True, actual_success_hook='086FF75C', synthetic_success_R0='086FFE10', synthetic_success_LR='086FF6EC', binding_refusals=11, semantic_controls_rejected=rejected, original_eight_IRQ_compare_match_store_final_logic_unchanged=True, synthetic_IRQ_not_actual_first_line_timing_proof=True, callback_bulk_or_new_guest_writes=False, old43_case_suite_rerun=False)


def host_preflight():
    path = ROOT / 'build/run_gba_shoot_terminal_display_epoch_20261110.py'
    blob = path.read_bytes(); assert sha(blob) == HOST
    assert sha((ROOT / 'build/gba-shoot-terminal-display-epoch-pins-20261110.json').read_bytes()) == PINS
    parent = (ROOT / 'build/run_gba_shoot_terminal_owner_20261109.py').read_bytes(); assert sha(parent) == owner.HOST
    expected = parent.decode()
    for old, new in (
        ('Repeat the frozen terminal test with the source-bound palette and reciprocal-owner repairs.', 'Repeat the frozen terminal test with the reviewed display-epoch repair.'),
        ('bizhawk-gba-shoot-terminal-owner-20261109-[a-z]', 'bizhawk-gba-shoot-terminal-display-epoch-20261110-[a-z]'),
        ('build/gba-shoot-terminal-owner-pins-20261109.json', 'build/gba-shoot-terminal-display-epoch-pins-20261110.json'),
        ('build/shoot-terminal-owner-link-20261109/component.gba', 'build/shoot-terminal-display-epoch-20261110/component.gba'),
        ("rom_sha = '" + owner.NEW + "'", "rom_sha = '" + ROM + "'"),
    ):
        expected = replace_once(expected, old, new)
    assert expected.count('bizhawk_probe_gba_shoot_terminal_owner.lua') == 2
    expected = expected.replace('bizhawk_probe_gba_shoot_terminal_owner.lua', 'bizhawk_probe_gba_shoot_terminal_display_epoch.lua')
    anchor = 'assert bytes(expected) == rom_data and source_rom[0xA0:0xB0] == rom_data[0xA0:0xB0]'
    block = "assert sha(bytes(expected)) == '" + owner.NEW + "'\nfor at, before, after in " + repr(SPANS) + ":\n    assert expected[at:at+len(bytes.fromhex(before))] == bytes.fromhex(before)\n    expected[at:at+len(bytes.fromhex(after))] = bytes.fromhex(after)\n"
    expected = replace_once(expected, anchor, block + anchor)
    code = blob.decode(); assert expected == code, 'onlyreviewedhostpathsROMandfourfrozenspans'
    prefix = code.split("\nout = root / 'build' / name", 1); assert len(prefix) == 2
    tree = ast.parse(prefix[0]); compile(code, str(path), 'exec')
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
            assert name not in {'mkdir', 'write_text', 'write_bytes', 'copyfile', 'PrivateDesktopProcess'}
    argv = sys.argv[:]
    try:
        sys.argv = [str(path), 'bizhawk-gba-shoot-terminal-display-epoch-20261110-z']
        env = {'__file__': str(path), '__name__': '__readonly__'}
        exec(compile(tree, str(path)+':readonlyprefix', 'exec'), env)
    finally:
        sys.argv = argv
    return dict(host_sha256=HOST, pins_sha256=PINS, exact_B159_parent_delta_only=True, readonly_prefix_executed=True, checkpoint_frame=env['parsed']['frame'], source_Core_sha256=sha(env['source_core']), component_sha256=sha(env['rom_data']), four_expected_spans=[dict(offset=f'{a:08X}', bytes=len(bytes.fromhex(b))) for a, b, _ in SPANS], declared_bytes=84, same_input_approval_late_oneword_ledger_180sec_private_bound_and_Core_qualification=True, paths_created=False, emulator_launched=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = dict(status='TERMINAL_DISPLAY_EPOCH_WRAPPER_HOST_DELTA_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), Lua=check_lua(), host=host_preflight(), actual_IRQ_first_line_timing_or_terminal_completion_claim=False)
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('PASS actualLua54 four-delta composition/7affectedroutes/refusals/earlyselection/read-onlyhost84Bdelta')


if __name__ == '__main__':
    main()
