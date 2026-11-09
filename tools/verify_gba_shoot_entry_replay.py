"""Actual Lua replay-loader checks; never loads a real emulator state."""
import argparse
import json
from pathlib import Path
import types

import verify_gba_shoot_entry_observer as prior
from verify_gba_shoot_entry_guard_delta import literal

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'build/bizhawk-gba-shoot-entry-20261109-b'

CHECK = r'''
local reference='W:/build/approved-reference'
local base='W:/build/native-entry-independent/'
local backing={}
for name,region in pairs(regions)do
 if region.domain=='IWRAM'or region.domain=='EWRAM'then
  for i=1,#region.data do backing[region.base+i-1]=region.data:byte(i)end
 end
end
local function run(options)
 local o=options or {};local m=create({config={frames=o.frames or 3,checkpoint_dir=reference,probe_sha256=string.rep('A',64)}})
 m.loads,m.clears,m.binds,m.state_saves,m.reference_reads=0,0,0,0,0
 local expected_args=copy(m.config);local saved=false
 local open=m.env.io.open
 m.env.io.open=function(path,mode)
  local text
  if path==reference..'/stage7-hp1.txt'then
   text=metadata
   if o.badmeta=='core'then text=text:gsub('core=64230','core=64231')end
   if o.badmeta=='relative'then text=text:gsub('input_relative=64229','input_relative=64228')end
   if o.badmeta=='consumed'then text=text:gsub('consumed=true','consumed=false')end
  elseif path==reference..'/stage7-hp1.State'then text=o.badzip and 'BAD!'or state
  elseif path:find(reference..'/05-stage7-checkpoint-',1,true)==1 then
   local name=path:match('checkpoint%-(%w+)%.bin$');text=assert(regions[name]).data
  elseif path=='W:/tools/bizhawk_gba_shoot_entry_observer.lua'then
   text=hard_source
   if o.anchor=='missing'then text=text:gsub('local consumed={}','local missing_consumed={}')end
   if o.anchor=='duplicate'then text=text..'\nlocal consumed={}\n'end
  elseif path=='W:/tools/bizhawk_probe_gba_shoot_entry.lua'then
   text=driver_source
   if o.driveranchor then text=text:gsub('local battle=false','local missing_battle=false')end
  end
  if text then
   assert(mode=='rb','all checkpoint/dependency paths read only');m.reference_reads=m.reference_reads+1
   return{read=function(_,kind)assert(kind=='*a');return text end,close=function()end}
  end
  return open(path,mode)
 end
 m.env.userdata.clear=function()
  m.clears=m.clears+1;if o.clear_error then error('userdata clear failed')end
  for k in pairs(m.config)do m.config[k]=nil end
 end
 m.env.userdata.set=function(k,v)
  assert(expected_args[k]~=nil,'explicit allowlisted rebinding only');m.binds=m.binds+1
  m.config[k]=o.badbind==k and 'wrong' or v
 end
 m.env.savestate.load=function(path,suppress)
  m.loads=m.loads+1;assert(path==reference..'/stage7-hp1.State'and suppress==true)
  assert(next(m.hooks)==nil and #m.inputs==0,'load before any callback/input')
  if o.loadmode=='throw'then error('load failed')elseif o.loadmode=='false'then return false end
  m.ram=setmetatable({},{__index=backing});m.frame=o.badframe and 64231 or 64230
  for k in pairs(m.config)do m.config[k]=nil end
  m.config.output='W:/build/old-checkpoint-path';m.config.stale_secret='must clear';m.config.frames=120000
  return true
 end
 local size=m.env.memory.getmemorydomainsize
 m.env.memory.getmemorydomainsize=function(d)return o.badsize==d and 1 or size(d)end
 local bulk=m.env.memory.read_bytes_as_binary_string
 m.env.memory.read_bytes_as_binary_string=function(a,n,d)
  assert(not m.callback,'bulk RAM outsidecallbacks')
  for _,region in pairs(regions)do if d==region.domain then
   assert(a==0 and n==#region.data)
   if (o.badram==d and not saved)or(o.badram_after==d and saved)then return '\255'..region.data:sub(2)end
   return region.data
  end end
  return bulk(a,n,d)
 end
 m.env.savestate.save=function(path,suppress)
  assert(not m.callback and suppress==true);m.state_saves=m.state_saves+1
  if path==base..'restored.State'then
   assert(next(m.hooks)==nil and #m.inputs==0,'restore proof before hook installation/input')
   if o.savemode=='throw'then error('save failed')elseif o.savemode=='false'then return false end
   m.files[path]='STATE';saved=true;if o.afterframe then m.frame=m.frame+1 end;return true
  end
  assert(path:find(base,1,true)==1,'exports stay in new output');m.files[path]='STATE';return true
 end
 if o.forcewrite then
  m.env.emu.frameadvance=function()
   m.advances=m.advances+1;m.frame=m.frame+1
   m.put(0x0300231E,1,1);m.put(0x03004502,0);m.put(0x02011828+4,1);m.put(0x02011710+0x66,4)
   m.fire(0x08373638)
  end
 end
 if o.firehit then
  m.env.emu.frameadvance=function()
   m.advances=m.advances+1;m.frame=m.frame+1
   if m.advances==1 then
    m.fire(0x0836E5E4,{R4=0x02011710,R5=0x02011828,R8=0,R0=1})
    m.put(0x02011828+0x64,0);m.fire(0x0836E5E8);m.fire(0x083736B0)
   end
  end
 end
 if o.samepath then m.config.checkpoint_dir=m.config.output end
 if o.badout then m.config.output='X:/outside' end
 local ok,err=pcall(m.run)
 if o.early then assert(not ok and m.exits==0 and m.advances==0,'invalid startup before actions');return m end
 assert(ok,err);assert(m.exits==1 and #m.writes==0,'one exit and no guest writes')
 if o.failure then
  assert(m.files[base..'shoot-entry-done.txt']=='failure:replay-preflight','preflight fail closed')
  assert(m.files[base..'replay-failure.txt']and m.advances==0,'no native inputs on invalid restore')
  if not o.afterhooks then assert(next(m.hooks)==nil,'invalid restore/anchor must not installhooks')end
 else
  assert(m.loads==1 and m.clears==1 and m.binds==6 and not m.config.stale_secret,'clear old userdata and rebind six explicit arguments')
  assert(m.config.output==expected_args.output and m.config.probe_sha256==expected_args.probe_sha256,'new output/probe survived state userdata')
  assert(m.inputs[1].frame==64230,'first replay controller at restored core')
  local k=m.inputs[1].keys;local frame=64229
  assert(k.A==(frame%97<7)and k.B==(frame%29<7),'next attack input uses original epoch')
  assert(k.Right==(frame%720<300)and k.Left==(frame%720>=360 and frame%720<660)and not k.Up,'next movement phase/base0')
  for _,v in pairs(m.inputs[#m.inputs].keys)do assert(not v,'final release')end
  assert(m.files[base..'replay.txt']:find('input_epoch=1 next_input_relative=64229',1,true))
 end
 return m
end
local m=run();assert(m.advances==3 and m.state_saves==1,'bounded replay; no duplicate boss checkpoint')
for _,mode in ipairs({'false','throw'})do run({loadmode=mode,failure=true});run({savemode=mode,failure=true})end
run({badframe=true,failure=true});run({afterframe=true,failure=true})
for _,region in pairs(regions)do
 run({badram=region.domain,failure=true});run({badram_after=region.domain,failure=true})
end
run({badsize='IWRAM',failure=true})
for _,what in ipairs({'core','relative','consumed'})do run({badmeta=what,failure=true})end
run({badzip=true,failure=true});run({clear_error=true,failure=true});run({badbind='output',failure=true})
for _,what in ipairs({'missing','duplicate'})do run({anchor=what,failure=true})end
run({driveranchor=true,failure=true})
run({samepath=true,early=true});run({badout=true,early=true})
for _,frames in ipairs({-1,1.5,8001})do run({frames=frames,early=true})end
local w=run({forcewrite=true});assert(w.advances==1,'forbidden ordinary score request stops replay')
assert(w.files[base..'shoot-entry-done.txt']=='failure:observer-error'and w.files[base..'shoot-entry-first-failure.txt']:find('replay guest write forbidden',1,true))
local h=run({firehit=true});assert(h.text():find('healthy%-root5'),'historical consumedstage7 survives load and binds later directhit/root5')
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    paths = [ROOT / 'tools' / name for name in ('bizhawk_replay_gba_shoot_entry.lua', 'bizhawk_gba_shoot_entry_observer.lua', 'bizhawk_probe_gba_shoot_entry.lua', 'bizhawk_probe_gba_collision.lua', 'bizhawk_probe_gba_collision_producer.lua')]
    data = [path.read_bytes() for path in paths]
    assert prior.sha(data[0]) == 'A73E59919E77FCA67A2DAE6EEA214E1571604818F05008B405CB919300E2C397'
    assert prior.sha(data[1]) == '7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59'
    regions = dict(iwram=('IWRAM', 0x03000000), ewram=('EWRAM', 0x02000000), vram=('VRAM', 0x06000000), palette=('PALRAM', 0x05000000), oam=('OAM', 0x07000000))
    prefix = 'local regions={\n'
    for name, (domain, base) in regions.items():
        blob = (CAPTURE / ('05-stage7-checkpoint-' + name + '.bin')).read_bytes()
        prefix += f"['{name}']={{domain='{domain}',base={base},data=" + literal(blob) + '},\n'
    prefix += '}\nlocal metadata=' + literal((CAPTURE / 'stage7-hp1.txt').read_bytes())
    prefix += '\nlocal state=' + literal((CAPTURE / 'stage7-hp1.State').read_bytes())
    prefix += '\nlocal driver_source=' + literal(data[2]) + '\n'
    host = types.FunctionType(prior.execute.__code__, dict(prior.__dict__, CHECK=prior.CHECK + prefix), argdefs=prior.execute.__defaults__)
    def run(loader):
        host(loader, data[1].decode(), data[3].decode(), data[4].decode(), CHECK)
    loader = data[0].decode()
    run(loader)
    controls = [
        ('userdata.clear()', '-- userdata clear removed', 'stale checkpoint userdata retained'),
        ('local epoch=captured-relative', 'local epoch=captured-relative+1', 'wrong original input epoch'),
        ('local consumed={[7]=true}', 'local consumed={[7]=false}', 'historical boss consumption lost'),
        ('write_u16_le=function()error("replay guest write forbidden")end',
         'write_u16_le=function(...)return memory.write_u16_le(...)end', 'guest write denial removed'),
        ('assert(savestate.save(out.."/restored.State",true)==true,"restored state export failed")',
         'savestate.save(out.."/restored.State",true)', 'restore export failure ignored'),
        ('==read(reference.."/05-stage7-checkpoint-"..r[1]..".bin")', '~=nil', 'full memory equality removed'),
        ('emu.framecount()==captured', 'true', 'restored frame checks removed'),
        ('captured==64230 and relative==64229', 'true', 'reviewed checkpoint epoch removed'),
    ]
    rejected = []
    for old, new, name in controls:
        assert old in loader
        try:
            run(loader.replace(old, new))
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError('replay mutation accepted: ' + name)
    launcher = ROOT / 'build/run_gba_shoot_entry_replay_20261109.py'
    launcher_bytes = launcher.read_bytes()
    assert prior.sha(launcher_bytes) == '421D809E76B91CBC1D122BB44D1BCDD476A224F501717188CCE5F786B2820172'
    # Execute only its immutable ROM/checkpoint assertions, before any directory/process creation.
    code = launcher_bytes.decode()
    start, stop = code.index("rom = root / 'build/shoot-presentation-target"), code.index("\nexe = root / 'local/")
    import verify_gba_shoot_entry_capture_v2 as capture
    scope = dict(root=ROOT, sha=prior.sha, json=json, parse_checkpoint=capture.parse_checkpoint,
                 checkpoint_core=capture.checkpoint_core, prior=capture.prior)
    exec(compile(code[start:stop], '@replay-host-readonly-preflight', 'exec'), scope)
    report = dict(status='ACTUAL_LUA_NATIVE_REPLAY_WRAPPER_PASS',
                  pins={str(path.relative_to(ROOT)).replace('\\', '/'): prior.sha(blob) for path, blob in zip(paths, data)},
                  verifier_sha256=prior.sha(Path(__file__).read_bytes()), launcher_sha256=prior.sha(launcher_bytes),
                  checkpoint_sha256=prior.sha((CAPTURE / 'stage7-hp1.State').read_bytes()),
                  corrected_rom_sha256=scope['rom_sha'],
                  actual_lua_checks=['load before hooks/input; clear/rebind six explicit args',
                                     'false/throw load/save; wrong frame before/after proof; all five RAM mismatches pre/post',
                                     'wrong metadata/header/domain/path/budget/rebind and missing/duplicate anchors refuse preflight',
                                     'original epoch1 next input64229; bounded loop/release and zero new guest writes',
                                     'historical consumed7 binds a later actual-Lua directhit/root5',
                                     'forced ordinary score request stops at immutable replay write denial'],
                  semantic_mutations_rejected=rejected,
                  readonly_host_preflight='actual exact five-word ROM delta+unchanged header and genuine Core/five-region checkpoint assertions passed',
                  expected_restored_Core_only_CRC_interval=[12, 16], emulator_launched=False,
                  actual_state_loaded=False, guest_memory_written=False,
                  limits=['API fixtures validate loader behavior; actual restore/resave full Core comparison remains root runtime QA'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', prior.sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
