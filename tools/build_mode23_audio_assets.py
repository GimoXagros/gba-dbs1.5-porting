"""Build relocatable mode-23 M4A assets without patching a ROM or allocating space."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from math import ceil, lcm, log2
from pathlib import Path
import struct

from analyze_mode23_looped_music import commands, duration, initial_state, pcm_data, source_updates, split_track, stable_loop
from analyze_wsc_evolution_music import WSC_SHA, extract, sha
from build_wsc_evolution_music import compile_channel, noise_samples, pitch_divisor, signed8, source_amplitude


BASE = 0x08000000
BEFORE = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
OLD_TABLE, OLD_COUNT = 0xD33000, 112
LOADERS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
SFX_BY_SOURCE = (
    (0x7C, 0x70, 1, 4), (0x84, 0x71, 1, 4), (0x98, 0x72, 1, 4), (0xD5, 0x73, 1, 4),
    (0xD6, 0x74, 1, 6), (0xD7, 0x75, 2, 4), (0xD9, 0x76, 1, 6), (0xDA, 0x77, 1, 6),
)
BGM_BY_SOURCE = ((0xF0, 0x78), (0xF4, 0x79))
WAVE_REUSE = {1: 0xD33398, 9: 0xD33400, 10: 0xD33434}
NOISE0_REUSE = 0xD334D0
TAPS = (14, 10, 13, 4)
WS_CLOCKS_PER_UPDATE = 256*159
TEMPO = bytes((0xBC, 0, 0xBB, 95))
WAITS = (*range(25), 28, 30, 32, 36, 40, 42, 44, 48, 52, 54, 56, 60, 64, 66, 68, 72, 76, 78, 80, 84, 88, 90, 92, 96)
WAIT_CODES = {duration: 0x80+i for i, duration in enumerate(WAITS)}
COMPONENT = 'mode23-audio-assets.bin'


def need(condition, description):
    if not condition:
        raise ValueError(description)


def addr(data, raw):
    return struct.unpack_from('<I', data, raw)[0]


def put_wait(stream, ticks):
    for duration in reversed(WAITS[1:]):
        count, ticks = divmod(ticks, duration)
        stream.extend(bytes((WAIT_CODES[duration],))*count)
        if not ticks:
            return


def compact_track(encoded):
    """Retain the exact timed engine commands from the existing native converter."""
    need(encoded[:4] == TEMPO and encoded[-1] == 0xB1, 'restricted existing M4A compiler result')
    compact = bytearray()
    i = 4
    widths = {op: 2 for op in (0xBD, 0xBE, 0xBF, 0xC0, 0xC1, 0xCE)}
    widths[0xCF] = 3
    while i < len(encoded)-1:
        opcode = encoded[i]
        if opcode == 0x81:
            stop = i+1
            while stop < len(encoded)-1 and encoded[stop] == 0x81:
                stop += 1
            put_wait(compact, stop-i)
        else:
            need(opcode in widths, f'unexpected existing compiler opcode {opcode:02X}')
            stop = i+widths[opcode]
            compact.extend(encoded[i:stop])
        i = stop
    return bytes(compact)


def noise_pcm(mode):
    """Source noise starts from reset and uses the mode-specific feedback tap."""
    need(0 <= mode < len(TAPS), 'supported typed WonderSwan noise mode')
    register = 0
    samples = bytearray()
    visited = {}
    while register not in visited:
        visited[register] = len(samples)
        bit = (1 ^ (register >> 7) ^ (register >> TAPS[mode])) & 1
        register = ((register << 1) | bit) & 0x7FFF
        samples.append(120 if bit else 136)
    loop = visited[register]
    need(loop < len(samples) <= 32767, 'finite noise prefix and repeating LFSR state')
    if mode == 0:
        need(loop == 0 and bytes(samples) == noise_samples(), 'retained noise mode0 sequence')
    return bytes(samples), loop


def sample_blob(pcm, loop, frequency):
    need(0 <= loop < len(pcm), 'PCM loop sample exists')
    return struct.pack('<4I', 0x40000000, frequency, loop, len(pcm)) + pcm + pcm[loop:loop+1]


def finite_source(payload, info):
    speed, wave, volume, header_effect = payload[:4]
    channel = info['hardware_channel']
    need(speed < 16 and wave < 16 and volume <= 15, 'bounded finite source header')
    state = dict(wave=wave, volume=volume, noise=0, effect=header_effect if channel & 1 else 0,
                 sweep=header_effect if channel == 2 else 0, stereo_ceiling=0xFF,
                 envelope_mode=0, envelope_period=0)
    pairs = tuple(zip(payload[4::2], payload[5::2], strict=True))
    need(pairs[-1] == (0xFF, 0xFF), 'full finite source terminator')
    tick = 0
    notes = []
    active = None
    unbound_holds = []
    for op, arg in pairs[:-1]:
        if op < 0xA0:
            need(arg > 0, 'positive finite source duration')
            if op & 15 < 12:
                active = dict(packed=op, start=tick, span=0, segments=[], sweep=state['sweep'],
                              voice=f'noise{state["noise"]}' if channel == 3 and state['effect'] else state['wave'])
                notes.append(active)
            else:
                active = None
        elif op == 0xA7:
            need(arg > 0, 'positive hold duration')
            if active is None:
                unbound_holds.append((tick, arg))
        if op < 0xA0 or op == 0xA7:
            if active:
                active['segments'].append((tick, arg, state.copy()))
                active['span'] += arg
            tick += arg
        elif op == 0xA0:
            need(arg <= 15, 'source volume width')
            state['volume'] = arg
        elif op == 0xA1:
            need(channel == 2 and (arg == 0 or arg & 15), 'typed source sweep command')
            state['sweep'] = arg
        elif op == 0xA2:
            need(arg < 16, 'source wave selector')
            state['noise' if channel & 1 and state['effect'] else 'wave'] = arg & 7 if channel == 3 and state['effect'] else arg
        elif 0xC0 <= op <= 0xCF:
            state['envelope_mode'], state['envelope_period'] = op&15, arg
        else:
            raise ValueError(f'unsupported finite source opcode {op:02X} for {info["id"]:02X}')
    need(notes and tick > 0, 'finite SFX is audible score data')
    return notes, tick, speed, unbound_holds


def sweep_curve(source, packed, command, length):
    base = pitch_divisor(source, packed)
    if not command:
        return [base]*length
    step = signed8(source[0x754B40+(command&15)-1])
    trigger = 8192*((command>>4)+1)
    # Sample the source register at each driver-update boundary. Native bends
    # cannot emit the intermediate hardware clocks within that same update.
    return [2048-((2048-base+elapsed*WS_CLOCKS_PER_UPDATE//trigger*step)&0x7FF)
            for elapsed in range(length)]


def semitone(divisor, frequency):
    return 60+12*log2((3072000/divisor)/(frequency/1024))


def bent_key(pitches, preferred):
    key = preferred
    if max(abs(p-key) for p in pitches) > 23:
        key = round((max(pitches)+min(pitches))/2)
    extent = max(1, ceil(max(abs(p-key) for p in pitches)))
    need(0 <= key < 128 and extent <= 24, 'bounded TIE key and bend span')
    return key, extent


def finite_track(source, descriptor, voice_ids, frequency):
    payload, info = descriptor
    notes, ticks, speed, inherited_holds = finite_source(payload, info)
    clock = source_updates(speed, ticks)
    final = clock[ticks][0]
    stream = bytearray(TEMPO)
    cursor, max_error, audible = 0, 0.0, 0
    for note in notes:
        start = clock[note['start']][0]
        end = clock[note['start']+note['span']][0]
        length = end-start
        put_wait(stream, start-cursor)
        stream.extend((0xBD, voice_ids[note['voice']]))
        pitches = [semitone(divisor, frequency)
                   for divisor in sweep_curve(source, note['packed'], note['sweep'], length)]
        raw = note['packed']
        key, extent = bent_key(pitches, 36+12*(raw>>4)+(raw&15))
        stream.extend((0xC1, extent))
        previous = None
        count = 0
        for tick, n, state in note['segments']:
            for update in range(clock[tick][0], clock[tick+n][0]):
                age = update-start
                left,right = source_amplitude(source, state, age)
                volume = round((left+right)*127/30)
                pan = min(127, round(128*right/(left+right))) if left+right else 64
                bend = max(-64, min(63, round((pitches[age]-key)*64/extent)))
                max_error = max(max_error, 100*abs((key+bend*extent/64)-pitches[age]))
                values = (volume,pan,bend+64)
                if values != previous:
                    put_wait(stream, count)
                    for i, value in enumerate(values):
                        if previous is None or value != previous[i]:
                            stream.extend((0xBE+i, value))
                    if previous is None:
                        stream.extend((0xCF,key,127))
                    previous, count = values, 0
                count += 1
                audible += volume > 0
        put_wait(stream, count)
        stream.extend((0xCE,key))
        cursor = end
    put_wait(stream, final-cursor)
    stream.append(0xB1)
    need(audible > 0, 'finite SFX has audible native updates')
    return bytes(stream), dict(source_id=info['id'], kind='finite', updates=final, source_note_count=len(notes),
                              max_pitch_error_cents=max_error, source_inherited_holds=inherited_holds,
                              uses_source_sweep=any(note['sweep'] for note in notes))


def define_music(source, sid):
    tracks = []
    for i in range(4):
        payload, info = extract(source, sid+i)
        first, repeat, _, _ = split_track(payload)
        speed = payload[0]
        quiet = payload[:4] == bytes(4)
        proof = stable_loop(first, repeat, initial_state(payload), info['hardware_channel'], speed)
        tracks.append(dict(payload=payload, info=info, first=first, repeat=repeat,
                           proof=proof, quiet=quiet))
    audible = [track for track in tracks if not track['quiet']]
    lead = max(t['proof']['nonsteady_loop_count'] for t in audible)
    period = lcm(*(t['proof']['steady_loop_count'] for t in audible))
    need(lead == 1 and period == (1 if sid == 0xF0 else 5), 'verified simultaneous three-track recurrence')
    return tracks, lead, period


def render_source_segment(source, track, events, clock, voice_ids):
    for row in events:
        a = row['tick']
        row['update'] = clock[a][0]
        row['duration_updates'] = clock[a+row['duration']][0]-row['update']
    compiled = dict(track['info'], header=list(track['payload'][:4]), notes=events, silent_infinite_rest=False)
    native, details = compile_channel(source, compiled, voice_ids)
    return compact_track(native), details['max_pitch_error_cents']


def music_track(source, track, lead, period, voice_ids):
    sid = track['info']['id']
    if track['quiet']:
        need(track['payload'][4:] == bytes.fromhex('a000fdf01f01b0f0ffff'), 'exact source mute track')
        # The source loop really is muted. Keep its one-update repeat instead
        # of substituting a finite marker, preserving the track lifetime.
        return TEMPO+b'\x81\xB2'+bytes(4), dict(source_id=sid, kind='quiet-loop', intro_updates=0,
                                               repeat_updates=1, loop_offset=len(TEMPO))
    first, repeat = track['first'], track['repeat']
    speed = track['payload'][0]
    split = duration(first)+lead*duration(repeat)
    final = split+period*duration(repeat)
    clock = source_updates(speed, final)
    state = initial_state(track['payload'])
    channel = track['info']['hardware_channel']
    prefix, tick = commands(first+repeat*lead, state, channel, 0)
    steady, end = commands(repeat*period, state, channel, tick)
    need(tick == split and end == final, 'shared source music period')
    prefix_body, initial_error = render_source_segment(source, track, prefix, clock, voice_ids)
    steady_body, steady_error = render_source_segment(source, track, steady, clock, voice_ids)
    target = len(TEMPO)+len(prefix_body)
    return TEMPO+prefix_body+steady_body+b'\xB2'+bytes(4), dict(source_id=sid, kind='score-loop',
        intro_updates=clock[split][0], repeat_updates=clock[final][0]-clock[split][0], loop_offset=target,
        source_initial_loop_passes=lead, source_loops_per_native_goto=period,
        source_intro_note_count=sum(n['midi_note'] is not None for n in prefix),
        source_repeat_note_count=sum(n['midi_note'] is not None for n in steady),
        max_pitch_error_cents=max(initial_error,steady_error))


@dataclass
class Bundle:
    data: bytearray
    objects: list
    fixups: list

    def append(self, label, body):
        self.data.extend(bytes((-len(self.data))%4))
        offset = len(self.data)
        self.objects.append(dict(label=label, offset=offset, size=len(body)))
        self.data.extend(body)
        return offset

    def pointer(self, at, relative):
        need(self.data[at:at+4] == bytes(4), 'zero relocatable local address field')
        self.fixups.append(dict(offset=at, relative_target=relative))


def check_external(before, offset, pcm):
    need(before[offset:offset+len(pcm)] == pcm, 'exact reusable existing source PCM')
    return BASE+offset


def build(before, source):
    need(len(before) == 0x1000000 and sha(before) == BEFORE and sha(source) == WSC_SHA,
         'pinned 16 MiB input and WSC source')
    need(all(addr(before, raw) == BASE+OLD_TABLE for raw in LOADERS), 'existing table loaders')
    need(before[0x37DE44:0x37DE44+len(WAITS)] == bytes(WAITS), 'installed native wait duration table')
    need(source[0x7872CC:0x7872D0] == bytes.fromhex('2f40ff4f'), 'source priority2 starts two descriptors')
    need(source[0x75401F:0x754022] == bytes.fromhex('b90200'), 'source two-channel thunk')
    need(source[0x754B40:0x754B4F] == bytes.fromhex('7f503a25150b0500faf4eadac5af80'), 'source sweep-step LUT')
    freq = round(3072000*4*1024/pitch_divisor(source, 0))
    old = before[OLD_TABLE:OLD_TABLE+OLD_COUNT*8]
    bundle = Bundle(bytearray(old+bytes((len(SFX_BY_SOURCE)+len(BGM_BY_SOURCE))*8)), [], [])
    sample_refs = {}
    wave_tags = (0, 1, 4, 9, 10)
    noise_tags = ('noise0','noise1','noise2','noise3')
    for wave in wave_tags:
        pcm = pcm_data(source, wave)
        sample = sample_blob(pcm, 0, freq)
        reused = WAVE_REUSE.get(wave)
        sample_refs[wave] = (None, check_external(before, reused, sample)) if reused is not None else (
            bundle.append(f'wsc-wave-{wave:02x}', sample), None)
    noise_data = {}
    for mode, tag in enumerate(noise_tags):
        pcm, loop = noise_pcm(mode)
        payload = sample_blob(pcm, loop, freq)
        sample_refs[tag] = (None, check_external(before, NOISE0_REUSE, payload)) if mode == 0 else (
            bundle.append(f'wsc-noise-mode-{mode}', payload), None)
        noise_data[str(mode)] = dict(tap=TAPS[mode], samples=len(pcm), loop_start=loop, sha256=sha(pcm))
    voices = bytearray()
    tags = (*wave_tags, *noise_tags)
    voice_ids = {tag: i for i,tag in enumerate(tags)}
    for tag in tags:
        _, external = sample_refs[tag]
        voices.extend(bytes((0,60,0,0))+struct.pack('<I', external or 0)+bytes((255,0,255,0)))
    voice_offset = bundle.append('mode23-voicegroup', voices)
    for tag in tags:
        target,_ = sample_refs[tag]
        if target is not None:
            bundle.pointer(voice_offset+voice_ids[tag]*12+4,target)
    songs = []
    def append_song(src, dst, priority, player, tracks, priority_override=40):
        descriptors = []
        for data, report in tracks:
            at = bundle.append(f'song-{dst:02x}-track-{len(descriptors)}', data)
            if 'loop_offset' in report:
                bundle.pointer(at+len(data)-4, at+report['loop_offset'])
            descriptors.append(report | dict(offset=at, bytes=len(data), sha256=sha(data)))
        n = len(descriptors)
        need(n <= before[0x37FBB4+player*12+8], 'existing native player track capacity')
        song = bundle.append(f'song-{dst:02x}', bytes((n,0,priority_override,128))+bytes(4+n*4))
        bundle.pointer(song+4,voice_offset)
        for i, row in enumerate(descriptors):
            bundle.pointer(song+8+i*4,row['offset'])
        bundle.pointer(dst*8,song)
        struct.pack_into('<2H',bundle.data,dst*8+4,player,player)
        songs.append(dict(source_id=src,native_id=dst,priority=priority,native_player=player,
                          header_offset=song,tracks=descriptors))

    for src, dst, priority, player in SFX_BY_SOURCE:
        tracks = [finite_track(source, extract(source, src+i), voice_ids, freq) for i in range(priority)]
        append_song(src,dst,priority,player,tracks)
    for src, dst in BGM_BY_SOURCE:
        tracks, lead, period = define_music(source,src)
        compiled = [music_track(source,t,lead,period,voice_ids) for t in tracks]
        audible = [details for _,details in compiled if details['kind']=='score-loop']
        need(len({(t['intro_updates'],t['repeat_updates']) for t in audible}) == 1, 'shared native GOTO timing across audible channels')
        append_song(src,dst,4,0,compiled,priority_override=0)
    need(bundle.data[:len(old)] == old, 'all 112 existing native song rows exact')
    need(len({f['offset'] for f in bundle.fixups}) == len(bundle.fixups), 'unique relative pointer fields')
    assets = bytes(bundle.data)
    return assets, dict(status='MODE23_AUDIO_ASSETS_BUILT', source_sha256=WSC_SHA,
        table_input_sha256=BEFORE, builder_sha256=sha(Path(__file__).read_bytes()), bundle_sha256=sha(assets),
        bundle_bytes=len(assets), table_offset=0, table_entries=122, existing_entries=112, existing_sha256=sha(old),
        existing_table_address=BASE+OLD_TABLE, unchanged_loader_literals=[BASE+a for a in LOADERS],
        asset_objects=bundle.objects, local_u32_fixups=bundle.fixups, song_map=songs,
        voicegroup_offset=voice_offset, sample_freq_field=freq, noise=noise_data,
        voices=[dict(voice=voice_ids[t],label=str(t),local=sample_refs[t][0],existing_address=sample_refs[t][1]) for t in tags],
        limits=['Assets and relative fixups only. Existing ROM, song table loaders, BGM cache, and scene entry unchanged.',
                'Native tempo95, mixer amplitude, envelope, stereo pan and per-update bend are quantized. '
                'Native sample/pitch phase on each note and source sub-update sweep clocks can differ.',
                'DA begins with an A7 hold before any new pitch. The initial inherited physical channel pitch is unavailable '
                'to a self-contained native song. Its time is preserved before the first source-defined pitch. '
                'Later A7 holds keep and extend the preceding native tone.',
                'SFX use existing players 4 and 6. Shared native player replacement and direct-sound mixer voice contention '
                'can differ from source hardware lane assignment.',
                'The F0/F4 vibrato recurrence uses deterministic zero starting phase as in the existing native score converter. '
                'Audible parity and the optional conditional volume fade still need native runtime verification.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before','source','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'fresh isolated audio output directory')
    assets, report = build(args.before.read_bytes(),args.source.read_bytes())
    args.output.mkdir(parents=True)
    (args.output/COMPONENT).write_bytes(assets)
    index = args.output/'manifest.json'
    index.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],len(assets),report['bundle_sha256'],sha(index.read_bytes()))


if __name__ == '__main__':
    main()
