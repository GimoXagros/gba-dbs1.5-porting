"""Observe ordinary mirrored aim from the exact v87 healthy checkpoint."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import time
import zlib

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools'))
from mgba_headless_gdb_capture import PrivateDesktopProcess
from verify_gba_shoot_entry_capture_v2 import checkpoint_core, parse_checkpoint, prior

sha = lambda data: hashlib.sha256(data).hexdigest().upper()
name = sys.argv[1]
assert re.fullmatch(r'bizhawk-collection-v89-20261124-[a-z]', name)
assert os.path.samefile('W:/', root)
launcher_bytes = Path(__file__).read_bytes()
pin_bytes = b'{\n  "tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua": "CF71EE6638E8F77BE4EB0F505F9D8738A2BA231EC78A5068ED78C653DECDB845",\n  "tools/bizhawk_probe_campaign_wholeplay_v86.lua": "66B9BB23039FDF1B7441559990E5FBCF227DF66F5026820F5A06DB1E45B27594",\n  "tools/bizhawk_gba_shoot_entry_observer.lua": "7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59",\n  "tools/verify_gba_shoot_entry_capture_v2.py": "4B5B30ACE08862B8943B0202886A796A4CFCADB33394DFFA45E8D8FFDABCFD68",\n  "tools/verify_gba_shoot_entry_capture.py": "970A6693D91215163E72F1437D70B5772F99E7EAF76FE907939748AE9251700D",\n  "tools/bizhawk_probe_gba_shoot_checkpoint_results_v88r4.lua": "6533778C81A901F173DEC973EAD1365A9511AEBB1E76AD3144A663F25388B311"\n}\n'
pins = json.loads(pin_bytes)
assert set(pins) == {'tools/bizhawk_probe_gba_shoot_checkpoint_results_v88r4.lua', 'tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua', 'tools/bizhawk_probe_campaign_wholeplay_v86.lua',
 'tools/bizhawk_gba_shoot_entry_observer.lua',
 'tools/verify_gba_shoot_entry_capture_v2.py', 'tools/verify_gba_shoot_entry_capture.py'}
pins['tools/bizhawk_probe_collection_route_v89.lua'] = 'E425C79B1665D93181FF0C4FBEDE9EF9AE60A29273234F25EE202EF0A8881A3A'
for path, digest in pins.items():
    assert sha((root / path).read_bytes()) == digest, path
rom = root / 'build/character-select-name-scene-r3-20261117/component.gba'
rom_data = rom.read_bytes()
rom_sha = '9B97967CFE6952C7C591805F9DEFCDD5815607A25986468D27F9F2AF3EC60DB5'
assert sha(rom_data) == rom_sha
baseline = root / 'build/bizhawk-wholeplay-v87-20261117-a'
source_rom = (baseline / 'probe.gba').read_bytes()
assert sha(source_rom) == '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
assert sha((baseline / 'launch.json').read_bytes()) == '4F4CD759EF4E0642EDD56158BD900A166C03B70A41A6EF7FCBD539D2D7648CCB'
baseline_launch = json.loads((baseline / 'launch.json').read_bytes())
checkpoint_names = ['healthy-activation.State', 'healthy-activation.txt'] + [
    '41-healthy-activation-' + region + '.bin' for region in ('iwram', 'ewram', 'vram', 'palette', 'oam')]
checkpoint_data = {filename: (baseline / filename).read_bytes() for filename in checkpoint_names}
assert all(sha(data) == baseline_launch['files'][filename] for filename, data in checkpoint_data.items())
state = checkpoint_data['healthy-activation.State']
meta = prior.fields(checkpoint_data['healthy-activation.txt'].decode().strip())
regions = {region: checkpoint_data['41-healthy-activation-' + region + '.bin']
           for region in ('iwram', 'ewram', 'vram', 'palette', 'oam')}
parsed = parse_checkpoint(state, meta, regions, source_rom)
source_core, _ = checkpoint_core(state)
assert sha(source_core) == 'BCA24A090D8AA084D25A4B6F7F31820DD8636054FD84898D201081D3C01793F8'
assert meta['stage7_consumed'] == 'true' and parsed['frame'] == 89405

exe = root / 'local/BizHawk-2.11.1/EmuHawk.exe'
assert sha(exe.read_bytes()) == 'F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD'
out = root / 'build' / name
out.mkdir(exist_ok=False)
alias = 'W:/build/' + name
reference = out / 'checkpoint'
reference.mkdir()
for filename, data in checkpoint_data.items():
    (reference / filename).write_bytes(data)
cfg = json.loads((root / 'build/bizhawk-gba-diagnostic-20261026/config.json').read_text(encoding='utf-8-sig'))
for index, entry in enumerate(cfg['PathEntries']['Paths']):
    entry['Path'] = alias + '/data/' + str(index)
    Path(entry['Path']).mkdir(parents=True)
cfg.update(AcceptBackgroundInput=False, AutoLoadLastSaveSlot=False, AutosaveSaveRAM=False,
           SoundEnabled=False, SoundOutputMethod=3)
def check_autoload(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'AutoLoad':
                assert child is False
            check_autoload(child)
    elif isinstance(value, list):
        for child in value:
            check_autoload(child)
check_autoload(cfg)
(out / 'config.json').write_text(json.dumps(cfg, indent=2), encoding='utf-8')
shutil.copyfile(rom, out / 'probe.gba')
args = ['--gdi', '--config=' + alias + '/config.json', '--lua=W:/tools/bizhawk_probe_collection_route_v89.lua',
        '--userdata=output:' + alias + ';checkpoint_dir:' + alias + '/checkpoint;probe_sha256:' + rom_sha + ';stage11_boss_authorization:user-approved-development-stage11-boss-hp1-once',
        alias + '/probe.gba']
report = dict(visible=False, physical_background_input=False, supplied_save_used=False, guest_writes=["stage11 live boss HP WORD1 once at a qualified ordinary B input"],
              phase_kind='current-checkpoint-source-results-and-autonomous-interstitials', rom_sha256=rom_sha,
              source_rom_sha256=sha(source_rom), source_core_sha256=sha(source_core), pins=pins, arguments=args,
              checkpoint_pins={filename: sha(data) for filename, data in checkpoint_data.items()})
done = out / 'collection-done.txt'
with PrivateDesktopProcess(exe, args, exe.parent) as process:
    report['pid'] = process.pid
    (out / 'launch.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    deadline = time.monotonic() + 360
    while not done.exists() and not (out / 'stop.request').exists() and time.monotonic() < deadline:
        time.sleep(.25)
    report['completed'] = done.exists()
    report['outcome'] = done.read_text(encoding='utf-8').strip() if done.exists() else 'partial'
    report['host_stop_requested'] = (out / 'stop.request').exists()
    report['host_deadline_reached'] = time.monotonic() >= deadline
report['loaded_rom_exact'] = (out / 'loaded-rom.bin').exists() and (out / 'loaded-rom.bin').read_bytes() == rom_data
report['scripts_unchanged'] = all(sha((root / path).read_bytes()) == digest for path, digest in pins.items())
report['checkpoint_copies_unchanged'] = all((reference / filename).read_bytes() == data for filename, data in checkpoint_data.items())
report['restored_core_exact_except_current_rom_crc'] = False
if (out / 'restored.State').exists():
    restored_core, _ = checkpoint_core((out / 'restored.State').read_bytes())
    expected_core = bytearray(source_core)
    struct.pack_into('<I', expected_core, 12, zlib.crc32(rom_data))
    report['restored_core_exact_except_current_rom_crc'] = restored_core == bytes(expected_core)
    report['restored_core_sha256'] = sha(restored_core)
    report['expected_restored_core_sha256'] = sha(bytes(expected_core))
    report['all_Core_byte_differences'] = [dict(offset=i, expected=a, actual=b)
        for i, (a, b) in enumerate(zip(expected_core, restored_core)) if a != b]
    length = struct.unpack_from('<I', source_core)[0]
    assert len(source_core) == len(restored_core)
    report['CPU_bank_equal'] = source_core[0x24:0x134] == restored_core[0x24:0x134]
    report['native_extensions_equal'] = source_core[4+0x61000:4+length] == restored_core[4+0x61000:4+length]
    report['managed_suffix_equal'] = source_core[4+length:] == restored_core[4+length:]
    report['qualification'] = 'Loaded-state observation; original full-Core identity is separately reported, never normalized.'
assert Path(__file__).read_bytes() == launcher_bytes
report['launcher_sha256'] = sha(launcher_bytes)
report['reviewed_pins_sha256'] = sha(pin_bytes)
report['files'] = {p.relative_to(out).as_posix(): sha(p.read_bytes()) for p in sorted(out.rglob('*'))
                   if p.is_file() and p.name != 'launch.json'}
(out / 'launch.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: report[key] for key in ('completed', 'outcome', 'loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged', 'restored_core_exact_except_current_rom_crc')}))
assert all(report[key] for key in ('loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged', 'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal'))
assert report['outcome'] == 'collection-shoot-returned'
if not report['completed']:
    sys.exit(2)
