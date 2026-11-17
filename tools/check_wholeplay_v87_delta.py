"""Execute the sole Lua ROM rebind and invert the private full-play host."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_campaign_wholeplay_v86 as oldqa
from verify_id13_main_inventory import sha

ROOT=Path(__file__).resolve().parents[1]
OLD='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
NEW='5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    old=(ROOT/'tools/bizhawk_probe_campaign_wholeplay_v86.lua').read_bytes()
    wrapper=(ROOT/'tools/bizhawk_probe_campaign_wholeplay_v87.lua').read_bytes()
    assert sha(old)==oldqa.PIN=='66B9BB23039FDF1B7441559990E5FBCF227DF66F5026820F5A06DB1E45B27594'
    assert sha(wrapper)=='D1A8096A746FB1DE249DA568B58F6370750C537FC5FEFFACA2AD026334FB1B6C'
    assert old.count(OLD.encode())==1
    expected=old.replace(OLD.encode(),NEW.encode())
    quote=oldqa.base.campaign.quote
    check='local original='+quote(old)+'\nlocal expected='+quote(expected)+'\nlocal wrapper='+quote(wrapper)+r'''
local native_load=load
local reads,closes,loaded,called=0,0,0,0
io.open=function(path,mode)
 assert(path=='W:/tools/bizhawk_probe_campaign_wholeplay_v86.lua' and mode=='rb')
 reads=reads+1
 return {read=function(self,kind)assert(kind=='*a');return original end,
 close=function()closes=closes+1;return true end}
end
load=function(code,name,mode,env)
 assert(code==expected and name=='@wholeplay-v87-ROM-binding' and mode=='t' and env==_ENV)
 loaded=loaded+1
 return function()called=called+1 end
end
assert(native_load(wrapper,'@actual-v87-wrapper','t',_ENV))()
assert(reads==1 and closes==1 and loaded==1 and called==1)
'''
    run=oldqa.base.campaign.host.lua_check
    FunctionType(run.__code__,dict(run.__globals__,CHECK=check))('','','')
    priorqa=(ROOT/'build/campaign-wholeplay-v86-qa-20261117/lua.json').read_bytes()
    assert sha(priorqa)=='8EE4B80B7F6EA925DD03911A413226F9E8DBCC6CE530A2183E63FFD9608CF69B'
    pinsraw=(ROOT/'build/wholeplay-v87-reviewed-pins-20261117.json').read_bytes();pins=json.loads(pinsraw)
    oldpins=json.loads((ROOT/'build/wholeplay-v86-reviewed-pins-20261117.json').read_bytes())
    assert set(pins)-set(oldpins)=={'tools/bizhawk_probe_campaign_wholeplay_v87.lua'}
    assert all(pins[k]==v for k,v in oldpins.items())
    for path,pin in pins.items():assert sha((ROOT/path).read_bytes())==pin,path
    indexed={int(x,16):int(y,16) for x,y in re.findall(rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})',old)}
    indexed|={0x085CD340:0xE92D5FFF,0x085CD740:0xE92D5FFF};assert len(indexed)==25
    allhooks=oldqa.base.ai.HOOKS|oldqa.base.provenance.HOOKS|oldqa.base.aligned.IR_OPCODES|indexed
    rom=(ROOT/'build/shoot-child-contact-20261117/component.gba').read_bytes();assert sha(rom)==NEW
    assert all(struct.unpack_from('<I',rom,x-0x08000000)[0]==y for x,y in allhooks.items())
    previous=(ROOT/'build/run_wholeplay_v86_20261117.py').read_bytes()
    host=(ROOT/'build/run_wholeplay_v87_20261117.py').read_bytes()
    assert sha(previous)=='A4C65697CB6DF2005497B553E6D7537778ABAB2D95D04EB5D39A4B9BE7AE0630'
    assert sha(host)=='10CB937D3B02C78DF6D9D4B63C7AB51439FA8DA8F201C0A27B438FB5EB2EE1A1'
    inverse=host.decode()
    pairs=[('bizhawk-wholeplay-v87-20261117-','bizhawk-wholeplay-v86-20261117-'),
      ('wholeplay-v87-reviewed-pins-20261117.json','wholeplay-v86-reviewed-pins-20261117.json'),
      ("    'tools/bizhawk_probe_campaign_wholeplay_v87.lua',\r\n",''),
      ('build/shoot-child-contact-20261117/component.gba','build/repro-v86-20261117-a/current-candidate.gba'),
      (NEW,OLD),('--lua=W:/tools/bizhawk_probe_campaign_wholeplay_v87.lua','--lua=W:/tools/bizhawk_probe_campaign_wholeplay_v86.lua'),
      ('assisted-v87-full-campaign-shoot-terminal-title','assisted-v86-full-campaign-shoot-terminal-title'),
      ("    'tools/bizhawk_probe_campaign_wholeplay_v86.lua',\n", "    'tools/bizhawk_probe_campaign_wholeplay_v86.lua',\r\n")]
    for new,oldtext in pairs:
        assert inverse.count(new)==1,new
        inverse=inverse.replace(new,oldtext)
    assert inverse.encode()==previous
    result=dict(status='WHOLEPLAY_V87_DELTA_PASS',wrapper_sha256=sha(wrapper),host_sha256=sha(host),
      reviewed_pins_sha256=sha(pinsraw),component_sha256=NEW,actual_Lua_single_ROM_rebind=True,
      effective_wrapper_sha256=sha(expected),prior_fixture_sha256=sha(priorqa),prior_six_cases_rerun=False,
      whole_host_inverse_groups=len(pairs),wholeplay_hook_words=25,total_nested_hook_words=len(allhooks),
      unchanged=['entire effective observer except ROM identity','all controls/authorized score and HP writes',
      'actual lethal-hit and ending/mode20/title completion guards','private desktop/no autoload/no save/no physical input',
      '120000-frame and1800-second bounds'],emulator_launched=False)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result))

if __name__=='__main__':main()
