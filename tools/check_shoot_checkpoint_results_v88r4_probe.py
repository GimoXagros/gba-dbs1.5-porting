"""Run the source result-chain wrapper through all frozen terminal observer fixtures."""
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
    probe = (prior.ROOT / 'tools/bizhawk_probe_gba_shoot_checkpoint_results_v88r4.lua').read_bytes()
    before, after = re.findall(rb'\[=\[(.*?)\]=\]', probe, re.S)[:2]
    old = sources[prior.PROBE].replace(b'\r\n', b'\n')
    assert old.count(before) == 1
    expected = old.replace(before, after)
    expected = expected.replace(prior.ROM.encode(), b'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C')
    expected = expected.replace(b'mode~=7 and mode~=8 and mode~=11 and mode~=20 and mode~=3',
                                b'mode~=7 and mode~=8 and mode~=12 and mode~=13 and mode~=11 and mode~=20 and mode~=3')
    inject = re.search(rb'\[==\[(.*?)\]==\]', probe, re.S).group(1)
    if inject.startswith(b'\n'):
        inject = inject[1:]
    key = b' local start=assert(s:find("local function finish(outcome)",1,true))'
    assert expected.count(key) == 1
    expected = expected.replace(key, inject)
    expected = expected.replace(b"MAX_FRAMES=89405,1800,8000", b"MAX_FRAMES=89405,1800,16000")
    fixture = prior.FIXTURE
    old_put = 'local function put(at,v,n)for i=0,n-1 do mem[at+i]=(v>>(i*8))&255 end end'
    new_put = 'local function put(at,v,n)for i=0,n-1 do mem[at+i]=(v>>(i*8))&255 end;if at==q+0x34 or at==q+0x36 then for i=0,n-1 do mem[at+4+i]=(v>>(i*8))&255 end end end'
    assert fixture.count(old_put) == fixture.count('put(q+0x36,5568,2)') == 1
    fixture = fixture.replace(old_put, new_put).replace('put(q+0x36,5568,2)', 'put(q+0x36,5216,2)')
    fixture = fixture.replace('env.load=function(code,name,mode,scope)',
                              'env.load=function(code,name,mode,scope)\n if name=="@shoot-checkpoint-source-results-route"then assert(code==expected)end')
    romhash = 'E21275218BEF6E4DDE08DB9EA64C2A0D925D102A265373A48BDFD1046A0C338C'
    rom = (prior.ROOT / 'build/shoot-stage11-results-route-20261117-r2/component.gba').read_bytes()
    assert prior.sha(rom) == romhash
    words = {int(at, 16): int(op, 16) for at, op in re.findall(rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', sources[prior.TAIL])}
    words |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF,
              0x080BBC24: 0xE92D403F, 0x080BD8E8: 0xE8BD0020,
              0x080CA24C: 0xE92D403F, 0x080CBCC0: 0xE8BD0020, 0x080CA39C: 0xE8BD0020, 0x080C1018: 0xE59F50D0, 0x080C10CC: 0xEBFD43D7}
    assert len(words) == 32 and all(struct.unpack_from('<I', rom, at - 0x08000000)[0] == op for at, op in words.items())
    old_route = '''  elseif get(mode,2)==8 then
   fire(0x0808A524)
   if keys.A then assert(core-result_age>=120);native_mode(11);fire(0x080BF1D0);ending_age=core end'''
    new_route = '''  elseif get(mode,2)==8 then
   assert(not keys.A and not keys.B);native_mode(12);fire(0x080BBC24)
  elseif get(mode,2)==12 then
   for _,v in pairs(keys)do assert(not v,"mode12 remains neutral")end
   put(0x0201D29C,0,2);fire(0x080BD8E8)
   native_mode(13);fire(0x080CA24C)
  elseif get(mode,2)==13 then
   for _,v in pairs(keys)do assert(not v,"mode13 remains neutral")end
   put(0x03003DA2,22,2);put(0x03004270,0x3F,2)
   fire(0x080CA39C);native_mode(11);fire(0x080BF1D0);ending_age=core'''
    assert fixture.count(old_route) == 1
    fixture = fixture.replace(old_route, new_route)
    fixture = fixture.replace('"results-constructor","result-ready","ending-entry"',
                              '"results-constructor","mode12-constructor","mode12-request","mode13-constructor","mode13-normal-request","ending-entry"')
    old_card = "  elseif get(mode,2)==11 then\n   fire(0x080C0050)"
    new_card = """  elseif get(mode,2)==11 then
   if core==ending_age+1 then fire(0x080C0050)end
   active(owner,true);put(owner,0x080C0F40,4);put(0x0300133C,owner,4)
   put(owner+0x20,1,2);put(owner+0x22,75,2);fire(0x080C1018,{R1=owner+0x18})"""
    assert fixture.count(old_card)==1
    fixture=fixture.replace(old_card,new_card)
    old_transition="assert(core-ending_age>=120);native_mode(20);fire(0x08040448)"
    new_transition="assert(core-ending_age>=120);put(0x03002314,1,2);put(0x03002316,0,2);put(0x03002318,0,2);fire(0x080C10CC);native_mode(20);fire(0x08040448)"
    assert fixture.count(old_transition)==1
    fixture=fixture.replace(old_transition,new_transition)
    assert fixture.count("put(owner+4,0xF100,4)")==1
    fixture=fixture.replace("put(owner+4,0xF100,4)","put(owner+4,0xFFFFF100,4)")
    setup = 'local cases={' + ','.join('"' + c + '"' for c in prior.CASES) + '}\n'
    setup += f'local probe={prior.quote(probe)}\nlocal expected={prior.quote(expected)}\nlocal romhash="{romhash}"\n'
    setup += 'local success="shoot-checkpoint-aim-terminal-results-title"\n'
    setup += 'local sources={' + ','.join(f'[{prior.quote(n.encode())}]={prior.quote(v)}' for n, v in sources.items()) + '}\n'
    setup += 'local words={' + ','.join(f'[{at}]={op}' for at, op in words.items()) + '}\n'
    execute = prior.host.lua_check
    FunctionType(execute.__code__, dict(execute.__globals__, CHECK=setup + fixture))('', '', '')
    report = dict(status='SHOOT_SOURCE_RESULTS_CHAIN_LUA_PASS', probe_sha256=prior.sha(probe),
                  effective_source_sha256=prior.sha(expected), frozen_inputs=prior.PINS,
                  cases=prior.CASES, opcode_sites=32, parent_replacements=5,
                  unchanged='All restore, ownership, sole HP1 write, real hit and terminal gates',
                  fixture_change='Stationary targets with previous=current positions and dy=-160',
                  limits=['Lua fixtures only; no actual native mode12/13 game execution',
                          'Positive native autonomous exit proof is separate CC39F151'])
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(report['status'], prior.sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
