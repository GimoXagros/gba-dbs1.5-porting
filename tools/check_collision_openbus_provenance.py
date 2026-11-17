"""Check the conditional historical E5 mechanism and the new read-only witness."""
import argparse
import hashlib
import json
import struct
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'local/pydeps'))
import verify_wsc_shoot_short_hard as host

CHECK = r'''
for _,case in ipairs({'valid','malformed','paired','stale','e5','truncate','two-types','bounded','metadata','stale-metadata','bad-opcode'})do
 local frame=100
 local p=0x020117BC
 local ram={[0x08352830]=0xE1D480B4,[0x08353CA4]=0xE594400C,[0x08353CA8]=0xE59F10D4,[0x08353C70]=0xE1C100B4,[0x08353D24]=0xE1C100B4,[0x0836E370]=0xE1C800B0,[0x0836E37C]=0xE1D130B2,[0x0836E380]=0xE1D120B4}
 local hooks,files={},{}
 local r={};for i=0,15 do r['R'..i]=0 end
 r.R4=p-0xAC;r.R5=p
 if case~='valid'and case~='truncate'then ram[p+0x24]=0xFFFFFFFF;ram[p+0x28]=0xFFFFFFFF end
 if case=='bad-opcode'then ram[0x08352830]=0 end
 local env=setmetatable({},{__index=_G})
 env.userdata={get=function(k)assert(k=='output');return 'W:/build/openbus-check'end}
 env.emu={framecount=function()return frame end,getregisters=function()return r end}
 env.event={on_bus_exec=function(fn,a)assert(not hooks[a]);hooks[a]=fn end}
 local domain={ROM=0x08000000,IWRAM=0x03000000,EWRAM=0x02000000}
 local function rd(a,d)return ram[domain[d]+a]or 0 end
 env.memory=setmetatable({read_u8=rd,read_u16_le=rd,read_u32_le=rd,read_bytes_as_binary_string=function(a,n,d)assert(a==0 and n==({IWRAM=0x8000,EWRAM=0x40000})[d]);return d end},{__index=function(_,k)error('unplanned memory API '..k)end})
 env.io={open=function(path,mode)
  assert(mode=='wb');assert(not files[path]);local f={data='',closed=false};files[path]=f
  function f:write(s)assert(not self.closed);self.data=self.data..s;return self end
  function f:flush()assert(not self.closed)end
  function f:close()assert(not self.closed);self.closed=true end
  return f
 end}
 local ok,api=pcall(assert(load(wrapper_source,'@openbus','t',env)))
 if case=='bad-opcode'then assert(not ok)else
  assert(ok)
  hooks[0x08352830]()
  if case=='paired'or case=='stale'then
   r.R4=0xFFFFFFFF;hooks[0x08353CA4]()
   r.R4=0xA02004E3;if case=='stale'then frame=101 end
   hooks[0x08353CA8]()
  end
  if case=='e5'or case=='truncate'or case=='two-types'then
   r.R1=0x030048C8;r.R4=0xA02004E3
   if case=='two-types'then r.R0=0xBD0000E8;hooks[0x08353C70]()end
   r.R0=case=='truncate'and 0x9F000008 or 0x9F0000E5;hooks[0x08353D24]()
   if case~='truncate'then
    ram[r.R1]=p-0xAC;r.R4=r.R1;r.R0=0xE5;hooks[0x0836E370]()
   end
  end
  if case=='bounded'then for i=1,40 do hooks[0x08352830]()end end
  if case=='metadata'or case=='stale-metadata'then
   r.R4=0x030048C8;ram[r.R4]=p-0xAC;r.R1=0xFFFFFFFF;hooks[0x0836E37C]()
   if case=='stale-metadata'then frame=101 end
   r.R3=0x04000020;hooks[0x0836E380]()
  end
  api.finish();api.finish()
  local f=files['W:/build/openbus-check/collision-openbus.txt'];assert(f.closed)
  local function contains(s)return f.data:find(s,1,true)end
  if case=='valid'or case=='truncate'then assert(contains('event=command-type count=0')and contains('invalid_captured=false'))end
  if case=='paired'then assert(contains('loaded_B=A02004E3')and contains('effective_read=0000000B'))end
  if case=='stale'then assert(contains('event=B-after count=0'))end
  if case=='e5'or case=='two-types'then
   assert(contains('loaded_type32=9F0000E5 stored_type16=00E5')and contains('event=overlap count=1'))
   assert(files['W:/build/openbus-check/collision-openbus-first-invalid-iwram.bin'].closed)
   assert(files['W:/build/openbus-check/collision-openbus-first-e5-ewram.bin'].closed)
   assert(files['W:/build/openbus-check/collision-openbus-produced.txt'].closed)
   assert(api.result():find('B=A02004E3 loaded=9F0000E5 stored=00E5',1,true))
   assert(api.outcome()=='collision-openbus-producer-observed')
  end
  if case=='metadata'then assert(contains('loaded_r3=04000020'))end
  if case=='stale-metadata'then assert(contains('event=metadata-after count=0'))end
  if case=='bounded'then
   local n=0;for _ in f.data:gmatch('event=actor%-gate core=')do n=n+1 end
   assert(n==32 and contains('event=actor-gate count=41'))
  end
  for _,file in pairs(files)do assert(file.closed)end
 end
end
'''


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def ror(value, shift):
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF if shift else value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    assert not args.report.exists()
    rom = (ROOT / 'build/stage-priority-routing-20261023-a/current-candidate.gba').read_bytes()
    probe = (ROOT / 'build/runtime-waterfall-third-exit-20261023-a/probe.json').read_bytes()
    memory = (ROOT / 'build/collision-alignment-20261116/mgba-memory-fa977.c').read_bytes()
    arm = (ROOT / 'build/e5-openbus-v79-20261117/mgba-arm-fa977.c').read_bytes()
    bios = (ROOT / 'build/e5-openbus-v79-20261117/mgba-bios-fa977.c').read_bytes()
    assert sha(rom) == '389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1'
    assert sha(probe) == '22A2F2D822688D1E2E7239C987F303AA2F6AA8FEE6AD0A5EBADA4437D16C9937'
    assert sha(memory) == '501DBBCA7D5D7CBAA86240DE2D6A4E2E1186B50F74DDE11BCF2F323C4AF8C437'
    assert sha(arm) == 'A798211D6872F0F09EA82823EC8DABAA1E69CCAA70ED9B517219C7FE6F6110F5'
    assert sha(bios) == '767C02DEB8712DF0C5A70C819E5D361FC0600424A784254BBC48774A51838718'
    assert b'gba->memory.biosPrefetch = 0xE3A02004;' in bios
    words = {0x353CA4: 0xE594400C, 0x353D20: 0xE1D400B0, 0x353D24: 0xE1C100B4,
             0x353D28: 0xE59F8070, 0x353C74: 0xE8BD0010, 0x36E37C: 0xE1D130B2,
             0x36E394: 0xE1D500B4, 0x36E3A8: 0xE1D120B4}
    for offset, expected in words.items():
        assert struct.unpack_from('<I', rom, offset)[0] == expected
    assert b'value = cpu->prefetch[1];' in memory
    assert b'value = (GBALoadBad(cpu) >> ((address & 2) * 8)) & 0xFFFF;' in memory
    assert b'LOAD_32(cpu->prefetch[1], cpu->gprs[ARM_PC]' in arm
    regs = struct.unpack('<17I', bytes.fromhex(json.loads(probe)['timeout_registers_hex']))
    # Conditional model: no intervening DMA bus substitution, latch as specified.
    latch = 0xE3A02004
    effective = (0xFFFFFFFF + 12) & 0xFFFFFFFF
    b_pointer = ror(latch, (effective & 3) * 8)
    assert effective == 11 and b_pointer == 0xA02004E3 and b_pointer >> 24 > 15
    def bad_half(address, prefetch):
        return ror((prefetch >> ((address & 2) * 8)) & 0xFFFF, (address & 1) * 8)
    loaded = bad_half(b_pointer, words[0x353D28])
    assert loaded == 0x9F0000E5 and loaded & 0xFFFF == 0xE5
    assert bad_half(0xFFFFFFFF, words[0x353C74]) == 0xBD0000E8
    assert ror(latch & 0xFFFF, 8) == regs[3] == 0x04000020
    assert ((loaded & 0xFFFF) - 8) * 2 == regs[1] == 0x1BA
    assert bad_half(b_pointer & ~1, words[0x353D28]) & 0xFFFF != 0xE5
    assert bad_half(b_pointer, words[0x353C74]) & 0xFFFF != 0xE5
    assert bad_half(b_pointer, 0) == 0
    assert ror(0xE3A00000, 24) != b_pointer
    observer = (ROOT / 'tools/bizhawk_observe_collision_openbus.lua').read_bytes()
    check = types.FunctionType(host.lua_check.__code__, dict(host.__dict__, CHECK=CHECK),
                               argdefs=host.lua_check.__defaults__)
    check(observer.decode(), '', '')
    report = dict(status='PASS_CONDITIONAL_MECHANISM_AND_OBSERVER_ONLY',
                  historical_producer_observed=False, emulator_launched=False,
                  lua_cases=11, observer_sha256=sha(observer), rom_sha256=sha(rom),
                  probe_sha256=sha(probe), memory_source_sha256=sha(memory), arm_source_sha256=sha(arm),
                  bios_source_sha256=sha(bios), latch_value_is_present_in_pinned_HLE=True,
                  conditional_latch=f'{latch:08X}', conditional_B=f'{b_pointer:08X}',
                  loaded_command_type=f'{loaded:08X}', stored_command_type=f'{loaded & 0xFFFF:04X}',
                  event_type_from_FFFFFFFF='00E8', metadata_r3=f'{regs[3]:08X}',
                  limits=['Historical command, B pointer, latch upper half, and list entry were not captured.',
                          'Normal ARM prefetch branch assumed; DMA bus substitution can change the loaded value.',
                          'Observer mocks prove capture logic, not live emulator callback behavior.',
                          'No corrective game change and no historical root-cause closure.'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
