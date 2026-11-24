"""Check the relocated mode-23 asset layout and note timing against original scores."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
INPUT = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
BUNDLE = '9EC8B6CD932407537FC364529891AE0FE310EA1FF5E4A5132FDFDBDF8158E49C'
MANIFEST = '3F59CECB61F4A1C43DEA8B9A861F790470B5E8BAB913E205AF4DBECF441DB90A'
BASE = 0x08000000
BINDINGS = (0x08C80000, 0x08F00000)
TABLE, COUNT = 0xD33000, 122
LOADERS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
SONGS = {
    0x70: (0x7C, 1, 4), 0x71: (0x84, 1, 4), 0x72: (0x98, 1, 4), 0x73: (0xD5, 1, 4),
    0x74: (0xD6, 1, 6), 0x75: (0xD7, 2, 4), 0x76: (0xD9, 1, 6), 0x77: (0xDA, 1, 6),
    0x78: (0xF0, 4, 0), 0x79: (0xF4, 4, 0),
}


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def sha(value):
    return hashlib.sha256(value).hexdigest().upper()


def u(value, at):
    return struct.unpack_from('<I', value, at)[0]


def signed(value):
    return value-256 if value >= 128 else value


def extract(source, index):
    raw = 0x3F0000+6*index
    owner, channel, at = struct.unpack_from('<3H', source, raw)
    end = struct.unpack_from('<H', source, raw+10)[0]
    data = source[0x3F0000+at:0x3F0000+end]
    require(owner in (0x54,0x7E,0xA8,0xD2,0xFC,0x126) and len(data) >= 6, 'source owner/descriptor')
    return data, channel


def source_tick(speed, tick):
    return 0 if not tick else 1+(16*(tick-1))//(16-speed)


def source_events(source, source_id, song_id):
    data, channel = extract(source, source_id)
    speed, wave, volume, effect = data[:4]
    words = list(zip(data[4::2],data[5::2],strict=True))
    require(words.pop() == (0xFF,0xFF), 'source terminator')
    looping = song_id >= 0x78
    mute = looping and volume == 0
    if mute:
        require(data == bytes.fromhex('00000000a000fdf01f01b0f0ffff'), 'exact quiet source loop')
        return [], 1, 0, speed, False
    split = None
    if looping:
        require(words.pop() == (0xB0,0xF0) and words.count((0xFD,0xF0)) == 1, 'source unbounded branch')
        mark = words.index((0xFD,0xF0))
        opening, repeat = words[:mark],words[mark+1:]
        first = opening+repeat
        split = source_tick(speed,sum(duration for op,duration in first if op < 0xA0))
        words = first+repeat*(1 if song_id == 0x78 else 5)
    controls = {'level':volume,'wave':wave,'pan':255,'sweep':effect if channel == 2 else 0,
                'kind':effect if channel & 1 else 0,'noise':0,'envelope':(0,0),'vibrato':254}
    tick = 0
    notes, previous = [], None
    inherited = False
    for op, value in words:
        if op < 160 or op == 0xA7:
            at = source_tick(speed,tick)
            end = source_tick(speed,tick+value)
            if op < 160:
                previous = None
                if op%16 < 12:
                    voice = f'noise{controls["noise"]}' if channel == 3 and controls['kind'] else str(controls['wave'])
                    previous = dict(packed=op, tick=tick, start=at, end=end, voice=voice,
                                    sweep=controls['sweep'], states=[])
                    notes.append(previous)
            elif previous is None:
                inherited = True
            if previous is not None:
                previous['end'] = end
                previous['states'].append((at,end,controls.copy()))
            tick += value
        elif op == 0xA0:
            controls['level']=value
        elif op == 0xA1:
            require(channel == 2,'source typed sweep')
            controls['sweep']=value
        elif op == 0xA2:
            if controls['kind'] and channel & 1:
                controls['noise']=value & 7
            else:
                controls['wave']=value
        elif op == 0xA3:
            controls['vibrato']=value
        elif op == 0xA4:
            controls['kind']=value
        elif op == 0xA5:
            controls['pan']=value
        elif 0xC0 <= op <= 0xCF:
            controls['envelope']=(op & 15,value)
        else:
            raise ValueError('unreviewed source opcode')
    return notes, source_tick(speed,tick), split, speed, inherited


def decode_native(data, waits, address, first=0):
    i, tick, active = first, 0, None
    controls = {}
    events, boundaries = [], {}
    while i < len(data):
        boundaries[i] = (tick, active is not None)
        op = data[i]
        i += 1
        if 0x81 <= op <= 0xB0:
            ticks = waits[op-0x80]
            if active is not None:
                active['states'].extend([tuple(controls[k] for k in (0xBE,0xBF,0xC0,0xC1))] * ticks)
            tick += ticks
        elif op == 0xCF:
            require(active is None and data[i+1] == 127, 'single explicit TIE with maximum velocity')
            require({0xBB,0xBC,0xBD,0xBE,0xBF,0xC0,0xC1} <= controls.keys()
                    or first, 'complete set of per-note controls')
            active = dict(key=data[i],start=tick,end=None,voice=controls[0xBD],states=[])
            i += 2
        elif op == 0xCE:
            require(active is not None and data[i] == active['key'], 'explicit EOT for exact open native key')
            active['end'] = tick
            events.append(active)
            active = None
            i += 1
        elif op in (0xBB,0xBC,0xBD,0xBE,0xBF,0xC0,0xC1):
            require(data[i] <= 127, 'native command operand byte')
            if op in (0xBB,0xBC):
                require(first == 0 and tick == 0 and data[i] == (95 if op == 0xBB else 0), 'tempo and key shift only in prologue')
            controls[op] = data[i]
            i += 1
        elif op in (0xB1,0xB2):
            require(active is None and i+(4 if op == 0xB2 else 0) == len(data), 'native terminal ends exact extent')
            jump = u(data,i)-address if op == 0xB2 else None
            if jump is not None:
                require(jump in boundaries and not boundaries[jump][1] and boundaries[jump][0] < tick,
                        'backward native branch to a resting command boundary')
            return events,tick,boundaries[jump][0] if jump is not None else None,jump
        else:
            raise ValueError(f'unexpected native opcode {op:02X}')
    raise ValueError('track has no terminal')


def raw_pitch(source, packed):
    return struct.unpack_from('<H', source, 0x754837+2*(packed%16))[0]//2**(packed//16)


def stereo(source, state, elapsed):
    mode,period = state['envelope']
    level = state['level']
    if elapsed and mode and period:
        rest = min(elapsed-1, period)
        index = 0
        for bit in (8,4,2,1):
            rest = (rest*2)&255
            if rest >= period:
                rest -= period
                index += bit
        atten = source[0x754DA0+16*mode+index]//16
        level = source[0x754867+16*atten+level]//16
    left, right = min(level,state['pan']//16),min(level,state['pan']%16)
    if left+right:
        return round(127*(left+right)/30),min(127,round(128*right/(left+right)))
    return 0,64


def compare_notes(source, source_rows, actual_rows, speed, voice_labels, frequency, looping):
    require(len(source_rows) == len(actual_rows), 'source/native note population')
    maximum = 0
    for old,new in zip(source_rows,actual_rows,strict=True):
        require((old['start'],old['end'],old['voice']) == (new['start'],new['end'],voice_labels[new['voice']]),
                'original note onset, hold ending and WSC voice identity')
        base = raw_pitch(source,old['packed'])
        for start,end,state in old['states']:
            for t in range(start,end):
                age = t-old['start']
                volume,pan,bend,span = new['states'][age]
                require((volume,pan) == stereo(source,state,age) and 1 <= span <= 24,
                        'quantized source envelope and stereo curve')
                shift = 0
                if old['sweep']:
                    command = old['sweep']
                    delta = signed(source[0x754B3F+(command%16)])
                    register = (2048-base + delta*((age*40704)//(8192*(1+command//16))))&2047
                    shift = base-(2048-register)
                elif looping and state['vibrato'] != 254 and age:
                    v = state['vibrato']
                    prior = t-1 - ((t-1)*speed//16)
                    if prior-old['tick'] >= 2*(v%16):
                        shift = signed(source[0x754967+(v&240)+t%16])
                target = (3072000/(base-shift))/(frequency/1024)
                actual = 2**((new['key']-60+(bend-64)*span/64)/12)
                error = abs(1200*math.log2(actual/target))
                require(error <= 38.0, 'bounded native pitch quantization')
                maximum = max(maximum,error)
    return maximum


def pcm_wave(source, wave):
    payload = source[0x754CC0+16*wave:0x754CC0+16*(wave+1)]
    samples = [(n&15,n//16) for n in payload]
    return bytes((sample*16-120)&255 for pair in samples for sample in pair),0


def pcm_noise(mode):
    taps = (14,10,13,4)
    state = [0]*15
    seen = {}
    bits = bytearray()
    while tuple(state) not in seen:
        seen[tuple(state)]=len(bits)
        bit = int(state[-8] == state[-(taps[mode]+1)])
        bits.append(120 if bit else -120 & 255)
        state = state[1:]+[bit]
    return bytes(bits),seen[tuple(state)]


def bind(blob, fixups, at):
    result = bytearray(blob)
    require(0x08000000 <= at and at+len(blob) <= 0x09000000 and at%4 == 0,'virtual base range')
    for f in fixups:
        here,target=f['offset'],f['relative_target']
        require(896 <= here <= len(blob)-4 and 0 <= target < len(blob) and u(blob,here)==0,
                'bounded local fixup and pristine zero field')
        struct.pack_into('<I',result,here,at+target)
    return bytes(result)


def audit_binding(before, source, blob, manifest, at):
    waits = before[0x37DE44:0x37DE75]
    slots = {item['offset']:item for item in manifest['asset_objects']}
    actual = bind(blob,manifest['local_u32_fixups'],at)
    labels = {}
    used_fixups = set()
    frequency = manifest['sample_freq_field']
    def ptr(offset):
        rel=u(actual,offset)-at
        require(0 <= rel < len(blob), 'relative object pointer')
        used_fixups.add(offset)
        return rel

    voicebank = manifest['voicegroup_offset']
    for i,entry in enumerate(manifest['voices']):
        labels[i]=entry['label']
        off=voicebank+i*12
        require(actual[off:off+4] == bytes((0,60,0,0)) and actual[off+8:off+12] == bytes((255,0,255,0)),
                'original PCM voice with neutral ADSR')
        samples, loop = pcm_noise(int(labels[i][-1])) if labels[i].startswith('noise') else pcm_wave(source,int(labels[i]))
        header=struct.pack('<4I',0x40000000,frequency,loop,len(samples))
        expected=header+samples+samples[loop:loop+1]
        if entry['local'] is None:
            reuse=u(actual,off+4)-BASE
            require(reuse==entry['existing_address']-BASE and before[reuse:reuse+len(expected)]==expected,
                    'reused existing exact PCM/noise span')
        else:
            pointed=ptr(off+4)
            require(pointed==entry['local'] and actual[pointed:pointed+len(expected)]==expected,
                    'new exact source PCM/noise span')

    tracks_checked, notes_checked, limits = 0,0,[]
    for row in manifest['song_map']:
        native = row['native_id']
        source_id,priority,player = SONGS[native]
        require((row['source_id'],row['priority'],row['native_player']) == (source_id,priority,player),
                'fixed source command mapping and request type')
        header = ptr(native*8)
        require(header == row['header_offset'] and header in slots and ptr(header+4) == voicebank,
                'new table row binds exact song/voicegroup')
        require(actual[header] == priority and actual[header+1:header+4] == bytes((0,0 if player==0 else 40,128)),
                'mode23 song track count and native priority')
        require(struct.unpack_from('<HH',actual,native*8+4) == (player,player)
                and priority <= before[0x37FBB4+player*12+8], 'native MPlay track slots')
        for j,track in enumerate(row['tracks']):
            start=ptr(header+8+j*4)
            require(start==track['offset'] and slots[start]['size'] == track['bytes'], 'owned track extent')
            body=actual[start:start+track['bytes']]
            source_rows, expected_total, expected_loop, speed, inherited=source_events(source,source_id+j,native)
            real,ticks,loop,jump = decode_native(body,waits,at+start)
            require((ticks,loop) == (expected_total,expected_loop), 'source introduction and exact repeated update counts')
            if jump is not None:
                pointer=start+len(body)-4
                require(ptr(pointer)==start+track['loop_offset']==start+jump, 'actual GOTO local target and source phase')
                repeated,repticks,loop2,jump2=decode_native(body,waits,at+start,jump)
                relative=[(r['start']-loop,r['end']-loop,r['key'],r['voice'],r['states']) for r in real if r['start'] >= loop]
                replayed=[(r['start'],r['end'],r['key'],r['voice'],r['states']) for r in repeated]
                require((repticks,loop2,jump2)==(ticks-loop,0,jump) and relative==replayed,
                        'reachable returning loop with identical steady note state')
            else:
                require(native < 0x78, 'finite effects alone stop at FINE')
            max_error=compare_notes(source,source_rows,real,speed,labels,frequency,jump is not None)
            if inherited:
                require(source_id==0xDA and source_rows[0]['start']==5,'retained context-dependent leading hold timing')
            tracks_checked += 1
            notes_checked += len(real)
            limits.append(max_error)
    require(used_fixups == {f['offset'] for f in manifest['local_u32_fixups']},
            'all local fixups traced to actual engine address fields')
    return dict(base=at,tracks=tracks_checked,source_note_count=notes_checked,max_pitch_error_cents=max(limits))


def audit(before,source,blob,manifest_bytes):
    require(tuple(map(sha,(before,source,blob,manifest_bytes))) == (INPUT,SOURCE,BUNDLE,MANIFEST),'immutable inputs and assets')
    manifest=json.loads(manifest_bytes)
    require(len(blob)==manifest['bundle_bytes'] and manifest['table_entries']==COUNT,'bounded bundle')
    require(blob[:112*8]==before[TABLE:TABLE+112*8],'all 112 native audio entries unchanged')
    require(all(u(before,a)==BASE+TABLE for a in LOADERS),'five original loader pointers')
    previous=COUNT*8
    for item in manifest['asset_objects']:
        now,end=item['offset'],item['offset']+item['size']
        require(now%4==0 and previous<=now and end<=len(blob) and not any(blob[previous:now]),'nonoverlapping objects and empty alignment gap')
        previous=end
    require(previous==len(blob),'whole bundle object closure')
    require([r['native_id'] for r in manifest['song_map']]==list(SONGS),'new native slots 70–79 exact')
    fixups=[f['offset'] for f in manifest['local_u32_fixups']]
    require(len(set(fixups))==len(fixups),'unique local fixups')
    proof=[audit_binding(before,source,blob,manifest,at) for at in BINDINGS]
    bad=next(t for row in manifest['song_map'] for t in row['tracks'] if 'loop_offset' in t)
    at=BINDINGS[0]
    relocated=bind(blob,manifest['local_u32_fixups'],at)
    body=bytearray(relocated[bad['offset']:bad['offset']+bad['bytes']])
    struct.pack_into('<I',body,len(body)-4,at)
    try:
        decode_native(body,before[0x37DE44:0x37DE75],at+bad['offset'])
    except ValueError:
        pass
    else:
        raise ValueError('out-of-track GOTO was accepted')
    return dict(status='MODE23_AUDIO_INDEPENDENT_PASS',asset_sha256=BUNDLE,manifest_sha256=MANIFEST,
                verification_sha256=sha(Path(__file__).read_bytes()),existing_rows=112,compiled_commands=10,
                simultaneous_source_d7_tracks=['D7','D8'],simulated_bindings=proof,negative_out_of_track_branch_rejected=True,
                scope='Source schedule, quantized track operand and relocation checks only. No ROM patching or audio playback.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ('before','source','assets','report'):
        parser.add_argument('--'+k,type=Path,required=True)
    a=parser.parse_args()
    require(not a.report.exists(),'fresh report')
    result=audit(a.before.read_bytes(),a.source.read_bytes(),(a.assets/'mode23-audio-assets.bin').read_bytes(),
                 (a.assets/'manifest.json').read_bytes())
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(result['status'],sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
