"""Check AI main wiring, whole predecessor inverse and fresh inventories."""
import argparse
import ast
import json
from pathlib import Path
import struct
from verify_id13_main_inventory import need, sha, read, inventory

ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = 'tools/build_current_candidate.py'
MAIN = 'BADCCD5949EBBD04C8AF2DF4FAD20D8868DD492061F3079E0E16A80B08B948A6'
OLD_MAIN = '1665CA2BD6E562662577A6102F8F2656946E0E92B53836576E9ACCFC37BD0A1B'
OLD = '75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
FINAL = 'DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
OLD_MANIFEST = '06BEDDA94A27448B7AA8758F68D328690D50E63D75A5E4C9DDE35C0307FD0230'
MANIFEST = '2645FA80910F747BEB4A07239645449536BCFA51652194D191749CF03DF063B3'
GATE = 'B1B21A1C119028B2EBD70602BCCB82F6580CF02A38932E69EB58187A7B885FC7'
PRIOR = ROOT / 'build/type8-main-inventory-20261117/final.json'
PRIOR_SHA = 'B00CFE9AE706A660C6A4DCFA61123440E0DD9B1EC9074C92D7D273727C4776F9'
SOURCE_PATH = Path.home() / 'Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc'
SOURCE_SHA = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PINS = {
    MAIN_PATH: MAIN,
    'tools/build_character_ai_tables.py': '3F8613A6697E2CFFB0112F1C699415A793EACDA7242790C8D30C6C9662691EC0',
    'tools/verify_character_ai_tables.py': '2A7FA8725CCF3BDD396060AA6A78DD83D9A22370618990DC1D1937A65C5237A1',
    'tools/verify_type8_main_inventory.py': 'D81CCF6764A6D77C7D5DDE11756CD19DC10297480DDCFDFCBA785AAC61E9CE15',
    'tools/verify_id13_main_inventory.py': '596A662F1BA9BFD2B0F6F75059D3A86FBB8029195F35355A1A6DBF50B47E73B2',
}
ARTIFACTS = {
    'character-type8-tables.gba': OLD,
    'character-type8-tables.json': OLD_MANIFEST,
    'current-candidate.gba': FINAL,
    'current-candidate.json': MANIFEST,
    'intermediate/character-ai-tables-verification.json': GATE,
}
ADDED = set(ARTIFACTS) - {'current-candidate.gba', 'current-candidate.json'}
META = {'verification_sha256': GATE, 'parameter_rows': 10, 'parameter_bytes_per_row': 17,
        'behavior_rows': 10, 'behavior_bytes_per_row': 384,
        'action_records': 264, 'action_bytes_per_record': 18,
        'declared_bytes': 8890, 'changed_bytes': 8128, 'new_RAM_bytes': 0,
        'dedicated_stage7_boss_skips_ordinary_initializer': True,
        'retained_native_source_exception': 'action42 +0C input mask007E instead of sourceFF7E',
        'actual_runtime_verified': False, 'whole_campaign_runtime_verified': False, 'final_port_complete': False}
OWNERS = ["output / 'evolution-music.json'", "output / 'evolution-transition.json'",
          "output / 'id13-air-relaunch.json'", "output / 'campaign-stage-progression.json'",
          "output / 'campaign-progress-consumers.json'", "output / 'character-type8-tables.json'"]
CALLS = {
    'build_character_ai_tables.py': ["'--before'", 'character_type8', "'--gba'", 'args.gba',
        "'--old'", 'args.wsc10', "'--source'", 'args.wsc15', "'--owners'", *OWNERS,
        "'--output'", 'candidate', "'--manifest'", "output / 'current-candidate.json'"],
    'verify_character_ai_tables.py': ["'--before'", 'character_type8', "'--after'", 'candidate',
        "'--source'", 'args.wsc15', "'--old'", 'args.wsc10', "'--gba'", 'args.gba',
        "'--owners'", *OWNERS, "'--report'", 'character_ai_review'],
}
PARAM_REFS = (0xC7140,0xC714C,0xC7154,0xC715C,0xC7164,0xC716C,0xC7174,
              0xC717C,0xC7184,0xC718C,0xC7194,0xC719C,0xC71A4,0xC71AC,0xC71B4)
ACTION_REFS = {0xC6A2C:14,0xC6A3C:0,0xC6B2C:0,0xC6B34:0,0xC6BB4:16,0xC6BB8:17,0xC6BBC:16}
SPANS = {0xD88800:170,0xD888AC:32,0xD88900:3840,0xD89800:4752,0xC6D68:4,
         **{a:4 for a in PARAM_REFS},0xC658C:4,**{a:4 for a in ACTION_REFS}}



def verify_main(raw):
    need(sha(raw) == MAIN and b'\r\n' in raw and b'\n' not in raw.replace(b'\r\n', b''), 'frozen CRLF main')
    tree = ast.parse(raw)
    expected = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id.startswith('EXPECTED_')}
    need(expected['EXPECTED_LAYERS']['character-type8-tables.gba'] == OLD and
         expected['EXPECTED_LAYERS']['current-candidate.gba'] == FINAL, 'explicit predecessor and final image closure')
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    variables = {'character_type8': "output / 'character-type8-tables.gba'",
                 'character_ai_review': "intermediate / 'character-ai-tables-verification.json'"}
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
        if call.func.id == 'require_hash' and isinstance(arg, ast.Name) and arg.id == 'character_ai_review':
            need(arg.id not in gates, 'one independent gate')
            gates[arg.id] = ast.literal_eval(call.args[1])
            removed.append(node)
    need(bindings == variables and calls == CALLS and gates == {'character_ai_review': GATE} and len(removed) == 5,
         'exact new calls, both paths, all six owners and independent hash gate')
    lines = {i for node in removed for i in range(node.lineno-1, node.end_lineno)}
    metadata = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in ('character_ai_tables', 'character-type8-tables.gba'):
                    if key.value == 'character_ai_tables': metadata.append(ast.literal_eval(value))
                    lines.update(range(key.lineno-1, value.end_lineno))
    need(metadata == [META], 'new metadata is exact and static-only')
    inverse = b''.join(line for i, line in enumerate(raw.splitlines(keepends=True)) if i not in lines)
    changes = [
        (b'"--output", character_type8,\r\n        "--manifest", output / "character-type8-tables.json"',
         b'"--output", candidate,\r\n        "--manifest", output / "current-candidate.json"'),
        (b'"--before", campaign_consumers, "--after", character_type8,',
         b'"--before", campaign_consumers, "--after", candidate,'),
        (FINAL.encode(), OLD.encode()),
    ]
    for new, old in changes:
        need(inverse.count(new) == 1, 'unique predecessor retarget')
        inverse = inverse.replace(new, old)
    need(sha(inverse) == OLD_MAIN, 'complete main inverse to1665 with every prior call/gate preserved')
    return expected


def inverse_rom(before, after, manifest):
    need(len(before)==len(after)==0x1000000 and sha(before)==OLD and sha(after)==FINAL, 'complete pinned layer')
    need(len(manifest['writes'])==28 and {w['offset']:w['size'] for w in manifest['writes']}==SPANS, 'exact28 declared spans')
    source=read(SOURCE_PATH)
    need(sha(source)==SOURCE_SHA,'original source data identity')
    planned=bytearray(before)
    planned[0xD88800:0xD888AA]=source[0x782970:0x782A1A]
    planned[0xD88900:0xD89800]=source[0x74EB2A:0x74FA2A]
    actions=bytearray(source[0x74D89A:0x74EB2A]);actions[42*18+13]=0
    planned[0xD89800:0xD8AA90]=actions
    planned[0xD888AC:0xD888CC]=bytes.fromhex('04802de500800fe10d0050e30500402208f028e104809de404002de527f9ccea')
    branch=0xEA000000|(((0xD888AC-0xC6D68-8)//4)&0xFFFFFF)
    planned[0xC6D68:0xC6D6C]=struct.pack('<I',branch)
    for at in PARAM_REFS: planned[at:at+4]=struct.pack('<I',0x08D88800)
    planned[0xC658C:0xC6590]=struct.pack('<I',0x08D88900)
    for at,offset in ACTION_REFS.items(): planned[at:at+4]=struct.pack('<I',0x08D89800+offset)
    need(bytes(planned)==after,'whole image independently reconstructed from original source and literal helper encoding')
    restored=bytearray(after)
    for w in manifest['writes']:
        at,size=w['offset'],w['size']
        need(before[at:at+size]==bytes.fromhex(w['before_hex']) and after[at:at+size]==bytes.fromhex(w['after_hex']),'every declared byte exact')
        restored[at:at+size]=before[at:at+size]
    need(bytes(restored)==before and sum(x!=y for x,y in zip(before,after))==8128 and sum(SPANS.values())==8890,
         'whole75BD inverse8890declared8128changed')


def preflight():
    raw = read(PRIOR)
    need(sha(raw) == PRIOR_SHA, 'frozen v81 complete audit')
    prior = json.loads(raw)
    need((prior['status'], prior['files_each'], prior['manifest_entries_each'], prior['final_sha256']) ==
         ('TYPE8_TWO_BUILD_INVENTORY_PASS', 337, 129, OLD), 'completed predecessor closure')
    pins = {**prior['source_tool_sha256'], **PINS}
    for path, digest in pins.items(): need(sha(read(ROOT/path)) == digest, 'unchanged source '+path)
    expected = verify_main(read(ROOT/MAIN_PATH))
    isolated = {**prior['isolated_inputs'],
        'build/character-ai-tables-v82-20261117/component.gba': FINAL,
        'build/character-ai-tables-v82-20261117/component.json': MANIFEST,
        'build/character-ai-independent-final-20261117/report.json': GATE}
    for path, digest in isolated.items(): need(sha(read(ROOT/path)) == digest, 'frozen isolated artifact '+path)
    inverse_rom(read(ROOT/'build/character-type8-tables-r2-20261117/component.gba'),
                read(ROOT/'build/character-ai-tables-v82-20261117/component.gba'),
                json.loads(read(ROOT/'build/character-ai-tables-v82-20261117/component.json')))
    for path in prior['builds']:
        need(inventory(ROOT/path) == prior['sha256_by_relative_path'], 'all 337 historical files remain unchanged')
    report = dict(status='CHARACTER_AI_MAIN_PREFLIGHT_PASS', main_sha256=MAIN, whole_main_inverse_sha256=OLD_MAIN,
                  isolated_inputs=isolated, final_sha256=FINAL, predicted_files_each=340, predicted_manifest_entries_each=130,
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
    need(actual[0] == actual[1] and len(actual[0]) == 340 and actual[0].keys()-old.keys() == ADDED and
         not old.keys()-actual[0].keys(), 'identical 340 files and exactly three additions')
    changed = sorted(path for path in old if old[path] != actual[0][path])
    need(changed == ['build-manifest.json','current-candidate.gba','current-candidate.json'], 'only three shared paths changed')
    for path,digest in ARTIFACTS.items(): need(actual[0][path] == digest, 'exact artifact '+path)
    old_manifest = json.loads(read(historical[0]/'build-manifest.json'))
    closures = []
    for directory in builds:
        manifest = json.loads(read(directory/'build-manifest.json'))
        need(manifest.keys()-old_manifest.keys() == {'character_ai_tables'} and not old_manifest.keys()-manifest.keys(),
             'one new metadata section only')
        need(manifest['character_ai_tables'] == META, 'bounded static metadata claims')
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
        need(len(entries) == 130, 'all 130 manifest entries')
        closures.append(entries)
        inverse_rom(read(directory/'character-type8-tables.gba'), read(directory/'current-candidate.gba'),
                    json.loads(read(directory/'current-candidate.json')))
    need([inventory(d) for d in builds] == actual and all(inventory(d) == old for d in historical),
         'fresh and historical inventories stable after audit')
    for path,digest in pins.items(): need(sha(read(ROOT/path)) == digest, 'sources unchanged after audit '+path)
    report.update(status='CHARACTER_AI_TWO_BUILD_INVENTORY_PASS', files_each=340, manifest_entries_each=130,
                  builds=[d.relative_to(ROOT).as_posix() for d in builds],sha256_by_relative_path=actual[0],source_tool_sha256=pins,
                  manifest_closures=closures, changed_shared_v81_paths=changed, baseline_audit_sha256=PRIOR_SHA,
                  whole_new_layer_inverse=True, previous_337_artifacts_preserved=True)


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
