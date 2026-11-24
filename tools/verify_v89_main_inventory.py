"""Compare two original-input builds with the audited v88 and isolated v89 images."""
import argparse
import json
from pathlib import Path
from verify_id13_main_inventory import inventory, need, read, sha

ROOT = Path(__file__).resolve().parents[1]
OLD_AUDIT = ROOT / 'build/stage11-results-main-inventory-20261117/final.json'
OLD_PIN = '8B242ACAF24686779F0E2D05C8BB5A4EED6EFF0CFC30D3223927871BCFCFAE77'
MAIN_PIN = 'C093F525A06BDE56805D3A05E5FDE656A9D7EC0FC7A0A067963E242D0E2D30E9'
PINS = {
    'stage11-results.gba': 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C',
    'intermediate/mode23-scene/component.gba': 'B1EA99E48E3854453B202935FA068D1F5A0DE85245B1BCDD12DD1B949DB062DE',
    'intermediate/mode23-eligible/component.gba': '36A126206237A5C6A0670105C8023B5237FFA055733EF7795AE2A3A42A5E3B8A',
    'intermediate/mode23-title/component.gba': '280202556B6DC6AD624718A9F693C0466F2C6287F1A7681C46AFDB06D853D58B',
    'portrait-selector.gba': '9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5',
    'current-candidate.gba': 'F61053394798E4529F45A75E8363791EC8777774681F0B7354A69966EF780E3B',
    'current-candidate.json': '29B914EF1CD8403C70B5C92A8CF9478E40B0014DAC41CD8FCB9F7F181AC11505',
    'intermediate/initial-portrait-verification.json': '8B9B04E3F777CE49CE7CB60422C21DE18D0419E59ECB46C5A8C6B3CD7F5E575E',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('first', 'second', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    need(args.first.resolve() != args.second.resolve() and not args.report.exists(), 'distinct builds and fresh report')
    need(sha(read(OLD_AUDIT)) == OLD_PIN, 'prior independently audited inventory')
    need(sha(read(ROOT / 'tools/build_current_candidate.py')) == MAIN_PIN, 'v89 production builder')
    old = json.loads(read(OLD_AUDIT))['sha256_by_relative_path']
    files = inventory(args.first)
    need(files == inventory(args.second), 'identical complete inventories')
    changed = {name for name, digest in old.items() if files.get(name) != digest}
    need(changed == {'current-candidate.gba', 'current-candidate.json', 'build-manifest.json'}, 'all prior intermediates preserved')
    need(files['stage11-results.gba'] == old['current-candidate.gba'] and
         files['stage11-results.json'] == old['current-candidate.json'], 'exact v88 baseline retained')
    for name, expected in PINS.items():
        need(files[name] == expected, name)
    manifest = json.loads(read(args.first / 'build-manifest.json'))
    for name, digest in manifest['layers'].items():
        need(files[name] == digest, 'every advertised output layer matches')
    meta = manifest['collection_and_language']
    need(meta['root_rows'] == 5 and meta['portrait_ids'] == 15 and meta['tamer_tag_guarded'] and
         meta['title_languages'] == ['en', 'ja', 'ko', 'digicode'] and not meta['complete_port'], 'bounded public scope')
    report = dict(status='TITLE_AND_PORTRAITS_TWO_FRESH_BUILDS_PASS', main_sha256=MAIN_PIN,
                  baseline_audit_sha256=OLD_PIN, files_each=len(files), manifest_layers=len(manifest['layers']),
                  preserved_prior_files=len(old)-len(changed), new_files=len(files)-len(old),
                  final_sha256=files['current-candidate.gba'], sha256_by_relative_path=files,
                  checker_sha256=sha(read(Path(__file__))))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(report['status'], report['files_each'], sha(read(args.report)))


if __name__ == '__main__':
    main()
