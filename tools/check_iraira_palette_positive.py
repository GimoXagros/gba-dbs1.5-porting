"""Verify the positive 574F palette witness composes the frozen diagnostic unchanged."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_iraira_palette_witness as old
from verify_gba_shoot_entry_capture import sha


ROM = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
PIN = '9043796D65B29758EDEB21692748D97C70040C10CCFA7EC97FDF451D3F4B9681'
WRAPPER = 'bizhawk_probe_iraira_palette_positive.lua'
POSITIVE = r'''
    local function palette_write(address,value,pc)
     regs.R15=pc+8;regs.R14=0x08D8B742
     if augmented and bus_hooks[address]then bus_hooks[address](address,value,0x2000)end
     put(address,value,2)
    end
    observe(0x080D0BD0,{R15=0x080D0BD4})
    observe(0x08377928,{R15=0x0837792C,R0=0,R8=0x05000000})
    palette_write(0x05000000,0,0x08377928)
    observe(0x080C4CC4,{R15=0x080C4CC8})
    observe(0x08D8AF40,{R15=0x08D8AF44})
    observe(0x08D8AF60,{R15=0x08D8AF64,CPSR=0x40000010})
    observe(0x08D8AD00,{R15=0x08D8AD04})
    local groups={{0,11,0x42,0x08D8AD5C},{0x80,6,0x62,0x08D8AD8C},
                  {0xC0,7,0x82,0x08D8ADBC},{0x130,7,0xA2,0x08D8ADEC},{0x190,7,0xC2,0x08D8AE1C}}
    for _,g in ipairs(groups)do
     for i=0,g[2]-1 do
      local address,value=0x05000000+g[3]+2*i,get(0x08584200+g[1]+2*i,2)
      observe(g[4],{R15=g[4]+4,R0=value,R2=address})
      palette_write(address,value,g[4])
     end
    end
    observe(0x08D8AE2C,{R15=0x08D8AE30})
'''
VERIFY = r'''
   local palette=assert(files[palette_path])
   assert(files[palette_done]=='palette-witness-121-frames')
   assert(palette:find('samples=121 disposition=bounded-no-activation',1,true))
   assert(palette:find('frontdoor stage=8 total=1',1,true))
   assert(palette:find('frontdoor stage=10 total=1',1,true))
   assert(not palette:find('kind=legacy-stage-branch',1,true))
   assert(not palette:find('kind=retail-stage3-handler',1,true))
   assert(not palette:find('kind=retail-gradient-backdrop',1,true))
   assert(palette:find('count kind=projector-enter total=1',1,true))
   assert(palette:find('count kind=projector-exit total=1',1,true))
   for _,part in ipairs({{'42',11},{'62',6},{'82',7},{'A2',7},{'C2',7}})do
    assert(palette:find('count kind=source-store-'..part[1]..' total='..part[2]..' ',1,true))
   end
   assert(palette:find('address=05000000 old=0000 value=0000',1,true))
   assert(palette:find('address=05000082 old=0000 value=7F77',1,true))
   local samples=0
   for s in palette:gmatch('\nsample [^\n]+')do
    samples=samples+1
    assert(s:find('colors=0000,4400,7F77,0011',1,true),s)
   end
   assert(samples==121)
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('output', type=Path)
    path = p.parse_args().output
    root = old.campaign.ROOT
    names = ('bizhawk_probe_campaign_complete.lua', 'bizhawk_probe_type8_event_provenance.lua',
             'bizhawk_probe_type8_corrected_campaign.lua', 'bizhawk_probe_ai_producer_provenance.lua',
             'bizhawk_probe_ai_corrected_campaign.lua', 'bizhawk_probe_ai_aligned_iraira.lua', old.WITNESS, WRAPPER)
    sources = {name: (root / 'tools' / name).read_bytes() for name in (*old.campaign.PINS, *names)}
    assert [sha(sources[name]) for name in names] == [
        old.campaign.WRAPPER, old.provenance.PIN, old.corrected.PIN, old.ai.PIN, old.repaired.PIN, old.aligned.PIN, old.PIN, PIN]
    assert {name: sha(sources[name]) for name in old.campaign.PINS} == old.campaign.PINS
    sub = old.provenance.substitute
    adapted = sub(sources[names[0]], old.campaign.ROM.encode(), ROM.encode())
    binding = b' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
    marker = b'  local f=assert(io.open(out.."/campaign-complete-done.txt","w"));assert(f:write(outcome));f:close()'
    expected = sub(adapted, binding, binding + b'\n attach_ai_probe(observer)\n attach_iraira_probe(observer)')
    expected = sub(expected, marker, b'  finish_ai_probe()\n  finish_iraira_probe()\n' + marker + b'\n  finish_palette_probe(outcome)')
    expected = sub(expected, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/iraira-outer-palette-v86-20261117/component.gba').read_bytes()
    assert sha(rom) == ROM
    added = {int(a, 16): int(w, 16) for a, w in re.findall(rb'\{0x([0-9A-F]+),0x([0-9A-F]+),"', sources[old.WITNESS])}
    assert added[0x080D0BD0] == 0xEB12CF8A
    added[0x080D0BD0] = 0xEB32EA9A
    pins = added | old.ai.HOOKS | old.provenance.HOOKS | old.aligned.IR_OPCODES
    for address, opcode in pins.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in pins]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD8ABA2, 18), (0xD88900 + 9 * 384 + 2 * 64, 2), (0xD8A658, 18), (0xC65F4, 64), (0x584200, 512)]
    quote = old.campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(sources[WRAPPER])}\n'
    setup += f'local instrumented_parent={quote(expected)}\nlocal romhash="{ROM}"\nlocal oldrom="{old.campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000+at},data={quote(rom[at:at+n])}}}'
                                            for at, n in blocks) + '}\n'
    body = sub(old.fixture(), old.FAKE, POSITIVE)
    body = sub(body, old.ASSERT, VERIFY)
    body = sub(body, 'name=="iraira-palette-write-00")', 'name:match("^iraira%-palette%-write%-"))')
    run = old.campaign.host.lua_check
    FunctionType(run.__code__, dict(run.__globals__, CHECK=setup + body))('', '', '')
    report = dict(status='IRAIRA_PALETTE_POSITIVE_LUA_QA_PASS', wrapper_sha256=PIN, rom_sha256=ROM,
                  inherited_diagnostic_hooks=len(added), changed_diagnostic_opcode='080D0BD0',
                  old_campaign_buttons_and_writes_equal=True, exact_effective_campaign=True,
                  no_new_game_operations=True, bounded_diagnostic_samples=121, modeled_projector_colors=38,
                  modeled_legacy3_dispatch_calls=0, emulator_launched=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(path.read_bytes())}")


if __name__ == '__main__':
    main()
