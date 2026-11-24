"""Actual native dispatcher consumers, original routes and new mode23 selector."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_dispatch_tables import patches, selector_assembly

TABLE, CONSTRUCTOR, SELECTOR, CONFIG = 0x08E00000, 0x08E10000, 0x08E20000, 0x03002310


def sha(v):
    return hashlib.sha256(v).hexdigest().upper()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('source', 'native', 'report'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    source, native = a.source.read_bytes(), a.native.read_bytes()
    blob, changed = patches(source, native, TABLE, CONSTRUCTOR, SELECTOR)
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(selector_assembly(), SELECTOR)[0])
    rom = bytearray(native)
    for at, v in {**changed, TABLE - 0x08000000: blob, SELECTOR - 0x08000000: code}.items():
        rom[at:at + len(v)] = v
    cases = 0
    for mode in (*range(21), 23):
        for site, offset in ((0x080159E0, 0), (0x080159FC, 4), (0x08015A20, 4), (0x08015AD4, 8)):
            m = Machine(rom)
            m.r[1] = mode * 12
            m.run(site, {site + 8})
            expected = struct.unpack_from('<I', native, 0x15B70 + mode * 12 + offset)[0] if mode < 21 else (CONSTRUCTOR if offset == 4 else 0x080159B0)
            assert m.r[9] == expected if site != 0x08015A20 else m.r[0] == expected
            cases += 1

    def transition(image, mode, choice, submode, flags):
        m = Machine(image, seed=7, flags=0xA000001F)
        for i in range(0x30):
            m.put(CONFIG + i, 0, 1)
        for off, value in ((0, mode), (2, submode), (4, 1), (6, choice), (8, 0x1234), (0x1A, flags)):
            m.put(CONFIG + off, value, 2)
        m.r[5] = CONFIG
        m.r[13] -= 4
        m.put(m.r[13], m.r[14])
        callbacks = []
        m.services = {0x08012008: lambda vm: callbacks.append(vm.r[8])}
        m.run(0x08015AE4, {m.r[14]})
        return bytes(m.get(CONFIG + i, 1) for i in range(0x30)), callbacks

    for mode in range(21):
        for choice in range(5):
            for submode, flags in ((0, 0), (1, 0), (1, 0x1000)):
                assert transition(rom, mode, choice, submode, flags) == transition(native, mode, choice, submode, flags)
                cases += 1
    for mode, choice, expected in ((4, 5, 23), (23, 0, 20)):
        data, calls = transition(rom, mode, choice, 0, 0)
        assert struct.unpack_from('<H', data)[0] == expected
        assert data[4:10] == bytes(6) and calls == [0x080159B4]
        cases += 1
    for state in (0, 0x10):
        for flags in range(16):
            m = Machine(rom, seed=9)
            m.r[5] = 0x02010018
            m.put(m.r[5], state, 2)
            m.put(CONFIG + 0x1A, flags, 2)
            m.run(0x08081C64, {0x08081CB4})
            assert m.r[1] == (4 if state else 3 if flags & 2 else 5 if flags & 8 else 1)
            cases += 1
    for count in (0, 1, 9, 52):
        m = Machine(rom, seed=2)
        m.put(CONFIG, 23, 2)
        m.put(0x04000006, 160, 2)
        m.r[2] = count
        end = m.r[14]
        calls = []
        m.services = {0x08012008: lambda vm: calls.append(vm.r[8])}
        stop = m.run(0x080159B4, {CONSTRUCTOR, end})
        if count:
            assert stop == CONSTRUCTOR and m.r[2] == count
            m.run(m.r[14], {end})
            assert calls == [0x08015AB4]
        else:
            assert stop == end and m.get(0x03002308) == CONSTRUCTOR
            assert calls == [0x08015A48]
        cases += 1
    result = dict(status='MODE23_DISPATCH_AUTHOR_PASS', cases=cases,
                  source_sha256=sha(source), native_sha256=sha(native),
                  module_sha256=sha((ROOT / 'tools/mode23_dispatch_tables.py').read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()), table_bytes=len(blob),
                  selector_bytes=len(code), patch_bytes=sum(map(len, changed.values())),
                  limits=['In-memory placement only; no ROM reservation or menu exposure',
                          'Constructor and task-callback change are explicit fixtures',
                          'Modes21/22 remain unregistered; no claimed implementation',
                          'No game execution or task/palette ownership proof'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
