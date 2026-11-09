#!/usr/bin/env python3
"""EXPERIMENTAL: connect one real case5 allocation to the resident source scene.

Development observation only. This does not approve complete external entry or
alter progression, force stage/mode/HP, or add a second scene allocation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from build_shoot_scene_route import code
from analyze_waterfall_third_pattern import no_inbound
from verify_shoot_static_companion_clear import Machine

ROOT=Path(__file__).resolve().parents[1]
INPUT='6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7'
GBA='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SELECTOR,HOOK=0x6FF380,0x33FD04
DEPENDENCIES={
 'build_shoot_scene_route.py':'6E431B580F24E59B2114E3378CE9B927810F669844E5218D5962A3281F0D9263',
 'analyze_waterfall_third_pattern.py':'DB327A22961631CBEE0CEB725525BFBA06775115313C0F34504AF1D9CAE174A3',
 'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
}
PINS=(
 (0x33FCCC,0x33FDC0,'BA358E3B4CE1E19E4EEDB0B54F0119F9D0FAEA77DE1DCF26AF2B75B9C15CAFF4'),
 (0x5C8000,0x5C8100,'66182845D1C182628BABA58D00EC0ED1C86DD4373A5B527378F93704B41707F6'),
 (0x629800,0x62988C,'8FEDEC3D4115A92339E37D1F78CAC2A1DE4A435A074CF641339FF22EC90B5F13'),
 (0x6FC300,0x6FC334,'3B528805D97B87A3C35CE298E929AE3B46BCE2BDF8009A165A04BFB4EB175474'),
)

def need(ok,label):
 if not ok:raise ValueError(label)

def sha(data):return hashlib.sha256(data).hexdigest().upper()

def join_check(data):
 cases=0
 for stage in (0,7,11,255):
  for difficulty in (0,1,3,255):
   for progress in (0,0x400,0xFFFF):
    m=Machine(data,cases%3,flags=((cases%16)<<28)|0xD3)
    for address,value,size in ((0x0300231E,stage,1),(0x0300231F,difficulty,1),(0x0300232A,progress,2)):
     m.put(address,value,size)
    initial,flags=m.r[:15],m.cpsr
    expected=0x085C8000 if stage!=11 and (difficulty==3 or difficulty!=0 and not progress&0x400) else 0x086FC300
    m.run(0x08000000+HOOK,{0x0833FD08})
    want=initial[:];want[8]=expected
    need(m.r[:15]==want and m.cpsr==flags,'actual callback argument join preserves all other registers/SP/LR/CPSR')
    need(all(initial[13]-16<=a and a+n<=initial[13] for a,v,n in m.writes),'selector writes its stack frame only')
    cases+=1
 return cases

def build(before,gba,source):
 need(sha(before)==INPUT and sha(gba)==GBA and sha(source)==SOURCE,'exact resident predecessor and originals')
 for name,digest in DEPENDENCIES.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen dependency '+name)
 for a,z,digest in PINS:need(sha(before[a:z])==digest,'retained scene/allocation dependency '+hex(a))
 need(before[0x33FCCC:0x33FDC0]==gba[0x33FCCC:0x33FDC0],'one original case5 allocator unchanged')
 need(sha(source[0x771F69:0x772011])=='CD05FF48C1922F76960ECEE5B2C2847E693DEC337D2B598C32777F7F367C2B8E','reviewed source case5 conditions and allocations')
 ledger_bytes=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
 need(sha(ledger_bytes)=='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33','complete1394-interval ownership ledger')
 ledger=json.loads(ledger_bytes)
 need(ledger['normalized_interval_count']==1394 and ledger['layer_count']==70,'complete declared predecessor extent')
 irq_bytes=(ROOT/'build/shoot-guarded-transition-20261109/component-c.json').read_bytes()
 need(sha(irq_bytes)=='D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C','frozen additional IRQ reservations')
 irq=json.loads(irq_bytes)
 owned=[[0,0x400000]]+ledger['merged_union']+irq['reservations']+[[0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0]]
 need(not any(lo<SELECTOR+128 and SELECTOR<hi for lo,hi in owned),'no declared ownership including erased tails')
 need(before[SELECTOR:SELECTOR+128]==b'\xff'*128,'whole128B selector cave erased')
 ownership=no_inbound(before,[(SELECTOR,SELECTOR+128)])
 need(not ownership['classified_instruction_interiors'],'no ownership exemptions for selector cave')
 selector,count=code()[0x5C9900]
 need(len(selector)==104 and count==80 and sha(selector)=='9408A3EE46D6FE57F025611FD9C5BDDA2D92A51341F2382B33A3DBD8F51A39E7','exact reviewed104B selector with source0653 terminal router')
 # Every relative reference stays within the unchanged block except its final
 # B to the original allocator argument push. Relocate that one word only.
 selector=bytearray(selector)
 struct.pack_into('<I',selector,76,0xEA000000|(((0x33FD08-(SELECTOR+76)-8)//4)&0xFFFFFF))
 selector=bytes(selector)
 need(before[HOOK:HOOK+4]==struct.pack('<I',0xE59F80A8),'original callback argument load')
 branch=struct.pack('<I',0xEA000000|(((SELECTOR-HOOK-8)//4)&0xFFFFFF))
 result=bytearray(before);result[SELECTOR:SELECTOR+104]=selector;result[HOOK:HOOK+4]=branch
 def validate(data):
  need(len(data)==len(before) and data[SELECTOR:SELECTOR+104]==selector and data[HOOK:HOOK+4]==branch,'exact two experimental writes')
  inverse=bytearray(data);inverse[SELECTOR:SELECTOR+104]=before[SELECTOR:SELECTOR+104];inverse[HOOK:HOOK+4]=before[HOOK:HOOK+4]
  need(inverse==before,'whole-ROM inverse; progression and all other paths unchanged')
 validate(result)
 cases=join_check(result)
 negatives=[]
 for label,at in (('hook',HOOK),('stage predicate',SELECTOR+20),('flags restore',SELECTOR+68),('progress producer',0xB9E68),('unused cave',SELECTOR+104),('initializer',0x629800)):
  bad=bytearray(result);bad[at]^=1
  try:validate(bad)
  except ValueError:negatives.append(label)
  else:raise ValueError('ineffective expected-write negative '+label)
 return bytes(result),dict(schema=1,status='EXPERIMENTAL_DEVELOPMENT_ENTRY_ONLY',
  input_sha256=INPUT,output_sha256=sha(result),gba_sha256=GBA,source_sha256=SOURCE,
  release_approved=False,complete_external_entry_approved=False,runtime_executed=False,
  source_predicate='stage!=11 && (difficulty==3 || (difficulty!=0 && !(progress&0400)))',
  selected_scene=0x085C8000,default_router=0x086FC300,single_original_allocator=0x0833FD18,
  priority=0x0FF0,new_allocations=0,new_guest_diagnostic_RAM=False,
  progression_producer_unchanged=True,stage_mode_HP_forcing=False,
  entry_precondition='Normal initialized battle and one engine-owned scene transition; existing caller/palette/storage/scene-owner contracts reused',
  scope_limits=['Generic upper-victim event48 conditional consumer risk','8EF3 residual nonpattern domain rejects','Guarded transition supports retained stationary family, not every legal source entry'],
  placements=[dict(offset=SELECTOR,bytes=104,code_bytes=count,sha256=sha(selector))],
  hooks=[dict(offset=HOOK,expected=0xE59F80A8,replacement=struct.unpack('<I',branch)[0])],
  declared_bytes=108,changed_bytes=sum(a!=b for a,b in zip(before,result)),
  whole_ROM_inverse=True,ownership=ownership,layout_ledger_sha256=sha(ledger_bytes),IRQ_reservations_manifest_sha256=sha(irq_bytes),
  original_reviewed_selector=0x5C9900,relocated_only_word_offset=76,actual_join_cases=cases,negative_controls=negatives,
  dependencies={**DEPENDENCIES,'build_shoot_runtime_entry_probe.py':sha(Path(__file__).read_bytes())})

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('input','gba','source','output'):p.add_argument(name,type=Path)
 p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
 paths=(a.input,a.gba,a.source,a.output,a.manifest)
 need(len({v.resolve()for v in paths})==5,'distinct paths')
 need(not a.output.exists()and not a.manifest.exists(),'fresh development outputs')
 result,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
 a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'))
 print('[EXPERIMENTAL ONLY] '+report['output_sha256'])

if __name__=='__main__':main()
