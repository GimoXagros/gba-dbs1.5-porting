"""Independently audit five installed fighter SFX, source records, PCM and native tone periods."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import wave

import numpy as np

BASE=0x08000000
SOURCES=(0xBC,0xC6,0xC8,0xCB,0xCC)
DURATIONS=(20,48,45,20,50)
FREQ=10512
ROOT_HASH='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
STEM_PINS=(
 'E46438141432E337079D6AAC83587E5326BF026B8022848707EFF9CE55E96F87',
 '3CF6A32B9AFC6032C0680079AC04C708ED8469F26239EC2BC7E619D44BA0BE18',
 '8CA63DC491FF43CEE2B3C2F9CC9AB9199EC2489E25BD4F1E89D3A328CB3E9AA4',
 '881D36791FC654E87CB92DFDFC9B46C123DF6647F773D30161C05233535867CF',
 '93DA8AD3C22AF379AB161C2F6351B3B1B9AA0E4254AF4CE5FEEE120A8396370D')


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def ptr(data,addr):
    return struct.unpack_from('<I',data,addr)[0]-BASE


def release_sample(stem,pcm):
    # Independently reconstruct the integer sample target, including zero
    # padding instead of wraparound at each finite cue's boundaries.
    centers=np.arange(len(pcm))*(44100/FREQ)
    offsets=centers.astype(np.int64)[:,None]+np.arange(-40,41)[None,:]
    diff=offsets-centers[:,None]
    width=diff/40
    window=.42+.5*np.cos(np.pi*width)+.08*np.cos(2*np.pi*width)
    window[np.abs(width)>=1]=0
    b=.94*FREQ/44100
    kernel=b*np.sinc(b*diff)*window
    padded=np.r_[stem,0.]
    locations=np.where((offsets>=0)&(offsets<len(stem)),offsets,len(stem))
    ref=np.clip(np.rint((padded[locations]*kernel).sum(axis=1)/kernel.sum(axis=1)/40),-127,127)
    actual=np.frombuffer(pcm,'i1')
    assert np.array_equal(actual,ref)


def c6_check(source,image,voice,track):
    source_data=source[0x3f8816:0x3f883c]
    desired=[]
    level=15
    for op,arg in zip(source_data[4::2],source_data[5::2]):
        if op==0xa0:level=arg
        elif op in (0x79,0x77,0x75,0x73):
            tone=struct.unpack_from('<H',source,0x754837+2*(op&15))[0]>>(op>>4)
            desired.append((level,arg,3072000/(tone*32)))
    assert len(desired)==10
    source_wave=source[0x754d00:0x754d10]
    bits=[v for octet in source_wave for v in (octet%16,octet//16)]
    assert bits==[15]*20+[0]*12
    magnitudes=[]
    for n in range(4):
        at=voice+12*n
        assert image[at:at+4]==bytes((3,60,0,0)) and image[at+8:at+12]==bytes((0,0,15,0))
        data=image[ptr(image,at+4):ptr(image,at+4)+16]
        pts=np.array([v for b in data for v in (b>>4,b&15)])
        assert np.all(pts==np.tile(pts[:8],4))
        if n==3:
            assert not pts.any()
        else:
            spectrum=np.abs(np.fft.rfft(pts-pts.mean()))
            assert spectrum.argmax()==4
            magnitudes.append(float(spectrum[4]))
    assert magnitudes[0]>magnitudes[1]>magnitudes[2]>0
    t=track
    assert image[t:t+10]==bytes((0xbc,0,0xbb,95,0xbe,127,0xbf,64,0xc1,1))
    t+=10
    assert image[t:t+8]==bytes([0x81])*8
    t+=8
    weights=ptr(image,0x37cbf0);period_table=ptr(image,0x37cbf4)
    errors=[]
    peaks=[]
    for n,(level,duration,want) in enumerate(desired):
        if n in (0,4,8):
            assert image[t:t+2]==bytes((0xbd,(15,9,6).index(level)))
            t+=2
        bend,key=image[t+1],image[t+3]
        assert image[t]==0xc0 and image[t+2]==0xcf+duration and image[t+4]==127
        r=[]
        for k in (key,key+1):
            code=image[weights+k-36]
            r.append(struct.unpack_from('<h',image,period_table+2*(code&15))[0]>>(code>>4))
        frac=(bend-64)*4
        period=-(r[0]+((r[1]-r[0])*frac>>8))
        actual=65536*4/period
        errors.append(abs(actual/want-1))
        peaks.append(round(actual,2))
        assert image[t+5:t+5+duration]==bytes([0x81])*duration
        t+=5+duration
    assert max(errors)<.025
    assert image[t:t+7]==bytes((0xbd,3,0xd0,60,127,0x81,0xb1))
    return dict(notes=len(desired),native_fundamentals_hz=peaks[:4],max_relative_pitch_error=max(errors),final_silent_dac=True)


def check(source,prior,image,raw_owner,renders):
    meta=json.loads(raw_owner)
    assert sha(source)==ROOT_HASH and sha(prior)==meta['input_sha256'] and sha(image)==meta['output_sha256']
    table=ptr(prior,0x37c2a4)
    for at in (0x37c2a4,0x37c2d8,0x37c324,0x37c378,0x37c3ac):
        assert ptr(image,at)==ptr(prior,at)==table
    assert image[table:table+8*95]==prior[table:table+8*95]
    assert image[table+8*100:table+8*128]==prior[table+8*100:table+8*128]
    inverse=bytearray(image)
    closed=set()
    for action in meta['writes']:
        a,n=action['offset'],action['size']
        assert sha(prior[a:a+n])==action['before_sha256'] and sha(image[a:a+n])==action['after_sha256']
        if a not in [table+8*i for i in range(95,100)]:
            assert prior[a:a+n]==bytes([255])*n
        else:assert n==4
        part=set(range(a,a+n));assert not closed&part;closed.update(part)
        inverse[a:a+n]=prior[a:a+n]
    assert inverse==prior
    checkrows=[]
    for i,sid in enumerate(SOURCES):
        offset,channel,phrase=struct.unpack_from('<3H',source,0x3f0000+6*sid)
        assert channel==2 and 0x8700<phrase<0x8900
        dest=table+8*(95+i)
        assert image[dest+4:dest+8]==prior[dest+4:dest+8]==bytes((4,0,4,0))
        header=ptr(image,dest)
        assert image[header:header+4]==bytes((1,0,40,128))
        voice,track=ptr(image,header+4),ptr(image,header+8)
        wavfile=renders/f'{sid:02x}'/'render.wav'
        assert sha(wavfile.read_bytes())==STEM_PINS[i]
        with wave.open(str(wavfile)) as wav:
            assert (wav.getframerate(),wav.getnchannels(),wav.getsampwidth())==(44100,2,2)
            sound=np.frombuffer(wav.readframes(wav.getnframes()),'<i2').reshape(-1,2)
        unit=44100*159*256/3072000
        n=round((DURATIONS[i]+3)*unit)
        start=round(521*unit)
        stem=sound[start:start+n,0]
        assert np.array_equal(stem,sound[start:start+n,1])
        if sid==0xc6:
            facts=c6_check(source,image,voice,track)
        else:
            assert image[voice:voice+4]==bytes((0,60,0,0)) and image[voice+8:voice+12]==bytes((255,0,255,0))
            base=ptr(image,voice+4)
            status,hz,loop,length=struct.unpack_from('<4I',image,base)
            assert (status,hz,loop,length)==(0,FREQ*1024,0,round(len(stem)*FREQ/44100))
            assert image[base+16+length]==0
            pcm=image[base+16:base+16+length]
            release_sample(stem,pcm)
            t=bytes((0xbc,0,0xbb,95,0xbd,0,0xbe,56,0xbf,64,0xcf,60,127))+bytes([0x81])*(DURATIONS[i]+3)+bytes((0xce,60,0xb1))
            assert image[track:track+len(t)]==t
            facts=dict(pcm_bytes=length,exact_quantized_source_samples=True)
        checkrows.append(dict(source=sid,native=95+i,slot=offset,hardware_channel=channel,**facts))
    return dict(status='FIVE_ORIGINAL_FIGHTER_TIMBRES_AND_ROW_OWNERSHIP_PASS',source_sha256=ROOT_HASH,
                prior_sha256=sha(prior),image_sha256=sha(image),owner_sha256=sha(raw_owner),
                production_rows_unchanged=123,whole_image_inverse=True,rows=checkrows,
                checker_sha256=sha(Path(__file__).read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','parent','image','owner','renders','report'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    result=check(a.source.read_bytes(),a.parent.read_bytes(),a.image.read_bytes(),a.owner.read_bytes(),a.renders)
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

