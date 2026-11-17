"""Exercise the fresh v88 campaign wrapper with the existing six terminal fixtures."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_campaign_wholeplay_v86 as prior

ROOT = prior.ROOT
ROM = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    a = p.parse_args()
    assert not a.report.exists()
    pins = json.loads((ROOT / 'build/wholeplay-v88-reviewed-pins-20261117.json').read_bytes())
    sources = {Path(path).name: (ROOT / path).read_bytes() for path in pins}
    assert {path: prior.sha((ROOT / path).read_bytes()) for path in pins} == pins
    assert prior.sha(sources[prior.WRAPPER]) == prior.PIN
    wrapper = sources['bizhawk_probe_campaign_wholeplay_v88.lua']
    parent = sources[prior.WRAPPER].replace(b'\r\n', b'\n')
    replacements = re.findall(rb'once\(\[=\[(.*?)\]=\],\[=\[(.*?)\]=\]\)', wrapper, re.S)
    assert len(replacements) == 1
    before, after = replacements[0]
    assert parent.count(before) == 1
    expected = parent.replace(before, after).replace(prior.ROM.encode(), ROM.encode())
    hook_old = b' hook(0x080BF1D0,0xE92D403B,"ending-entry",function(r)'
    hook_new = re.search(rb"once\(' hook\(0x080BF1D0.*?,\[=\[(.*?)\]=\]\)", wrapper, re.S).group(1).lstrip(b'\n')
    assert expected.count(hook_old) == 1
    expected = expected.replace(hook_old, hook_new).replace(
        b'require_fact(result_mode,"ending-before-results",r)',
        b'require_fact(result_mode and seen["mode13-request"],"ending-before-mode13-exit",r)')
    fixture = prior.fixture()
    def once(old, new):
        nonlocal fixture
        assert fixture.count(old) == 1, old
        fixture = fixture.replace(old, new)
    once(' local function advance(context)context.joypad.set({});context.emu.frameadvance()end',
         ' local function advance(context)put(q+0x38,get(q+0x34,2),2);put(q+0x3A,get(q+0x36,2),2);context.joypad.set({});context.emu.frameadvance()end')
    once('put(q+0x36,0x1C0,2)', 'put(q+0x36,0x60,2)')
    once('  for _=1,120 do fire(0x0808A524);advance(context);assert(not pressed(\'A\'))end\n  fire(0x0808A524);advance(context);assert(pressed(\'A\'))\n  native_mode(11)',
         '''  native_mode(12);fire(0x080BBC24)
  for _=1,20 do advance(context);assert(not pressed('A') and not pressed('B'))end
  put(0x0201D29C,0,2);put(0x03002314,1,2);put(0x03002316,0,2);put(0x03002318,0,2)
  fire(0x080BD8E8);native_mode(13);fire(0x080CA24C)
  for _=1,20 do advance(context);assert(not pressed('A') and not pressed('B'))end
  fire(0x080CBCC0);native_mode(11)''')
    once("'result-ready','ending-entry'", "'mode12-constructor','mode12-request','mode13-constructor','mode13-request','ending-entry'")
    # Capture the wrapper's expansion before the existing nested execution checks.
    marker = 'env.load=function(code,name,mode,context)'
    once(marker, marker + '\n  if name=="@wholeplay-v88-source-results-and-input"then assert(code==expected)end')
    rom = (ROOT / 'build/shoot-stage11-results-route-20261117-r2/component.gba').read_bytes()
    assert prior.sha(rom) == ROM
    indexed = {int(x, 16): int(y, 16) for x, y in re.findall(rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', expected)}
    indexed |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF}
    assert len(indexed) == 29
    hooks = prior.base.ai.HOOKS | prior.base.provenance.HOOKS | prior.base.aligned.IR_OPCODES | indexed
    assert all(struct.unpack_from('<I', rom, at-0x08000000)[0] == op for at, op in hooks.items())
    blocks = [(at-0x08000000, 4) for at in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD8ABA2, 18), (0xD88900+9*384+2*64, 2), (0xD8A658, 18), (0xC65F4, 64)]
    quote = prior.base.campaign.quote
    setup = f'local provenance={quote(wrapper)}\nlocal expected={quote(expected)}\nlocal romhash="{ROM}"\nlocal oldrom="{prior.base.campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(n.encode())}]={quote(v)}' for n, v in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000+at},data={quote(rom[at:at+n])}}}' for at, n in blocks) + '}\n'
    run = prior.base.campaign.host.lua_check
    FunctionType(run.__code__, dict(run.__globals__, CHECK=setup+fixture))('', '', '')
    result = dict(status='WHOLEPLAY_V88_LUA_PASS', wrapper_sha256=prior.sha(wrapper),
                  effective_source_sha256=prior.sha(expected), component_sha256=ROM,
                  checksum_bound_exec_sites=29, cases=6, pins=pins,
                  unchanged_pre_shoot_driver=True, sole_stage11_hp1_word=True,
                  source_result_mode_sequence=[8, 12, 13, 11, 20, 3], actual_emulator=False)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf8', newline='\n')
    print(result['status'], prior.sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
