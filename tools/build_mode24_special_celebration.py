"""Install the source Master celebration in the cable result's two existing task payloads."""
import argparse
import json
from pathlib import Path
import struct

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_mode24_link_cards import branch
from mode23_linker import compose
from mode24_special import M24_SPECIAL_EXPORTS, assembly

PARENT = '505DCE0601EA9ACCB7D27D9AE410132D27933E733580574F4B177541B05DA96D'
OWNER = '49225A158C655F86D44C5D7CADD525A0DBD12E5E650FA90DBD1D8F9C4D815F27'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SPRITE, EDITOR = 0x08ECAA78, 0x08ECAA3C


def equal_branch(at, target):
    encoded, = struct.unpack('<I', branch(at, target))
    return struct.pack('<I', encoded & 0x0fffffff)


def build(image, source, owner_bytes):
    assert (sha(image), sha(source), sha(owner_bytes)) == (PARENT, SOURCE, OWNER)
    owner = json.loads(owner_bytes)
    assert owner['output_sha256'] == PARENT
    assert image[SPRITE-BASE:SPRITE-BASE+4] == bytes.fromhex('020916e3')
    assert image[EDITOR-BASE:EDITOR-BASE+4] == equal_branch(EDITOR, 0x08ECAB1C)
    prior = owner['prior_excluded_extents'] + [[a['start'], a['end']] for a in owner['allocations']]
    allocator = Allocator(image)
    exclude(allocator, prior)
    body = assembly(source, image)
    trial, _, _ = compose((body,), BASE, M24_SPECIAL_EXPORTS)
    start = allocator.allocate(len(trial), 'mode24 Master celebration and private particle states', 4)
    code, symbols, linkage = compose((body,), BASE+start, M24_SPECIAL_EXPORTS)
    assert len(code) == len(trial)
    changes = [(start, code), (SPRITE-BASE, branch(SPRITE, symbols['m24s_sprite'])),
               (EDITOR-BASE, equal_branch(EDITOR, symbols['m24s_editor']))]
    result = bytearray(image)
    for at, data in changes:
        result[at:at+len(data)] = data
    inverse = result[:]
    for at, data in changes:
        inverse[at:at+len(data)] = image[at:at+len(data)]
    assert inverse == image
    folder = Path(__file__).parent
    return result, dict(input_sha256=PARENT, source_sha256=SOURCE, prior_owner_sha256=OWNER,
                        output_sha256=sha(result), symbols=symbols, linkage=linkage,
                        storage_exports=owner['storage_exports'], prior_excluded_extents=prior,
                        allocations=allocator.allocations, whole_image_inverse=True,
                        modules={k: sha((folder/k).read_bytes()) for k in (Path(__file__).name, 'mode24_special.py')},
                        writes=[dict(offset=i, size=len(raw), before_sha256=sha(image[i:i+len(raw)]),
                                     after_sha256=sha(raw)) for i, raw in sorted(changes)])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('source', 'input', 'owner', 'output'):
        parser.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    image, report = build(args.input.read_bytes(), args.source.read_bytes(), args.owner.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'component.gba').write_bytes(image)
    manifest = args.output/'manifest.json'
    manifest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print(report['output_sha256'], sha(manifest.read_bytes()))


if __name__ == '__main__':
    main()
