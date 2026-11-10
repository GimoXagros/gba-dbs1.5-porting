#!/usr/bin/env python3
"""Independent capture-free identity and one-word inverse packaging gate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
INPUT = 'FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
OUTPUT = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR = '6C57D65740F27CFA64CC5EFE892F7FAC80BDB778D3128F6BF8BED0B5DCBC930C'
MANIFEST = 'D6D66777FCA9BD4A6979F960DEAFBCDDF38D0CB2D3A112C3EF222B67AA2061FD'
SITE = 0x6FFC00

def need(ok, label):
    if not ok:
        raise ValueError(label)

def sha(data):
    return hashlib.sha256(data).hexdigest().upper()

def inverse(before, after):
    need(len(before) == len(after) == 0x800000, 'eight MiB extent')
    need(before[SITE:SITE+4] == bytes.fromhex('180096E5'), 'old LDR r0,[r6,+18]')
    need(after[SITE:SITE+4] == bytes.fromhex('280096E5'), 'new LDR r0,[r6,+28]')
    need(after[:SITE] + before[SITE:SITE+4] + after[SITE+4:] == before, 'whole-ROM inverse')

def audit(before, after, source, manifest_blob):
    need(tuple(map(sha, (before, after, source))) == (INPUT, OUTPUT, SOURCE), 'approved identities')
    need(sha((ROOT/'tools/build_shoot_terminal_owner_link.py').read_bytes()) == AUTHOR, 'frozen author')
    need(sha(manifest_blob) == MANIFEST, 'frozen new manifest')
    inverse(before, after)
    manifest = json.loads(manifest_blob)
    writes = [dict(offset=SITE, before='180096e5', after='280096e5')]
    need(manifest['expected_writes'] == writes and manifest['input_sha256'] == INPUT and
         manifest['output_sha256'] == OUTPUT and manifest['source_sha256'] == SOURCE and
         manifest['declared_bytes'] == 4 and manifest['changed_bytes'] == 1 and
         manifest['new_storage'] is False and manifest['new_RAM_owner'] is False, 'manifest contract')
    for data, key in ((before, 'native_pins'), (source, 'source_pins')):
        for start, end, digest in manifest[key]:
            need(sha(data[start:end]) == digest, key + hex(start))
    need(tuple(struct.unpack_from('<I', after, a)[0] for a in (0x5BC29C,0x5BC2A8,0x5BC380)) ==
         (0xE5846028,0xE5847018,0xE5864028), 'constructor reciprocal owner and distinct opponent')
    rejected = []
    for at in (SITE, SITE+1, SITE+2, SITE+3, SITE+4, 0x5BC29C, 0x5CD978, 0x5BF400, 0x7FFFFF):
        bad = bytearray(after); bad[at] ^= 1
        try:
            inverse(before, bytes(bad))
        except ValueError:
            rejected.append(at)
        else:
            raise ValueError('mutation accepted')
    return dict(status='INDEPENDENT_SOURCE_ONLY_TERMINAL_OWNER_LINK_PRODUCTION_PASS',
                input_sha256=INPUT, output_sha256=OUTPUT, source_sha256=SOURCE,
                builder_sha256=AUTHOR, manifest_sha256=MANIFEST, expected_writes=writes,
                declared_bytes=4, changed_bytes=1, whole_ROM_inverse=True,
                historical_capture_dependency=False, semantic_cases_rerun=False,
                new_storage=False, new_RAM_owner=False, inverse_mutations_rejected=rejected,
                verifier_sha256=sha(Path(__file__).read_bytes()), runtime_acceptance=False)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('before','after','source','manifest','report'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report')
    report = audit(*(getattr(args,k).read_bytes() for k in ('before','after','source','manifest')))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(report['status'], sha(args.report.read_bytes()))

if __name__ == '__main__':
    main()
