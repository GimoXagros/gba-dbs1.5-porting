#!/usr/bin/env python3
"""ROM-only evidence for Shoot scene sound IDs and existing native services.

This decodes instructions and compares immutable data. It does not execute
either CPU, initialize an emulator, inspect SRAM, or import a builder.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16

HASHES = (
    '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED',
    '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735',
    'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
)
RANGES = (
    (0, 0x1565C, 0x15810, 'native reset', '42D0CDC0817926DD399BFD3265A319E3B80F84CE0C65394D1FEFDF8861902717'),
    (0, 0x158C8, 0x158CC, 'native channel fade', '379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F'),
    (0, 0x354758, 0x3547D0, 'commercial 98 sound receiver', '19D1EDD6869E155406E347F7A8D2203874E0AE9251281FB0ADC4D4C5972C7053'),
    (1, 0x392835, 0x39288D, 'commercial 98 sound producer', 'E1C86551AF71364951D97D5EB2F61812B13063815648CFFD7AC206EAFA93D82E'),
    (2, 0x754ED0, 0x754F74, 'source channel fade', '1910B806C0D2277241896320BFD0D2E2E634C290838DDB90B1A82E4B1F863FA5'),
    (2, 0x7550E2, 0x755220, 'source reset', '6D977539D01D7AD2F7006EC97869600BF800E51B25A08A7CA7684FC14B2AEE5F'),
    (0, 0x340378, 0x3403DC, 'commercial stop receiver', '2327DC8CB0709E8770D4B39AE0103FBDCC5363DDC21ABD570F988D92EBC3CB8A'),
    (1, 0x3BEAF4, 0x3BEBDE, 'commercial stop producer', 'C70B98ACCB1D982E4875BF6A3AAF9CA5C23025FCEE1C23B384E05B52BD440DE1'),
)

def digest(data):
    return hashlib.sha256(data).hexdigest().upper()

def need(ok, label):
    if not ok:
        raise ValueError(label)

def branch(data, pos):
    word, = struct.unpack_from('<I', data, pos)
    need(word & 0x0F000000 == 0x0B000000, 'BL encoding')
    imm = word & 0xFFFFFF
    if imm & 0x800000:
        imm -= 0x1000000
    return (0x08000000 + pos + 8 + 4 * imm) & 0xFFFFFFFF

def payload(data, bank, sid):
    start, = struct.unpack_from('<H', data, bank + sid * 6 + 4)
    end, = struct.unpack_from('<H', data, bank + (sid + 1) * 6 + 4)
    need(0x400 <= start < end < 0x10000, 'payload bounds')
    return data[bank + start:bank + end]

def request_gba(data, pos, sid, kind):
    need(struct.unpack_from('<III', data, pos - 12) ==
         (0xE3A08000 | sid, 0xE3A09000 | kind, 0xE3A0A000), 'native ID/type/delay')
    need(branch(data, pos) == 0x080D15C0, 'native request consumer')

def request_wsc(data, pos, sid, kind):
    expected = (b'\xc7\x44\x02' + struct.pack('<H', sid) + b'\xc7\x44\x0e' +
                struct.pack('<H', kind) + bytes.fromhex('c744060000814c100001'))
    need(data[pos:pos + len(expected)] == expected, 'source ID/type/delay/flag')

def inspect(gba, old, new):
    # Same payload alone is insufficient; the old caller and its actual GBA
    # conversion establish the backend ID and request type independently.
    rows = ((0x9A, 0x98, 0x5A, 1, 0x39284A, 0x354768),
            (0xA9, 0xA7, 0x4C, 2, 0x395B5E, 0x3719C0),
            (0x06, 0x06, 0x00, 2, 0x3BEB12, 0x340394))
    ids = []
    for src, former, dst, kind, source_call, native_call in rows:
        data = payload(new, 0x3F0000, src)
        need(data == payload(old, 0x2D0000, former), 'payload identity')
        request_wsc(old, source_call, former, kind)
        request_gba(gba, native_call, dst, kind)
        ids.append({'source_id': src, 'old_id': former, 'native_id': dst,
                    'request_type': kind, 'payload_sha256': digest(data),
                    'old_request': source_call, 'native_request': native_call})
    need(old[0x39BA00:0x39BAA4] == new[0x754ED0:0x754F74], 'fade helper identity')
    arm = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    code = list(arm.disasm(gba[0x1565C:0x15804], 0x0801565C))
    calls = [(i.address, int(i.op_str[1:], 16)) for i in code if i.mnemonic == 'bl']
    need([t for _, t in calls] == [0x080158C8] * 8 + [0x0837B44C], 'reset eight channel calls then stop')
    need(gba[0x158C8:0x158CC] == bytes.fromhex('1eff2fe1'), 'retail fade is BX LR')
    clears = [(i.mnemonic, i.op_str) for i in code if 0x080157B0 <= i.address <= 0x080157D8]
    need(clears == [('subs', 'r0, r0, r0')] +
         [('strh', 'r0, [r4]' if off == 0 else f'r0, [r4, #{off if off < 10 else hex(off)}]')
          for off in (0, 2, 4, 6, 8, 12, 14, 16)] +
         [('subs', 'r0, r0, #1'), ('strh', 'r0, [r4, #0xa]')], 'native reset exact field widths/order')
    need(struct.unpack_from('<III', gba, 0x15804) == (0x030022F0,) * 3, 'native request owner')
    # Confirm source reset has the same nine fields, including the negative
    # deferred-ID sentinel; all fields are in existing commercial RAM.
    x86 = Cs(CS_ARCH_X86, CS_MODE_16)
    source_clear = list(x86.disasm(new[0x7551C5:0x7551E2], 0x7551C5))
    need([(i.mnemonic, i.op_str) for i in source_clear] ==
         [('xor', 'ax, ax')] +
         [('mov', 'word ptr [si], ax' if off == 0 else f'word ptr [si + {hex(off) if off >= 10 else off}], ax')
          for off in (0, 2, 4, 6, 8, 12, 14, 16)] +
         [('dec', 'ax'), ('mov', 'word ptr [si + 0xa], ax')], 'source reset exact field widths/order')
    source_calls = [i.address for i in x86.disasm(new[0x773051:0x7730D9], 0x773051)
                    if i.mnemonic == 'lcall' and i.op_str == '0x4fff, 0x4ee0']
    need(len(source_calls) == 8, 'scene pre-fade eight channel calls')
    # Native all-stop really iterates the existing MPlay records, rather than
    # merely resetting the public request latch.
    need(branch(gba, 0x37B47C) == 0x0837DB84, 'zero-ID all-stop route')
    need(struct.unpack_from('<I', gba, 0x37DB8C)[0] == 0x0837C3B1, 'ARM to Thumb stop trampoline')
    return {'ids': ids, 'reset_entry': 0x0801565C, 'reset_instructions': len(code),
            'native_fade_entry': 0x080158C8, 'native_fade_is_retail_noop': True,
            'source_prefade_calls': source_calls,
            'source_fade_ticks': 32, 'native_intermediate_fade_equivalence': False,
            'request_owner': 0x030022F0, 'native_reset_calls': calls}

def negatives(gba, old, new):
    mutations = ((0, 0x35475C, bytes.fromhex('3d80a0e3'), 'invented arithmetic ID'),
                 (0, 0x354760, bytes.fromhex('0290a0e3'), 'request type'),
                 (0, 0x15804, struct.pack('<I', 0x03002310), 'request owner'),
                 (0, 0x157BC, bytes.fromhex('b060c4e1'), 'reset wrong register'),
                 (0, 0x158C8, bytes.fromhex('0000a0e1'), 'invented fade body'),
                 (2, 0x3F844E, b'\x07', 'changed count sound payload'))
    rejected = []
    for which, pos, value, label in mutations:
        items = [bytearray(gba), bytearray(old), bytearray(new)]
        items[which][pos:pos + len(value)] = value
        try:
            inspect(*items)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('negative mutation escaped: ' + label)
    return rejected

def main():
    p = argparse.ArgumentParser()
    p.add_argument('gba', type=pathlib.Path)
    p.add_argument('wsc10', type=pathlib.Path)
    p.add_argument('wsc15', type=pathlib.Path)
    p.add_argument('--output', required=True, type=pathlib.Path)
    a = p.parse_args()
    data = [x.read_bytes() for x in (a.gba, a.wsc10, a.wsc15)]
    for value, expected in zip(data, HASHES, strict=True):
        need(digest(value) == expected, 'original ROM hash')
    ranges = []
    for which, start, end, label, expected in RANGES:
        actual = digest(data[which][start:end])
        need(actual == expected, label + ' evidence bytes')
        ranges.append({'input': which, 'start': start, 'end': end, 'label': label, 'sha256': actual})
    result = {'inputs': list(HASHES), 'evidence': ranges, 'analysis': inspect(*data),
              'negative_controls': negatives(*data), 'runtime_executed': False,
              'save_accessed': False}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(digest(a.output.read_bytes()))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
