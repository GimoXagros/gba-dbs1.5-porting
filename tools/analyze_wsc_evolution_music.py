"""Extract the four source evolution scores and their native selection mismatch.

No emulator, save, audio download, ROM modification, or title inference is used.
Times are original driver updates, not guessed seconds or native M4A ticks.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct

WSC_SHA = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
GBA_SHA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
CATEGORIES = bytes((2,2,2,1,1,0,0,0,0,1,1,3,3,0,0,2))
SONGS = (0x38, 0x3C, 0x40, 0xF8)
BANK = 0x3F0000

def sha(data): return hashlib.sha256(data).hexdigest().upper()
def need(ok, message):
    if not ok: raise ValueError(message)

def extract(wsc, sid):
    state, channel, offset = struct.unpack_from('<HHH', wsc, BANK + sid * 6)
    end = struct.unpack_from('<H', wsc, BANK + (sid + 1) * 6 + 4)[0]
    need(0x648 <= offset < end <= 0x10000, 'bounded sound entry')
    payload = wsc[BANK + offset:BANK + end]
    return payload, dict(id=sid, state_offset=state, hardware_channel=channel,
                         raw=BANK+offset, size=len(payload), sha256=sha(payload))

def parse(payload):
    """Decode all commands in these exact scores; reject unimplemented commands."""
    need(len(payload) >= 6 and len(payload) % 2 == 0, 'pair-aligned score')
    speed, wave, volume, effect = payload[:4]
    need(speed < 16 and wave < 16 and volume < 16, 'bounded source header')
    commands, counts, notes = [], collections.Counter(), []
    state = dict(wave=wave, volume=volume, effect=effect, vibrato=0xFE,
                 stereo_ceiling=255, envelope_mode=0, envelope_period=0)
    silent_loop = payload[4:] == bytes.fromhex('a000fdf01f01b0f0ffff')
    ticks = 0
    for cursor in range(4, len(payload), 2):
        op, arg = payload[cursor:cursor+2]
        commands.append(dict(offset=cursor, op=op, arg=arg, tick=ticks))
        counts[f'{op:02X}'] += 1
        if op == 0xFF:
            need(arg == 255 and cursor + 2 == len(payload), 'terminal FF pair')
            break
        if op == 0xA0: state['volume'] = arg
        elif op == 0xA2: state['wave'] = arg
        elif op == 0xA3: state['vibrato'] = arg
        elif op == 0xA4: state['effect'] = arg
        elif op == 0xA5: state['stereo_ceiling'] = arg
        elif 0xC0 <= op <= 0xCF:
            state['envelope_mode'], state['envelope_period'] = op & 15, arg
        elif op in (0xFD, 0xB0):
            need(silent_loop and arg == 0xF0, 'only exact zero-volume infinite rest loop')
        elif op < 0xA0:
            need(arg > 0, 'positive duration')
            need(state['wave'] < 16 and state['volume'] < 16, 'bounded waveform and volume')
            notes.append(dict(tick=ticks, duration=arg, packed_note=op,
                              midi_note=None if op & 15 >= 12 else 36+12*(op>>4)+(op&15),
                              **state))
            ticks += arg
        else: raise ValueError(f'unsupported source opcode {op:02X} at {cursor:X}')
    else: raise ValueError('missing terminal FF')
    # Source 75420A..754232: a fraction accumulator skips the countdown
    # whenever addition reaches16. Initialization7540C1 clears it. The first
    # note starts immediately through75415F; subsequent ticks start atupdate1.
    update, fraction, tick = 0, 0, 0
    onset = {0: 0}
    while tick < ticks:
        update += 1
        fraction += speed
        if fraction >= 16: fraction -= 16
        else:
            tick += 1
            onset[tick] = update
    for note in notes:
        note['update'] = onset[note['tick']]
        note['duration_updates'] = onset[note['tick']+note['duration']] - note['update']
    return dict(header=list(payload[:4]), commands=commands, command_counts=dict(counts),
                notes=notes, score_ticks=ticks, driver_updates=update,
                silent_infinite_rest=silent_loop, finite=not silent_loop)

def analyze(wsc, gba):
    need(sha(wsc) == WSC_SHA and sha(gba) == GBA_SHA, 'original input identities')
    need(wsc[0x787267:0x787277] == CATEGORIES, 'source character categories')
    need(wsc[0x787277:0x78727F] == bytes.fromhex('38043c044004f804'), 'source selection pairs')
    need(gba[0xD14A8:0xD14BC] == bytes.fromhex('020202010100000000010102021c041c041c0400'),
         'retail categories and collapsed selection')
    songs = []
    for category, first in enumerate(SONGS):
        channels = []
        for sid in range(first, first+4):
            payload, info = extract(wsc, sid)
            channels.append(dict(**info, payload_hex=payload.hex(), **parse(payload)))
        need([c['state_offset'] for c in channels] == [168,210,252,294], 'four source slots')
        need(sorted(c['hardware_channel'] for c in channels) == [0,1,2,3], 'hardware permutation')
        durations = [c['driver_updates'] for c in channels if c['finite']]
        songs.append(dict(category=category, source_base_id=first, source_request_type=4,
                          character_ids=[n for n,c in enumerate(CATEGORIES) if c == category],
                          longest_finite_updates=max(durations), channels=channels,
                          requested_title=None, title_status='not established by ROM bytes'))
    ranges = [(0x754015,0x7540B9,'four-channel start'),
              (0x7540B9,0x754165,'channel initialization'),
              (0x754165,0x7542C5,'driver update'),
              (0x75445D,0x7547B3,'note and command interpreter'),
              (0x753E80,0x753F7F,'envelope and stereo output'),
              (0x754837,0x754867,'pitch divisors'),
              (0x754867,0x754967,'volume lookup'),
              (0x754967,0x754A57,'vibrato lookup'),
              (0x754CC0,0x754DC0,'waveforms'),
              (0x754DA0,0x754EA0,'envelope lookup'),
              (0x787267,0x7872C8,'source selector'),
              (0xD14A8,0xD14FC,'retail selector')]
    bindings=[]
    for start,end,label in ranges:
        data = gba if label.startswith('retail') else wsc
        bindings.append(dict(start=start,end=end,label=label,sha256=sha(data[start:end])))
    return dict(source_sha256=WSC_SHA,retail_sha256=GBA_SHA,songs=songs,
                source_table=dict(raw=BANK,entry_size=6,entry_count=0x10C),
                source_bindings=bindings,
                requested_names=['brave heart','Beat Hit!','EVO','One Vision'],
                findings={'retail_all_evolution_categories_request':0x1C,
                          'retail_request_type':4,'source_distinct_evolution_groups':4},
                limits=['Titles are not stored in the examined scores or selector.',
                        'Driver-update schedule is not a rendered APU or an audible parity claim.',
                        'A3 requires global vibrato phase and delay; A4 on channel3 is noise.',
                        'Native conversion must preserve stereo ceilings, speed, waveforms, and envelopes.',
                        'Infinite silent rest channels remain explicitly marked, not falsely finite.'])

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--wsc',required=True,type=Path)
    p.add_argument('--gba',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    paths=[a.wsc.resolve(),a.gba.resolve(),a.report.resolve()]
    need(len(set(paths))==len(paths) and not a.report.exists(),'fresh nonalias report output')
    report=analyze(a.wsc.read_bytes(),a.gba.read_bytes())
    # Failing closed is part of the parser contract, including music effects
    # absent from the old SFX-only translators.
    first=bytes.fromhex(report['songs'][0]['channels'][0]['payload_hex'])
    rejected=[]
    for label,bad in [('unknown opcode',first[:4]+b'\xa6\x00'+first[6:]),
                      ('missing end',first[:-2]),('bad header',b'\x10'+first[1:]),
                      ('unproved loop',first[:4]+b'\xb0\xf0'+first[6:])]:
        try: parse(bad)
        except ValueError: rejected.append(label)
        else: raise AssertionError(label)
    report['negative_controls']=rejected
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report_sha256':sha(a.report.read_bytes()),
                      'songs':[{k:s[k] for k in ('source_base_id','character_ids','longest_finite_updates')} for s in report['songs']]}))

if __name__ == '__main__': main()
