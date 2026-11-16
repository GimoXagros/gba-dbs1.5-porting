"""Independent bounded music telemetry composition and actual-host prefix gate."""
import argparse,ast,hashlib,json,re,struct,types
from pathlib import Path
import verify_wsc_shoot_short_hard as host
import verify_result_language_capture as runtime

ROOT=Path(__file__).resolve().parents[1]
OUTER='CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430'
INNER='5D6264063DEBCB9F6F3A1405B0F0BA5F96AFFF96A6D072E8E97819E5BF877EAF'
BASE='928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
ROM='C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
RUNTIME='DA8D3AA45AFE81D6EDF328F084B69F333E138CF8FAEEA71BAA0AAF94347D1085'
HOST='A6342D07460F21FB324005C31A717F6AA42E4232D478CDE69BC1EBE4ED28E339'
sha=lambda b:hashlib.sha256(b).hexdigest().upper()
quote=lambda b:'"'+''.join('\\'+f'{v:03d}'for v in b)+'"'
def need(v,s):
    if not v:raise ValueError(s)


def lua_check(outer,inner,base,rom):
    prefix=re.findall(rb'local telemetry=\[=\[\n(.*?)\]=\]',outer,re.S);need(len(prefix)==1,'one telemetry block');prefix=prefix[0]
    body=base.replace(b'dump("loaded-rom.bin","ROM",0,0x800000)',b'dump("loaded-rom.bin","ROM",0,0x1000000)')
    need(body.count(b'client.exit()')==1,'one ordinary finish')
    expected=prefix+body.replace(b'client.exit()',b'music_lifetime_finish()\nclient.exit()')
    need(sha(expected)=='88B8672BC0C87DA27145F4E6012175A0CB8058F5D17908E63A01A94953A616E8','entire expected composition')
    sites=[0x37B458,0xD7DFC0,0xD7DFC8,0x37FBB4]+[0xD33000+i*8+j for i in range(0x6C,0x70)for j in (0,4)]
    values={0x08000000+a:struct.unpack_from('<I',rom,a)[0]for a in sites}
    header=values[0x08D33000+0x6E*8]
    setup='local scalars={'+','.join(f'[{a}]={v}'for a,v in values.items())+'}\nlocal HEADER='+str(header)+'\n'
    test=r'''
for _,mode in ipairs({'absence','all-caps','bad-ROM','missing-mid-anchor','duplicate-mid-anchor','missing-exit','duplicate-exit'})do
 local hooks,lines={},{};local frame=91;local final=false
 local regs={R0=0,R1=0,R2=0,R3=0,R4=0x02011710,R8=0,R13=0x03007F00,R14=0x0835A454,R15=0}
 local ram={};for a,v in pairs(scalars)do ram[a]=v end
 ram[0x03007F00]=2;ram[0x02011721]=2;ram[0x03004E98]=0x6E;ram[0x03006B40]=HEADER
 if mode=='bad-ROM'then ram[0x0837B458]=0 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/lifetime-independent'end}
 local bases={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function read(a,d)return ram[assert(bases[d])+a]or 0 end
 env.memory=setmetatable({getmemorydomainsize=function()return 0x1000000 end,read_u8=read,read_u16_le=read,read_u32_le=read},{__index=function(_,k)error('unapprovedmemoryAPI:'..k)end})
 env.emu={framecount=function()return frame end,getregisters=function()return regs end}
 env.event={on_bus_exec=function(fn,a,label)assert(not hooks[a]);hooks[a]=fn end}
 env.joypad=setmetatable({},{__index=function()error('telemetryinputforbidden')end})
 env.savestate=setmetatable({},{__index=function()error('telemetrystateforbidden')end})
 env.io={open=function(path,access)
  if access=='rb'then
   local payload
   if path=='W:/tools/bizhawk_probe_result_languages_16m.lua'then
    payload=inner_source
    if mode=='missing-mid-anchor'then payload=payload:gsub('@reviewed%-result%-sixteen%-MiB%-capture','@wrong')end
    if mode=='duplicate-mid-anchor'then payload=payload..'\n-- '..MID_ANCHOR end
   elseif path=='W:/tools/bizhawk_probe_result_languages.lua'then
    payload=base_source
    if mode=='missing-exit'then payload=payload:gsub('client%.exit%(%)','client.other()')end
    if mode=='duplicate-exit'then payload=payload..'\n-- client.exit()'end
   else error('unexpected source path')end
   return{read=function()return payload end,close=function()end}
  end
  assert(path=='W:/build/lifetime-independent/music-lifetime.txt'and access=='wb')
  return{write=function(_,s)assert(#s<2048,'scalarrecords');lines[#lines+1]=s;return true end,flush=function()end,close=function()end}
 end}
 env.load=function(text,name,kind,scope)
  assert(kind=='t'and scope==env)
  if name~='@reviewed-result-music-lifetime'then return load(text,name,kind,scope)end
  assert(text==expected_source,'entirebaseonlyprefixandfinish');assert(load(text,name,kind,scope));final=true
  return function()
   env.HOOKS=hooks;env.REGS=regs;env.RAM=ram;env.HEADER=HEADER;env.MODE=mode
   env.NEXT_FRAME=function()frame=frame+1 end
   local exercise=[[
    if MODE=='all-caps'then
     for i=1,41 do
      HOOKS[0x080D14BC]();HOOKS[0x080D14F0]();REGS.R8=0x6E;HOOKS[0x0837B44C]()
      REGS.R0=0x03006B40;REGS.R1=HEADER;HOOKS[0x0837C298]();HOOKS[0x0837C29C]()
      RAM[0x03004506]=i%2==0 and 0 or 0x80;HOOKS[0x0835A75C]()
      HOOKS[0x0837B48C]();HOOKS[0x0837B4A8]()
      REGS.R0=123;REGS.R1=i%2==0 and 123 or 124;HOOKS[0x0837C364]();HOOKS[0x0837C398]()
     end
     REGS.R8=0x50;HOOKS[0x0837B44C]()
     REGS.R0=0x03006B80;HOOKS[0x0837C298]();HOOKS[0x0837C29C]()
     REGS.R0=0x03006B40;REGS.R1=HEADER;HOOKS[0x0837C298]();NEXT_FRAME();HOOKS[0x0837C29C]()
    end
    music_lifetime_finish()
   ]]
   assert(load(prefix_source..exercise,'@independent-scalars','t',env))()
  end
 end
 local ok=pcall(assert(load(wrapper_source,'@outer','t',env)))
 if mode=='absence'or mode=='all-caps'then
  assert(ok and final);local count=0;for _ in pairs(hooks)do count=count+1 end;assert(count==10)
  local text=table.concat(lines);local rows=0;for row in text:gmatch('[^\n]+')do if row:sub(1,6)=='event='then rows=rows+1 end end
  assert(text:find('absence_is_not_coverage=true',1,true))
  if mode=='absence'then assert(rows==0 and text:find('evolution_entries=0 starts6C=0 starts6D=0 starts6E=0 starts6F=0',1,true))
  else
   assert(rows==320 and text:find('evolution_entries=41 starts6C=0 starts6D=0 starts6E=42 starts6F=0',1,true))
   assert(text:find('count event=music-request observed=41 emitted=32',1,true))
   assert(text:find('count event=player-zero-start observed=42 emitted=32',1,true))
   assert(text:find('count event=player-zero-start-return observed=41 emitted=32',1,true))
   assert(text:find('equal=true',1,true)and text:find('equal=false',1,true))
  end
 else assert(not ok,'bad source refused:'..mode)end
end
'''
    code='local inner_source='+quote(inner)+'\nlocal base_source='+quote(base)+'\nlocal expected_source='+quote(expected)+'\nlocal prefix_source='+quote(prefix)+'\nlocal MID_ANCHOR='+quote(b'assert(load(source,"@reviewed-result-sixteen-MiB-capture","t",_ENV))()')+'\n'+setup+test
    fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=code),argdefs=host.lua_check.__defaults__);fn(outer.decode(),'','')
    return sha(expected)


def source_and_prefix(outer,rom):
    q=(ROOT/'tools/verify_result_language_capture.py').read_bytes();h=(ROOT/'build/run_result_v77_r3_20261110.py').read_bytes()
    need((sha(q),sha(h))==(RUNTIME,HOST),'actual frozen runtime/host')
    old=(ROOT/'build/verify_result_language_capture_pre_lifetime_20261110.py').read_bytes();need(sha(old)=='949F36CBE92602220022D72F449ADD2657AD9D3431FF304B2AEC0C8AB9523C81','prior runtime')
    tree=ast.parse(q);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='audit')
    added=[n for n in ast.walk(fn)if isinstance(n,ast.If)and "sha(rom) == 'C344"in ast.unparse(n.test)]
    need(len(added)==1,'one new script selection branch');node=added[0]
    removed=set(range(node.lineno-1,node.end_lineno));restored=b''.join(s for i,s in enumerate(q.splitlines(keepends=True))if i not in removed)
    need(restored==old,'whole runtime only three added lines')
    prior_host=(ROOT/'build/run_result_v77_r2_20261110.py').read_bytes();need(sha(prior_host)=='5991F620E6DD4899802B61BC30EFBDF4995EDE06D3B742E3763FB04E0C16139E','prior host')
    text=h.decode();block="inner_script = root / 'tools/bizhawk_probe_result_languages_16m.lua'\ninner_sha = sha(inner_script)\nassert inner_sha == '"+INNER+"'\n"
    need(text.count(block)==1,'inner source prepin');text=text.replace(block,'').replace(' and sha(inner_script) == inner_sha','').replace("report['inner_script_sha256'] = inner_sha\n",'')
    text=text.replace('build/evolution-music-pause-cache-20261110/component.gba','build/repro-v77-20261110-c/current-candidate.gba').replace('bizhawk_probe_result_music_lifetime.lua','bizhawk_probe_result_languages_16m.lua').replace(OUTER,INNER)
    need(text.encode()==prior_host,'whole host only source path/wrapper/pins changes')
    calls=[]
    class Blocked(Exception):pass
    allowed={ROOT/'tools/build_evolution_music_integration.py',ROOT/'tools/bizhawk_probe_result_languages.lua',ROOT/'tools/bizhawk_probe_result_languages_16m.lua'}
    def read(p):
        if p in allowed:return p.read_bytes()
        calls.append(p.name);raise Blocked()
    function=types.FunctionType(runtime.audit.__code__,dict(runtime.audit.__globals__,read=read),argdefs=runtime.audit.__defaults__)
    retail=Path('C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba').read_bytes()
    try:function(Path('NO_CAPTURE'),rom,retail,outer)
    except Blocked:need(calls==['launch.json'],'valid prefix before first capture access')
    else:raise ValueError('prefix boundary missing')
    return sha(old),sha(prior_host)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();need(not a.report.exists(),'fresh output')
    files=[ROOT/'tools'/n for n in ('bizhawk_probe_result_music_lifetime.lua','bizhawk_probe_result_languages_16m.lua','bizhawk_probe_result_languages.lua')];outer,inner,base=[p.read_bytes()for p in files]
    need(tuple(map(sha,(outer,inner,base)))==(OUTER,INNER,BASE),'three frozen observer levels')
    rom=(ROOT/'build/evolution-music-pause-cache-20261110/component.gba').read_bytes();need(sha(rom)==ROM,'same final C344')
    effective=lua_check(outer,inner,base,rom);oldq,oldh=source_and_prefix(outer,rom)
    report=dict(status='MUSIC_LIFETIME_WRAPPER_RUNTIME_HOST_PREFLIGHT_PASS',wrapper_sha256=OUTER,inner_sha256=INNER,base_sha256=BASE,effective_sha256=effective,runtime_sha256=RUNTIME,host_sha256=HOST,whole_prior_runtime_sha256=oldq,whole_prior_host_sha256=oldh,actual_Lua54_scenarios=7,all10_scalar_hooks_32_rows_each_320_total=True,uncapped_counts_and_absence_checked=True,wrong_player_SFX_and_cross_frame_return_filtered=True,exact_entire_ordinary_body_only_prefix_and_finish=True,actual_C344_ROM_scalar_assertions=True,no_new_guest_write_input_frame_or_bulk_capture=True,first_capture_access_blocked=True,emulator_launched=False,old_full_suite_rerun=False,verifier_sha256=sha(Path(__file__).read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()
