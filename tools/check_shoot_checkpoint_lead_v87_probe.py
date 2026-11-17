"""Run the input-only lead wrapper through all frozen terminal observer fixtures."""
import argparse
import json
import re
import struct
from pathlib import Path
from types import FunctionType
import check_shoot_checkpoint_aim_v87_probe as prior


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    a = p.parse_args()
    assert not a.report.exists()
    sources = {name: (prior.ROOT / 'tools' / name).read_bytes() for name in prior.PINS}
    assert {name: prior.sha(data) for name, data in sources.items()} == prior.PINS
    probe = (prior.ROOT / 'tools/bizhawk_probe_gba_shoot_checkpoint_lead_v87.lua').read_bytes()
    before, after = re.findall(rb'\[=\[(.*?)\]=\]', probe, re.S)
    old = sources[prior.PROBE].replace(b'\r\n', b'\n')
    assert old.count(before) == 1
    expected = old.replace(before, after)
    fixture = prior.FIXTURE
    old_put = 'local function put(at,v,n)for i=0,n-1 do mem[at+i]=(v>>(i*8))&255 end end'
    new_put = 'local function put(at,v,n)for i=0,n-1 do mem[at+i]=(v>>(i*8))&255 end;if at==q+0x34 or at==q+0x36 then for i=0,n-1 do mem[at+4+i]=(v>>(i*8))&255 end end end'
    assert fixture.count(old_put) == fixture.count('put(q+0x36,5568,2)') == 1
    fixture = fixture.replace(old_put, new_put).replace('put(q+0x36,5568,2)', 'put(q+0x36,5216,2)')
    fixture = fixture.replace('env.load=function(code,name,mode,scope)',
                              'env.load=function(code,name,mode,scope)\n if name=="@shoot-checkpoint-event57-lead"then assert(code==expected)end')
    rom = (prior.ROOT / 'build/shoot-child-contact-20261117/component.gba').read_bytes()
    assert prior.sha(rom) == prior.ROM
    words = {int(at, 16): int(op, 16) for at, op in re.findall(rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', sources[prior.TAIL])}
    words |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF}
    assert len(words) == 25 and all(struct.unpack_from('<I', rom, at - 0x08000000)[0] == op for at, op in words.items())
    setup = 'local cases={' + ','.join('"' + c + '"' for c in prior.CASES) + '}\n'
    setup += f'local probe={prior.quote(probe)}\nlocal expected={prior.quote(expected)}\nlocal romhash="{prior.ROM}"\n'
    setup += 'local success="shoot-checkpoint-aim-terminal-results-title"\n'
    setup += 'local sources={' + ','.join(f'[{prior.quote(n.encode())}]={prior.quote(v)}' for n, v in sources.items()) + '}\n'
    setup += 'local words={' + ','.join(f'[{at}]={op}' for at, op in words.items()) + '}\n'
    execute = prior.host.lua_check
    FunctionType(execute.__code__, dict(execute.__globals__, CHECK=setup + fixture))('', '', '')
    report = dict(status='SHOOT_CHECKPOINT_LEAD_LUA_PASS', probe_sha256=prior.sha(probe),
                  effective_source_sha256=prior.sha(expected), frozen_inputs=prior.PINS,
                  cases=prior.CASES, opcode_sites=25, replacements=1,
                  unchanged='All restore, ownership, sole HP1 write, real hit and terminal gates',
                  fixture_change='Stationary targets with previous=current positions and dy=-160',
                  limits=['Lua fixtures only; predictive input is not a guaranteed collision',
                          'Actual event57 timing and rectangle proof are a separate prerequisite'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], prior.sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
