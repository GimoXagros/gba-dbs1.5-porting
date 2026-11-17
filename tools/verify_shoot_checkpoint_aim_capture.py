"""Independent failed-aim capture integrity and bounded animation/geometry replay.

Reconstruction executes the native animation tick, rectangle producer and overlap
test in memory. It is not a new emulator run or an early-frame producer trace.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from verify_gba_shoot_entry_capture_v2 import checkpoint_core
from verify_shoot_child_contact_component import Machine
from analyze_character_p1_oracle import pointer, source as parse_p1

ROOT = Path(__file__).resolve().parents[1]
BASE, P, Q = 0x08000000, 0x02011710, 0x02011828
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def fields(line): return dict(part.split('=', 1) for part in line.split() if '=' in part)
def fill(m, at, data):
    for i, byte in enumerate(data): m.put(at + i, byte, 1)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args(); assert not a.report.exists()
    launch_bytes = (a.capture / 'launch.json').read_bytes(); launch = json.loads(launch_bytes)
    assert launch['completed'] and launch['outcome'] == 'failure:wholeplay-live-aim-owner'
    assert not launch['host_stop_requested'] and not launch['host_deadline_reached']
    assert all(launch[key] for key in ('loaded_rom_exact', 'scripts_unchanged', 'checkpoint_copies_unchanged', 'CPU_bank_equal', 'native_extensions_equal', 'managed_suffix_equal'))
    for name, digest in launch['files'].items(): assert sha((a.capture / name).read_bytes()) == digest, name
    for name, digest in launch['pins'].items(): assert sha((ROOT / name).read_bytes()) == digest, name
    rom = (a.capture / 'loaded-rom.bin').read_bytes()
    assert sha(rom) == launch['rom_sha256'] == '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
    original, _ = checkpoint_core((a.capture / 'checkpoint/healthy-activation.State').read_bytes())
    restored, _ = checkpoint_core((a.capture / 'restored.State').read_bytes())
    assert len(original) == len(restored)
    differences = [dict(offset=i, expected=x, actual=y) for i, (x, y) in enumerate(zip(original, restored)) if x != y]
    assert differences == launch['all_Core_byte_differences'] and len(differences) == 15
    assert original != restored and not launch['restored_core_exact_except_current_rom_crc']
    for region in ('iwram', 'ewram', 'vram', 'palette', 'oam'):
        assert (a.capture / ('01-checkpoint-before-' + region + '.bin')).read_bytes() == (a.capture / ('checkpoint/41-healthy-activation-' + region + '.bin')).read_bytes()
    decisions = [fields(x) for x in (a.capture / 'shoot-checkpoint-aim-decisions.txt').read_text().splitlines()[1:]]
    bycore = {int(x['core']): x for x in decisions}
    assert list(bycore) == list(range(89405, 93897))
    eligible = [x for x in decisions if x['B_candidate'] == 'true']
    assert len(eligible) == 1 and eligible[0]['core'] == '89500'
    write_lines = (a.capture / 'wholeplay-stage11-writes.txt').read_text().splitlines()
    assert len(write_lines) == 1
    write = fields(write_lines[0])
    assert all(write[k] == v for k, v in dict(core='89500', address='0201188C', bytes='2', before='37', requested='1', after='1', verified='true').items())
    assert write['authorization'] == 'user-approved-development-stage11-boss-hp1-once'
    terminal = fields((a.capture / 'failure-observed.txt').read_text())
    assert all(terminal[k] == v for k, v in dict(core='93897', mode='7', stage='11', P1HP='0', P2HP='1').items())
    events = (a.capture / 'wholeplay-trace.txt').read_text().splitlines()
    assert [fields(x)['event'] for x in events] == ['healthy', 'stage11-hp1']
    ewram = (a.capture / '02-wholeplay-stage11-hp1-ewram.bin').read_bytes()
    assert struct.unpack_from('<I', ewram, P - 0x02000000)[0] == 0x083587F0
    assert struct.unpack_from('<H', ewram, P - 0x02000000 + 0xBA)[0] == 87
    source = a.source.read_bytes()
    assert sha(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    source_p1 = pointer(source, 0x740006)
    rows, commands, _ = parse_p1(source, source_p1)
    assert source_p1 == 0x32D990 and rows[87][0] == 8
    native_rows = [struct.unpack_from('<4H2I', rom, 0xD6700 + i * 16) for i in range(8)]
    assert [r[0] & 255 for r in native_rows] == [3, 5, 6, 3, 3, 3, 6, 5]
    assert [r[0] & 255 for r in commands[87]] == [4, 6, 8, 4, 4, 4, 7, 6]
    active_rectangles = []
    for index in (3, 4):
        src = source_p1 + commands[87][index][5]
        native = native_rows[index][5] - BASE
        assert source[src:src + 10] == rom[native:native + 10]
        active_rectangles.append(dict(command=index, source=f'{src:06X}', native=f'{native:06X}', values=struct.unpack_from('<Hhhhh', rom, native)))
    # Captured state at89501 already includes one attack update. Execute only
    # subsequent native animation updates; physics/callback cadence is qualified.
    m = Machine(rom, seed=2)
    fill(m, P, ewram[P - 0x02000000:P - 0x02000000 + 0x100])
    m.put(0x030022F6, 1, 2)
    sp, end = m.r[13], m.r[14]
    reconstructed = []
    for core in range(89501, 89537):
        command = m.get(P + 0xC6, 2)
        rect = m.get(m.get(P + 0xD0) + 12)
        if rect:
            assert command in (3, 4)
            # Actual attack-list producer: left retains signed x, right negates;
            # y is added unchanged. Exercise both to prove the mirror operation.
            produced = []
            for facing in (0, 0x4000):
                n = Machine(rom)
                n.r[4], n.r[1] = rect, 0x030049B8
                n.put(0x03004C5C, facing, 2)
                n.put(0x03004C58, 0x0E00, 2); n.put(0x03004C5A, 0x1500, 2)
                n.run(0x08353CD8, {0x08353D28}, max_steps=40)
                produced.append(tuple(n.get(0x030049B8 + off, 2) for off in (6, 8, 10, 12)))
            # Unknown within-frame producer epoch is bracketed by adjacent
            # recorded target coordinates. Every bracket remains nonoverlap.
            overlaps = []
            for sample in (core - 1, core, core + 1):
                row = bycore[sample]
                assert row['facing'] == 'left' and row['freeze'] == '0' and row['upper_event'] == '1'
                x, y = 0xE00 + int(row['dx']), 0x1500 + int(row['dy'])
                n = Machine(rom)
                ax, ay, aw, ah = produced[0]
                # Native135D4 stack: attacker halfH/halfW/Y/X,
                # victim halfH/halfW/Y/X, output pointer.
                for i, value in enumerate((ah, aw, ay, ax, 112, 112, y, x, 0, 0x02030000)):
                    n.put(n.r[13] + i * 4, value)
                n.run(0x080135D4, {n.r[14]}, max_steps=80)
                overlaps.append(n.r[0])
            assert overlaps == [0, 0, 0]
            reconstructed.append(dict(frame=core, command=command, left=produced[0], right=produced[1], adjacent_epoch_overlaps=overlaps))
        m.r[14] = end
        for i, value in enumerate((1, 0, P + 0xAC)): m.put(sp + i * 4, value)
        m.run(0x08012A84, {end}, max_steps=400)
        assert m.r[13] == sp
    assert reconstructed and reconstructed[0]['frame'] == 89515
    result = dict(status='SHOOT_AIM_FAILED_CAPTURE_INTEGRITY_AND_BOUNDED_GEOMETRY_PASS',
                  gameplay_success=False, launch_sha256=sha(launch_bytes), tool_sha256=sha(Path(__file__).read_bytes()),
                  files_verified=len(launch['files']), core_differences=differences,
                  one_eligible_input=eligible[0], authorized_write=write, terminal=terminal,
                  source_p1=f'{source_p1:06X}', source_native_rectangles=active_rectangles,
                  reconstruction=reconstructed,
                  conclusion='Single accepted event87 attack starts while target moves through and then behind the left-facing actor; active rectangles arrive after it crosses, with no overlap in every adjacent-frame bracket.',
                  limits=['Animation/rectangle/overlap instructions execute independently from captured state; early attack producer hooks were not retained.',
                          'Assumes one unpaused native animation update per frame; exact producer epoch is not observed, and adjacent-frame brackets are checked.',
                          'This is a direct FIRST rectangle, not a projectile. No left-facing implementation fault is established.',
                          'Loaded Core differs in15 explicitly retained bytes. No normalized full-Core identity or terminal success.'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], sha(a.report.read_bytes()))

if __name__ == '__main__': main()
