"""Check only the positive palette witness ROM/opcode binding and host delta."""
import argparse,ast,hashlib,json,struct
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua
ROOT=Path(__file__).resolve().parents[1]
OLD='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
NEW='574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def rep(s,a,b):assert s.count(a)==1;return s.replace(a,b)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 wrapper=(ROOT/'tools/bizhawk_probe_iraira_palette_positive.lua').read_bytes();parent=(ROOT/'tools/bizhawk_probe_iraira_palette_witness.lua').read_bytes();combined=(ROOT/'tools/bizhawk_probe_ai_aligned_iraira.lua').read_bytes()
 assert sha(wrapper)=='9043796D65B29758EDEB21692748D97C70040C10CCFA7EC97FDF451D3F4B9681' and sha(parent)=='3535C550347DA2F291024B1DA921B817EC8F2A1E8E756B9BB4935D6D6CED0764'
 expected=rep(parent.decode(),OLD,NEW);expected=rep(expected,'0x080D0BD0,0xEB12CF8A','0x080D0BD0,0xEB32EA9A')
 marker='local source=assert(f:read("*a"));f:close()';expected=rep(expected,marker,marker+';source=bind_palette_positive_rom(source)')
 nested=rep(combined.decode(),OLD,NEW)
 setup='\n'.join('local '+k+'='+lua.quote(v) for k,v in [('wrapper',wrapper),('parent',parent),('combined',combined),('expected',expected.encode()),('nested',nested.encode())])+'\n'
 check=r'''
local captured,scope
local env=setmetatable({},{__index=_G})
env.io={open=function(path,mode)assert(path=='W:/tools/bizhawk_probe_iraira_palette_witness.lua'and mode=='rb');return{read=function()return parent end,close=function()end}end}
env.load=function(code,name,mode,context)assert(not captured);captured=code;scope=context;return function()end end
assert(load(wrapper,'@positive-delta','t',env))()
assert(captured==expected and scope.bind_palette_positive_rom(combined)==nested)
assert(not pcall(scope.bind_palette_positive_rom,nested))
'''
 runner=lua.host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+check))('','','')
 rom=(ROOT/'build/iraira-outer-palette-v86-20261117/component.gba').read_bytes();assert sha(rom)==NEW and struct.unpack_from('<I',rom,0xD0BD0)[0]==0xEB32EA9A
 host=(ROOT/'build/run_iraira_palette_positive_v86_20261117.py').read_bytes();prior=(ROOT/'build/run_iraira_palette_v84_20261117.py').read_bytes()
 assert sha(host)=='A36696E07BC2CA71DE2646B99D6EDDAA640B9135672EEF686A0EB199165B51BB' and sha(prior)=='30098F3E355A5BFAD11C39BE0E32B144B6E7332C240E7A425F3AA8DA6705520D'
 tree=ast.parse((ROOT/'build/prepare_iraira_palette_positive_host.py').read_text());pairs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pairs' for t in n.targets));assert len(pairs)==7
 back=host.decode()
 for x,y in reversed(pairs):back=rep(back,y,x)
 assert back.encode()==prior
 raw=(ROOT/'build/iraira-palette-positive-reviewed-pins-20261117.json').read_bytes();pins=json.loads(raw);oldpins=json.loads((ROOT/'build/iraira-palette-reviewed-pins-20261117.json').read_bytes())
 assert sha(raw)=='161A6ABE2131856A4D17C53437AF8FFEE18F0854ED18560BAEB01F585E91E4DD'
 assert set(pins)-set(oldpins)=={'tools/bizhawk_probe_iraira_palette_positive.lua'} and all(pins[k]==v for k,v in oldpins.items()) and all(sha((ROOT/k).read_bytes())==v for k,v in pins.items())
 result=dict(status='IRAIRA_PALETTE_POSITIVE_DELTA_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),wrapper_sha256=sha(wrapper),host_sha256=sha(host),pins_sha256=sha(raw),exact_nested_ROM_repin=True,changed_hook='080D0BD0:EB12CF8A->EB32EA9A',host_inverse_groups=7,game_actions_and_121_clock_stop_unchanged=True,actual_runtime_claim=False)
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
