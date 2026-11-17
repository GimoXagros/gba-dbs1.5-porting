"""Check the new ID14 air observer's composed Lua and one-shot input policy without an emulator."""
import argparse
import hashlib
import json
import re
import struct
import types
from pathlib import Path

import verify_wsc_shoot_short_hard as lua_host

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest().upper()
QUOTE = lambda data: '"' + ''.join('\\' + f'{byte:03d}' for byte in data) + '"'
PINS = {
    'bizhawk_probe_evolution_id14_air.lua': '6F6DF7F2B94030585C80A5302A5D5B2F3394A6F58F96C32A819B97E855BAD7AB',
    'bizhawk_probe_evolution_id14_r2.lua': 'A42E8338C44D258AFC8E262BB20EED6FD45A1741A7E74F4CFAE788F931382BAA',
    'bizhawk_probe_evolution_id14.lua': 'DA591E60FC3793D77F9A38B6FFF1F5F8707F8F7B415A0B07C5AF5E7FC6D59E2B',
    'bizhawk_probe_evolution_music_three.lua': 'B93AA91CFDA80E52D9F8991A1979860AEC9409315642E2D5903A61051F6EA881',
    'bizhawk_probe_result_music_lifetime.lua': 'CE19C883938D17D82C19BC6678B0F521D53E104BB132362528098A510D7FE430',
    'bizhawk_probe_result_languages.lua': '928186AE59C1A9EFC89E706FED46D66B595089D99F18341701A0E1059EBCE2EC',
    'bizhawk_observe_evolution_event_queue.lua': 'C83AAD2FCB536C4F3021339ECF776565A87E819790BC9021D538C4FB1BB6E23D',
    'bizhawk_observe_collision_alignment.lua': 'B22D8E4E87799DCAD300E9E87F2263C1F8FA8A902F3E9DC1CADBA88CE247128C',
}
CHECK = r'''
local captured,collision_capture
local env=setmetatable({},{__index=_G})
env.userdata={get=function(k)if k=="target_song" then return 108 end return "W:/build/mock-air" end}
env.memory={getmemorydomainsize=function()return 0x1000000 end}
env.io={open=function(path,mode)
 assert(mode=="rb" and sources[path],path)
 return {read=function()return sources[path]end,close=function()end}
end}
env.load=function(s,n,m,e)
 if n=="@ID14-collision-witness" then collision_capture=s end
 if n=="@ID14-event-witness" or n=="@ID14-collision-witness" then
  return function()return{finish=function()end}end
 end
 if n=="@reviewed-evolution-music-pause" then captured=s;return function()end end
 return load(s,n,m,e)
end
assert(load(wrapper_source,"@ID14-air","t",env))()
assert(captured and select(2,captured:gsub('local air={state="unarmed"}',''))==1)
assert(select(2,captured:gsub(' music_pause_input%(keys,stage,mode%)\n music_air_input%(keys,stage,mode%)\n joypad.set%(keys%)',''))==1)
assert(captured:find('music_lifetime_finish()\nid14_evidence_finish()\nlocal f=',1,true))
assert(captured:find('music_log(label,r);music_lifetime_finish();id14_evidence_finish()',1,true))
assert(collision_capture and collision_capture:find('snapshot("collision-e5");finish();id14_evidence_finish(true)',1,true))
local function between(first,last)
 local a=assert(captured:find(first,1,true));assert(not captured:find(first,a+1,true))
 local b=assert(captured:find(last,a+1,true));return captured:sub(a,b-1)
end
local policy=between('local function actor(p)','local function music_selection()')..between('local air={state="unarmed"}','local function music_pause_input')
local p,q=0x02011710,0x02011828
local function case(body,invalid)
 local ram={ [0x0300489C]=p,[0x030048A0]=q,[0x03004529]=0,
  [p-8]=2,[q-8]=2,[p]=0x0835620C,[p+4]=0,[p+6]=0,[p+8]=0x4000,[p+0xA]=0,
  [p+0x10]=0,[p+0x11]=14,[q+0x10]=1,[p+0x14]=p,[p+0x18]=q,[q+0x18]=p,[p+0x2C]=0 }
 local context=setmetatable({RAM=ram,frame=100,logs={},p=p,q=q}, {__index=_G})
 context.context=context
 context.music_read=function(a)return ram[a] or 0 end
 context.emu={framecount=function()return context.frame end,getregisters=function()return{}end}
 context.music_log=function(label)table.insert(context.logs,label)end
 context.invalidate=function()if invalid then invalid(ram)end end
 assert(load(policy..body,'@air-policy','t',context))()
end
case([[
 local keys={Right=true};RAM[p+0x6A]=49;music_air_input(keys,'battle',7)
 assert(air.state=='armed' and keys.Right)
 RAM[p]=0;RAM[p+0x6A]=48;context.frame=101;music_air_input(keys,'battle',7)
 assert(air.state=='window' and not keys.A)
 RAM[p]=0x0835620C;RAM[p+0x6A]=47;context.frame=102;music_air_input(keys,'battle',7)
 assert(air.state=='held' and air.until_frame==122 and keys.A and not keys.Right)
 for n=103,121 do context.frame=n;RAM[p+0x6A]=47-(n-102);keys={};music_air_input(keys,'battle',7);assert(keys.A)end
 context.frame=122;keys={};music_air_input(keys,'battle',7)
 assert(air.state=='done' and not keys.A)
 context.frame=123;RAM[p+0x6A]=48;keys={};music_air_input(keys,'battle',7)
 assert(air.state=='done' and not keys.A and #context.logs==4 and context.logs[1]=='air-jump-window' and context.logs[2]=='air-jump-window' and context.logs[3]=='air-jump-trigger' and context.logs[4]=='air-jump-release')
]])
case([[
 local keys={};RAM[p+0x6A]=48;music_air_input(keys,'battle',7)
 RAM[p+0x6A]=47;music_air_input(keys,'battle',7);assert(air.state=='unarmed' and not keys.A)
]])
case([[
 local keys={};RAM[p+0x6A]=49;music_air_input(keys,'battle',7)
 RAM[p+0x6A]=46;music_air_input(keys,'battle',7)
 assert(air.state=='missed' and not keys.A and context.logs[1]=='air-jump-missed')
]])
local guards={
 {'paused',function(r)r[0x03004529]=1 end},
 {'wrong ID',function(r)r[p+0x11]=13 end},
 {'wrong side',function(r)r[p+0x10]=1 end},
 {'bad link',function(r)r[p+0x18]=0 end},
 {'ordinary kind',function(r)r[p+4]=1 end},
 {'not evolved',function(r)r[p+8]=0 end},
 {'not idle',function(r)r[p]=0 end},
 {'airborne',function(r)r[p+6]=1 end},
 {'return blocked',function(r)r[p+6]=0x20 end},
 {'actor blocked',function(r)r[p+0xA]=0x1000 end},
 {'A not released',function(r)r[p+0x2C]=0x40 end},
}
for _,guard in ipairs(guards)do
 case([[
  local keys={};RAM[p+0x6A]=49;music_air_input(keys,'battle',7)
  RAM[p+0x6A]=48;invalidate();music_air_input(keys,'battle',7)
  assert(air.state~='held' and not keys.A and #context.logs<=1)
 ]],guard[2])
end
case([[
 local keys={};RAM[p+0x6A]=49;music_air_input(keys,'battle',7)
 RAM[p+0x6A]=48;music_air_input(keys,'menu',7)
 assert(air.state=='armed' and not keys.A)
 music_air_input(keys,'battle',6);assert(air.state=='armed' and not keys.A)
]])
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists(), 'fresh report required'
    blobs = {name: (ROOT / 'tools' / name).read_bytes() for name in PINS}
    assert {name: SHA(blob) for name, blob in blobs.items()} == PINS
    assert not re.search(rb'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.setregister', blobs['bizhawk_probe_evolution_id14_air.lua'])
    source = Path('C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc').read_bytes()
    assert SHA(source) == 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
    assert source[0x74356F:0x7435A8].hex() == 'f744080040743aff4c567959f7440a00107403e94f00f7440620007548814c066000814c048000814c080700c6445b00c744620000c7046f0c'
    old = (ROOT / 'build/impmon-evolution-clean15-20261116/component.gba').read_bytes()
    fixed = (ROOT / 'build/evolution-transition-tables-20261116/component.gba').read_bytes()
    assert SHA(old) == '8C727FA831F0DF3B2DCE41EE76AE471BE2D50F0DAA877235E40E856CD78B2BD8'
    assert SHA(fixed) == 'C91E8EE23830C1BDCB52C8060742EB939ADDCD156B34DAC4C877ED5F47E5B8B1'
    opcodes = {0x3525BC: 0xE5948000, 0x3525C4: 0xE12FFF18, 0x3525E8: 0xEB0001C8,
               0x352598: 0xEB00015C, 0x35A3D0: 0xE3A09C06, 0x35A3D4: 0xE1C496BA,
               0x352FC0: 0xE2888040, 0x352FD8: 0xE1C486BA, 0x35A548: 0xE3180001,
               0x35A558: 0xE92D0020, 0x35620C: 0xE92D4000, 0x35624C: 0xEBFFFD76}
    assert all(struct.unpack_from('<I', old, at)[0] == word for at, word in opcodes.items())
    assert struct.unpack_from('<I', old, 0x35A598)[0] == 0x00190019
    assert struct.unpack_from('<I', fixed, 0x35A598)[0] == 0x08D3F03C
    assert struct.unpack_from('<H', old, 0x35A5B2)[0] == 0xE3A0
    assert struct.unpack_from('<H', fixed, 0xD3F058)[0] == 25
    sources = {name: blob for name, blob in blobs.items() if name != 'bizhawk_probe_evolution_id14_air.lua'}
    prefix = 'wrapper_source=' + QUOTE(blobs['bizhawk_probe_evolution_id14_air.lua']) + '\nlocal sources={' + ','.join(
        '[' + QUOTE(('W:/tools/' + name).encode()) + ']=' + QUOTE(blob) for name, blob in sources.items()) + '}\n'
    run = types.FunctionType(lua_host.lua_check.__code__, dict(lua_host.__dict__, CHECK=prefix + CHECK),
                             argdefs=lua_host.lua_check.__defaults__)
    run('', '', '')
    result = dict(status='ID14_AIR_OBSERVER_QA_PASS', wrapper_sha256=PINS['bizhawk_probe_evolution_id14_air.lua'],
                  checker_sha256=SHA(Path(__file__).read_bytes()), dependency_sha256=PINS,
                  source_timer_and_native_branch_pinned=True, nested_Lua54_composition=True,
                  focused_policy_cases=15, terminal_closures_preserved=3, one_shot_A_hold_frames=20,
                  actual_gameplay_proven=False, emulator_launched=False, forced_game_state=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(result['status'], SHA(args.report.read_bytes()))


if __name__ == '__main__':
    main()
