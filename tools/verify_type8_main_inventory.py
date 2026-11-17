"""Check type8 main wiring, complete predecessor inverse and fresh inventories."""
import argparse
import ast
import json
from pathlib import Path
import struct
from verify_id13_main_inventory import need, sha, read, inventory

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = 'tools/build_current_candidate.py'
MAIN = '1665CA2BD6E562662577A6102F8F2656946E0E92B53836576E9ACCFC37BD0A1B'
OLD_MAIN = 'B82099CA9E1257148DF978F35BA763F7B8F78CFECBDFB90679C3ECD1E6A162BC'
OLD = '933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
FINAL = '75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
OLD_MANIFEST = '6032094CBFB4CC366ACACDB5CE7E6817F815251B557553BA26BE78DDB92EA53C'
MANIFEST = '06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230'
GATE = '0A5EB8355D74AF38C61A90C74ECAD636BDCF6250066C786119DC4EC2513C8896'
PRIOR = ROOT / 'build/campaign-main-inventory-20261117/final.json'
PRIOR_SHA = '55CEF6F5AA41755446C9B01B534B4A41D141B6436620A89DF96F7FC38113B4B4'
PINS = {
    MAIN_PATH: MAIN,
    'tools/build_character_type8_tables.py': '5CCB654D5DFE62F3791BF11E3F82B4176CBD271E5CFE55A64B09811D49AEF46C',
    'tools/verify_character_type8_tables.py': '3269953041EE9FB57C210CA01206630BFFFC781B77F1477C47F6E0E851867648',
    'tools/verify_campaign_main_inventory.py': 'E117717E9D26A460BE81A27B565FEB468CD08A361B519A25115C4D16FA07E2CD',
    'tools/verify_id13_main_inventory.py': '596A662F1BA9BFD2B0F6F75059D3A86FBB8029195F35355A1A6DBF50B47E73B2',
}
ARTIFACTS = {
    'campaign-progress-consumers.gba': OLD,
    'campaign-progress-consumers.json': OLD_MANIFEST,
    'current-candidate.gba': FINAL,
    'current-candidate.json': MANIFEST,
    'intermediate/type8-tables-verification.json': GATE,
}
ADDED = set(ARTIFACTS) - {'current-candidate.gba', 'current-candidate.json'}
META = {'verification_sha256': GATE, 'source_identities': 15, 'tables': 4,
        'native_pointer_readers': 5, 'declared_bytes': 260, 'changed_bytes': 255,
        'new_RAM_bytes': 0, 'native_action_records_and_code_preserved': True,
        'actual_runtime_verified': False, 'whole_campaign_runtime_verified': False,
        'final_port_complete': False}
OWNERS = ["output / 'evolution-music.json'", "output / 'evolution-transition.json'",
          "output / 'id13-air-relaunch.json'", "output / 'campaign-stage-progression.json'",
          "output / 'campaign-progress-consumers.json'"]
CALLS = {
    'build_character_type8_tables.py': ["'--before'", 'campaign_consumers', "'--gba'", 'args.gba',
        "'--old'", 'args.wsc10', "'--source'", 'args.wsc15', "'--owners'", *OWNERS,
        "'--output'", 'candidate', "'--manifest'", "output / 'current-candidate.json'"],
    'verify_character_type8_tables.py': ["'--before'", 'campaign_consumers', "'--after'", 'candidate',
        "'--source'", 'args.wsc15', "'--old'", 'args.wsc10', "'--gba'", 'args.gba',
        "'--owners'", *OWNERS, "'--report'", 'type8_review'],
}
TABLES = (0xD3FD04, 0xD3FD40, 0xD3FD7C, 0xD3FE90)
ALIASES = ((0x36F7AC,), (0x36F7B0,), (0x36F7B4,), (0x36CAA8, 0x36F7B8))
SPANS = {**{a: 60 for a in TABLES}, **{a: 4 for aliases in ALIASES for a in aliases}}


def verify_main(raw):
    need(sha(raw) == MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b''), 'frozen CRLF main')
    tree = ast.parse(raw)
    expected = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.startswith('EXPECTED_')}
    need(expected['EXPECTED_LAYERS']['campaign-progress-consumers.gba'] == OLD and
         expected['EXPECTED_LAYERS']['current-candidate.gba'] == FINAL, 'explicit predecessor and final image closure')
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    variables = {'campaign_consumers': "output / 'campaign-progress-consumers.gba'",
                 'type8_review': "intermediate / 'type8-tables-verification.json'"}
    removed, bindings, calls, gates = [], {}, {}, {}
    for node in main.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in variables:
                    need(target.id not in bindings, 'one new variable binding')
                    bindings[target.id] = ast.unparse(node.value)
                    removed.append(node)
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
            continue
        call = node.value
        if not (isinstance(call.func, ast.Name) and call.args):
            continue
        arg = call.args[0]
        if call.func.id == 'run' and isinstance(arg, ast.Constant) and arg.value in CALLS:
            need(arg.value not in calls and not call.keywords, 'one literal layer call')
            calls[arg.value] = [ast.unparse(a) for a in call.args[1:]]
            removed.append(node)
        if call.func.id == 'require_hash' and isinstance(arg, ast.Name) and arg.id == 'type8_review':
            need(arg.id not in gates, 'one independent gate')
            gates[arg.id] = ast.literal_eval(call.args[1])
            removed.append(node)
    need(bindings == variables and calls == CALLS and gates == {'type8_review': GATE} and len(removed) == 5,
         'exact new calls, both paths, all five owners and independent hash gate')
    lines = {i for node in removed for i in range(node.lineno-1, node.end_lineno)}
    metadata = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in ('type8_reaction_tables', 'campaign-progress-consumers.gba'):
                    if key.value == 'type8_reaction_tables': metadata.append(ast.literal_eval(value))
                    lines.update(range(key.lineno-1, value.end_lineno))
    need(metadata == [META], 'new metadata is exact and static-only')
    inverse = b''.join(line for i, line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
    changes = [
        (b'"--output", campaign_consumers, "--manifest", output / "campaign-progress-consumers.json"',
         b'"--output", candidate, "--manifest", output / "current-candidate.json"'),
        (b'"--after", campaign_consumers,\r\n        "--manifest", output / "campaign-progress-consumers.json"',
         b'"--after", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
        (FINAL.encode(), OLD.encode()),
    ]
    for new, old in changes:
        need(inverse.count(new) == 1, 'unique predecessor retarget')
        inverse = inverse.replace(new, old)
    need(sha(inverse) == OLD_MAIN, 'complete main inverse to B820 with every prior call/gate preserved')
    return expected


def inverse_rom(before, after, manifest):
    need(len(before) == len(after) == 0x1000000 and sha(before) == OLD and sha(after) == FINAL, 'complete pinned layer')
    need(len(manifest['writes']) == 9 and {w['offset']: w['size'] for w in manifest['writes']} == SPANS,
         'independent exact nine write ranges')
    planned = bytearray(before)
    for k, table in enumerate(TABLES):
        planned[table:table+60] = struct.pack('<15I', *((0x0836C12C + k*128,) * 15))
        for alias in ALIASES[k]:
            need(struct.unpack_from('<I', before, alias)[0] == 0x0836BE44 + k*48, 'old literal owner')
            planned[alias:alias+4] = struct.pack('<I', 0x08000000+table)
    need(bytes(planned) == after, 'entire image equals independently encoded tables and five pointers')
    restored = bytearray(after)
    for write in manifest['writes']:
        at, size = write['offset'], write['size']
        need(before[at:at+size] == bytes.fromhex(write['before_hex']) and
             after[at:at+size] == bytes.fromhex(write['after_hex']), 'all declared bytes exact')
        restored[at:at+size] = before[at:at+size]
    need(bytes(restored) == before and sum(a != b for a,b in zip(before,after)) == 255 and sum(SPANS.values()) == 260,
         'complete inverse and exact 260 declared / 255 changed bytes')


def preflight():
    raw = read(PRIOR)
    need(sha(raw) == PRIOR_SHA, 'frozen v80 complete audit')
    prior = json.loads(raw)
    need((prior['status'], prior['files_each'], prior['manifest_entries_each'], prior['final_sha256']) ==
         ('CAMPAIGN_TWO_BUILD_INVENTORY_PASS', 334, 128, OLD), 'completed predecessor closure')
    pins = {**prior['source_tool_sha256'], **PINS}
    for path, digest in pins.items(): need(sha(read(ROOT/path)) == digest, 'unchanged source '+path)
    expected = verify_main(read(ROOT/MAIN_PATH))
    isolated = {**prior['isolated_inputs'],
        'build/character-type8-tables-r2-20261117/component.gba': FINAL,
        'build/character-type8-tables-r2-20261117/component.json': MANIFEST,
        'build/type8-tables-independent-final-20261117/report.json': GATE}
    for path, digest in isolated.items(): need(sha(read(ROOT/path)) == digest, 'frozen isolated artifact '+path)
    inverse_rom(read(ROOT/'build/campaign-stage-progression-v80-20261117-r2/component.gba'),
                read(ROOT/'build/character-type8-tables-r2-20261117/component.gba'),
                json.loads(read(ROOT/'build/character-type8-tables-r2-20261117/component.json')))
    for path in prior['builds']:
        need(inventory(ROOT/path) == prior['sha256_by_relative_path'], 'all 334 historical files remain unchanged')
    report = dict(status='TYPE8_MAIN_PREFLIGHT_PASS', main_sha256=MAIN, whole_main_inverse_sha256=OLD_MAIN,
                  isolated_inputs=isolated, final_sha256=FINAL, predicted_files_each=337, predicted_manifest_entries_each=129,
                  new_relative_paths=sorted(ADDED), new_calls=CALLS, independent_gate_sha256=GATE,
                  old_semantic_suites_rerun=False, full_build_executed_by_auditor=False, emulator_launched_by_auditor=False)
    return prior, pins, expected, report


def audit(args, prior, pins, expected, report):
    need(args.root_completed and args.build_a and args.build_b, 'explicit root completion of both builds')
    builds = [args.build_a.resolve(), args.build_b.resolve()]
    historical = [(ROOT/path).resolve() for path in prior['builds']]
    need(len(set(builds)) == 2 and not set(builds)&set(historical) and all(d.parent == ROOT/'build' for d in builds),
         'two distinct fresh workspace builds')
    old = prior['sha256_by_relative_path']
    actual = [inventory(directory) for directory in builds]
    need(actual[0] == actual[1] and len(actual[0]) == 337 and actual[0].keys()-old.keys() == ADDED and
         not old.keys()-actual[0].keys(), 'identical 337 files and exactly three additions')
    changed = sorted(path for path in old if old[path] != actual[0][path])
    need(changed == ['build-manifest.json','current-candidate.gba','current-candidate.json'], 'only three shared paths changed')
    for path,digest in ARTIFACTS.items(): need(actual[0][path] == digest, 'exact artifact '+path)
    old_manifest = json.loads(read(historical[0]/'build-manifest.json'))
    closures = []
    for directory in builds:
        manifest = json.loads(read(directory/'build-manifest.json'))
        need(manifest.keys()-old_manifest.keys() == {'type8_reaction_tables'} and not old_manifest.keys()-manifest.keys(),
             'one new metadata section only')
        need(manifest['type8_reaction_tables'] == META, 'bounded static metadata claims')
        for key,value in old_manifest.items():
            if key != 'layers': need(manifest[key] == value, 'prior metadata unchanged '+key)
        entries = []
        for key,subdir,const in [('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),
                                ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),
                                ('layers','','EXPECTED_LAYERS')]:
            need(manifest[key] == expected[const], 'literal manifest closure '+key)
            for name,digest in manifest[key].items():
                need(Path(name).name == name and sha(read(directory/subdir/name)) == digest, 'actual asset/layer closure '+name)
                entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
        need(len(entries) == 129, 'all 129 manifest entries')
        closures.append(entries)
        inverse_rom(read(directory/'campaign-progress-consumers.gba'), read(directory/'current-candidate.gba'),
                    json.loads(read(directory/'current-candidate.json')))
    need([inventory(d) for d in builds] == actual and all(inventory(d) == old for d in historical),
         'fresh and historical inventories stable after audit')
    for path,digest in pins.items(): need(sha(read(ROOT/path)) == digest, 'sources unchanged after audit '+path)
    report.update(status='TYPE8_TWO_BUILD_INVENTORY_PASS', files_each=337, manifest_entries_each=129,
                  builds=[d.relative_to(ROOT).as_posix() for d in builds],sha256_by_relative_path=actual[0],source_tool_sha256=pins,
                  manifest_closures=closures, changed_shared_v80_paths=changed, baseline_audit_sha256=PRIOR_SHA,
                  whole_new_layer_inverse=True, previous_334_artifacts_preserved=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--build-a', type=Path)
    parser.add_argument('--build-b', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    prior,pins,expected,result = preflight()
    if args.preflight:
        need(not args.root_completed and not args.build_a and not args.build_b, 'preflight excludes fresh outputs')
    else:
        audit(args,prior,pins,expected,result)
    result['checker_sha256'] = sha(read(Path(__file__)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x',encoding='utf-8',newline='\n') as output:
        json.dump(result,output,indent=2)
        output.write('\n')
    print(result['status'],sha(read(args.report)))
