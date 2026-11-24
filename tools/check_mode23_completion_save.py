"""Execute completion adapter, native sanitizer and sorter; capture EEPROM handoff."""
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
from mode23_completion_save import assembly, sanitizer_patches

CODE, CONFIG, BUFFER = 0x08E00000, 0x03002310, 0x03001120


class SaveMachine(Machine):
    def put(self, at, value, size=4, log=False):
        super().put(at, value, size, log)
        if at == 0x040000DE:
            assert size == 2 and value == 0x8400
            source, dest = self.get(0x040000D4), self.get(0x040000D8)
            count = self.get(0x040000DC, 2)
            assert count == 2
            assert source in (BUFFER + 0x14, BUFFER + 0x1C, BUFFER + 0x24, 0x03003D10)
            assert dest in (BUFFER + 0x14, BUFFER + 0x1C, BUFFER + 0x24, 0x03003D10)
            for i in range(count):
                super().put(dest + i * 4, self.get(source + i * 4), 4, True)


def sha(v):
    return hashlib.sha256(v).hexdigest().upper()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('source', 'native', 'report'):
        p.add_argument('--' + n, type=Path, required=True)
    a = p.parse_args()
    assert not a.report.exists()
    source, native = a.source.read_bytes(), a.native.read_bytes()
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(assembly(source, native), CODE)[0])
    rom = bytearray(native)
    rom[CODE - 0x08000000:CODE - 0x08000000 + len(code)] = code
    for at, v in sanitizer_patches(native).items():
        rom[at:at + len(v)] = v
    cases = 0
    for permanent in range(64):
        for pending in (0, 0x10, 0x20, 0xFF):
            for flag in (0, 15):
                m = SaveMachine(rom, seed=11, flags=(flag << 28) | 31)
                for i in range(0xE8):
                    m.put(BUFFER + i, 0, 1)
                for i in range(0x30):
                    m.put(CONFIG + i, 0xA5, 1)
                m.put(CONFIG + 0x18, pending, 1)
                m.put(CONFIG + 0x19, permanent, 1)
                m.put(BUFFER + 0x10, 0xFFFF, 2)
                m.put(BUFFER + 0x12, 0xFFFF, 2)
                m.put(BUFFER + 0x64, 0xFFFF, 2)
                # First three records exercise the actual descending sorter.
                for i in range(10):
                    entry = BUFFER + 0x14 + 8 * i
                    m.put(entry, 1, 1)
                    m.put(entry + 1, (13, 14, 15)[i % 3], 1)
                    for j in range(3):
                        m.put(entry + 2 + j, 0x21 + i, 1)
                    m.put(entry + 6, 100 + i, 2)
                before = dict(m.mem)
                regs, sp = m.r[:14].copy(), m.r[13]
                writes = []

                def writer(vm):
                    writes.append(bytes(vm.get(BUFFER + i, 1) for i in range(0xC0)))

                m.services = {0x0801FC5C: writer}
                m.run(CODE, {m.r[14]}, max_steps=30000)
                assert m.r[:14] == regs and m.r[13] == sp
                assert m.get(CONFIG + 0x18, 1) == (pending | (0x10 & ~permanent))
                assert m.get(CONFIG + 0x19, 1) == permanent
                assert len(writes) == 1
                assert struct.unpack_from('<H', writes[0], 0x12)[0] == permanent
                assert m.get(BUFFER + 0x10, 2) == 0x3FFF
                assert m.get(BUFFER + 0x64, 2) == 0x1F
                assert sorted(m.get(BUFFER + 0x15 + 8 * i, 1) for i in range(10)) == [0] * 3 + [13] * 4 + [14] * 3
                scores = [m.get(BUFFER + 0x1A + 8 * i, 2) for i in range(3)]
                assert scores == [102, 101, 100], scores
                assert all(m.get(CONFIG + i, 1) == before[CONFIG + i] for i in range(0x30) if i != 0x18)
                assert all(m.get(BUFFER + i, 1) == before[BUFFER + i] for i in range(0xC0, 0xE8))
                cases += 1
    result = dict(status='MODE23_COMPLETION_SAVE_AUTHOR_PASS', cases=cases,
                  source_sha256=sha(source), native_sha256=sha(native),
                  module_sha256=sha((ROOT / 'tools/mode23_completion_save.py').read_bytes()),
                  checker_sha256=sha(Path(__file__).read_bytes()), linked_bytes=len(code),
                  linked_sha256=sha(code), actual_native=['0801FA98 sanitizer', '080C12EC sorter'],
                  patches={f'{k:08X}': v.hex() for k, v in sanitizer_patches(native).items()},
                  limits=['DMA3 immediate two-word copy is modeled at hardware-register writes',
                          'EEPROM writer is a typed capture fixture; no physical persistence check',
                          'No installed scene or emulator execution',
                          'E8 source record versus C0 native record ownership requires independent review'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
