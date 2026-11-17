"""Close the stage11 Results main delta and two fresh build inventories."""
import argparse
import ast
import json
from pathlib import Path

from verify_id13_main_inventory import inventory, need, read, sha

ROOT = Path(__file__).resolve().parents[1]
MAIN = '0F116F63C0F49F91FE8A0D75227F675E87E4E9329BEE11284C21113E939EBD16'
OLD_MAIN = '7B293379F8EA36BC9AE8264561F7F2A59660F7A03A78857FA9D4C44FD7C54F3E'
BEFORE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
AFTER = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
GATE = 'F12C481BA9A03745E132AA10A4A9BA48C19898A2EDF35BBF7EFA735DC14511CC'
MANIFEST = '3056D7601D1C89C84FDE341EEFEAD50B68B27AE7F7415B9A047A2D0657FB6770'
OWNER = '162C4A9D2B8A684582EF2C3F22D8E60B6887E832BEBE4CB23730169C2198425C'
PRIOR = 'build/child-contact-main-inventory-20261117/final.json'
PRIOR_SHA = '79C9465AFC56F68CFA3AF3366F36723DFA99995757C1A422036D2E97C5169702'
PINS = {
    'tools/build_progression_integration.py': 'D469EA92B2C635EFA019B9AF2C1953D8F9400CB0694BA9E6C159CBBC2C104100',
    'tools/build_shoot_stage11_results_route.py': '2191E1B9092687F5BDB82CA691421CB9043A91CDC3D4B75F27BBF81082F6E313',
    'tools/mode23_completion_save.py': '0741223598DF038EE4DE569B600A90B731A687CDAC892FBE4FB00E9396D6D196',
    'tools/mode23_eligibility_storage.py': 'ECB077770FB4620F3EB678D86AC74F3BB3D7DBFA33013FBE20B3D2FB9166E873',
    'tools/mode23_linker.py': '20D276546966E63231AC23B4C1006B39BE64A0ACE8890F296DEFAC50D4F354EE',
    'tools/verify_gba_shoot_entry_capture.py': '970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D',
    'tools/verify_gba_shoot_entry_capture_v2.py': '4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68',
    'tools/verify_mode23_completion_save.py': 'D5DBFAF77571E8ADD6A4F81329CCDCAF3ABEFB73D2B07B0E2E05B402F9844232',
    'tools/verify_mode23_eligibility_storage.py': '7B62FC5120F832C69407D70E05592AFA3B7967115B13CE0ACBEB9DE93227A64A',
    'tools/verify_shoot_stage11_results_route.py': 'F90F23EF7A2D11042F64221F6AD3D5CC332EAEC0E702F95F658294572C508060',
}
META = dict(verification_sha256=GATE, declared_bytes=16, new_RAM_bytes=0,
            source_final_stages=[7, 11], native_transition_modes=[8, 12, 13, 11, 20, 3],
            ordinary_progress_table_preserved=True, actual_runtime_verified=False,
            final_port_complete=False)


def verify_main(raw):
    need(sha(raw) == MAIN, 'frozen main')
    tree = ast.parse(raw)
    excluded = set()
    for node in ast.walk(tree):
        remove = False
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            remove = node.targets[0].id in ('child_contact', 'results_route', 'results_route_review')
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.args:
                remove |= call.func.id == 'run' and isinstance(call.args[0], ast.Constant) and call.args[0].value in (
                    'build_shoot_stage11_results_route.py', 'verify_shoot_stage11_results_route.py')
                remove |= call.func.id == 'require_hash' and isinstance(call.args[0], ast.Name) and call.args[0].id == 'results_route_review'
            if isinstance(call.func, ast.Attribute) and call.func.attr == 'replace':
                remove |= ast.unparse(call.func.value) in ("results_route / 'component.gba'", "results_route / 'manifest.json'")
        if remove:
            excluded.update(range(node.lineno - 1, node.end_lineno))
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in ('shoot-child-contact.gba', 'shoot_stage11_results_route'):
                    if key.value == 'shoot_stage11_results_route':
                        need(ast.literal_eval(value) == META, 'bounded metadata')
                    excluded.update(range(key.lineno - 1, value.end_lineno))
    inverse = b''.join(line for n, line in enumerate(raw.splitlines(keepends=True)) if n not in excluded)
    for current, prior in ((b'"--output", child_contact,', b'"--output", candidate,'),
                           (b'"--manifest", output / "shoot-child-contact.json")', b'"--manifest", output / "current-candidate.json")'),
                           (b'"--after", child_contact,', b'"--after", candidate,'),
                           (b'"--installed", child_contact,', b'"--installed", candidate,'),
                           (AFTER.encode(), BEFORE.encode())):
        need(inverse.count(current) == 1, 'unique inverse replacement')
        inverse = inverse.replace(current, prior)
    need(sha(inverse) == OLD_MAIN, 'whole main inverse to v87')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-a', type=Path, required=True)
    p.add_argument('--build-b', type=Path, required=True)
    p.add_argument('--root-completed', action='store_true', required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    need(not a.report.exists(), 'fresh report')
    prior_raw = read(ROOT / PRIOR)
    need(sha(prior_raw) == PRIOR_SHA, 'verified v87 baseline')
    prior = json.loads(prior_raw)
    verify_main(read(ROOT / 'tools/build_current_candidate.py'))
    old = prior['sha256_by_relative_path']
    need(len(old) == 356, '356 baseline artifacts')
    historic = [(ROOT / path).resolve() for path in prior['builds']]
    dirs = [a.build_a.resolve(), a.build_b.resolve()]
    need(len(set(dirs)) == 2 and not set(dirs) & set(historic) and all(d.parent == ROOT / 'build' for d in dirs), 'fresh distinct build dirs')
    added = {'shoot-child-contact.gba': BEFORE, 'shoot-child-contact.json': OWNER,
             'intermediate/shoot-stage11-results-route-verification.json': GATE}
    outputs = [inventory(d) for d in dirs]
    need(outputs[0] == outputs[1] and len(outputs[0]) == 359, '359 identical files')
    current = outputs[0]
    need(current.keys() - old.keys() == added.keys() and not old.keys() - current.keys(), 'exact three additions')
    need(sorted(k for k in old if current[k] != old[k]) == ['build-manifest.json', 'current-candidate.gba', 'current-candidate.json'], 'only three historical paths changed')
    for path, digest in {**added, 'current-candidate.gba': AFTER, 'current-candidate.json': MANIFEST}.items():
        need(current[path] == digest, 'artifact ' + path)
    for d in historic:
        need(inventory(d) == old, 'historical files unchanged')
    previous_manifest = json.loads(read(historic[0] / 'build-manifest.json'))
    for d in dirs:
        manifest = json.loads(read(d / 'build-manifest.json'))
        need(manifest.pop('shoot_stage11_results_route') == META, 'new metadata only')
        need(manifest['layers'].pop('shoot-child-contact.gba') == BEFORE, 'preserved prior final layer')
        need(manifest['layers']['current-candidate.gba'] == AFTER, 'new final layer')
        manifest['layers']['current-candidate.gba'] = BEFORE
        need(manifest == previous_manifest, 'all previous metadata preserved')
        before, after = read(d / 'shoot-child-contact.gba'), bytearray(read(d / 'current-candidate.gba'))
        after[0x89538:0x8953C] = before[0x89538:0x8953C]
        after[0xD8CB20:0xD8CB2C] = before[0xD8CB20:0xD8CB2C]
        need(bytes(after) == before, 'whole installed layer inverse')
    pins = dict(prior['source_tool_sha256'], **PINS, **{'tools/build_current_candidate.py': MAIN})
    for path, digest in pins.items():
        need(sha(read(ROOT / path)) == digest, 'source pin ' + path)
    isolated = dict(prior['isolated_inputs'], **{
        'build/shoot-stage11-results-route-20261117-r2/component.gba': AFTER,
        'build/shoot-stage11-results-route-20261117-r2/manifest.json': MANIFEST,
        'build/shoot-stage11-results-route-qa-20261117-r2/portable.json': GATE})
    for path, digest in isolated.items():
        need(sha(read(ROOT / path)) == digest, 'isolated artifact ' + path)
    result = dict(status='STAGE11_RESULTS_TWO_BUILD_INVENTORY_PASS', main_sha256=MAIN,
                  whole_main_inverse_sha256=OLD_MAIN, baseline_audit_sha256=PRIOR_SHA,
                  final_sha256=AFTER, files_each=359, manifest_entries_each=136,
                  builds=[d.relative_to(ROOT).as_posix() for d in dirs],
                  sha256_by_relative_path=current, source_tool_sha256=pins,
                  isolated_inputs=isolated, mandatory_gate=GATE,
                  old_semantic_suites_rerun=False, emulator_launched=False,
                  checker_sha256=sha(read(Path(__file__))))
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8', newline='\n')
    print(result['status'], sha(read(a.report)))


if __name__ == '__main__':
    main()
