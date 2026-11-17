"""Exercise the combined AI/Iraira observation delta with the real Lua scripts."""
import argparse
import json
from pathlib import Path
import struct
from types import FunctionType

import check_ai_corrected_campaign as repaired
import check_ai_producer_provenance as ai
import check_campaign_complete_probe as campaign
import check_type8_corrected_campaign as corrected
import check_type8_event_provenance as provenance
from verify_gba_shoot_entry_capture import sha


ROM = '3FE5CF45072E6277FACD74515B95CD883109135935F5D6B9994F9372FE80B77F'
PIN = 'C32E0C08B82F5EBC805387C25990B6FC9C4C0A6056E84412D020A83266872860'
IR_OPCODES = {0x0837501C: 0xE59F8150, 0x08375018: 0xE1C890B0, 0x08D8AF8C: 0xE1C100B0,
              0x086283A4: 0xE1C010B0, 0x086283AC: 0xE1C320B0}
IR_FIXTURE = r'''
   if progress==4 then
    local addr=0x03002568
    local function phase(value,pc)
     regs.R15=pc
     if augmented then bus_hooks[addr](addr,value,0x2000)end
     put(addr,value,2)
    end
    put(addr,2,2);phase(0,0x08D8AF94)
    local start=frame
    for i=0,123 do
     pending_frame=function()
      phase((i%2==0) and 2 or 0,0x086283B4)
      put(0x03004500,7199-i,2)
      observe(0x0837501C,{R8=i==1 and 0x03004502 or 0x03004500,R9=7199-i,R15=0x08375020})
     end
     advance(context)
    end
    ir_start=start
   end
'''
IR_ASSERT = r'''
   local ir=assert(files[ir_path])
   local head=ir:match('^[^\n]+')
   assert(head:find('phase_total=125 phase_kept=32 clock_observed=122 clock_streak=121 guest_writes=none input=frozen-parent',1,true),head)
   assert(ir:find('role=init-clear pc=08D8AF94 address=03002568 old=0002 value=0000',1,true))
   assert(ir:find('role=display-toggle pc=086283B4 address=03002568 old=0000 value=0002',1,true))
   assert(ir:find('role=display-toggle pc=086283B4 address=03002568 old=0002 value=0000',1,true))
   local samples=0
   for core,value in ir:gmatch('\nclock core=(%d+) value=(%d+) owner=03004500')do
    assert(tonumber(core)==ir_start+2+samples and tonumber(value)==7197-samples)
    samples=samples+1
   end
   assert(samples==121)
'''


def fixture():
    sub = provenance.substitute
    script = ai.fixture()
    corrected_ai = repaired.FIRE
    for old, new in (('R1=17,','R1=18,'), ('R8=0x08D88800,R1=153','R8=0x08D8AB00,R1=162'),
                     ('get(0x08D88899,2)','get(0x08D8ABA2,2)')):
        corrected_ai = sub(corrected_ai, old, new)
    script = sub(script, ai.FIRE, corrected_ai + IR_FIXTURE)
    compare = repaired.AFTER.replace('#writes==3', '#writes==5')
    compare = sub(compare, 'effective_id=9 stride=17','effective_id=9 stride=18')
    compare = sub(compare, 'src=08D88899 halfword=02E4','src=08D8ABA2 halfword=02E4')
    compare = compare.rsplit('  end', 1)[0] + IR_ASSERT + '  end\n'
    script = sub(script, ai.AFTER, compare)
    script = sub(script, '   if progress==2 then return end', '   if progress==4 then return end')
    script = sub(script, ' local bus_hooks,modeled_after_target={},false',
                 ' local bus_hooks,modeled_after_target,ir_start={},false,nil')
    script = sub(script, " local ai_path='W:/build/campaign-independent/ai-producer-provenance.txt'",
                 " local ai_path='W:/build/campaign-independent/ai-producer-provenance.txt'\n local ir_path='W:/build/campaign-independent/iraira-clock-phase.txt'")
    script = sub(script, 'name=="ai-producer-selector-write"',
                 '(name=="ai-producer-selector-write" or name=="iraira-display-phase-write")')
    script = sub(script, 'closed[provenance_path] and closed[ai_path]',
                 'closed[provenance_path] and closed[ai_path] and closed[ir_path]')
    script = sub(script, 'path==provenance_path or path==ai_path',
                 'path==provenance_path or path==ai_path or path==ir_path')
    script = sub(script, f"assert(done==(augmented and '{ai.FAIL}' or 'bounded-no-activation')and old==done,done)",
                 "assert(done=='bounded-no-activation'and old==done,done)")
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    root = campaign.ROOT
    names = ('bizhawk_probe_campaign_complete.lua', 'bizhawk_probe_type8_event_provenance.lua',
             'bizhawk_probe_type8_corrected_campaign.lua', 'bizhawk_probe_ai_producer_provenance.lua',
             'bizhawk_probe_ai_corrected_campaign.lua', 'bizhawk_probe_ai_aligned_iraira.lua')
    sources = {name: (root / 'tools' / name).read_bytes() for name in (*campaign.PINS, *names)}
    assert {name: sha(sources[name]) for name in campaign.PINS} == campaign.PINS
    assert [sha(sources[name]) for name in names] == [campaign.WRAPPER, provenance.PIN, corrected.PIN, ai.PIN, repaired.PIN, PIN]
    sub = provenance.substitute
    adapted = sub(sources[names[0]], campaign.ROM.encode(), ROM.encode())
    binding = b' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
    marker = b'  local f=assert(io.open(out.."/campaign-complete-done.txt","w"))'
    expected = sub(adapted, binding, binding + b'\n attach_ai_probe(observer)\n attach_iraira_probe(observer)')
    expected = sub(expected, marker, b'  finish_ai_probe()\n  finish_iraira_probe()\n' + marker)
    expected = sub(expected, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/iraira-render-repair-v84-20261117/component.gba').read_bytes()
    assert sha(rom) == ROM
    hooks = provenance.HOOKS | ai.HOOKS | IR_OPCODES
    for address, opcode in hooks.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    assert struct.unpack_from('<I', rom, 0xC6D6C)[0] == 0xE3A01012
    assert rom[0xD8ABA2:0xD8ABB4] == bytes.fromhex('E40294000B14050A0E05090E0504050F0F00')
    blocks = [(address - 0x08000000, 4) for address in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD8ABA2, 18), (0xD88900 + 9 * 384 + 2 * 64, 2), (0xD8A658, 18), (0xC65F4, 64)]
    quote = campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(sources[names[-1]])}\n'
    setup += f'local instrumented_parent={quote(expected)}\nlocal romhash="{ROM}"\nlocal oldrom="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000 + at},data={quote(rom[at:at + n])}}}'
                                            for at, n in blocks) + '}\n'
    check = campaign.host.lua_check
    FunctionType(check.__code__, dict(check.__globals__, CHECK=setup + fixture()))('', '', '')
    report = dict(status='AI_ALIGNED_IRAIRA_LUA_QA_PASS', rom_sha256=ROM, wrapper_sha256=PIN,
                  exact_effective_campaign=True, unchanged_original_hook_words=16, new_pinned_words=len(IR_OPCODES),
                  source_aligned_parameter_row9=True, modeled_phase_clear_and_alternation=True,
                  valid_clock_streak=121, wrong_owner_resets_streak=True,
                  observer_no_additional_guest_writes=True, original_buttons_and_files_equal=True,
                  old_full_suites_rerun=False, emulator_launched=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
