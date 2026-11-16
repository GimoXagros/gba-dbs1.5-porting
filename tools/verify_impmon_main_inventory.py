"""Verify the last two v77 evolution layers and both fresh build inventories."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = 'tools/build_current_candidate.py'
OLD_MAIN = '15DC1DAB1DAE7766D312A0F666E23D3F5EACEF78B9CEB680DE55FEF2BB0A47CF'
MAIN = '07B5A946051F4E823F1AAB9B7A8A1B3D7BC3FD7C29E4AA686C3059EC8E82158C'
OLD = 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
MID = '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
FINAL = 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
IMP_MANIFEST = '32AD301794BEE771211F53E75C1CDC7DE8BE8E7A030C32356A11519564CD48D9'
TABLE_MANIFEST = '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6'
IMP_GATE = 'D727C5DC1D35E2C743F8C3B8E6D24BC096AFFACBE45172FE078DD5196A250661'
TABLE_GATE = 'A787F41CD3A78BD0B509F2A7EC96C10133BDB825292BC11EDB169D162AA2469B'
PRIOR = ROOT / 'build/repro-v77-final-audit-20261116/audit.json'
PRIOR_SHA = '0EBBA5EFBEA7292990F54E7E138C1527E853BF58047BEF73260B6BBFF352ECFE'
PINS = {
    MAIN_PATH: MAIN,
    'tools/build_impmon_evolution_gate.py': 'C7D88E9E07E683DF73D56F5097EA422DF484D111D4EDCF70CAF76119274EBF73',
    'tools/verify_impmon_evolution_gate.py': '8AD86CF8A65D2D46612399907BA9DB44E21ABE1975087B8AF106570753193705',
    'tools/build_evolution_transition_tables.py': '7DC002920D38E12F49743DB1D51E644037FFA5E487A69632445ACB616D05600D',
    'tools/verify_evolution_event_tables.py': 'B9BB463EA86CBF76A5534B954DF7FE6555F4CA5BD1AA81FB8FD59212EC994A67',
}
ARTIFACTS = {
    'evolution-music-pause.gba': OLD,
    'impmon-evolution.gba': MID,
    'impmon-evolution.json': IMP_MANIFEST,
    'intermediate/impmon-evolution-verification.json': IMP_GATE,
    'intermediate/evolution-transition-verification.json': TABLE_GATE,
    'current-candidate.gba': FINAL,
    'current-candidate.json': TABLE_MANIFEST,
}
ADDED = set(ARTIFACTS) - {'current-candidate.gba', 'current-candidate.json'} | {'evolution-music-pause.json'}
META = {
    'impmon_evolution_contact': {
        'mode_scope': 'source flag-clear default Ver.1.5 mode; alternate mode not implemented',
        'declared_bytes': 4, 'changed_bytes': 1, 'boss_identity_15_excluded': True,
        'actual_runtime_evolution_verified': False, 'final_port_complete': False,
    },
    'evolution_transition_tables': {
        'playable_identities': 15, 'tables': 3, 'declared_bytes': 114, 'changed_bytes': 109,
        'old_identities_0_to_10_preserved': True, 'source_events_and_native_bounds_verified': True,
        'actual_runtime_verified': False, 'historical_e5_cause_proven': False, 'final_port_complete': False,
    },
}
CALLS = {
    'build_impmon_evolution_gate.py': [
        "'--before'", 'evolution_music_pause', "'--gba'", 'args.gba', "'--wsc10'", 'args.wsc10',
        "'--wsc15'", 'args.wsc15', "'--output'", 'impmon_evolution', "'--manifest'", "output / 'impmon-evolution.json'",
    ],
    'build_evolution_transition_tables.py': [
        "'--before'", 'impmon_evolution', "'--wsc15'", 'args.wsc15', "'--allocation-manifest'", "output / 'evolution-music.json'",
        "'--output'", 'candidate', "'--manifest'", "output / 'current-candidate.json'",
    ],
    'verify_impmon_evolution_gate.py': [
        "'--before'", 'evolution_music_pause', "'--after'", 'impmon_evolution', "'--gba'", 'args.gba',
        "'--wsc10'", 'args.wsc10', "'--wsc15'", 'args.wsc15', "'--report'", 'impmon_evolution_review',
    ],
    'verify_evolution_event_tables.py': [
        "'--before'", 'impmon_evolution', "'--after'", 'candidate', "'--wsc15'", 'args.wsc15',
        "'--music-manifest'", "output / 'evolution-music.json'", "'--report'", 'evolution_tables_review',
    ],
}
CHECKS = {'impmon_evolution_review': IMP_GATE, 'evolution_tables_review': TABLE_GATE}
IMP_SPANS = ((0x354700, 4),)
TABLE_SPANS = ((0x35A1E4, 4), (0x35A210, 4), (0x35A54C, 4), (0x35A550, 4),
               (0x35A580, 4), (0x35A598, 4), (0xD3F000, 90))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state', '.saveram'), 'no save or state reads')
    return path.read_bytes()


def inventory(directory, excluded=None):
    return {p.relative_to(directory).as_posix(): sha(read(p))
            for p in sorted(directory.rglob('*')) if p.is_file() and p != excluded}


def verify_main(raw):
    need(sha(raw) == MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b''), 'exact reviewed CRLF main')
    tree = ast.parse(raw)
    expected = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id.startswith('EXPECTED_')}
    need({name: expected['EXPECTED_LAYERS'][name] for name in (
        'evolution-music-pause.gba', 'impmon-evolution.gba', 'current-candidate.gba')}
        == {name: ARTIFACTS[name] for name in ('evolution-music-pause.gba', 'impmon-evolution.gba', 'current-candidate.gba')},
        'literal image closure for all three stages')
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    variables = {
        'evolution_music_pause': "output / 'evolution-music-pause.gba'",
        'impmon_evolution': "output / 'impmon-evolution.gba'",
        'impmon_evolution_review': "intermediate / 'impmon-evolution-verification.json'",
        'evolution_tables_review': "intermediate / 'evolution-transition-verification.json'",
    }
    removed, calls, gates, bindings = [], {}, {}, {}
    for node in main.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in variables:
                    need(target.id not in bindings, 'one new path binding')
                    bindings[target.id] = ast.unparse(node.value)
                    removed.append(node)
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
            continue
        call = node.value
        if isinstance(call.func, ast.Name) and call.args:
            arg = call.args[0]
            if call.func.id == 'run' and isinstance(arg, ast.Constant) and arg.value in CALLS:
                need(arg.value not in calls and not call.keywords, 'one literal new tool call')
                calls[arg.value] = [ast.unparse(value) for value in call.args[1:]]
                removed.append(node)
            if call.func.id == 'require_hash' and isinstance(arg, ast.Name) and arg.id in CHECKS:
                need(arg.id not in gates, 'one independent gate per production tool')
                gates[arg.id] = ast.literal_eval(call.args[1])
                removed.append(node)
    need(bindings == variables and calls == CALLS and gates == CHECKS and len(removed) == 10,
         'exact production tool arguments, paths and pins')

    lines = {i for node in removed for i in range(node.lineno - 1, node.end_lineno)}
    metadata = {}
    layer_keys = {'evolution-music-pause.gba', 'impmon-evolution.gba'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in META.keys() | layer_keys:
                    if key.value in META:
                        need(key.value not in metadata, 'one conservative manifest section')
                        metadata[key.value] = ast.literal_eval(value)
                    lines.update(range(key.lineno - 1, value.end_lineno))
    need(metadata == META, 'qualified metadata without runtime or E5 completion claim')
    inverse = b''.join(line for n, line in enumerate(raw.splitlines(keepends=True)) if n not in lines)
    changes = (
        (b'"--output", evolution_music_pause, "--manifest", output / "evolution-music-pause.json"',
         b'"--output", candidate, "--manifest", output / "current-candidate.json"'),
        (b'"--after", evolution_music_pause,\r\n        "--manifest", output / "evolution-music-pause.json"',
         b'"--after", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
        (FINAL.encode(), OLD.encode()),
    )
    for new, old in changes:
        need(inverse.count(new) == 1, 'unique exact changed predecessor argument')
        inverse = inverse.replace(new, old)
    need(sha(inverse) == OLD_MAIN, 'complete unchanged caller and gate inverse to frozen 15DC main')
    return expected


def inverse_rom(before, after, spans, expected_changes):
    need(len(before) == len(after) == 0x1000000, 'whole 16 MiB layer extents')
    restored = bytearray(after)
    changed = 0
    for at, size in spans:
        restored[at:at + size] = before[at:at + size]
        changed += sum(x != y for x, y in zip(before[at:at + size], after[at:at + size]))
    need(bytes(restored) == before and changed == expected_changes, 'whole layer inverse and changed-byte count')


def preflight():
    raw = read(PRIOR)
    need(sha(raw) == PRIOR_SHA, 'frozen completed 319-artifact v77 baseline')
    prior = json.loads(raw)
    need((prior['status'], prior['files_each'], prior['manifest_entries_each'], prior['final_sha256'])
         == ('PASS', 319, 123, OLD), 'earlier independent record')
    source_pins = {**prior['source_tool_sha256'], **PINS}
    for path, digest in source_pins.items():
        need(sha(read(ROOT / path)) == digest, 'immutable source ' + path)
    expected = verify_main(read(ROOT / MAIN_PATH))
    isolated = {
        'build/evolution-music-pause-cache-20261110/component.gba': OLD,
        'build/impmon-evolution-clean15-20261116/component.gba': MID,
        'build/evolution-transition-tables-20261116/component.gba': FINAL,
        'build/impmon-evolution-clean15-20261116/manifest.json': IMP_MANIFEST,
        'build/evolution-transition-tables-20261116/component.json': TABLE_MANIFEST,
        'build/impmon-evolution-clean15-independent-qa-20261116/gate.json': IMP_GATE,
        'build/evolution-transition-tables-independent-qa-20261116/gate.json': TABLE_GATE,
    }
    blobs = {path: read(ROOT / path) for path in isolated}
    need({path: sha(blob) for path, blob in blobs.items()} == isolated, 'identical isolated components and audit gates')
    before, middle, after = [blob for path, blob in blobs.items() if path.endswith('.gba')]
    inverse_rom(before, middle, IMP_SPANS, 1)
    inverse_rom(middle, after, TABLE_SPANS, 109)
    return prior, source_pins, expected, dict(
        status='EVOLUTION_MAIN_PREFLIGHT_PASS', main_sha256=MAIN, whole_main_inverse_sha256=OLD_MAIN,
        isolated_inputs=isolated, final_sha256=FINAL, predicted_files_each=325, predicted_manifest_entries_each=125,
        new_relative_paths=sorted(ADDED), new_calls=CALLS, independent_gate_sha256=[IMP_GATE, TABLE_GATE],
        old_semantic_suites_rerun=False, full_build_executed_by_auditor=False, emulator_launched_by_auditor=False)


def audit(args, prior, pins, expected, report):
    need(args.root_completed and args.build_a and args.build_b, 'explicit completion of both builds before artifact reads')
    builds = [args.build_a.resolve(), args.build_b.resolve()]
    historical = [(ROOT / path).resolve() for path in prior['builds']]
    need(len(set(builds)) == 2 and not set(builds) & set(historical)
         and all(directory.parent == ROOT / 'build' for directory in builds), 'two fresh distinct workspace builds')
    old = prior['sha256_by_relative_path']
    excluded = (ROOT / prior['excluded_path']).resolve()
    need(all(inventory(directory, excluded) == old for directory in historical),
         'all 319 earlier artifacts retained and only its named save excluded')
    actual = [inventory(directory) for directory in builds]
    need(actual[0] == actual[1] and actual[0].keys() - old.keys() == ADDED
         and not old.keys() - actual[0].keys() and len(actual[0]) == 325, 'matching 325 archives with exact six additions')
    changed = sorted(path for path in old if old[path] != actual[0][path])
    need(changed == ['build-manifest.json', 'current-candidate.gba', 'current-candidate.json'], 'only three changed shared paths')
    for path, digest in {**ARTIFACTS, 'evolution-music-pause.json': old['current-candidate.json']}.items():
        need(actual[0][path] == digest, 'exact retained or new artifact ' + path)
    old_manifest = json.loads(read(historical[0] / 'build-manifest.json'))
    closures = []
    for directory in builds:
        manifest = json.loads(read(directory / 'build-manifest.json'))
        need(manifest.keys() - old_manifest.keys() == META.keys() and not old_manifest.keys() - manifest.keys(),
             'exact two added main metadata sections')
        for key, value in old_manifest.items():
            if key != 'layers':
                need(manifest[key] == value, 'retained main metadata ' + key)
        need({key: manifest[key] for key in META} == META, 'conservative added claim scope')
        entries = []
        for key, subdir, const in (
            ('assets', 'converted-assets', 'EXPECTED_ASSETS'), ('stage_assets', 'stage-assets', 'EXPECTED_STAGE_ASSETS'),
            ('opening_assets', 'opening-assets', 'EXPECTED_OPENING_ASSETS'), ('shoot_assets', 'shoot-assets', 'EXPECTED_SHOOT_ASSETS'),
            ('layers', '', 'EXPECTED_LAYERS'),
        ):
            need(manifest[key] == expected[const], 'literal manifest closure ' + key)
            for name, digest in manifest[key].items():
                need(Path(name).name == name and sha(read(directory / subdir / name)) == digest, 'actual closure ' + name)
                entries.append(dict(section=key, path=(Path(subdir) / name).as_posix(), sha256=digest))
        need(len(entries) == 125, 'complete 125-entry closure per fresh build')
        closures.append(entries)
        before, middle, final = [read(directory / name) for name in ('evolution-music-pause.gba', 'impmon-evolution.gba', 'current-candidate.gba')]
        inverse_rom(before, middle, IMP_SPANS, 1)
        inverse_rom(middle, final, TABLE_SPANS, 109)

    need([inventory(directory) for directory in builds] == actual, 'fresh inventories remain unchanged')
    need(all(inventory(directory, excluded) == old for directory in historical), 'frozen historical inventories remain unchanged')
    for path, digest in pins.items():
        need(sha(read(ROOT / path)) == digest, 'sources remain unchanged ' + path)
    report.update(status='EVOLUTION_TWO_BUILD_INVENTORY_PASS', files_each=325, manifest_entries_each=125,
                  builds=[directory.relative_to(ROOT).as_posix() for directory in builds], sha256_by_relative_path=actual[0],
                  source_tool_sha256=pins, manifest_closures=closures, changed_shared_v77_paths=changed,
                  baseline_audit_sha256=PRIOR_SHA, whole_new_layer_inverses=True, previous_319_artifacts_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--build-a', type=Path)
    parser.add_argument('--build-b', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    prior, pins, expected, result = preflight()
    if args.preflight:
        need(not args.root_completed and not args.build_a and not args.build_b, 'preflight excludes fresh output arguments')
    else:
        audit(args, prior, pins, expected, result)
    result['checker_sha256'] = sha(read(Path(__file__)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], sha(read(args.report)))
