"""Audit a root-finalized native entry capture without launching an emulator."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
ROM = 'D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
PINS = {
    'tools/bizhawk_probe_gba_shoot_entry.lua': 'D40E44C090D21FB722D8FF72D3C20241869A1C93DC80B9826E454B36996C0A6D',
    'tools/bizhawk_gba_shoot_entry_observer.lua': 'E620B76A96ED09E6E19DED5E3EE8134D14E62A6022A332D899E08E3493FF76FF',
    'tools/bizhawk_probe_gba_collision.lua': '7BE2872543FC4F3AA7980FB0C7A9EC0563A73743185D082957A4A7159C79FCE9',
    'tools/bizhawk_probe_gba_collision_producer.lua': '146D7645A8F11557EE83E9DD5014A53A41AECD76F9DD0B0E269795E1D7781963',
}
HOST = '019A9E583F8A5B04E819746F1802FC808B7501378417D6436801FEBA2084C1A0'
SIZES = dict(iwram=0x8000, ewram=0x40000, vram=0x18000, palette=0x400, oam=0x400, display=0x60)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def fields(line):
    return dict(re.findall(r'(\w+)=([^ ]+)', line))


def word(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def long(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def actor(pointer):
    return 0x02010018 <= pointer <= 0x02010018 + 51 * 0x118 and (pointer - 0x02010018) % 0x118 == 0


def ledger(lines):
    rows = [fields(line) for line in lines if line.strip()]
    scores = bosses = 0
    prior = -1
    for row in rows:
        core, stage = int(row['core']), int(row['stage'])
        first, second = int(row['FIRST'], 16), int(row['SECOND'], 16)
        assert core >= prior and actor(first) and actor(second) and first != second
        prior = core
        assert row['bytes'] == '2' and row['verified'] == 'true'
        assert 0 < int(row['P1HP']) < 0x8000
        address, before, requested, after = int(row['address'], 16), int(row['before']), int(row['requested']), int(row['after'])
        if row['kind'] == 'score':
            assert 0 <= stage <= 10 and stage != 7
            assert address == first + 0x66 and requested == after == 999 and before != 999
            assert int(row['P1score_before']) == before and int(row['neighbor_left']) == int(row['P1HP'])
            scores += 1
        else:
            assert row['kind'] == 'boss' and stage == 7
            assert address == second + 0x64 and requested == after == 1 and 1 < before < 0x8000
            bosses += 1
    assert bosses <= 1
    return rows, scores, bosses


def snapshot(directory, name):
    blobs = {region: (directory / f'{name}-{region}.bin').read_bytes() for region in SIZES}
    assert {key: len(value) for key, value in blobs.items()} == SIZES
    png = (directory / (name + '.png')).read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack_from('>II', png, 16) == (240, 160)
    iw, ew = blobs['iwram'], blobs['ewram']
    p, q = long(iw, 0x489C), long(iw, 0x48A0)
    result = dict(mode=word(iw, 0x2310), stage=iw[0x231E], difficulty=iw[0x231F],
                  game_kind=word(iw, 0x4502), flags=word(iw, 0x450A), first=p, second=q)
    if actor(p) and actor(q):
        def actor_state(pointer):
            at = pointer - 0x02000000
            return dict(active=bool(word(ew, at - 8) & 2), kind=word(ew, at + 4) & 15,
                        flags=word(ew, at + 4), index=ew[at + 0x10], fighter=ew[at + 0x11],
                        self=long(ew, at + 0x14), opponent=long(ew, at + 0x18),
                        child=long(ew, at + 0x28),
                        hp=word(ew, at + 0x64), score=word(ew, at + 0x66))
        result['p1'], result['p2'] = actor_state(p), actor_state(q)
        a = long(iw, 0x4D3C)
        if actor(a):
            result['aux_pointer'], result['aux'] = a, actor_state(a)
        services = {}
        for key, offset in (('input', 0x4510), ('battle', 0x4514)):
            pointer = long(iw, offset)
            if actor(pointer + 0x18):
                services[key] = dict(header=pointer, active=bool(word(ew, pointer - 0x02000000 + 0x10) & 2), callback=long(ew, pointer - 0x02000000))
        result['services'] = services
    return result


def audit(directory):
    launch_bytes = (directory / 'launch.json').read_bytes()
    launch = json.loads(launch_bytes)
    assert launch['launcher_sha256'] == HOST and launch['pins'] == PINS
    assert launch['loaded_rom_exact'] and launch['scripts_unchanged'] and launch['rom_sha256'] == ROM
    assert launch['visible'] is False and launch['physical_background_input'] is False and launch['supplied_save_used'] is False
    assert sha((ROOT / 'build/run_gba_shoot_entry_20261109.py').read_bytes()) == HOST
    frozen = ROOT / 'build/gba-shoot-entry-capture-qa-20261109/frozen-lua'
    assert {name: sha((frozen / Path(name).name).read_bytes()) for name in PINS} == PINS
    inventory = {path.relative_to(directory).as_posix(): sha(path.read_bytes())
                 for path in sorted(directory.rglob('*')) if path.is_file() and path.name != 'launch.json'}
    assert inventory == launch['files'], 'entire finalized recursive inventory'
    rom = (directory / 'loaded-rom.bin').read_bytes()
    assert len(rom) == 0x800000 and sha(rom) == ROM and rom == (directory / 'probe.gba').read_bytes()
    cfg = json.loads((directory / 'config.json').read_bytes())
    assert cfg['SoundEnabled'] is False
    for key in ('AcceptBackgroundInput', 'AutoLoadLastSaveSlot', 'AutosaveSaveRAM'):
        assert cfg[key] is False
    def autoload(value):
        if isinstance(value, dict):
            for key, child in value.items():
                assert key != 'AutoLoad' or child is False
                autoload(child)
        elif isinstance(value, list):
            for child in value:
                autoload(child)
    autoload(cfg)
    prefix = 'W:/build/' + directory.name + '/data/'
    assert all(entry['Path'].startswith(prefix) for entry in cfg['PathEntries']['Paths'])
    generated_save_paths = [name for name in inventory if name.lower().endswith(('.sav', '.saveram'))]
    lines = (directory / 'shoot-entry-trace.txt').read_text('utf-8').splitlines()
    captures, registers = {}, {}
    for line in lines:
        if line.startswith('capture='):
            row = fields(line)
            if 'observed_core' in row:
                assert row['capture'] not in captures
                assert int(row['observed_core']) <= int(row['export_core']) and row['memory'] == 'outer-frame-boundary'
                captures[row['capture']] = row
            else:
                match = re.fullmatch(r'capture=(\S+) reg (\S+)=([0-9A-F]+)', line)
                assert match
                registers.setdefault(match[1], {})[match[2]] = int(match[3], 16)
    decoded = {}
    for name, row in captures.items():
        assert all('R' + str(index) in registers[name] for index in range(16))
        decoded[name] = snapshot(directory, name)
    ledger_path = directory / 'shoot-entry-writes.txt'
    rows, scores, bosses = ledger(ledger_path.read_text('utf-8').splitlines() if ledger_path.exists() else [])
    done = directory / 'shoot-entry-done.txt'
    outcome = done.read_text('utf-8').strip() if done.exists() else 'partial'
    assert launch['completed'] == done.exists() and launch['outcome'] == outcome
    summary = [fields(line) for line in lines if line.startswith('summary ')]
    if done.exists():
        assert len(summary) == 1 and summary[0]['outcome'] == outcome
        assert int(summary[0]['score_writes']) == scores and int(summary[0]['boss_writes']) == bosses
        assert summary[0]['stage11_writes'] == '0'
    immediate = directory / 'shoot-entry-first-failure.txt'
    failure = fields(immediate.read_text('utf-8').splitlines()[0]) if immediate.exists() else None
    if outcome.startswith('failure:'):
        assert failure and failure['outcome'] == outcome
    healthy = outcome == 'healthy-native-shoot-activation'
    names = {re.sub(r'^\d+-', '', name): name for name in captures}
    healthy_state = directory / 'healthy-activation.State'
    if healthy:
        assert not failure and bosses == 1 and healthy_state.is_file() and healthy_state.stat().st_size > 0
        required = ['boss-hit-pre', 'boss-hit-post', 'healthy-root5', 'scene-saved-health', 'saved-health-restore', 'activation-tail', 'healthy-activation']
        assert all(name in names for name in required)
        assert sorted(int(captures[names[name]]['observed_core']) for name in required) == [int(captures[names[name]]['observed_core']) for name in required]
        h = decoded[names['healthy-activation']]
        assert h['mode'] == 7 and h['stage'] == 11 and h['game_kind'] == 2 and h['flags'] & 4
        assert h['p1']['active'] and 0 < h['p1']['hp'] < 0x8000
        saved, restored = captures[names['scene-saved-health']], captures[names['saved-health-restore']]
        assert int(saved['saved']) == int(restored['restored']) == h['p1']['hp']
        assert saved['owner'] == restored['owner']
        pre, post = captures[names['boss-hit-pre']], captures[names['boss-hit-post']]
        rpre, rpost = registers[names['boss-hit-pre']], registers[names['boss-hit-post']]
        assert rpre['R15'] == 0x0836E5E8 and rpost['R15'] == 0x0836E5EC
        assert rpre['R4'] == rpost['R4'] == int(pre['actual_attacker'], 16)
        assert rpre['R5'] == rpost['R5'] == int(pre['victim'], 16)
        assert pre['before'] == '1' and rpre['R8'] & 0xFFFF == int(pre['computed'], 16)
        assert int(pre['computed'], 16) == 0 or int(pre['computed'], 16) >= 0x8000
    else:
        assert not healthy_state.exists() and 'healthy-activation' not in names, 'failure cannot claim healthy checkpoint'
    refusal = None
    if 'typed-owner-refusal' in names:
        h = decoded[names['typed-owner-refusal']]
        p1, p2, aux = h['p1'], h['p2'], h['aux']
        checks = dict(p1_active=p1['active'], p2_active=p2['active'], aux_active=aux['active'],
                      p1_kind0=p1['kind'] == 0, p2_kind3=p2['kind'] == 3,
                      p1_index0=p1['index'] == 0, p1_fighter0=p1['fighter'] == 0,
                      p2_index1=p2['index'] == 1, p2_fighter15=p2['fighter'] == 15,
                      p1_self=p1['self'] == h['first'], p2_self=p2['self'] == h['second'],
                      p1_opponent=p1['opponent'] == h['second'], p2_opponent=p2['opponent'] == h['first'],
                      second_aux=p2['child'] == h['aux_pointer'], aux_second=aux['child'] == h['second'],
                      aux_first=aux['opponent'] == h['first'], frozen_aux_kind6=aux['kind'] == 6)
        refusal = dict(capture=names['typed-owner-refusal'], observed_core=int(captures[names['typed-owner-refusal']]['observed_core']),
                       export_core=int(captures[names['typed-owner-refusal']]['export_core']), checks=checks,
                       failed_frozen_actor_checks=[key for key, passed in checks.items() if not passed])
    return dict(status='NATIVE_ENTRY_CAPTURE_INTEGRITY_PASS', launch_sha256=sha(launch_bytes),
                file_count=len(inventory), rom_sha256=ROM, pins=PINS, outcome=outcome,
                healthy_native_activation=healthy, score_writes=scores, boss_writes=bosses,
                stage11_writes=0, write_ledger=rows, captures=decoded,
                generated_save_paths=generated_save_paths,
                requested_sound_method=3, final_sound_method=cfg['SoundOutputMethod'], sound_enabled=False,
                typed_owner_refusal=refusal,
                immediate_first_failure=failure, capture_count=len(captures),
                emulator_launched_by_auditor=False, final_port_QA=False,
                limits=['write-time guard evidence uses frozen Lua and its ledger; full memory exports are later',
                        'capture integrity does not itself prove source parity or completed gameplay'])


def selfcheck():
    base = 'core=20 kind=boss address=02010194 bytes=2 before=44 requested=1 stage=7 FIRST=02010018 SECOND=02010130 P1HP=8 P1score_before=0 neighbor_left=0 neighbor_right=0 after=1 verified=true'
    assert ledger([base])[2] == 1
    controls = [base.replace('stage=7', 'stage=11'), base.replace('P1HP=8', 'P1HP=0'),
                base.replace('requested=1', 'requested=0'), base.replace('address=02010194', 'address=0201007C'),
                base.replace('verified=true', 'verified=false')]
    for bad in controls:
        try:
            ledger([bad])
        except AssertionError:
            pass
        else:
            raise AssertionError('ledger control accepted')
    try:
        ledger([base, base])
    except AssertionError:
        pass
    else:
        raise AssertionError('duplicate boss action accepted')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'fresh audit output'
    selfcheck()
    report = audit(args.capture.resolve())
    report['verifier_sha256'] = sha(Path(__file__).read_bytes())
    report['ledger_negative_controls'] = 6
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(args.output.read_bytes()), report['outcome'])


if __name__ == '__main__':
    main()
