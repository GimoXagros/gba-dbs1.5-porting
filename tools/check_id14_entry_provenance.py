"""Verify nested fixed-entry Lua composition and the targeted source/native entry row."""

import argparse
import json
import struct
import types
from pathlib import Path

import check_id14_openbus_wrapper as existing

ENTRY = 'bizhawk_probe_id14_entry_provenance.lua'
OBSERVER = 'bizhawk_observe_evolution_entry_provenance.lua'
ENTRY_SHA = '0A5742C9B04130EC3418F5C67A8FC7D471343726FE18693066903F316EF99F78'
OBSERVER_SHA = 'C942791335CDA9F7DE23411F5EC9069DC1F32D1F431C3B607775F0F4EDB8C93C'
OPS = {0x835A1EC: 0xE92D0020, 0x835A1FC: 0xE28DD00C, 0x8352830: 0xE1D480B4,
       0x8353C98: 0xE594800C, 0x8353C9C: 0xE3580000, 0x8353CA8: 0xE59F10D4,
       0x8353C70: 0xE1C100B4, 0x8353D24: 0xE1C100B4}


def check_target(source, fixed):
    assert existing.sha(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert existing.sha(fixed) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    base = 0x08000000
    assert all(struct.unpack_from('<I', fixed, address - base)[0] == opcode for address, opcode in OPS.items())
    source_p1, native_p1, event = 0x368FF0, 0x086184A0, 115
    assert struct.unpack_from('<H', source, 0x7679DE) == (event,)
    table, = struct.unpack_from('<I', fixed, 0x835A210 - base)
    assert table == 0x08D3F000 and struct.unpack_from('<H', fixed, table - base + 14 * 2) == (event,)
    source_row = source_p1 + struct.unpack_from('<H', source, source_p1)[0] + event * 8
    native_row = struct.unpack_from('<I', fixed, native_p1 - base)[0] + event * 16
    assert (source_row, native_row) == (0x36938C, 0x08618BD8)
    count, command, metadata, event_b = struct.unpack_from('<4H', source, source_row)
    assert (count, command, metadata, event_b) == (2, 0x1F24, 0x2298, 0)
    ncount, ncommand, nmetadata, nevent_b = struct.unpack_from('<4I', fixed, native_row - base)
    assert (ncount, ncommand, nmetadata, nevent_b) == (count, 0x0861B0A8, 0x0861B258, event_b)
    assert source[source_p1 + command:source_p1 + command + 12].hex() == '03ff1d002a00010000000000'
    assert fixed[ncommand - base:ncommand - base + 16].hex() == '02ff1d002a0001000000000000000000'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    root = existing.ROOT
    scripts = {name: (root / 'tools' / name).read_bytes() for name in (ENTRY, OBSERVER) + existing.NAMES[2:]}
    assert (existing.sha(scripts[ENTRY]), existing.sha(scripts[OBSERVER])) == (ENTRY_SHA, OBSERVER_SHA)
    check_target((Path.home() / 'Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc').read_bytes(),
                 (root / 'build/evolution-transition-tables-20261116/component.gba').read_bytes())

    # The two wrappers have the same outer boundary contract with distinct witnesses and outcome names.
    check = existing.CHECK
    for old, new in ((existing.NAMES[0], ENTRY), ('@openbus-observer', '@entry-provenance-observer'),
                     ('openbus_evidence', 'entry_provenance'),
                     ('collision-openbus-producer-observed', 'evolution-entry-provenance-observed')):
        assert old in check
        check = check.replace(old, new)
    sources = ','.join(f'[{existing.quote(("W:/tools/" + name).encode())}]={existing.quote(data)}'
                       for name, data in scripts.items())
    host = existing.host
    run = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK='local sources={' + sources + '}\n' + check))
    run('', '', '')
    result = dict(status='ID14_FIXED_ENTRY_COMPOSITION_PASS', dependency_sha256={n: existing.sha(s) for n, s in scripts.items()},
                  checker_sha256=existing.sha(Path(__file__).read_bytes()), exact_effective_inverse=True,
                  boundary_cases=4, marker_after_observer_finish=True, fixed_hook_opcodes=len(OPS),
                  event=115, source_row='36938C', native_row='08618BD8', source_expected_command_B=0,
                  emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(result, indent=2) + '\n').encode()
    with args.report.open('xb') as output:
        output.write(payload)
    print(result['status'], existing.sha(payload))


if __name__ == '__main__':
    main()
