#!/usr/bin/env python3
"""Independent actual-Lua DI observer audit; no emulator, saves or guest writes."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
CORE = {
    'WonderSwan.cs': '73E5D28F50F2180FE56966349E2E72758DABFD75846EB4DCDCE8303DCEAC2C29',
    'BizSwan.cs': '0889F0173BBD93082439ABC2BDD9651D5851C83CE0694585A0CF43DC84807EAA',
    'memory.cpp': 'F4BA9ACFD24372C08F67A554E5836FD3F8640A08F00E49F2BDEBE5B00FD5C7D4',
    'v30mz.h': '05CCBE35E54D7CE3806892AF10B474C801283009282623832BF35A8720C0AED4',
    'v30mz.cpp': 'C6DF2310688FAA755313A9BA04287DD96E4ECE99594493F6B8A96A100CB24DE4',
    'v30mz-private.h': '9C4F0C037202FC6BAA0C60C5196442F1E2A0A717554828744739B9FBF17A2DAD',
    'v30mz-modrm.inc': 'BB92604F1E65F97D4F65BDB9AEA5274B5854992AC4CB7DD18EC0900E8E6BC690',
}


def need(ok, label):
    if not ok: raise ValueError(label)


def sha(data): return hashlib.sha256(data).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state', '.saveram'), 'save/state access forbidden')
    return path.read_bytes()


def contracts(source, core_dir):
    need(sha(source) == SOURCE, 'exact original source')
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    expected = ((0x750EBD, 1, 'push ax'), (0x773650, 3, 'mov ax, 0xc00'),
                (0x75FC98, 4, 'mov ax, word ptr es:[di + 0xa]'), (0x75FC9C, 2, 'out 0x10, al'))
    for at, size, text in expected:
        i = next(decoder.disasm(source[at:at + size], at), None)
        need(i is not None and i.size == size and i.mnemonic + ' ' + i.op_str == text, 'actual fixed hook instruction: ' + hex(at))
    blobs = {name: read(core_dir / name) for name in CORE}
    need({name: sha(blob) for name, blob in blobs.items()} == CORE, 'pinned2.11.1 source archives')
    managed, binding, cpu, private, memory = (blobs[x].decode() for x in (
        'WonderSwan.cs', 'BizSwan.cs', 'v30mz.cpp', 'v30mz-private.h', 'memory.cpp'))
    need(re.search(r'bizswan_setmemorycallbacks\(Core,\s*MemoryCallbacks.HasReads \? ReadCallbackD : null,\s*MemoryCallbacks.HasWrites \? WriteCallbackD : null,\s*MemoryCallbacks.HasExecutes \? ExecCallbackD : null', managed), 'managed callback order R,W,E')
    need('MemoryCallback rcb, MemoryCallback ecb, MemoryCallback wcb' in binding, 'native binding order R,E,W')
    need('CallMemoryCallbacks(addr, 0, flags, "System Bus")' in managed and
         'This isn\'t an actual memory domain' in managed, 'callback scope/value distinct from memory domain/consumed byte')
    need('typedef enum { DS1, PS, SS, DS0 } SREGS;' in blobs['v30mz.h'].decode() and
         'typedef enum { AW, CW, DW, BW, SP, BP, IX, IY } WREGS;' in blobs['v30mz.h'].decode(), 'DS1=ES and IY=DI native register identities')
    need('EO=(I.regs.w[IY]+(int8)FETCH); EA=DefaultBase(DS0)+EO;' in cpu and
         'ReadWord(ea) (cpu_readmem20((ea))+(cpu_readmem20(((ea)+1))<<8))' in private and
         'FETCHOP (cpu_readop((I.sregs[PS]<<4)+I.pc++))' in private,
         'V30MZ offset truncation, physical high byte and postincremented fetch PC')
    need('return wsSRAM[(offset | (BankSelector[1] << 16)) & (sram_size - 1)]' in memory and
         'case 0:  return wsRAM[offset];' in memory, 'actual RAM and cartridge SRAM mapper')
    return [dict(raw=hex(at), bus=hex(at - 0x700000), size=size, instruction=text) for at, size, text in expected]


MOCK = r'''
local function reject(fn,label)
 assert(not pcall(fn),'negative accepted: '..label)
end
local function up(fn,wanted)
 for i=1,100 do local n,v=debug.getupvalue(fn,i);if not n then break end;if n==wanted then return v end end
 error('actual Lua upvalue missing: '..wanted)
end
local function create(options)
 local o=options or {}
 local m={files={},hooks={},reads={},stage=o.stage or 11,frame=80}
 m.r={PS=0x4FFF,PC=0,DS0=0x0C00,DS1=0x300,IX=0x9876,IY=0,AW=0xA5A5,BW=0xEA,SP=0xF720}
 local function byte(a,d)
  if d=='ROM' then assert(rom[a],'ROM outside exact pin fixtures');return o.badopcode and a==0x75FC98 and 0 or rom[a] end
  assert(d=='RAM' or d=='SRAM','nonexistent memory domain: '..tostring(d))
  local size=d=='RAM' and 65536 or 32768
  assert(a%1==0 and a>=0 and a<size,'backing address outside real memory domain')
  m.reads[#m.reads+1]={a,d}
  if d=='SRAM' and a==0x5C then return m.stage end
  return (a*37+math.floor(a/256)*11+(d=='RAM' and 7 or 113))%256
 end
 m.byte=byte
 local env={assert=assert,error=error,pairs=pairs,ipairs=ipairs,tostring=tostring,string=string,math=math,table=table}
 env.userdata={get=function(k)return ({output='W:/build/independent-di-v3',callback_order=o.backend or 'bizhawk2111-rew',source_sha256=o.hash or SOURCE})[k]end}
 env.memory={getmemorydomainsize=function(d)return ({ROM=0x800000,RAM=o.badsize and 0x8000 or 0x10000,SRAM=0x8000})[d]end,
  read_u8=byte,read_u16_le=function(a,d)return byte(a,d)+256*byte(a+1,d)end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(a==0 and ((d=='RAM' and n==65536) or(d=='SRAM' and n==32768)))
   return string.rep(d=='RAM' and 'R' or 'S',n)
  end}
 env.io={open=function(p,mode)
  assert(p:match('^W:/build/independent%-di%-v3/'))
  if mode=='rb' then return o.existing and {close=function()end} or nil end
  assert(mode=='a' or mode=='wb')
  if mode=='wb' then assert(not m.files[p],'snapshot overwritten');m.files[p]='' end
  return {write=function(_,s)assert(type(s)=='string');m.files[p]=(m.files[p]or'')..s end,close=function()end}
 end}
 env.emu={getsystemid=function()return 'WSWAN'end,getregisters=function()return m.r end,framecount=function()return m.frame end}
 local function register(kind,fn,address,name,scope)
  assert(scope=='System Bus' and not m.hooks[name]);m.hooks[name]={kind=kind,fn=fn,address=address}
 end
 env.event={availableScopes=function()return o.noscope and {'RAM'}or{'System Bus'}end,
  on_bus_write=function(...)register('W',...)end,on_bus_exec=function(...)register('E',...)end,on_bus_read=function(...)register('R',...)end}
 m.observer=assert(load(observer_source,'@actual-di-v3','t',env))()
 local hooks=0;for _ in pairs(m.hooks)do hooks=hooks+1 end;assert(hooks==4,'exactly four fixed hooks')
 function m.fire(label,opts)
  opts=opts or {};local hook=assert(m.hooks['shoot-di-v3-'..label])
  local expected={calibration=0x50EBD,terminal=0x73650,pre=0x5FC98,post=0x5FC9C}
  assert(hook.address==expected[label],'fixed instruction callback address')
  m.r.PS=(label=='terminal' and 0x71F0 or 0x4FFF)+(opts.psdelta or 0)
  m.r.PC=(hook.address+1-m.r.PS*16)%65536+(opts.pcdelta or 0)
  -- Managed R,W,E binds to native R,E,W: native execute dispatches managed W.
  local kind=opts.nativewrite and 'E' or 'W'
  if hook.kind~=kind then return 0 end
  hook.fn(hook.address+(opts.addressdelta or 0),0,0)
  return 1
 end
 function m.calibrate()assert(m.fire('calibration')==1);m.fire('calibration');m.fire('calibration');assert(m.observer.status().calibrated==2)end
 function m.word(di)
  local lo=di<=0xFFF5 and 0x300A+di or 0x3000+di-0xFFF6
  local function b(a)return a<0x10000 and byte(a,'RAM')or byte(a-0x10000,'SRAM')end
  return b(lo)+256*b(lo+1)
 end
 function m.pre(di)m.r.IY=di;m.r.AW=0xA5A5;assert(m.fire('pre')==1)end
 function m.post(di,opts)m.r.AW=m.word(di);assert(m.fire('post',opts)==1);m.frame=m.frame+1 end
 function m.pair(di)m.pre(di);m.post(di)end
 function m.countfiles()local n=0;for p,s in pairs(m.files)do if p:match('%.bin$')then n=n+1;assert(#s==(p:find('SRAM.bin',1,true) and 32768 or 65536))end end;return n end
 return m
end

-- Exhaust the actual private operand/peek functions, reached through installed closures.
local m=create();m.calibrate()
local fn=up(m.hooks['shoot-di-v3-pre'].fn,'fn')
local operand,peek=up(fn,'operand'),up(fn,'peek')
for di=0,65535 do
 local off,lo,hi=operand(0x300,di)
 local expected=di<=0xFFF5 and 0x300A+di or 0x3000+di-0xFFF6
 assert(lo==expected and hi==expected+1 and off==expected-0x3000,'full16bit DI physical address oracle')
 local actual,domain,backing=peek(lo)
 local ed=lo<0x10000 and 'RAM' or 'SRAM';local ea=lo<0x10000 and lo or lo-0x10000
 assert(domain==ed and backing==ea and actual==m.byte(ea,ed),'full16bit DI backing-domain oracle')
end
local off,lo,hi=operand(0xFFFF,5);assert(off==15 and lo==0xFFFFF and hi==0,'20bitphysical high-byte wrap')
for _,a in ipairs({0,0xFFFF,0x10000,0x17FFF,0x18000,0x1FFFF})do
 local actual,d,b=peek(a);local ed=a<65536 and'RAM'or'SRAM';local eb=a<65536 and a or a%32768
 assert(d==ed and b==eb and actual==m.byte(eb,ed),'real32Kcartridge mapper alias')
end
reject(function()peek(0x20000)end,'outside32Kmapperwindow')
reject(function()peek(-1)end,'negativephysicaladdress')

-- Real installed hook executions. Callback value is always0 and SI deliberately differs from DI.
for _,di in ipairs({0,0xCFF5,0xCFF6,0xD000,0xFFF5,0xFFF6,0xFFFF})do m.pair(di)end
for i=1,505 do m.pair(i)end
local st=m.observer.status();assert(st.paired_reads==512 and st.distinct_snapshots==16 and st.actual_final_irq_observed)
assert(m.countfiles()==32,'16distinct snapshots each RAM+SRAM')
local before=m.files['W:/build/independent-di-v3/di-observer-v3.txt']
for i=1,20 do m.pair(i)end
assert(m.observer.status().paired_reads==512 and m.countfiles()==32 and m.files['W:/build/independent-di-v3/di-observer-v3.txt']==before,'pair cap does not log or dump')
assert(m.fire('terminal')==1);m.fire('terminal');assert(m.observer.status().terminal_observed and m.countfiles()==34,'one additional terminal snapshot')
local done=m.observer.finish();assert(done.finished and not done.pending)
local final=m.files['W:/build/independent-di-v3/di-observer-v3.txt']
for _,label in ipairs({'calibration','terminal','pre','post'})do m.fire(label,{pcdelta=7})end
assert(m.files['W:/build/independent-di-v3/di-observer-v3.txt']==final and m.countfiles()==34,'all callbacks inert after finish')
reject(function()m.observer.finish()end,'doublefinish')

for _,opts in ipairs({{backend='wrong'},{hash='wrong'},{badopcode=true},{badsize=true},{noscope=true},{existing=true}})do
 reject(function()create(opts)end,'initial source/backend/domain/freshness contract')
end
local q=create();local s=q.observer.finish();assert(s.paired_reads==0 and not s.actual_final_irq_observed and not s.terminal_observed,'empty observation makes no runtime claim')
q=create({stage=7});q.fire('pre');q.fire('post');q.fire('terminal');assert(q.observer.status().paired_reads==0 and q.countfiles()==0,'otherstage ignored')
q=create();reject(function()q.fire('pre')end,'missingcalibration')
q=create();reject(function()q.fire('terminal')end,'terminalmissingcalibration')
q=create();reject(function()q.fire('calibration',{pcdelta=1})end,'wrongfetchPC')
q=create();reject(function()q.fire('calibration',{addressdelta=1})end,'wrongfetchaddress')
q=create();q.calibrate();reject(function()q.fire('post')end,'orphanpost')
q=create();q.calibrate();q.r.DS1=0xC00;reject(function()q.pre(0)end,'wrongES')
q=create();q.calibrate();q.pre(0);reject(function()q.pre(0)end,'duplicatepre')
q=create();q.calibrate();q.pre(0);reject(function()q.observer.finish()end,'pendingfinish')
q=create();q.calibrate();q.pre(0);q.r.IY=1;q.r.AW=q.word(0);reject(function()q.fire('post')end,'differentDI')
q=create();q.calibrate();q.pre(0);q.r.DS1=0x301;q.r.AW=q.word(0);reject(function()q.fire('post')end,'differentES')
q=create();q.calibrate();q.pre(0);q.r.AW=q.word(0);reject(function()q.fire('post',{psdelta=1})end,'validphysicalaliasdifferentPSPC')
q=create();q.calibrate();q.pre(0);q.r.AW=(q.word(0)+256)%65536;reject(function()q.fire('post')end,'wronghighbytewithcorrectAL')
q=create();q.calibrate();q.pre(0);q.r.AW=0;reject(function()q.fire('post')end,'callbackzeroisnotconsumedword')
return 'actualLuaPASS:65536operand,512pairs,16distinct+terminal,22invalid'
'''


def run_lua(observer, source):
    library = ROOT / 'local/BizHawk-2.11.1/dll/lua54.dll'
    dll = ctypes.CDLL(str(library))
    pointer, integer = ctypes.c_void_p, ctypes.c_int
    for name, result, args in (
        ('luaL_newstate', pointer, []), ('luaL_openlibs', None, [pointer]),
        ('luaL_loadbufferx', integer, [pointer, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.c_char_p]),
        ('lua_pcallk', integer, [pointer, integer, integer, integer, ctypes.c_ssize_t, pointer]),
        ('lua_tolstring', ctypes.c_char_p, [pointer, integer, pointer]), ('lua_close', None, [pointer]),
    ):
        function = getattr(dll, name); function.restype = result; function.argtypes = args
    spans = ((0x75FC8C, 23), (0x773650, 10), (0x750EBD, 7))
    rom = ','.join(f'[{a + n}]={source[a + n]}' for a, size in spans for n in range(size))
    text = ('local SOURCE="' + SOURCE + '"\nlocal rom={' + rom + '}\nlocal observer_source=[====[\n' + observer + ']====]\n' + MOCK).encode()
    state = dll.luaL_newstate(); need(bool(state), 'Lua54 state allocation')
    try:
        dll.luaL_openlibs(state)
        result = dll.luaL_loadbufferx(state, text, len(text), b'independent-di-v3', b't')
        if result == 0: result = dll.lua_pcallk(state, 0, 1, 0, 0, None)
        value = dll.lua_tolstring(state, -1, None)
        message = value.decode() if value else 'no Lua result'
        need(result == 0, message)
        return message
    finally:
        dll.lua_close(state)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'observer', 'output'): p.add_argument(name, type=Path)
    p.add_argument('--core-source', required=True, type=Path)
    a = p.parse_args()
    need(a.output.suffix.lower() == '.json' and a.output.resolve() not in (a.source.resolve(), a.observer.resolve()), 'distinct JSON output')
    source, observer_bytes = read(a.source), read(a.observer)
    hooks = contracts(source, a.core_source)
    observer = observer_bytes.decode('utf-8')
    need(not re.search(r'\b(?:memory|mainmemory)\.write|\bsavestate\.|\bemu\.(?:setregister|frameadvance)|\bjoypad\.', observer), 'read-only observer API boundary')
    execution = run_lua(observer, source)
    rejected = []
    mutations = (
        ('64Kphysicalalias', '(es*16+offset)%0x100000', '(es*16+offset)%0x10000'),
        ('segmentedhighbytere-wrap', '(low+1)%0x100000', '(es*16+(offset+1)%0x10000)%0x100000'),
        ('wrong32KSRAMalias', 'physical%0x8000', 'physical%0x10000'),
        ('SIinsteadofDI', 'operand(r.DS1,r.IY)', 'operand(r.DS1,r.IX)'),
        ('DSinsteadofES', 'operand(r.DS1,r.IY)', 'operand(r.DS0,r.IY)'),
        ('wrongmanagedcallback', 'event.on_bus_write(function(address)', 'event.on_bus_exec(function(address)'),
        ('lowbyteonlycomparison', 'local match=r.AW==pending.word', 'local match=r.AW%256==pending.word%256'),
        ('missinginstructionstreampair', 'assert(r.PS==pending.ps and r.PC==(pending.pc+4)%0x10000,"instruction stream changed across MOV")', ''),
        ('paircap513', 'MAX_PAIRS,MAX_DISTINCT=512,16', 'MAX_PAIRS,MAX_DISTINCT=513,16'),
        ('snapshotcap17', 'MAX_PAIRS,MAX_DISTINCT=512,16', 'MAX_PAIRS,MAX_DISTINCT=512,17'),
    )
    for label, old, new in mutations:
        need(observer.count(old) == 1, 'unique semantic mutation site: ' + label)
        try: run_lua(observer.replace(old, new), source)
        except ValueError: rejected.append(label)
        else: raise ValueError('observer mutation accepted: ' + label)
    report = dict(status='ACTUAL_LUA_DI_V3_OBSERVER_QA_PASS', source_sha256=SOURCE,
        observer_sha256=sha(observer_bytes), verifier_sha256=sha(Path(__file__).read_bytes()),
        lua_runtime_sha256=sha(read(ROOT / 'local/BizHawk-2.11.1/dll/lua54.dll')),
        core_source_sha256=CORE, hooks=hooks, actual_lua_execution=execution,
        exhaustive_DI_values=65536, actual_paired_hook_cases=512, distinct_snapshots=16,
        additional_terminal_snapshot=True, fixed_callbacks=4, rejected_mutations=rejected,
        real_runtime_executed=False, emulator_launched=False, save_read=False, guest_writes=False,
        limits=['Actual Lua executed with isolated in-memory host API mocks; no actual WSC/game observation.',
                'Backing peeks are checked against post-instruction AW; callbacks do not expose consumed byte values.',
                'No new input, save provenance, launcher or actual Shoot-entry authorization.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(read(a.output)))


if __name__ == '__main__': main()
