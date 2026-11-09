"""Corrected native capture audit, including genuine mGBA checkpoints."""
import argparse
import inspect
import io
import json
from pathlib import Path
import struct
import sys
import zipfile
import zlib

import verify_gba_shoot_entry_capture as prior

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'build/gba-shoot-entry-capture-v2-qa-20261109'
sys.path.insert(0, str(ROOT / 'vendor'))
import pyzstd

PINS = dict(prior.PINS, **{'tools/bizhawk_gba_shoot_entry_observer.lua':
                          '7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59'})
SOURCE = {
    'MGBAHawk.IStatable.cs': '90CD3291A89CF20C2DCD1552AE139FABF442EDF365C67C0EB35FCD799F1E6971',
    'bizinterface.c': '3C720EB1FF5D33C62ECE48563231F990A64DDC34A7F7BB9213EAC429E74E2179',
    'serialize.h': 'B7437677E104AF90838FC0D54530779CE0063B9EA6EA91130192A3F716D2EAFF',
    'core-serialize.c': '6B11E8F4667E3B853BDDEACBBAF7BAC662E56FC2EFA9DC9F706AF4BFE143970E',
    'gba-serialize.c': '222A79513CD6B94354E3B56EE38E3EB46BA933B709C0D2686CADDB683A960482',
}
OFFSETS = dict(palette=(0x800, 0x400), oam=(0xC00, 0x400), vram=(0x1000, 0x18000),
               iwram=(0x19000, 0x8000), ewram=(0x21000, 0x40000))


def checkpoint_core(blob):
    """Return exact decompressed Core bytes; no state load or emulator action."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) and archive.testzip() is None
        assert {'BizState 1.0', 'BizVersion.txt', 'Core.bin.zst', 'SyncSettings.json'} <= set(names)
        assert archive.read('BizState 1.0').strip() == b'3'
        assert archive.read('BizVersion.txt').decode('utf-8-sig').strip() == 'Version 2.11.1'
        return pyzstd.decompress(archive.read('Core.bin.zst')), names


def parse_checkpoint(blob, metadata, expected_regions, rom):
    core, entries = checkpoint_core(blob)
    length = struct.unpack_from('<I', core)[0]
    assert length >= 0x61000 and len(core) == 4 + length + 21, 'complete native payload and managed suffix'
    native = core[4:4 + length]
    lag, lag_count, frame, overflow, cycles = struct.unpack_from('<?iiiq', core, 4 + length)
    assert frame == int(metadata['core'])
    assert struct.unpack_from('<I', native)[0] == 0x01000009
    assert struct.unpack_from('<I', native, 8)[0] == zlib.crc32(rom)
    assert native[0x10:0x20] == rom[0xA0:0xB0]
    equal = {}
    for name, expected in expected_regions.items():
        start, size = OFFSETS[name]
        assert len(expected) == size and native[start:start + size] == expected, 'checkpoint/dump memory mismatch ' + name
        equal[name] = True
    iw = native[0x19000:0x21000]
    ew = native[0x21000:0x61000]
    p, q = prior.long(iw, 0x489C), prior.long(iw, 0x48A0)
    assert prior.actor(p) and prior.actor(q)
    values = dict(mode=prior.word(iw, 0x2310), stage=iw[0x231E], difficulty=iw[0x231F],
                  progress=prior.word(iw, 0x232A), FIRST=p, SECOND=q, flags=prior.word(iw, 0x450A),
                  P1HP=prior.word(ew, p - 0x02000000 + 0x64),
                  P2HP=prior.word(ew, q - 0x02000000 + 0x64),
                  fighter=ew[p - 0x02000000 + 0x11], base=prior.word(ew, p - 0x02000000 + 8) >> 8 & 1,
                  input_task=prior.long(iw, 0x4510), battle_task=prior.long(iw, 0x4514))
    for name, value in values.items():
        assert value == int(metadata[name], 16 if name in ('progress', 'FIRST', 'SECOND', 'flags', 'input_task', 'battle_task') else 10), 'checkpoint metadata ' + name
    return dict(zip_entries=entries, core_sha256=prior.sha(core), native_sha256=prior.sha(native),
                native_bytes=length, frame=frame, lag_frame=lag, lag_count=lag_count,
                cycle_overflow=overflow, cycle_count=cycles, compared_regions=equal, state=values)


def checkpoint_controls(blob, metadata, regions, rom):
    core, _ = checkpoint_core(blob)
    length = struct.unpack_from('<I', core)[0]
    def repack(changes):
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(blob)) as old, zipfile.ZipFile(output, 'w') as new:
            for name in old.namelist():
                new.writestr(name, changes.get(name, old.read(name)))
        return output.getvalue()
    controls = []
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        info = archive.getinfo('Core.bin.zst')
        offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra) + info.compress_size // 2
    damaged = bytearray(blob)
    damaged[offset] ^= 1
    controls.append(('ZIP CRC corruption', bytes(damaged), metadata, regions))
    controls.append(('wrong BizVersion', repack({'BizVersion.txt': b'Version 2.11.0'}), metadata, regions))
    for name, offset in [('native length', 0), ('managed frame', 4 + length + 5), ('native ROM CRC', 4 + 8)]:
        damaged = bytearray(core)
        damaged[offset] ^= 1
        controls.append((name, repack({'Core.bin.zst': pyzstd.compress(bytes(damaged))}), metadata, regions))
    for region, expected in regions.items():
        changed = bytearray(expected)
        changed[0] ^= 1
        controls.append(('full ' + region + ' equality', blob, metadata, dict(regions, **{region: bytes(changed)})))
    controls.append(('metadata P1HP', blob, dict(metadata, P1HP='0'), regions))
    rejected = []
    for name, test_blob, test_metadata, test_regions in controls:
        try:
            parse_checkpoint(test_blob, test_metadata, test_regions, rom)
        except (AssertionError, ValueError, zipfile.BadZipFile, pyzstd.ZstdError, struct.error):
            rejected.append(name)
        else:
            raise AssertionError('actual checkpoint mutation accepted: ' + name)
    return rejected


def audit(directory):
    assert prior.sha(Path(prior.__file__).read_bytes()) == '970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D'
    assert {name: prior.sha((HERE / 'source' / name).read_bytes()) for name in SOURCE} == SOURCE
    # Reuse the unchanged capture checks with only the reviewed pins/archive changed.
    source = inspect.getsource(prior.audit)
    anchor = "frozen = ROOT / 'build/gba-shoot-entry-capture-qa-20261109/frozen-lua'"
    assert source.count(anchor) == 1
    namespace = dict(prior.__dict__, PINS=PINS, FROZEN=HERE / 'frozen-lua')
    exec(compile(source.replace(anchor, 'frozen = FROZEN'), '@v2-reused-capture-checks', 'exec'), namespace)
    result = namespace['audit'](directory)
    lines = (directory / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    captures = {row['capture']: row for row in map(prior.fields, lines) if 'observed_core' in row}
    names = {name.split('-', 1)[1]: name for name in captures}
    registers = {}
    for line in lines:
        if line.startswith('capture=') and ' reg ' in line:
            head, tail = line.split(' reg ')
            key, value = tail.split('=')
            registers.setdefault(head.split('=', 1)[1], {})[key] = int(value, 16)
    checkpoints = {}
    checkpoint_negatives = []
    rom = (directory / 'loaded-rom.bin').read_bytes()
    for name in ('stage7-hp1', 'healthy-activation', 'failure-observed'):
        path = directory / (name + '.State')
        if not path.exists():
            continue
        meta = prior.fields((directory / (name + '.txt')).read_text('utf-8').strip())
        frame = int(meta['core'])
        same_frame = [key for key, value in captures.items() if int(value['export_core']) == frame]
        regions = {region: (directory / f'{same_frame[-1]}-{region}.bin').read_bytes() for region in OFFSETS} if same_frame else {}
        parsed = parse_checkpoint(path.read_bytes(), meta, regions, rom)
        assert int(meta['input_relative']) == frame - int(next(prior.fields(line)['initial_core'] for line in lines if line.startswith('summary ')))
        if name == 'stage7-hp1':
            assert meta['stage7_consumed'] == 'true' and parsed['state']['stage'] == 7
            assert 0 < parsed['state']['P1HP'] < 0x8000 and parsed['state']['P2HP'] == 1
            assert result['boss_writes'] == 1 and regions
            checkpoint_negatives = checkpoint_controls(path.read_bytes(), meta, regions, rom)
        if name == 'healthy-activation':
            assert result['healthy_native_activation'] and regions
        if name == 'failure-observed':
            assert result['outcome'].startswith('failure:')
        parsed['metadata'] = meta
        parsed['same_frame_capture'] = same_frame[-1] if same_frame else None
        checkpoints[name] = parsed
    if result['boss_writes']:
        assert 'stage7-hp1' in checkpoints or result['outcome'].startswith('failure:checkpoint-')
    if result['outcome'].startswith('failure:'):
        flag = [line for line in lines if line.startswith('failure_checkpoint_saved=')]
        assert flag == ['failure_checkpoint_saved=' + str('failure-observed' in checkpoints).lower()]
    route = {}
    if 'boss-hit-post' in names:
        required = ['boss-hit-pre', 'boss-hit-post', 'healthy-root5', 'case5-predicate', 'case5-selected', 'scene-entry', 'scene-saved-health']
        assert all(name in names for name in required)
        rows = {name: captures[names[name]] for name in required}
        order = [int(rows[name]['observed_core']) for name in required]
        assert order == sorted(order)
        pre, post = rows['boss-hit-pre'], rows['boss-hit-post']
        rp, rq = registers[names['boss-hit-pre']], registers[names['boss-hit-post']]
        p, q = int(pre['FIRST'], 16), int(pre['SECOND'], 16)
        assert pre['before'] == pre['P2HP'] == '1' and post['P2HP'] == '0'
        assert rp['R4'] == rq['R4'] == int(pre['actual_attacker'], 16) == p
        assert rp['R5'] == rq['R5'] == int(pre['victim'], 16) == q
        assert rp['R8'] & 0xFFFF == int(pre['computed'], 16) == 0
        assert rp['R0'] == int(pre['damage']) == 1
        assert rp['R15'] == 0x0836E5E8 and rq['R15'] == 0x0836E5EC
        hp = int(rows['healthy-root5']['P1HP'])
        assert 0 < hp < 0x8000 and hp == int(pre['P1HP']) == int(post['P1HP'])
        pred = rows['case5-predicate']
        assert pred['eligible'] == 'true' and int(pred['stage']) == 7 and int(pred['difficulty']) == 2
        assert int(pred['progress'], 16) & 0x400 == 0
        assert rows['case5-selected']['selected'] == '085C8000' and registers[names['case5-selected']]['R8'] == 0x085C8000
        assert int(rows['scene-saved-health']['saved']) == hp
        saved = rows['scene-saved-health']
        owner = int(saved['owner'], 16)
        ew = (directory / (names['scene-saved-health'] + '-ewram.bin')).read_bytes()
        assert prior.actor(owner) and prior.word(ew, owner - 0x02000000 + 0x54) == hp
        route = dict(observed_cores={name: int(row['observed_core']) for name, row in rows.items()},
                     direct_first_damage=1, boss_before=1, boss_after=0, victory_p1_hp=hp,
                     selected_callback=0x085C8000, scene_owner=owner, saved_hp=hp,
                     initializer_observed='initializer-call' in names,
                     restore_observed='saved-health-restore' in names,
                     activation_observed='healthy-activation' in names,
                     full_pre_post_memory_timing='both exported after frame; scalar hooks establish before/after')
    final_ram = None
    if (directory / 'iwram.bin').exists():
        raw = {name: (directory / (name + '.bin')).read_bytes() for name in OFFSETS}
        assert all(len(raw[name]) == size for name, (_, size) in OFFSETS.items())
        iw, ew = raw['iwram'], raw['ewram']
        summary = next(prior.fields(line) for line in lines if line.startswith('summary '))
        p, q = prior.long(iw, 0x489C), prior.long(iw, 0x48A0)
        assert prior.actor(p) and prior.actor(q)
        final_ram = dict(mode=prior.word(iw, 0x2310), stage=iw[0x231E], difficulty=iw[0x231F],
                         progress=prior.word(iw, 0x232A), flags=prior.word(iw, 0x450A), FIRST=p, SECOND=q,
                         scene_control_4508=prior.word(iw, 0x4508),
                         P1HP=prior.word(ew, p - 0x02000000 + 0x64), P2HP=prior.word(ew, q - 0x02000000 + 0x64),
                         regions={name: prior.sha(value) for name, value in raw.items()})
        for name in ('mode', 'stage', 'difficulty', 'P1HP', 'P2HP'):
            assert final_ram[name] == int(summary[name]), 'final raw RAM/summary ' + name
        for name in ('progress', 'flags', 'FIRST', 'SECOND'):
            assert final_ram[name] == int(summary[name], 16)
        owners = {}
        for name, row in captures.items():
            if 'owner' in row:
                owner = int(row['owner'], 16)
                assert prior.actor(owner)
                at = owner - 0x02000000
                owners[f'{owner:08X}'] = dict(active=bool(prior.word(ew, at - 8) & 2),
                                            callback=prior.long(ew, at - 0x18),
                                            saved_hp=prior.word(ew, at + 0x54),
                                            payload_sha256=prior.sha(ew[at:at + 0x100]))
        final_ram['observed_scene_owners'] = owners
    old = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-a'
    old_launch = json.loads((old / 'launch.json').read_bytes())
    assert prior.sha((old / 'launch.json').read_bytes()) == '1C67BB4137D4EA8062E9D9EE5679208CA8B28A64CA35E42BD14D791D2CC539D0'
    prefix = {}
    for name in old_launch['files']:
        if name.startswith(('01-first-battle-', '02-first-score999-', '03-generic-grab-event48-')) or name in ('01-first-battle.png', '02-first-score999.png', '03-generic-grab-event48.png'):
            assert prior.sha((old / name).read_bytes()) == old_launch['files'][name]
            assert (directory / name).read_bytes() == (old / name).read_bytes(), 'ordinary prefix changed ' + name
            prefix[name] = old_launch['files'][name]
    assert len(prefix) == 21
    result.update(status='NATIVE_ENTRY_CAPTURE_V2_INTEGRITY_PASS', checkpoints=checkpoints,
                  ordinary_prefix_equal_files=len(prefix), checkpoint_source_pins=SOURCE,
                  parser_source='BizHawk2.11.1 and exact mGBA submodule94b1578f',
                  full_native_state_restored=False, final_raw_RAM=final_ram, native_route=route,
                  actual_checkpoint_mutations_rejected=checkpoint_negatives)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'fresh audit output'
    report = audit(args.capture.resolve())
    report['verifier_sha256'] = prior.sha(Path(__file__).read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', prior.sha(args.output.read_bytes()), report['outcome'])


if __name__ == '__main__':
    main()
