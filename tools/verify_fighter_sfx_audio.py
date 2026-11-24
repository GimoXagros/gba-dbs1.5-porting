"""Measure original/new fighter cue similarity, C6 high tones, stereo and terminal silence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import wave

import numpy as np

WSC=3072000/(159*256)
GBA=16777216/280896
IDS=(0xbc,0xc6,0xc8,0xcb,0xcc)
TICKS=(20,48,45,20,50)


def sha(b):return hashlib.sha256(b).hexdigest().upper()


def recording(folder,sid,expected_rom,kind):
    m=json.loads((folder/'report.json').read_bytes())
    assert m['rom_sha256']==expected_rom and m['platform']==kind
    row=next(r for r in m['rows'] if r['source']==sid)
    f=folder/f'{sid:02x}'/'render.wav'
    assert row['wav_sha256']==sha(f.read_bytes()) and row['headless'] and not row['guest_writes']
    trace=f.with_name('trace.txt').read_bytes()
    assert row['trace_sha256']==sha(trace)
    with wave.open(str(f))as w:
        assert (w.getnchannels(),w.getframerate(),w.getsampwidth())==(2,44100,2)
        pcm=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2)
    return pcm,trace.decode().splitlines(),row['wav_sha256']


def fit(stereo,ref):
    start=round(532*44100/GBA)
    steps=round(12*44100/GBA)
    concrete=stereo[start:start+len(ref)+steps].mean(axis=1)
    ref=ref.astype(np.float64);ref-=ref.mean()
    n=1<<(len(concrete)+len(ref)-1).bit_length()
    cov=np.fft.irfft(np.fft.rfft(concrete,n)*np.conj(np.fft.rfft(ref,n)),n)[:steps]
    power=np.cumsum(np.r_[0.,concrete**2])
    norm=np.sqrt(power[len(ref):]-power[:-len(ref)])
    correlation=cov/np.maximum(1.,np.linalg.norm(ref)*norm[:steps])
    i=int(correlation.argmax())
    return start+i,round(float(correlation[i]),5),round(float(norm[i]/np.linalg.norm(ref)),5)


def dominant(y):
    y=y.astype(np.float64)
    y-=y.mean()
    spectrum=np.abs(np.fft.rfft(y*np.hanning(len(y)),8192))
    peaks=np.flatnonzero((spectrum[1:-1]>spectrum[:-2])&(spectrum[1:-1]>=spectrum[2:]))+1
    peaks=peaks[peaks>120]
    top=peaks[np.argsort(spectrum[peaks])[-2:][::-1]]
    return top[0]*44100/8192,spectrum[top[1]]/spectrum[top[0]],float(np.std(y))


def master(rom,source,old,new):
    meta=json.loads((new/'report.json').read_bytes())
    assert meta['rom_sha256']==sha(rom)
    start=round(521*44100/WSC)
    checks=[]
    for i,sid in enumerate(IDS):
        S,logs,sh=recording(source,sid,'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','wsc')
        N,events,nh=recording(new,sid,sha(rom),'gba')
        O,_,oh=recording(old,sid,'D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99','gba')
        table=struct.unpack_from('<I',rom,0x37c2a4)[0]-0x08000000
        header=struct.unpack_from('<I',rom,table+8*(95+i))[0]
        active=[int(f) for f,addr,status in (s.split() for s in events)if int(addr,16)==header and int(status,16)&0xffff]
        assert active and max(active)<610
        assert np.max(np.abs(N[round(611*44100/GBA):round(630*44100/GBA)]))<=1
        source_samples=S[start:start+round(TICKS[i]*44100/WSC)]
        assert np.array_equal(source_samples[:,0],source_samples[:,1])
        if sid==0xc6:
            native=round(544.35*44100/GBA);original=round(529.18*44100/WSC)
            heard=[]
            for j in range(10):
                # Windows inside the held portion, avoiding GBA VBlank onset quantization.
                shift=round(j*4*44100/WSC)
                sp,ss,sr=dominant(S[original+shift+270:original+shift+1294,0])
                gp,gs,gr=dominant(N[native+shift+270:native+shift+1294,0])
                assert abs(gp/sp-1)<.026 and gs<.72 and sr>100 and gr>100,(j,sp,gp,gs)
                heard.append(dict(original_hz=round(sp,2),native_hz=round(gp,2),secondary_to_primary=round(gs,4)))
            assert np.array_equal(N[round(540*44100/GBA):round(605*44100/GBA),0],N[round(540*44100/GBA):round(605*44100/GBA),1])
            facts=dict(actual_ten_tones=heard)
        else:
            _,prior_corr,_=fit(O,source_samples[:,0])
            onset,after_corr,ratio=fit(N,source_samples[:,0])
            assert after_corr>.91 and prior_corr<.14 and .9<ratio<1.08
            actual=N[onset:onset+len(source_samples)].astype(float)
            rms=(actual**2).mean(axis=0)**.5
            assert .97<rms[0]/rms[1]<1.03
            facts=dict(before_correlation=prior_corr,after_correlation=after_corr,native_to_original_rms=ratio)
        checks.append(dict(source=sid,native=95+i,original_pcm=sh,old_pcm=oh,native_pcm=nh,
                           player_on=[min(active),max(active)],terminal_pcm_silent=True,**facts))
    return dict(status='FIVE_HIDDEN_FIGHTER_PCM_COMPARISONS_PASS',rom_sha256=sha(rom),
        rows=checks,limitations='Boot-request substitution isolates each unmodified driver. GBA C6 hardware quantizes periods and retains weaker harmonics. Finite DirectSound sweep samples follow the isolated source capture at the native game mixer rate. No claim of sample-identical analog hardware.',
        checker_sha256=sha(Path(__file__).read_bytes()))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('image','source-renders','old-renders','new-renders','report'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    result=master(a.image.read_bytes(),a.source_renders,a.old_renders,a.new_renders)
    with a.report.open('x',encoding='utf-8',newline='\n')as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

