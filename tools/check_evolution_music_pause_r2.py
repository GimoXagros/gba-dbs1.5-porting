"""Bounded author Lua54 source/composition and pause-policy checks; no emulator."""
import argparse
import hashlib
import json
import re
import struct
import types
from pathlib import Path
import verify_wsc_shoot_short_hard as host

ROOT = Path(__file__).resolve().parents[1]
sha = lambda b: hashlib.sha256(b).hexdigest().upper()
quote = lambda b: '"' + ''.join('\\' + f'{v:03d}' for v in b) + '"'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    assert not args.report.exists()
    names = ['bizhawk_probe_evolution_music_pause_r2.lua', 'bizhawk_probe_result_music_lifetime.lua', 'bizhawk_probe_result_languages.lua']
    wrapper, lifetime, base = [(ROOT / 'tools' / n).read_bytes() for n in names]
    assert sha(lifetime) == 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430'
    assert sha(base) == '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC'
    rom = (ROOT / 'build/evolution-music-pause-cache-20261110/component.gba').read_bytes()
    assert sha(rom) == 'C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
    telemetry = re.search(rb'local telemetry=\[=\[\n(.*?)\]=\]', lifetime, re.S).group(1)
    telemetry = telemetry.replace(b' music_counts[label]=(music_counts[label] or 0)+1', b' music_pause_observe(label,r)\n music_counts[label]=(music_counts[label] or 0)+1')
    telemetry = telemetry.replace(b'policy=unchanged hook_count=10 per_label_limit=32 max_event_rows=320', b'policy=ordinary-until-6E-then-Start-pair hook_count=14 per_label_limit=32 max_event_rows=512')
    policy = re.search(rb'local policy=\[=\[\n(.*?)\]=\]', wrapper, re.S).group(1)
    changes = [
        (b'dump("loaded-rom.bin","ROM",0,0x800000)', b'dump("loaded-rom.bin","ROM",0,0x1000000)'),
        (b'local limit=userdata.get("frames") or 24000', b'local limit=math.min(userdata.get("frames") or 15000,15000)'),
        (b' joypad.set(keys)', b' music_pause_input(keys,stage,mode)\n joypad.set(keys)'),
        (b' if outcome then break end', b' local pause_outcome=music_pause_outcome()\n if pause_outcome then outcome=pause_outcome;capture("pause-end") end\n if outcome then break end'),
        (b'if not outcome then outcome="bounded-no-result";capture("bounded-end") end', b'if outcome~="evolution-pause-resume-stage-return" and not (outcome and outcome:match("^failure:")) then outcome="failure:pause-target-not-completed";capture("bounded-end") end'),
        (b'local f=assert(io.open(out.."/result-done.txt","w"));', b'music_lifetime_finish()\nlocal f=assert(io.open(out.."/result-done.txt","w"));'),
    ]
    body = base
    for before, after in changes:
        assert body.count(before) == 1
        body = body.replace(before, after)
    prefix = b'local music_pause_observe\n' + telemetry + policy
    expected = prefix + body
    sites = [0x37B458, 0xD7DFC0, 0xD7DFC8, 0x37FBB4] + [0xD33000 + i * 8 + j for i in [0x10, 0x6C, 0x6D, 0x6E, 0x6F] for j in (0, 4)]
    scalars = 'local scalars={' + ','.join(f'[{0x08000000+a}]={struct.unpack_from("<I", rom, a)[0]}' for a in sites) + '}\n'
    test = r'''
for _,case in ipairs({'happy','absence','wrong-cache','missing-stop','wrong-player','stale-compare','missing-resume','early-return','foreign-restart','deadline'})do
 local frame=100;local hooks,lines={},{};local ram={};for k,v in pairs(scalars)do ram[k]=v end
 local marker
 local regs={R0=0,R1=0,R2=0,R3=0,R4=0,R8=0,R13=0,R14=0,R15=0}
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/pause-author'end}
 local domains={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function read(a,d)return ram[assert(domains[d])+a]or 0 end
 env.memory=setmetatable({getmemorydomainsize=function()return 0x1000000 end,read_u8=read,read_u16_le=read,read_u32_le=read},{__index=function(_,k)error('unexpected memory API '..k)end})
 env.emu={framecount=function()return frame end,getregisters=function()return regs end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 env.io={open=function(path,mode)
  if mode=='rb'then local payload=path=='W:/tools/bizhawk_probe_result_music_lifetime.lua'and hard_source or path=='W:/tools/bizhawk_probe_result_languages.lua'and collect_source;assert(payload);return{read=function()return payload end,close=function()end}end
  if path=='W:/build/pause-author/result-done.txt'then assert(mode=='w');return{write=function(_,s)assert(table.concat(lines):find('count event=iwram-alias-cache observed=1 emitted=1',1,true));marker=s;return true end,close=function()end}end
  assert(path=='W:/build/pause-author/music-lifetime.txt'and mode=='wb')
  return{write=function(_,s)lines[#lines+1]=s;return true end,flush=function()end,close=function()end}
 end}
 local captured
 env.load=function(s,n,m,e)assert(n=='@reviewed-evolution-music-pause'and m=='t'and e==env);assert(s==expected);assert(load(s,n,m,e));captured=s;return function()end end
 assert(load(wrapper_source,'@wrapper','t',env))();assert(captured)
 env.RAM=ram;env.REGS=regs;env.HOOKS=hooks;env.CASE=case;env.SET_FRAME=function(v)frame=v end
 local exercise=[[
 local function hit(pc)HOOKS[pc]()end
 local function start(header,cache)
  REGS.R0=0x03006B40;REGS.R1=header;hit(0x0837C298)
  RAM[0x03006B40]=header;RAM[0x03004E98]=cache;RAM[0x03006B44]=7;hit(0x0837C29C)
 end
 local keys={Start=false,A=true};music_pause_input(keys,'battle',7);assert(keys.A and not keys.Start)
 if CASE=='absence'then assert(not music_pause_outcome());music_lifetime_finish();return end
 start(evo,CASE=='wrong-cache'and 0x10 or 0x6E)
 if CASE=='wrong-cache'then assert(pause.phase=='waiting');music_lifetime_finish();return end
 SET_FRAME(101);music_pause_input(keys,'battle',7);assert(keys.Start and not keys.A)
 hit(0x0837B48C);REGS.R0=evo;REGS.R1=evo;hit(0x0837C364)
 if CASE=='stale-compare'then SET_FRAME(102)end
 REGS.R0=CASE=='wrong-player'and 0x03006B80 or 0x03006B40;REGS.R14=0x0837C36F
 if CASE~='missing-stop'then hit(0x0837C9C8)end
 RAM[0x03006B44]=0x80000007
 local pressed=1
 for age=1,37 do
  SET_FRAME(101+age);music_pause_input(keys,'battle',7)
  assert(keys.Start==(age<4 or age>=34));assert(not keys.A)
  if keys.Start then pressed=pressed+1 end
  if age==4 and (CASE=='missing-stop'or CASE=='wrong-player'or CASE=='stale-compare')then assert(music_pause_outcome()=='failure:pause-not-held');music_lifetime_finish();return end
  if age==34 and CASE~='missing-resume'then
   hit(0x0837B4A8);REGS.R0=evo;REGS.R1=evo;hit(0x0837C398);REGS.R0=0x03006B40;REGS.R14=0x0837C3A3;hit(0x0837C1A8);RAM[0x03006B44]=7
   if CASE=='early-return'then hit(0x0835A75C);assert(not pause.devolution);assert(not music_pause_outcome())end
  end
 end
 assert(pressed==8)
 SET_FRAME(139);music_pause_input(keys,'battle',7);assert(not keys.Start)
 if CASE=='missing-resume'then assert(music_pause_outcome()=='failure:resume-not-active');music_lifetime_finish();return end
 assert(pause.resume_boundary and pause.phase=='running'and not music_pause_outcome())
 if CASE=='foreign-restart'then start(stage_header,0x10);assert(music_pause_outcome()=='failure:unexpected-player-zero-restart')
 elseif CASE=='deadline'then SET_FRAME(3100);assert(music_pause_outcome()=='failure:pause-return-deadline')
 else SET_FRAME(200);hit(0x0835A75C);assert(pause.devolution==200);SET_FRAME(201);start(stage_header,0x10);assert(music_pause_outcome()=='evolution-pause-resume-stage-return')end
 for i=1,40 do hit(0x03000D00)end
 assert(music_pause_outcome()=='failure:copied-request-entry-executed')
 local ok,err=pcall(function()hit(0x03000D0C)end);assert(not ok and err:find('copied-cache-branch-executed',1,true))
 ]]
 assert(load(prefix..exercise,'@policy-exercise','t',env))()
 local n=0;for _ in pairs(hooks)do n=n+1 end;assert(n==14)
 if case=='happy'or case=='early-return'or case=='foreign-restart'or case=='deadline'then
  local alias_rows=0;for _,line in ipairs(lines)do if line:match('^event=iwram%-alias%-')then alias_rows=alias_rows+1 end end;assert(alias_rows==33)
  assert(marker=='failure:copied-cache-branch-executed')
 end
 assert(table.concat(lines):find('policy=ordinary-until-6E-then-Start-pair',1,true))
end
'''
    check = 'local expected=' + quote(expected) + '\nlocal prefix=' + quote(prefix) + '\n' + scalars + test
    fn = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=check), argdefs=host.lua_check.__defaults__)
    fn(wrapper.decode(), lifetime.decode(), base.decode())
    report = dict(status='EVOLUTION_MUSIC_PAUSE_AUTHOR_PASS', wrapper_sha256=sha(wrapper), lifetime_sha256=sha(lifetime), base_sha256=sha(base), rom_sha256=sha(rom), effective_sha256=sha(expected), actual_Lua54_cases=10, base_exact_substitutions=len(changes), input_schedule='4 Start / 30 neutral / 4 Start / neutral until return', maximum_total_frames=15000, maximum_post_arm_frames=3000, emulator_launched=False, runtime_proven=False, checker_sha256=sha(Path(__file__).read_bytes()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes((json.dumps(report, indent=2)+'\n').encode())
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
