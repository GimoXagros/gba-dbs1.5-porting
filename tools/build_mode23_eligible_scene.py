"""Compose the reviewed Results, mode23 scene and persistent eligibility layers."""
import argparse
import json
from pathlib import Path
from types import FunctionType

import mode23_eligibility_storage as eligibility
from mode23_linker import compose
import verify_shoot_caller_resident as scanner

BASE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
RESULTS = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
SCENE = 'B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE'
MANIFEST = '3A412FCB9C87BA61F3CAB5CB3CF4B99CCEAEAE940D62C3E74019A29AD134ED9B'
CODE = 0xD8D200
STAGE_SPANS = ((0x89538, 0x8953C), (0xD8CB20, 0xD8CB2C))
PINS = {'mode23_eligibility_storage.py': 'ECB077770FB4620F3EB678D86AC74F3BB3D7DBFA33013FBE20B3D2FB9166E873',
        'mode23_linker.py': '20D276546966E63231AC23B4C1006B39BE64A0ACE8890F296DEFAC50D4F354EE',
        'verify_shoot_caller_resident.py': '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}
need, sha = scanner.need, scanner.sha


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'base', 'results', 'scene', 'scene-manifest', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    need(not a.output.exists(), 'fresh directory')
    source, base, results, scene, raw = (getattr(a, name).read_bytes() for name in
                                        ('source', 'base', 'results', 'scene', 'scene_manifest'))
    need(tuple(map(sha, (base, results, scene, raw))) == (BASE, RESULTS, SCENE, MANIFEST), 'exact reviewed layers')
    need(len(base) == len(results) == len(scene) == 0x1000000, '16MiB layers')
    for name, pin in PINS.items():
        need(sha(Path(__file__).with_name(name).read_bytes()) == pin, 'frozen module ' + name)
    manifest = json.loads(raw)
    need(manifest['input_sha256'] == BASE and manifest['output_sha256'] == SCENE, 'scene lineage')
    inverse = bytearray(results)
    for lo, hi in STAGE_SPANS:
        inverse[lo:hi] = base[lo:hi]
    need(bytes(inverse) == base, 'complete stage-only inverse')
    inverse, merged = bytearray(scene), bytearray(results)
    intervals = []
    for row in manifest['writes']:
        lo, hi = row['offset'], row['offset'] + row['size']
        need(all(hi <= first or lo >= last for first, last in STAGE_SPANS + tuple(intervals)), 'disjoint scene writes')
        need(sha(base[lo:hi]) == row['before_sha256'] and sha(scene[lo:hi]) == row['after_sha256'], 'actual scene bytes')
        need(results[lo:hi] == base[lo:hi], 'results leaves scene input intact')
        inverse[lo:hi], merged[lo:hi] = base[lo:hi], scene[lo:hi]
        intervals.append((lo, hi))
    need(len(intervals) == 187 and bytes(inverse) == base, 'complete scene inverse')
    combined = bytes(merged)
    for (lo, hi), pin in eligibility.NATIVE_ANCHORS.items():
        normalized = bytearray(combined[lo:hi])
        if lo <= 0x89538 and hi >= 0x8953C:
            normalized[0x89538-lo:0x8953C-lo] = base[0x89538:0x8953C]
        need(sha(normalized) == pin, 'shared native ABI unchanged except proved stage predicate')
    code, symbols, link = compose((eligibility.assembly(source, base),), 0x08000000 + CODE, eligibility.EXPORTS)
    stop = CODE + len(code)
    need(0xD8CE00 <= CODE < stop <= 0xD8D800 and combined[CODE:stop] == b'\xff' * len(code), 'new erased span outside child-contact reservation')
    need(all(stop <= lo or CODE >= hi for lo, hi in intervals), 'new code outside every scene write')
    census = FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((CODE, stop),)), argdefs=scanner.inbound.__defaults__)
    need(not census(combined), 'complete composed image has zero inbound references to eligibility span')
    patches = eligibility.patches(base, symbols)
    del patches[0x89538]
    need(set(patches) == {0x8B394, 0x1F9C4}, 'reuse installed final-stage predicate')
    writes = [(CODE, code)] + sorted(patches.items())
    for at, data in writes:
        need(all(at + len(data) <= lo or at >= hi for lo, hi in intervals + list(STAGE_SPANS)), 'no ownership collision')
        merged[at:at+len(data)] = data
    inverse = bytearray(merged)
    for at, data in writes:
        inverse[at:at+len(data)] = combined[at:at+len(data)]
    need(bytes(inverse) == combined, 'complete eligibility layer inverse')
    report = dict(status='MODE23_ELIGIBLE_SCENE_PREPARED_MENU_NOT_EXPOSED', source_sha256=sha(source),
                  base_sha256=BASE, results_sha256=RESULTS, scene_sha256=SCENE, scene_manifest_sha256=MANIFEST,
                  composed_before_eligibility_sha256=sha(combined), output_sha256=sha(merged),
                  builder_sha256=sha(Path(__file__).read_bytes()), module_pins=PINS,
                  exports=symbols, link=link, code_span=[CODE, stop],
                  writes=[dict(offset=at, size=len(data), before_hex=combined[at:at+len(data)].hex(), after_hex=data.hex()) for at, data in writes],
                  stage_predicate_reused=[0x89538, 0xD8CB20], strict_inbound_count=0,
                  new_global_RAM_bytes=0, whole_image_inverses=True, menu_exposed=False,
                  actual_game_execution=False, final_port_complete=False)
    a.output.mkdir(parents=True)
    (a.output / 'component.gba').write_bytes(merged)
    (a.output / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print(report['status'], report['output_sha256'], sha((a.output / 'manifest.json').read_bytes()))


if __name__ == '__main__':
    main()
