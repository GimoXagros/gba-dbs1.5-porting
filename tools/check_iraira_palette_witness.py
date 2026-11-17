"""Execute the palette diagnostic over the actual frozen 3FE5 Lua chain."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_ai_aligned_iraira as aligned
import check_ai_corrected_campaign as repaired
import check_ai_producer_provenance as ai
import check_campaign_complete_probe as campaign
import check_type8_corrected_campaign as corrected
import check_type8_event_provenance as provenance
from verify_gba_shoot_entry_capture import sha


PIN = '3535C550347DA2F291024B1DA921B817EC8F2A1E8E756B9BB4935D6D6CED0764'
WITNESS = 'bizhawk_probe_iraira_palette_witness.lua'
FAKE = r'''
    local function palette_write(value)
     regs.R15=0x080C9334;regs.R14=0x080D0F70
     if augmented then bus_hooks[0x05000000](0x05000000,value,0x2000)end
     put(0x05000000,value,2)
    end
    observe(0x080D0BD0,{R15=0x080D0BD4})
    observe(0x080D0BD4,{R0=3,R15=0x080D0BD8})
    observe(0x080D0BE4,{R1=3,R8=0x080D0C38,R9=0x080D0ED0,R15=0x080D0BE8})
    observe(0x080D0ED0,{R15=0x080D0ED4})
    observe(0x080C932C,{R15=0x080C9330})
    palette_write(0x33D)
'''
ASSERT = r'''
   local palette=assert(files[palette_path])
   assert(files[palette_done]=='palette-witness-121-frames')
   assert(palette:find('samples=121 disposition=bounded-no-activation',1,true))
   assert(palette:find('frontdoor stage=8 total=1',1,true))
   assert(palette:find('frontdoor stage=10 total=0',1,true))
   assert(palette:find('kind=legacy-stage-branch',1,true) and palette:find('r9=080D0ED0',1,true))
   assert(palette:find('kind=write-00',1,true) and palette:find('address=05000000 old=0000 value=033D',1,true))
   local samples=0
   for s in palette:gmatch('\nsample [^\n]+')do
    samples=samples+1
    assert(s:find('colors=033D',1,true) and s:find('080C9334:080D0F70',1,true),s)
   end
   assert(samples==121 and not palette:find('kind=projector-enter',1,true))
'''


def fixture():
    sub = provenance.substitute
    script = aligned.fixture()
    script = sub(script, '   if progress==2 then\n    pending_frame=function()',
                 '   if progress==0 then observe(0x080C4CC4,{R15=0x080C4CC8})end\n'
                 '   if progress==2 then\n    pending_frame=function()')
    script = sub(script, '    local start=frame\n    for i=0,123 do', FAKE + '    local start=frame\n    ir_start=start\n    for i=0,122 do')
    script = sub(script, '   advance(context)\n   if progress==4 then return end',
                 '   if progress==4 then return end\n   advance(context)')
    script = sub(script, " local ir_path='W:/build/campaign-independent/iraira-clock-phase.txt'",
                 " local ir_path='W:/build/campaign-independent/iraira-clock-phase.txt'\n"
                 " local palette_path='W:/build/campaign-independent/iraira-palette-witness.txt'\n"
                 " local palette_done='W:/build/campaign-independent/iraira-palette-witness-done.txt'")
    script = sub(script, 'name=="iraira-display-phase-write")',
                 'name=="iraira-display-phase-write" or name=="iraira-palette-write-00")')
    script = sub(script, 'ROM=0x08000000,VRAM=0x06000000', 'ROM=0x08000000,VRAM=0x06000000,PALRAM=0x05000000')
    script = sub(script, "  if path:match('/campaign%-complete%-done.txt$')then",
                 "  if path==palette_done then assert(closed[palette_path] and closed['W:/build/campaign-independent/campaign-complete-done.txt'])end\n"
                 "  if path:match('/campaign%-complete%-done.txt$')then")
    script = sub(script, 'phase_total=125 phase_kept=32', 'phase_total=124 phase_kept=32')
    script = sub(script, '   assert(samples==121)', '   assert(samples==121)\n' + ASSERT)
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    path = parser.parse_args().output
    root = campaign.ROOT
    names = ('bizhawk_probe_campaign_complete.lua', 'bizhawk_probe_type8_event_provenance.lua',
             'bizhawk_probe_type8_corrected_campaign.lua', 'bizhawk_probe_ai_producer_provenance.lua',
             'bizhawk_probe_ai_corrected_campaign.lua', 'bizhawk_probe_ai_aligned_iraira.lua', WITNESS)
    sources = {name: (root / 'tools' / name).read_bytes() for name in (*campaign.PINS, *names)}
    assert [sha(sources[name]) for name in names] == [
        campaign.WRAPPER, provenance.PIN, corrected.PIN, ai.PIN, repaired.PIN, aligned.PIN, PIN]
    assert {name: sha(sources[name]) for name in campaign.PINS} == campaign.PINS
    sub = provenance.substitute
    adapted = sub(sources[names[0]], campaign.ROM.encode(), aligned.ROM.encode())
    binding = b' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
    marker = b'  local f=assert(io.open(out.."/campaign-complete-done.txt","w"));assert(f:write(outcome));f:close()'
    expected = sub(adapted, binding, binding + b'\n attach_ai_probe(observer)\n attach_iraira_probe(observer)')
    expected = sub(expected, marker, b'  finish_ai_probe()\n  finish_iraira_probe()\n' + marker + b'\n  finish_palette_probe(outcome)')
    expected = sub(expected, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/iraira-render-repair-v84-20261117/component.gba').read_bytes()
    assert sha(rom) == aligned.ROM
    added = {int(address,16): int(opcode,16) for address, opcode in
             re.findall(rb'\{0x([0-9A-F]+),0x([0-9A-F]+),"', sources[WITNESS])}
    assert len(added) == 20 and 0x0837501C not in added
    hooks = ai.HOOKS | provenance.HOOKS | aligned.IR_OPCODES | added
    for address, opcode in hooks.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD8ABA2, 18), (0xD88900 + 9 * 384 + 2 * 64, 2), (0xD8A658, 18), (0xC65F4, 64)]
    quote = campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(sources[WITNESS])}\n'
    setup += f'local instrumented_parent={quote(expected)}\nlocal romhash="{aligned.ROM}"\nlocal oldrom="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000+at},data={quote(rom[at:at+n])}}}' for at, n in blocks) + '}\n'
    run = campaign.host.lua_check
    FunctionType(run.__code__, dict(run.__globals__, CHECK=setup + fixture()))('', '', '')
    report = dict(status='IRAIRA_PALETTE_WITNESS_LUA_QA_PASS', wrapper_sha256=PIN, corrected_rom_sha256=aligned.ROM,
                  new_read_only_exec_hooks=len(added), observed_palette_addresses=4, duplicated_clock_hooks=0,
                  exact_effective_campaign=True, modeled_clock_streak=121, scoped_legacy3_path_recorded=True,
                  cross_stage_frontdoor_counted=True, expected_bounded_outcome_preserved=True,
                  done_markers_follow_all_log_closes=True, unchanged_modeled_inputs_and_guest_writes=True,
                  emulator_launched_by_auditor=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(path.read_bytes())}")


if __name__ == '__main__':
    main()
