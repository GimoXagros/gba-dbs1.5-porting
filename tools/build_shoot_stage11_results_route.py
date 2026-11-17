"""Restore the source stage 11 final-result path over the exact v87 native image."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
from types import FunctionType

from build_progression_integration import arm_branch
import verify_shoot_caller_resident as scanner


SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
OWNER = '162C4A9D2B8A684582EF2C3F22D8E60B6887E832BEBE4CB23730169C2198425C'
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'
HOOK, ADAPTER, CONTINUATION = 0x89538, 0xD8CB20, 0x8953C


def build(source, before, owner_raw):
    need, sha = scanner.need, scanner.sha
    need(sha(source) == SOURCE and sha(before) == BEFORE and len(before) == 0x1000000,
         'exact WSC source and v87 16 MiB predecessor')
    need(source[0x777049:0x777055] == bytes.fromhex('807d0e0b7406807d0e07751f')
         and source[0x777065:0x77706A] == bytes.fromhex('9a8115f176'),
         'source stage 7/11, normal result save lineage')
    need(before[HOOK:HOOK + 4] == bytes.fromhex('070058e3'), 'displaced CMP r8,#7')
    need(sha(Path(scanner.__file__).read_bytes()) == SCANNER, 'frozen strict complete-ROM reference scanner')
    body = struct.pack('<3I', 0xE3580007, 0x1358000B,
                       arm_branch(ADAPTER + 8, CONTINUATION))
    stop = ADAPTER + len(body)
    need(before[ADAPTER:stop] == b'\xff' * len(body), 'exact adapter span erased')
    census = FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((ADAPTER, stop),)),
                          argdefs=scanner.inbound.__defaults__)
    need(not census(before), 'zero incoming pointer/ARM/Thumb encodings, no exemptions')
    need(sha(owner_raw) == OWNER, 'exact predecessor child-contact ownership manifest')
    owner = json.loads(owner_raw)
    need(owner['output_sha256'] == BEFORE and owner['reservations'] == [[0xD8C800, 0xD8CE00]],
         'exact serial child-contact envelope')
    native_rows = [(row['offset'], row['offset'] + row['size']) for row in owner['writes']]
    need(native_rows == [(0xD8C800, 0xD8CA68), (0x36F77C, 0x36F780)]
         and all(before[lo:hi] == bytes.fromhex(row['after_hex'])
                 for (lo, hi), row in zip(native_rows, owner['writes'], strict=True)),
         'complete actual predecessor writes present')
    need(0xD8CA68 <= ADAPTER < stop <= 0xD8CE00, 'serial layer tail suballocation')
    serial_owner = dict(manifest_sha256=OWNER, reserved_span=[0xD8C800, 0xD8CE00],
                        prior_payload_span=list(native_rows[0]), borrowed_tail_span=[ADAPTER, stop])
    changes = {HOOK: struct.pack('<I', arm_branch(HOOK, ADAPTER)), ADAPTER: body}
    after = bytearray(before)
    for at, data in changes.items():
        after[at:at + len(data)] = data
    inverse = bytearray(after)
    for at, data in changes.items():
        inverse[at:at + len(data)] = before[at:at + len(data)]
    need(inverse == before, 'full image inverse')
    return bytes(after), dict(status='SHOOT_STAGE11_NATIVE_RESULTS_ROUTE_PREPARED',
                              source_sha256=sha(source), input_sha256=sha(before), output_sha256=sha(after),
                              builder_sha256=sha(Path(__file__).read_bytes()),
                              writes=[dict(offset=at, size=len(data), before=before[at:at + len(data)].hex(),
                                           after=data.hex()) for at, data in changes.items()],
                              declared_bytes=16, changed_bytes=sum(x != y for x, y in zip(before, after, strict=True)),
                              adapter_span=[ADAPTER, stop], strict_inbound_count=0, whole_image_inverse=True,
                              serial_child_contact_tail=serial_owner,
                              new_RAM_bytes=0, tested_native_runtime=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('source', 'before', 'owner', 'output'):
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    scanner.need(not args.output.exists(), 'fresh isolated output directory')
    after, manifest = build(args.source.read_bytes(), args.before.read_bytes(), args.owner.read_bytes())
    args.output.mkdir(parents=True)
    (args.output / 'component.gba').write_bytes(after)
    report = args.output / 'manifest.json'
    report.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(manifest['status'], manifest['output_sha256'], scanner.sha(report.read_bytes()))


if __name__ == '__main__':
    main()

