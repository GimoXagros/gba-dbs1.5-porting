"""Narrow actual-Lua no-frame roundtrip control and read-only host preflight."""
import argparse
import json
from pathlib import Path
import struct
import types
import zlib

import verify_gba_shoot_entry_replay as replay
import verify_gba_shoot_entry_capture_v2 as state
from verify_gba_shoot_entry_guard_delta import literal

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    control = (ROOT / 'tools/bizhawk_gba_checkpoint_roundtrip_control.lua').read_bytes()
    loader = (ROOT / 'tools/bizhawk_replay_gba_shoot_entry.lua').read_bytes()
    host_bytes = (ROOT / 'build/run_gba_checkpoint_roundtrip_20261109.py').read_bytes()
    assert state.prior.sha(control) == '592083E4C310E48AED75DA08E992821E0CC0B7BE6EF69625CD660AE20ABC45F5'
    assert state.prior.sha(loader) == 'A73E59919E77FCA67A2DAE6EEA214E1571604818F05008B405CB919300E2C397'
    assert state.prior.sha(host_bytes) == '5AA85E58C28217D5C5605F27951E338E9922BE5E2F2631767EA18C90F86936B0'
    assert state.prior.sha(Path(replay.__file__).read_bytes()) == 'FC5652C31F03149219C133447CCCFB26D4090A6A4F1F9C711232638D0C942C74'
    fixture = replay.CHECK[:replay.CHECK.index('local m=run();')]
    fixture = fixture.replace('  local text\n', '''  local text
  if path=='W:/tools/bizhawk_replay_gba_shoot_entry.lua'then
   text=replay_source
   if o.anchor=='missing'then text=text:gsub('local module=read','local missing_module=read')end
   if o.anchor=='duplicate'then text=text..'\\nlocal module=read("W:/tools/bizhawk_gba_shoot_entry_observer.lua")\\n'end
  elseif path=='W:/tools/bizhawk_gba_shoot_entry_observer.lua'or path=='W:/tools/bizhawk_probe_gba_shoot_entry.lua'then
   error('policy dependency read forbidden in control')
  end
''')
    start = fixture.index("  assert(m.inputs[1].frame==64230")
    stop = fixture.index('\n end\n return m\nend', start)
    fixture = fixture[:start] + '''  assert(m.advances==0 and #m.inputs==0 and next(m.hooks)==nil,'no frame/input/hook in control')
  assert(m.state_saves==1 and m.files[base..'restored.State'],'one immediate proof state')
  assert(m.files[base..'shoot-entry-done.txt']=='checkpoint-roundtrip-only','control success marker')
  assert(#m.files[base..'loaded-rom.bin']==0x800000,'loaded ROM proof')
''' + fixture[stop:]
    fixture += '''
run()
for _,mode in ipairs({'false','throw'})do run({loadmode=mode,failure=true});run({savemode=mode,failure=true})end
run({badframe=true,failure=true});run({afterframe=true,failure=true})
for _,r in pairs(regions)do run({badram=r.domain,failure=true});run({badram_after=r.domain,failure=true})end
run({anchor='missing',early=true});run({anchor='duplicate',early=true})
'''
    prefix = 'local replay_source=' + literal(loader) + '\nlocal regions={\n'
    for name, (domain, base) in dict(iwram=('IWRAM', 0x03000000), ewram=('EWRAM', 0x02000000), vram=('VRAM', 0x06000000), palette=('PALRAM', 0x05000000), oam=('OAM', 0x07000000)).items():
        b = (replay.CAPTURE / ('05-stage7-checkpoint-' + name + '.bin')).read_bytes()
        prefix += f"['{name}']={{domain='{domain}',base={base},data=" + literal(b) + '},\n'
    prefix += '}\nlocal metadata=' + literal((replay.CAPTURE / 'stage7-hp1.txt').read_bytes())
    prefix += '\nlocal state=' + literal((replay.CAPTURE / 'stage7-hp1.State').read_bytes()) + '\n'
    runner = types.FunctionType(replay.prior.execute.__code__, dict(replay.prior.__dict__, CHECK=replay.prior.CHECK + prefix), argdefs=replay.prior.execute.__defaults__)
    def run(text):
        runner(text, '', '', '', fixture)
    run(control.decode())
    negatives = []
    for before, after, name in [
        ('source=source:sub(1,cut-1)..source:sub(tail)', 'source=source', 'policy tail retained'),
        ('loaded-rom.bin', 'wrong-rom.bin', 'loaded ROM evidence omitted'),
        (';client.exit()end', ';end', 'success exit omitted')]:
        assert control.decode().count(before) == 1
        try:
            run(control.decode().replace(before, after))
        except ValueError:
            negatives.append(name)
        else:
            raise AssertionError('control mutation accepted')
    code = host_bytes.decode()
    start, stop = code.index("rom = root / 'build/"), code.index("\nexe = root / 'local/")
    scope = dict(root=ROOT, sha=state.prior.sha, json=json, parse_checkpoint=state.parse_checkpoint,
                 checkpoint_core=state.checkpoint_core, prior=state.prior)
    exec(compile(code[start:stop], '@roundtrip-readonly-preflight', 'exec'), scope)
    fixed, _ = state.checkpoint_core((ROOT / 'build/bizhawk-gba-shoot-entry-replay-20261109-a/restored.State').read_bytes())
    assert state.prior.sha(fixed) == '42448E25FAF97F523C2FDEFA26C64B6E71414ABC424F937A5B31EB3B9809D72E'
    expected = bytearray(fixed)
    struct.pack_into('<I', expected, 12, zlib.crc32(scope['rom_data']))
    report = dict(status='NO_FRAME_SAME_ROM_CONTROL_LUA_PASS', control_sha256=state.prior.sha(control),
                  launcher_sha256=state.prior.sha(host_bytes), verifier_sha256=state.prior.sha(Path(__file__).read_bytes()),
                  actual_lua_checks=['exact reviewed prefix extraction; no module/driver read, hook/input/frame',
                                     'load/save false/throw; frame and all five RAM pre/post mismatch rejection',
                                     'missing/duplicate extraction anchor rejection; immediate done and exit'],
                  semantic_mutations_rejected=negatives, actual_readonly_D0_checkpoint_preflight_pass=True,
                  expected_D0_control_Core_sha256_if_patch_independent=state.prior.sha(bytes(expected)),
                  comparison_buffer_only_CRC_interval=[12, 16], original_strict_Core_failure_preserved=True,
                  emulator_launched=False, state_loaded=False,
                  limits=['positive control remains to run; matching post-load states would isolate patch independence, not original exact restoration'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', state.prior.sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
