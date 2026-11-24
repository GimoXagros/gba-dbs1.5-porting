"""Read back exact real MP2K owners and requests around the earned score transition."""
import argparse
import json
import re
from pathlib import Path
from verify_mode23_completion_save import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('capture','presentation','negative','report'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    result=json.loads(a.presentation.read_bytes())
    raw=(a.capture/'award'/'trace.txt').read_bytes()
    lines=raw.decode().splitlines()
    assert result['status']=='MODE11_EARNED_PRESENTATION_AND_COLD_BCD_PASS'
    launch=json.loads((a.capture/'award'/'launch.json').read_bytes())
    assert launch['files']['trace.txt']==sha(raw) and launch['rom_sha256']==result['rom_sha256']
    frame=int(next(s.split()[0] for s in lines if 'award score=' in s))
    times={}
    for key, expected in (('native-audio 03 priority=4 delay=0',61),('native-audio 7F priority=1 delay=0',92),
                          ('audio-state before-number-stop',318),('audio-state after-number-stop',318),
                          ('native-audio 7B priority=1 delay=0',710),('native-audio 7E priority=4 delay=0',824)):
        found=[int(s.split()[0])-frame for s in lines if key in s]
        assert found==[expected],(key,found)
        times[key]=expected
    states={}
    for s in lines:
        m=re.search(r'audio-state (\S+) p0=([0-9A-F]+)/([0-9A-F]+) p3=([0-9A-F]+)/([0-9A-F]+)',s)
        if m:states[m[1]]=tuple(int(v,16) for v in m.groups()[1:])
    assert states['score-105']==states['score-250']==(0x8381f64,7,0x8dac22c,1)
    assert states['score-317']==states['before-number-stop']==(0x8381f64,0x80000000,0x8dac22c,1)
    assert states['after-number-stop']==states['score-320']==(0x8381f64,0x80000000,0x8dac22c,0x80000001)
    assert sha(a.negative.read_bytes())=='299446891E213CED923C80A18EC3FC90431A88C5A302F93417118B8FAE471955'
    report=dict(status='MODE11_REAL_SCORE_REEL_LIFETIME_PASS',rom_sha256=result['rom_sha256'],
                checker_sha256=sha(Path(__file__).read_bytes()),presentation_proof=sha(a.presentation.read_bytes()),
                trace_sha256=sha(raw),relative_frames=times,player_state=states,
                physical_shared_player_negative=sha(a.negative.read_bytes()),
                limits='The score song ended naturally before the reel stopped. Player0 retained that finished state across the player3 release.')
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

