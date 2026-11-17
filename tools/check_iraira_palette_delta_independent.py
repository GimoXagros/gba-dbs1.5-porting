"""Independent delta-only review of the read-only Iraira palette witness."""
import argparse,ast,hashlib,json,re,struct
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def rep(s,a,b):assert s.count(a)==1;return s.replace(a,b)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 wrapper=(ROOT/'tools/bizhawk_probe_iraira_palette_witness.lua').read_bytes();parent=(ROOT/'tools/bizhawk_probe_ai_aligned_iraira.lua').read_bytes()
 assert sha(wrapper)=='3535C550347DA2F291024B1DA921B817EC8F2A1E8E756B9BB4935D6D6CED0764'
 assert sha(parent)=='C32E0C08B82F5EBC805387C25990B6FC9C4C0A6056E84412D020A83266872860'
 text=wrapper.decode();assert not re.search(r'\b(?:memory|mainmemory)\.write|\b(?:joypad|savestate|client)\.|\bemu\.(?!framecount|getregisters)',text)
 expected=rep(parent.decode(),'local function attach(observer)\n','local function attach(observer)\n install_palette_probe(observer)\n')
 tail='core,value,r.R8,r.R9,r.R15,word(0x03002568),word(0x03002654))'
 expected=rep(expected,tail,tail+'\n  sample_palette_clock(#clock,core)')
 old=' return replace(source,marker,[=[ return replace(parent,marker,"  finish_ai_probe()\\n  finish_iraira_probe()\\n"..marker)]=])'
 new=' return bind_palette_finish(replace(source,marker,[=[ return replace(parent,marker,"  finish_ai_probe()\\n  finish_iraira_probe()\\n"..marker)]=]))'
 expected=rep(expected,old,new)
 ops=[(int(x,16),int(y,16)) for x,y in re.findall(r'\{(0x[0-9A-F]+),(0x[0-9A-F]+),"',text)]
 rom=(ROOT/'build/iraira-render-repair-v84-20261117/component.gba').read_bytes()
 assert sha(rom)=='3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
 assert len(ops)==20 and all(struct.unpack_from('<I',rom,x-0x08000000)[0]==y for x,y in ops)
 for part in ('ring[(serial-1)%256+1]','if not first[kind]','if index==121 then ready=true end','return stopped() or ready','byte(0x232E)==4 and byte(0x231E)==10 and byte(0x231C)==11','assert(f:close())','palette-witness-121-frames'):
  assert part in text
 setup='\n'.join('local '+k+'='+lua.quote(v) for k,v in [('wrapper',wrapper),('parent',parent),('expected',expected.encode())])+'\n'
 check=r'''
local captured,scope
local env=setmetatable({},{__index=_G})
env.userdata={get=function(k)if k=='output'then return'W:/build/palette-delta-fixture'end;assert(k=='probe_sha256');return'3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'end}
env.io={open=function(path,mode)assert(path=='W:/tools/bizhawk_probe_ai_aligned_iraira.lua'and mode=='rb');return{read=function()return parent end,close=function()end}end}
env.load=function(code,name,mode,context)assert(not captured);captured=code;scope=context;return function()end end
assert(load(wrapper,'@palette-delta','t',env))()
assert(captured==expected,'exact three parent insertions')
local marker='  local f=assert(io.open(out.."/campaign-complete-done.txt","w"));assert(f:write(outcome));f:close()'
assert(scope.finish_palette_parent(marker)==marker..'\n  finish_palette_probe(outcome)')
assert(not pcall(scope.finish_palette_parent,marker..marker))
local binding=' return replace(parent,marker,"  finish_ai_probe()\\n  finish_iraira_probe()\\n"..marker)'
local bound=' return finish_palette_parent(replace(parent,marker,"  finish_ai_probe()\\n  finish_iraira_probe()\\n"..marker))'
assert(scope.bind_palette_finish(binding)==bound)
assert(not pcall(scope.bind_palette_finish,binding..binding))
'''
 runner=lua.host.lua_check;FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+check))('','','')
 host=(ROOT/'build/run_iraira_palette_v84_20261117.py').read_bytes();prior=(ROOT/'build/run_ai_iraira_v84_20261117.py').read_bytes()
 assert sha(host)=='30098F3E355A5BFAD11C39BE0E32B144B6E7332C240E7A425F3AA8DA6705520D' and sha(prior)=='2E68861ADF5D4CC5BC9CFE404557D62F37DDCAD54EFA3227DF8A2B9460161140'
 tree=ast.parse((ROOT/'build/prepare_iraira_palette_host.py').read_text());pairs=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pairs' for t in n.targets));assert len(pairs)==7
 back=host.decode()
 for x,y in reversed(pairs):back=rep(back,y,x)
 assert back.encode()==prior
 raw=(ROOT/'build/iraira-palette-reviewed-pins-20261117.json').read_bytes();pins=json.loads(raw);oldpins=json.loads((ROOT/'build/ai-iraira-reviewed-pins-20261117.json').read_bytes())
 assert sha(raw)=='091B716B400CF054B707B490D7A059FC047AD74D8BBB9003D52BCBF66FFB2AF7'
 assert set(pins)-set(oldpins)=={'tools/bizhawk_probe_iraira_palette_witness.lua'} and all(pins[k]==v for k,v in oldpins.items())
 assert all(sha((ROOT/k).read_bytes())==v for k,v in pins.items())
 result=dict(status='IRAIRA_PALETTE_DELTA_INDEPENDENT_PASS',checker_sha256=sha(Path(__file__).read_bytes()),wrapper_sha256=sha(wrapper),host_sha256=sha(host),pins_sha256=sha(raw),native_opcode_checks=len(ops),parent_insertions=3,host_inverse_groups=7,game_actions_unchanged=True,
  bounded_journal=256,clock_samples=121,scope='Actual outer Lua composition and nested finish bindings; independent opcode/ABI and boundedness review. Author focused fixture covers event execution. No runtime outcome claim.')
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
