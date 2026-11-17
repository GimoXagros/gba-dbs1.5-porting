"""Exercise the read-only AI journal with the actual frozen 75BD script chain."""
import argparse
import json
from pathlib import Path
import struct
from types import FunctionType

import check_campaign_complete_probe as campaign
import check_type8_corrected_campaign as corrected
import check_type8_event_provenance as provenance
from verify_gba_shoot_entry_capture import sha


PIN = '4A2AE9672BAF2C1BC53EE3B8A6F891DCB66B7EE77C0163966CA2F123F15C4C30'
HOOKS = {0x080C6D60: 0xE350000B, 0x080C6D70: 0xE0010190, 0x080C6D7C: 0xE19100B8,
         0x080C6D84: 0xE1C800B2, 0x080C6EB0: 0xE3A00000, 0x080C65AC: 0xE92D4020,
         0x080C65EC: 0xE7989105, 0x080C65F0: 0xE12FFF19}
FAIL = 'failure:first-invalid-ai-collider-target'

FIRE = r'''
   local function observe(at,values)
    for key,value in pairs(values)do regs[key]=value end
    if augmented then fire(at,values)else assert(not hooks[at])end
   end
   if progress==1 then observe(0x080C6D60,{R0=1})end
   if progress==2 then
    pending_frame=function()
     local owner=0x03003D50
     local function set_selector(value)
      if augmented then bus_hooks[owner](owner,value,0x2000)end
      put(owner,value,2)
     end
     observe(0x080C6D60,{R0=14,R4=q,R15=0x080C6D64})
     observe(0x080C6D70,{R0=14,R1=17,R15=0x080C6D74})
     observe(0x080C6D7C,{R8=0x080C6C7C,R1=238,R15=0x080C6D80})
     local first=get(0x080C6D6A,2)
     observe(0x080C6D84,{R8=0x03004D88,R0=first,R15=0x080C6D88})
     put(0x03004D8A,first,2)
     observe(0x080C6EB0,{R15=0x080C6EB4})
     for _=1,140 do observe(0x080C65AC,{R15=0x080C65B0})end
     set_selector(2)
     observe(0x080C65EC,{R8=0x080C65F4,R5=2,R15=0x080C65F0})
     observe(0x080C65F0,{R9=get(0x080C65FC,4),R15=0x080C65F4})
     assert(not api.stopped(),'valid native selector must continue')
     set_selector(15)
     observe(0x080C65EC,{R8=0x080C65F4,R5=15,R15=0x080C65F0})
     observe(0x080C65F0,{R9=0xE3A00000,R15=0x080C65F4})
     assert(api.stopped()==augmented)
     modeled_after_target=true
    end
   end
'''
AFTER = r'''
  assert(modeled_after_target and #writes==3)
  local function to_string(rows)
   local all={}
   for _,row in ipairs(rows)do
    local which={}
    for k,v in pairs(row)do which[#which+1]=tostring(k)..'='..tostring(v)end
    table.sort(which);all[#all+1]=table.concat(which,',')
   end
   return table.concat(all,';')
  end
  if not augmented then
   baseline={writes=to_string(writes),inputs=to_string(input_calls)}
  else
   assert(#saves==1 and baseline.writes==to_string(writes) and baseline.inputs==to_string(input_calls))
   local proof=assert(files[ai_path])
   assert(proof:find('serial=151 guest_writes=none input=frozen-parent',1,true),proof:sub(1,96))
   local first={}
   for row in proof:gmatch('\nfirst (seq=[^\n]+)')do first[#first+1]=row end
   local matches={'raw_id=14','effective_id=14 stride=17','src=080C6D6A','dst=03004D8A',
                  'params_03004D88=','address=03003D50 old=0002 value=000F'}
   assert(#first==#matches)
   for i,x in ipairs(matches)do assert(first[i]:find(x,1,true),first[i])end
   local rows={}
   for line in proof:gmatch('\n(seq=[^\n]+)')do rows[#rows+1]=line end
   assert(#rows==128 and rows[1]:find('^seq=24 ') and rows[#rows]:find('^seq=151 '))
   assert(rows[#rows]:find('pc=080C65F0 selector=000F index=0F table=080C65F4 slot=080C6630 word=E3A00000 target=E3A00000',1,true))
   assert(files['W:/build/campaign-independent/shoot-entry-first-failure.txt']:find('timing=before-instruction',1,true))
  end
'''


def fixture():
    sub = provenance.substitute
    script = corrected.fixture()
    comparison = provenance.COMPARISON.split('   assert(closed[provenance_path]', 1)[0]
    comparison = comparison.replace('#saves==1', '#saves==0')
    script = sub(script, comparison + corrected.WINDOW_CHECK, AFTER)
    script = sub(script, corrected.CORRECTED_FIRINGS, FIRE)
    script = sub(script, "   if case=='bounded' then return end", '   if progress==2 then return end')
    script = sub(script, " local frame,inside_hook,exited=8665,false,false",
                 " local frame,inside_hook,exited=100,false,false\n local bus_hooks,modeled_after_target={},false")
    script = sub(script, " local provenance_path='W:/build/campaign-independent/type8-event-provenance.txt'",
                 " local provenance_path='W:/build/campaign-independent/type8-event-provenance.txt'\n"
                 " local ai_path='W:/build/campaign-independent/ai-producer-provenance.txt'")
    script = sub(script, 'on_bus_write=function()end',
                 'on_bus_write=function(callback,address,name)if name=="ai-producer-selector-write" then bus_hooks[address]=callback end end')
    script = sub(script, 'if augmented then assert(closed[provenance_path])end',
                 'if augmented then assert(closed[provenance_path] and closed[ai_path])end')
    script = sub(script, "if path==provenance_path then assert(not inside_hook",
                 "if path==provenance_path or path==ai_path then assert(not inside_hook")
    script = sub(script, "elseif case=='bounded'or case=='typed-refusal'then assert(done=='bounded-no-activation'and old==done)",
                 f"elseif case=='bounded'then assert(done==(augmented and '{FAIL}' or 'bounded-no-activation')and old==done,done)")
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    root = campaign.ROOT
    parent = (root / 'tools/bizhawk_probe_campaign_complete.lua').read_bytes()
    prior = (root / 'tools/bizhawk_probe_type8_event_provenance.lua').read_bytes()
    repaired = (root / 'tools/bizhawk_probe_type8_corrected_campaign.lua').read_bytes()
    wrapper = (root / 'tools/bizhawk_probe_ai_producer_provenance.lua').read_bytes()
    assert [sha(raw) for raw in (parent, prior, repaired, wrapper)] == [campaign.WRAPPER, provenance.PIN, corrected.PIN, PIN]
    sources = {name: (root / 'tools' / name).read_bytes() for name in campaign.PINS}
    assert {name: sha(blob) for name, blob in sources.items()} == campaign.PINS
    sources['bizhawk_probe_campaign_complete.lua'] = parent
    sources['bizhawk_probe_type8_event_provenance.lua'] = prior
    sources['bizhawk_probe_type8_corrected_campaign.lua'] = repaired
    adapted = provenance.substitute(parent, campaign.ROM.encode(), corrected.NEW.encode())
    binding = b' observer=assert(load(code,"@frozen-shoot-observer-16MiB","t",module_env))()'
    marker = b'  local f=assert(io.open(out.."/campaign-complete-done.txt","w"))'
    expected = provenance.substitute(adapted, binding, binding + b'\n attach_ai_probe(observer)')
    expected = provenance.substitute(expected, marker, b'  finish_ai_probe()\n' + marker)
    expected = provenance.substitute(expected, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/character-type8-tables-r2-20261117/component.gba').read_bytes()
    assert sha(rom) == corrected.NEW
    hooks = provenance.HOOKS | HOOKS
    for address, opcode in hooks.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xC6D6A, 17), (0xC65F4, 64)]
    quote = campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(wrapper)}\n'
    setup += f'local instrumented_parent={quote(expected)}\nlocal romhash="{corrected.NEW}"\nlocal oldrom="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000 + at},data={quote(rom[at:at + length])}}}'
                                            for at, length in blocks) + '}\n'
    check = campaign.host.lua_check
    FunctionType(check.__code__, dict(check.__globals__, CHECK=setup + fixture()))('', '', '')
    report = dict(status='AI_PRODUCER_PROVENANCE_LUA_QA_PASS', wrapper_sha256=PIN,
                  corrected_rom_sha256=corrected.NEW, frozen_corrected_wrapper_sha256=corrected.PIN,
                  ordered_first_parameter_facts=5, old_and_new_selector_write_retained=True,
                  ring_rows=128, scope_refusal=True, valid_selector_continues=True,
                  invalid_target_stops_through_frozen_observer=True, modeled_post_hook_executes=True,
                  input_and_authorized_writes_match=True, runtime_game_or_arm_executed=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
