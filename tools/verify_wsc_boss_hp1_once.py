"""Disabled optional boss proposal: narrow source guards and actual-Lua host mocks."""
import argparse
import json
from pathlib import Path
import types

import verify_wsc_shoot_short_hard as host
from analyze_shoot_lifetime_consumers import exact, need, sha, SOURCE_SHA

ROOT = Path(__file__).resolve().parents[1]


def contracts(s):
    exact(s, 0x740CA1, ['mov word ptr [0x3ce], 0x4650',
        'mov word ptr [0x3d2], 0x4628', 'add ax, 2'])
    exact(s, 0x741115, ['dec word ptr es:[0x3ce]'])
    exact(s, 0x76B880, ['push 0x4090', 'push 0x7fa', 'push 0xc00',
        'push word ptr es:[0x3de]', 'lcall 0x4fff, 0xbc7', 'add sp, 8',
        'push 0x4090', 'push 0xd0b', 'push 0xc00',
        'push word ptr es:[0x3e0]', 'lcall 0x4fff, 0xbc7', 'add sp, 8'])
    exact(s, 0x7417A1, ['lcall 0x875a, 0', 'lcall 0x875a, 0x3a',
        'lcall 0x875a, 0x6f', 'lcall 0x875a, 0xec'])
    exact(s, 0x7417C7, ['mov bx, word ptr es:[0x65c]',
        'cmp word ptr [bx + 0x50], 0', 'jne 0x7417e6'])
    exact(s, 0x7417E6, ['mov bx, word ptr es:[0x65e]',
        'cmp word ptr [bx + 0x50], 0', 'jg 0x7417fe',
        'push 5', 'lcall 0x71f0, 0'])
    exact(s, 0x745640, ['and word ptr [si + 4], 0x73ff',
        'mov byte ptr [si + 0x11], 0xf'])
    exact(s, 0x743388, ['push 1', 'push word ptr [0x65c]',
        'push word ptr [0x65e]', 'lcall 0x4090, 0x2cda'])
    exact(s, 0x743630, ['mov ax, word ptr [bp + 0xa]',
        'mov byte ptr [si + 0x10], al'])
    exact(s, 0x74364E, ['mov ax, word ptr [bp + 8]',
        'mov word ptr [si + 0x14], ax'])
    exact(s, 0x75097D, ['mov bx, 0x14', 'mov cx, word ptr [bx + 0xa]',
        'and cx, 2', 'je 0x750990', 'add bx, 0x110', 'jmp 0x750980'])
    exact(s, 0x7509A3, ['mov ax, 2', 'mov word ptr [di + 0xa], ax'])
    exact(s, 0x760185, ['sub word ptr [di + 0x50], ax'])


CHECK = r'''
local cases=0
local function fixture(approved)
 local q={ram={},s={},writes={},installs=0,log=''}
 for a=0,65535 do q.ram[a]=(a*13+29)%256 end
 local function put(a,v)q.ram[a]=v%256;q.ram[a+1]=math.floor(v/256)end
 q.put=put
 local function get(a)return q.ram[a]+q.ram[a+1]*256 end
 q.get=get
 q.s={[0x4E]=7,[0x50]=0,[0x3D0]=2,[0x5C]=7,[0x3CC]=0,[0x3CD]=0,
  [0x3CE]=17999,[0x3DE]=0x14,[0x3E0]=0x124,[0x65C]=0x1784,[0x65E]=0x1894}
 for _,p in ipairs({0x24,0x134,0x1784,0x1894})do put(0xC000+p-6,2)end
 put(0xC014,0x07FA);put(0xC016,0x4090);put(0xC124,0x0D0B);put(0xC126,0x4090)
 put(0xD788,0xF700);q.ram[0xD794]=0;put(0xD798,0x1894)
 put(0xD898,0x7303);q.ram[0xD8A4]=1;q.ram[0xD8A5]=15;put(0xD8A8,0x1784)
 put(0xD7D4,8);put(0xD8E4,44)
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)return ({output='W:/build/mock-boss-hp1',
  source_sha256='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7',
  callback_order='bizhawk2111-rew',boss_hp1_approval=approved and 'user-approved-original-reference-once' or nil})[k]end}
 env.memory={read_u16_le=function(a,d)assert(d=='SRAM');return assert(q.s[a])end,
  read_u8=function(a,d)assert(d=='SRAM');return assert(q.s[a])end}
 env.mainmemory={read_u16_le=get,read_u8=function(a)return q.ram[a]end,
  write_u16_le=function(a,v)assert(a==0xD8E4 and v==1,'sole SECOND HP WORD1');
   q.writes[#q.writes+1]={a,v};put(a,v)end}
 env.emu={getsystemid=function()return 'WSWAN'end,
  getregisters=function()return {PS=0x4090,PC=0xEA2}end,framecount=function()return 88000 end}
 env.event={on_bus_write=function(fn,a,n,d)assert(a==0x417A1 and d=='System Bus');
  q.installs=q.installs+1;q.hook=fn end}
 env.io={open=function(p,m)assert(p=='W:/build/mock-boss-hp1/boss-hp1-once-writes.txt'and m=='a');
  return {write=function(_,x)q.log=q.log..x end,close=function()end}end}
 q.env=env;q.module=assert(load(wrapper_source,'@actual-boss-hp1-proposal','t',env))()
 return q
end
local q=fixture(false);q.module.tick();q.module.finish()
assert(q.installs==0 and #q.writes==0 and not q.module.status().approved,'default is inert');cases=cases+1
local function fire(q,expected)
 local before={};for a=0,65535 do before[a]=q.ram[a]end
 q.module.tick();q.module.tick();assert(q.installs==1 and #q.writes==0)
 q.hook(0x417A1);assert(#q.writes==(expected and 1 or 0),'guard result')
 for a=0,65535 do
  local wanted=before[a]
  if expected and a==0xD8E4 then wanted=1 elseif expected and a==0xD8E5 then wanted=0 end
  assert(q.ram[a]==wanted,'full64K preservation at '..a)
 end
 cases=cases+1
end
q=fixture(true);fire(q,true);assert(q.module.status().applied and not q.module.status().enabled)
assert(q.log:find('address=D8E4 bytes=2 before=44 after=1',1,true))
q.put(0xD8E4,43);q.hook(0x417A1);assert(#q.writes==1 and q.get(0xD8E4)==43,'one-shot never holds1')
q.put(0xD8E4,0);q.hook(0x417A1);assert(#q.writes==1 and q.get(0xD8E4)==0,'natural zero stayszero')
q.module.finish();q.module.finish();q.hook(0x417A1);assert(#q.writes==1)
for _,timer in ipairs({0,17998})do q=fixture(true);q.s[0x3CE]=timer;fire(q,true)end
for _,hp in ipairs({2,32767})do q=fixture(true);q.put(0xD8E4,hp);fire(q,true)end
for _,spec in ipairs({{0x4E,6},{0x4E,8},{0x50,1},{0x3D0,0},{0x5C,11},{0x3CC,1},
 {0x3CD,1},{0x3CD,2},{0x3CD,4},{0x3CE,18000},{0x3CE,65535},
 {0x65C,0},{0x65C,0x1785},{0x65E,0x3764},{0x65E,0x1784},
 {0x3DE,0},{0x3DE,0x3645},{0x3E0,0x14}})do
 q=fixture(true);q.s[spec[1]]=spec[2];fire(q,false)
end
for _,spec in ipairs({{0xD77E,0},{0xD88E,0},{0xC01E,0},{0xC12E,0},
 {0xC014,0x71A},{0xC016,0x668E},{0xC124,0xA16},{0xD788,0xF701},
 {0xD798,0x244},{0xD898,0x7304},{0xD8A8,0x244},{0xD7D4,0},{0xD7D4,65535},
 {0xD8E4,0},{0xD8E4,1},{0xD8E4,65535}})do
 q=fixture(true);q.put(spec[1],spec[2]);fire(q,false)
end
for _,spec in ipairs({{0xD794,1},{0xD8A4,0},{0xD8A5,14}})do
 q=fixture(true);q.ram[spec[1]]=spec[2];fire(q,false)
end
q=fixture(true);q.module.tick();assert(not pcall(function()q.hook(0x417A2)end),'bad opcode rejected')
q.module.finish();q.hook(0x417A1);assert(#q.writes==0,'finish before write inert')
assert(cases==43,'finite case count '..cases)
'''


def run(module):
    fn = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=CHECK),
                            argdefs=host.lua_check.__defaults__)
    fn(module, '', '')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    need(not a.output.exists(), 'fresh proposal selfcheck output')
    s = a.source.read_bytes()
    need(sha(s) == SOURCE_SHA, 'pinned original source')
    contracts(s)
    path = ROOT / 'tools/bizhawk_wsc_boss_hp1_once.lua'
    module = path.read_text(encoding='utf8')
    run(module)
    rejected = []
    for old, new, label in [
        ('p2+0x50,1)', 'p1+0x50,1)', 'wrong owner'),
        ('p2+0x50,1)', 'p2+0x50,0)', 'directzero'),
        ('if finished or applied then return end', 'if finished then return end', 'fixed1 instead of once'),
        ('word(0x3CE)>=18000', 'word(0x3CE)>18000', 'intro enabled'),
    ]:
        need(module.count(old) == 1, 'unique mutation anchor')
        try:
            run(module.replace(old, new))
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('accepted proposal mutation ' + label)
    report = dict(status='DISABLED_BOSS_HP1_PROPOSAL_SELFCHECK_PASS',
        source_sha256=SOURCE_SHA, module_sha256=sha(path.read_bytes()),
        actual_Lua_scenarios=43, full_RAM_bytes_compared_per_scenario=65536,
        rejected_mutations=rejected, sole_write='C000+SECOND+50 WORD1',
        user_approval_received=True, requires_explicit_approval_token=True, current_driver_wired=False,
        source_opcode=0x7417A1, one_shot_entire_module_lifetime=True,
        excludes_intro_by_owned_callbacks_and_timer=True,
        emulator_started=False, guest_memory_written=False)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print('PASS', sha(a.output.read_bytes()))


if __name__ == '__main__':
    main()
