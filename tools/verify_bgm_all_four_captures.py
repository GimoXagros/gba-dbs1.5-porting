"""Bounded completed render inventory, initialization, duration and spectral audit."""
from pathlib import Path
import hashlib,json,re,struct,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
    if not v:raise ValueError(s)
def main():
    source_dir=ROOT/'build/evolution-music-render-fixtures-20261110-r1';native_dir=ROOT/'build/evolution-music-render-fixtures-20261110-r2'
    manifests={}
    for key,d,pin in [('wsc',source_dir,'FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F'),('gba',native_dir,'CE2DC41BB52843B7022027A724115F30D9A5D9695302F7633655590A46028AD9')]:
        raw=(d/'manifest.json').read_bytes();need(sha(raw)==pin,'fixture manifest');manifests[key]=json.loads(raw)
    rates={'wsc':3072000/(256*159),'gba':16777216/280896};start={'wsc':521,'gba':535};results=[]
    for sid,updates in zip((56,60,64,248),(3309,2753,2972,2089)):
        pair={};arrays={}
        for p in ('wsc','gba'):
            suffix='-uninterrupted' if p=='gba' else '';d=ROOT/f'build/bgm-render-{p}-{sid:02x}{suffix}-20261110-a'
            raw=(d/'report.json').read_bytes();r=json.loads(raw);need(r['exited_before_deadline'],'finished capture')
            host='build/run_bgm_uninterrupted_render_20261110.py' if p=='gba' else 'build/run_bgm_render_20261110.py'
            hostpin='546B4A1F1892A2B154FD8FA621482EB2EEF50A2AC6965D3ED2E204143716BD21' if p=='gba' else 'AD087E2F9130E8467D3930469E08B1C88BCB4C7B845BF87D5FE40985C82162A4'
            need(sha((ROOT/host).read_bytes())==r['launcher_sha256']==hostpin,'actual host pin')
            need(r['observer_sha256']=='09D3A36CB410D2B550C16734425498065154900D27C5462ECBFE4145CD2E2C49','observer pin')
            need(r['fixture_gate_sha256']==('BCCE368043295E0E5420C32B7BF7044AD807086840B4327C53F34561F67E48B6' if p=='gba' else 'FB77CBEDAB114B4EEB32A1A930250653D130ECC69A7D9DE30073C1A10FF92B5C'),'fixture gate')
            f=next(x for x in manifests[p]['fixtures'] if x['source_base_id']==sid and (p=='gba' or x['platform']=='WSC'));need(r['fixture']==f,'fixture entry')
            ext='gba' if p=='gba' else 'wsc';rom=(d/f'fixture.{ext}').read_bytes();need(sha(rom)==f['output_sha256'],'actual copied ROM')
            inventory={x.relative_to(d).as_posix():sha(x.read_bytes()) for x in d.rglob('*') if x.is_file() and x.name!='report.json'};need(inventory==r['files'],'complete exact inventory')
            cfg=json.loads((d/'config.json').read_text(encoding='utf-8-sig'));need(all(cfg[k] is False for k in ('SoundEnabled','SoundEnabledNormal','AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM')),'saved audio/input/save isolation')
            with wave.open(str(d/'music.wav'),'rb') as w:
                need((w.getnchannels(),w.getframerate(),w.getsampwidth())==(2,44100,2),'PCM format');a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').reshape(-1,2).astype(float)
            need(len(a)==r['samples'] and np.count_nonzero(a)==r['nonzero_samples'] and int(np.max(abs(a)))==r['peak'],'PCM values')
            need(abs(len(a)/44100-4400/rates[p])<.05,'dump frame duration');arrays[p]=a
            trace=(d/'music-requests.txt').read_text();lines=trace.splitlines()
            if p=='wsc':
                line=next(x for x in lines if x.startswith('frame=521 '))
                for ch in range(4):
                    state,hw,offset=struct.unpack_from('<HHH',rom,0x3F0528+6*ch)
                    match=re.search(fr'slot{ch+4}=([0-9A-F]+)/(?:ch)(\d+)',line);need(match and int(match[1],16)==offset and int(match[2])&3==hw,'actual source four-channel initialization')
            else:need('frame=534 id=0001 type=0004 flags=0100' in lines and 'frame=535 id=0001 type=0004 flags=0000' in lines,'actual native request consumption')
            nz=np.flatnonzero(np.any(a!=0,axis=1));end=(int(nz[-1])+1)/44100;expected=start[p]/rates[p]+updates/(rates[p]*(95/75 if p=='gba' else 1))
            if p=='gba':need(abs(end-expected)<.1,'native PCM reaches expected full duration')
            pair[p]=dict(capture_report_sha256=sha(raw),wav_sha256=inventory['music.wav'],files=len(inventory)+1,seconds=len(a)/44100,last_nonzero_seconds=end,predicted_end_seconds=expected,end_difference_seconds=end-expected,peak=r['peak'],clipped_samples=int(np.count_nonzero(abs(a)>=32767)),request_trace=lines if p=='gba' else [x for x in lines if 'frame=521 ' in x or 'id=0000 ' in x])
        freq=np.fft.rfftfreq(8192,1/44100);grid=np.geomspace(100,5000,192);spectra={};duration=min(updates/rates['wsc']-1,38)
        for p,a in arrays.items():
            spectra[p]=[];scale=1 if p=='wsc' else rates['wsc']/(rates['gba']*95/75)
            for t in np.arange(1,duration,1):
                at=int((start[p]/rates[p]+t*scale)*44100);power=np.mean(abs(np.fft.rfft(a[at:at+8192]*np.hanning(8192)[:,None],axis=0))**2,axis=1);spectra[p].append(np.sqrt(np.interp(grid,freq,power)))
        cosine={}
        for factor in (.5,1,2):
            vals=[]
            for x,y in zip(spectra['wsc'],spectra['gba']):
                z=np.interp(grid*factor,grid,y,left=0,right=0);vals.append(float(np.dot(x,z)/(np.linalg.norm(x)*np.linalg.norm(z)+1e-20)))
            cosine[str(factor)]=float(np.median(vals))
        results.append(dict(source_id=f'{sid:02X}',source_schedule_driver_updates=updates,captures=pair,spectral_windows=len(spectra['wsc']),spectral_cosine_median_by_native_frequency_factor=cosine))
    report=dict(status='PASS_CAPTURE_PROVENANCE_AND_NATIVE_DURATION',verifier_sha256=sha(Path(__file__).read_bytes()),pairs=results,limits=['Render-only stop suppression is not a production change or evolution activation proof.','Source schedules count driver updates, not outer frames;38 diagnostic independently proves11 skipped passes. Other source end differences remain qualified.','Spectral similarity is descriptive and gain-normalized; no listening, timbre, stereo-envelope or title-identity verdict.','Native PCM duration is observed; player FINE states are not directly traced.'])
    out=ROOT/'build/bgm-all-four-capture-qa-20261110/report.json';out.parent.mkdir(exist_ok=True);need(not out.exists(),'fresh report');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(out.read_bytes()),pairs=[dict(source_id=x['source_id'],spectral=x['spectral_cosine_median_by_native_frequency_factor'],ends={k:v['end_difference_seconds'] for k,v in x['captures'].items()}) for x in results])))
if __name__=='__main__':main()
