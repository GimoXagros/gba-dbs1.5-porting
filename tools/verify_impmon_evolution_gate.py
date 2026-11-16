"""Read-only independent verification of the flag-clear 1.5 Impmon gate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

PINS = {
    'before': 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278',
    'after': '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8',
    'gba': '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED',
    'wsc10': '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735',
    'wsc15': 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
}
SITE = 0x354700


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(rom, address):
    return struct.unpack_from('<I', rom, address)[0]


def branch(rom, address, zero):
    encoding = word(rom, address)
    conditions = {0: zero, 1: not zero, 14: True}
    condition = encoding >> 28
    need(encoding & 0x0F000000 == 0x0A000000 and condition in conditions, 'expected ARM branch')
    displacement = ((encoding & 0xFFFFFF) ^ 0x800000) - 0x800000
    return address + 8 + 4 * displacement if conditions[condition] else address + 4


def collector(rom, kind, actor):
    need([word(rom, address) for address in (0x3546F0, 0x3546FC, 0x35473C)]
         == [0xE3500008, 0xE358000B, 0xE358000F], 'actual compare instructions')
    lane = branch(rom, 0x3546F4, kind == 8)
    if lane == 0x354758:
        return 'other-object'
    need(lane == 0x3546F8 and word(rom, lane) == 0xE5D58011, 'fighter identity load')
    lane = branch(rom, SITE, actor == 11)
    if lane == 0x354704:
        return 'legacy-impmon-special'
    need(lane == 0x354738 and word(rom, lane) == 0xE5D58011, 'ordinary identity load')
    lane = branch(rom, 0x354740, actor == 15)
    if lane == 0x3547D0:
        return 'boss-excluded'
    need(lane == 0x354744, 'natural evolution route')
    need([word(rom, address) for address in (0x354744, 0x354748, 0x35474C, 0x354904)]
         == [0xE59F81B8, 0xE5858000, 0xE5845014, 0x0835A0F8], 'actual callback and collectible owner stores')
    return 'ordinary-evolution'


def verify(before, after, gba, wsc10, wsc15):
    need({key: sha(blob) for key, blob in zip(PINS, (before, after, gba, wsc10, wsc15))} == PINS,
         'exact candidate and source inputs')
    need(len(before) == len(after) == 0x1000000, 'exact 16 MiB images')
    need(before[SITE:SITE + 4] == bytes.fromhex('0C00001A')
         and after[SITE:SITE + 4] == bytes.fromhex('0C0000EA')
         and after[:SITE] + before[SITE:SITE + 4] + after[SITE + 4:] == before,
         'only raw byte 354703 changes and the whole ROM inverse matches')
    need(before[0x3546F0:0x354738] == gba[0x3546F0:0x354738], 'native legacy identity-only exception')
    anchors = (
        (wsc10, 0x3927F2, '80 7D 11 0B 75 20'),
        (wsc15, 0x742AD2, '26 F6 06 73 00 01 74 26 80 7D 11 0B 75 20'),
        (wsc15, 0x742B00, '80 7D 11 0F 75 03 E9 6C 00'),
        (wsc15, 0x74FC47, '88 47 20 88 47 25'),
        (wsc15, 0x778826, '26 F6 45 25 01 75 03'),
        (wsc15, 0x780B36, '26 88 45 25'),
    )
    for rom, address, hex_bytes in anchors:
        expected = bytes.fromhex(hex_bytes)
        need(rom[address:address + len(expected)] == expected, f'actual source instruction at {address:06X}')

    cases = []
    for kind in (5, 7, 8, 9):
        for actor in range(16):
            old_route, new_route = collector(before, kind, actor), collector(after, kind, actor)
            expected = 'other-object' if kind != 8 else 'boss-excluded' if actor == 15 else 'ordinary-evolution'
            need(new_route == expected and old_route == (
                'legacy-impmon-special' if kind == 8 and actor == 11 else new_route),
                'only collectible kind 8 for actor 11 changes route')
            cases.append(dict(kind=kind, actor=actor, before=old_route, after=new_route))
    need(word(after, 0x3534B8) == 0x0860B000, 'actual group-one loader base')
    row = struct.unpack_from('<8I', after, 0x60B000 + 11 * 32)
    need(row == (0x084B0000, 0x0861B4BC, 0x084A1390, 0x084A1390, 0x08568000, 0, 0, 0),
         'retained actor 11 group-one resource pointers')
    return dict(status='IMPMON_CLEAN15_ISOLATED_PASS', input_sha256=PINS['before'], output_sha256=PINS['after'],
                inputs=PINS, declared_bytes=4, changed_bytes=1, changed_offset=SITE + 3, whole_inverse=True,
                cases=cases, native_group_1_actor_11_record=[f'{entry:08X}' for entry in row],
                scope='WSC 1.5 flag-clear collector and existing native resource row. Alternate mode and actual gameplay are separate.',
                verifier_sha256=sha(Path(__file__).read_bytes()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (*PINS, 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    result = verify(*(getattr(args, key).read_bytes() for key in PINS))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print(result['status'], sha(args.report.read_bytes()))
