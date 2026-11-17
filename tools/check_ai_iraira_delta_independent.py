"""Delta-only combined observer composition, opcodes and exact host inverse."""
import argparse,ast,hashlib,json,re,struct
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua
ROOT=Path(__file__).resolve().parents[1]
ROM='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
OLD='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def rep(s,a,b):assert s.count(a)==1;return s.replace(a,b)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 wrapper=(ROOT/'tools/bizhawk_probe_ai_aligned_iraira.lua').read_bytes();parent=(ROOT/'tools/bizhawk_probe_ai_corrected_campaign.lua').read_bytes();ai=(ROOT/'tools/bizhawk_probe_ai_producer_provenance.lua').read_bytes()
 assert sha(wrapper)=='C32E0C08B82F5EBC805387C25990B6FC9C4C0A6056E84412D020A83266872860'
 assert sha(parent)=='45490F604352C49539A73E54A9F7AE9FF1A2DDDDA8508A1C4BA28372B45085A4' and sha(ai)=='4A2AE9672BAF2C1BC53EE3B8A6F891DCB66B7EE77C0163966CA2F123F15C4C30'
 assert not re.search(rb'\b(?:memory|mainmemory)\.write|\b(?:joypad|savestate|client)\.|\bemu\.(?!framecount|getregisters)',wrapper)
 expected=rep(parent.decode(),OLD,ROM)
 expected=rep(expected,'local source=assert(f:read("*a"));f:close()\nsource=replace(source,OLD,NEW)','local source=assert(f:read("*a"));f:close()\nsource=extend_iraira_ai(source)\nsource=replace(source,OLD,NEW)')
 extended=rep(ai.decode(),' parent=replace(parent,binding,binding.."\\n attach_ai_probe(observer)")',' parent=replace(parent,binding,binding.."\\n attach_ai_probe(observer)\\n attach_iraira_probe(observer)")')
 extended=rep(extended,' return replace(parent,marker,"  finish_ai_probe()\\n"..marker)',' return replace(parent,marker,"  finish_ai_probe()\\n  finish_iraira_probe()\\n"..marker)')
 rom=(ROOT/'build/iraira-render-repair-v84-20261117/component.gba').read_bytes();assert sha(rom)==ROM
 ops={0x0837501C:0xE59F8150,0x08375018:0xE1C890B0,0x08D8AF8C:0xE1C100B0,0x086283A4:0xE1C010B0,0x086283AC:0xE1C320B0}
 assert all(struct.unpack_from('<I',rom,k-0x08000000)[0]==v for k,v in ops.items())
 text=wrapper.decode()
 for fragment in ('if #phases<32 then','if #clock==121 or not scoped() or not observer.live() then return end','r.R8~=0x03004500 or (r.R9&65535)~=value or value>=7200','core~=last_core+1 or value~=last_clock-1','[0x08D8AF94]="init-clear",[0x086283B4]="display-toggle"'):
  assert fragment in text
 assert text.count('event.on_bus_exec(')==1 and text.count('event.on_bus_write(')==1
 setup='\n'.join('local '+k+'='+lua.quote(v) for k,v in [('wrapper',wrapper),('parent',parent),('ai',ai),('expected',expected.encode()),('extended',extended.encode())])+'\nlocal romhash="'+ROM+'"\n'
 check=r'''
local captured,scope
local env=setmetatable({},{__index=_G})
env.userdata={get=function(k)if k=='output'then return'W:/build/iraira-delta-fixture'end;assert(k=='probe_sha256');return romhash end}
env.io={open=function(path,mode)assert(path=='W:/tools/bizhawk_probe_ai_corrected_campaign.lua'and mode=='rb');return{read=function()return parent end,close=function()end}end}
env.load=function(code,name,mode,context)assert(not captured);captured=code;scope=context;return function()end end
assert(load(wrapper,'@combined-delta','t',env))()
assert(captured==expected and scope.extend_iraira_ai(ai)==extended,'exact nested source insertion delta')
assert(not pcall(scope.extend_iraira_ai,extended),'fail-closed repeat adaptation')
'''
 runner=lua.host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+check))('','','')
 host=(ROOT/'build/run_ai_iraira_v84_20261117.py').read_bytes();prior=(ROOT/'build/run_ai_corrected_v82_20261117.py').read_bytes()
 assert sha(host)=='2E68861ADF5D4CC5BC9CFE404557D62F37DDCAD54EFA3227DF8A2B9460161140' and sha(prior)=='F1397304FFEF2CEAAACC4DECEE774CE442A5317FAF101BA0A56F0B70C110706D'
 tree=ast.parse((ROOT/'build/prepare_ai_iraira_host.py').read_text());pairs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pairs' for t in n.targets));assert len(pairs)==7
 back=host.decode()
 for x,y in reversed(pairs):back=rep(back,y,x)
 assert back.encode()==prior
 raw=(ROOT/'build/ai-iraira-reviewed-pins-20261117.json').read_bytes();pins=json.loads(raw)
 assert sha(raw)=='56E388FF5987CF82CBE019C21C82197AE2228AD9C3DA50F1865BF5CCCF6E67D0'
 oldpins=json.loads((ROOT/'build/ai-corrected-reviewed-pins-20261117.json').read_bytes());assert set(pins)-set(oldpins)=={'tools/bizhawk_probe_ai_aligned_iraira.lua'}
 assert all(pins[k]==v for k,v in oldpins.items()) and all(sha((ROOT/k).read_bytes())==v for k,v in pins.items())
 result=dict(status='AI_IRAIRA_OBSERVER_DELTA_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),wrapper_sha256=sha(wrapper),host_sha256=sha(host),pins_sha256=sha(raw),host_inverse_groups=7,
  added_exec_hooks=1,added_write_hooks=1,phase_bound=32,clock_streak_bound=121,exact_nested_composition=True,
  game_actions_unchanged=True,actual_runtime_evidence=False,scope='Actual outer Lua composition plus opcode/boundedness code review; author A1F11727 covers clock/phase mock cases, old suites not repeated.')
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
