"""Read-only delta review of the private sprite diagnostic launcher; never runs it."""
import argparse,hashlib,json,sys
from pathlib import Path
from verify_gba_shoot_entry_capture_v2 import checkpoint_core,parse_checkpoint,prior
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 old=(ROOT/'build/run_gba_shoot_first_input_20261109.py').read_bytes()
 new=(ROOT/'build/run_sprite_mode_replay_20261117.py').read_bytes()
 assert sha(old)=='DDC1E38B514032299FB7CA43EBFE8E421B58E9DEFB687FF9F1862196B2FECA01'
 text=new.decode();changes=[
 ('Observe the native sprite writer from the genuine v86 healthy checkpoint.','Observe a fresh native A edge after genuine healthy Shoot activation.'),
 ('bizhawk-sprite-mode-replay-20261117-','bizhawk-gba-shoot-first-input-20261109-'),
 ('sprite-mode-replay-pins-20261117.json','gba-shoot-first-input-pins-20261109.json'),
 ('bizhawk_probe_sprite_mode_corruption.lua','bizhawk_probe_gba_shoot_first_input.lua'),
 ('build/repro-v86-20261117-a/current-candidate.gba','build/shoot-presentation-target-lifetime-20261109/component.gba'),
 ('574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76','84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'),
 ('build/bizhawk-wholeplay-v86-20261117-a','build/bizhawk-gba-shoot-entry-replay-20261109-a'),
 ("assert sha((baseline / 'launch.json').read_bytes()) == '3CB69CE4892AF21D13C42A65AB17F53160E88CAE8822C88E2E451691D78B707A'", "assert sha((root / 'build/gba-shoot-entry-replay-capture-qa-20261109/report.json').read_bytes()) == '5FF3EC35673391DF6A53462A035E28654E937DEE35688C5E9E8EB1FCDFBB225D'\nassert sha((root / 'build/gba-checkpoint-roundtrip-capture-qa-20261109/final-report.json').read_bytes()) == '6126B270F17BE65203113631195F9B36007A8FC7B71E9BA552B2F6F228D160DC'"),
 ('41-healthy-activation-','13-healthy-activation-'),
 ('43B2893A6BD9537D3D5C3FDE47C65FE12A386F76BB12B342FC4ADAE3C978E9E7','6A81B95EA208CA2842F29649F36599347A60B5627C2FA99C953A92B6F1034D93'),
 ("parsed['frame'] == 89405","parsed['frame'] == 68927"),
 ('v86-healthy-sprite-mode-writer-readonly-replay','genuine-healthy-Shoot-first-A-edge-six-frames'),
 ('sprite-replay-done.txt','first-input-done.txt'),
 ('time.monotonic() + 180','time.monotonic() + 60'),
 ('first-invalid-game-mode','six-input-frames-captured')]
 for a,b in changes:
  expected=2 if a in ('bizhawk_probe_sprite_mode_corruption.lua','41-healthy-activation-') else 1
  assert text.count(a)==expected,(a,text.count(a));text=text.replace(a,b)
 assert text.encode()==old,'complete inverse to frozen private host'
 folder=ROOT/'build/bizhawk-wholeplay-v86-20261117-a';launchb=(folder/'launch.json').read_bytes()
 assert sha(launchb)=='3CB69CE4892AF21D13C42A65AB17F53160E88CAE8822C88E2E451691D78B707A'
 launch=json.loads(launchb);names=['healthy-activation.State','healthy-activation.txt']+['41-healthy-activation-'+r+'.bin' for r in ('iwram','ewram','vram','palette','oam')]
 files={n:(folder/n).read_bytes() for n in names}
 assert all(sha(b)==launch['files'][n] for n,b in files.items())
 rom=(ROOT/'build/repro-v86-20261117-a/current-candidate.gba').read_bytes();assert sha(rom)==changes[5][0]
 assert (folder/'probe.gba').read_bytes()==rom
 meta=prior.fields(files['healthy-activation.txt'].decode().strip())
 regions={r:files['41-healthy-activation-'+r+'.bin'] for r in ('iwram','ewram','vram','palette','oam')}
 parsed=parse_checkpoint(files['healthy-activation.State'],meta,regions,rom);core,_=checkpoint_core(files['healthy-activation.State'])
 assert parsed['frame']==89405 and meta['stage7_consumed']=='true' and sha(core)==changes[9][0]
 result=dict(result='PASS',scope='static private host and exact checkpoint only; Lua policy/final run separate',host_sha256=sha(new),prior_host_sha256=sha(old),inverse_groups=len(changes),source_launch_sha256=sha(launchb),source_core_sha256=sha(core),frame=parsed['frame'],checkpoint_pins={n:sha(b) for n,b in files.items()},preserved=['PrivateDesktopProcess','fresh copied ROM/checkpoint/data paths','physical background input disabled','autoload flags false','save autosave disabled','unchanged full Core/CPU/native extension/managed suffix reporting'],not_run=True)
 args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
