"""Local actual-Lua check for the authorized separate stage11 upper-boss HP1 module."""
import argparse
import json
from pathlib import Path
import struct
import types

import verify_wsc_boss_hp1_once as prior
import verify_wsc_shoot_short_hard as host
from analyze_shoot_lifetime_consumers import exact, need, sha, SOURCE_SHA

ROOT=Path(__file__).resolve().parents[1]


def contracts(s):
    prior.contracts(s)  # Source owner/slot/hook contracts only; never rerun its Lua suite.
    exact(s,0x77345F,['or word ptr es:[0x3d8], 4','push 0x4090',
        'push 0x7fa','push 0xc00','push word ptr es:[0x3de]',
        'lcall 0x4fff, 0xbc7','add sp, 8','push 0x4090','push 0xd0b',
        'push 0xc00','push word ptr es:[0x3e0]','lcall 0x4fff, 0xbc7','add sp, 8'])
    exact(s,0x747B7E,['push 0x24b2','push 0','push 0xbd','push 0x25f8',
        'push 0','push 0xbc','push 0x2f41','push 0','push 0xc00','push si',
        'lcall 0x4fff, 0x23f4'])
    exact(s,0x747B1F,['mov ax, word ptr [si + 0x50]','shr ax, 1',
        'mov word ptr [si + 0x54], ax','shr ax, 1','mov word ptr [si + 0x56], ax'])
    need(struct.unpack_from('<H',s,0x747E54)[0]==30,'defaultID0 base boss HP30')
    exact(s,0x747B0E,['sar ax, 2','add word ptr [si + 0x50], ax',
        'cmp byte ptr es:[0x5d], 3','jne 0x747b1f','add word ptr [si + 0x50], ax'])
    for at,target in [(0x7489C1,0x7DD9),(0x748761,0x7E8D),
                      (0x748781,0x7EBB),(0x748932,0x8069),(0x748993,0x809C)]:
        exact(s,at,[f'mov word ptr [si], 0x{target:x}',
                    'mov word ptr [si + 2], 0x4090'])


PRELUDE=prior.CHECK.split('local q=fixture(false)')[0]
PRELUDE=PRELUDE.replace('boss_hp1_approval','shoot_boss_hp1_approval').replace(
    'user-approved-original-reference-once','user-approved-original-stage11-boss-once').replace(
    'boss-hp1-once-writes.txt','shoot-boss-hp1-once-writes.txt')
CHECK=PRELUDE+r'''
local function ready(approved)
 local q=fixture(approved);q.s[0x5C]=11;q.s[0x5D]=3;q.s[0x3D8]=4
 q.ram[0xD795]=0
 q.put(0xD894,0x7E8D);q.put(0xD896,0x4090)
 q.put(0xD95A,0);q.put(0xD95C,0x2F41);q.put(0xD95E,0xBC)
 q.put(0xD960,0);q.put(0xD962,0x25F8);q.put(0xD964,0xBD)
 q.put(0xD8B0,0x19A4);q.put(0xD99E,2);q.put(0xD9A8,0x26)
 q.put(0xD9C0,0x1894);q.put(0xD9B8,0x1784)
 q.put(0xDA6A,0);q.put(0xDA6C,0x2D73);q.put(0xDA6E,0xBB)
 q.put(0xD8E8,22);q.put(0xD8EA,11);q.put(0xD9FA,0x1234)
 return q
end
local n=0
local function fire(q,expected)
 local before={};for a=0,65535 do before[a]=q.ram[a]end
 q.module.tick();q.module.tick()
 assert(q.installs==(q.module.status().approved and 1 or 0))
 if q.hook then q.hook(0x417A1)end
 assert(#q.writes==(expected and 1 or 0),'stage11 guard')
 for a=0,65535 do
  local want=before[a]
  if expected and a==0xD8E4 then want=1 elseif expected and a==0xD8E5 then want=0 end
  assert(q.ram[a]==want,'whole64K preservation '..a)
 end
 n=n+1
end
local q=ready(false);fire(q,false)
q=ready(true);fire(q,true)
assert(q.log:find('stage=11',1,true)and q.log:find('boss56=11 aux=19A4 aux56=4660',1,true))
q.put(0xD8E4,44);q.hook(0x417A1);assert(#q.writes==1 and q.get(0xD8E4)==44)
q.put(0xD8E4,0);q.hook(0x417A1);assert(#q.writes==1 and q.get(0xD8E4)==0)
q.module.finish();q.module.finish();q.hook(0x417A1);assert(#q.writes==1)
for _,callback in ipairs({0x7DD9,0x7EBB,0x8069,0x809C})do q=ready(true);q.put(0xD894,callback);fire(q,true)end
for _,spec in ipairs({{0x5C,7},{0x5D,2},{0x3D8,0},{0x4E,8},{0x3D0,0},
 {0x3CE,18000},{0x3CD,4}})do q=ready(true);q.s[spec[1]]=spec[2];fire(q,false)end
for _,spec in ipairs({{0xD894,0x7792},{0xD894,0x7AB1},{0xD896,0x668E},
 {0xD95C,0x2F23},{0xD95A,2},{0xD95E,0xBD},{0xD962,0x214E},
 {0xD8B0,0x1784},{0xD99E,0},{0xD9A8,0x23},{0xD9C0,0},{0xD9B8,0},
 {0xDA6C,0x2F41},{0xD7D4,0},{0xD8E4,0},{0xD8E4,1},{0xD8E4,45}})do
 q=ready(true);q.put(spec[1],spec[2]);fire(q,false)
end
q=ready(true);q.ram[0xD795]=1;fire(q,false)
q=ready(true);q.s[0x3CE]=0;q.put(0xD8E4,2);fire(q,true)
assert(n==32,'finite scenarios '..n)
'''


def run(module):
    fn=types.FunctionType(host.lua_check.__code__,dict(host.__dict__,CHECK=CHECK),
                          argdefs=host.lua_check.__defaults__)
    fn(module,'','')


def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    need(not a.output.exists(),'fresh stage11 check output')
    s=a.source.read_bytes();need(sha(s)==SOURCE_SHA,'immutable source');contracts(s)
    path=ROOT/'tools/bizhawk_wsc_shoot_boss_hp1_once.lua';module=path.read_text(encoding='utf8')
    run(module)
    rejected=[]
    for old,new,label in [('p2+0x50,1)','p1+0x50,1)','wrong owner'),
        ('p2+0x50,1)','p2+0x50,0)','directzero'),
        ('if finished or applied then return end','if finished then return end','continuous1'),
        ('ram(p2+0xC8)~=0x2F41','ram(p2+0xC8)~=0x2F23','stage7resource')]:
        need(module.count(old)==1,'mutation anchor')
        try:run(module.replace(old,new))
        except ValueError:rejected.append(label)
        else:raise ValueError('accepted mutation '+label)
    report=dict(status='STAGE11_BOSS_HP1_MODULE_PASS',source_sha256=SOURCE_SHA,
        module_sha256=sha(path.read_bytes()),actual_Lua_scenarios=32,
        full_RAM_bytes_compared_per_scenario=65536,negative_controls=rejected,
        sole_write='C000+SECOND+50 WORD1',initial_default0_hard_HP=44,
        retained_upper_thresholds=[22,11],aux56_preserved=True,
        user_boss_HP1_authorization_received=True,requires_explicit_approval_token=True,
        driver_wired=False,emulator_started=False,guest_memory_written=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS',sha(a.output.read_bytes()))


if __name__=='__main__':main()
