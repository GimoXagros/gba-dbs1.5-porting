"""Execute the actual nested whole-play Lua with adversarial terminal fixtures."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

import check_iraira_palette_witness as base
from verify_gba_shoot_entry_capture import ROOT, sha


WRAPPER = 'bizhawk_probe_campaign_wholeplay_v86.lua'
PIN = '66B9BB23039FDF1B7441559990E5FBCF227DF66F5026820F5A06DB1E45B27594'
ROM = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
SUCCESS = 'campaign-shoot-terminal-results-title'
TAIL = r'''
 local function continue_tail(context)
  local function native_mode(next_mode)
   regs.R15=0x0801597C
   bus_hooks[0x03002310](0x03002310,next_mode,0x2000)
   put(0x03002310,next_mode,2)
  end
  local function pressed(key)
   return input_calls[#input_calls][key]==true
  end
  local header=owner-0x18
  local n=#writes
  put(p,0x0835620C,4);put(p+0xB4,0,2)
  put(p+0x34,0x200,2);put(p+0x36,0x100,2)
  put(q+0x34,0x300,2);put(q+0x36,0x1C0,2)
  put(q+0xBA,1,2);put(q+0x64,37,2)
  assert(#writes==n and files[root..'healthy-activation.txt'])
  if case=='typed-refusal'then put(q+0x28,aux+4,4);advance(context);return end
  advance(context);assert(pressed('Right') and not pressed('B') and #writes==n)
  put(p+0xB4,0x4000,2);put(q+0x34,0x201,2)
  advance(context);assert(not pressed('B') and #writes==n)
  put(q+0x34,0x300,2);put(p+0x2C,0x80,2)
  advance(context);assert(not pressed('B') and #writes==n)
  put(p+0x2C,0,2);put(q+0xBA,2,2)
  advance(context);assert(not pressed('B') and #writes==n)
  put(q+0xBA,1,2)
  advance(context);assert(pressed('B') and #writes==n+1 and get(q+0x64,2)==1)
  assert(writes[n+1].stage==11 and get(p+0x64,2)==100 and get(p+0x66,2)==0)
  advance(context);assert(pressed('B') and #writes==n+1)
  local function lethal()
   fire(0x0836E5E4,{R4=p,R5=q,R8=case=='bad-hit' and 0xFFFF or 0,R0=1})
   if case=='bad-hit'then return end
   put(q+0x64,0,2)
   fire(0x0836E5E8,{R4=p,R5=q})
   fire(0x085CD960,{R4=p,R5=q})
   put(q,0x085BDD00,4);put(aux,0x085BF204,4)
   fire(0x0836E604,{R4=p,R5=aux,R0=q})
   fire(0x083736B0,{R4=p,R5=q})
   fire(0x0833FD08,{R8=0x086FC300})
  end
  pending_frame=lethal
  advance(context)
  assert(not api.stopped() and #writes==n+1)
  pending_frame=function()
   put(0x0300133C,header,4);put(header+4,0xFF0,4);active(owner,true)
   fire(0x085CD000);fire(0x085CD340);fire(0x085CD740)
   fire(0x08340C54);active(owner,false)
   put(0x03002314,1,2);put(0x0300475E,1,1)
   fire(0x08340CA8)
  end
  advance(context);assert(not pressed('B'))
  native_mode(8)
  fire(0x080897AC)
  for _=1,120 do fire(0x0808A524);advance(context);assert(not pressed('A'))end
  fire(0x0808A524);advance(context);assert(pressed('A'))
  native_mode(11)
  fire(0x080BF1D0)
  for _=1,120 do fire(0x080C0050);advance(context);assert(not pressed('A'))end
  fire(0x080C0050);advance(context);assert(pressed('A'))
  native_mode(20)
  fire(0x08040448)
  advance(context);assert(not pressed('A'))
  active(owner,true);put(header+4,0xF100,4);put(header,0x0804074C,4)
  put(0x03004738,0x102,2);fire(0x0804071C)
  fire(0x08040608,{R9=0x03002310})
  native_mode(3)
  put(header+4,0x1000,4);put(header,0x08090C7C,4)
  pending_frame=function()fire(0x08090C7C)end
  advance(context)
 end
'''
VERIFY = r'''
 local done=files[root..'wholeplay-done.txt']
 if case=='missing-stage11-approval' or case=='wrong-ROM'then
  assert(not ok and not done and #writes==0 and #input_calls==0)
 else
  assert(ok,tostring(err))
  local expected={complete='campaign-shoot-terminal-results-title',bounded='bounded-wholeplay-incomplete',
                  ['typed-refusal']='failure:wholeplay-live-aim-owner',['bad-hit']='failure:wholeplay-unqualified-stage11-damage'}
  assert(done==expected[case]..'\n',case..' actual '..tostring(done))
  local campaign_done=files[root..'campaign-complete-done.txt']
  assert(campaign_done==expected[case] and files[root..'shoot-entry-done.txt']==expected[case])
  assert(exited and captures>0)
  for _,pressed in pairs(input_calls[#input_calls])do assert(not pressed,'final input release')end
  local eff=effective['@frozen-shoot-entry-driver']
  local a,b=assert(eff:find('\n if select_wholeplay_input(keys,mode)then return end',1,true))
  assert(eff:sub(1,a-1)..eff:sub(b+1)==sources['bizhawk_probe_gba_shoot_entry.lua'])
  if case=='complete'then
   assert(#writes==12 and #saves==2)
   local trace=files[root..'wholeplay-trace.txt'];local before=1
   for _,event in ipairs({'healthy','stage11-hp1','hit-pre','hit-post','fatal-adapter','fatal-pair','root5','case5',
    'terminal-entry','terminal-middle','terminal-final','cleanup-entry','cleanup-request','results-constructor',
    'result-ready','ending-entry','ending-ready','mode20-entry','mode20-art','mode20-return-request','title-ready'})do
    local at=assert(trace:find('event='..event..' ',before,true));before=at+1
   end
   local ledger=files[root..'wholeplay-stage11-writes.txt']
   assert(ledger:find('bytes=2 before=37 requested=1',1,true) and ledger:find('after=1 verified=true',1,true))
   local modes=files[root..'wholeplay-mode-writes.txt'];assert(modes:find('old=20 new=3',1,true))
  elseif case=='typed-refusal'then
   assert(#writes==11 and not files[root..'wholeplay-stage11-writes.txt'])
  elseif case=='bad-hit'then
   assert(#writes==12 and not files[root..'wholeplay-trace.txt']:find('event=hit-post ',1,true))
  else
   assert(#writes==11 and #saves==1 and not files[root..'wholeplay-stage11-writes.txt'])
  end
 end
end
'''


def fixture():
    sub = base.provenance.substitute
    source = base.aligned.fixture()
    source = sub(source, "for _,augmented in ipairs({false,true})do\n local case='bounded'",
                 "for _,case in ipairs({'complete','bounded','typed-refusal','bad-hit','missing-stage11-approval','wrong-ROM'})do\n"
                 " local augmented=true\n local root='W:/build/campaign-independent/'")
    source = sub(source, "  elseif key=='boss_authorization'", "  elseif key=='stage11_boss_authorization'then return "
                 "case=='missing-stage11-approval' and 'bad' or 'user-approved-development-stage11-boss-hp1-once'\n"
                 "  elseif key=='boss_authorization'")
    source = sub(source, 'assert(not hooks[at]);hooks[at]=fn end',
                 'local prior=hooks[at];hooks[at]=prior and function()prior();fn()end or fn end')
    source = sub(source, 'name=="iraira-display-phase-write")', 'name=="iraira-display-phase-write" or name=="wholeplay-mode-write")')
    source = sub(source, "or(stage==7 and a==q+0x64", "or((stage==7 or stage==11) and a==q+0x64")
    source = sub(source, "return{read=function()return sources[name]end,close=function()end}",
                 "return{read=function()return sources[name]end,close=function()return true end}")
    source = sub(source, "  assert(mode=='w'or mode=='wb'or mode=='a')",
                 "  if mode=='ab'then mode='a'end\n"
                 "  if path==root..'wholeplay-done.txt'then\n"
                 "   assert(closed[root..'campaign-complete-done.txt'] and closed[root..'shoot-entry-done.txt'])\n"
                 "   for name,is_closed in pairs(closed)do assert(is_closed,'open journal '..name)end\n"
                 "  end\n"
                 "  assert(mode=='w'or mode=='wb'or mode=='a')")
    source = sub(source, " local function loop(context)", TAIL + "\n local function loop(context)")
    source = sub(source, "   if case=='typed-refusal'then put(q+0x18,p+1,4)end\n", "")
    source = sub(source, "   if progress==4 then return end\n", "")
    source = sub(source, "   if case=='typed-refusal'then assert(#writes==0,'actual pair refusal guards assisted write');return end\n", "")
    source = sub(source, "put(0x0300231E,11,1);boss(11);put(0x0300450A,4,2)",
                 "put(0x0300231E,11,1);boss(11);put(q+0x64,37,2);put(0x0300450A,4,2)")
    source = sub(source, "  activate(context)", "  activate(context)\n  continue_tail(context)")
    source = sub(source, "  if name=='@frozen-campaign-with-readonly-provenance'then assert(code==instrumented_parent)end\n", "")
    source = sub(source, "augmented and provenance or wrapper", "provenance")
    return source.split(" if case=='wrong-ROM'or case=='missing-authorization'then", maxsplit=1)[0] + VERIFY


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    names = ('bizhawk_probe_campaign_complete.lua', 'bizhawk_probe_type8_event_provenance.lua',
             'bizhawk_probe_type8_corrected_campaign.lua', 'bizhawk_probe_ai_producer_provenance.lua',
             'bizhawk_probe_ai_corrected_campaign.lua', 'bizhawk_probe_ai_aligned_iraira.lua', WRAPPER)
    pins = (base.campaign.WRAPPER, base.provenance.PIN, base.corrected.PIN, base.ai.PIN, base.repaired.PIN,
            base.aligned.PIN, PIN)
    sources = {name: (ROOT / 'tools' / name).read_bytes() for name in (*base.campaign.PINS, *names)}
    assert {name: sha(sources[name]) for name in base.campaign.PINS} == base.campaign.PINS
    assert [sha(sources[name]) for name in names] == list(pins)
    rom = (ROOT / 'build/iraira-outer-palette-v86-20261117/component.gba').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM
    indexed = {int(a, 16): int(b, 16) for a, b in re.findall(
        rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', sources[WRAPPER])}
    indexed |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF}
    assert len(indexed) == 25
    hooks = base.ai.HOOKS | base.provenance.HOOKS | base.aligned.IR_OPCODES | indexed
    assert all(struct.unpack_from('<I', rom, a-0x08000000)[0] == opcode for a, opcode in hooks.items())
    blocks = [(a-0x08000000, 4) for a in hooks]
    blocks += [(0x8B70C, 4), (0xB6054, 4), (0xB5FEA, 32), (0xD3FB10, 5), (0xD3FB18, 40), (0xD3FB40, 11),
               (0xD8ABA2, 18), (0xD88900 + 9 * 384 + 2 * 64, 2), (0xD8A658, 18), (0xC65F4, 64)]
    quote = base.campaign.quote
    lua = f'local provenance={quote(sources[WRAPPER])}\nlocal romhash="{ROM}"\nlocal oldrom="{base.campaign.ROM}"\n'
    lua += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(raw)}' for name, raw in sources.items()) + '}\n'
    lua += 'local romblocks={' + ','.join(f'{{at={0x08000000+a},data={quote(rom[a:a+n])}}}' for a, n in blocks) + '}\n'
    run = base.campaign.host.lua_check
    FunctionType(run.__code__, dict(run.__globals__, CHECK=lua+fixture()))('', '', '')
    report = dict(status='WHOLEPLAY_V86_LUA_QA_PASS', wrapper_sha256=PIN, component_sha256=ROM,
                  checksum_bound_exec_sites=len(indexed), cases=['full-ordered-route', 'bounded-no-activation',
                  'stage11-owner-refusal', 'invalid-damage-math', 'missing-stage11-approval', 'wrong-rom'],
                  original_driver_inverse=True, unchanged_pre_shoot_inputs=True, sole_extra_hp1_word=True,
                  final_release=True, mode20_handshake_required=True, harness_emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(report['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
