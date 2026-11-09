#!/usr/bin/env python3
"""Reproduce the approved native Shoot connection from v73 and immutable originals.

Packaging only: no new behavior, historical ROM, capture, or runtime dependency.
Runtime acceptance and main-chain promotion remain separate decisions.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

import build_shoot_runtime_entry_probe as entry
import build_shoot_presentation_target_lifetime as target
import build_shoot_score_hud_guard as hud
import build_shoot_stage11_runtime_probe as nonfatal
import build_shoot_guarded_transition_irq as irq

ROOT=Path(__file__).resolve().parents[1]
INPUT=entry.INPUT
GBA,SOURCE=entry.GBA,entry.SOURCE
OUTPUT='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
D0=target.INPUT
TARGET='84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
HUD='8AA1A58844C31681EAB9816D1131C072F89FE4DD5EFA6F001F5C0F641088279D'
LEDGER='89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
DEPS={**entry.DEPENDENCIES,**hud.DEPENDENCIES,**nonfatal.DEPS,
 'build_shoot_runtime_entry_probe.py':'027FD5849411535D0C367B2C35E5978DECA381628744D62F0F868EDFDF3518E2',
 'build_shoot_score_hud_guard.py':'7D5C647547E4FECD6707A0B8AB6411B6A0FC3233442B04465820F27823634B32',
 'build_shoot_stage11_runtime_probe.py':'1C6CF23798A362A6ABE0B6D5B37C9B61F849FAE524B4F3D4D85C90FC7475BAE0',
 'build_shoot_guarded_transition_irq.py':'CBD14D957BDFC61F7A6163C727CC8CE9D0673D4B935EDD99830725CA1E164514'}


def need(ok,label):
    if not ok:raise ValueError(label)
def sha(data):return hashlib.sha256(data).hexdigest().upper()
def word(value):return struct.pack('<I',value)
def branch(at,to):return word(hud.branch(at,to))


def apply(before,writes):
    out=bytearray(before)
    for at,old,new in writes:
        need(len(old)==len(new) and out[at:at+len(old)]==old,'ExpectedWrite predecessor '+hex(at))
        out[at:at+len(new)]=new
    return bytes(out)


def validate(before,after,writes):
    need(len(before)==len(after),'unchanged ROM size')
    inverse=apply(after,[(at,new,old)for at,old,new in writes])
    need(inverse==before,'whole-ROM inverse outside exact writes')


def cave_check(before,start,end,owned):
    need(not any(a<end and start<z for a,z in owned),'full reservation overlap '+hex(start))
    need(before[start:end]==b'\xff'*(end-start),'entire reservation erased '+hex(start))
    scan=entry.no_inbound(before,[(start,end)])
    need(not scan['classified_instruction_interiors'],'strict zero ownership exemptions')
    return scan


def build(before,gba,source):
    need((sha(before),sha(gba),sha(source))==(INPUT,GBA,SOURCE),'exact v73 and immutable originals')
    for name,digest in DEPS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen dependency '+name)
    for a,z,digest in entry.PINS:need(sha(before[a:z])==digest,'retained entry dependency '+hex(a))
    need(before[0x33FCCC:0x33FDC0]==gba[0x33FCCC:0x33FDC0],'one unchanged original case5 allocator')
    need(sha(source[0x771F69:0x772011])=='CD05FF48C1922F76960ECEE5B2C2847E693DEC337D2B598C32777F7F367C2B8E','source case5 predicate/allocation')
    ledger_bytes=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    need(sha(ledger_bytes)==LEDGER,'complete tracked ownership ledger')
    ledger=json.loads(ledger_bytes)
    need(ledger['normalized_interval_count']==1394 and ledger['layer_count']==70,'complete1394 interval/70layer extent')
    irq_spans=[[irq.ADAPTER,irq.ADAPTER_LIMIT],[irq.START,irq.LIMIT]]
    need(irq_spans==[[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0]],'full v73 IRQ reservations including erased tails')
    owned=[[0,0x400000]]+ledger['merged_union']+irq_spans+[[irq.SITE,irq.SITE+4],[0x36E5EC,0x36E5F0]]
    entry_scan=cave_check(before,entry.SELECTOR,entry.SELECTOR+128,owned)
    selector,count=entry.code()[0x5C9900]
    need(len(selector)==104 and count==80 and sha(selector)=='9408A3EE46D6FE57F025611FD9C5BDDA2D92A51341F2382B33A3DBD8F51A39E7','reviewed original selector body')
    selector=bytearray(selector);selector[76:80]=branch(entry.SELECTOR+76,0x33FD08)
    ew=[(entry.HOOK,word(0xE59F80A8),branch(entry.HOOK,entry.SELECTOR)),
        (entry.SELECTOR,b'\xff'*104,bytes(selector))]
    d0=apply(before,ew);need(sha(d0)==D0,'exact approved D0 entry intermediate')
    target_contract=target.contract(d0,gba,source) # Pure code/source proof; no capture_memory().
    tw=[(a,word(old),word(new))for a,old,new in target.WRITES]
    fixed=apply(d0,tw);need(sha(fixed)==TARGET,'exact approved84D target intermediate')
    hud_contract=hud.source_contract(fixed,gba,source)
    hud_scan=cave_check(fixed,hud.CAVE,hud.CAVE+16,owned+[[entry.HOOK,entry.HOOK+4],[entry.SELECTOR,entry.SELECTOR+128]])
    hw=[(hud.HOOK,word(0xE3590007),branch(hud.HOOK,hud.CAVE)),
        (hud.CAVE,b'\xff'*16,struct.pack('<3I',0xE359000B,0x012FFF1E,0xE3590007)+branch(hud.CAVE+12,0x373EDC))]
    guarded=apply(fixed,hw);need(sha(guarded)==HUD,'exact approved HUD intermediate')
    normal_contract=nonfatal.source_contract(guarded,gba,source) # Pure resident/source contracts.
    nw=[(nonfatal.HOOK,word(0xE59F805C),branch(nonfatal.HOOK,nonfatal.ADAPTER))]
    after=apply(guarded,nw);need(sha(after)==OUTPUT,'exact approved combined6D identity')
    groups=[ew,tw,hw,nw];writes=sum(groups,[])
    spans=sorted((a,a+len(old))for a,old,_ in writes)
    need(len(spans)==10 and all(z<=a for (_,z),(a,_)in zip(spans,spans[1:])),'ten pairwise disjoint write spans')
    validate(before,after,writes)
    # All four approved deltas commute; each complete inverse restores v73.
    orders=0
    for order in itertools.permutations(groups):
        flat=sum(order,[]);candidate=apply(before,flat)
        need(candidate==after,'four-component commutation');validate(before,candidate,flat);orders+=1
    c8=apply(d0,hw)
    need(sha(c8)==nonfatal.C8,'independently reproduced approved C8 branch')
    entry_cases=entry.join_check(after)
    rejected=[]
    for at in [a for a,_,_ in writes]+[0x6FF3E8,0x6FF410,0x6FF720,0xB9E68,0x36E5EC]:
        damaged=bytearray(after);damaged[at]^=1
        try:validate(before,damaged,writes)
        except ValueError:rejected.append(at)
        else:raise ValueError('ineffective inverse mutation '+hex(at))
    return after,dict(schema=1,status='REPRODUCIBLE_APPROVED_COMPONENT_COMPOSITION',
        input_sha256=INPUT,retail_sha256=GBA,source_sha256=SOURCE,output_sha256=OUTPUT,
        intermediates=dict(entry=D0,target=TARGET,hud=HUD,entry_hud=nonfatal.C8),
        writes=[dict(raw=a,bytes=len(old),before=old.hex().upper(),after=new.hex().upper())for a,old,new in writes],
        declared_bytes=sum(len(old)for _,old,_ in writes),changed_bytes=sum(x!=y for x,y in zip(before,after)),
        reservations=[[entry.SELECTOR,entry.SELECTOR+128],[hud.CAVE,hud.CAVE+16]],
        inherited_IRQ_reservations=irq_spans,layout_ledger_sha256=LEDGER,
        ownership=dict(entry_predecessor=INPUT,entry=entry_scan,HUD_predecessor=TARGET,HUD=hud_scan),
        source_contracts=dict(target=target_contract,HUD=hud_contract,nonfatal=normal_contract),
        whole_ROM_inverse=True,component_commutation_orders=orders,actual_ARM_selector_join_cases=entry_cases,
        inverse_mutations_rejected=rejected,new_behavior=False,new_RAM_or_task=False,
        historical_ROM_or_capture_dependency=False,runtime_executed_by_builder=False,
        runtime_acceptance_pending=True,main_chain_promotion_approved=False,
        limits=['Composition identity and retained source contracts only; actual nonlethal hit/expiry and terminal acceptance remain separate.',
                'Existing generic upper event48, residual8EF3 domain, and bounded stationary transition limitations are retained.',
                'Target contract retains documented SWI6 ABI boundary; no BIOS or hardware executes in this packaging check.'],
        dependencies={**DEPS,Path(__file__).name:sha(Path(__file__).read_bytes())})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','gba','source','output'):p.add_argument(name,type=Path)
    p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    need(len({v.resolve()for v in (a.input,a.gba,a.source,a.output,a.manifest)})==5,'distinct input/output paths')
    need(not a.output.exists() and not a.manifest.exists(),'fresh isolated outputs')
    result,report=build(a.input.read_bytes(),a.gba.read_bytes(),a.source.read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(result)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('[COMPOSITION PASS; RUNTIME ACCEPTANCE SEPARATE] '+report['output_sha256'])


if __name__=='__main__':main()
