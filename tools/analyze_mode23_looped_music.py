"""Verify the eight source tracks of the two looping mode-23 scores."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from analyze_wsc_evolution_music import WSC_SHA, extract, sha
from build_wsc_evolution_music import compile_channel, noise_samples, pitch_divisor


SONGS = (0xF0, 0xF4)
SPEEDS = (8, 6)
CONTROL = (0xA0, 0xA2, 0xA3, 0xA4, 0xA5)
STATE_KEYS = ('wave', 'volume', 'effect', 'vibrato', 'stereo_ceiling', 'envelope_mode', 'envelope_period', 'noise_mode')
# Pinned opcode anchors from the original source interpreter.
ANCHORS = {
    0x7545DE: '3cfd751c',
    0x7545F7: '8b04890543ebc1',
    0x754669: '880574058b45018904e943',
    0x75467C: '3cf0751480e40f8ac402e402c432e48bfe83c71603f8ebd9',
    0x7544CB: 'be d0 4c',
    0x754560: '8a440c0c18e68e',
}


def need(ok, detail):
    if not ok:
        raise ValueError(detail)


def source_updates(speed, total):
    """Source 75420A--754232 decrements only on noncarry updates."""
    fraction = 0
    update = 0
    clock = [(0, 0)]
    while len(clock) <= total:
        update += 1
        fraction += speed
        if fraction >= 16:
            fraction -= 16
        else:
            clock.append((update, fraction))
    need(all(u == (16*(t-1)//(16-speed)+1) for t, (u, _) in enumerate(clock) if t), 'independent closed-form timing')
    return clock


def split_track(payload):
    need(len(payload) >= 12 and len(payload) % 2 == 0, 'complete paired source track')
    pairs = tuple(zip(payload[4::2], payload[5::2], strict=True))
    need(pairs[-2:] == ((0xB0, 0xF0), (0xFF, 0xFF)), 'exact unconditional slot-0 loop then end marker')
    slots = [i for i, pair in enumerate(pairs) if pair == (0xFD, 0xF0)]
    need(len(slots) == 1, 'unique slot-0 save')
    marker = slots[0]
    allowed = set(CONTROL) | set(range(0xC0, 0xD0))
    for op, arg in pairs[:marker] + pairs[marker+1:-2]:
        if op < 0xA0:
            need(arg > 0, 'every source note or rest has a duration')
        else:
            need(op in allowed, f'unsupported source opcode {op:02X}')
    return pairs[:marker], pairs[marker+1:-2], 4+2*(marker+1), len(payload)-4


def initial_state(payload):
    _, wave, volume, effect = payload[:4]
    need(wave < 16 and volume <= 15 and effect == 0, 'source initial channel fields')
    return dict(wave=wave, volume=volume, effect=effect, vibrato=0xFE, stereo_ceiling=0xFF,
                envelope_mode=0, envelope_period=0, noise_mode=0)


def commands(pairs, state, channel, tick):
    events = []
    for op, arg in pairs:
        if op < 0xA0:
            key = 36+12*(op >> 4)+(op & 15) if op & 15 < 12 else None
            if key is not None:
                need(0 <= key < 128, 'seven-bit native keys')
            events.append(dict(tick=tick, duration=arg, packed_note=op, midi_note=key, **state))
            tick += arg
        elif op == 0xA0:
            need(arg <= 15, 'volume')
            state['volume'] = arg
        elif op == 0xA2:
            need(arg < 16, 'wave selection')
            if state['effect'] and channel & 1:
                state['noise_mode'] = arg
            else:
                state['wave'] = arg
        elif op == 0xA3:
            state['vibrato'] = arg
        elif op == 0xA4:
            need(arg in (0, 1) and channel == 3, 'source channel-3 noise enable')
            state['effect'] = arg
        elif op == 0xA5:
            state['stereo_ceiling'] = arg
        else:
            need(0xC0 <= op <= 0xCF, 'only remaining source envelope selector')
            state['envelope_mode'] = op & 15
            state['envelope_period'] = arg
    return events, tick


def duration(pairs):
    return sum(value for op, value in pairs if op < 0xA0)


def stable_loop(intro, loop, state, channel, speed):
    t0, period = duration(intro), duration(loop)
    need(period > 0, 'positive loop period')
    clock = source_updates(speed, t0+65*period)
    _, tick = commands(intro, state, channel, 0)
    need(tick == t0, 'source intro duration')
    boundaries, seen = [], {}
    for i in range(65):
        update, fraction = clock[tick]
        control = tuple(state[name] for name in STATE_KEYS)
        key = (update % 16, fraction, control)
        if key in seen:
            start = seen[key]
            return dict(intro_ticks=t0, repeat_ticks=period, first_update=clock[t0][0],
                        first_repeat_update=clock[t0+period][0], boundaries=boundaries,
                        nonsteady_loop_count=start, steady_loop_count=i-start,
                        steady_tick_period=tick-boundaries[start]['tick'],
                        steady_update_period=update-boundaries[start]['update'])
        boundaries.append(dict(tick=tick, update=update, fractional_remainder=fraction,
                               global_vibrato_phase=update % 16, **state))
        seen[key] = i
        _, end = commands(loop, state, channel, tick)
        need(end-tick == period, 'each taken loop has identical source score ticks')
        tick = end
    raise ValueError('no bounded source timing/control recurrence')


def score_track(payload, meta, expected_speed):
    intro, loop, back, branch = split_track(payload)
    state = initial_state(payload)
    channel = meta['hardware_channel']
    speed = payload[0]
    quiet = init_is_silent = payload[:4] == bytes(4)
    need(speed == (0 if quiet else expected_speed), 'typed source speed')
    lead, tick = commands(intro, state, channel, 0)
    repeated, end = commands(loop, state, channel, tick)
    notes = lead+repeated
    typed = [note for note in notes if note['midi_note'] is not None and note['volume']]
    need(bool(typed) != quiet and (not init_is_silent or not repeated[0]['midi_note']), 'silent rest loop versus audible tracks')
    if quiet:
        need(payload[4:] == bytes.fromhex('a000fdf01f01b0f0ffff'), 'exact quiet loop')
    clock = source_updates(speed, end)
    for note in notes:
        t = note['tick']
        n = note['duration']
        note['update'] = clock[t][0]
        note['duration_updates'] = clock[t+n][0]-clock[t][0]
    proof = stable_loop(intro, loop, initial_state(payload), channel, speed)
    note_set = {(n['noise_mode'] if n['effect'] and channel == 3 else None, n['wave']) for n in typed}
    need(all(mode in (None, 0) for mode, _ in note_set), 'only source noise mode 0 in these two songs')
    waves = sorted(wave for mode, wave in note_set if mode is None)
    noise_modes = sorted({mode for mode, _ in note_set if mode is not None})
    compiled = dict(**meta, header=list(payload[:4]), notes=notes, silent_infinite_rest=quiet)
    summary = dict(**meta, speed=speed, loop_target_payload_offset=back, loop_jump_payload_offset=branch,
                   one_pass_notes=len(typed), first_pitch_update=typed[0]['update'] if typed else None,
                   all_source_pcm_waves=waves, source_noise_modes=noise_modes, silent_loop=quiet,
                   one_pass_control_counts={f'{k:02X}': v for k, v in sorted(Counter(
                       op for op, _ in intro+loop if op >= 0xA0).items())},
                   **proof)
    return compiled, summary


def pcm_data(source, wave):
    old = source[0x754CC0+wave*16:0x754CC0+(wave+1)*16]
    need(len(old) == 16, 'typed source 32-sample waveform')
    return bytes((16*((old[i//2] >> ((i%2)*4)) & 15)-120)&255 for i in range(32))


def independent_noise():
    shift = [0]*15
    wave = bytearray()
    for i in range(1, 32768):
        bit = 1 ^ shift[7] ^ shift[0]
        shift = shift[1:]+[bit]
        wave.append(120 if bit else 136)
        if not any(shift):
            need(i == 32767, 'first mode-0 return exactly at full LFSR period')
            break
    need(not any(shift) and bytes(wave) == noise_samples(), 'independent noise generator equals existing native reconstruction')
    return bytes(wave)


def analyze(source):
    need(sha(source) == WSC_SHA, 'original WSC 1.5 pin')
    for a, literal in ANCHORS.items():
        want = bytes.fromhex(literal)
        need(source[a:a+len(want)] == want, f'original instruction anchor {a:06X}')
    songs = []
    channel_data = {}
    for sid, speed in zip(SONGS, SPEEDS, strict=True):
        rows = []
        for i in range(4):
            payload, meta = extract(source, sid+i)
            compiled, row = score_track(payload, meta, speed)
            channel_data[sid+i] = compiled
            rows.append(row)
        need([r['state_offset'] for r in rows] == [168,210,252,294], 'four regular song channels')
        need([r['hardware_channel'] for r in rows] == [0,1,3,2], 'source channel permutation')
        need([r['silent_loop'] for r in rows] == [False,False,False,True], 'three playing channels and one muted')
        songs.append(dict(source_id=sid, priority=4, tracks=rows))
    waves = sorted({wave for song in songs for r in song['tracks'] for wave in r['all_source_pcm_waves']})
    voice_ids = {wave: i for i, wave in enumerate(waves)} | {'noise0': len(waves)}
    modes = {}
    for song in songs:
        for row in song['tracks']:
            track_source = channel_data[row['id']]
            stream, detail = compile_channel(source, track_source, voice_ids)
            need(stream[-1] == 0xB1, 'native finite preview ending FINE')
            need(detail['silent_loop_elided'] == row['silent_loop'], 'explicit quiet-loop preview treatment')
            if row['source_noise_modes']:
                need(all('source_noise' in n for n in detail['notes']) and all(n['source_noise'] for n in detail['notes']),
                     'native existing converter selected source mode 0')
            row['existing_native_converter_preview'] = dict(bytes=len(stream), sha256=sha(stream),
                                                           max_pitch_error_cents=detail['max_pitch_error_cents'])
        modes[song['source_id']] = sorted({mode for r in song['tracks'] for mode in r['source_noise_modes']})
    waves_report = [dict(wave=wave, raw=0x754CC0+16*wave, samples=32, sha256=sha(pcm_data(source,wave))) for wave in waves]
    noise = independent_noise()
    result = dict(status='MODE23_LOOPED_MUSIC_SOURCE_PASS', source_sha256=WSC_SHA, songs=songs,
                  original_pcm_waves=waves_report, noise_mode=0, noise_samples=len(noise), noise_sha256=sha(noise),
                  noise_modes_by_song=modes, pcm_frequency_field=round(3072000*4*1024/pitch_divisor(source,0)),
                  future_native_requirements=['Use a native backward branch with a pinned target after the source intro.',
                    'Emit initial loop pass separately when controls at the first marker differ from the stable recurrence.',
                    'Carry speed fraction, global vibrato phase, waveform/noise state and gating across source B0-F0 jumps.',
                    'The existing converter was exercised only on one-pass preview streams that stop at FINE. No looping native stream or ROM was installed.'])
    return result


def negative_checks(source):
    payload, meta = extract(source, 0xF0)
    marker = payload.index(bytes.fromhex('fdf0'))
    corruptions = {
        'wrong-saved-slot': payload[:marker+1]+b'\xf1'+payload[marker+2:],
        'counted-instead-of-infinite-jump': payload[:-4]+b'\xb1\xf0\xff\xff',
        'unknown-opcode': payload[:4]+b'\xa6\x01'+payload[6:],
        'duration-zero': payload[:marker-1]+b'\x00'+payload[marker:],
        'missing-end': payload[:-2],
    }
    rejected = []
    for label, bad in corruptions.items():
        try:
            score_track(bad, meta, 8)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError(f'corrupted mode-23 score accepted: {label}')
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report')
    source = args.source.read_bytes()
    report = analyze(source)
    report['negative_controls'] = negative_checks(source)
    report['checker_sha256'] = sha(Path(__file__).read_bytes())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
