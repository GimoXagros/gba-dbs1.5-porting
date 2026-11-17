"""Independent bounded completion-save ABI, native transfer and source-owner check.

No installed ROM, physical EEPROM, save file, emulator, or main builder is changed.
Only the device block API and immediate DMA hardware are modeled; native service,
sanitizer, sorter, checksum, writer and reader instructions execute unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
from verify_shoot_static_companion_clear import Machine
from mode23_completion_save import assembly, sanitizer_patches

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
NATIVE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
BUFFER, CONFIG, CODE = 0x03001120, 0x03002310, 0x08E00000
SOURCE_RANGES = {
    (0x74B959, 0x74B981): '64813B8FAA047838FABC5F5549F169BD60F99E238231BFA7725A4145627F4FB6',
    (0x785FE1, 0x786091): 'ACC5B4581D07AE282E35AEA47E396948BFD5AA0F17666BB1A3A959FFB7D3F71F',
    (0x7860CF, 0x786147): 'D4861B6BB6EE391BD16ED49B2DAF6CC15D2050D04EFCB1BC37CA8B4EAAF08483',
    (0x77B588, 0x77B61A): '826A9BC72E05DA876ADB533E5AC4472D9AA5186469C51FEE53AFA100EE5A265E',
    (0x77856D, 0x7785B3): '0E0F9BEF4162340DEC6CCAA2A35E1425A4FFD5E89CB883E7728AF54C1C890BD3',
    (0x778629, 0x778678): '460EC2E94B3F80047EBD983CE0E6E210D5E8B4444C851197E174D8E8BD3DAB91',
    (0x774BB0, 0x774BD4): 'CDF405F5DC005E1B5A9B9BE76127F655F0783B67A71D3FA94603A6AF1C16B4C9',
    (0x784980, 0x784990): 'D1D8FF79ADD44071E5B2D91A21F571B073B7885BE4F96ECE51EE8D45E116E179',
    (0x7850E9, 0x78510E): 'CFC3D496525D38BA26767733566D6A0FDF5E418D368FDC8A6282E9F9AF62DC6E',
    (0x78518A, 0x7851A7): 'F03ECAD801E86B52E0CC7B9276E13B9FDE85C296C5C9D2558D3F9C683D6E1CBE',
}

def sha(b): return hashlib.sha256(b).hexdigest().upper()
def need(ok, why):
    if not ok: raise ValueError(why)
def dump(m, at, size): return bytes(m.get(at + i, 1) for i in range(size))
def fill(m, at, data):
    for i, byte in enumerate(data): m.put(at + i, byte, 1)

class StorageMachine(Machine):
    def __init__(self, rom, flags=31, fail=-1):
        super().__init__(rom, seed=47, flags=flags)
        self.blocks = bytearray((i * 29 + 71) & 255 for i in range(512))
        self.block_writes, self.block_reads, self.dmas = [], [], []
        self.fail = fail
        self.services = {0x0837DB54: self.write_block, 0x0837DB60: self.read_block}

    def write_block(self, vm):
        block, pointer = vm.r[0], vm.r[1]
        need(block < 25 and pointer == BUFFER + block * 8, 'native write extent')
        self.block_writes.append(block)
        vm.r[0] = 0x8000 if block == self.fail else 0
        if not vm.r[0]: self.blocks[block * 8:block * 8 + 8] = dump(vm, pointer, 8)

    def read_block(self, vm):
        block, pointer = vm.r[0], vm.r[1]
        need(block < 25 and pointer == BUFFER + block * 8, 'native read extent')
        self.block_reads.append(block)
        fill(vm, pointer, self.blocks[block * 8:block * 8 + 8])
        vm.r[0] = 0

    def put(self, at, value, size=4, log=False):
        super().put(at, value, size, log)
        if at == 0x040000DE:
            src, dst, count = self.get(0x040000D4), self.get(0x040000D8), self.get(0x040000DC, 2)
            allowed = {BUFFER + 0x14, BUFFER + 0x1C, BUFFER + 0x24, 0x03003D10}
            need(size == 2 and value == 0x8400 and count == 2 and src in allowed and dst in allowed,
                 'exact native sorter DMA transaction')
            self.dmas.append((src, dst, count))
            data = dump(self, src, 8)
            for i, byte in enumerate(data): super().put(dst + i, byte, 1, True)

def payload(seed):
    b = bytearray((i * 7 + seed) & 255 for i in range(0xC0))
    b[:16] = b'DIMPS Ver0.72  ' + bytes([0xA2])
    struct.pack_into('<HH', b, 0x10, 0xFFFF, 0xFFFF)
    struct.pack_into('<H', b, 0x64, 0xFFFF)
    for i in range(10):
        at = 0x14 + 8 * i
        b[at:at + 6] = bytes([0xFF, (12, 13, 14, 15, 127, 128, 255, 0, 1, 11)[i], 0x41, 0x42, 0x43, 0])
        struct.pack_into('<H', b, at + 6, (300, 9999, 301, 10000, 32767, 32768, 65535, 0, 200, 999)[i])
    return b

def source_model(b, permanent):
    b = bytearray(b)
    struct.pack_into('<H', b, 0x10, struct.unpack_from('<H', b, 0x10)[0] & 0x3FFF)
    struct.pack_into('<H', b, 0x64, struct.unpack_from('<H', b, 0x64)[0] & 0x1F)
    mask = 1
    for i in range(10):
        at = 0x14 + 8 * i
        # Source DX is reused by the name/score logic; it is not reloaded1
        # at the loop back edge. Native R3 retains this same behavior.
        b[at] &= mask & 255
        if b[at + 1] > 14: b[at + 1] = 0
        score = struct.unpack_from('<H', b, at + 6)[0]
        struct.pack_into('<H', b, at + 6, 200 if score & 0x8000 else min(score, 9999))
        mask = 0 if score & 0x8000 else 9999
    first = [bytes(b[0x14 + 8 * i:0x1C + 8 * i]) for i in range(3)]
    b[0x14:0x2C] = b''.join(sorted(first, key=lambda r: struct.unpack_from('<H', r, 6)[0], reverse=True))
    struct.pack_into('<H', b, 0x12, permanent)
    return b

def exercise(rom, permanent, flags, fail=-1):
    m = StorageMachine(rom, flags, fail)
    initial = payload(permanent)
    fill(m, BUFFER, initial + bytes(range(40)))
    fill(m, CONFIG, bytes([0x5A]) * 0x30)
    m.put(CONFIG + 0x18, 0xA5, 1); m.put(CONFIG + 0x19, permanent, 1)
    preserved_block25 = bytes(m.blocks[200:])
    regs, sp, end = m.r[:14].copy(), m.r[13], m.r[14]
    m.run(CODE, {end}, max_steps=30000)
    need(m.r[:14] == regs and m.r[13] == sp, 'adapter ABI')
    expected = source_model(initial, permanent)
    need(dump(m, BUFFER, 0xC0) == expected, 'source completion payload')
    need(m.get(CONFIG + 0x18, 1) == (0xA5 | (0x10 & ~permanent)), 'pending unlock')
    need(dump(m, BUFFER + 0xC4, 36) == bytes(range(4, 40)), 'native trailing bytes preserved')
    need(m.block_writes == list(range(25 if fail < 0 else fail + 1)), 'first failure terminates writer')
    need(bytes(m.blocks[200:]) == preserved_block25, 'Shoot block25 and later untouched')
    need(m.get(BUFFER + 0xC0) == sum(expected), 'native C0 checksum')
    if fail >= 0: return
    need(m.blocks[:0xC0] == expected, 'modeled persistent payload')
    fill(m, BUFFER, bytes([0xDD]) * 200)
    m.r[14] = end
    m.run(0x0801FCA8, {end}, max_steps=30000)
    need(m.block_reads == list(range(25)) and m.cpsr & 0x40000000, 'native reader checksum pass')
    need(dump(m, BUFFER, 0xC0) == expected, 'native reader retains bit5 and fighter13/14')
    m.r[1], m.r[14] = CONFIG, end
    m.run(0x08015948, {0x0801595C}, max_steps=20)
    need(m.get(CONFIG + 0x19, 1) == permanent, 'actual boot record-to-config copy')
    m.blocks[0] ^= 1
    m.r[14] = end
    m.run(0x0801FCA8, {end}, max_steps=30000)
    need(not m.cpsr & 0x40000000, 'native checksum rejects changed payload')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('source', 'native', 'report'): p.add_argument('--' + n, required=True, type=Path)
    a = p.parse_args(); need(not a.report.exists(), 'fresh report required')
    source, native = a.source.read_bytes(), a.native.read_bytes()
    need(sha(source) == SOURCE and sha(native) == NATIVE, 'immutable input identities')
    for (start, end), digest in SOURCE_RANGES.items(): need(sha(source[start:end]) == digest, 'source extent')
    patches = sanitizer_patches(native)
    need(patches == {0x1FAB8: bytes.fromhex('3f8008e2'), 0x1FB08: bytes.fromhex('0e0050e3')}, 'only source-domain sanitizer patches')
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(assembly(source, native), CODE)[0])
    rom = bytearray(native); rom[CODE - 0x08000000:CODE - 0x08000000 + len(code)] = code
    for at, data in patches.items(): rom[at:at + len(data)] = data
    # Completion replaces +12 after normalization; test the shared normalizer
    # separately so its new mask is actually exercised, not only byte-pinned.
    for value in (0, 0x10, 0x20, 0x3F, 0x40, 0xFFFF):
        m = StorageMachine(rom)
        fill(m, BUFFER, payload(7))
        m.put(BUFFER + 0x12, value, 2)
        m.run(0x0801FA98, {m.r[14]}, max_steps=10000)
        need(m.get(BUFFER + 0x12, 2) == value & 0x3F, 'shared permanent mask')
        need(m.get(BUFFER + 0x64, 2) == 0x1F, 'separate count mask unchanged')
    for permanent in range(64): exercise(rom, permanent, ((permanent % 16) << 28) | 31)
    for fail in range(25): exercise(rom, 0x3F, 0xF000001F, fail)
    # Direct table reader used by the high-score portrait has valid retained rows13/14.
    need(struct.unpack_from('<I', native, 0x1F4A0)[0] == 0x084A80F8, 'relocated portrait table')
    rows = [struct.unpack_from('<5I', native, 0x4A80F8 + i * 32) for i in (13, 14)]
    need(all(0x08000000 <= v < 0x09000000 for row in rows for v in row), 'fighter13/14 resource pointers')
    report = dict(status='MODE23_COMPLETION_SAVE_BOUNDED_INDEPENDENT_PASS', native_sha256=NATIVE,
                  source_sha256=SOURCE, tool_sha256=sha(Path(__file__).read_bytes()),
                  module_sha256=sha((ROOT / 'tools/mode23_completion_save.py').read_bytes()),
                  assembled_sha256=sha(code), cases=dict(shared_sanitizer=6, roundtrip=64, first_write_failure=25),
                  patches={f'{k:06X}': v.hex() for k, v in patches.items()},
                  source_ranges={f'{x:X}..{y:X}': v for (x, y), v in SOURCE_RANGES.items()},
                  source_tail_live=True, source_tail_required_by_B059=False,
                  limits=['Device block API is an in-memory fixture; no physical persistence or atomicity claim.',
                          'No installed scene, complete source save-format parity or arbitrary computed-alias census.',
                          'Valid three-character names used; native malformed-name reset spelling differs from source.',
                          'Source tail includes additional fighter statistics, flags, pairing data and eleven counters.',
                          'Adapter preserves caller R0, so low-level write failure is not surfaced by the source-shaped completion callback.'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], sha(a.report.read_bytes()))

if __name__ == '__main__': main()
