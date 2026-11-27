"""Compare cold opening captures at callback age 8 from run_opening_playback.py."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image


USA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'


def checked(directory, digest):
    run = json.loads((directory / 'launch.json').read_bytes())
    assert run['loaded_rom_exact'] and run['rom_sha256'] == digest
    assert hashlib.sha256((directory / 'loaded-rom.bin').read_bytes()).hexdigest().upper() == digest
    assert run['visible'] is False and run['guest_writes'] == [] and not run['skip']
    assert run['status'] in ('title', 'bounded-after-title')


def first_frame(directory, step):
    path = min(directory.glob(f'frame-*-step{step:02d}.png'))
    with Image.open(path) as image:
        return image.convert('RGB')


def actor_pixels(image):
    dx, dy = (8, 8) if image.size == (240, 160) else (0, 0)
    pixels = image.load()
    # Isolate the primary fighter from the scrolling art at the extreme sides.
    return {(x, y) for y in range(144) for x in range(20, 198)
            if pixels[x + dx, y + dy] != pixels[4 + dx, y + dy]}


def verify(usa, source, candidate, candidate_hash):
    for directory, digest in ((usa, USA), (source, WSC), (candidate, candidate_hash)):
        checked(directory, digest)
    native = [*range(7), *range(11, 19)]
    for step in native:
        assert first_frame(usa, step).tobytes() == first_frame(candidate, step).tobytes(), step
    actors = []
    for step in range(7, 11):
        expected = actor_pixels(first_frame(source, step))
        actual = actor_pixels(first_frame(candidate, step))
        difference = len(expected ^ actual)
        # Mixed-to-white color rounding makes one edge pixel visible in callback 10.
        assert len(expected) >= 1200 and difference <= (1 if step == 10 else 0), (step, difference)
        actors.append({'step': step, 'wsc_actor_pixels': len(expected), 'mask_difference': difference})
    return {'candidate': candidate_hash, 'retail_frame_matches': native, 'source_fighters': actors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('usa', 'source', 'candidate'):
        parser.add_argument(name, type=Path)
    parser.add_argument('candidate_hash')
    args = parser.parse_args()
    print(json.dumps(verify(args.usa, args.source, args.candidate, args.candidate_hash.upper()), indent=2))
