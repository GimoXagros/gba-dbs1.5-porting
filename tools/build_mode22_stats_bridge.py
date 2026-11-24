"""Install stat and reset hooks on the Tamer Tag viewer with inherited ROM ownership."""
import argparse
import json
from pathlib import Path

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mode22_stats_bridge import assemble, patches

BEFORE = '63D7B68138CF7C1EBD96CEE168E1AFCD414A7591EDD9FBD8329A7E64C96F6248'
OWNER = '3500FD488577E1F849B1A063CA8098FF1B70ED06893993156AE29DEDE2136195'


def build(before, owner):
    if sha(before) != BEFORE or sha(owner) != OWNER:
        raise ValueError('mode 22 viewer image/ownership identity')
    parent = json.loads(owner)
    assert parent['output_sha256'] == BEFORE
    exports = parent['storage_exports']
    services = (exports['m22_read_snapshot'], exports['m22_write_snapshot'])
    assert services == (0x08FB6130, 0x08FB6230)
    extents = parent['prior_excluded_extents'] + [[r['start'], r['end']] for r in parent['allocations']]
    allocator = Allocator(before)
    exclude(allocator, extents)
    size = len(assemble(0x08f00000, *services)[0])
    offset = allocator.allocate(size, 'mode22 stat rows and verified reset', 4)
    assert before[offset:offset + size] == b'\xff' * size
    assert all(offset+size <= a or b <= offset for a,b in extents)
    code, symbols, link = assemble(BASE + offset, *services)
    assert len(code) == size
    changes = patches(before, symbols, predecessor_sha256=BEFORE)
    changes[offset] = code
    image = bytearray(before)
    inverse = bytearray(before)
    for at, data in changes.items():
        image[at:at+len(data)] = data
    inverse[:] = image
    for at, data in changes.items():
        inverse[at:at+len(data)] = before[at:at+len(data)]
    assert inverse == before
    files = [Path(__file__), Path(__file__).with_name('mode22_stats_bridge.py')]
    return image, dict(input_sha256=BEFORE, output_sha256=sha(image), prior_owner_sha256=OWNER,
        module_sha256={f.name:sha(f.read_bytes()) for f in files}, symbols=symbols, storage_exports=exports,
        prior_excluded_extents=extents, allocations=allocator.allocations, linkage=link,
        writes=[dict(offset=at, size=len(data), before_sha256=sha(before[at:at+len(data)]),
                     after_sha256=sha(data)) for at,data in sorted(changes.items())], whole_image_inverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'owner', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    image, report = build(args.input.read_bytes(), args.owner.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'component.gba').write_bytes(image)
    manifest = args.output/'manifest.json'
    manifest.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(report['output_sha256'], sha(manifest.read_bytes()))


if __name__ == '__main__':
    main()
