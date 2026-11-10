"""Independent bounded scalar BG telemetry wrapper/host delta QA; no emulator."""
import argparse
import ast
import json
from pathlib import Path
import re
import sys
import types

import verify_gba_shoot_terminal_owner_wrapper as owner

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = '8BC67A68FCF9681D5CF7F34E12F501611A14C9DB2F2D50C2760B10A9775F0439'
HOST = 'CD9EA4A6F31107660D2C229EC826542D1DCA2177BB4DEFEE94579ADDCEA5ECFF'
PINS = '3DFC073361BD9FA69BBB3C60FB031EE2D0F8A5644FA5E787D32AD6AC56EB744D'
sha, replace_once = owner.sha, owner.replace_once


def lua(code, source=''):
    helper = owner.palette.lua_host
    fn = types.FunctionType(helper.lua_check.__code__, dict(helper.__dict__, CHECK=code), argdefs=helper.lua_check.__defaults__)
    fn(source, '', '')


def extract(source):
    parts = re.findall(r'local telemetry=\[=\[(.*?)\]=\]', source, re.S)
    assert len(parts) == 1 and parts[0].startswith('\n')
    return parts[0][1:]


def actual_routes(source, original):
    telemetry = extract(source)
    expected = replace_once(owner.composed(original).decode(), 'local function install()\n', 'local function install()\n' + telemetry)
    body = owner.palette.prior.harness()
    body = replace_once(body, "probe_sha256='" + owner.OLD + "'", "probe_sha256='" + owner.NEW + "'")
    body = replace_once(body, ' env.io={open=function(path,access)', ' reference["W:/tools/bizhawk_probe_gba_shoot_terminal.lua"]=hard_source\n env.io={open=function(path,access)')
    body = replace_once(body, "assert(m.loads==1 and m.frame==68927 and not m.hooks[address]);m.hooks[address]=fn", "assert(m.loads==1 and m.frame==68927);m.hooks[address]=m.hooks[address]or {};table.insert(m.hooks[address],fn)")
    body = replace_once(body, 'local ok,err=pcall(assert(m.hooks[address]),address,0,0)', 'local ok,err=pcall(function()for _,fn in ipairs(assert(m.hooks[address]))do fn(address,0,0)end end)')
    body = replace_once(body, "  if mode~='actual-aux-FIRST'then m.put(AUX+0x18,Q,4)end", """  assert(m.get(AUX+0x18,4)==P and m.get(AUX+0x28,4)==Q,'realauxlinks')
  if mode=='BG-velocity'then m.put(0x03002356,1)end
  if mode=='hardware-BG-mapping'then m.put(0x0400000A,0x1F03)end""")
    body = body.replace("mode=='actual-aux-FIRST'", "(mode=='BG-velocity'or mode=='hardware-BG-mapping')")
    body = replace_once(body, "m.files[out..'/terminal-trace.txt']:find('native-guard-aux18-not-upper',1,true)", "m.files[out..'/terminal-trace.txt']:find('kind=guard-refusal '..mode..' ',1,true)")
    body = replace_once(body, " local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))", """ local native_load=load;local rebinds=0
 env.load=function(text,name,kind,scope)
  assert(text==collect_source and name=='@reviewed-terminal-BG-epoch-telemetry'and kind=='t'and scope==env,'exactownerbodyplusonlytelemetryinsertion')
  rebinds=rebinds+1;return native_load(text,name,kind,scope)
 end
 local ok,err=pcall(assert(load(wrapper_source,'@terminal-under-test','t',env)))
 assert(rebinds==1,'onecomposedobserverload')""")
    body = replace_once(body, ' return m\nend', """ local trace=assert(m.files[out..'/terminal-trace.txt'])
 assert(trace:find('kind=bg-epoch point=guard ',1,true),'telemetrycallbackexecuted')
 assert(not trace:find('native-guard-aux18-not-upper',1,true),'oldownerrefusalabsent')
 if mode=='success'then assert(trace:find('kind=queue-substitution',1,true),'originalguardandIRQretained')
 else assert(not trace:find('kind=queue-substitution',1,true),'actualrefusalretained')end
 return m
end""")
    code = 'hard_source=' + owner.palette.quoted(original) + '\ncollect_source=' + owner.palette.quoted(expected.encode()) + '\n' + body
    lua(code + "\ntest('success')\ntest('BG-velocity')\ntest('hardware-BG-mapping')\n", source)
    return expected.encode()


SCALAR_BEFORE = r'''
local scene=nil;local mode,stage,flags=7,11,0x400;local frame=100
local hooks,rows={},{}
local values={[0x03002354]=0x11,[0x03002356]=0x22,[0x030023A4]=0x33,[0x030023A6]=0x44,[0x030012CE]=0x12,[0x04000008]=0x5A04,[0x0400000A]=0x1E03}
local function w(a)if a==0x03002310 then return mode elseif a==0x0300450A then return flags end;return assert(values[a],'unexpectedhalfread')end
local function b(a)if a==0x0300231E then return stage end;return assert(values[a],'unexpectedbyteread')end
local function read(a,n)assert(n==1);if a==0x08001032 then return 0x1F elseif a==0x08001031 then return 0x1E end;error('unexpectedROMread')end
local function state()return 'state-scalar'end
local function irq_state()return 'IRQ-scalar'end
local function log(kind,text,r)assert(kind=='bg-epoch');rows[#rows+1]={text=text,R0=r.R0}end
local function hook(a,label,fn)assert(not hooks[a]);hooks[a]=fn end
local emu={framecount=function()return frame end}
'''
SCALAR_AFTER = r'''
local points={0x085E716C,0x085E7170,0x086FF9C0,0x086FF698,0x080C97B8,0x080D0C18,0x080D0C1C,0x080D0C20,0x08000FEC,0x08001010,0x08001014}
local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==11)
local r={R0=0x12};local function fire(a)assert(hooks[a])(r)end
fire(points[1]);assert(#rows==0,'noscenenobegin');scene=1
mode=8;fire(points[1]);assert(#rows==0,'wrongmodenobegin');mode=7
stage=10;fire(points[1]);assert(#rows==0,'wrongstagenobegin');stage=11
flags=0;fire(points[1]);assert(#rows==0,'nontransitionnobegin');flags=0x400
r.R0=0x13;fire(points[9]);assert(#rows==0,'irrelevantmapnobegin')
for _,f in ipairs({200,201})do
 frame=f;r.R0=f==200 and 0x12 or 0x21
 for _,a in ipairs(points)do fire(a);fire(a)end
 assert(#rows==(f-199)*11,'onepersitepercore')
end
frame=202;for _,a in ipairs(points)do fire(a)end
frame=199;for _,a in ipairs(points)do fire(a)end
assert(#rows==22,'strict22logtwocorebound')
local maps=0
for i,row in ipairs(rows)do
 assert(row.text:find('first_core=200',1,true),'qualificationdoesnotstartwindow')
 assert(row.text:find('velocities=0011,0022,0033,0044 map_selector=12 BG0CNT=5A04',1,true),'allscalarfields')
 assert(row.text:find('state-scalar IRQ-scalar',1,true),'stateandIRQscalarsretained')
 if row.text:find('point=map-',1,true)then
  maps=maps+1;assert(row.text:find('planned_BG1CNT='..(i<=11 and '1F03' or '1E03'),1,true),'realmap12and21')
 else assert(row.text:find('planned_BG1CNT=none',1,true))end
end
assert(maps==6,'allthreemapcallsbothframes')
'''


def scalar_contract(telemetry):
    assert not re.search(r'\b(?:memory|mainmemory|savestate|joypad|client)\s*[.:]|\bwrite\s*\(|read_bytes|setregister', telemetry)
    lua(SCALAR_BEFORE + telemetry + SCALAR_AFTER)


def install_bindings(source, original):
    body = r'''
for _,kind in ipairs({'missing','duplicate'})do
 local payload=hard_source;local anchor='local function install()\n'
 if kind=='missing'then local a,b=assert(payload:find(anchor,1,true));payload=payload:sub(1,a-1)..payload:sub(b+1)
 else payload=payload..'\n-- '..anchor end
 local loads=0;local env=setmetatable({},{__index=_G})
 env.userdata={get=function()return 'ROM'end}
 env.io={open=function()return{read=function()return payload end,close=function()end}end}
 env.load=function()loads=loads+1;return function()end end
 assert(not pcall(assert(load(wrapper_source,'@installation-binding-test','t',env))),'badinstallationrefused')
 assert(loads==0,'badinstallationneverexecutes')
end
'''.replace('ROM', owner.NEW)
    owner.execute(source, original, body)


def check_lua():
    assert sha(Path(owner.__file__).read_bytes()) == '0D39EBF680CABA0D88B73933B64673C8EB07A91DBDF7F0C3C2FE8021CF54AF7F'
    original = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal.lua').read_bytes()
    blob = (ROOT / 'tools/bizhawk_probe_gba_shoot_terminal_bg_epoch.lua').read_bytes()
    assert sha(original) == owner.palette.prior.LUA and sha(blob) == WRAPPER
    source = blob.decode(); effective = actual_routes(source, original); telemetry = extract(source)
    scalar_contract(telemetry); owner.bindings(source, original); install_bindings(source, original)
    rom = (ROOT / 'build/shoot-terminal-owner-link-20261109/component.gba').read_bytes()
    assert sha(rom) == owner.NEW and rom[0x1031:0x1033] == bytes([0x1E, 0x1F])
    rejected = []
    for label, old, new in (
        ('third-frame-accepted', 'core>bg_epoch_first+1', 'core>bg_epoch_first+2'),
        ('dedup-removed', 'if bg_epoch_seen[key]then return end', 'if false then return end'),
        ('transition-gate-removed', 'w(0x0300450A)&0x400==0', 'false'),
        ('map-filter-removed', 'r.R0==0x12 or r.R0==0x21', 'true'),
        ('wrong-map-table', '0x08001030+(r.R0&7)', '0x08001030+1'),
    ):
        try:
            scalar_contract(replace_once(telemetry, old, new))
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('control survived:' + label)
    try:
        install_bindings(replace_once(source, 'assert(i and not source:find(anchor,j+1,true),', 'assert(i,'), original)
    except ValueError:
        rejected.append('duplicate-install-accepted')
    else:
        raise AssertionError('installation control survived')
    return dict(wrapper_sha256=WRAPPER, base_sha256=sha(original), effective_sha256=sha(effective), telemetry_sha256=sha(telemetry.encode()), entire_owner_observer_plus_single_install_insertion=True, affected_actual_Lua54_full_routes=3, same_real_aux18_FIRST_aux28_SECOND=True, existing_BG_velocity_and_hardware_refusals_retained=True, scalar_hook_sites=11, maximum_records=22, window_cores=2, qualification_and_per_site_core_dedup_checked=True, map12_planned_BG1CNT='1F03', map21_planned_BG1CNT='1E03', actual_ROM_map_table_bound=True, binding_refusals=9, semantic_controls_rejected=rejected, added_guest_writes=False, callback_bulk_or_state_capture=False, old_full_suite_rerun=False)


def host_preflight():
    path = ROOT / 'build/run_gba_shoot_terminal_bg_epoch_20261110.py'
    blob = path.read_bytes(); assert sha(blob) == HOST
    assert sha((ROOT / 'build/gba-shoot-terminal-bg-epoch-pins-20261110.json').read_bytes()) == PINS
    parent = (ROOT / 'build/run_gba_shoot_terminal_owner_20261109.py').read_bytes()
    assert sha(parent) == owner.HOST
    expected = parent.decode()
    for old, new in (
        ('Repeat the frozen terminal test with the source-bound palette and reciprocal-owner repairs.', 'Observe two native transition frames with read-only scalar background telemetry.'),
        ('bizhawk-gba-shoot-terminal-owner-20261109-[a-z]', 'bizhawk-gba-shoot-terminal-bg-epoch-20261110-[a-z]'),
        ('build/gba-shoot-terminal-owner-pins-20261109.json', 'build/gba-shoot-terminal-bg-epoch-pins-20261110.json'),
    ):
        expected = replace_once(expected, old, new)
    assert expected.count('bizhawk_probe_gba_shoot_terminal_owner.lua') == 2
    expected = expected.replace('bizhawk_probe_gba_shoot_terminal_owner.lua', 'bizhawk_probe_gba_shoot_terminal_bg_epoch.lua')
    code = blob.decode(); assert expected == code, 'onlydescriptionrunpinandobserverpathschange'
    prefix = code.split("\nout = root / 'build' / name", 1); assert len(prefix) == 2
    tree = ast.parse(prefix[0]); compile(code, str(path), 'exec')
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ''
            assert name not in {'mkdir', 'write_text', 'write_bytes', 'copyfile', 'PrivateDesktopProcess'}
    argv = sys.argv[:]
    try:
        sys.argv = [str(path), 'bizhawk-gba-shoot-terminal-bg-epoch-20261110-z']
        env = {'__file__': str(path), '__name__': '__readonly__'}
        exec(compile(tree, str(path)+':readonlyprefix', 'exec'), env)
    finally:
        sys.argv = argv
    return dict(host_sha256=HOST, pins_sha256=PINS, exact_B159_parent_delta_only=True, readonly_prefix_executed=True, checkpoint_frame=env['parsed']['frame'], source_Core_sha256=sha(env['source_core']), component_sha256=sha(env['rom_data']), same_ROM_input_approval_onewrite_ledger_180sec_private_bound_and_Core_qualification=True, paths_created=False, emulator_launched=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    report = dict(status='TERMINAL_BG_EPOCH_WRAPPER_HOST_DELTA_PASS', verifier_sha256=sha(Path(__file__).read_bytes()), Lua=check_lua(), host=host_preflight(), synthetic_telemetry_not_actual_epoch_or_runtime_eligibility_proof=True, actual_terminal_completion_claim=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print('PASS actualLua54 exactcomposition/11sites/22scalarbound/refusals/read-onlyhostdelta')


if __name__ == '__main__':
    main()
