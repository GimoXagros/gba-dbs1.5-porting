"""Check the compact and warm-title rebase against the verified title controller."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import pack, unpack_from
from types import FunctionType

import verify_mode23_title_scene_installed as prior
from verify_mode23_title_pixel_assets import exact, need, sha


TITLE = '280202556B6DC6AD624718A9F693C0466F2C6287F1A7681C46AFDB06D853D58B'
MANIFEST = '91618BDC7A28BB36A829AABDD19271CDCB66747B305917E5174968AC38D9F412'
PIXELS = '178DEF852F565C069E79EE849D081DAA17FAD091DE9D9CEB9FBE5DF44174703D'
OLD_GATE = '94A5E5DBF2FF1CDA6AA8CEB24584338447F9812C5FE44AD60B922BD8AA99D2D7'
SCENE_OWNER = '3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B'


def owner_intervals(m, scene):
    prior_code = (0xDB0404, 0xDB5C04)
    need(prior_code[0] <= scene['code']['start'] < scene['code']['reserved_end'] == scene['root_entry_reservation'][0]
         < scene['root_entry_reservation'][1] == prior_code[1], 'Full prior code and reserved root extent')
    previous = [prior_code] + [(entry['start'], entry['end']) for entry in scene['allocations']]
    need([list(pair) for pair in previous] == m['prior_excluded_extents'] and len(previous) == 164,
         'Exclude the full original reservation and all 163 typed allocations')
    for row in m['allocations']:
        lo, hi = row['start'], row['end']
        need(all(hi <= start or end <= lo for start, end in previous), 'No title bytes in any previous scene reservation')
    return len(previous)


def controller_delta(old, new, old_m, new_m):
    need(old_m['module_sha256'] == new_m['module_sha256']
         and old_m['code_span'] == new_m['code_span']
         and old_m['symbols'] == new_m['symbols'] and old_m['link'] == new_m['link'],
         'Same 2656-byte placed controller and closed branch proof')
    old_assets, new_assets = (m['asset_pointers'] for m in (old_m, new_m))
    need({label for label in old_assets if old_assets[label] != new_assets[label]} == {'digicode_p0'},
         'One changed physical asset pointer')
    lo, hi = new_m['code_span']
    older = old[lo:hi]
    original = pack('<I', old_assets['digicode_p0'])
    relocated = pack('<I', new_assets['digicode_p0'])
    need(older.count(original) == 1 and older.replace(original, relocated) == new[lo:hi],
         'Entire controller binary changes only the single typed Digicode P0 table word')
    ptr = lo + older.index(original)
    need(ptr % 4 == 0 and unpack_from('<4I', new, ptr - 12) ==
         tuple(new_assets[lang + '_p0'] for lang in prior.LANGUAGES), 'Exact four physically selected title atlases')
    for offset in (0x90A18, 0x90BBC, 0x90C70, 0x90E34):
        need(old[offset:offset + 4] == new[offset:offset + 4], 'Four unchanged retail hook words')
    return dict(controller_pointer_word_bytes=4, controller_changed_bytes=sum(a != b for a, b in zip(original, relocated)),
                changed_pointer_word_offset=ptr, old_pointer=old_assets['digicode_p0'],
                installed_pointer=new_assets['digicode_p0'], unchanged_native_hooks=4)


def audit_composition(before, rom, m, atlas, metadata, original):
    # Reuse the complete installed pointer and inverse checks with the new exact builder path.
    def exact_builder(path, digest):
        if path == prior.ROOT / 'tools/build_mode23_title_scene_r2.py':
            path = path.with_name('build_mode23_title_scene_r4.py')
        return exact(path, digest)

    examine = FunctionType(prior.composition.__code__, dict(prior.composition.__globals__, exact=exact_builder))
    return examine(before, rom, m, atlas, metadata, original)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    need(not a.report.exists(), 'Fresh independent report')
    work = prior.ROOT / 'build'
    old_dir, new_dir = (work / f'mode23-title-scene-r{revision}-20261117' for revision in (2, 4))
    earlier = json.loads(exact(work / 'mode23-title-installed-independent-20261117/final.json', OLD_GATE))
    need(earlier['installed_sha256'] == prior.TITLE and earlier['native_full_title_initializer_executed'], 'Reviewed title baseline')
    old = exact(old_dir / 'component.gba', prior.TITLE)
    old_m = json.loads(exact(old_dir / 'manifest.json', prior.MANIFEST))
    rom = exact(new_dir / 'component.gba', TITLE)
    m = json.loads(exact(new_dir / 'manifest.json', MANIFEST))
    before = exact(work / 'mode23-eligible-scene-20261117/component.gba', prior.ELIGIBLE)
    pixels = json.loads(exact(work / 'mode23-title-compact-prompt-independent-20261117/report.json', PIXELS))
    atlas_dir = work / 'mode23-title-assets-r4-20261117'
    atlas = exact(atlas_dir / 'assets.bin', pixels['assets_sha256'])
    metadata = json.loads(exact(atlas_dir / 'manifest.json', pixels['manifest_sha256']))
    original = exact(a.source, prior.SOURCE)
    owner = json.loads(exact(work / 'mode23-scene-v88-r3-20261117/manifest.json', SCENE_OWNER))
    old_intervals = owner_intervals(m, owner)
    delta = controller_delta(old, rom, old_m, m)
    proof = audit_composition(before, rom, m, atlas, metadata, original)
    paths = [prior.title_route(rom, m, lang, False) for lang in prior.LANGUAGES]
    paths.append(prior.title_route(rom, m, 'digicode', True))
    need(all(path['root_parts'] == 110 for path in paths), 'All five rows at the original frame width and parts budget')
    report = dict(status='MODE23_COMPACT_WARM_TITLE_INSTALLED_PASS', checker_sha256=sha(Path(__file__).read_bytes()),
                  installed_sha256=TITLE, manifest_sha256=MANIFEST, independent_pixel_report=PIXELS,
                  native_controller_delta=delta, excluded_prior_regions=old_intervals, placement=proof,
                  complete_native_initialization_and_routes=paths, live_BizHawk_title_executed=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(report['status'], sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
