#!/usr/bin/env python3
"""Independent source-only composition QA; reuse frozen proofs, no old suites."""
from pathlib import Path
import argparse
from contextlib import ExitStack
import hashlib
import importlib
import itertools
import json
import struct
from unittest.mock import patch

import verify_shoot_runtime_entry_probe as entry
import verify_shoot_presentation_target_lifetime as target
import verify_shoot_score_hud_guard as hud
import verify_shoot_stage11_runtime_probe as nonfatal
import verify_shoot_fatal_callback_route as fatal
import verify_shoot_caller_resident as refs

ROOT=Path(__file__).resolve().parents[1]
BASE=0x08000000
INPUT='6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7'
OUTPUT='6D883A52A1F13467477DC0733D6B349510703A66CA4D7AC74436ABB7E9D00331'
D0='D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
FIXED='84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B'
HUD='8AA1A58844C31681EAB9816D1131C072F89FE4DD5EFA6F001F5C0F641088279D'
AUTHOR='2C73B081970F3466CEE1932AC15CAA876F3292CB6A2C59916C6AE2071D652E2E'
PROOFS={
 'verify_shoot_runtime_entry_probe.py':'FBC762178FE59DB9797B2272B5776C429608FC48747AFDC16A3ACAB91C37A05F',
 'verify_shoot_presentation_target_lifetime.py':'F384BDBDEDF0F10AF62AC3CE968599BA4C8BB6E3BA3A31D32DFCAE3F3C8888EC',
 'verify_shoot_score_hud_guard.py':'AB2B16EBFFEFD5617ED0C7275F64B459077548473AF545159FCED2618BBB0407',
 'verify_shoot_stage11_runtime_probe.py':'259061E232A4B3C2462112711B48196EEFF736194C35E904EB1803E5B3B885E7',
 'verify_shoot_fatal_callback_route.py':'48600765FC794FBB3A0859520125AB21B3736DCDAD76B491F020F71ADCFBFCF0',
 'verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def word(v):return struct.pack('<I',v)
def branch(at,to):return word(0xEA000000|(((to-at-8)//4)&0xFFFFFF))

def apply(before,writes):
    out=bytearray(before)
    for at,old,new in writes:
        need(len(old)==len(new)and out[at:at+len(old)]==old,'ExpectedWrite '+hex(at))
        out[at:at+len(new)]=new
    return bytes(out)

def inverse(before,after,writes):
    need(len(before)==len(after)==0x800000,'complete eight MiB')
    need(apply(after,[(a,n,o)for a,o,n in writes])==before,'whole composition inverse')

def ownership(data,spans,owned):
    for start,end in spans:
        need(not any(a<end and start<z for a,z in owned),'full reservation ownership '+hex(start))
        need(data[start:end]==b'\xff'*(end-start),'full erased cave '+hex(start))
    refs.SPANS=tuple(spans)
    need(refs.inbound(data)==[],'all-alignment mirrored pointer ARM Thumb scan without exemptions')

def production_api(before,gba,source):
    """Implementation API probe only; its results never define expected writes."""
    prod=importlib.import_module('build_shoot_native_scene_connection')
    reads=[];read=Path.read_bytes
    ledger=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').resolve()
    toolroot=(ROOT/'tools').resolve()
    def safe_read(path):
        resolved=path.resolve()
        need(resolved==ledger or(resolved.parent==toolroot and resolved.suffix=='.py'),
             'production historical/capture input denied '+str(path))
        reads.append(resolved.relative_to(ROOT).as_posix())
        return read(path)
    def denied(*args,**kwargs):raise ValueError('old capture/build/write API forbidden')
    with ExitStack()as stack:
        stack.enter_context(patch.object(Path,'read_bytes',safe_read))
        stack.enter_context(patch.object(Path,'write_bytes',denied))
        stack.enter_context(patch.object(Path,'write_text',denied))
        for module in (prod.entry,prod.target,prod.hud,prod.nonfatal):
            stack.enter_context(patch.object(module,'build',denied))
        stack.enter_context(patch.object(prod.target,'capture_memory',denied))
        result,report=prod.build(before,gba,source)
    return result,report,sorted(set(reads))

def audit(before,after,gba,source,manifest):
    need((sha(before),sha(after),sha(gba),sha(source))==(INPUT,OUTPUT,entry.GBA,entry.SOURCE),'immutable ROM identities')
    need(sha((ROOT/'tools/build_shoot_native_scene_connection.py').read_bytes())==AUTHOR,'frozen packaging author')
    for name,digest in PROOFS.items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'frozen independent proof '+name)
    ledger_blob=(ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    need(sha(ledger_blob)==entry.LAYOUT,'tracked ledger identity')
    ledger=json.loads(ledger_blob)
    need((ledger['normalized_interval_count'],ledger['layer_count'])==(1394,70),'full ownership inventory')
    owned=[[0,0x400000]]+ledger['merged_union']+[[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0],
        [0xD0BE8,0xD0BEC],[0x36E5EC,0x36E5F0]]
    selector=after[0x6FF380:0x6FF3E8]
    ew=[(0x33FD04,word(0xE59F80A8),branch(0x33FD04,0x6FF380)),(0x6FF380,b'\xff'*104,selector)]
    d0=apply(before,ew);need(sha(d0)==D0,'entry intermediate identity')
    entry.structural(before,d0,ledger_blob,scan=False)
    entry_contract=entry.source_contract(source,gba,before,d0)
    ownership(before,[(0x6FF380,0x6FF400)],owned)
    tw=[(a,word(old),word(new))for a,old,new in target.WORDS]
    fixed=apply(d0,tw);need(sha(fixed)==FIXED,'target intermediate identity')
    target.structure(d0,fixed)
    target_contract=target.source_and_helpers(d0,fixed,gba,source)
    hw=[(0x373ED8,word(0xE3590007),branch(0x373ED8,0x6FF400)),
        (0x6FF400,b'\xff'*16,word(0xE359000B)+word(0x012FFF1E)+word(0xE3590007)+branch(0x6FF40C,0x373EDC))]
    guarded=apply(fixed,hw);need(sha(guarded)==HUD,'HUD intermediate identity')
    hud.structure(fixed,guarded)
    hud_contract=hud.source_and_callers(source,gba,fixed,guarded)
    ownership(fixed,[(0x6FF400,0x6FF410)],owned+[[0x6FF380,0x6FF400],[0x33FD04,0x33FD08]])
    nw=[(0x36E634,word(0xE59F805C),branch(0x36E634,0x5CD9A0))]
    expected=apply(guarded,nw);need(expected==after,'all ten independently constructed spans')
    nonfatal_contract=nonfatal.bindings(fixed,after,gba,source)
    need(sha(after[0x5CD9A0:0x5CDA3C])==nonfatal.ADAPTER_SHA,'preexisting156-byte nonfatal adapter retained')
    families=(ew,tw,hw,nw);writes=sum(families,[])
    spans=sorted((a,a+len(old))for a,old,_ in writes)
    need(len(spans)==10 and sum(z-a for a,z in spans)==152 and all(z<=a for(_,z),(a,_)in zip(spans,spans[1:])),'ten disjoint spans152 bytes')
    inverse(before,after,writes)
    irq=bytearray(before);irq[0x36E5EC:0x36E5F0]=word(0xE1A00005)
    need(sha(irq)==fatal.BEFORE,'join exact preexisting guarded IRQ identity')
    fatal.exact_change(bytes(irq),before)
    for order in itertools.permutations(families):
        need(apply(before,sum(order,[]))==after,'independent24-order component commutation')
    rejected=[]
    for at in [a for a,_,_ in writes]+[0x6FF3E8,0x6FF410,0x6FF720,0x6FFECF,0xB9E68,0x36E5EC]:
        damaged=bytearray(after);damaged[at]^=1
        try:inverse(before,damaged,writes)
        except ValueError:rejected.append(at)
        else:raise ValueError('ineffective inverse mutation '+hex(at))
    actual,actual_report,reads=production_api(before,gba,source)
    need(actual==after,'production API matches independently expected output')
    expected_writes=[dict(raw=a,bytes=len(old),before=old.hex().upper(),after=new.hex().upper())for a,old,new in writes]
    need(manifest==json.loads(json.dumps(actual_report)) and manifest['writes']==expected_writes and
         manifest['output_sha256']==OUTPUT and manifest['historical_ROM_or_capture_dependency']is False,
         'fresh manifest matches actual source-only API and independent spans')
    return dict(status='INDEPENDENT_NATIVE_SCENE_CONNECTION_COMPOSITION_PASS',input_sha256=INPUT,output_sha256=OUTPUT,
        retail_sha256=sha(gba),source_sha256=sha(source),builder_sha256=AUTHOR,
        intermediates=dict(entry=D0,target=FIXED,hud=HUD),written_spans=expected_writes,
        declared_bytes=152,changed_bytes=sum(a!=b for a,b in zip(before,after)),whole_ROM_inverse=True,
        prior_guarded_IRQ_sha256=sha(irq),prior_fatal_inverse=True,component_orders=24,
        reservations=[[0x6FF380,0x6FF400],[0x6FF400,0x6FF410]],inherited_IRQ_reservations=[[0x6FF600,0x6FF800],[0x6FF9C0,0x6FFED0]],
        strict_scan_exemptions=[],ownership_inventory=[1394,70],inverse_mutations_rejected=rejected,
        source_contracts=dict(entry=entry_contract,target=target_contract,HUD=hud_contract,nonfatal=nonfatal_contract),
        production_read_allowlist='tracked tools/*.py plus exact tracked ownership ledger only; ROM originals supplied in memory',
        observed_production_reads=reads,old_build_capture_and_file_write_APIs_denied=True,
        observed_author_selector_joins=actual_report['actual_ARM_selector_join_cases'],
        dependencies={**PROOFS,Path(__file__).name:sha(Path(__file__).read_bytes())},
        qualification='Source-only packaging equality, not runtime acceptance. Prior broad semantic suites reused by frozen proof hashes; no captured data/save/emulator required. Child rectangle1477 remains a separate component; final main promotion and positive-hit/expiry/terminal gate remain with root.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','gba','source','manifest','report'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    result=audit(*(getattr(a,k).read_bytes()for k in ('before','after','gba','source')),json.loads(a.manifest.read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
