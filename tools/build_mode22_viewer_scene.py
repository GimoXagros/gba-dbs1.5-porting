"""Install the Tamer Tag viewer over the verified stack-backed EEPROM transport."""
import argparse
import json
from pathlib import Path

from build_character_select_name_scene import exclude
from build_mode23_title_scene_r2 import Allocator
from mode22_viewer_install import plan, sha

INPUT = 'D390CA3B9620A2A9F3DAC214F2EC9DD3C8D0D8A91787BA78735AB8AC2E11749F'
OWNER = '8DE4DEBE8364CF25B60C7B6C9354124BBC71357A7EC39224B85CC478F24FBB9C'


def build(source, before, owner_bytes, resources, audio):
    assert sha(before) == INPUT and sha(owner_bytes) == OWNER
    parent = json.loads(owner_bytes)
    assert parent['output_sha256'] == INPUT
    extents = parent['prior_excluded_extents'] + [[r['start'], r['end']] for r in parent['allocations']]
    allocation = Allocator(before)
    exclude(allocation, extents)
    reader = parent['exports']['m22_read_snapshot']
    spans, meta = plan(source, before, allocation, reader, *resources, *audio)
    image = bytearray(before)
    records = []
    for at, data, label in spans:
        image[at:at+len(data)] = data
        records.append(dict(offset=at, size=len(data), purpose=label,
                            before_sha256=sha(before[at:at+len(data)]), after_sha256=sha(data)))
    inverse = bytearray(image)
    for row in records:
        at, n = row['offset'], row['size']
        inverse[at:at+n] = before[at:at+n]
    assert inverse == before
    modules = [Path(__file__)] + [Path(__file__).with_name(name + '.py') for name in
        ('mode22_viewer_install', 'mode22_viewer', 'mode22_viewer_graphics', 'mode22_source_scene', 'mode23_linker')]
    manifest = dict(input_sha256=INPUT, output_sha256=sha(image), parent_owner_sha256=OWNER,
                    module_sha256={f.name:sha(f.read_bytes()) for f in modules}, **meta,
                    prior_excluded_extents=extents, allocations=allocation.allocations,
                    storage_exports=parent['exports'], writes=records, whole_image_inverse=True)
    return image, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('input','owner','source','resources','audio','output'):
        parser.add_argument('--'+option, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    def read_bundle(folder, name):
        return (folder/name).read_bytes(), (folder/'manifest.json').read_bytes()
    image, report = build(args.source.read_bytes(), args.input.read_bytes(), args.owner.read_bytes(),
                          read_bundle(args.resources,'resources.bin'), read_bundle(args.audio,'audio.bin'))
    args.output.mkdir(parents=True)
    (args.output/'component.gba').write_bytes(image)
    manifest = args.output/'manifest.json'
    manifest.write_text(json.dumps(report,indent=2)+'\n', encoding='utf-8', newline='\n')
    print('PASS', report['output_sha256'], sha(manifest.read_bytes()), len(report['writes']))


if __name__ == '__main__':
    main()

