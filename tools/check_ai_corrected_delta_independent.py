"""Narrow corrected AI wrapper composition and host inverse; no emulator."""
import argparse,ast,hashlib,json,re
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua
ROOT=Path(__file__).resolve().parents[1]
OLD='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
NEW='DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def replace(s,a,b):assert s.count(a)==1;return s.replace(a,b)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 wrapper=(ROOT/'tools/bizhawk_probe_ai_corrected_campaign.lua').read_bytes();prior=(ROOT/'tools/bizhawk_probe_ai_producer_provenance.lua').read_bytes();nested=(ROOT/'tools/bizhawk_probe_type8_corrected_campaign.lua').read_bytes()
 assert sha(wrapper)=='45490F604352C49539A73E54A9F7AE9FF1A2DDDDA8508A1C4BA28372B45085A4'
 assert sha(prior)=='4A2AE9672BAF2C1BC53EE3B8A6F891DCB66B7EE77C0163966CA2F123F15C4C30'
 assert sha(nested)=='844C896950AFFDB42B255CB843AEE8F2354A61237E0997506D0A74EAC81B00EC'
 assert not re.search(rb'\b(?:memory|mainmemory)\.write|\b(?:joypad|savestate|client)\.|\bemu\.(?!framecount|getregisters)',wrapper)
 expected=replace(prior.decode(),OLD,NEW)
 load='local source=assert(f:read("*a"));f:close()'
 expected=replace(expected,load,load+';source=bind_corrected_ai_rom(source)')
 loadfact='rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4)))'
 expected=replace(expected,loadfact,'rd(OWNER,2),r.R5,r.R8,addr,rd(addr,4)),true)')
 expected=replace(expected,'record("target",r,detail)','record("target",r,detail,true)')
 ledger='address,rd(OWNER,2),value&65535,flags),(value&65535)==15)'
 extra='''
   local r=emu.getregisters()
   if not init["action-first-copy"] and r.R14==0x080C69B8 and r.R5==OWNER then
    local src=r.R4-2
    record("action-first-copy",r,string.format("src=%08X ordinal=%04X word=%04X bank=%04X rng=%04X action18=%s",
     src,rd(0x03003D68,2),value&65535,rd(0x03004D92,2),rd(0x03004DB2,2),bytes(src,18)),true)
   end
'''
 expected=replace(expected,ledger,ledger+extra)
 setup='\n'.join('local '+n+'='+lua.quote(v) for n,v in [('wrapper',wrapper),('prior',prior),('nested',nested),('expected',expected.encode()),('nested_expected',replace(nested.decode(),OLD,NEW).encode())])+'\n'
 check=r'''
local captured,scope
local env=setmetatable({},{__index=_G})
env.io={open=function(path,mode)
 assert(path=='W:/tools/bizhawk_probe_ai_producer_provenance.lua' and mode=='rb')
 return{read=function()return prior end,close=function()end}
end}
env.load=function(code,name,mode,context)
 assert(not captured and name=='@frozen-ai-provenance-corrected-rom' and mode=='t')
 captured=code;scope=context;return function()end
end
assert(load(wrapper,'@corrected-ai-delta','t',env))()
assert(captured==expected,'exact five permitted deltas')
assert(scope.bind_corrected_ai_rom(nested)==nested_expected,'nested844C ROM pin reaches F393 binding')
assert(not pcall(scope.bind_corrected_ai_rom,nested_expected),'unique fail-closed source pin')
'''
 runner=lua.host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+check))('','','')
 host=(ROOT/'build/run_ai_corrected_v82_20261117.py').read_bytes();oldhost=(ROOT/'build/run_ai_provenance_v82_20261117.py').read_bytes()
 assert sha(host)=='F1397304FFEF2CEAAACC4DECEE774CE442A5317FAF101BA0A56F0B70C110706D'
 assert sha(oldhost)=='BBB6960EB4C55A927946F190399BFD947695B64A830BA3C149769BC653531FC3'
 prep=ast.parse((ROOT/'build/prepare_ai_corrected_host.py').read_text())
 pairs=next(ast.literal_eval(n.value) for n in prep.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pairs' for t in n.targets))
 assert len(pairs)==8
 inverse=host.decode()
 for x,y in reversed(pairs):inverse=replace(inverse,y,x)
 assert inverse.encode()==oldhost
 rawpins=(ROOT/'build/ai-corrected-reviewed-pins-20261117.json').read_bytes();pins=json.loads(rawpins)
 assert sha(rawpins)=='D7A7625DBEFBD84ACDE7C15F6AE41AF8557659A5A0CE862542943DB873660D7A'
 priorpins=json.loads((ROOT/'build/ai-provenance-reviewed-pins-20261117.json').read_bytes())
 assert set(pins)-set(priorpins)=={'tools/bizhawk_probe_ai_corrected_campaign.lua'}
 assert all(pins[k]==v for k,v in priorpins.items())
 assert all(sha((ROOT/k).read_bytes())==v for k,v in pins.items())
 result=dict(status='AI_CORRECTED_DELTA_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),wrapper_sha256=sha(wrapper),
  host_sha256=sha(host),pins_sha256=sha(rawpins),exact_wrapper_delta_groups=5,host_inverse_groups=8,nested_rom_binding=True,
  input_and_guest_write_paths_unchanged=True,hook_opcodes_and_target_guards_unchanged=True,first_facts_bounded=True,
  actual_runtime_evidence=False,limitations=['Delta-only review builds on frozen4A2 and844C gates; no prior full Lua suites repeated.'])
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
