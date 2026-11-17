"""Static six-group inverse of the child event private replay host."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 old=(ROOT/'build/run_sprite_mode_replay_20261117.py').read_bytes();new=(ROOT/'build/run_child_event_replay_20261117.py').read_bytes()
 assert sha(old)=='A19E994876CA5E6704CDA3AEDC646D147D36BD6E54F6283A2B6FCA2FF3BBB3C8'
 text=new.decode();pairs=[('bizhawk-child-event-replay-20261117-','bizhawk-sprite-mode-replay-20261117-'),('child-event-replay-pins-20261117.json','sprite-mode-replay-pins-20261117.json'),('bizhawk_probe_child_event_producer.lua','bizhawk_probe_sprite_mode_corruption.lua'),('v86-healthy-child-event-producer-readonly-replay','v86-healthy-sprite-mode-writer-readonly-replay'),('child-event-done.txt','sprite-replay-done.txt'),('invalid-child-event-captured','first-invalid-game-mode')]
 for a,b in pairs:
  assert text.count(a)==(2 if a.startswith('bizhawk_probe') else 1);text=text.replace(a,b)
 assert text.encode()==old
 prior=(ROOT/'build/sprite-mode-replay-independent-20261117/host.json').read_bytes()
 assert sha(prior)=='18858DA52FCBA65E4F5AF40B5E1A88BA692DD02ED0553017616AE50BBDA7D5D2'
 result=dict(result='PASS',host_sha256=sha(new),prior_host_sha256=sha(old),groups=6,full_inverse=True,checkpoint_review_sha256=sha(prior),unchanged=['private desktop','all5 RAM and89405metadata checkpoint parser','sourceCore43B2893A','ROM574F','noautoload/noautosave/physicalinputoff','180secondhostbound','originalCPU/nativeextensions/managedsuffixcomparisons'],emulator_launched=False,scope='host delta; probe fixture and actual runtime are separate')
 args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
