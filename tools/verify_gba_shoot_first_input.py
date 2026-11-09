"""Source-bound actual-Lua first-input probe; no emulator/state load."""
import argparse
import json
from pathlib import Path
import sys
import types

import verify_gba_shoot_entry_observer as host
import verify_gba_shoot_entry_capture_v2 as state
from verify_gba_shoot_entry_guard_delta import literal

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / 'build/bizhawk-gba-shoot-entry-replay-20261109-a'

CHECK = r'''
local base,ref='W:/build/native-entry-independent/','W:/build/healthy-reference'
local backing={}
for _,r in pairs(regions)do if r.domain=='IWRAM'or r.domain=='EWRAM'then for i=1,#r.data do backing[r.base+i-1]=r.data:byte(i)end end end
local function run(options)
 local o=options or {};local m=create({config={checkpoint_dir=ref,probe_sha256=PROBE}})
 m.loads,m.saves,m.binds=0,0,0;local saved=false;local input_keys={}
 m.env.io.open=function(path,mode)
  assert(not m.callback,'no callback disk I/O')
  local text
  if path==ref..'/healthy-activation.txt'then text=o.badmeta and 'core=1' or metadata
  elseif path==ref..'/healthy-activation.State'then text=o.badzip and 'BAD!'or checkpoint
  else
   local name=path:match('^W:/build/healthy%-reference/13%-healthy%-activation%-(%w+)%.bin$')
   if name then text=assert(regions[name]).data end
  end
  if text then assert(mode=='rb','reference read only');return{read=function()return text end,close=function()end}end
  assert(path:find(base,1,true)==1 and mode=='wb','new output only')
  m.files[path]='';return{write=function(self,s)m.files[path]=m.files[path]..s;return self end,close=function()end}
 end
 m.env.userdata.clear=function()for k in pairs(m.config)do m.config[k]=nil end end
 m.env.userdata.set=function(k,v)m.binds=m.binds+1;m.config[k]=v end
 m.env.savestate.load=function(path,suppress)
  assert(path==ref..'/healthy-activation.State'and suppress==true and next(m.hooks)==nil and #m.inputs==0)
  m.loads=m.loads+1;if o.load=='throw'then error('load failure')elseif o.load=='false'then return false end
  m.ram=setmetatable({},{__index=backing});m.frame=o.badframe and 68928 or 68927
  if o.heldA then m.put(0x03001302,0x40)end
  if o.badcontroller then m.put(m.get(0x03004510,4),0,4)end
  m.config.old_checkpoint_userdata='remove';m.config.output='W:/build/old-path'
  return true
 end
 local size=m.env.memory.getmemorydomainsize
 m.env.memory.getmemorydomainsize=function(d)return o.badsize==d and 1 or size(d)end
 local bulk=m.env.memory.read_bytes_as_binary_string
 m.env.memory.read_bytes_as_binary_string=function(a,n,d)
  assert(not m.callback,'no callback bulk memory')
  for _,r in pairs(regions)do if d==r.domain then
   assert(a==0 and n==#r.data)
   if (o.badram==d and not saved)or(o.badram_after==d and saved)then return '\255'..r.data:sub(2)end
   return r.data
  end end
  return bulk(a,n,d)
 end
 m.env.savestate.save=function(path,suppress)
  assert(not m.callback and suppress==true);m.saves=m.saves+1
  if path==base..'restored.State'then
   assert(next(m.hooks)==nil and #m.inputs==0)
   if o.save=='throw'then error('export failure')elseif o.save=='false'then return false end
   saved=true;if o.afterframe then m.frame=m.frame+1 end
  else
   assert(path==base..'after-input.State'and m.advances==6)
   if o.finalsave then return false end
  end
  m.files[path]='STATE';return true
 end
 m.env.joypad.set=function(keys)
  for k,v in pairs(keys)do assert(not v or k=='A','only A may be pressed')end
  input_keys=copy(keys);m.inputs[#m.inputs+1]={frame=m.frame,keys=copy(keys)}
 end
 m.env.emu.frameadvance=function()
  m.advances=m.advances+1
  assert(input_keys.A==(m.advances==1),'one A frame followed by five releases')
  if o.advance_error then error('synthetic advance failure')end
  local held=input_keys.A and 0x40 or 0;local previous=m.get(0x03001302)
  local edge=held&(previous~held)
  m.put(0x03001300,previous);m.put(0x03001302,held);m.put(0x03001306,edge)
  m.fire(0x08375138,{R4=0x02011710,R3=0,R0=held,R1=edge})
  m.put(0x02011710+0x2C,held);m.fire(0x0837513C)
  m.put(0x02011710+0x2E,edge);m.fire(0x08375140)
  m.frame=m.frame+(o.advance_two and 2 or 1)
 end
 m.run();assert(m.exits==1 and #m.writes==0,'one exit, no guest write API')
 for _,v in pairs(m.inputs[#m.inputs].keys)do assert(not v,'error/success final release')end
 if o.failure then
  assert(m.files[base..'first-input-done.txt']=='failure'and m.files[base..'first-input-failure.txt'],'API/guard failure surfaced')
  if not o.advance_error and not o.advance_two and not o.finalsave then assert(m.advances==0 and next(m.hooks)==nil,'invalid preflight cannot installhooks/advance')end
 else
  assert(m.loads==1 and m.binds==3 and not m.config.old_checkpoint_userdata,'three explicit userdata bindings')
  assert(m.advances==6 and m.frame==68933 and m.saves==2,'six exact frame advances/two proof exports')
  assert(m.files[base..'first-input-done.txt']=='six-input-frames-captured')
  local trace=m.files[base..'first-input-trace.txt']
  assert(trace:find('held=0040 edge=0040 pheld=0000 pedge=0000',1,true),'138 prestore copied scalar values')
  assert(trace:find('pheld=0040 pedge=0000',1,true)and trace:find('pheld=0040 pedge=0040',1,true),'13C/140 store sequencing')
  assert(trace:find('R0=00000040',1,true)and trace:find('R15=0837513C',1,true),'register payload and pipeline PC retained')
 end
 return m
end
run()
for _,mode in ipairs({'false','throw'})do run({load=mode,failure=true});run({save=mode,failure=true})end
run({badframe=true,failure=true});run({afterframe=true,failure=true})
for _,r in pairs(regions)do run({badram=r.domain,failure=true});run({badram_after=r.domain,failure=true})end
run({heldA=true,failure=true});run({badcontroller=true,failure=true});run({badsize='IWRAM',failure=true})
run({badmeta=true,failure=true});run({badzip=true,failure=true})
run({advance_error=true,failure=true});run({advance_two=true,failure=true});run({finalsave=true,failure=true})
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    lua = (ROOT / 'tools/bizhawk_probe_gba_shoot_first_input.lua').read_bytes()
    launcher = (ROOT / 'build/run_gba_shoot_first_input_20261109.py').read_bytes()
    assert state.prior.sha(lua) == '32D7C0D83CC2C4C030A90D8A1F554FD38EF82637408DC017C9E7C556B55D457A'
    assert state.prior.sha(launcher) == 'DDC1E38B514032299FB7CA43EBFE8E421B58E9DEFB687FF9F1862196B2FECA01'
    rom = (ROOT / 'build/shoot-presentation-target-lifetime-20261109/component.gba').read_bytes()
    sys.path.insert(0, str(ROOT / 'vendor'))
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    contracts = {0x1190C: 'tst r0, #1', 0x11910: 'orrne r2, r2, #0x40',
                 0x11914: 'tst r0, #2', 0x11918: 'orrne r2, r2, #0x80',
                 0x119B4: 'eors r2, r2, r0', 0x119B8: 'and r0, r0, r2', 0x119BC: 'strh r0, [r8, #6]',
                 0x375138: 'strh r0, [r4, #0x2c]', 0x37513C: 'strh r1, [r4, #0x2e]'}
    for offset, expected in contracts.items():
        i = next(decoder.disasm(rom[offset:offset + 4], 0x08000000 + offset))
        assert i.mnemonic + ' ' + i.op_str == expected
    prefix = 'local PROBE="84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B"\nlocal regions={\n'
    for name, (domain, base) in dict(iwram=('IWRAM', 0x03000000), ewram=('EWRAM', 0x02000000), vram=('VRAM', 0x06000000), palette=('PALRAM', 0x05000000), oam=('OAM', 0x07000000)).items():
        b = (CAPTURE / ('13-healthy-activation-' + name + '.bin')).read_bytes()
        prefix += f"['{name}']={{domain='{domain}',base={base},data=" + literal(b) + '},\n'
    prefix += '}\nlocal metadata=' + literal((CAPTURE / 'healthy-activation.txt').read_bytes())
    prefix += '\nlocal checkpoint=' + literal((CAPTURE / 'healthy-activation.State').read_bytes()) + '\n'
    runner = types.FunctionType(host.execute.__code__, dict(host.__dict__, CHECK=host.CHECK.replace('m.regs.R15=a', 'm.regs.R15=a+4') + prefix), argdefs=host.execute.__defaults__)
    def run(text):
        runner(text, '', '', '', CHECK)
    run(lua.decode())
    controls = [('&0x40==0', '&1==0', 'wrong A mask'),
                ('keys.A=i==1', 'keys.A=i<=2', 'A held for two frames'),
                ('keys.A=i==1;joypad.set(keys)', 'keys.A=i==1;keys.B=true;joypad.set(keys)', 'B input introduced'),
                ('0x03001302,2),word(0x03001306,2)', '0x03003856,2),word(0x03003858,2)', 'WSC globals reused'),
                ('assert(savestate.save(out.."/restored.State",true)==true,"restore export failed")', 'savestate.save(out.."/restored.State",true)', 'failed restore export ignored')]
    rejected = []
    for old, new, label in controls:
        assert old in lua.decode()
        try:
            run(lua.decode().replace(old, new))
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError('first-input mutant accepted ' + label)
    code = launcher.decode()
    start, stop = code.index("rom = root / 'build/"), code.index("\nexe = root / 'local/")
    scope = dict(root=ROOT, sha=state.prior.sha, json=json, parse_checkpoint=state.parse_checkpoint,
                 checkpoint_core=state.checkpoint_core, prior=state.prior)
    exec(compile(code[start:stop], '@first-input-readonly-preflight', 'exec'), scope)
    report = dict(status='FIRST_NATIVE_A_INPUT_PROBE_LUA_PASS', lua_sha256=state.prior.sha(lua), launcher_sha256=state.prior.sha(launcher),
                  verifier_sha256=state.prior.sha(Path(__file__).read_bytes()), source_instruction_contracts=contracts,
                  A_mask=0x40, B_mask=0x80, global_held=0x03001302, global_edge=0x03001306,
                  FIRST_held_offset=0x2C, FIRST_edge_offset=0x2E, hook_registers='R4 actor/R3 selector/R0 held/R1 edge; R15=hook+4',
                  actual_lua_checks=['fresh A one frame, five releases, no B or write API; pre/store/post order',
                                     'load/save false/throw, five RAM before/after, frame/controller/heldA preconditions',
                                     'advance exception/two-frame advance/final save failure release all controls'],
                  semantic_mutations_rejected=rejected, actual_healthy_checkpoint_readonly_preflight_pass=True,
                  original_full_Core_failure_qualification_preserved=True, emulator_launched=False, real_state_loaded=False,
                  limits=['model of source input stores validates probe semantics; actual A acceptance/motion is future runtime evidence'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', state.prior.sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
