"""Verify the corrected AI journaling delta with the actual frozen Lua chain."""
import argparse
import json
from pathlib import Path
import struct
from types import FunctionType

import check_ai_producer_provenance as ai
import check_campaign_complete_probe as campaign
import check_type8_corrected_campaign as corrected
import check_type8_event_provenance as provenance
from verify_gba_shoot_entry_capture import sha


ROM = 'DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98'
PIN = '45490F604352C49539A73E54A9F7AE9FF1A2DDDDA8508A1C4BA28372B45085A4'
FIRE = r'''
   local function observe(at,values)
    for key,value in pairs(values)do regs[key]=value end
    if augmented then fire(at,values)else assert(not hooks[at])end
   end
   if progress==2 then
    pending_frame=function()
     local owner=0x03003D50
     observe(0x080C6D60,{R0=14,R4=q,R15=0x080C6D64})
     observe(0x080C6D70,{R0=9,R1=17,R15=0x080C6D74})
     observe(0x080C6D7C,{R8=0x08D88800,R1=153,R15=0x080C6D80})
     local first=get(0x08D88899,2)
     observe(0x080C6D84,{R8=0x03004D88,R0=first,R15=0x080C6D88})
     put(0x03004D8A,first,2)
     observe(0x080C6EB0,{R15=0x080C6EB4})
     put(0x03004D92,9*384,2)
     local action=get(0x08D88900+9*384+2*64,2)
     local src=0x08D89800+action*18
     local selector=get(src,2)
     put(0x03003D68,action,2)
     regs.R14=0x080C69B8;regs.R4=src+2;regs.R5=owner
     if augmented then bus_hooks[owner](owner,selector,0x2000)end
     put(owner,selector,2)
     observe(0x080C65EC,{R8=0x080C65F4,R5=selector,R15=0x080C65F0})
     observe(0x080C65F0,{R9=get(0x080C65F4+selector*4,4),R15=0x080C65F4})
     for _=1,140 do observe(0x080C65AC,{R15=0x080C65B0})end
     assert(not api.stopped(),'source row and valid target must continue')
     modeled_after_target=true
    end
   end
'''
AFTER = r'''
  assert(modeled_after_target and #writes==3 and #saves==0)
  local function encode(rows)
   local all={}
   for _,row in ipairs(rows)do
    local sorted={}
    for k,v in pairs(row)do sorted[#sorted+1]=tostring(k)..'='..tostring(v)end
    table.sort(sorted);all[#all+1]=table.concat(sorted,',')
   end
   return table.concat(all,';')
  end
  if not augmented then baseline={writes=encode(writes),inputs=encode(input_calls),files=files}
  else
   assert(baseline.writes==encode(writes) and baseline.inputs==encode(input_calls))
   for path,value in pairs(baseline.files)do assert(files[path]==value,path)end
   local rows={}
   local proof=assert(files[ai_path])
   for line in proof:gmatch('\nfirst (seq=[^\n]+)')do rows[#rows+1]=line end
   local clues={'raw_id=14','effective_id=9 stride=17','src=08D88899 halfword=02E4 row17=E40294000B14050A0E05090E0504050F0F',
                'dst=03004D8A','params_03004D88=','src=08D8A658 ordinal=00CC word=0008 bank=0D80',
                'selector=0008 index=08 table=080C65F4','pc=080C65F0 selector=0008 index=08'}
   assert(#rows==#clues)
   for i,clue in ipairs(clues)do assert(rows[i]:find(clue,1,true),rows[i])end
   assert(not proof:find('\nseq=9 ',1,true) and proof:find('\nseq=22 ',1,true),proof:sub(1,100))
  end
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    root = campaign.ROOT
    names = dict(parent='bizhawk_probe_campaign_complete.lua', predecessor='bizhawk_probe_type8_event_provenance.lua',
                 type8='bizhawk_probe_type8_corrected_campaign.lua', ai='bizhawk_probe_ai_producer_provenance.lua',
                 wrapper='bizhawk_probe_ai_corrected_campaign.lua')
    sources = {name: (root / 'tools' / name).read_bytes() for name in (*campaign.PINS, *names.values())}
    assert {name: sha(sources[name]) for name in campaign.PINS} == campaign.PINS
    assert [sha(sources[name]) for name in names.values()] == [campaign.WRAPPER, provenance.PIN, corrected.PIN, ai.PIN, PIN]
    sub = provenance.substitute
    parent = sources[names['parent']]
    adapted = sub(parent, campaign.ROM.encode(), ROM.encode())
    binding = b' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
    marker = b'  local f=assert(io.open(out.."/campaign-complete-done.txt","w"))'
    expected = sub(adapted, binding, binding + b'\n attach_ai_probe(observer)')
    expected = sub(expected, marker, b'  finish_ai_probe()\n' + marker)
    expected = sub(expected, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/character-ai-tables-v82-20261117/component.gba').read_bytes()
    assert sha(rom) == ROM
    hooks = provenance.HOOKS | ai.HOOKS
    for address, opcode in hooks.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD88899, 17), (0xD88900 + 9 * 384 + 2 * 64, 2), (0xD8A658, 18), (0xC65F4, 64)]
    quote = campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(sources[names["wrapper"]])}\n'
    setup += f'local instrumented_parent={quote(expected)}\nlocal romhash="{ROM}"\nlocal oldrom="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000 + at},data={quote(rom[at:at + n])}}}'
                                            for at, n in blocks) + '}\n'
    fixture = sub(ai.fixture(), ai.FIRE, FIRE)
    fixture = sub(fixture, ai.AFTER, AFTER)
    fixture = sub(fixture, f"assert(done==(augmented and '{ai.FAIL}' or 'bounded-no-activation')and old==done,done)",
                  "assert(done=='bounded-no-activation'and old==done,done)")
    check = campaign.host.lua_check
    FunctionType(check.__code__, dict(check.__globals__, CHECK=setup + fixture))('', '', '')
    report = dict(status='AI_CORRECTED_CAMPAIGN_LUA_QA_PASS', corrected_rom_sha256=ROM, wrapper_sha256=PIN,
                  unchanged_executable_hook_words=len(hooks), actual_effective_campaign_exact=True,
                  retained= ['raw AI ID14', 'normalized row9', 'parameter row 08D88899', 'action ordinal CC',
                             'valid index8 and target', 'first records survive journal rollover'],
                  no_additional_guest_or_input_operations=True, emulator_launched=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
