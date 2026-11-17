"""Execute only the corrected observer delta; reuse the frozen E999/F393 gates."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from types import FunctionType
import check_campaign_complete_probe as lua

ROOT=Path(__file__).resolve().parents[1]
OLD='933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
NEW='75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
PINS={'bizhawk_probe_type8_corrected_campaign.lua':'844C896950AFFDB42B255CB843AEE8F2354A61237E0997506D0A74EAC81B00EC',
      'bizhawk_probe_type8_event_provenance.lua':'E999477CB5D5A72E64B46DCC6F24838BF4D2447B221A3E018DB88B15BC467523',
      'bizhawk_probe_campaign_complete.lua':'F3932EC9C0215CBEF8BA8D0C2A583506DE899090EE39EBF30B69AFC155DEC9DF'}
CHECK=r'''
local frame,r,ram,hooks,files,captured=8666,{},{},{},{},nil
local q,p=0x02011828,0x02011710
ram[0x03002310]=7;ram[0x0300231E]=8;ram[0x0300489C]=p;ram[0x030048A0]=q
ram[p-8]=2;ram[q-8]=2;ram[q+0x10]=1;ram[q+0x11]=13;ram[q+0x18]=p;ram[p+0x18]=q;ram[q+4]=1
ram[0x03004D26]=1
for i=0,15 do r['R'..i]=0 end;r.R4=q;r.CPSR=0
local env=setmetatable({},{__index=_G})
local function forbidden(_,key)error('forbidden API '..tostring(key))end
env.userdata={get=function(k)if k=='output'then return 'W:/build/type8-delta-fixture'end;assert(k=='probe_sha256');return newhash end}
env.emu=setmetatable({framecount=function()return frame end,getregisters=function()return r end},{__index=forbidden})
env.event={on_bus_exec=function(fn,at,name)assert(not hooks[at] and opcodes[at]);hooks[at]=fn end}
local bases={EWRAM=0x02000000,IWRAM=0x03000000,ROM=0x08000000}
local function rd(a,d)return ram[a+bases[d]]or opcodes[a+bases[d]]or 0 end
env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd},{__index=forbidden})
env.mainmemory=setmetatable({},{__index=forbidden});env.joypad=setmetatable({},{__index=forbidden})
env.client=setmetatable({},{__index=forbidden});env.savestate=setmetatable({},{__index=forbidden})
env.io={open=function(path,mode)
 if mode=='rb'then assert(sources[path]);return{read=function()return sources[path]end,close=function()end}end
 assert(mode=='wb'and path=='W:/build/type8-delta-fixture/type8-event-provenance.txt'and not files[path])
 local f={text='',closed=false};files[path]=f
 function f:write(s)assert(not self.closed);self.text=self.text..s;return true end
 function f:close()assert(not self.closed);self.closed=true;return true end
 return f
end}
local function replace(s,old,new)
 local a,b=assert(s:find(old,1,true));assert(not s:find(old,b+1,true));return s:sub(1,a-1)..new..s:sub(b+1)
end
local old=sources['W:/tools/bizhawk_probe_type8_event_provenance.lua']
local want=replace(old,oldhash,newhash)
local ring='local ring,counts,serial,closed={}, {},0,false'
want=replace(want,ring,ring..'\n'..[=[local first_window,first_chain={},{}
local chain_candidate,chain_core,chain_record
]=])
local ending='r.R0,r.R1,r.R3,r.R4,r.R5,r.R8,r.R14,r.R15,r.CPSR,detail)'
want=replace(want,ending,ending..'\n'..[=[ local core,line=emu.framecount(),ring[(serial-1)%256+1]
 if core>=8667 and core<=8673 and #first_window<256 then
  first_window[#first_window+1]=line
 end
 if #first_chain==0 then
  if kind=="type8-air-selector" and (r.CPSR&0x40000000)==0 then
   chain_candidate,chain_core,chain_record={line},core,false
  elseif chain_candidate and core<=chain_core+1 and #chain_candidate<32 then
   chain_candidate[#chain_candidate+1]=line
   if kind=="damage-record-selected" then
    local subtype=rd(0x03004D26,1)
    chain_record=subtype>=0 and subtype<4 and r.R1==0x0836C2AC+subtype*32
   end
   if kind=="event-store" and chain_record and r.R3==0x16 then first_chain=chain_candidate end
  end
 end
]=])
local save=[=[ for n=math.max(1,serial-255),serial do assert(file:write(ring[(n-1)%256+1].."\n"))end]=]
want=replace(want,save,[=[ assert(file:write(string.format("first-window frames=8667..8673 count=%d\n",#first_window)))
 for _,line in ipairs(first_window)do assert(file:write("first "..line.."\n"))end
 assert(file:write(string.format("first-chain count=%d\n",#first_chain)))
 for _,line in ipairs(first_chain)do assert(file:write("chain "..line.."\n"))end
]=]..save)
local parent_read='local source=assert(f:read("*a"));f:close()'
want=replace(want,parent_read,parent_read..';source=corrected_campaign_parent(source)')
env.load=function(code,name,mode,context)
 assert(mode=='t')
 if name=='@frozen-provenance-corrected-rom'then
  assert(code==want,'only reviewed provenance delta');return assert(load(code,name,mode,context))
 end
 assert(name=='@frozen-campaign-with-readonly-provenance'and not captured)
 local parent=sources['W:/tools/bizhawk_probe_campaign_complete.lua']
 parent=replace(replace(parent,oldhash,newhash),'  log:close()','  log:close();finish_provenance()')
 assert(code==parent,'unchanged F393 actions and guards, exact ROM/close substitutions')
 captured=context;return function()end
end
assert(load(sources['W:/tools/bizhawk_probe_type8_corrected_campaign.lua'],'@review','t',env))()
local n=0;for _ in pairs(hooks)do n=n+1 end;assert(n==8 and captured)
local function fire(at)hooks[0x083525C4]()end
fire();frame=8667;fire();frame=8673;for _=1,300 do fire()end
frame=8674;for _=1,300 do fire()end
local sp=0x03007E80
local function selector(core,z)
 frame=core;r.R5=q;r.CPSR=z and 0x40000000 or 0;hooks[0x0836EC90]()
end
local function selected(address)
 r.R5=q;r.R1=address;hooks[0x0836F3CC]()
end
local function store()
 r.R5=q+0xAC;r.R3=0x16;r.R4=0x0861CF0C;r.R13=sp
 hooks[0x08012884]();r.R4=q
end
selector(9000,true);selected(0x0836C2CC);store()
selector(9100,false);selected(0x0836C32C);store()
selector(9200,false);selected(0x0836C2CC);frame=9202;store()
selector(9300,false);for _=1,33 do fire()end;selected(0x0836C2CC);store()
selector(9400,false)
r.R1=0x08D3FE90;hooks[0x0836F3B8]()
selected(0x0836C2CC)
r.R4=q;r.R5=q+0xAC;hooks[0x083555D0]()
ram[sp]=0x16;ram[sp+8]=q+0xAC;r.R13=sp;hooks[0x08012874]()
store()
frame=9500;for _=1,300 do fire()end
captured.finish_provenance()
local f=files['W:/build/type8-delta-fixture/type8-event-provenance.txt']
assert(f.closed and f.text:find('summary serial=953 core=9500',1,true))
assert(f.text:find('first-window frames=8667..8673 count=256',1,true))
assert(f.text:find('first-chain count=6',1,true))
local first,tail,chain={},{},{}
for line in f.text:gmatch('[^\n]+')do
 if line:find('^first seq=')then first[#first+1]=line
 elseif line:find('^chain seq=')then chain[#chain+1]=line
 elseif line:find('^seq=')then tail[#tail+1]=line end
end
assert(#first==256 and #tail==256)
assert(first[1]:find('^first seq=2 core=8667 ')and first[256]:find('^first seq=257 core=8673 '))
assert(tail[1]:find('^seq=698 core=9500 ')and tail[256]:find('^seq=953 core=9500 '))
assert(#chain==6 and chain[1]:find('^chain seq=648 core=9400 ')and chain[6]:find('^chain seq=653 core=9400 '))
hooks[0x083525C4]();assert(not pcall(captured.finish_provenance),'close exactly once')
'''

def sha(b):return hashlib.sha256(b).hexdigest().upper()

def host_delta():
 old=(ROOT/'build/run_campaign_complete_v80_20261117.py').read_bytes()
 new=(ROOT/'build/run_type8_corrected_v81_20261117.py').read_bytes()
 assert sha(old)=='1E18406F7CAC6A8112585FB0839A528CE785BC1B4A35920BAFC528619FEA738B'
 assert sha(new)=='18DDDFCFE48DD615B6F64A2B46755D270831428FE951B72A2859CCB747366864'
 changes=[('bizhawk-campaign-complete-v80-20261117-[a-z]','bizhawk-type8-corrected-v81-20261117-[a-z]'),
          ('build/campaign-complete-reviewed-pins-20261117.json','build/type8-corrected-reviewed-pins-20261117.json'),
          ("    'tools/bizhawk_probe_campaign_complete.lua',","    'tools/bizhawk_probe_campaign_complete.lua',\r\n    'tools/bizhawk_probe_type8_event_provenance.lua',\r\n    'tools/bizhawk_probe_type8_corrected_campaign.lua',"),
          ('build/campaign-stage-progression-v80-20261117-r2/component.gba','build/character-type8-tables-r2-20261117/component.gba'),
          (OLD,NEW),('--lua=W:/tools/bizhawk_probe_campaign_complete.lua','--lua=W:/tools/bizhawk_probe_type8_corrected_campaign.lua'),
          ("phase_kind='assisted-source-eleven-encounter-to-healthy-shoot'","phase_kind='type8-corrected-assisted-eleven-encounter-to-healthy-shoot'")]
 inverse=new
 for before,after in reversed(changes):
  assert inverse.count(after.encode())==1;inverse=inverse.replace(after.encode(),before.encode())
 assert inverse==old,'all host input, write authorization, failures, bounds and visibility retained'
 pins=(ROOT/'build/type8-corrected-reviewed-pins-20261117.json').read_bytes()
 assert sha(pins)=='0126D44047D3AD655DA84C34E3DF75CBC33360CAD5B3450CE335B57AAD0DCD2B'
 actual=json.loads(pins);base=json.loads((ROOT/'build/campaign-complete-reviewed-pins-20261117.json').read_bytes())
 assert actual==base|{'tools/'+n:PINS[n]for n in ('bizhawk_probe_type8_corrected_campaign.lua','bizhawk_probe_type8_event_provenance.lua')}
 assert all(sha((ROOT/n).read_bytes())==digest for n,digest in actual.items())
 return dict(host_sha256=sha(new),reviewed_pins_sha256=sha(pins),exact_seven_group_host_inverse=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 assert not a.report.exists()
 sources={n:(ROOT/'tools'/n).read_bytes()for n in PINS}
 assert {n:sha(b)for n,b in sources.items()}==PINS
 assert not re.search(rb'\b(?:memory|mainmemory|joypad|client|savestate)\.|emu\.(?!framecount)',sources['bizhawk_probe_type8_corrected_campaign.lua'])
 parent=sources['bizhawk_probe_type8_event_provenance.lua']
 opcodes={int(x,16):int(y,16)for x,y in re.findall(rb'hook\(0x([0-9A-F]+),0x([0-9A-F]+),',parent)}
 rom=(ROOT/'build/character-type8-tables-r2-20261117/component.gba').read_bytes();assert sha(rom)==NEW
 assert all(struct.unpack_from('<I',rom,at-0x08000000)[0]==op for at,op in opcodes.items())
 setup='local sources={'+','.join('['+lua.quote(('W:/tools/'+n).encode())+']='+lua.quote(b)for n,b in sources.items())+'}\n'
 setup+='local opcodes={'+','.join(f'[{at}]={op}'for at,op in opcodes.items())+'}\n'
 setup+=f'local oldhash="{OLD}";local newhash="{NEW}"\n'
 runner=lua.host.lua_check
 FunctionType(runner.__code__,dict(runner.__globals__,CHECK=setup+CHECK))('','','')
 host=host_delta()
 result=dict(status='TYPE8_CORRECTED_DELTA_INDEPENDENT_PASS',pins=PINS,rom_sha256=NEW,
             exact_effective_E999_delta=True,exact_F393_ROM_and_close_substitutions=True,guest_writes_added=0,input_calls_added=0,
             first_window_frames=[8667,8673],first_window_capacity=256,retained_first_rows=256,retained_tail_rows=256,
             exercised_journal_events=953,retained_causal_chain_rows=6,causal_chain_rejections=['condition false','wrong record','expired candidate','32-row overflow'],
             causal_chain_positive_subtype=1,actual_gameplay=False,prior_full_suites_repeated=False,checker_sha256=sha(Path(__file__).read_bytes()),**host)
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
