"""Split three oversized mode 23 MP2K tracks into relocatable cartridge objects."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


BASE = '9EC8B6CD932407537FC364529891AE0FE310EA1FF5E4A5132FDFDBDF8158E49C'
BASE_MANIFEST = '3F59CECB61F4A1C43DEA8B9A861F790470B5E8BAB913E205AF4DBECF441DB90A'
MAX_FRAGMENT = 12000
OVERSIZED = {f'song-79-track-{i}' for i in range(3)}
GOTO = b'\xB2\0\0\0\0'
COMPONENT = 'mode23-audio-assets.bin'


def sha(value):
    return hashlib.sha256(value).hexdigest().upper()


def need(check, message):
    if not check:
        raise ValueError(message)


def quiet_boundaries(data):
    """Recognize only the emitted fully explicit TIE, EOT, wait and controls."""
    pc, key = 0, None
    quiet = set()
    while pc < len(data):
        opcode = data[pc]
        if key is None:
            quiet.add(pc)
        if 0x81 <= opcode <= 0xB0:
            pc += 1
        elif opcode in (0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 0xC1):
            need(data[pc + 1] < 128, 'explicit MP2K control operand')
            pc += 2
        elif opcode == 0xCF:
            need(key is None and data[pc + 1] < 128 and data[pc + 2] == 127, 'explicit native TIE')
            key = data[pc + 1]
            pc += 3
        elif opcode == 0xCE:
            need(key is not None and data[pc + 1] == key, 'explicit matching EOT')
            key = None
            pc += 2
        elif opcode == 0xB2:
            need(key is None and data[pc:] == GOTO, 'exact original final GOTO field')
            return quiet
        else:
            raise ValueError(f'unsupported split-track command {opcode:02X} at {pc:X}')
    raise ValueError('missing final loop branch')


def split_bundle(bundle: bytes, manifest: dict) -> tuple[bytes, dict]:
    need(sha(bundle) == BASE and manifest['bundle_sha256'] == BASE
         and manifest['bundle_bytes'] == len(bundle), 'exact frozen original audio bundle')
    need(manifest['table_offset'] == 0 and manifest['table_entries'] == 122
         and manifest['existing_entries'] == 112, 'frozen source song table contract')
    size = manifest['table_entries'] * 8
    output = bytearray(bundle[:size])
    objects, ranges, tracks, links = [], [], {}, []
    split = set()
    for row in manifest['asset_objects']:
        name, start, count = (row[k] for k in ('label', 'offset', 'size'))
        end = start + count
        data = bundle[start:end]
        need(len(data) == count and count > 0, f'{name} whole source object')
        beginnings = [0]
        if name in OVERSIZED:
            split.add(name)
            bounds = quiet_boundaries(data)
            while count - beginnings[-1] > MAX_FRAGMENT:
                a = beginnings[-1]
                b = max(offset for offset in bounds if a < offset <= a + MAX_FRAGMENT - len(GOTO))
                beginnings.append(b)
        fragments = []
        for index, (a, b) in enumerate(zip(beginnings, beginnings[1:] + [count], strict=True)):
            output.extend(bytes((-len(output)) % 4))
            local = len(output)
            label = name if not index else f'{name}-continuation-{index}'
            body = data[a:b] + (GOTO if b < count else b'')
            obj = dict(label=label, offset=local, size=len(body))
            output.extend(body)
            objects.append(obj)
            ranges.append((start + a, start + b, local))
            fragments.append(obj | dict(original_start=a, original_end=b, sha256=sha(body)))
            if index:
                previous = fragments[index - 1]
                links.append(dict(offset=previous['offset'] + previous['size'] - 4, relative_target=local))
        tracks[start] = fragments
    need(split == OVERSIZED, 'exact three track splits')

    def translate(old):
        if 0 <= old < size:
            return old
        mappings = [new + old - lo for lo, hi, new in ranges if lo <= old < hi]
        need(len(mappings) == 1, f'one originating object for local address {old:X}')
        return mappings[0]

    fixups = [dict(offset=translate(old['offset']), relative_target=translate(old['relative_target']))
              for old in manifest['local_u32_fixups']] + links
    need(len({entry['offset'] for entry in fixups}) == len(fixups)
         and all(entry['offset'] >= 112 * 8 and output[entry['offset']:entry['offset'] + 4] == bytes(4)
                 for entry in fixups), 'unique blank fixups, preserve all 112 old table rows')
    result = deepcopy(manifest)
    result['base_bundle_sha256'] = BASE
    result['status'] = 'MODE23_AUDIO_TRACKS_FRAGMENTED'
    result['splitter_sha256'] = sha(Path(__file__).read_bytes())
    result['asset_objects'] = objects
    result['local_u32_fixups'] = fixups
    result['voicegroup_offset'] = translate(manifest['voicegroup_offset'])
    for voice in result['voices']:
        if voice['local'] is not None:
            voice['local'] = translate(voice['local'])
    for song in result['song_map']:
        song['header_offset'] = translate(song['header_offset'])
        for track in song['tracks']:
            original = track['offset']
            first, *extra = tracks[original]
            track['offset'] = first['offset']
            if 'loop_offset' in track and extra:
                track['loop_offset'] = translate(original + track['loop_offset']) - first['offset']
                need(0 <= track['loop_offset'] < first['size'], 'reviewed loop destination is in the first fragment')
            if extra:
                track.update(logical_bytes=track['bytes'], logical_sha256=track['sha256'],
                             bytes=first['size'], sha256=first['sha256'], fragments=[first, *extra])
    raw = bytes(output)
    result['bundle_sha256'] = sha(raw)
    result['bundle_bytes'] = len(raw)
    result['fragments'] = dict(maximum_bytes=MAX_FRAGMENT, modified_tracks=sorted(split), new_gotos=len(links),
                               placement='Each fragment is a distinct object. Apply all local pointer fixups after placement.')
    return raw, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'fresh scatter-audio output directory')
    index = (args.input / 'manifest.json').read_bytes()
    need(sha(index) == BASE_MANIFEST, 'exact original audio manifest')
    data, manifest = split_bundle((args.input / COMPONENT).read_bytes(), json.loads(index))
    args.output.mkdir(parents=True)
    (args.output / COMPONENT).write_bytes(data)
    report = args.output / 'manifest.json'
    report.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(manifest['status'], len(data), sha(data), sha(report.read_bytes()))


if __name__ == '__main__':
    main()

