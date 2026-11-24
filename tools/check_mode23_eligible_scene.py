"""Rebind the frozen EEPROM device fixture to the installed eligibility code."""
import argparse
import json
from pathlib import Path

import verify_mode23_eligibility_storage as fixture


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--component', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    rom, raw = a.component.read_bytes(), a.manifest.read_bytes()
    assert fixture.sha(rom) == '36A126206237A5C6A0670105C8023B5237FFA055733EF7795AE2A3A42A5E3B8A'
    assert fixture.sha(raw) == '819D898DA7CD53AE19556FE6AD48DBBEEAB863F9B13EEAABCD7A6513CD70C02D'
    manifest = json.loads(raw)
    baseline = bytearray(rom)
    for row in manifest['writes']:
        at, size = row['offset'], row['size']
        assert rom[at:at+size] == bytes.fromhex(row['after_hex'])
        baseline[at:at+size] = bytes.fromhex(row['before_hex'])
    assert fixture.sha(baseline) == manifest['composed_before_eligibility_sha256']
    # The device fixture checks its ROM constant pointer against this link address.
    fixture.CODE = 0x08D8D200
    symbols = manifest['exports']
    assert symbols['m23_eligibility_read'] == fixture.CODE
    reads, stages = fixture.reader(rom, symbols), fixture.result_gate(rom)
    cases = [(7, fixture.CLOSED, True, False, 0, -1), (11, fixture.CLOSED, True, False, 0, -1),
             (11, bytes([255])*8, True, False, 0, -1), (7, fixture.MARKER, True, False, 0, -1),
             (11, fixture.CLOSED, False, False, 0, -1), (11, fixture.CLOSED, True, True, 0, -1),
             (7, fixture.CLOSED, True, False, 1, -1), (10, fixture.CLOSED, True, False, 0, -1),
             (15, fixture.CLOSED, True, False, 0, -1), (11, fixture.CLOSED, True, False, 0, 26)]
    cases += [(11, fixture.CLOSED, True, False, 0, block) for block in fixture.RECORD]
    for case in cases:
        fixture.play_result(rom, *case)
    for reset in [(0,), (1,), (0, 'checksum'), (0, 'signature'), (1, '', 26)]:
        fixture.reset_test(rom, baseline, symbols, *reset)
    report = dict(status='MODE23_ELIGIBLE_SCENE_RELOCATED_ARM_PASS', component_sha256=fixture.sha(rom),
                  manifest_sha256=fixture.sha(raw), read_cases=reads, stage_cases=stages,
                  result_cases=len(cases), reset_cases=5, actual_code_origin=fixture.CODE,
                  exports=symbols, fixture_sha256=fixture.sha(Path(fixture.__file__).read_bytes()),
                  checker_sha256=fixture.sha(Path(__file__).read_bytes()), emulator_executed=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print(report['status'], fixture.sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
