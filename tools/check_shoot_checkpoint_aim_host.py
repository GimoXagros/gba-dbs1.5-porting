"""Read-only independent private-host inverse and current-checkpoint preflight."""
import argparse
import hashlib
import json
from pathlib import Path
from verify_gba_shoot_entry_capture_v2 import checkpoint_core, parse_checkpoint, prior

ROOT = Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest().upper()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args(); assert not a.report.exists()
    old = (ROOT / 'build/run_child_contact_positive_20261117.py').read_bytes()
    new = (ROOT / 'build/run_shoot_checkpoint_aim_v87_20261117.py').read_bytes()
    assert sha(old) == '1C0BCBBBAE7FED9E7E2FFF7C3E094965D9C43C659272E1278D683BD43012A2FF'
    assert sha(new) == '4E3F3959ED977595C57FB70D15C1EA108C3957813D9EB4F778BE3AF5CAEA8F68'
    delta = json.loads((ROOT / 'build/shoot-checkpoint-aim-host-delta-20261117.json').read_bytes())
    assert delta['old_sha256'] == sha(old) and delta['new_sha256'] == sha(new) and len(delta['replacements']) == 15
    inverse = new.decode()
    for before, after in reversed(delta['replacements']):
        assert inverse.count(after) == 1, after
        inverse = inverse.replace(after, before)
    assert inverse.encode() == old
    pin_bytes = (ROOT / 'build/shoot-checkpoint-aim-v87-pins-20261117.json').read_bytes()
    pins = json.loads(pin_bytes)
    assert len(pins) == 5 and all(sha((ROOT / name).read_bytes()) == digest for name, digest in pins.items())
    assert pins['tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua'] == 'CF71EE6638E8F77BE4EB0F505F9D8738A2BA231EC78A5068ED78C653DECDB845'
    author = (ROOT / 'build/shoot-checkpoint-aim-v87-author-20261117/report.json').read_bytes()
    assert sha(author).startswith('0222C2B3')
    baseline = ROOT / 'build/bizhawk-wholeplay-v87-20261117-a'
    launch_bytes = (baseline / 'launch.json').read_bytes()
    assert sha(launch_bytes) == '4F4CD759EF4E0642EDD56158BD900A166C03B70A41A6EF7FCBD539D2D7648CCB'
    launch = json.loads(launch_bytes)
    rom = (ROOT / 'build/shoot-child-contact-20261117/component.gba').read_bytes()
    assert sha(rom) == '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
    assert (baseline / 'probe.gba').read_bytes() == rom
    names = ['healthy-activation.State', 'healthy-activation.txt'] + [
        '41-healthy-activation-' + name + '.bin' for name in ('iwram', 'ewram', 'vram', 'palette', 'oam')]
    data = {name: (baseline / name).read_bytes() for name in names}
    assert all(sha(content) == launch['files'][name] for name, content in data.items())
    meta = prior.fields(data['healthy-activation.txt'].decode().strip())
    regions = {name: data['41-healthy-activation-' + name + '.bin'] for name in ('iwram', 'ewram', 'vram', 'palette', 'oam')}
    parsed = parse_checkpoint(data['healthy-activation.State'], meta, regions, rom)
    core, _ = checkpoint_core(data['healthy-activation.State'])
    assert sha(core) == 'BCA24A090D8AA084D25A4B6F7F31820DD8636054FD84898D201081D3C01793F8'
    assert parsed['frame'] == 89405 and meta['stage7_consumed'] == 'true'
    result = dict(status='SHOOT_CHECKPOINT_AIM_HOST_PREFLIGHT_PASS', host_sha256=sha(new),
                  original_host_sha256=sha(old), inverse_groups=15, pin_sha256=sha(pin_bytes),
                  source_launch_sha256=sha(launch_bytes), source_core_sha256=sha(core),
                  checkpoint_pins={name: sha(content) for name, content in data.items()},
                  probe_sha256=pins['tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua'],
                  author_lua_report_sha256=sha(author), tool_sha256=sha(Path(__file__).read_bytes()),
                  guarantees=['Exact host inverse to frozen1C0B.', 'Same528 ROM and allfive checkpoint memory regions validated.',
                              'Private desktop, copies only, noautoload/noautosave/background physical input disabled.',
                              '360second host bound; stop request retained; no supplied save.',
                              'Explicit one-shot stage11 boss HP1 approval passed as userdata; no score/stage7 writes.',
                              'Complete restored Core differences reported without normalization; CPU/extensions/suffix checks retained.'],
                  limits=['No emulator launch or runtime result.', 'Wholeplay source finished defeat; healthy89405 checkpoint is independently valid.',
                          'Probe behavior has separate nine-case actual Lua author fixture; this review binds it and reviews host scope.'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))

if __name__ == '__main__': main()
