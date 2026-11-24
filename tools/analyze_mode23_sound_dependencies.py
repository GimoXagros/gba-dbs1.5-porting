"""Map the bounded mode-23 source sound requests and retained native score owners."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import json
from pathlib import Path
import struct

from analyze_shoot_audio_lineage import GBA_SHA256, WSC10_SHA256, WSC15_SHA256, branch_target, sha256, sound_payload
from analyze_wsc_evolution_music import extract


COMPONENT = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
GBA_BASE = 0x08000000
TABLE = 0xD33000
LOADERS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
# These are decoded mode-23 producers; other occurrences of the same IDs are outside scope.
REQUESTS = {
    0x04: (4, (0x74A969, 0x74AA29, 0x74B698)),
    0x18: (4, (0x74D1E6,)), 0x1C: (4, (0x74D223,)),
    0x24: (4, (0x74B89C,)), 0x30: (4, (0x74B991,)), 0x6C: (4, (0x74B3C9,)),
    0x7C: (1, (0x74B090,)), 0x7D: (1, (0x74B163,)),
    0x84: (1, (0x74BBC4, 0x74BE01)), 0x98: (1, (0x74D03F,)), 0x9A: (1, (0x74CF4F,)),
    0xAC: (1, (0x74C3C8,)), 0xD5: (1, (0x74C07D,)), 0xD6: (1, (0x74BD12, 0x74BDB6)),
    0xD7: (2, (0x74BF02,)), 0xD9: (1, (0x74CD8A, 0x74CDB3, 0x74CDDC)), 0xDA: (1, (0x74C224,)),
    0xF0: (4, (0x74B4E3,)), 0xF4: (4, (0x74B511,)),
}
OLD_ALIASES = {0x04: 0x04, 0x18: 0x18, 0x1C: 0x1C, 0x24: 0x24, 0x30: 0x30, 0x6C: 0x6C, 0x7C: 0x7C, 0x7D: 0x7D,
               0x84: 0x82, 0x98: 0x96, 0x9A: 0x98, 0xAC: 0xAA}
NATIVE = {0x04: 0x00, 0x18: 0x04, 0x1C: 0x05, 0x24: 0x07, 0x30: 0x0A, 0x6C: 0x19, 0x7D: 0x23, 0x9A: 0x5A, 0xAC: 0x4E}
STANDALONE = {0x7C, 0x84, 0x98, 0xD5, 0xD6, 0xD7, 0xD9, 0xDA}
MUSIC = {0xF0, 0xF4}


def u(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def h(data, offset):
    return struct.unpack_from('<H', data, offset)[0]


def check_producer(data, offset, sid, priority, delay=0):
    expected = bytes.fromhex('c74402') + struct.pack('<H', sid) + bytes.fromhex('c7440e')
    expected += struct.pack('<H', priority) + bytes.fromhex('c74406') + struct.pack('<H', delay)
    assert data[offset:offset+20] == expected + bytes.fromhex('814c100001')


def score_keys(payload):
    return [36 + 12 * (op >> 4) + (op & 15) for op in payload[4::2] if op < 0xA0 and op & 15 < 12]


def source_track(payload, meta):
    speed, _, init_volume, init_effect = payload[:4]
    assert speed < 16 and init_volume <= 15
    commands = list(zip(payload[4::2], payload[5::2], strict=True))
    assert commands[-1] == (0xFF, 0xFF)
    ticks, marker, end, effect, noise = 0, None, None, init_effect, set()
    counts = Counter()
    for i, (op, arg) in enumerate(commands[:-1]):
        counts[op] += 1
        if op < 0xA0 or op == 0xA7:
            assert arg > 0
            ticks += arg
        elif op == 0xFD:
            assert marker is None and arg == 0xF0
            marker = i, ticks
        elif op == 0xB0:
            assert marker and arg == 0xF0 and i == len(commands)-2 and ticks > marker[1]
            end = i, ticks
        elif op == 0xA0:
            assert arg <= 15
        elif op == 0xA2:
            assert arg <= 15
            if meta['hardware_channel'] == 3 and effect:
                noise.add(arg & 7)
        elif op == 0xA4:
            effect = arg
            if meta['hardware_channel'] == 3 and effect:
                noise.add(0)
        else:
            assert op in (0xA1, 0xA3, 0xA5) or 0xC0 <= op <= 0xCF
    assert bool(marker) == bool(end)
    loop = None
    if marker:
        initial, repeated = marker[1], ticks-marker[1]
        loop = dict(saved_cursor_payload_offset=4+2*(marker[0]+1), jump_payload_offset=4+2*end[0],
                    intro_score_ticks=initial, loop_score_ticks=repeated,
                    phase_realign_loops=next(iter(i for i in range(1,17)
                                                 if (repeated*i*speed) % (16-speed) == 0)),
                    audible=bool(init_volume and score_keys(payload)))
    update_count = lambda t: 0 if t == 0 else 16*(t-1)//(16-speed)+1
    return meta | dict(speed=speed, initial_volume=init_volume, one_pass_score_ticks=ticks,
                       one_pass_source_updates=update_count(ticks), pitch_count=len(score_keys(payload)),
                       loop=loop, hardware_noise_modes=sorted(noise), hardware_sweep=0xA1 in counts,
                       opcode_counts={f'{op:02X}': count for op, count in sorted(counts.items())})


def native_keys(rom, at):
    """Bounded pitch census. Stop at the first native control-flow instruction."""
    keys, running = [], None
    for _ in range(4000):
        byte = rom[at]
        at += 1
        if byte < 0x80:
            assert running is not None
            op = running
            at -= 1
        else:
            op = byte
            if op >= 0xBD:
                running = op
        if op >= 0xCF:
            if rom[at] >= 0x80:
                assert keys
                keys.append(keys[-1])
                continue
            keys.append(rom[at])
            at += 1
            for _ in range(2):
                if rom[at] >= 0x80:
                    break
                at += 1
        elif 0xBA <= op <= 0xCD:
            at += 1
        elif op == 0xCE:
            at += int(rom[at] < 0x80)
        elif op in (0xB1, 0xB2, 0xB3, 0xB4):
            return keys
        else:
            assert op <= 0xB0
    raise AssertionError('unterminated native track')


def native_song(rom, i):
    header, player, mirrored = struct.unpack_from('<IHH', rom, TABLE+i*8)
    assert player == mirrored and GBA_BASE <= header < GBA_BASE+len(rom)
    at = header-GBA_BASE
    count = rom[at]
    assert count <= 12
    pointers = struct.unpack_from(f'<{count}I', rom, at+8)
    assert all(GBA_BASE <= address < GBA_BASE+len(rom) for address in pointers)
    return header, player, pointers


def check_native_caller(gba, offset, sid, priority, delay=0):
    assert struct.unpack_from('<III', gba, offset-12) == (0xE3A08000 | sid, 0xE3A09000 | priority, 0xE3A0A000 | delay)
    assert branch_target(GBA_BASE+offset, u(gba, offset)) == 0x080D15C0


def pitch_evidence(source, rom, source_id, native_id, n=3):
    header, player, pointers = native_song(rom, native_id)
    tracks = []
    for channel, ptr in enumerate(pointers[:n]):
        a = score_keys(extract(source, source_id+channel)[0])
        b = native_keys(rom, ptr-GBA_BASE)
        match = SequenceMatcher(a=a, b=b, autojunk=False).find_longest_match()
        differences = lambda seq: [v - k for k, v in zip(seq, seq[1:])]
        intervals = SequenceMatcher(a=differences(a), b=differences(b), autojunk=False).find_longest_match()
        tracks.append(dict(original_id=source_id+channel, native_track=ptr, original_keys=len(a),
                           matched_contiguous_intervals=intervals.size,
                           matched_exact_contiguous_keys=match.size,
                           whole_pitch_sequence_exact=a == b))
    return dict(header=header, player=player, tracks=tracks)


def analyze(source, old, gba, rom):
    assert tuple(map(sha256, (source, old, gba, rom))) == (WSC15_SHA256, WSC10_SHA256, GBA_SHA256, COMPONENT)
    assert len(rom) == 0x1000000
    assert all(u(rom, offset) == GBA_BASE+TABLE for offset in LOADERS)
    assert rom[TABLE:TABLE+0x5B*8] == gba[0x37FC20:0x37FC20+0x5B*8]
    for i in range(0x70):
        native_song(rom, i)
    assert u(rom, TABLE+0x70*8) == 0x01020202
    assert rom[0xD1500:0xD1544] == gba[0xD1500:0xD1544]
    assert rom[0xD15C0:0xD15F0] == gba[0xD15C0:0xD15F0]
    assert h(gba, 0x158C8) == 0xFF1E and u(gba, 0x158C8) == 0xE12FFF1E
    assert source[0x74D2C1:0x74D2C6] == bytes.fromhex('9a48011987')
    assert source[0x74D2D4:0x74D2D9] == bytes.fromhex('9a844fff4f')
    assert source[0x7545DE:0x7545E2] == bytes.fromhex('3cfd751c')
    assert source[0x754669:0x754674] == bytes.fromhex('880574058b45018904e943')

    check_producer(old, 0x3BEB12, 0x06, 2)
    check_native_caller(gba, 0x340394, 0, 2)
    check_producer(old, 0x39284A, 0x98, 1)
    check_native_caller(gba, 0x354768, 0x5A, 1)
    check_producer(old, 0x3BD0FE, 0x7D, 1)
    check_native_caller(gba, 0xB692C, 0x23, 1)
    check_producer(old, 0x3B1626, 0xAA, 1, 1)
    check_native_caller(gba, 0x378FF0, 0x4E, 1, 1)
    check_native_caller(gba, 0xBC0AC, 0x04, 4)
    check_native_caller(gba, 0xC04DC, 0x0A, 4)
    check_native_caller(gba, 0xC04C8, 0x07, 4)
    check_native_caller(gba, 0x3779D4, 0x19, 4)
    assert source[0x74B4F9:0x74B4FF] == bytes.fromhex('26803e180006')
    old_payloads = {i: sound_payload(old, 0x2D0000, i) for i in range(0xB9)}
    rows = []
    for sid, (priority, addresses) in REQUESTS.items():
        for a in addresses:
            check_producer(source, a, sid, priority)
        tracks = []
        for offset in range(4 if priority == 4 else 1):
            payload, meta = extract(source, sid+offset)
            exact = [old_i for old_i, raw in old_payloads.items() if raw == payload]
            if sid in OLD_ALIASES:
                assert OLD_ALIASES[sid]+offset in exact
            elif sid in MUSIC:
                if offset < 3:
                    assert not exact
            else:
                assert not exact
            tracks.append(source_track(payload, meta) | dict(wsc10_payload_matches=exact))
        mapping = dict(native_id=NATIVE.get(sid))
        if sid in (0x18, 0x1C, 0x24, 0x30, 0x6C, 0x7D, 0xAC):
            pitch = pitch_evidence(source, rom, sid, NATIVE[sid], 1 if sid in (0x7D, 0xAC) else 3)
            limit = {0x18: (15,10,15), 0x1C: (14,14,2), 0x24: (12,12,0), 0x30: (12,12,17), 0x6C: (7,7,0), 0x7D: (2,), 0xAC: (16,)}[sid]
            assert all(max(row['matched_exact_contiguous_keys'], row['matched_contiguous_intervals'] + 1) >= minimum
                       for row, minimum in zip(pitch['tracks'], limit, strict=True)), (sid, pitch)
            assert pitch['tracks'][0]['matched_exact_contiguous_keys'] >= limit[0]
            if len(limit) > 1:
                assert pitch['tracks'][1]['matched_exact_contiguous_keys'] >= limit[1]
            mapping.update(status='commercial-score-counterpart', pitch=pitch)
            if sid == 0x7D:
                mapping.update(wsc10_request=0x3BD0FE, native_request=0x080B692C)
            if sid == 0xAC:
                mapping.update(wsc10_request=0x3B1626, native_request=0x08378FF0,
                               retail_compared_delay=1, mode23_delay=0)
        elif sid == 0x9A:
            mapping.update(status='commercial-caller-counterpart', wsc10_request=0x39284A, native_request=0x08354768)
        elif sid == 0x04:
            assert all(not track['loop']['audible'] for track in tracks)
            mapping.update(status='audible-zero-retail-stop', old_stop_request=0x3BEB12, native_request=0x08340394,
                           limitation='Source installs four zero-volume loop channels. Native ID00 stops MPlay players.')
        elif sid in MUSIC:
            assert all(track['loop']['audible'] for track in tracks[:3]) and not tracks[-1]['loop']['audible']
            mapping.update(status='new-looping-four-track-score')
        else:
            assert sid in STANDALONE and not tracks[0]['loop']
            mapping.update(status='source-finite-conversion')
            if sid == 0x7C:
                candidate = pitch_evidence(source, rom, sid, 0x22, 1)
                assert candidate['tracks'][0]['matched_exact_contiguous_keys'] == 13
                mapping.update(candidate_native_id=0x22, candidate_pitch=candidate,
                               limitation='Another retained score has the complete interval contour transposed. Use source conversion until the caller is bound.')
        rows.append(dict(source_id=sid, priority=priority, delay=0, source_calls=addresses, tracks=tracks, mapping=mapping))
    return dict(status='MODE23_SOUND_SOURCE_SCOPE_PASS', component_sha256=COMPONENT,
                commands=rows, request_count=sum(len(a) for _, a in REQUESTS.values()),
                table=dict(current_base=GBA_BASE+TABLE, rows=112, row_size=8, loader_sites=[GBA_BASE+a for a in LOADERS],
                           next_word=u(rom, TABLE+0x70*8), coexistence='Relocate the full table. Preserve all 112 old entries and five loaders.'),
                services=dict(source_enqueue_owner='0C00:390E', native_enqueue=0x080D15C0,
                              native_enqueue_registers='R8 native ID, R9 source priority, R10 zero delay; save R4-R11 and LR',
                              native_queue_owner=0x030022F0, source_flush=0x7872D8, native_flush=0x080D1500,
                              source_conditional_fade_tick=0x754F74, native_legacy_channel_fade=0x080158C8,
                              fade_limit='Retail per-channel fade is BX LR. Source adds per-channel countdown and hardware volume stepping.'),
                ambient_order=dict(primary=0xF0, round6_replacement=0xF4, source_round_check=0x74B4F9,
                                   same_delay_zero_pending_slot=True),
                new_finite_ids=sorted(STANDALONE), new_looped_music=sorted(MUSIC),
                limitations=['The commercial matches establish corresponding scores or existing service calls. No audible hardware equivalence is asserted.',
                             'D9 needs noise mode 2. F2/F6 use mode 0; exact global phase, loops and state continuity must be implemented for F0/F4.',
                             'A1 is hardware sweep on source channel 2. A7 advances the current gated pitch state without starting another note.',
                             'No ROM, mode 23 runtime, audio render, or mode transition was created by this report.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'old', 'gba', 'rom', 'report'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    result = analyze(*(getattr(args, name).read_bytes() for name in ('source', 'old', 'gba', 'rom')))
    result['checker_sha256'] = sha256(Path(__file__).read_bytes())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha256(args.report.read_bytes()))


if __name__ == '__main__':
    main()
