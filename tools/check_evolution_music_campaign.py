"""Small actual-Lua author check for the separate score-assisted CPU11 route."""
import argparse
import hashlib
import json
import struct
import types
from pathlib import Path
import verify_wsc_shoot_short_hard as host

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
quote=lambda b:'"'+''.join('\\'+f'{v:03d}'for v in b)+'"'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert not a.report.exists()
 names=['bizhawk_probe_evolution_music_campaign.lua','bizhawk_probe_evolution_music_three.lua','bizhawk_probe_result_music_lifetime.lua','bizhawk_probe_result_languages.lua']
 outer,three,lifetime,base=[(ROOT/'tools'/n).read_bytes()for n in names]
 assert sha(three)=='B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881'
 assert sha(lifetime)=='CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430'
 assert sha(base)=='928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
 rom=(ROOT/'build/evolution-music-pause-cache-20261110/component.gba').read_bytes();assert sha(rom)=='C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
 sites=[0x37B458,0xD7DFC0,0xD7DFC8,0x37FBB4,0xD14A8]+[0xD33000+i*8+j for i in [0x10,0x6C,0x6D,0x6E,0x6F]for j in(0,4)]
 values={0x08000000+x:struct.unpack_from('<I',rom,x)[0]for x in sites};cat=values[0x080D14A8]
 values.update({cat+i:rom[cat-0x08000000+i]for i in range(16)})
 values.update({0x08628000+i:struct.unpack_from('<H',rom,0x628000+i)[0]for i in range(0,128,2)})
 setup='local scalars={'+','.join(f'[{k}]={v}'for k,v in values.items())+'}\nlocal three='+quote(three)+'\n'
 test=r'''
local effective
for _,case in ipairs({'write','wrong-mode','wrong-kind','wrong-id','dead','difficulty','budget','no-auth'})do
 local ram={};for k,v in pairs(scalars)do ram[k]=v end
 local writes,logs,closed,hooks={}, {}, {}, {}
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)if k=='output'then return 'W:/build/campaign-author'elseif k=='target_song'then return 0x6F elseif k=='score_authorization'then return case=='no-auth'and 'missing'or 'user-approved-development-score999'end;error(k)end}
 local bases={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function read(a,d)return ram[assert(bases[d])+a]or 0 end
 env.memory={getmemorydomainsize=function()return 0x1000000 end,read_u8=read,read_u16_le=read,read_u32_le=read,
 write_u16_le=function(a,v,d)assert(d=='EWRAM'and a==0x11776 and v==999);writes[#writes+1]={a,v};ram[0x02000000+a]=v end}
 env.emu={framecount=function()return 240 end,getregisters=function()return {R0=0,R1=0,R2=0,R3=0,R4=0,R8=0,R13=0,R14=0,R15=0}end}
 env.event={on_bus_exec=function(fn,pc)assert(not hooks[pc]);hooks[pc]=fn end}
 env.io={open=function(path,mode)
  if mode=='rb'then local b=path=='W:/tools/bizhawk_probe_evolution_music_three.lua'and three or path=='W:/tools/bizhawk_probe_result_music_lifetime.lua'and hard_source or path=='W:/tools/bizhawk_probe_result_languages.lua'and collect_source;assert(b);return{read=function()return b end,close=function()end}end
  assert(path:match('^W:/build/campaign%-author/'));return{write=function(_,s)assert(not closed[path]);logs[#logs+1]={path,s};return true end,flush=function()end,close=function()closed[path]=true end}
 end}
 env.load=function(s,n,m,e)
  assert(m=='t'and e==env)
  if n=='@reviewed-evolution-music-campaign-wrapper'then return load(s,n,m,e)end
  assert(n=='@reviewed-evolution-music-pause');assert(load(s,n,m,e));effective=s;return function()end
 end
 assert(load(wrapper_source,'@campaign','t',env))();assert(effective)
 local anchor='-- Ordinary-input Options commit -> title -> 1P battle -> natural result.'
 local at=assert(effective:find(anchor,1,true));local prefix=effective:sub(1,at-1)
 env.RAM=ram;env.CASE=case;env.WRITES=writes
 local exercise=[[
  RAM[0x03004740]=12;assert(music_selection()=='A'and chosen==0)
  local p,q=0x02011710,0x02011828
  RAM[0x0300489C]=p;RAM[0x030048A0]=q;RAM[0x0300231F]=1;RAM[0x0300231E]=1;RAM[0x0300232E]=0
  RAM[p-8]=2;RAM[q-8]=2;RAM[p+4]=0;RAM[q+4]=0;RAM[p+0x10]=0;RAM[q+0x10]=1;RAM[p+0x11]=0;RAM[q+0x11]=1
  RAM[p+0x14]=p;RAM[q+0x14]=q;RAM[p+0x18]=q;RAM[q+0x18]=p
  RAM[p+0x64]=8;RAM[q+0x64]=8;RAM[p+0x66]=12;RAM[p+0x68]=0x11223344
  if CASE=='wrong-kind'then RAM[q+4]=3 elseif CASE=='wrong-id'then RAM[p+0x11]=1 elseif CASE=='dead'then RAM[p+0x64]=0 elseif CASE=='difficulty'then RAM[0x0300231F]=2 elseif CASE=='budget'then score_writes=512 end
  campaign_input('battle',CASE=='wrong-mode'and 8 or 7)
  if CASE=='write'then
   assert(#WRITES==1 and RAM[p+0x66]==999 and RAM[p+0x64]==8 and RAM[q+0x64]==8 and RAM[p+0x68]==0x11223344)
   campaign_input('battle',7);assert(#WRITES==1)
  else assert(#WRITES==0)end
  if CASE=='difficulty'then assert(music_pause_outcome()=='failure:campaign-not-Normal')end
  if CASE=='budget'then assert(music_pause_outcome()=='failure:score-write-budget')end
  score_file:close();music_lifetime_finish()
 ]]
 local ok,err=pcall(assert(load(prefix..exercise,'@campaign-exercise','t',env)))
 if case=='no-auth'then assert(not ok and err:find('score assist authorization',1,true))else assert(ok,err);local n=0;for _ in pairs(hooks)do n=n+1 end;assert(n==17)end
end
local body=assert(wrapper_source:match('local result_after=%[=%[\n(.-)%]=%]'))
for _,mode in ipairs({8,5,6,7,9,3})do
 local env=setmetatable({},{__index=_G});local call
 env.mode=mode;env.stage='result';env.frame=17;env.campaign_round=0
 env.pulse=function(b,f)assert(b=='A'and f==17);call='pulse'end
 env.capture=function(s)assert(s=='battle-enter');call='capture'end
 env.state=function(s,f)assert(s=='battle'and f==17);call='battle'end
 env.fail=function(s)call=s end
 assert(load('if false then\n'..body,'@native-result-continuation','t',env))()
 assert(call==(mode==7 and 'battle'or mode==9 and 'campaign-continue'or mode==3 and 'campaign-returned-title'or 'pulse'))
 if mode==7 then assert(env.campaign_round==1)end
end
OUTPUT(effective)
'''
 # Retain the composed source for review; Lua's Windows fopen needs an ASCII path.
 outdir=a.report.parent;outdir.mkdir(parents=True,exist_ok=True)
 effective_path=outdir/'campaign-effective-author.lua';assert not effective_path.exists()
 destination=effective_path.resolve().relative_to(ROOT).as_posix()
 code=setup+'local OUTPUT=function(s)local f=assert(io.open('+quote(destination.encode())+',"wb"));assert(f:write(s));f:close()end\n'+test
 fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__);fn(outer.decode(),lifetime.decode(),base.decode())
 result=dict(status='EVOLUTION_MUSIC_CAMPAIGN_AUTHOR_PASS',probe_sha256=sha(outer),inner_sha256=sha(three),effective_sha256=sha(effective_path.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),score_cases=8,result_transition_cases=6,score_only_address='live FIRST+66 / EWRAM u16',score_write_max=512,total_frame_max=60000,post_target_frame_max=3000,emulator_launched=False,actual_campaign_proven=False)
 a.report.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))

if __name__=='__main__':main()
