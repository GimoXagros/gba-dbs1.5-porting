"""Execute the exact v87 checkpoint aim wrapper with mocked BizHawk APIs."""
import argparse
import json
from pathlib import Path
import re
import struct
from types import FunctionType

from check_campaign_complete_probe import host, quote
from verify_gba_shoot_entry_capture import ROOT, sha


PROBE = 'bizhawk_probe_gba_shoot_checkpoint_aim_v87.lua'
TAIL = 'bizhawk_probe_campaign_wholeplay_v86.lua'
OBSERVER = 'bizhawk_gba_shoot_entry_observer.lua'
PINS = {
    PROBE: 'CF71EE6638E8F77BE4EB0F505F9D8738A2BA231EC78A5068ED78C653DECDB845',
    TAIL: '66B9BB23039FDF1B7441559990E5FBCF227DF66F5026820F5A06DB1E45B27594',
    OBSERVER: '7513D499A3A6D90AD1FAB0AF898AB2769621DE63A030E1A4CB29795D1642CD59',
}
ROM = '5284435AE1BA291699331F5A899358D254844E7EA4784A60D250DCEF2A07CECC'
CASES = ('left-complete', 'right-complete', 'bounded', 'bad-math', 'bad-owner',
         'invalid-mode', 'state-mismatch', 'wrong-rom', 'missing-approval')
FIXTURE = r'''
for _,case in ipairs(cases)do
 local out,ref="W:/build/aim-qa","W:/build/aim-qa/checkpoint"
 local approval="user-approved-development-stage11-boss-hp1-once"
 local data={output=out,checkpoint_dir=ref,probe_sha256=case=="wrong-rom" and "bad" or romhash,
  stage11_boss_authorization=case~="missing-approval" and approval or nil}
 local domains={ROM=0x1000000,IWRAM=0x8000,EWRAM=0x40000,VRAM=0x18000,PALRAM=0x400,OAM=0x400}
 local bases={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000,VRAM=0x06000000,PALRAM=0x05000000,OAM=0x07000000}
 local files,opened,mem,hooks,inputs,captures,writes,saves={},{},{},{},{},{},{},{}
 local p,q,aux=0x02011710,0x02011828,0x02011940
 local owner,mode,core=0x020120D0,0x03002310,89405
 local regs={CPSR=0x60000010};for i=0,15 do regs["R"..i]=0 end
 local inside,exited,loads=false,false,0
 local function put(at,v,n)for i=0,n-1 do mem[at+i]=(v>>(i*8))&255 end end
 local function get(at,n)local v=0;for i=0,n-1 do v=v|((mem[at+i]or 0)<<(i*8))end;return v end
 local function fire(at,values)
  regs.R15=at+4
  for k,v in pairs(values or {})do regs[k]=v end
  inside=true
  for _,fn in ipairs(assert(hooks[at],string.format("hook %08X",at)))do fn()end
  inside=false
 end
 local function active(header,value)put(header+0x10,value and 2 or 0,2)end
 local function native_mode(n)
  assert(not inside)
  inside=true;regs.R15=0x0801597C
  for _,fn in ipairs(hooks[mode])do fn(mode,n,0x2000)end
  put(mode,n,2);inside=false
 end
 for at,word in pairs(words)do put(at,word,4)end
 for _,a in ipairs({p,q,aux})do
  active(a-0x18,true);put(a+0x14,a,4)
 end
 for _,x in ipairs({{p+0x18,q},{q+0x18,p},{q+0x28,aux},{aux+0x18,p},{aux+0x28,q},
  {0x0300489C,p},{0x030048A0,q},{0x03004D3C,aux},{q+0xF0,0x085D0000},{q+0xF4,0x085D1000},
  {aux+0xF0,0x085D029C},{aux+0xF4,0x085D1100},{p,0x0835620C},{q,0x085BF800}})do put(x[1],x[2],4)end
 for _,x in ipairs({{mode,7},{p+0x64,8},{q+0x64,37},{q+4,3},{aux+4,6},{q+0x10,0x0F01},
  {0x03004502,2},{0x0300450A,6},{p+0x34,3584},{p+0x36,5376},
  {q+0x34,4706},{q+0x36,3579},{q+0xBA,1}})do put(x[1],x[2],2)end
 put(0x0300231E,11,1);put(0x0300231F,2,1)
 for _,x in ipairs({{0x03004510,0x02011D88,0x08374FF4},{0x03004514,0x02011EA0,0x083735BC}})do
  put(x[1],x[2],4);active(x[2],true);put(x[2],x[3],4)
 end
 local result_age,ending_age
 local function advance()
  local keys=inputs[#inputs]
  local relative=core-89405
  if relative==0 then
   assert(keys.Right and not keys.Left and not keys.B and #writes==0)
   put(p+0xB4,0x4000,2)
   if case=="bad-owner"then put(q+0x28,aux+4,4)
   elseif case=="invalid-mode"then native_mode(77)
   elseif case~="bounded"then
    put(q+0x34,3584+(case=="right-complete" and 256 or -256),2)
    put(q+0x36,5568,2)
    if case=="right-complete"then put(p+0x2C,0x80,2)end
   end
  elseif case=="bounded"then assert(not keys.B and #writes==0)
  elseif relative==1 then
   assert(keys.Left==(case~="right-complete") and not keys.B and #writes==0)
   if case~="right-complete"then put(p+0xB4,0,2);put(p+0x2C,0x80,2)
   else put(p+0x2C,0,2);put(q+0xBA,3,2)end
  elseif relative==2 then
   assert(not keys.Left and not keys.Right and not keys.B and #writes==0)
   put(p+0x2C,0,2);put(q+0xBA,3,2)
  elseif relative==3 then
   assert(not keys.B and #writes==0)
   put(q+0xBA,4,2);put(p+6,1,2)
  elseif relative==4 then
   assert(not keys.B and #writes==0)
   put(p+6,0,2)
  elseif relative==5 then
   assert(keys.B and not keys.Left and not keys.Right and #writes==1)
   fire(0x0836E5E4,{R4=p,R5=q,R8=case=="bad-math" and 0xFFFF or 0,R0=1})
   if case~="bad-math"then
    put(q+0x64,0,2);fire(0x0836E5E8,{R4=p,R5=q})
    fire(0x085CD960,{R4=p,R5=q})
    put(q,0x085BDD00,4);put(aux,0x085BF204,4)
    fire(0x0836E604,{R4=p,R5=aux,R0=q})
    fire(0x083736B0,{R4=p,R5=q})
    fire(0x0833FD08,{R8=0x086FC300})
   end
  elseif relative==6 then
   assert(not keys.B and #writes==1)
   put(0x0300133C,owner,4);put(owner+4,0xFF0,4);active(owner,true)
   fire(0x085CD000);fire(0x085CD340);fire(0x085CD740)
   fire(0x08340C54);active(owner,false);put(0x03002314,1,2);put(0x0300475E,1,1)
   fire(0x08340CA8);native_mode(8);fire(0x080897AC)
   result_age=core
  elseif get(mode,2)==8 then
   fire(0x0808A524)
   if keys.A then assert(core-result_age>=120);native_mode(11);fire(0x080BF1D0);ending_age=core end
  elseif get(mode,2)==11 then
   fire(0x080C0050)
   if keys.A then
    assert(core-ending_age>=120);native_mode(20);fire(0x08040448)
    active(owner,true);put(owner+4,0xF100,4);put(owner,0x0804074C,4)
    put(0x03004738,0x102,2);fire(0x0804071C);fire(0x08040608,{R9=0x03002310})
   end
  elseif get(mode,2)==20 then
   assert(not keys.A and not keys.B)
   native_mode(3);put(owner+4,0x1000,4);put(owner,0x08090C7C,4);fire(0x08090C7C)
  else error("unexpected fixture step")end
  core=core+1
 end
 local function readfile(path)
  local name=path:match("[^/]+$")
  if path:match("^W:/tools/")then return assert(sources[name])end
  assert(path:sub(1,#ref)==ref)
  if name=="healthy-activation.txt"then return "core=89405 input_relative=89404 stage7_consumed=true mode=7 stage=11 retained"end
  if name=="healthy-activation.State"then return "PK\003\004checkpoint"end
  local domain=({iwram="IWRAM",ewram="EWRAM",vram="VRAM",palette="PALRAM",oam="OAM"})[name:match("41%-healthy%-activation%-(%a+)%.bin")]
  return string.rep("x",domains[assert(domain,name)])
 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)return data[k]end,set=function(k,v)data[k]=v end,clear=function()data={}end}
 env.emu={getsystemid=function()return "GBA"end,framecount=function()return core end,frameadvance=advance,getregisters=function()return regs end}
 local function add(fn,at)
  hooks[at]=hooks[at]or{};table.insert(hooks[at],fn)
 end
 env.event={on_bus_exec=add,on_bus_write=add}
 env.memory={read_u8=function(a,d)return get(bases[d]+a,1)end,
  read_u16_le=function(a,d)return get(bases[d]+a,2)end,
  read_u32_le=function(a,d)return get(bases[d]+a,4)end,getmemorydomainsize=function(d)return domains[d]end,
  read_bytes_as_binary_string=function(a,n,d)
   assert(not inside);return string.rep(case=="state-mismatch" and d=="VRAM" and "y" or "x",n)
  end,write_u16_le=function(a,v,d)
   assert(not inside and get(mode,2)==7 and get(0x0300231E,1)==11)
   assert(a+0x02000000==q+0x64 and v==1 and d=="EWRAM" and #writes==0)
   assert(get(q+0x64,2)==37 and get(p+0x64,2)==8)
   writes[1]=a;put(a+0x02000000,v,2)
  end}
 env.joypad={set=function(k)
  local c={}
  for key,v in pairs(k)do
   assert(not v or key=="Left" or key=="Right" or key=="B" or key=="A");c[key]=v
  end
  assert(not(c.Left and c.Right)and not(c.B and (c.Left or c.Right)))
  inputs[#inputs+1]=c
 end}
 env.savestate={load=function(path,quiet)
  assert(path==ref.."/healthy-activation.State" and quiet);loads=loads+1;return true
 end,save=function(path,quiet)assert(quiet and not inside);saves[path]=true;return true end}
 env.client={screenshot=function(path)assert(not inside);captures[path]=true end,
  speedmode=function(n)assert(n==800)end,exit=function()exited=true end}
 env.io={open=function(path,mode)
  if mode=="rb"then return {read=function()return readfile(path)end,close=function()return true end}end
  assert(not (mode=="wb" and opened[path]))
  if path:match("shoot%-checkpoint%-aim%-done.txt$")then assert(not next(opened),"logs closed before marker")end
  opened[path]=true
  local f={chunks={},append=mode=="a" or mode=="ab"}
  function f:write(data)table.insert(self.chunks,data);return true end
  function f:flush()return true end
  function f:close()
   files[path]=(self.append and files[path] or "")..table.concat(self.chunks)
   opened[path]=nil;return true
  end
  return f
 end}
 env.load=function(code,name,mode,scope)
  if name=="@shoot-checkpoint-readonly-observer"then
   assert(not code:find("memory.write",1,true))
  elseif name=="@shoot-checkpoint-frozen-terminal-tail"then
   assert(select(2,code:gsub("memory%.write_u16_le",""))==1)
   assert(not code:find("local function campaign",1,true))
  end
  return load(code,name,mode,scope)
 end
 local ok,err=pcall(assert(load(probe,"@actual-checkpoint-aim","t",env)))
 local marker=files[out.."/shoot-checkpoint-aim-done.txt"]
 if case=="missing-approval" or case=="wrong-rom"then
  assert(not ok and not marker and loads==0 and #inputs==0 and #writes==0,tostring(err))
 else
  assert(ok and exited and loads==1,tostring(err))
  for _,v in pairs(inputs[#inputs])do assert(not v,"quiet on exit")end
  local outcomes={["left-complete"]=success,["right-complete"]=success,bounded="failure:bounded-no-eligible-shot",
   ["bad-math"]="failure:wholeplay-unqualified-stage11-damage",["bad-owner"]="failure:wholeplay-live-aim-owner",
   ["invalid-mode"]="failure:checkpoint-invalid-mode",["state-mismatch"]="failure:script-error"}
  assert(marker==outcomes[case].."\n",case.." "..tostring(marker).." "..tostring(files[out.."/shoot-checkpoint-aim-error.txt"]))
  if case=="state-mismatch"then assert(not saves[out.."/restored.State"] and #writes==0 and #inputs==1)
  else
   assert(saves[out.."/restored.State"] and captures[out.."/01-checkpoint-before.png"])
   local ledger=files[out.."/wholeplay-stage11-writes.txt"]
   local choices=assert(files[out.."/shoot-checkpoint-aim-decisions.txt"])
   if marker==success.."\n" or case=="bad-math"then
    assert(ledger:find("after=1 verified=true",1,true) and #writes==1)
    assert(choices:find("B_candidate=true reason=eligible",1,true))
    assert(choices:find("B_candidate=false reason=held-B",1,true))
    assert(choices:find("B_candidate=false reason=upper-event",1,true))
    assert(choices:find("B_candidate=false reason=ready",1,true))
    local trace=files[out.."/wholeplay-trace.txt"]
    local prior=0
    if marker==success.."\n"then
     for _,label in ipairs({"healthy","stage11-hp1","hit-pre","hit-post","fatal-adapter","fatal-pair","root5",
      "case5","terminal-entry","terminal-middle","terminal-final","cleanup-entry","cleanup-request",
      "results-constructor","result-ready","ending-entry","ending-ready","mode20-entry","mode20-art",
      "mode20-return-request","title-ready"})do
      prior=assert(trace:find("event="..label.." ",prior+1,true),label)
     end
    else assert(not trace:find("event=hit-post",1,true))end
   else
    assert(not ledger and #writes==0 and saves[out.."/failure-observed.State"])
    if case=="bounded"then
     assert(core==91205 and #inputs==1801)
     assert(select(2,choices:gsub("B_candidate=false",""))==1800)
    end
   end
  end
 end
end
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    assert not args.report.exists()
    sources = {name: (ROOT / 'tools' / name).read_bytes() for name in PINS}
    assert {name: sha(data) for name, data in sources.items()} == PINS
    rom = (ROOT / 'build/shoot-child-contact-20261117/component.gba').read_bytes()
    assert len(rom) == 0x1000000 and sha(rom) == ROM
    words = {int(address, 16): int(opcode, 16) for address, opcode in re.findall(
        rb'(?:hook\(|\{)0x([0-9A-F]{8}),0x([0-9A-F]{8})(?:,"|\})', sources[TAIL])}
    words |= {0x085CD340: 0xE92D5FFF, 0x085CD740: 0xE92D5FFF}
    assert len(words) == 25
    assert all(struct.unpack_from('<I', rom, pc - 0x08000000)[0] == op for pc, op in words.items())
    setup = 'local cases={' + ','.join(f'"{case}"' for case in CASES) + '}\n'
    setup += f'local probe={quote(sources[PROBE])}\nlocal romhash="{ROM}"\n'
    setup += 'local success="shoot-checkpoint-aim-terminal-results-title"\n'
    setup += 'local sources={' + ','.join(f'[{quote(name.encode())}]={quote(data)}'
                                         for name, data in sources.items()) + '}\n'
    setup += 'local words={' + ','.join(f'[{pc}]={op}' for pc, op in words.items()) + '}\n'
    execute = host.lua_check
    FunctionType(execute.__code__, dict(execute.__globals__, CHECK=setup + FIXTURE))('', '', '')
    result = dict(status='SHOOT_CHECKPOINT_AIM_V87_LUA_QA_PASS', source_checkpoint_core=89405,
                  rom_sha256=ROM, script_sha256=PINS, checked_hook_opcodes=len(words), cases=CASES,
                  authorizes_only_first_eligible_stage11_hp1=True, verifies_five_restored_memory_domains=True,
                  aim_bound=1800, total_bound=8000, ordered_title_path_fixture=True, emulator_launched=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(result['status'], sha(args.report.read_bytes()))

if __name__ == '__main__':
    main()

