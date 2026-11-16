"""Verify the independent WSC 1.5 evolution event-table extension."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import types

import verify_shoot_caller_resident as reference_scan

PINS = {
    'before': '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8',
    'after': 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1',
    'wsc15': 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
    'music_manifest': 'AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
}
ROM = 0x08000000
RESERVE = (0xD3F000, 0xD3F05A)
TABLES = (
    # name, WSC source, old table, native consumer, aligned literal, condition, new table
    ('entry', 0x7679C2, 0x35A210, 0x35A1E4, 0x35A210, 14, 0xD3F000),
    ('ground', 0x7679E0, 0x35A580, 0x35A54C, 0x35A580, 0, 0xD3F01E),
    ('air', 0x7679FE, 0x35A596, 0x35A550, 0x35A598, 1, 0xD3F03C),
)
SCANNER_SHA = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from('<I', data, at)[0]


def half(data, at):
    return struct.unpack_from('<H', data, at)[0]


def old_base(data, at, cond):
    op = word(data, at)
    need(op >> 28 == cond and op & 0x0FFFF000 == 0x028F8000 and (op >> 8) & 0xF == 0,
         'old non-flag-setting ADD uses PC and only writes R8')
    return at + 8 + (op & 255)


def new_base(data, at, cond, expected_slot):
    op = word(data, at)
    need(op >> 28 == cond and op & 0x0FFFF000 == 0x059F8000,
         'new constant aligned word load uses same condition, PC and R8')
    slot = at + 8 + (op & 0xFFF)
    need(slot == expected_slot and slot % 4 == 0, 'no ARM7TDMI rotated unaligned literal')
    return word(data, slot) - ROM


def p1_counts(data):
    owners = tuple(word(data, at) - ROM for at in (0x3534BC, 0x3534B8))
    need(owners == (0x4A80F8, 0x60B000), 'actual native group-zero and group-one record bases')
    counts = []
    for actor in range(15):
        row = []
        for owner in owners:
            p1 = word(data, owner + actor * 32 + 4) - ROM
            index = word(data, p1) - ROM
            first_command = word(data, index + 4) - ROM
            size = first_command - index
            need(0 < size and size % 16 == 0 and first_command < len(data), 'bound event table by first command')
            row.append(size // 16)
        counts.append(row)
    return counts


def inbound(before, after):
    need(sha(Path(reference_scan.__file__).read_bytes()) == SCANNER_SHA, 'frozen independent scanner')
    spans = (RESERVE, *((slot, slot + 4) for _, _, _, _, slot, _, _ in TABLES))
    scan = types.FunctionType(reference_scan.inbound.__code__,
         dict(reference_scan.__dict__, SPANS=spans), argdefs=reference_scan.inbound.__defaults__)
    # These two Thumb-shaped halfwords are contained by an ARM CMP and BX LR.
    need((word(before, 0x359B6C), word(before, 0x359FAC)) == (0xE3500000, 0xE12FFF1E),
         'classify Thumb-shaped words in ARM instructions')
    raw_arm_shapes = {('Thumb B', 0x359B6E, ROM + 0x35A212), ('Thumb B', 0x359FAE, ROM + 0x35A210)}
    old_hits, new_hits = scan(before), scan(after)
    need(set(old_hits) == raw_arm_shapes | {
         ('ARM ADR', 0x35A1E4, ROM + 0x35A210), ('ARM ADR', 0x35A54C, ROM + 0x35A580)},
         'no inbound encodings in the unused reserve and only known refs into overwritten literal words')
    need(set(new_hits) == raw_arm_shapes
         | {('ARM literal', site, ROM + slot) for _, _, _, site, slot, _, _ in TABLES}
         | {('pointer', slot, ROM + table) for _, _, _, _, slot, _, table in TABLES},
         'exact new literal consumers, pointers and conservative shapes')
    return dict(before=old_hits, after=new_hits, known_thumb_shapes=sorted(raw_arm_shapes), scanner_sha256=SCANNER_SHA)


def verify(before, after, wsc15, music_manifest):
    need({key: sha(blob) for key, blob in zip(PINS, (before, after, wsc15, music_manifest))} == PINS,
         'exact immutable candidate, source and ownership inputs')
    need(len(before) == len(after) == 0x1000000, 'both complete 16 MiB ROMs')
    need(wsc15[0x7673BA:0x7673C6] == bytes.fromhex('33 DB 8A 5C 11 D1 E3 2E 8B 87 E2 10')
         and wsc15[0x7675BB:0x7675D3] == bytes.fromhex(
             '33 DB 8A 5C 11 D1 E3 2E 8B 87 00 11 F7 44 06 01 00 74 05 2E 8B 87 1E 11'),
         'actual source character index and three source table consumers')
    need((word(before, 0x35A1E8), word(before, 0x35A548), word(before, 0x35A554))
         == (0xE19100B8, 0xE3180001, 0xE19100F8), 'actual native index loads and grounded/air test')
    need((word(before, 0x35A20C), word(before, 0x35A57C)) == (0xE12FFF1E,) * 2, 'legacy data follows native returns')

    start, end = RESERVE
    music = json.loads(music_manifest)
    areas = [tuple(area) for area in music['reservations'] if area[0] <= start < end <= area[1]]
    need(areas == [(0xD33000, 0xD40000)] and before[start:end] == b'\xff' * (end - start),
         'erased tail in frozen owned allocation')
    used = [row for row in music['writes'] if areas[0][0] <= row['offset'] < areas[0][1]]
    need(max(row['offset'] + row['size'] for row in used) == 0xD3EA01 <= start
         and all(sha(after[row['offset']:row['offset'] + row['size']]) == row['after_sha256'] for row in used),
         'no overlap or byte change in prior audio payloads')

    expected = bytearray(before)
    shown = []
    actor_counts = p1_counts(after)
    spans = [(start, end - start)]
    for index, (name, source, old_table, site, slot, cond, new_table) in enumerate(TABLES):
        need(old_base(before, site, cond) == old_table and new_base(after, site, cond, slot) == new_table,
             'exact table origin through actual instruction decode')
        old_values = struct.unpack_from('<11H', before, old_table)
        values = struct.unpack_from('<15H', wsc15, source)
        need(values[:11] == old_values and tuple(half(after, new_table + 2 * actor) for actor in range(15)) == values,
             'all 15 source values and exactly preserved first 11')
        need(all(event < actor_counts[actor][index != 0] for actor, event in enumerate(values)),
             'every new event stays inside its actual native P1 owner')
        struct.pack_into('<I', expected, site, cond << 28 | 0x059F8000 | (slot - site - 8))
        struct.pack_into('<I', expected, slot, ROM + new_table)
        expected[new_table:new_table + 30] = wsc15[source:source + 30]
        spans.extend(((site, 4), (slot, 4)))
        shown.append(dict(name=name, source_offset=source, old_native_offset=old_table, site=site,
                          literal_slot=slot, condition=cond, native_offset=new_table, values=values))
    need(bytes(expected) == after, 'whole independent construction and all unrelated bytes identical')
    inverse = bytearray(after)
    changed = 0
    for offset, size in sorted(spans):
        inverse[offset:offset + size] = before[offset:offset + size]
        changed += sum(a != b for a, b in zip(before[offset:offset + size], after[offset:offset + size]))
    need(bytes(inverse) == before and changed == 109, 'entire inverse and exact changed byte count')
    need((half(before, 0x35A580 + 22), half(before, 0x35A596 + 22), word(before, 0x35A5AC))
         == (25, 0x4000, 0xE92D4000), 'actual old ID11 ground/air overreads')
    return dict(status='EVOLUTION_EVENT_TABLES_ISOLATED_PASS', input_sha256=PINS['before'], output_sha256=PINS['after'],
                input_pins=PINS, source_rows=shown, native_p1_event_counts=actor_counts, inverse=True,
                declared_bytes=114, changed_bytes=changed, spans=sorted(spans), inbound=inbound(before, after),
                abi='Same conditions and R8-only base loads without flag updates; unchanged unsigned/signed event consumers.',
                scope='Static isolated gate. Gameplay caller and equivalent alternate source mode are separate evidence.',
                verifier_sha256=sha(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (*PINS, 'report'):
        parser.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    result = verify(*(getattr(args, key).read_bytes() for key in PINS))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], sha(args.report.read_bytes()))
