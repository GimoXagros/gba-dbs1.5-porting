"""Audit completed first render pair; descriptive PCM metrics, no audio-quality verdict."""
import hashlib,json,re,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
    if not v:raise ValueError(s)
def main():
    manifest=json.loads((ROOT/'build/evolution-music-render-fixtures-20261110-r1/manifest.json').read_bytes())
    rates={'wsc':3072000/(256*159),'gba':16777216/280896}; starts={'wsc':521,'gba':535}
    pins={'launcher_sha256':'AD087E2F9130E8467D3930469E08B1C88BCB4C7B845BF87D5FE40985C82162A4','observer_sha256':'09D3A36CB410D2B550C16734425498065154900D27C5462ECBFE4145CD2E2C49','fixture_gate_sha256':'FB77CBEDAB114B4EEB32A1A930250653D130ECC69A7D9DE30073C1A10FF92B5C','fixture_manifest_sha256':'FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F'}
    results={};arrays={}
    for platform in ('wsc','gba'):
        d=ROOT/f'build/bgm-render-{platform}-38-20261110-a';raw=(d/'report.json').read_bytes();r=json.loads(raw)
        need(all(r[k]==v for k,v in pins.items()),'frozen host/observer/gate')
        need(r['exited_before_deadline'] and all(r[k] is False for k in ('visible','supplied_save_used','guest_writes','input_injected','physical_audio_requested')),'launch assertions')
        files={p.relative_to(d).as_posix():sha(p.read_bytes()) for p in d.rglob('*') if p.is_file() and p.name!='report.json'}
        need(files==r['files'],'exact complete file inventory')
        fixture=next(x for x in manifest['fixtures'] if x['platform']==platform.upper() and x['category']==0)
        need(r['fixture']==fixture,'exact fixture binding')
        cfg=json.loads((d/'config.json').read_text(encoding='utf-8-sig'))
        need(all(cfg[x] is False for x in ('SoundEnabled','SoundEnabledNormal','AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM')) and cfg['SoundVolume']==cfg['SoundVolumeRWFF']==0,'saved isolation and physical audio off')
        with wave.open(str(d/'music.wav'),'rb') as w:
            need((w.getnchannels(),w.getframerate(),w.getsampwidth())==(2,44100,2),'stereo 44100 PCM16')
            a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(np.float64)
        need(len(a)==r['samples'] and np.count_nonzero(a)==r['nonzero_samples'] and int(np.max(abs(a)))==r['peak'],'actual PCM measurements')
        duration=len(a)/44100;need(abs(duration-4400/rates[platform])<.05,'4400 platform frames worth of audio')
        nonzero=np.flatnonzero(np.any(a!=0,axis=1));arrays[platform]=a
        trace=(d/'music-requests.txt').read_text();rows=[dict(frame=int(f),id=int(i,16),type=int(t,16),flags=int(g,16)) for f,i,t,g in re.findall(r'frame=(\d+) id=([\dA-F]+) type=([\dA-F]+) flags=([\dA-F]+)',trace)]
        if platform=='gba':
            need(rows[-4:]==[dict(frame=534,id=1,type=4,flags=256),dict(frame=535,id=1,type=4,flags=0),dict(frame=2883,id=0,type=4,flags=256),dict(frame=2884,id=0,type=4,flags=0)],'native start and later stop request')
        else:
            line=next(x for x in trace.splitlines() if x.startswith('frame=521 '))
            need(all(x in line for x in ('slot4=3840/ch64','slot5=3930/ch33','slot6=3EDA/ch146','slot7=422C/ch35')),'source selected group initialized with actual channel states')
            last=trace.splitlines()[-1];need(last.startswith('frame=3517 ') and 'slot0=0648/ch0' in last and all(x in last for x in ('slot4=3840','slot5=3930','slot6=3EDA','slot7=422C')),'foreground replacement retains background descriptors')
        results[platform]=dict(report_sha256=sha(raw),files=len(files)+1,wav_sha256=r['wav_sha256'],frames=len(a),seconds=duration,last_nonzero_seconds=(int(nonzero[-1])+1)/44100,first_nonzero_seconds=int(nonzero[0])/44100,peak=r['peak'],clipped_samples=int(np.count_nonzero(abs(a)>=32767)),channel_rms=np.sqrt(np.mean(a*a,axis=0)).tolist(),requests=rows)
    # 50 ms stereo-energy windows, aligned by observed driver initialization.
    times=np.arange(.1,38,.05);envelopes={}
    for p in arrays:
        a=arrays[p];start=starts[p]/rates[p]
        # Account for the independently established native tempo error.
        scale=1 if p=='wsc' else 1/(rates['gba']*(95/75)/rates['wsc'])
        envelopes[p]=np.array([np.sqrt(np.mean(a[int((start+t*scale)*44100):int((start+(t+.05)*scale)*44100)]**2)) for t in times])
    corr=float(np.corrcoef(envelopes['wsc'],envelopes['gba'])[0,1])
    # Frequency landmarks from each core's own PCM, normalized independently.
    freq=np.fft.rfftfreq(8192,1/44100);grid=np.geomspace(100,5000,192)
    spectra={};landmarks={}
    for p,a in arrays.items():
        spectra[p]=[];landmarks[p]=[]
        scale=1 if p=='wsc' else 1/(rates['gba']*(95/75)/rates['wsc'])
        for t in np.arange(1,37,1):
            at=int((starts[p]/rates[p]+t*scale)*44100)
            power=np.mean(abs(np.fft.rfft(a[at:at+8192]*np.hanning(8192)[:,None],axis=0))**2,axis=1)
            selected=(freq>=100)&(freq<=5000)
            landmarks[p].append(float(freq[selected][np.argmax(power[selected])]))
            spectra[p].append(np.sqrt(np.interp(grid,freq,power)))
    similarities={}
    for factor in (.5,1,2):
        vals=[]
        for left,right in zip(spectra['wsc'],spectra['gba']):
            shifted=np.interp(grid*factor,grid,right,left=0,right=0)
            vals.append(float(np.dot(left,shifted)/(np.linalg.norm(left)*np.linalg.norm(shifted)+1e-20)))
        similarities[str(factor)]=float(np.median(vals))
    expected=535/rates['gba']+3309/(rates['gba']*95/75)
    report=dict(status='PASS_CAPTURE_PROVENANCE_PARTIAL_NATIVE_RENDER',verifier_sha256=sha(Path(__file__).read_bytes()),captures=results,comparison=dict(aligned_window_seconds=38,window_seconds=.05,stereo_rms_envelope_correlation=corr,native_expected_schedule_end_seconds=expected,native_stop_consumed_seconds=2884/rates['gba'],native_last_sample_shortfall_seconds=expected-results['gba']['last_nonzero_seconds']),limits=['Native fixture is interrupted; this is not a complete score capture.','Source later00 request targets foreground slots while background descriptors remain; descriptor retention alone is not complete event tracing.','PCM envelope correlation is descriptive, not audible quality, pitch identity or arrangement parity.','No emulator or playback listening performed by this audit; launcher exit codes were reported by root, not stored by host.'])
    report['comparison'].update(spectral_cosine_median_by_native_frequency_factor=similarities,dominant_frequency_landmarks_hz=landmarks,source_expected_schedule_end_seconds=521/rates['wsc']+3309/rates['wsc'],source_end_timing_qualified=True)
    out=ROOT/'build/bgm-render-pair38-capture-qa-20261110/report.json';out.parent.mkdir(exist_ok=True);need(not out.exists(),'fresh report');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(out.read_bytes()),comparison=report['comparison'],captures={p:{k:v for k,v in x.items() if k in ('seconds','last_nonzero_seconds','peak','clipped_samples')} for p,x in results.items()})))
if __name__=='__main__':main()
