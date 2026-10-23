"""Keep the dedicated Shoot stage at the two native manager lookups."""
import argparse
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import BASE, GBA, OLD, NEW, need, sha, u32, no_inbound

PARENT = 'B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8'
FIRST, LIMIT = 0x629500, 0x629518
SITES = (0x36D28C, 0x36D2F8)
GUARDS = (
    ('source', 0x743FC0, 0x7440C7, 'A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6'),
    ('source', 0x747A68, 0x747AC7, '1A1B4E6046E15687E8087FF14AF909546AF8F41AE3BC95964C16FB2D992CF447'),
    ('before', 0x36D224, 0x36D38C, 'BAD85987BF89590DF2DE5BB72B3CECAB5DDB2118531ED25AF847FE132418F471'),
    ('before', 0x582C40, 0x582C78, 'EDC7EA0D1CBBB0D76547636A2D3F5E22E4A454181B5F40EB92196CEA76A62EEB'),
    ('before', 0x584C00, 0x584C60, '17DDA5211D60EF553341981E26447E93E02C6A145307DD255371BD277B151F75'),
    ('before', 0x584B00, 0x584B60, '825C46426C772F27E08376179CB1AF3749382C87E2DC06E010C3D762A433B570'),
    ('before', 0x5C4300, 0x5C4354, '715D48A742EC4B7046E8822615D2E5A2599A7627FFCEFDC04587D338C72A272D'),
)


def branch(at, target, link=False):
    delta = target - (BASE + at + 8)
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), 'ARM branch range')
    return (0xEB000000 if link else 0xEA000000) | ((delta // 4) & 0xFFFFFF)


def helper():
    return struct.pack('<6I', 0xE59F800C, 0xE5D8000E, 0xE350000B,
                       0x012FFF1E, branch(FIRST + 16, 0x080D1C78), 0x03002310)


def validate(before, after):
    need(len(before) == len(after), 'fixed ROM size')
    need(after[FIRST:LIMIT] == helper(), 'exact unsigned stage read and private tail-call helper')
    spans = [(at, at + 4) for at in SITES] + [(FIRST, LIMIT)]
    for at in SITES:
        need(u32(after, at) == branch(at, BASE + FIRST, True), 'actual manager BL destination')
    inverse = bytearray(after)
    for start, end in spans:
        inverse[start:end] = before[start:end]
    need(inverse == before, 'only two calls and helper change; public getter and all tables preserved')
    return spans


def build(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (PARENT, GBA, OLD, NEW), 'pinned originals and repaired predecessor')
    for label, start, end, expected in GUARDS:
        need(sha((source if label == 'source' else before)[start:end]) == expected, 'source/caller ownership: ' + hex(start))
    need(before[0x6294C0:LIMIT] == b'\xff' * (LIMIT - 0x6294C0), 'unowned alignment gap and private code reservation')
    ownership = no_inbound(before, ((FIRST, LIMIT),))
    for at in SITES:
        need(u32(before, at) == branch(at, 0x080D1C78, True), 'original two shared-getter calls')
    after = bytearray(before)
    after[FIRST:LIMIT] = helper()
    for at in SITES:
        struct.pack_into('<I', after, at, branch(at, BASE + FIRST, True))
    spans = validate(before, after)
    changed_cases = []
    routes = {11: 10, 13: 8, 14: 9}
    for character in range(256):
        for stage in range(256):
            original = routes.get(character, stage)
            repaired = 11 if stage == 11 else original
            if original != repaired:
                changed_cases.append([character, stage, original, repaired])
    need(changed_cases == [[11, 11, 10, 11], [13, 11, 8, 11], [14, 11, 9, 11]], 'only three dedicated-stage cases differ')
    negative_sites = [SITES[0], SITES[1], FIRST, FIRST + 4, FIRST + 8,
                      FIRST + 12, FIRST + 16, FIRST + 20, 0xD1C78]
    for at in negative_sites:
        wrong = bytearray(after)
        wrong[at] ^= 1
        try:
            validate(before, wrong)
        except ValueError:
            pass
        else:
            raise AssertionError('bad stage route accepted at ' + hex(at))
    return bytes(after), dict(schema=1, kind='private-shoot-stage-manager-priority',
        input_sha256=PARENT, output_sha256=sha(after), declared_bytes=32,
        changed_bytes=sum(a != b for a, b in zip(before, after)), full_inverse=True,
        writes=[dict(start=a, end=b, before_sha256=sha(before[a:b]), after_sha256=sha(after[a:b])) for a, b in spans],
        ownership=ownership, compared_byte_cases=65536, changed_cases=changed_cases,
        negative_cases=len(negative_sites), new_RAM_bytes=0,
        limits=['Only two manager lookups; all other temporary character routes retained.',
                'Stage values outside 0..11 remain outside the manager table contract.',
                'Complete Shoot entry remains unconnected; no runtime reachability claim.'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('before', 'gba', 'old', 'source', 'output'):
        p.add_argument(key, type=Path)
    p.add_argument('--manifest', required=True, type=Path)
    a = p.parse_args()
    inputs = [a.before, a.gba, a.old, a.source]
    need(all(x.suffix.lower() in ('.gba', '.wsc') for x in inputs), 'explicit ROM inputs only')
    need(a.output.suffix.lower() == '.gba' and a.manifest.suffix.lower() == '.json', 'explicit artifact formats')
    need(a.output.resolve() not in {x.resolve() for x in inputs}, 'output cannot replace an input')
    result, report = build(*(x.read_bytes() for x in inputs))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(result)
    a.manifest.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', output_sha256=report['output_sha256'], declared_bytes=32)))


if __name__ == '__main__':
    main()
