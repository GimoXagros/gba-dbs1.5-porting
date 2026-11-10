#!/usr/bin/env python3
"""Narrow v75 wiring/inverse/host preflight; no build, capture or emulator I/O."""
import argparse
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import verify_result_language_capture as runtime
from verify_result_v74_integration import need, sha, read, audit_prefix

ROOT = Path(__file__).resolve().parents[1]
MAIN = 'F5CDCE4F4D51FAA2D95BE30BB2C93C819494F3B1EDDE3B660E39ACFDDE5FD1C0'
RUNTIME = 'C31719BAE4C6D1BBD6B92A6BA8C0AB04C1494339EEEDF6D0D61435CBD4279A67'
OLD_RUNTIME = 'DFDD17521A0B728EE4ED1B511EF606D736DD61269B87EFC9AF2CFBD22CE42025'
HELPER = '67C68ECED8B42BC0736F8A04EAECE3C4163F757901CFF08052EB7E62A860FB68'
HOST = 'B006A842802BF90241538D9CCE744F75ED58889E2B14468745183C065B97120F'
OLD_HOST = '58D9E9EBE7ECF4823DAC35DC7EE4EE5146301AF963E9D4E4C84937D178E2AAD5'
V74 = '1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
PALETTE = 'FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
FINAL = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
REPORT_PINS = {
    'rectangle_review': 'BAD282D7F5AEAC391022D3A3C350C4257A6BC15A901406EC29F875CEDFB4DACA',
    'palette_calls_review': '94F9FD0FC4B95F64CA7BFB4F424DF333EF29170B8CDA32A1CA2FB4BEF0BDC840',
    'owner_link_review': '8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3',
}


def main_calls(tree):
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    paths = dict(shoot_native_scene='shoot-native-scene.gba', shoot_rectangle='shoot-child-rectangle.gba',
                 shoot_palette_calls='shoot-palette-calls.gba', candidate='current-candidate.gba')
    reviews = dict(rectangle_review='shoot-child-rectangle-verification.json',
                   palette_calls_review='shoot-palette-calls-verification.json',
                   owner_link_review='shoot-owner-link-verification.json')
    env = dict(output=Path('FRESH'), intermediate=Path('FRESH/intermediate'),
               args=SimpleNamespace(gba=Path('ORIGINAL.gba'), wsc15=Path('ORIGINAL.wsc')))
    for mapping, parent in ((paths, 'output'), (reviews, 'intermediate')):
        for name, path in mapping.items():
            nodes = [n for n in main.body if isinstance(n, ast.Assign) and
                     any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
            need(len(nodes) == 1 and ast.unparse(nodes[0].value) == f"{parent} / '{path}'", 'fresh path ' + name)
            env[name] = env[parent] / path
    s, r, p, c = (env[x] for x in paths)
    g, w = env['args'].gba, env['args'].wsc15
    expected = {
        'build_shoot_child_attack_rectangle.py': [s, g, w, r, '--manifest', Path('FRESH/shoot-child-rectangle.json')],
        'build_shoot_palette_dim_calls.py': [r, w, p, '--manifest', Path('FRESH/shoot-palette-calls.json')],
        'build_shoot_terminal_owner_link.py': [p, w, c, '--manifest', Path('FRESH/current-candidate.json')],
        'verify_shoot_child_attack_rectangle_production.py': ['--before', s, '--after', r, '--gba', g, '--source', w,
            '--manifest', Path('FRESH/shoot-child-rectangle.json'), '--report', env['rectangle_review']],
        'verify_shoot_palette_dim_calls_production.py': ['--before', r, '--after', p, '--source', w,
            '--manifest', Path('FRESH/shoot-palette-calls.json'), '--report', env['palette_calls_review']],
        'verify_shoot_terminal_owner_link_production.py': ['--before', p, '--after', c, '--source', w,
            '--manifest', Path('FRESH/current-candidate.json'), '--report', env['owner_link_review']],
    }
    calls, pins = {}, {}
    for n in ast.walk(main):
        if not isinstance(n, ast.Call) or not isinstance(n.func, ast.Name) or not n.args:
            continue
        if n.func.id == 'run' and isinstance(n.args[0], ast.Constant) and n.args[0].value in expected:
            key = n.args[0].value
            need(key not in calls, 'unique production caller')
            calls[key] = [eval(compile(ast.Expression(a), 'main caller', 'eval'), {'__builtins__': {}}, env) for a in n.args[1:]]
        if n.func.id == 'require_hash' and isinstance(n.args[0], ast.Name) and n.args[0].id in reviews:
            key = n.args[0].id
            need(key not in pins, 'unique report pin')
            pins[key] = ast.literal_eval(n.args[1])
    need(calls == expected and pins == REPORT_PINS, 'exact fresh production calls and report pins')
    return {name: [str(x) for x in values] for name, values in calls.items()}


def check():
    mainraw = read(ROOT / 'tools/build_current_candidate.py')
    raw = read(ROOT / 'tools/verify_result_language_capture.py')
    host = read(ROOT / 'build/run_result_v75_20261110.py')
    oldhost = read(ROOT / 'build/run_result_v74_20261109.py')
    need(tuple(map(sha, (mainraw, raw, host, oldhost))) == (MAIN, RUNTIME, HOST, OLD_HOST), 'frozen main/runtime/hosts')
    need(sha(read(ROOT / 'tools/verify_result_v74_integration.py')) == HELPER, 'unchanged reused helpers')
    function = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'audit')
    cases = function.body[1:3]
    need(all(isinstance(n, ast.If) for n in cases), 'first two new inverse branches')
    removed = {i for n in cases for i in range(n.lineno - 1, n.end_lineno)}
    previous = b''.join(line for i, line in enumerate(raw.splitlines(keepends=True)) if i not in removed)
    need(len(removed) == 13 and sha(previous) == OLD_RUNTIME, 'only13 new inverse lines; oldDFDD byte exact')
    need(host == oldhost.replace(b'v74-20261109', b'v75-20261110').replace(V74.encode(), FINAL.encode()), 'host exact date/version and ROM delta')
    ast.parse(host)
    tree = ast.parse(mainraw)
    calls = main_calls(tree)
    layers = ast.literal_eval(next(n.value for n in tree.body if isinstance(n, ast.Assign) and
        any(isinstance(t, ast.Name) and t.id == 'EXPECTED_LAYERS' for t in n.targets)))
    need({k: layers[k] for k in ('shoot-child-rectangle.gba', 'shoot-palette-calls.gba', 'current-candidate.gba')} ==
        {'shoot-child-rectangle.gba': V74, 'shoot-palette-calls.gba': PALETTE, 'current-candidate.gba': FINAL}, 'three layer identities')
    claims = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for key, value in zip(n.keys, n.values):
                if isinstance(key, ast.Constant) and key.value in ('shoot_palette_dim_calls', 'shoot_terminal_owner_link'):
                    need(key.value not in claims, 'unique layer claim')
                    claims[key.value] = ast.literal_eval(value)
    need(claims == {
        'shoot_palette_dim_calls': dict(verification_sha256=REPORT_PINS['palette_calls_review'], declared_bytes=16,
            changed_bytes=12, new_RAM_bytes=0, conditional_calls=4, existing_helper='085C6FD4', self_targeting_calls_removed=True),
        'shoot_terminal_owner_link': dict(verification_sha256=REPORT_PINS['owner_link_review'], declared_bytes=4,
            changed_bytes=1, new_RAM_bytes=0, guard_site='086FFC00', auxiliary_owner_offset=40,
            other_guard_predicates_unchanged=True, final_port_complete=False)}, 'accurate new layer claims')
    need(all(t in mainraw for t in (b'UNRESOLVED_OBSERVER', b'general terminal ',
        b'interrupted-DI and moving-player camera domains remain unfulfilled')), 'retained unresolved scope')
    v74, palette, final = (read(ROOT / p) for p in (
        'build/shoot-child-attack-rectangle-20261109/component.gba',
        'build/shoot-palette-project-calls-20261109/component.gba',
        'build/shoot-terminal-owner-link-20261109/component.gba'))
    need(tuple(map(sha, (v74, palette, final))) == (V74, PALETTE, FINAL), 'approved full component identities')
    restored = bytearray(final)
    restored[0x6FFC00:0x6FFC04] = bytes.fromhex('180096E5')
    need(bytes(restored) == palette, 'whole owner inverse to palette component')
    sites = (0x5C6F4C, 0x5C6F5C, 0x5C6F88, 0x5C6FBC, 0x6FFC00)
    for at in sites[:4]:
        restored[at:at + 4] = bytes.fromhex('FEFFFF1B')
    need(bytes(restored) == v74, 'whole five-span inverse to v74')
    changed = [i for i, (a, b) in enumerate(zip(final, v74)) if a != b]
    need(len(final) == len(v74) == 0x800000 and len(changed) == 13 and
         all(any(at <= i < at + 4 for at in sites) for i in changed), '20 declared bytes and13 actual changes only')
    retail = read(Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba'))
    observer = read(ROOT / 'tools/bizhawk_probe_result_languages.lua')
    for rom in (final, palette, v74):
        audit_prefix(runtime.audit, rom, retail, observer, True)
    rejected = []
    for at in sorted({i for site in sites for i in range(site - 1, site + 5)} | {0x5B9180, 0x7FFFFF}):
        bad = bytearray(final); bad[at] ^= 1
        audit_prefix(runtime.audit, bytes(bad), retail, observer, False)
        rejected.append(hex(at))
    audit_prefix(runtime.audit, final + b'\xff', retail, observer, False)
    rejected.append('length')
    controls = []
    for old, new in ((b"restored[0x6FFC00:0x6FFC04] = bytes.fromhex('180096E5')",
                     b"restored[0x6FFC00:0x6FFC04] = bytes.fromhex('280096E5')"),
                    (b'(0x5C6F4C, 0x5C6F5C, 0x5C6F88, 0x5C6FBC)', b'(0x5C6F4C, 0x5C6F5C, 0x5C6F88)'),
                    (b"bytes.fromhex('FEFFFF1B')", b"bytes.fromhex('2000001B')")):
        need(raw.count(old) == 1, 'unique inverse mutation anchor')
        namespace = {'__name__': 'v75_inverse_control', '__file__': str(ROOT / 'tools/verify_result_language_capture.py')}
        exec(compile(raw.replace(old, new), 'v75 inverse mutation', 'exec'), namespace)
        audit_prefix(namespace['audit'], final, retail, observer, False)
        controls.append(old.decode())
    return dict(status='PASS_V75_MAIN_INVERSE_HOST_PREFLIGHT', main_sha256=MAIN, runtime_sha256=RUNTIME,
        host_sha256=HOST, reused_helper_sha256=HELPER, reconstructed_prior_runtime_sha256=sha(previous),
        new_inverse_lines=len(removed), host_delta_only=['v74-20261109 to v75-20261110', '1477 to46B3'],
        fresh_affected_callers=calls, report_pins=REPORT_PINS, new_layer_claims=claims,
        whole_two_layer_inverse=True, declared_bytes=20, changed_bytes=len(changed), changed_offsets=changed,
        actual_audit_pre_capture_positives=3, corruptions_rejected_before_capture_IO=rejected,
        semantic_inverse_controls=controls, capture_files_opened=0, full_build_executed=False,
        emulator_launched=False, old_semantic_suites_rerun=False, checker_sha256=sha(read(Path(__file__))),
        qualification='Changed wiring/inverse/private-host delta only. Fresh builds and actual runtime acceptance remain root-owned; E5 and final port remain open.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report')
    result = check()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
