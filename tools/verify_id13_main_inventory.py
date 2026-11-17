"""Independently close ID13 main wiring, isolated inverse and two fresh inventories."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = 'tools/build_current_candidate.py'
OLD_MAIN = '07B5A946051F4E823F1AAB9B7A8A1B3D7BC3FD7C29E4AA686C3059EC8E82158C'
MAIN = '59F43FB5516E1500683A03FD90F197F8FFDDB1CA22A9CE028C0DF9A39C04D10C'
OLD = 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
FINAL = 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
MANIFEST = '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD'
GATE = 'AF427CBB5E7FCD208D20E624CD907DDF4F3A3573408A67AD8272FB198DFFD6C0'
TABLE_MANIFEST = '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6'
PRIOR = ROOT / 'build/repro-v78-final-audit-20261117/audit.json'
PRIOR_SHA = 'C59C5FA1B43994A24C6F3851B03A25A658E3C8394EEA1E0CE555BBF1085AF97B'
PINS = {MAIN_PATH: MAIN,
    'tools/build_id13_air_relaunch.py': 'F450172FC1ABFA99F895C1A46309D90E3F4E6A21BD9450B24325BE396171F5B3',
    'tools/verify_id13_air_relaunch.py': 'CC077B90609E4E9D93D6C8740D154EC94184F642B2A5910F729E00E3E64A54CE'}
ARTIFACTS = {'evolution-transition.gba': OLD, 'evolution-transition.json': TABLE_MANIFEST,
    'current-candidate.gba': FINAL, 'current-candidate.json': MANIFEST,
    'intermediate/id13-air-relaunch-verification.json': GATE}
ADDED = set(ARTIFACTS) - {'current-candidate.gba', 'current-candidate.json'}
META = {'verification_sha256': GATE, 'source_entry_sites': 4, 'native_entry_sites': 3,
    'callbacks': 4, 'declared_bytes': 988, 'changed_bytes': 968, 'new_RAM_bytes': 0,
    'actual_runtime_verified': False, 'wall_clock_parity_verified': False, 'final_port_complete': False}
OLD_SCOPE = 'source-only character13 aerial branches and audio timbre parity remain unimplemented; '
NEW_SCOPE_PARTS = ('ID13 automatic aerial entry and four source callbacks connect through all three shared fall consumers; ',
    'shared field aliases and native special-air units are preserved; audio timbre parity remains unimplemented; ')
SPANS = ((0xD3F100, 64), (0x357054, 4), (0xD3F150, 64), (0x35732C, 4),
    (0xD3F1A0, 64), (0x3578D4, 4), (0xD3F200, 36), (0xD3F280, 356),
    (0xD3F500, 220), (0xD3F700, 172))
CALLS = {
    'build_id13_air_relaunch.py': ["'--before'", 'evolution_transition', "'--source'", 'args.wsc15',
        "'--gba'", 'args.gba', "'--audio-manifest'", "output / 'evolution-music.json'",
        "'--table-manifest'", "output / 'evolution-transition.json'", "'--output'", 'candidate',
        "'--manifest'", "output / 'current-candidate.json'"],
    'verify_id13_air_relaunch.py': ["'--before'", 'evolution_transition', "'--after'", 'candidate',
        "'--manifest'", "output / 'current-candidate.json'", "'--source'", 'args.wsc15', "'--gba'", 'args.gba',
        "'--audio-manifest'", "output / 'evolution-music.json'", "'--table-manifest'",
        "output / 'evolution-transition.json'", "'--report'", 'id13_air_review']}


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state', '.saveram'), 'no save/state reads')
    return path.read_bytes()


def inventory(directory):
    return {p.relative_to(directory).as_posix(): sha(read(p)) for p in sorted(directory.rglob('*')) if p.is_file()}


def verify_main(raw):
    need(sha(raw) == MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b''), 'frozen CRLF main')
    tree = ast.parse(raw)
    expected = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.startswith('EXPECTED_')}
    need(expected['EXPECTED_LAYERS']['evolution-transition.gba'] == OLD and
         expected['EXPECTED_LAYERS']['current-candidate.gba'] == FINAL, 'intermediate and final image closure')
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    variables = {'evolution_transition': "output / 'evolution-transition.gba'",
        'id13_air_review': "intermediate / 'id13-air-relaunch-verification.json'"}
    removed, bindings, calls, gates = [], {}, {}, {}
    for node in main.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in variables:
                    need(target.id not in bindings, 'unique binding')
                    bindings[target.id] = ast.unparse(node.value); removed.append(node)
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
            continue
        call = node.value
        if not (isinstance(call.func, ast.Name) and call.args):
            continue
        arg = call.args[0]
        if call.func.id == 'run' and isinstance(arg, ast.Constant) and arg.value in CALLS:
            need(arg.value not in calls and not call.keywords, 'one literal new tool call')
            calls[arg.value] = [ast.unparse(x) for x in call.args[1:]]; removed.append(node)
        if call.func.id == 'require_hash' and isinstance(arg, ast.Name) and arg.id == 'id13_air_review':
            need(not gates, 'one independent report gate')
            gates[arg.id] = ast.literal_eval(call.args[1]); removed.append(node)
    need(bindings == variables and calls == CALLS and gates == {'id13_air_review': GATE} and len(removed) == 5,
         'exact paths, tool arguments and independent gate')
    lines = {i for node in removed for i in range(node.lineno - 1, node.end_lineno)}
    metadata = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in ('id13_air_relaunch', 'evolution-transition.gba'):
                    if key.value == 'id13_air_relaunch':
                        metadata.append(ast.literal_eval(value))
                    lines.update(range(key.lineno - 1, value.end_lineno))
    need(metadata == [META], 'qualified new metadata')
    inverse = b''.join(line for i, line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
    for new, old in (
        (b'"--output", evolution_transition,\r\n        "--manifest", output / "evolution-transition.json"',
         b'"--output", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
        (b'"--after", evolution_transition,', b'"--after", candidate,'),
        ((NEW_SCOPE_PARTS[0] + '"\r\n            "' + NEW_SCOPE_PARTS[1]).encode(), OLD_SCOPE.encode()),
        (FINAL.encode(), OLD.encode())):
        need(inverse.count(new) == 1, 'unique predecessor retarget')
        inverse = inverse.replace(new, old)
    need(sha(inverse) == OLD_MAIN, 'complete main inverse to old07B5; all prior calls/gates unchanged')
    return expected


def inverse_rom(before, after, manifest):
    need(len(before) == len(after) == 0x1000000 and sha(before) == OLD and sha(after) == FINAL, 'exact whole images')
    need(tuple((w['offset'], w['size']) for w in manifest['writes']) == SPANS and sum(n for _, n in SPANS) == 988,
         'independent ten-span extent')
    restored = bytearray(after)
    for w, (at, size) in zip(manifest['writes'], SPANS):
        need(before[at:at+size] == bytes.fromhex(w['before_hex']) and
             after[at:at+size] == bytes.fromhex(w['after_hex']), 'exact declared before/after bytes')
        restored[at:at+size] = before[at:at+size]
    need(restored == before and sum(a != b for a, b in zip(before, after)) == 968, 'whole inverse and changed count')


def preflight():
    raw = read(PRIOR); need(sha(raw) == PRIOR_SHA, 'frozen completed v78 inventory')
    prior = json.loads(raw)
    need((prior['status'], prior['files_each'], prior['manifest_entries_each'], prior['final_sha256']) ==
         ('EVOLUTION_TWO_BUILD_INVENTORY_PASS', 325, 125, OLD), 'prior complete closure')
    pins = {**prior['source_tool_sha256'], **PINS}
    for path, digest in pins.items():
        need(sha(read(ROOT / path)) == digest, 'unchanged source ' + path)
    expected = verify_main(read(ROOT / MAIN_PATH))
    isolated = {'build/evolution-transition-tables-20261116/component.gba': OLD,
        'build/evolution-transition-tables-20261116/component.json': TABLE_MANIFEST,
        'build/id13-air-relaunch-v79-20261117/component.gba': FINAL,
        'build/id13-air-relaunch-v79-20261117/component.json': MANIFEST,
        'build/id13-air-relaunch-independent-v79-20261117/audit.json': GATE}
    blobs = {path: read(ROOT / path) for path in isolated}
    need({p: sha(b) for p, b in blobs.items()} == isolated, 'frozen isolated artifacts and independent gate')
    inverse_rom(blobs[next(iter(isolated))], blobs['build/id13-air-relaunch-v79-20261117/component.gba'],
                json.loads(blobs['build/id13-air-relaunch-v79-20261117/component.json']))
    report = dict(status='ID13_MAIN_PREFLIGHT_PASS', main_sha256=MAIN, whole_main_inverse_sha256=OLD_MAIN,
        isolated_inputs=isolated, final_sha256=FINAL, predicted_files_each=328, predicted_manifest_entries_each=126,
        new_relative_paths=sorted(ADDED), new_calls=CALLS, independent_gate_sha256=GATE,
        old_semantic_suites_rerun=False, full_build_executed_by_auditor=False, emulator_launched_by_auditor=False)
    return prior, pins, expected, report


def audit(args, prior, pins, expected, report):
    need(args.root_completed and args.build_a and args.build_b, 'root completion of both builds required')
    builds = [args.build_a.resolve(), args.build_b.resolve()]
    historical = [(ROOT / p).resolve() for p in prior['builds']]
    need(len(set(builds)) == 2 and not set(builds) & set(historical) and
         all(p.parent == ROOT / 'build' for p in builds), 'two distinct fresh workspace builds')
    old = prior['sha256_by_relative_path']
    need(all(inventory(d) == old for d in historical), 'all325 historical artifacts retained')
    actual = [inventory(d) for d in builds]
    need(actual[0] == actual[1] and len(actual[0]) == 328 and actual[0].keys() - old.keys() == ADDED and
         not old.keys() - actual[0].keys(), 'two identical328 inventories with exact3 additions')
    changed = sorted(p for p in old if old[p] != actual[0][p])
    need(changed == ['build-manifest.json', 'current-candidate.gba', 'current-candidate.json'], 'only three shared files changed')
    for p, digest in ARTIFACTS.items():
        need(actual[0][p] == digest, 'exact new/retained artifact ' + p)
    old_manifest = json.loads(read(historical[0] / 'build-manifest.json'))
    closures = []
    for directory in builds:
        manifest = json.loads(read(directory / 'build-manifest.json'))
        need(manifest.keys() - old_manifest.keys() == {'id13_air_relaunch'} and
             not old_manifest.keys() - manifest.keys(), 'one added metadata section')
        need(manifest['id13_air_relaunch'] == META, 'qualified new claims')
        for key, value in old_manifest.items():
            if key != 'layers':
                if isinstance(value, str) and OLD_SCOPE in value:
                    need(value.count(OLD_SCOPE) == 1, 'one historical scope statement')
                    value = value.replace(OLD_SCOPE, ''.join(NEW_SCOPE_PARTS))
                need(manifest[key] == value, 'retained metadata ' + key)
        entries = []
        for key, subdir, const in [('assets','converted-assets','EXPECTED_ASSETS'),
            ('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'), ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),
            ('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'), ('layers','','EXPECTED_LAYERS')]:
            need(manifest[key] == expected[const], 'literal closure ' + key)
            for name, digest in manifest[key].items():
                need(Path(name).name == name and sha(read(directory / subdir / name)) == digest, 'actual closure ' + name)
                entries.append(dict(section=key, path=(Path(subdir) / name).as_posix(), sha256=digest))
        need(len(entries) == 126, 'all126 manifest entries close')
        closures.append(entries)
        inverse_rom(read(directory / 'evolution-transition.gba'), read(directory / 'current-candidate.gba'),
                    json.loads(read(directory / 'current-candidate.json')))
    need([inventory(d) for d in builds] == actual and all(inventory(d) == old for d in historical), 'stable inventories')
    for path, digest in pins.items():
        need(sha(read(ROOT / path)) == digest, 'sources unchanged after audit ' + path)
    report.update(status='ID13_TWO_BUILD_INVENTORY_PASS', files_each=328, manifest_entries_each=126,
        builds=[d.relative_to(ROOT).as_posix() for d in builds], sha256_by_relative_path=actual[0], source_tool_sha256=pins,
        manifest_closures=closures, changed_shared_v78_paths=changed, baseline_audit_sha256=PRIOR_SHA,
        whole_new_layer_inverse=True, previous_325_artifacts_preserved=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight', action='store_true'); p.add_argument('--root-completed', action='store_true')
    p.add_argument('--build-a', type=Path); p.add_argument('--build-b', type=Path)
    p.add_argument('--report', type=Path, required=True); args = p.parse_args()
    need(not args.report.exists(), 'fresh report required')
    prior, pins, expected, result = preflight()
    if args.preflight:
        need(not args.root_completed and not args.build_a and not args.build_b, 'preflight reads no fresh outputs')
    else:
        audit(args, prior, pins, expected, result)
    result['checker_sha256'] = sha(read(Path(__file__)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(result['status'], sha(read(args.report)))
