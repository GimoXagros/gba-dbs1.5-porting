"""Execute the new ID14 composition and affected policy under Lua54; no emulator."""
import argparse,hashlib,json,re,struct,types
from pathlib import Path
import verify_wsc_shoot_short_hard as host
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
quote=lambda b:'"'+''.join('\\'+f'{v:03d}'for v in b)+'"'
PINS={
 'bizhawk_probe_evolution_music_three.lua':'B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881',
 'bizhawk_probe_evolution_music_6c_approach.lua':'404A0A087F852BCF3634963F3229F1F72A8DED463783E85E2B8EA760C1E11338',
 'bizhawk_probe_result_music_lifetime.lua':'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
 'bizhawk_probe_result_languages.lua':'928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
 'bizhawk_observe_evolution_event_queue.lua':'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
 'bizhawk_observe_collision_alignment.lua':'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C'}
TEST=r'''
for _,case in ipairs({'normal','alias','e5','wrong-song'})do
 local files,hooks,ram={},{},{};for k,v in pairs(scalars)do ram[k]=v end
 local regs={};for n=0,15 do regs['R'..n]=0 end
 local frame=101;local env=setmetatable({},{__index=_G});local captured,composed_env
 local domains={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[assert(domains[d])+a]or 0 end
 env.userdata={get=function(k)if k=='target_song'then return case=='wrong-song'and 109 or 108 end;assert(k=='output');return'W:/build/id14-author'end}
 env.memory=setmetatable({getmemorydomainsize=function()return 0x1000000 end,read_u8=rd,read_u16_le=rd,read_u32_le=rd,read_bytes_as_binary_string=function(_,n)return string.rep('\0',n)end},{__index=function(_,k)error('forbidden memory API '..k)end})
 env.emu={framecount=function()return frame end,getregisters=function()return regs end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 env.io={open=function(path,mode)
  if mode=='rb'then local s=assert(sources[path]);return{read=function()return s end,close=function()end}end
  assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()self.closed=true end
  return f
 end}
 env.load=function(s,n,m,e)
  if n=='@reviewed-evolution-music-pause'then assert(load(s,n,m,e));captured=s;composed_env=e;return function()end end
  return load(s,n,m,e)
 end
 local ok,err=pcall(function()assert(load(wrapper_source,'@ID14','t',env))()end)
 if case=='wrong-song'then assert(not ok and not next(files));goto next_case end
 assert(ok,err);assert(captured)
 assert(captured:find('music_lifetime_finish()\nid14_evidence_finish()\nlocal f=',1,true))
 local at=assert(captured:find('-- Ordinary-input Options commit',1,true));local prefix=captured:sub(1,at-1)
 env.RAM=ram;env.REGS=regs;env.HOOKS=hooks;env.CASE=case
 local exercise=[[
 RAM[0x03004740]=12;RAM[0x0300473C]=0;RAM[0x0300473E]=0
 assert(music_selection()=='Down'and chosen==14)
 RAM[0x0300473C]=12;RAM[0x0300473E]=12;assert(music_selection()=='A')
 local p,q,cal=0x02011710,0x02011828,0x02011940
 RAM[p-8]=2;RAM[q-8]=2;RAM[p+0x10]=0;RAM[q+0x10]=1;RAM[p+0x11]=14;RAM[q+0x11]=1
 RAM[p+0x14]=p;RAM[p+0x18]=q;RAM[q+0x18]=p;RAM[0x0300489C]=p;RAM[0x030048A0]=q
 RAM[p+0x34]=0x1000;RAM[p+0x36]=0x1000
 local keys={A=true,Right=true};music_contact(keys,'battle',7);assert(keys.Left and not keys.Right and not keys.A)
 RAM[p+0x34]=0x600;music_contact(keys,'battle',7);assert(not keys.Left)
 RAM[0x03004CE8]=cal;RAM[cal-8]=2;RAM[cal+4]=0x1008;RAM[cal+0x10]=2;RAM[cal+0x34]=0x1000;RAM[cal+0x36]=0x1000
 music_contact(keys,'battle',7);assert(keys.Right and not keys.Left)
 stage_verified=100;stage_id=0x10;stage_header=music_read(0x08D33080,4)
 RAM[0x03004E98]=stage_id;RAM[0x03006B40]=stage_header
 REGS.R4=p;REGS.R13=0x03007F00;RAM[REGS.R13]=5;RAM[p+0x11]=5
 music_pause_observe('evolution-selector',REGS);assert(not pause.actor)
 RAM[REGS.R13]=14;RAM[p+0x11]=14;RAM[p+0x10]=1
 music_pause_observe('evolution-selector',REGS);assert(not pause.actor)
 RAM[p+0x10]=0;music_pause_observe('evolution-selector',REGS);assert(pause.actor==p and pause.identity==14 and pause.side==0)
 if CASE=='alias'then
  local ok,err=pcall(HOOKS[0x03000D0C]);assert(not ok and err:find('copied-cache-branch-executed',1,true))
 elseif CASE=='e5'then
  RAM[0x03004D20]=0xE5;local ok,err=pcall(HOOKS[0x0836EB58]);assert(not ok and err:find('observed-collision-e5',1,true))
 else music_lifetime_finish();id14_evidence_finish()end
 ]]
 assert(load(prefix..exercise,'@ID14-policy','t',composed_env))()
 local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==25)
 for _,name in ipairs({'music-lifetime.txt','evolution-event-queue.txt','collision-alignment.txt'})do assert(files['W:/build/id14-author/'..name].closed)end
 if case~='normal'then local marker=assert(files['W:/build/id14-author/result-done.txt']);assert(marker.closed and marker.data==(case=='alias'and'failure:copied-cache-branch-executed'or'failure:observed-collision-e5'))end
 ::next_case::
end
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 wrapper=(ROOT/'tools/bizhawk_probe_evolution_id14.lua').read_bytes()
 sources={name:(ROOT/'tools'/name).read_bytes()for name in PINS}
 assert all(sha(sources[n])==v for n,v in PINS.items())
 assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister',wrapper)
 rom=(ROOT/'build/impmon-evolution-clean15-20261116/component.gba').read_bytes()
 assert sha(rom)=='8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
 sites=[0x37B458,0xD7DFC0,0xD7DFC8,0x37FBB4,0xD14A8,0x35A1EC,0x35A558,0x12BA8,0xD15D0,0xD157C,0x36E37C,0x36E380,0x36EB58,0x36EBA4]+[0xD33000+i*8+j for i in(0x10,0x6C,0x6D,0x6E,0x6F)for j in(0,4)]
 values={0x08000000+x:struct.unpack_from('<I',rom,x)[0]for x in sites};cat=values[0x080D14A8]
 values.update({cat+i:rom[cat-0x08000000+i]for i in range(16)})
 values.update({0x08628000+i:struct.unpack_from('<H',rom,0x628000+i)[0]for i in range(0,128,2)})
 check='local scalars={'+','.join(f'[{k}]={v}'for k,v in values.items())+'}\nlocal sources={'+','.join('['+quote(('W:/tools/'+n).encode())+']='+quote(b)for n,b in sources.items())+'}\n'+TEST
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=check),argdefs=host.lua_check.__defaults__)
 fn(wrapper.decode(),'','')
 report=dict(status='ID14_ORDINARY_CONTACT_AUTHOR_PASS',wrapper_sha256=sha(wrapper),checker_sha256=sha(Path(__file__).read_bytes()),dependency_pins=PINS,actual_Lua54_cases=4,
  menu_identity=14,target_song=108,side=0,guest_writes=False,total_frame_limit=24000,post_target_frame_limit=3000,hooks=25,
  checks=['ordinary roster ID14','404A inactive-left policy','active contact steering','same-category wrong identity refused','wrong side refused','normal close','alias failure close','E5 failure close','wrong song pre-I/O rejection'],
  actual_gameplay_proven=False,emulator_launched=False,old_seed17_replay=False)
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
if __name__=='__main__':main()
