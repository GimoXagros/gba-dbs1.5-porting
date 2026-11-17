"""Align source AI parameter halfwords for real ARM7TDMI loads."""
import argparse
import json
from pathlib import Path
import struct
import types

import build_character_ai_tables as parent

INPUT = 'DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
OWNER = '2645FA80910F747BEB4A07239645449536BCFA51652194D191749CF03DF063B3'
PARENT = '3F8613A6697E2CFFB0112F1C699415A793EACDA7242790C8D30C6C9662691EC0'
FIRST, LIMIT = 0xD8AB00, 0xD8AC00
need, sha = parent.need, parent.sha


def arm7_ldrh(data, at):
    value = parent.h(data, at & ~1)
    return ((value >> 8) | (value << 24)) & 0xFFFFFFFF if at & 1 else value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'source', 'owner', 'output', 'manifest'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    paths = [a.before, a.source, a.owner, a.output, a.manifest]
    need(len({x.resolve() for x in paths}) == 5 and not a.output.exists() and not a.manifest.exists(), 'fresh distinct outputs')
    before, source, owner_bytes = (x.read_bytes() for x in paths[:3])
    need((sha(before), sha(source), sha(owner_bytes)) == (INPUT, parent.SOURCE, OWNER), 'pinned input/source/owner')
    need(sha(Path(parent.__file__).read_bytes()) == PARENT, 'frozen parent helper')
    owner = json.loads(owner_bytes)
    params = source[0x782970:0x782A1A]
    need(len(params) == 170 and before[parent.PARAMS:parent.PARAMS + 170] == params, 'ten complete source rows')
    need(parent.aliases(before, parent.PARAMS, 170) == dict.fromkeys(parent.PARAM_ALIASES, 0), 'all parameter readers')
    need(parent.u(before, 0xC6D6C) == 0xE3A01011, 'native packed stride')
    need(before[FIRST:LIMIT] == b'\xff' * (LIMIT - FIRST), 'blank reservation')
    for lo, hi in owner['reservations']:
        need(not max(lo, FIRST) < min(hi, LIMIT), 'disjoint reservation')
    need(sha(Path(parent.scanner.__file__).read_bytes()) == parent.SCANNER, 'frozen scanner')
    scan = types.FunctionType(parent.scanner.inbound.__code__, dict(parent.scanner.__dict__, SPANS=((FIRST, LIMIT),)), argdefs=parent.scanner.inbound.__defaults__)
    need(not scan(before), 'zero incoming references without exemptions')
    after, writes = bytearray(before), []

    def put(at, blob, label):
        need(not any(max(at, w['offset']) < min(at + len(blob), w['offset'] + w['size']) for w in writes), 'disjoint writes')
        writes.append(dict(offset=at, size=len(blob), before_hex=before[at:at + len(blob)].hex(), after_hex=blob.hex(), label=label))
        after[at:at + len(blob)] = blob

    table = b''.join(params[i:i + 17] + b'\0' for i in range(0, 170, 17))
    put(FIRST, table, 'ten source rows with unused even-stride padding')
    put(0xC6D6C, struct.pack('<I', 0xE3A01012), '18-byte parameter stride')
    for at in parent.PARAM_ALIASES:
        put(at, struct.pack('<I', parent.BASE + FIRST), 'aligned parameter reader')
    after = bytes(after)
    inverse = bytearray(after)
    for w in writes:
        inverse[w['offset']:w['offset'] + w['size']] = bytes.fromhex(w['before_hex'])
    need(bytes(inverse) == before and len(writes) == 17 and sum(w['size'] for w in writes) == 244, 'whole image inverse and write extent')
    for w in owner['writes']:
        lo, hi = w['offset'], w['offset'] + w['size']
        need(before[lo:hi] == bytes.fromhex(w['after_hex']), 'prior owner input intact')
        if lo not in parent.PARAM_ALIASES:
            need(after[lo:hi] == before[lo:hi], 'non-parameter AI owner retained')
    old_words, new_words = [], []
    for row in range(10):
        old_words.append(arm7_ldrh(before, parent.PARAMS + row * 17) & 0xFFFF)
        new_words.append(arm7_ldrh(after, FIRST + row * 18))
        need(after[FIRST + row * 18:FIRST + row * 18 + 17] == params[row * 17:row * 17 + 17], 'all source field bytes')
        for off in (0, 2):
            need(arm7_ldrh(after, FIRST + row * 18 + off) == parent.h(params, row * 17 + off), 'both source halfwords load exactly')
    need(arm7_ldrh(before, parent.PARAMS + 9 * 17) == 0x0F0000E4 and new_words[9] == 0x02E4, 'observed old odd-load failure and corrected row9')
    report = dict(status='PASS', input_sha256=INPUT, output_sha256=sha(after), source_sha256=parent.SOURCE,
                  owner_sha256=OWNER, reservations=[[FIRST, LIMIT]], writes=writes,
                  declared_bytes=244, actual_changed_bytes=sum(x != y for x, y in zip(before, after)), new_RAM_bytes=0,
                  old_arm7_first_words=old_words, aligned_source_first_words=new_words,
                  superseded_parameter_aliases=list(parent.PARAM_ALIASES), preserved_other_AI_writes=13,
                  limits=['Odd rows intentionally recover full source halfwords; commercial truncated values are not retained.',
                          'No live emulator result is claimed. Native action42 input-mask exception remains unchanged.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.manifest.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(after)
    a.manifest.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status='PASS', output_sha256=sha(after), manifest_sha256=sha(a.manifest.read_bytes()), changed=report['actual_changed_bytes'])))


if __name__ == '__main__':
    main()
