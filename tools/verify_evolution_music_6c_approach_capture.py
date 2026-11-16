"""Audit the completed ordinary 6C approach run using the shared v77 capture checks."""
import argparse
from pathlib import Path

import verify_evolution_music_three_capture as common

HOST = 'build/run_evolution_music_6c_approach_20261116.py'
OBSERVER = 'tools/bizhawk_probe_evolution_music_6c_approach.lua'
CONTACT = common.OBSERVER
PINS = {
    HOST: '574204F1B52DE5668F59CEEF506D9248059827C6B326CDEB61A866033706F8F0',
    OBSERVER: '404A0A087F852BCF3634963F3229F1F72A8DED463783E85E2B8EA760C1E11338',
    'tools/verify_evolution_music_three_capture.py': '7C63D2E061F643D879C97FB0F7E178E820CE4D52569D85ACA3494644BCEFEF13',
}


if __name__ == '__main__':
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    common.need(args.root_completed and not args.report.exists(), 'completed capture and fresh report required')
    common.HOST, common.OBSERVER = HOST, OBSERVER
    common.PINS.update(PINS)
    directory = common.ROOT / 'build/bizhawk-music-three-6c-20261116-b'
    result = common.audit(directory, 0x6C)
    common.need(result['launch']['contact_script_sha256'] == common.PINS[CONTACT], 'launch pre/post-pin of contact Lua')
    result['approach_verifier_sha256'] = common.sha(common.read(Path(__file__)))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(result, output, indent=2)
        output.write('\n')
    print('PASS', result['song'], common.sha(common.read(args.report)))
