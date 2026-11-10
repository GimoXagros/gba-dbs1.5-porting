"""Isolated four-score native reconstruction using original WSC waveforms.

This is a development component, not an audible parity assertion. Quantized
native timing/pitch/pan and note-phase differences are recorded in the manifest.
Unknown source commands fail in the shared source decoder; no retail melody or
retail instrument replaces any of these four scores.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
from analyze_wsc_evolution_music import analyze, need, sha, CATEGORIES

INPUT = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
BASE = 0x08000000
# New 16MiB image extension, three explicit incoming-encoding-free blocks.
# The rejected old-image730000..760000 census is retained in the manifest.
RESERVATIONS = ((0xD33000,0xD40000),(0xD41000,0xD4B000),(0xD74000,0xD7E000))
START, END = RESERVATIONS[0][0], RESERVATIONS[-1][1]
OUTPUT_SIZE = 0x1000000
OLD_TABLE, COUNT = 0x686800, 0x6C
LITERALS = (0x37C2A4,0x37C2D8,0x37C324,0x37C378,0x37C3AC)

def signed8(n): return n if n < 128 else n-256

def source_amplitude(wsc, note, age):
    volume=note['volume']
    period=note['envelope_period']
    mode=note['envelope_mode']
    if age and mode and period:
        # The original quotient is four 8-bit shift/subtract steps, not
        # unlimited-precision division. Age is saturated by the driver.
        value=min(age-1,period)
        quotient=0
        for _ in range(4):
            value=(value*2)&255
            ge=value>=period
            if ge: value-=period
            quotient=(quotient*2)+int(ge)
        shape=wsc[0x754DA0+mode*16+quotient]&0xF0
        volume=wsc[0x754867+(shape|volume)]>>4
    ceiling=note['stereo_ceiling']
    return min(volume,ceiling>>4),min(volume,ceiling&15)

def pitch_divisor(wsc, packed):
    return struct.unpack_from('<H',wsc,0x754837+(packed&15)*2)[0]>>(packed>>4)

def noise_samples():
    # WSC noise mode0: 15-bit XNOR feedback taps7/14, reset to0 by OUT8E#18.
    # This is the full repeating hardware sequence, not a GBA noise analogue.
    register=0
    result=bytearray()
    while True:
        register=((register<<1)|(1^((register>>7)&1)^((register>>14)&1)))&0x7FFF
        result.append(120 if register&1 else 136) # signed +120 / -120
        if register == 0: break
        need(len(result)<32768,'bounded maximal noise period')
    need(len(result)==32767,'noise mode0 full period')
    return bytes(result)

def compile_channel(wsc, channel, voice_ids):
    # Native tempo95 gives95/75 ticks per GBA VBlank. The exact difference
    # from one WSC driver update per75.471698Hz frame is reported, not hidden.
    stream=bytearray((0xBC,0,0xBB,95))
    controls=[]
    if channel['silent_infinite_rest']:
        # Zero-volume source loop is represented by immediate native FINE:
        # it produces no sound and consumes no native mixer voice. This is
        # an explicit lifetime difference, not a false source finite claim.
        stream.append(0xB1)
        return bytes(stream),dict(silent_loop_elided=True,notes=[],max_pitch_error_cents=0)
    speed=channel['header'][0]
    base_divisor=pitch_divisor(wsc,0)
    sample_frequency=round(3072000*4*1024/base_divisor)
    maximum_error=0.0
    for note in channel['notes']:
        duration=note['duration_updates']
        if note['midi_note'] is None:
            stream.extend([0x81]*duration)
            continue
        noise=channel['hardware_channel']==3 and note['effect']!=0
        need(not note['effect'] or noise,'unsupported effect on non-noise channel')
        need(not noise or note['wave']==0,'only actual source noise mode0')
        voice=voice_ids['noise0' if noise else note['wave']]
        key=note['midi_note']
        need(0<=key<128,'native key range')
        base_rate=(sample_frequency/1024)*2**((key-60)/12)
        bends=[]
        for age in range(duration):
            elapsed=note['update']+age
            previous_tick=max(0,elapsed-1)-(max(0,elapsed-1)*speed//16)
            vibrato=note['vibrato']
            delta=0
            if vibrato!=0xFE and age and previous_tick-note['tick']>=2*(vibrato&15):
                delta=signed8(wsc[0x754967+(vibrato&0xF0)+(elapsed&15)])
            divisor=pitch_divisor(wsc,note['packed_note'])-delta
            need(divisor>0,'positive source pitch divisor')
            bends.append(12*math.log2((3072000/divisor)/base_rate))
        bend_range=max(1,math.ceil(max(abs(x) for x in bends)))
        need(bend_range<=24,'native bend range')
        stream.extend((0xBD,voice,0xC1,bend_range))
        previous=None
        curve=[]
        for age,bend in enumerate(bends):
            left,right=source_amplitude(wsc,note,age)
            volume=round((left+right)*127/30)
            pan=min(127,round(128*right/(left+right))) if left+right else 64
            quant=max(-64,min(63,round(bend*64/bend_range)))
            maximum_error=max(maximum_error,abs(quant*bend_range/64-bend)*100)
            current=(volume,pan,quant+64)
            if previous is None or current[0]!=previous[0]: stream.extend((0xBE,current[0]))
            if previous is None or current[1]!=previous[1]: stream.extend((0xBF,current[1]))
            if previous is None or current[2]!=previous[2]: stream.extend((0xC0,current[2]))
            if age==0: stream.extend((0xCF,key,127)) # TIE until explicit EOT
            stream.append(0x81)
            previous=current
            curve.append(dict(left=left,right=right,volume=volume,pan=pan,bend=current[2]))
        stream.extend((0xCE,key))
        controls.append(dict(source_offset_tick=note['tick'],update=note['update'],
                             duration_updates=duration,key=key,voice=voice,
                             source_noise=noise,bend_range=bend_range,curve=curve))
    stream.append(0xB1)
    return bytes(stream),dict(silent_loop_elided=False,notes=controls,
                             max_pitch_error_cents=maximum_error)

def inbound(before, intervals=RESERVATIONS):
    refs=[]
    for at in range(len(before)-3):
        word=struct.unpack_from('<I',before,at)[0]
        if any(BASE+a<=word<BASE+b for a,b in intervals):
            refs.append(dict(site=at,kind='unaligned pointer',target=word))
    for at in range(0,len(before)-3,4):
        word=struct.unpack_from('<I',before,at)[0]
        if word>>28!=15 and word&0x0E000000==0x0A000000:
            delta=word&0xFFFFFF
            if delta&0x800000: delta-=0x1000000
            target=at+8+delta*4
            if any(a<=target<b for a,b in intervals): refs.append(dict(site=at,kind='ARM-like branch',target=BASE+target))
    return refs

def build(before,wsc,gba):
    need(sha(before)==INPUT,'frozen owner46 input')
    source=analyze(wsc,gba)
    need(len(before)==0x800000,'exact8MiB predecessor')
    extended=before+b'\xFF'*(OUTPUT_SIZE-len(before))
    need(all(extended[a:b]==b'\xFF'*(b-a) for a,b in RESERVATIONS),'strict erased audio reservations')
    refs=inbound(before)
    need(not refs,'pre-existing pointer/ARM encoding into audio reservation: '+str(refs[:8]))
    rejected=inbound(before,((0x730000,0x760000),))
    old_pointer=struct.pack('<I',BASE+OLD_TABLE)
    hits=tuple(i for i in range(len(before)-3) if before[i:i+4]==old_pointer)
    need(hits==LITERALS,'complete existing native song-table literal set')
    need(before[0xD14A8:0xD14FC]==gba[0xD14A8:0xD14FC],'unmodified evolution selector')
    placements=[]
    table=bytearray(before[OLD_TABLE:OLD_TABLE+COUNT*8]+bytes(4*8))
    cursor=START+len(table)
    def place(data,label):
        nonlocal cursor
        cursor=(cursor+3)&~3
        for begin,end in RESERVATIONS:
            candidate=max(begin,cursor)
            if candidate+len(data)<=end:
                cursor=candidate
                break
        else: raise ValueError('bounded native audio allocations')
        at=cursor
        placements.append((at,data,label));cursor+=len(data)
        return at
    categories=place(CATEGORIES,'source_character_categories')
    pairs=place(bytes(sum(([COUNT+n,4] for n in range(4)),[])),'native_evolution_pairs')
    wave_set=sorted({n['wave'] for s in source['songs'] for c in s['channels'] for n in c['notes'] if n['midi_note'] is not None and not (c['hardware_channel']==3 and n['effect'])})
    voice_ids={wave:index for index,wave in enumerate(wave_set)}
    voice_ids['noise0']=len(voice_ids)
    sample_freq=round(3072000*4*1024/pitch_divisor(wsc,0))
    samples=[]
    for wave in wave_set:
        packed=wsc[0x754CC0+wave*16:0x754CD0+wave*16]
        pcm=bytes((value*16-120)&255 for byte in packed for value in (byte&15,byte>>4))
        # Native PCM header: status bit30=loop, frequency units1/1024Hz,
        # loop start0, sample count32; signed8 data uses original WSC shape.
        samples.append(place(struct.pack('<IIII',0x40000000,sample_freq,0,len(pcm))+pcm+pcm[:1],f'original_wave_{wave:02X}'))
    pcm=noise_samples()
    samples.append(place(struct.pack('<IIII',0x40000000,sample_freq,0,len(pcm))+pcm+pcm[:1],'wsc_noise_mode0'))
    voices=place(b''.join(bytes((0,60,0,0))+struct.pack('<I',BASE+at)+bytes((255,0,255,0)) for at in samples),'original_wave_voices')
    schedules=[]
    for index,song in enumerate(source['songs']):
        tracks=[];details=[]
        for channel in song['channels']:
            track,detail=compile_channel(wsc,channel,voice_ids)
            tracks.append(place(track,f'source_{channel["id"]:02X}_native_track'))
            details.append(dict(source_id=channel['id'],track_sha256=sha(track),**detail))
        header=bytes((4,0,0,128))+struct.pack('<I',BASE+voices)+struct.pack('<4I',*(BASE+t for t in tracks))
        at=place(header,f'song_{COUNT+index:02X}')
        struct.pack_into('<IHH',table,(COUNT+index)*8,BASE+at,0,0)
        schedules.append(dict(source_base_id=song['source_base_id'],native_id=COUNT+index,
                              header=at,channels=details))
    placements.insert(0,(START,bytes(table),'expanded_song_table_00_6F'))
    need(cursor<=END,'bounded native audio allocation')
    after=bytearray(extended);writes=[];allowed=set()
    def patch(at,old,new,label):
        need(extended[at:at+len(old)]==old and len(old)==len(new),'Expected Write '+label)
        after[at:at+len(new)]=new
        allowed.update(range(at,at+len(new)))
        writes.append(dict(offset=at,size=len(new),label=label,before_hex=old.hex(),after_sha256=sha(new)))
    for at,blob,label in placements:patch(at,b'\xFF'*len(blob),blob,label)
    for at in LITERALS:patch(at,old_pointer,struct.pack('<I',BASE+START),'song-table lookup')
    for at,pointer in ((0xD14A8,BASE+categories),(0xD14AC,BASE+pairs),(0xD14B0,BASE+pairs+1)):
        patch(at,before[at:at+4],struct.pack('<I',pointer),'selector base literal')
    for at,literal in ((0xD14C4,0xD14A8),(0xD14D0,0xD14AC),(0xD14D8,0xD14B0)):
        instruction=0xE51F8000|(at+8-literal) # LDR r8,[pc,#-delta]
        patch(at,before[at:at+4],struct.pack('<I',instruction),'selector literal load')
    changed={i for i,(a,b) in enumerate(zip(extended,after,strict=True)) if a!=b}
    need(changed and changed<=allowed,'whole-ROM exact containment')
    restored=bytearray(after)
    for write in writes:
        at=write['offset'];restored[at:at+write['size']]=bytes.fromhex(write['before_hex'])
    need(bytes(restored)==extended,'complete inverse restores byte-identical FF extension')
    need(bytes(restored[:len(before)])==before,'truncated inverse equals frozen input')
    need(after[START:START+COUNT*8]==before[OLD_TABLE:OLD_TABLE+COUNT*8],'all108 prior song entries exact')
    gba_tick=(16777216/280896)*(95/75)
    wsc_tick=3072000/(256*159)
    report=dict(input_sha256=INPUT,output_sha256=sha(after),source_report_sha256=sha(json.dumps(source,sort_keys=True).encode()),
                reservations=RESERVATIONS,used_end=cursor,writes=writes,changed_bytes=len(changed),
                input_size=len(before),output_size=len(after),extension_fill=255,
                preserved_song_entries=COUNT,source=source,schedules=schedules,
                source_wave_ids=wave_set,sample_frequency_field=sample_freq,
                pitch_contract=dict(source_packed_zero_divisor=pitch_divisor(wsc,0),
                                    source_sample_clock=3072000,source_wave_samples=32,
                                    source_packed_zero_assigned_native_key=36,native_voice_base_key=60,
                                    frequency_field_formula='round(3072000 * 4 * 1024 / divisor(packed0))',
                                    per_note_correction='actual divisor from source table and octave shift, then quantized native BEND'),
                pointer_arm_inbound_encodings=refs,
                rejected_old_image_reservation=dict(interval=[0x730000,0x760000],encodings=rejected),
                native_tick_hz=gba_tick,source_frame_hz=wsc_tick,
                tempo_relative_error=gba_tick/wsc_tick-1,
                validation_status='isolated development reconstruction; runtime and audible comparison pending',
                limitations=['M4A tempo95 quantizes source update rate; see explicit rate error.',
                             'M4A pitch bend and pan are quantized; pitch errors recorded per channel.',
                             'Original global vibrato phase is represented by a deterministic zero phase.',
                             'Native PCM voices restart waveform phase on notes; source wave phase can continue.',
                             'Source silent infinite rest channels use native FINE; no audible data discarded.',
                             'Source-to-native mixer amplitude, update latency and noise reset parity need capture.',
                             'No requested title is asserted from numeric IDs alone.',
                             'No Thumb/data ownership or actual runtime caller-domain proof is claimed by this pointer/ARM scan.'],
                hardware_noise_reference='https://github.com/libretro/beetle-wswan-libretro/blob/master/mednafen/wswan/sound.c')
    return bytes(after),report

def main():
    p=argparse.ArgumentParser()
    for name in ('input','wsc','gba','output','manifest'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    paths=[getattr(a,n).resolve() for n in ('input','wsc','gba','output','manifest')]
    need(len(set(paths))==len(paths),'all input/output paths distinct')
    need(not a.output.exists() and not a.manifest.exists(),'fresh component and manifest outputs')
    after,report=build(a.input.read_bytes(),a.wsc.read_bytes(),a.gba.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('output_sha256','changed_bytes','used_end','tempo_relative_error')}))

if __name__=='__main__':main()
