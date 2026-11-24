"""Check the final eligible scene against the three reviewed component layers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import unpack_from
from types import FunctionType

import verify_mode23_eligibility_storage as fixture
import verify_shoot_caller_resident as scanner
from verify_mode23_completion_save import need, sha


ROOT = Path(__file__).resolve().parents[1]
BUS = 0x08000000
PLACE = (0xD8D200, 0xD8D2E8)
CODE = BUS + PLACE[0]
RESULT_SPANS = ((0x89538, 0x8953C), (0xD8CB20, 0xD8CB2C))
FINAL_WRITES = (PLACE, (0x1F9C4, 0x1F9C8), (0x8B394, 0x8B398))
EXPORTS = dict(m23_eligibility_read=CODE, m23_eligibility_result_stage=CODE + 0x4C,
               m23_eligibility_commit_after_clear=CODE + 0x58, m23_eligibility_reset_then_save=CODE + 0x90)
IDENTITY = {
    'base': ('build/shoot-child-contact-20261117/component.gba',
             '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'),
    'owner': ('build/shoot-child-contact-20261117/manifest.json',
              '162C4A9D2B8A684582EF2C3F22D8E60B6887E832BEBE4CB23730169C2198425C'),
    'results': ('build/shoot-stage11-results-route-20261117-r2/component.gba',
                'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'),
    'scene': ('build/mode23-scene-v88-r3-20261117/component.gba',
              'B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'),
    'scene_manifest': ('build/mode23-scene-v88-r3-20261117/manifest.json',
                       '3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B'),
    'final': ('build/mode23-eligible-scene-20261117/component.gba',
              '36A126206237A5C6A0670105C8023B5237FFA055733EF7795AE2A3A42A5E3B8A'),
    'manifest': ('build/mode23-eligible-scene-20261117/manifest.json',
                 '819D898DA7CD53AE19556FE6AD48DBBEEAB863F9B13EEAABCD7A6513CD70C02D'),
    'previous_qa': ('build/mode23-eligibility-storage-qa-20261117/report.json',
                    'B4442F0F575778A597EA4AADA6C40D908762BA7A6688ACCD16FCC48752F4B755'),
    'builder': ('tools/build_mode23_eligible_scene.py',
                '2E9E437B38230185108DD62FA924631E0EBA83D1F2F35695DF0B70AA30A0D449'),
    'fixture': ('tools/verify_mode23_eligibility_storage.py',
                '7B62FC5120F832C69407D70E05592AFA3B7967115B13CE0ACBEB9DE93227A64A'),
}


def exact_input(name):
    path, digest = IDENTITY[name]
    data = (ROOT / path).read_bytes()
    need(sha(data) == digest, f'Exact reviewed artifact {path}')
    return data


def differences(before, after, declared, label):
    reverted = bytearray(after)
    count = 0
    for lo, hi in declared:
        need(0 <= lo < hi <= len(before), label + ' bounds of declared edit')
        original, installed = before[lo:hi], after[lo:hi]
        count += sum(a != b for a, b in zip(original, installed, strict=True))
        need(original != installed, label + ' actual change in each extent')
        reverted[lo:hi] = original
    need(bytes(reverted) == before, label + ' complete whole-image inverse')
    return count


def require_disjoint(spans):
    ordered = sorted(spans)
    need(all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'Declared layers have no overlapping writes')


def branch(rom, offset, op):
    word = unpack_from('<I', rom, offset)[0]
    need(word >> 24 == op, f'Typed ARM branch at {offset:06X}')
    field = word & 0xFFFFFF
    return BUS + offset + 8 + 4 * (field - 2 * (field & 0x800000))


def composition(base, results, scene, final, sm, fm, owner):
    need(len(base) == len(results) == len(scene) == len(final) == 0x1000000, 'Full cartridge extents')
    need(owner['reservations'] == [[0xD8C800, 0xD8CE00]], 'Reviewed predecessor child-contact reservations')
    scene_writes = [(row['offset'], row['offset'] + row['size']) for row in sm['writes']]
    need(len(scene_writes) == 187 and sum(hi - lo for lo, hi in scene_writes) == 264294, 'All registered r3 scene writes')
    require_disjoint(scene_writes + list(RESULT_SPANS) + list(FINAL_WRITES))
    for row, (lo, hi) in zip(sm['writes'], scene_writes, strict=True):
        need(sha(base[lo:hi]) == row['before_sha256'] and sha(scene[lo:hi]) == row['after_sha256'],
             'Actual scene bytes and predecessor span ' + row['label'])
    scene_changed = differences(base, scene, scene_writes, 'Mode 23 scene')
    results_changed = differences(base, results, RESULT_SPANS, 'Stage 11 Results')
    combined = bytearray(scene)
    for lo, hi in RESULT_SPANS:
        combined[lo:hi] = results[lo:hi]
    before = bytes(combined)
    need(sha(before) == fm['composed_before_eligibility_sha256'], 'Exact composed predecessor')
    written_spans = [(row['offset'], row['offset'] + row['size']) for row in fm['writes']]
    need(written_spans == list(FINAL_WRITES), 'Three exact eligibility writes')
    for row, (lo, hi) in zip(fm['writes'], FINAL_WRITES, strict=True):
        need(row['before_hex'] == before[lo:hi].hex() and row['after_hex'] == final[lo:hi].hex(), 'Exact old/new bytes in each write')
    eligibility_changed = differences(before, final, FINAL_WRITES, 'Persistent stage 11 eligibility')
    need(differences(base, final, scene_writes + list(RESULT_SPANS) + list(FINAL_WRITES), 'All three layers') ==
         scene_changed + results_changed + eligibility_changed, 'Three disjoint edits compose exactly')
    need(fm['code_span'] == list(PLACE) and fm['exports'] == EXPORTS and fm['new_global_RAM_bytes'] == 0
         and fm['stage_predicate_reused'] == [lo for lo, _ in RESULT_SPANS]
         and fm['menu_exposed'] is fm['actual_game_execution'] is fm['final_port_complete'] is False,
         'Bounded eligibility metadata')
    reservations = [tuple(row) for row in owner['reservations']] + [tuple(sm['root_entry_reservation']),
                   (sm['code']['start'], sm['code']['reserved_end'])]
    reservations += [(item['start'], item['end']) for item in sm['allocations']]
    lo, hi = PLACE
    need(all(end <= lo or hi <= start for start, end in reservations), 'No owned or reserved extent reused by the eligibility bridge')
    need(before[lo:hi] == b'\xff' * (hi - lo), 'All 232 predecessor bytes are erased')
    census = FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=(PLACE,)), argdefs=scanner.inbound.__defaults__)
    need(census(before) == [] and fm['strict_inbound_count'] == 0, 'Strict full-ROM inbound census over the actual placement')
    need(branch(final, 0x89538, 0xEA) == BUS + 0xD8CB20
         and final[0xD8CB20:0xD8CB2C] == results[0xD8CB20:0xD8CB2C]
         and branch(final, 0xD8CB28, 0xEA) == BUS + 0x8953C, 'Existing reachable stage-7/11 adapter remains byte exact')
    need(branch(final, 0x8B394, 0xEA) == EXPORTS['m23_eligibility_commit_after_clear']
         and branch(final, 0x1F9C4, 0xEB) == EXPORTS['m23_eligibility_reset_then_save'], 'Precisely linked success and reset hooks')
    for module, digest in fm['module_pins'].items():
        need(sha((ROOT / 'tools' / module).read_bytes()) == digest, 'Frozen composed build dependency ' + module)
    return before, dict(scene_rows=187, scene_declared_bytes=264294, scene_changed_bytes=scene_changed,
                        results_declared_bytes=16, results_changed_bytes=results_changed, eligibility_writes=list(FINAL_WRITES),
                        eligibility_declared_bytes=240, eligibility_changed_bytes=eligibility_changed,
                        strict_predecessor_inbound=0, images_inverse_to_frozen_base=True)


def fixture_at_actual_code(final, predecessor, previous, manifest):
    lo, hi = PLACE
    need(hi - lo == previous['code_bytes'] and sha(final[lo:hi]) == previous['linked_code_sha256'],
         'All installed executable and data bytes equal the prior independent ARM fixture')
    for name, prior in previous['linkage']['native_veneers'].items():
        actual = manifest['link']['native_veneers'][name]
        address = CODE + prior['address'] - fixture.CODE
        need(actual == dict(address=address, target=prior['target'])
             and unpack_from('<II', final, address - BUS) == (0xE51FF004, prior['target']), 'Installed native API veneer ' + name)
    base_fixture = fixture.EEPROMFixture
    relocated_device = FunctionType(base_fixture.device.__code__, dict(base_fixture.device.__globals__, CODE=CODE))

    class RelocatedEEPROM(base_fixture):
        device = relocated_device

    def call(func, *args):
        placed = FunctionType(func.__code__, dict(func.__globals__, EEPROMFixture=RelocatedEEPROM), argdefs=func.__defaults__)
        return placed(*args)

    readers = call(fixture.reader, final, EXPORTS)
    compare = call(fixture.result_gate, final)
    results = [(7, fixture.CLOSED), (11, fixture.CLOSED), (11, fixture.MARKER),
               (10, fixture.CLOSED), (11, fixture.CLOSED, False),
               (11, fixture.CLOSED, True, True), (7, fixture.CLOSED, True, False, 1)]
    results += [(11, fixture.CLOSED, True, False, 0, block) for block in (0, 12, 24, 26)]
    for args in results:
        checked = call(fixture.play_result, final, *args)
        installed_marker = bytes(checked.blocks[208:216])
        reader = RelocatedEEPROM(final, installed_marker)
        registers = reader.r[:]
        reader.drive(EXPORTS['m23_eligibility_read'], {reader.r[14]})
        need(reader.r[0] == int(installed_marker == fixture.MARKER) and reader.r[1:15] == registers[1:15]
             and reader.io == [('read', 26, None)], 'New reader object observes only the actual persisted marker')
    resets = [(0,), (1,), (0, 'checksum'), (0, 'signature'), (1, '', 26)]
    for reset in resets:
        call(fixture.reset_test, final, predecessor, EXPORTS, *reset)
    need(fixture.CODE == 0x08FF0000 and fixture.EEPROMFixture is base_fixture, 'Frozen fixture globals unchanged')
    return dict(installed_adapter_sha256=previous['linked_code_sha256'], installed_entry=CODE,
                reader_cases=readers, unchanged_stage_predicate_cases=compare, result_cases=len(results),
                reload_after_result_cases=len(results), record_init_cases=len(resets), fixture_device_modeled=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'Fresh report')
    for name in ('builder', 'fixture'):
        exact_input(name)
    base, results, scene, final = (exact_input(name) for name in ('base', 'results', 'scene', 'final'))
    sm, fm, owner, previous = (json.loads(exact_input(name)) for name in ('scene_manifest', 'manifest', 'owner', 'previous_qa'))
    before, comparison = composition(base, results, scene, final, sm, fm, owner)
    transactions = fixture_at_actual_code(final, before, previous, fm)
    report = dict(status='MODE23_ELIGIBLE_SCENE_COMPOSITION_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  frozen_inputs={name: digest for name, (_, digest) in IDENTITY.items()},
                  inverses=comparison, relocated_ARM=transactions, actual_BizHawk_execution=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
