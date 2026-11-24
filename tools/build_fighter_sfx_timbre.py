"""Restore the five fighter cues from isolated original driver PCM and source wave RAM."""
import argparse
from array import array
import json
import math
from pathlib import Path
import struct
import sys
import wave

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from build_character_audio import SCORES
from render_fighter_sfx import IDS, SOURCE

READERS=(0x37c2a4,0x37c2d8,0x37c324,0x37c378,0x37c3ac)
RATE=10512
ORIGINAL_ROWS='4A00A52D38D41DD0FF36B4090BFAA29AE8164F32B333FFB9024E85930F93BA00'
DURATION=(20,48,45,20,50)
SAMPLES_PER_UPDATE=44100*159*256/3072000
FIRST_SAMPLE=round(521*SAMPLES_PER_UPDATE)


def load_stems(folder):
    meta=json.loads((folder/'report.json').read_bytes())
    assert meta['platform']=='wsc' and meta['rom_sha256']==SOURCE
    assert sha(json.dumps(meta['rows'],sort_keys=True,separators=(',',':')).encode())==ORIGINAL_ROWS
    stems={}
    for row in meta['rows']:
        sid=row['source']
        path=folder/f'{sid:02x}'/'render.wav'
        assert sha(path.read_bytes())==row['wav_sha256']
        assert sha((path.parent/'trace.txt').read_bytes())==row['trace_sha256']
        with wave.open(str(path)) as f:
            assert (f.getframerate(),f.getnchannels(),f.getsampwidth())==(44100,2,2)
            samples=array('h',f.readframes(f.getnframes()))
        if sys.byteorder!='little':
            samples.byteswap()
        n=round((DURATION[IDS.index(sid)]+3)*SAMPLES_PER_UPDATE)
        right=samples[FIRST_SAMPLE*2+1:(FIRST_SAMPLE+n)*2:2]
        assert right==samples[FIRST_SAMPLE*2:(FIRST_SAMPLE+n)*2:2]
        assert all(abs(v)<2 for v in samples[(FIRST_SAMPLE-4000)*2:(FIRST_SAMPLE-32)*2])
        stems[sid]=right
    return stems


def bandlimited(stem):
    # Sample directly at this game's 176 PCM samples per VBlank. A symmetric
    # Blackman-windowed low pass prevents the original harmonics folding down.
    output=bytearray()
    taps=40
    cutoff=0.47*RATE/44100
    for i in range(round(len(stem)*RATE/44100)):
        center=i*44100/RATE
        low=int(center)-taps
        value=weight=0.
        for k in range(low,low+2*taps+1):
            delta=k-center
            x=delta/taps
            if abs(x)>=1:continue
            win=.42+.5*math.cos(math.pi*x)+.08*math.cos(2*math.pi*x)
            sinc=2*cutoff if not delta else math.sin(2*math.pi*cutoff*delta)/(math.pi*delta)
            coeff=win*sinc
            weight+=coeff
            if 0<=k<len(stem):value+=stem[k]*coeff
        output.append(max(-127,min(127,round(value/weight/40)))&255)
    return bytes(output)


def c6_sequence(source):
    packed=source[0x754cc0+4*16:0x754cc0+5*16]
    wave32=[n for x in packed for n in (x&15,x>>4)]
    assert wave32==[15]*20+[0]*12
    # Wave RAM plays four identical periods per 32 steps so the GBA has
    # finer period resolution for these 10.67..16 kHz source notes.
    # At the lowest of these four source frequencies, its second harmonic
    # already exceeds 21 kHz. Preserve the measured original fundamental
    # without folding the ultrasonic square-wave harmonics into the GBA mix.
    harmonic=sum(v*complex(math.cos(2*math.pi*j/32),-math.sin(2*math.pi*j/32))
                 for j,v in enumerate(wave32))/32
    phase=[(harmonic*complex(math.cos(2*math.pi*j/8),math.sin(2*math.pi*j/8))).real
           for j in range(8)]*4
    banks=[]
    for level in (15,9,6):
        wave4=[round(3+3*x/max(abs(v) for v in phase)*level/15) for x in phase]
        banks.append(bytes(16*hi+lo for hi,lo in zip(wave4[::2],wave4[1::2])))
    banks.append(bytes(16))
    data=source[0x3f8816:0x3f883c]
    assert data.hex()=='00000f001f08a204a00f7904770475047304a0097904770475047304a00679047704ffffffff'
    keys={0x79:120,0x77:117,0x75:114,0x73:112}
    seq=bytearray((0xbc,0,0xbb,95,0xbe,127,0xbf,64,0xc1,1))
    for op,arg in zip(data[4::2],data[5::2]):
        if op==0xa0:seq.extend((0xbd,(15,9,6).index(arg)))
        elif op==0x1f:seq.extend(b'\x81'*arg)
        elif op in keys:
            seq.extend((0xc0,96 if op==0x75 else 64,0xcf+arg,keys[op],127))
            seq.extend(b'\x81'*arg)
        else:assert op in (0xa2,0xff)
    # Let the real wave DAC sample zero before the M4A release.
    seq.extend((0xbd,3,0xd0,60,127,0x81,0xb1))
    return banks,bytes(seq)


def build(before,raw_owner,source,stems,input_hash,owner_hash):
    meta=json.loads(raw_owner)
    assert sha(before)==meta['output_sha256']==input_hash and sha(raw_owner)==owner_hash
    assert sha(source)==SOURCE
    assert [x[0] for x in SCORES]==list(IDS)
    for sid,raw,pattern in SCORES:
        slot,channel,ptr=struct.unpack_from('<3H',source,0x3f0000+6*sid)
        assert channel==2 and raw==0x3f0000+ptr and source[raw:raw+len(pattern)//2]==bytes.fromhex(pattern)
    table=struct.unpack_from('<I',before,READERS[0])[0]-BASE
    assert all(struct.unpack_from('<I',before,r)[0]==BASE+table for r in READERS)
    original=before[table+0x5f*8:table+0x64*8]
    assert original==before[0x683200+0x5f*8:0x683200+0x64*8]
    used=meta['prior_excluded_extents']+[[r['start'],r['end']] for r in meta['allocations']]
    alloc=Allocator(before);exclude(alloc,used)
    after=bytearray(before)
    writes=[]
    def write(at,payload,why):
        assert after[at:at+len(payload)]==before[at:at+len(payload)]
        writes.append(dict(offset=at,size=len(payload),purpose=why,before_sha256=sha(before[at:at+len(payload)]),after_sha256=sha(payload)))
        after[at:at+len(payload)]=payload
    def reserve(payload,why):
        loc=alloc.allocate(len(payload),why,4)
        write(loc,payload,why)
        return loc
    rows=[]
    for i,sid in enumerate(IDS):
        title=f'fighter sound {sid:02X}'
        if sid==0xc6:
            banks,track=c6_sequence(source)
            sample_at=[reserve(bank,title+' source wavetable') for bank in banks]
            group=b''.join(bytes((3,60,0,0))+struct.pack('<I',BASE+a)+bytes((0,0,15,0)) for a in sample_at)
        else:
            pcm=bandlimited(stems[sid])
            data=struct.pack('<4I',0,RATE*1024,0,len(pcm))+pcm+b'\0'
            sample_at=[reserve(data,title+' original sweep PCM')]
            group=bytes((0,60,0,0))+struct.pack('<I',BASE+sample_at[0])+bytes((255,0,255,0))
            track=bytes((0xbc,0,0xbb,95,0xbd,0,0xbe,56,0xbf,64,0xcf,60,127))+b'\x81'*(DURATION[i]+3)+bytes((0xce,60,0xb1))
        voice=reserve(group,title+' voice')
        tr=reserve(track,title+' track')
        header=reserve(bytes((1,0,40,128))+struct.pack('<2I',BASE+voice,BASE+tr),title+' header')
        dest=table+8*(0x5f+i)
        write(dest,struct.pack('<I',BASE+header),title+' existing player 4 row')
        rows.append(dict(source=sid,native=0x5f+i,header=header,track=tr,voice=voice,samples=sample_at))
    return after,dict(input_sha256=input_hash,prior_owner_sha256=owner_hash,source_sha256=SOURCE,
                      output_sha256=sha(after),source_render_rows_sha256=ORIGINAL_ROWS,prior_excluded_extents=used,
                      allocations=alloc.allocations,storage_exports=meta['storage_exports'],writes=writes,table=table,
                      rows=rows,module_sha256=sha(Path(__file__).read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('input','source','owner','renders','output'):
        p.add_argument('--'+key,required=True,type=Path)
    for key in ('input-sha256','owner-sha256'):
        p.add_argument('--'+key,required=True)
    a=p.parse_args()
    result,meta=build(a.input.read_bytes(),a.owner.read_bytes(),a.source.read_bytes(),
                      load_stems(a.renders),a.input_sha256,a.owner_sha256)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/'component.gba').write_bytes(result)
    report=a.output/'manifest.json'
    report.write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(meta['output_sha256'],sha(report.read_bytes()))


if __name__=='__main__':
    main()

