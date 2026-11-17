"""Preflight the read-only type8 provenance wrapper against the frozen campaign."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_campaign_complete_probe as campaign
from verify_gba_shoot_entry_capture import sha


PIN = 'E999477CB5D5A72E64B46DCC6F24838BF4D2447B221A3E018DB88B15BC467523'
HOOKS = {
    0x08012874: 0xE92D403F,
    0x08012884: 0xE1C530BE,
    0x083555D0: 0xE92D4008,
    0x083525C4: 0xE12FFF18,
    0x0836A69C: 0xE92D4013,
    0x0836EC90: 0x159F1B20,
    0x0836F3B8: 0xE5D50011,
    0x0836F3CC: 0xE92D0010,
}
FIRINGS = r'''
   local function observe(at,values)
    for key,value in pairs(values)do regs[key]=value end
    if augmented then fire(at,values)else assert(not hooks[at])end
   end
   local sp=0x03007E80
   put(q+0xF0,0x0861CF0C,4)
   put(q+0xBA,0x0C,2)
   -- These four callbacks must all be excluded from the 277-event count.
   observe(0x083525C4,{R4=p})
   active(q,false);observe(0x083525C4,{R4=q});active(q,true)
   put(q+0x10,0,1);observe(0x083525C4,{R4=q});put(q+0x10,1,1)
   put(q+0x18,p+4,4);observe(0x083525C4,{R4=q});put(q+0x18,p,4)
   for _=1,270 do observe(0x083525C4,{R4=q,R8=0x0836A744})end
   put(0x03004D20,8,2)
   observe(0x0836EC90,{R5=q,CPSR=0})
   observe(0x0836F3B8,{R5=q,R1=0x0836BED4})
   observe(0x0836F3CC,{R5=q,R1=0x0836C32C})
   observe(0x083555D0,{R4=q,R5=q+0xAC,R1=0x0836C32C,R14=0x0836F3E0})
   put(sp,0x36,4);put(sp+8,q+0xAC,4)
   observe(0x08012874,{R13=sp,R14=0x08355620})
   put(sp+0x18,0x08355620,4);put(0x02010600,0x0861D1B4,4)
   observe(0x08012884,{R13=sp,R3=0x36,R5=q+0xAC,R4=0x02010600})
   put(q+0xBA,0x36,2)
   put(sp,10,4);put(sp+8,0x0836AF64,4);put(sp+0x10,q,4)
   observe(0x0836A69C,{R13=sp})
   put(0x030048C8,q,4)
   pending_frame=function()fire(0x08353D24,{R0=0x8070,R1=0x030048C8,R4=0xE59F80D4})end
'''
COMPARISON = r'''
  assert(#writes==1 and writes[1].stage==8 and writes[1].value==999 and #saves==1)
  local function encode(rows)
   local all={}
   for _,row in ipairs(rows)do
    local sorted={}
    for key,value in pairs(row)do sorted[#sorted+1]=tostring(key)..'='..tostring(value)end
    table.sort(sorted);all[#all+1]=table.concat(sorted,',')
   end
   return table.concat(all,';')
  end
  if not augmented then
   baseline={files=files,inputs=encode(input_calls),writes=encode(writes),saves=table.concat(saves,',')}
  else
   for path,value in pairs(baseline.files)do assert(files[path]==value,'frozen output changed: '..path)end
   for path in pairs(files)do assert(path==provenance_path or baseline.files[path],'unexpected output: '..path)end
   assert(encode(input_calls)==baseline.inputs and encode(writes)==baseline.writes and table.concat(saves,',')==baseline.saves, 'host side effect mismatch')
   local proof=assert(files[provenance_path])
   assert(closed[provenance_path] and proof:find('summary serial=277 core=101 timing=before-instruction',1,true), proof:sub(1,512))
   local rows={}
   for line in proof:gmatch('seq=[^\n]+')do rows[#rows+1]=line end
   assert(#rows==256 and rows[1]:find('^seq=22 ') and rows[#rows]:find('^seq=277 '), tostring(#rows)..' '..tostring(rows[1])..' / '..tostring(rows[#rows]))
   local tail={{'type8-air-selector','conditional_NE=true literal=0836BED4'},
               {'damage-table-entry','id=13 table=0836BED4 indexed=0836C32C subtype=0'},
               {'damage-record-selected','record=00360000,0836AE94'},
               {'metadata-entry','lr=0836F3E0'}, {'setter-entry','selected=00000036'},
               {'event-store','selected=00000036 saved_lr=08355620 table=0861D1B4'},
               {'hitstop-entry','event=0036'}}
   for i,item in ipairs(tail)do
    local row=rows[#rows-#tail+i]
    assert(row:find('kind='..item[1]..' ',1,true) and row:find(item[2],1,true),row)
   end
  end
'''


def substitute(script, old, new):
    assert script.count(old) == 1, old
    return script.replace(old, new, 1)


def composed_fixture():
    original = campaign.CHECK
    old_cases, rest = original.split("for _,case in ipairs(cases)do", 1)
    assert old_cases.lstrip().startswith('local cases=')
    old_rows = old_cases[old_cases.index("local first="):]
    script = old_rows + "local baseline\nfor _,augmented in ipairs({false,true})do\n local case='retained-type-failure'" + rest
    edits = [
        (" local regs={};", " local pending_frame\n local regs={CPSR=0};"),
        ("frameadvance=function()assert(not inside_hook);frame=frame+1 end", "frameadvance=function()assert(not inside_hook);if pending_frame then pending_frame();pending_frame=nil end;frame=frame+1 end"),
        ("inside_hook=true;hooks[at]();inside_hook=false", "inside_hook=true;local ok,why=pcall(hooks[at]);inside_hook=false;assert(ok,tostring(why))"),
        (" local frame,inside_hook,exited=100,false,false",
         " local frame,inside_hook,exited=100,false,false\n local provenance_path='W:/build/campaign-independent/type8-event-provenance.txt'"),
        ("  if path:match('/campaign%-complete%-done.txt$')then",
         "  if path:match('/campaign%-complete%-done.txt$')then\n   if augmented then assert(closed[provenance_path])end"),
        ("  function f:write(s)assert(not self.closed);files[path]=files[path]..s;return self end",
         "  function f:write(s)assert(not self.closed);if path==provenance_path then assert(not inside_hook and closed['W:/build/campaign-independent/campaign-complete-trace.txt'])end;files[path]=files[path]..s;return self end"),
        ("self.closed=true;closed[path]=true end", "self.closed=true;closed[path]=true;return true end"),
        ("   if case=='retained-type-failure'then fire(0x0836E370,{R0=0xE5,R4=0x030048C8})end", FIRINGS),
        ("  local compiled=assert(load(code,name,mode,context));effective[name]=code",
         "  local compiled=assert(load(code,name,mode,context));effective[name]=code\n"
         "  if name=='@frozen-campaign-with-readonly-provenance'then assert(code==instrumented_parent)end"),
        ("local ok,err=pcall(assert(load(wrapper,'@new-campaign-wrapper','t',env)))",
         "local ok,err=pcall(assert(load(augmented and provenance or wrapper,'@new-campaign-wrapper','t',env)))"),
        ("done=='failure:invalid-overlap-type'and old==done", "done=='failure:first-invalid-producer'and old==done"),
        ("  assert(exited and #input_calls>0 and captures>0", COMPARISON + "  assert(exited and #input_calls>0 and captures>0"),
    ]
    for old, new in edits:
        script = substitute(script, old, new)
    return script


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    output = parser.parse_args().output
    root = campaign.ROOT
    provenance = (root / 'tools/bizhawk_probe_type8_event_provenance.lua').read_bytes()
    parent = (root / 'tools/bizhawk_probe_campaign_complete.lua').read_bytes()
    assert sha(provenance) == PIN and sha(parent) == campaign.WRAPPER
    assert not re.search(rb'\b(?:(?:memory|mainmemory)\.write|savestate\.|emu\.setregister|joypad\.|client\.)', provenance)
    declared = {int(at, 16): int(opcode, 16) for at, opcode in re.findall(rb'hook\(0x([0-9A-F]+),0x([0-9A-F]+),', provenance)}
    assert declared == HOOKS
    insertion = b'  log:close();finish_provenance()'
    compiled_parent = substitute(parent, b'  log:close()', insertion)
    assert substitute(compiled_parent, insertion, b'  log:close()') == parent
    sources = {name: (root / 'tools' / name).read_bytes() for name in campaign.PINS}
    assert {name: sha(raw) for name, raw in sources.items()} == campaign.PINS
    sources['bizhawk_probe_campaign_complete.lua'] = parent
    rom = (root / 'build/campaign-stage-progression-v80-20261117-r2/component.gba').read_bytes()
    assert sha(rom) == campaign.ROM
    for address, opcode in HOOKS.items():
        assert struct.unpack_from('<I', rom, address - 0x08000000)[0] == opcode
    blocks = [(address - 0x08000000, 4) for address in HOOKS]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0x36F7B8, 4), (0x36BED4, 56), (0x36C32C, 32), (0x61D514, 16)]
    quote = campaign.quote
    setup = f'local wrapper={quote(parent)}\nlocal provenance={quote(provenance)}\n'
    setup += f'local instrumented_parent={quote(compiled_parent)}\nlocal romhash="{campaign.ROM}"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    setup += 'local romblocks={' + ','.join(f'{{at={0x08000000 + at},data={quote(rom[at:at + length])}}}'
                                            for at, length in blocks) + '}\n'
    check = campaign.host.lua_check
    FunctionType(check.__code__, dict(check.__globals__, CHECK=setup + composed_fixture()))('', '', '')
    report = dict(status='TYPE8_EVENT_PROVENANCE_LUA_QA_PASS', wrapper_sha256=PIN, parent_sha256=campaign.WRAPPER,
                  campaign_driver_observer_collision_hashes=campaign.PINS, rom_sha256=campaign.ROM,
                  exact_parent_inverse=True, parent_driver_observer_collision_composed=True,
                  added_guest_writes=0, added_input_calls=0, baseline_mock_files_equal=True,
                  active_actor_filters=['wrong register', 'inactive actor', 'wrong role', 'broken reciprocal owner'],
                  retained_ring_rows=256, model_events=277, journal_closed_before_campaign_completion=True,
                  verified_rom_hook_words={f'{address:08X}': f'{opcode:08X}' for address, opcode in HOOKS.items()},
                  emulator_launched=False, dynamic_arm_provenance_observed=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['status']} {sha(output.read_bytes())}")


if __name__ == '__main__':
    main()
