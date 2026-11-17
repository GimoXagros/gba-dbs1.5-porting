"""Independent exact inverse of the positive child-contact private host."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(b): return hashlib.sha256(b).hexdigest().upper()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    old=(ROOT/'build/run_child_event_replay_20261117.py').read_bytes()
    new=(ROOT/'build/run_child_contact_positive_20261117.py').read_bytes()
    assert sha(old)=='C8EE8525013740555C7A4E2D9D7F186418493A49501D62A07E3D5C252F75DC9E'
    assert sha(new)=='1C0BCBBBAE7FED9E7E2FFF7C3E094965D9C43C659272E1278D683BD43012A2FF'
    pairs=[
      ('bizhawk-child-contact-positive-20261117-','bizhawk-child-event-replay-20261117-'),
      ('child-contact-positive-pins-20261117.json','child-event-replay-pins-20261117.json'),
      ("'tools/bizhawk_probe_child_contact_positive.lua', ",''),
      ('build/shoot-child-contact-20261117/component.gba','build/repro-v86-20261117-a/current-candidate.gba'),
      ("rom_sha = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'",
       "rom_sha = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'"),
      ("assert sha(source_rom) == '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'",
       'assert source_rom == rom_data'),
      ('--lua=W:/tools/bizhawk_probe_child_contact_positive.lua','--lua=W:/tools/bizhawk_probe_child_event_producer.lua'),
      ('source-child-contact-positive-readonly-replay','v86-healthy-child-event-producer-readonly-replay'),
      ('child-contact-done.txt','child-event-done.txt'),
      ('source-child-contact-retired','invalid-child-event-captured')]
    inverse=new.decode()
    for current,prior in pairs:
        assert inverse.count(current)==1,current
        inverse=inverse.replace(current,prior)
    assert inverse.encode()==old
    probe=(ROOT/'tools/bizhawk_probe_child_contact_positive.lua').read_bytes()
    assert sha(probe)=='D5EE2AEEB153946E74ABE43B8B386BC3AFBF5634CF32A3687EDF76B027793BD8'
    assert sha((ROOT/'tools/bizhawk_probe_child_event_producer.lua').read_bytes())=='B01A4F35A77D9CB7E24173E73C6D85818FBF8A3563B29FE55E69294EBCA7A9F9'
    result=dict(status='PASS',host_sha256=sha(new),prior_host_sha256=sha(old),inverse_groups=len(pairs),
      whole_file_inverse=True,probe_sha256=sha(probe),emulator_launched=False,
      unchanged=['private desktop and copies only','source574F/Core43B2893A/checkpoint89405/all5 RAM validation',
      'noautoload/noautosave/physical-input-off','Right2 then neutral via frozen observer','180-second host bound',
      'CPU bank/native extensions/managed suffix comparison and complete Core difference report'],
      probe_review=['all fixed-owner first/wait/release milestones required','event2 requires actual observed bus store',
      'native effect constructor exact stack/R5/R11 assertion','target/contact flags cleared before terminal milestone',
      'frame-boundary stop and snapshot/log/marker order retained'],
      limits=['Actual composed Lua fixture is separately owned by QA; no runtime claim.',
      'Full Core identity is not assumed: previous restore differed in15 serialized bytes.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result))

if __name__=='__main__': main()
