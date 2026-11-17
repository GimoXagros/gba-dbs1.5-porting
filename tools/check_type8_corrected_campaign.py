"""Exercise the corrected wrapper on Lua 5.4 with the actual composed scripts."""
import argparse
import json
from pathlib import Path
import struct
from types import FunctionType

import check_campaign_complete_probe as campaign
import check_type8_event_provenance as earlier
from verify_gba_shoot_entry_capture import sha


NEW = '75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F'
PIN = '844C896950AFFDB42B255CB843AEE8F2354A61237E0997506D0A74EAC81B00EC'
CORRECTED_FIRINGS = r'''
   local function observe(at,values)
    for key,value in pairs(values)do regs[key]=value end
    if augmented then fire(at,values)else assert(not hooks[at])end
   end
   local sp=0x03007E80
   put(q+0xF0,0x0861CF0C,4);put(q+0xBA,0x0C,2);put(0x03004D20,8,2)
   local function air_chain(record,event,subtype)
    put(0x03004D26,subtype,1)
    observe(0x0836EC90,{R5=q,CPSR=0})
    observe(0x0836F3B8,{R5=q,R1=0x08D3FE90})
    observe(0x0836F3CC,{R5=q,R1=record})
    observe(0x083555D0,{R4=q,R5=q+0xAC,R1=record,R14=0x0836F3E0})
    put(sp,event,4);put(sp+8,q+0xAC,4);put(sp+0x18,0x08355620,4)
    observe(0x08012874,{R13=sp,R14=0x08355620})
    observe(0x08012884,{R13=sp,R3=event,R5=q+0xAC,R4=0x0861CF0C})
    put(q+0xBA,event,2)
   end
   air_chain(0x0836C32C,0x16,1);advance(context)
   air_chain(0x0836C2CC,0x16,1);advance(context)
   for core=8667,8673 do
    assert(frame==core)
    observe(0x083525C4,{R4=q,R8=0x0836AAC0})
    if core==8672 then air_chain(0x0836C2AC,0x16,0)end
    advance(context)
   end
   for _=1,270 do observe(0x083525C4,{R4=q,R8=0x0836AAC0})end
   put(0x030048C8,q,4)
   pending_frame=function()fire(0x08353D24,{R0=8,R1=0x030048C8,R4=0x0861DA1C})end
'''
WINDOW_CHECK = r'''
   assert(closed[provenance_path] and proof:find('summary serial=295 core=8675',1,true),proof:sub(1,512))
   local rows={}
   for line in proof:gmatch('\n(seq=[^\n]+)')do rows[#rows+1]=line end
   assert(#rows==256 and rows[1]:find('^seq=40 ') and rows[#rows]:find('^seq=295 '))
   assert(proof:find('first-window frames=8667..8673 count=13',1,true))
   local fixed=0
   for core in proof:gmatch('\nfirst seq=%d+ core=(%d+)')do
    fixed=fixed+1;assert(tonumber(core)>=8667 and tonumber(core)<=8673)
   end
   assert(fixed==13 and proof:find('first-chain count=6',1,true))
   local chain={}
   for line in proof:gmatch('\nchain (seq=[^\n]+)')do chain[#chain+1]=line end
   local ordered={'conditional_NE=true literal=08D3FE90','id=13 table=08D3FE90 indexed=0836C2AC subtype=1',
                  'record=00160000,0836AAC0,033C0000','lr=0836F3E0','selected=00000016',
                  'selected=00000016 saved_lr=08355620 table=0861CF14'}
   assert(#chain==#ordered)
   for index,token in ipairs(ordered)do
    assert(chain[index]:find('core=8666',1,true) and chain[index]:find(token,1,true),chain[index])
   end
  end
'''


def fixture():
    sub = earlier.substitute
    script = earlier.composed_fixture()
    compare = earlier.COMPARISON.split('   assert(closed[provenance_path]', 1)[0]
    compare = compare.replace('#saves==1', '#saves==0')
    script = sub(script, earlier.COMPARISON, compare + WINDOW_CHECK)
    script = sub(script, earlier.FIRINGS, CORRECTED_FIRINGS)
    script = sub(script, " local case='retained-type-failure'", " local case='bounded'")
    script = sub(script, ' local frame,inside_hook,exited=100,false,false',
                 ' local frame,inside_hook,exited=8665,false,false')
    script = sub(script, "   advance(context)\n   if case=='typed-refusal'",
                 "   advance(context)\n   if case=='bounded' then return end\n   if case=='typed-refusal'")
    script = sub(script, "  if name=='@frozen-campaign-with-readonly-provenance'then assert(code==instrumented_parent)end",
                 "  if name=='@frozen-campaign-with-readonly-provenance'then assert(code==instrumented_parent)end\n"
                 "  if name=='@frozen-provenance-corrected-rom'then assert(code:find(romhash,1,true) and not code:find(oldrom,1,true))end")
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    root = campaign.ROOT
    wrapper = (root / 'tools/bizhawk_probe_type8_corrected_campaign.lua').read_bytes()
    predecessor = (root / 'tools/bizhawk_probe_type8_event_provenance.lua').read_bytes()
    parent = (root / 'tools/bizhawk_probe_campaign_complete.lua').read_bytes()
    assert (sha(wrapper), sha(predecessor), sha(parent)) == (PIN, earlier.PIN, campaign.WRAPPER)
    sources = {name: (root / 'tools' / name).read_bytes() for name in campaign.PINS}
    assert {name: sha(data) for name, data in sources.items()} == campaign.PINS
    sources['bizhawk_probe_campaign_complete.lua'] = parent
    sources['bizhawk_probe_type8_event_provenance.lua'] = predecessor
    adapted = earlier.substitute(parent, campaign.ROM.encode(), NEW.encode())
    with_finish = earlier.substitute(adapted, b'  log:close()', b'  log:close();finish_provenance()')
    rom = (root / 'build/character-type8-tables-r2-20261117/component.gba').read_bytes()
    assert sha(rom) == NEW
    for address, opcode in earlier.HOOKS.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in earlier.HOOKS]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0x36F7B8, 4), (0xD3FE90, 56), (0x36C2AC, 128), (0x36C32C, 32), (0x61CF0C, 16),
               (0x61D074, 16), (0x61D274, 16)]
    quote = campaign.quote
    setup = f'local wrapper={quote(adapted)}\nlocal provenance={quote(wrapper)}\n'
    setup += f'local instrumented_parent={quote(with_finish)}\nlocal romhash="{NEW}"\nlocal oldrom="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000 + at},data={quote(rom[at:at + length])}}}'
                                            for at, length in blocks) + '}\n'
    check = campaign.host.lua_check
    FunctionType(check.__code__, dict(check.__globals__, CHECK=setup + fixture()))('', '', '')
    report = dict(status='TYPE8_CORRECTED_CAMPAIGN_LUA_QA_PASS', wrapper_sha256=PIN,
                  corrected_rom_sha256=NEW, predecessor_sha256=earlier.PIN, campaign_parent_sha256=campaign.WRAPPER,
                  actual_parent_with_exact_rom_and_finish_delta=True,
                  added_guest_writes=0, added_input_calls=0, modeled_file_changes=['type8-event-provenance.txt'],
                  fixed_window_preserved=True, first_dynamic_qualifying_chain_core=8666, first_dynamic_subtype=1,
                  earlier_wrong_record_refused=True, later_matching_chain_did_not_replace_first=True,
                  retained_after_legacy_ring_rollover=True, all_eight_hook_words_verified=True,
                  old_full_suites_rerun=False, dynamic_arm_provenance_observed=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
