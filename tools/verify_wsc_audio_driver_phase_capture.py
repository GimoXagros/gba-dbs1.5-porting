"""Actual source diagnostic noninterference and driver-pass timing audit."""
from pathlib import Path
import collections,hashlib,json,re,struct
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
    if not v:raise ValueError(s)
def main():
    d=ROOT/'build/bgm-render-wsc-38-driverphase-20261110-a';old=ROOT/'build/bgm-render-wsc-38-20261110-a'
    r=json.loads((d/'report.json').read_bytes())
    need(r['exited_before_deadline'] and r['observer_sha256']=='D657CE693873BDC2622453EA5EDD188E71777873CD288C148ED5393A9B1CEA16','completed frozen observer')
    need(sha((ROOT/'build/run_bgm_driver_phase_r1_20261110.py').read_bytes())==r['launcher_sha256']=='B2CC988C73359CFD8DBE0CAE59E23315B3D58A546C443141C8A8EEBDD03FD94A','actual host')
    files={p.relative_to(d).as_posix():sha(p.read_bytes()) for p in d.rglob('*') if p.is_file() and p.name!='report.json'};need(files==r['files'],'complete inventory')
    for name in ('music.wav','music-requests.txt','fixture.wsc','data/276/fixture.SaveRAM'):
        need((d/name).read_bytes()==(old/name).read_bytes(),'exact prior evidence '+name)
    cfg=json.loads((d/'config.json').read_text(encoding='utf-8-sig'));need(cfg['SoundEnabled'] is False and cfg['SoundEnabledNormal'] is False and cfg['AcceptBackgroundInput'] is False,'saved isolation')
    rows=[]
    for line in (d/'audio-driver-phase.txt').read_text().splitlines():
        f,p,g,s=re.fullmatch(r'frame=(\d+) phase=([0-9A-F]{2}) flags=([0-9A-F]{4}) states=([0-9A-F]{336})',line).groups();rows.append((int(f),int(p,16),int(g,16),bytes.fromhex(s)))
    need([x[0] for x in rows]==list(range(1,4401)),'4400 consecutive samples')
    delta=[(b[1]-a[1])%256 for a,b in zip(rows,rows[1:])];need(set(delta)<={0,1},'bounded modulo deltas')
    need(all(x[2]&4==0 for x in rows[520:]),'normal driver after initialization')
    gaps=[b[0] for a,b in zip(rows[520:],rows[521:]) if (b[1]-a[1])%256==0]
    ends=[]
    for ch in range(4):
        end=next(x[0] for x in rows[521:] if struct.unpack_from('<H',x[3],42*ch)[0]==65535)
        passes=sum((b[1]-a[1])%256 for a,b in zip(rows[520:end-1],rows[521:end]));ends.append(dict(channel=ch,end_frame=end,outer_frames=end-521,driver_updates=passes))
    need([x['driver_updates'] for x in ends]==[2843,3295,2843,3309],'observed finite score lengths')
    fractions=countdowns=0
    for a,b in zip(rows[520:],rows[521:]):
        dt=(b[1]-a[1])%256
        for ch in range(4):
            x=a[3][42*ch:42*(ch+1)];y=b[3][42*ch:42*(ch+1)];cx=int.from_bytes(x[:2],'little');cy=int.from_bytes(y[:2],'little')
            if cx==65535 or cy==65535:continue
            need(y[7]==(x[7]+dt*(x[6]&15))%16,'actual fractional accumulator');fractions+=1
            if cx==cy and x[9]>1:
                need(y[9]==x[9]-(dt and x[7]+(x[6]&15)<16),'actual stable-cursor countdown');countdowns+=1
    report=dict(status='PASS_ACTUAL_DRIVER_UPDATE_TIMING',verifier_sha256=sha(Path(__file__).read_bytes()),capture_report_sha256=sha((d/'report.json').read_bytes()),wav_sha256=r['wav_sha256'],trace_sha256=r['trace_sha256'],phase_trace_sha256=files['audio-driver-phase.txt'],files=len(files)+1,rows=len(rows),delta_counts=dict(collections.Counter(delta)),gap_frames_after_initialization=gaps,channel_ends=ends,fraction_checks=fractions,countdown_checks=countdowns,conclusion='Longest source channel takes exactly3309 driver updates across3320 outer frames. Eleven skipped driver passes explain accumulating drift; no tempo retune justified.',limits=['Counter is modulo256; bounded trace and state transitions support0/1 interpretation, not instruction-level tracing.','PCM output continues briefly beyond final cursor termination; filter/mixer latency not separately measured.'])
    out=ROOT/'build/wsc-audio-driver-phase-capture-qa-20261110/report.json';out.parent.mkdir(exist_ok=True);need(not out.exists(),'fresh report');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(out.read_bytes()),verifier_sha256=report['verifier_sha256'])))
if __name__=='__main__':main()
