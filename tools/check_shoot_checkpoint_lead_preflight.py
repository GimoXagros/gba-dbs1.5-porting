"""Independent exact delta gate for measured input lead; no emulator launch."""
import argparse, hashlib, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 old=(ROOT/'build/run_shoot_checkpoint_aim_v87_20261117.py').read_bytes()
 new=(ROOT/'build/run_shoot_checkpoint_lead_v87_20261117.py').read_bytes()
 assert sha(old)=='4E3F3959ED977595C57FB70D15C1EA108C3957813D9EB4F778BE3AF5CAEA8F68'
 assert sha(new)=='3F78FF140378F26E5CF6A715728E8EED17BB32143294554293FDBE1B7C7BA8EF'
 delta=json.loads((ROOT/'build/shoot-checkpoint-lead-host-delta-20261117.json').read_bytes())
 assert len(delta['replacements'])==5 and delta['old_sha256']==sha(old) and delta['new_sha256']==sha(new)
 inv=new.decode()
 for before,after in reversed(delta['replacements']):
  assert inv.count(after)==1;inv=inv.replace(after,before)
 assert inv.encode()==old
 pins=json.loads((ROOT/'build/shoot-checkpoint-lead-v87-pins-20261117.json').read_bytes())
 oldpins=json.loads((ROOT/'build/shoot-checkpoint-aim-v87-pins-20261117.json').read_bytes())
 wrapper='tools/bizhawk_probe_gba_shoot_checkpoint_lead_v87.lua'
 assert set(pins)==set(oldpins)|{wrapper} and all(pins[k]==v for k,v in oldpins.items())
 assert all(sha((ROOT/k).read_bytes())==v for k,v in pins.items())
 raw=(ROOT/wrapper).read_bytes();text=raw.decode().replace('\r\n','\n')
 assert sha(raw).startswith('15B146DB')
 before,after=re.findall(r'local (?:before|after)=\[=\[(.*?)\]=\]',text,re.S)
 assert before==' local horizontal=forward>=96 and forward<=384\n local vertical=dy>=128 and dy<=256'
 assert after==' local vx=signed(w(q+0x34))-signed(w(q+0x38))\n local vy=signed(w(q+0x36))-signed(w(q+0x3A))\n local lead_dx=dx+15*vx\n local lead_dy=dy+15*vy\n local lead_forward=right and lead_dx or -lead_dx\n local horizontal=lead_forward>=128 and lead_forward<=576\n local vertical=lead_dy>=-384 and lead_dy<=64'
 parent=(ROOT/'tools/bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua').read_text().replace('\r\n','\n')
 assert parent.count(before)==1
 effective=parent.replace(before,after)
 assert effective.replace(after,before)==parent
 # Bind prior independently reviewed exact host/checkpoint and all prior guards.
 previous=(ROOT/'build/shoot-checkpoint-aim-independent-20261117/host.json').read_bytes()
 assert sha(previous)=='7942F06DEE46929EF0B2B8FE0A365ADDC2B92C026759F0EFA5D1722BADC65C17'
 result=dict(status='SHOOT_CHECKPOINT_LEAD_DELTA_PREFLIGHT_PASS',host_sha256=sha(new),probe_sha256=sha(raw),tool_sha256=sha(Path(__file__).read_bytes()),host_inverse_groups=5,unchanged_parent_pin_count=5,effective_lua_sha256=sha(effective.encode()),prior_host_report_sha256=sha(previous),scope='Only input eligibility uses measured15frame linear lead. Checkpoint, ROM, sole approved HP1, owner/outcome guards, private360second host and complete Core difference reporting unchanged.',limits=['No new runtime or hit claim. Source/native timing reconstruction has adjacent-frame epoch uncertainty.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
