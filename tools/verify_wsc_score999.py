"""Source-bound and actual-Lua mocks for the explicitly authorized score cheat."""
import argparse
import json
from pathlib import Path
import types
import verify_wsc_shoot_short_hard as lua_host
from analyze_shoot_terminal_bx import exact, SOURCE
from analyze_shoot_lifetime_consumers import need, sha

ROOT=Path(__file__).resolve().parents[1]

def contracts(s):
    exact(s,0x743630,['mov ax, word ptr [bp + 0xa]','mov byte ptr [si + 0x10], al',
        'mov word ptr [si + 0x50], 8','mov word ptr [si + 0x52], 0'])
    exact(s,0x742B48,['mov al, byte ptr [si + 0x10]','cmp byte ptr [di + 0x10], al',
        'je 0x742b5f','inc word ptr [di + 0x52]','cmp word ptr [di + 0x52], 0xfa',
        'jbe 0x742b5f','mov word ptr [di + 0x52], 0xfa'])
    exact(s,0x74161F,['call 0x7426b0','call 0x7427fb','mov si, word ptr es:[0x65c]',
        'mov di, word ptr es:[0x65e]','call 0x74273b'])
    exact(s,0x7417A1,['lcall 0x875a, 0','lcall 0x875a, 0x3a','lcall 0x875a, 0x6f',
        'lcall 0x875a, 0xec','mov bx, 0xc00','mov ax, 0x1000','mov ds, bx','mov es, ax',
        'cmp word ptr es:[0x3d0], 2'])
    exact(s,0x7417FE,['cmp word ptr es:[0x3ce], 0','jns 0x74181a',
        'mov word ptr es:[0x3ce], 0','push 0','lcall 0x71f0, 0'])
    exact(s,0x78769E,['cmp byte ptr [0x5c], 7','je 0x7876ec',
        'cmp byte ptr [0x5c], 0xb','je 0x7876ec','xor dx, dx',
        'mov dl, byte ptr [0x3cc]','shl dl, 1','mov si, 0x65c','add si, dx',
        'mov si, word ptr [si]','mov ax, word ptr es:[si + 0x52]',
        'cmp ax, 0x3e7','jbe 0x7876c7','mov ax, 0x3e7'])
    exact(s,0x77243A,['mov si, word ptr es:[0x65c]','mov di, word ptr es:[0x65e]',
        'mov ax, word ptr [si + 0x52]','mov byte ptr es:[0x66e], al',
        'mov ax, word ptr [di + 0x52]','mov byte ptr es:[0x66f], al'])
    exact(s,0x7755DC,['xor ax, ax','mov al, byte ptr [si]','mov word ptr [bp - 2], ax'])
    exact(s,0x77560B,['cmp ax, dx','jbe 0x775624','inc word ptr [si + 0xe6]'])
    exact(s,0x76D00C,['cmp al, ah','jle 0x76d014','inc word ptr [bx + si + 0x8e]'])

CHECK=r'''
local env,hook,installs,recorded,log={},nil,0,{},''
local s={[0x4E]=7,[0x50]=0,[0x3D0]=0,[0x5C]=8,[0x3CC]=0,[0x3CD]=0,[0x65C]=0x1784,[0x65E]=0x1894}
local at,other=0xD784,0xD894
local ram={[at-6]=2,[at+4]=0xF700,[at+0x10]=0,[at+0x14]=0x1894,
 [at+0x50]=8,[at+0x52]=4,[at+0x54]=0x1234,[other+0x52]=8}
env.userdata={get=function(k)if k=='output'then return 'W:/build/mock-score999'else return 'bizhawk2111-rew'end end}
env.memory={read_u16_le=function(a,d)assert(d=='SRAM' and s[a]~=nil);return s[a]end,
 read_u8=function(a,d)assert(d=='SRAM' and s[a]~=nil);return s[a]end}
env.mainmemory={read_u16_le=function(a)return ram[a]or 0 end,read_u8=function(a)return ram[a]or 0 end,
 write_u16_le=function(a,v)assert(a==at+0x52 and v==999,'only score WORD999');recorded[#recorded+1]={a,v};ram[a]=v end}
env.emu={getregisters=function()return {PS=0x4090,PC=0xEA2}end,framecount=function()return 1234 end}
env.event={on_bus_write=function(fn,a,n,d)assert(a==0x417A1 and d=='System Bus');installs=installs+1;hook=fn end}
env.io={open=function(p,m)assert(p=='W:/build/mock-score999/score999-writes.txt'and m=='a');return {
 write=function(_,x)log=log..x end,close=function()end}end}
setmetatable(env,{__index=_G})
local m=assert(load(wrapper_source,'@actual-score999','t',env))()
assert(installs==0 and not m.status().enabled)
m.tick();m.tick();assert(installs==1 and #recorded==0)
local cases=0
local function fire(expected)
 local n=#recorded;ram[at+0x52]=4;hook(0x417A1)
 assert(#recorded==n+(expected and 1 or 0),'eligibility boundary')
 assert(ram[at+0x50]==8 and ram[at+0x54]==0x1234 and ram[other+0x52]==8,'adjacent/HP/opponent unchanged')
 cases=cases+1
end
fire(true)
local n=#recorded;hook(0x417A1);assert(#recorded==n,'already999 makes no write')
ram[at+0x52]=250;hook(0x417A1);assert(ram[at+0x52]==999,'postpickup clamp restored')
for mode=0,25 do s[0x4E]=mode;fire(mode==7)end;s[0x4E]=7
for stage=0,15 do s[0x5C]=stage;fire(stage<=10 and stage~=7)end;s[0x5C]=8
for kind=0,3 do s[0x3D0]=kind;fire(kind==0)end;s[0x3D0]=0
for pause=0,7 do s[0x3CD]=pause;fire(pause==0)end;s[0x3CD]=0
for _,spec in ipairs({{0x50,1},{0x3CC,1},{0x65C,0},{0x65C,0x1785},
 {0x65C,0x3764},{0x65E,0},{0x65E,0x1784}})do
 local old=s[spec[1]];s[spec[1]]=spec[2];fire(false);s[spec[1]]=old
end
for _,spec in ipairs({{at-6,0},{at+4,0xF701},{at+0x10,1},{at+0x14,0x244}})do
 local old=ram[spec[1]];ram[spec[1]]=spec[2];fire(false);ram[spec[1]]=old
end
local ok=pcall(function()hook(0x417A2)end);assert(not ok,'opcode calibration rejection')
assert(log:find('address=D7D6 bytes=2',1,true)and log:find('results export low byte231',1,true))
m.finish();m.finish();n=#recorded;ram[at+0x52]=4;hook(0x417A1);assert(#recorded==n and m.status().finished)
assert(cases==66,'finite mock count')
'''

def run(module):
    fn=types.FunctionType(lua_host.lua_check.__code__,dict(lua_host.__dict__,CHECK=CHECK),
                          argdefs=lua_host.lua_check.__defaults__)
    fn(module,'','')

def main():
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'fresh proof output');s=a.source.read_bytes()
    need(sha(s)==SOURCE,'original source');contracts(s)
    path=ROOT/'tools/bizhawk_wsc_score999.lua';module=path.read_text(encoding='utf8');run(module)
    rejected=[]
    for old,new,label in [('at+0x52,999','at+0x50,999','HP address'),
                          ('at+0x52,999','at+0x52,998','wrong value'),
                          ('or stage==7','or stage==77','boss allowed'),
                          ('~=0\n  or mainmemory.read_u16_le(at+0x14)','~=99\n  or mainmemory.read_u16_le(at+0x14)','wrong owner'),
                          ('0x7417A1,0x417A1','0x7417B5,0x417B5','late hook')]:
        need(module.count(old)==1,'unique mutation anchor '+label)
        try:run(module.replace(old,new))
        except ValueError:rejected.append(label)
        else:raise ValueError('accepted module mutation '+label)
    for at in (0x74363D,0x742B55,0x7417A2,0x7876C0,0x772449):
        bad=bytearray(s);bad[at]^=1
        try:contracts(bad)
        except ValueError:rejected.append(f'source{at:X}')
        else:raise ValueError('accepted source mutation')
    report=dict(status='SCORE999_MODULE_PASS',source_sha256=SOURCE,module_sha256=sha(path.read_bytes()),
        actual_Lua_guard_cases=66,negative_controls=rejected,score_word_offset=0x52,write_bytes=2,value=999,
        original_raw_opcode_hook=0x7417A1,ordinary_game_mode=7,game_kind=0,excluded_stages=[7,11],
        natural_pickup_cap=250,HUD_max=999,result_export_byte=999%256,
        signed_stats_consumer_interprets_export_as=-25,source_actor_base=0xC000,
        module_installs_once=True,post_award_pre_HUD_pre_timeout=True,emulator_run=False,guest_memory_written=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS',sha(a.output.read_bytes()))

if __name__=='__main__':main()
