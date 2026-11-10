#!/usr/bin/env python3
"""Audit only completed v75 A/B inventories, retaining the completed v74 proof."""
import argparse
import ast
import json
from pathlib import Path
from verify_repro_v74_inventory import ROOT, need, sha, read, inventory, inverse

PRIOR = ROOT/'build/repro-v74-final-audit-20261109/audit.json'
PRIOR_SHA = '02DAA8035A04909CD0277410944D1052FA4A0423CDA6E31C8319FBAF4483DDE6'
BEFORE = '1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
PALETTE = 'FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
FINAL = '46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
PALETTE_MANIFEST = '6E44701A7465E6CEBDD5E8C0B4ADA1EE48C398EA8DF2EF804530076EF3D0C310'
OWNER_MANIFEST = 'D6D66777FCA9BD4A6979F960DEAFBCDDF38D0CB2D3A112C3EF222B67AA2061FD'
PALETTE_QA = '94F9FD0FC4B95F64CA7BFB4F424DF333EF29170B8CDA32A1CA2FB4BEF0BDC840'
OWNER_QA = '8CE38E626C7629F4A1F2ABB041B55B85B94AD71809CC1B8EA8C1F8F338AF27A3'
PINS = {
    'tools/verify_result_language_capture.py':'C31719BAE4C6D1BBD6B92A6BA8C0AB04C1494339EEEDF6D0D61435CBD4279A67',
    'tools/build_current_candidate.py':'F5CDCE4F4D51FAA2D95BE30BB2C93C819494F3B1EDDE3B660E39ACFDDE5FD1C0',
    'tools/build_shoot_palette_dim_calls.py':'66E70D72AB1401A526ADB16A560FB0EFB18E42BE2F56B3A411358DEB1FB6BE91',
    'tools/build_shoot_terminal_owner_link.py':'6C57D65740F27CFA64CC5EFE892F7FAC80BDB778D3128F6BF8BED0B5DCBC930C',
    'tools/verify_shoot_palette_dim_calls_production.py':'0CACBFB6D878F2D0CED87CA35E29F704D42ED9DD52654EB4859DE56AD3DB9C9B',
    'tools/verify_shoot_terminal_owner_link_production.py':'47144AA1300AB2C26907C8343306E4C9BA1C0ADB6025AE310E43A100AFFE7C13',
}
NEW_PATHS = {'shoot-child-rectangle.gba','shoot-child-rectangle.json','shoot-palette-calls.gba',
             'shoot-palette-calls.json','intermediate/shoot-palette-calls-verification.json',
             'intermediate/shoot-owner-link-verification.json'}
PALETTE_SITES = (0x5C6F4C,0x5C6F5C,0x5C6F88,0x5C6FBC)
PALETTE_WORDS = ('2000001b','1c00001b','1100001b','0400001b')
OWNER_SITE = 0x6FFC00
BUILDS = [ROOT/'build'/('repro-v75-20261110-'+x) for x in ('a','b')]

def main_literals(blob):
    expected, sections = {}, {}
    tree = ast.parse(blob)
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for name in node.targets:
                if isinstance(name,ast.Name) and name.id.startswith('EXPECTED_'):
                    expected[name.id] = ast.literal_eval(node.value)
    for node in ast.walk(tree):
        if isinstance(node,ast.Dict):
            for key,value in zip(node.keys,node.values):
                if isinstance(key,ast.Constant) and key.value in ('claim_scope','shoot_palette_dim_calls','shoot_terminal_owner_link'):
                    sections[key.value] = ast.literal_eval(value)
    need(len(sections)==3,'all new literal contracts found')
    return expected,sections

def write_contract(before, after, manifest, expected):
    need(manifest['expected_writes']==expected,'exact independently specified words')
    for w in expected:
        a=w['offset']
        need(before[a:a+4]==bytes.fromhex(w['before']) and after[a:a+4]==bytes.fromhex(w['after']), 'actual word values')
    inverse(after,before,[(w['offset'],4) for w in expected])

def audit(root_completed):
    need(root_completed,'root must confirm both complete builds before reading either output')
    need(sha(read(PRIOR))==PRIOR_SHA,'completed v74 report identity')
    prior=json.loads(read(PRIOR)); old=prior['sha256_by_relative_path']
    need(prior['status']=='PASS' and prior['final_sha256']==BEFORE and len(old)==301 and
         prior['new_declared_bytes']==194 and prior['new_changed_bytes']==170,'completed v74 baseline contract')
    pins={**prior['source_tool_sha256'],**PINS,'tools/'+Path(__file__).name:sha(read(Path(__file__)))}
    for path,digest in pins.items():
        need(sha(read(ROOT/path))==digest,'source pin '+path)
    baseline=[ROOT/'build'/('repro-v74-20261109-'+x) for x in ('a','b')]
    need(all(inventory(path)==old for path in baseline),'both completed v74 inventories remain intact')
    actual=[inventory(path) for path in BUILDS]
    need(actual[0]==actual[1] and len(actual[0])==307,'all307 full file hashes and paths equal')
    changed=sorted(k for k in old.keys() & actual[0].keys() if old[k]!=actual[0][k])
    need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'only three changed shared paths')
    need(not old.keys()-actual[0].keys() and actual[0].keys()-old.keys()==NEW_PATHS,'exact six additions, zero removals')
    for name,digest in {
        'shoot-child-rectangle.gba':BEFORE,'shoot-child-rectangle.json':old['current-candidate.json'],
        'shoot-palette-calls.gba':PALETTE,'shoot-palette-calls.json':PALETTE_MANIFEST,
        'current-candidate.gba':FINAL,'current-candidate.json':OWNER_MANIFEST,
        'intermediate/shoot-palette-calls-verification.json':PALETTE_QA,
        'intermediate/shoot-owner-link-verification.json':OWNER_QA}.items():
        need(actual[0][name]==digest,'new and preserved output identity '+name)
    oldbm=json.loads(read(baseline[0]/'build-manifest.json'))
    expected,sections=main_literals(read(ROOT/'tools/build_current_candidate.py'))
    palette_writes=[dict(offset=a,before='feffff1b',after=v) for a,v in zip(PALETTE_SITES,PALETTE_WORDS)]
    owner_writes=[dict(offset=OWNER_SITE,before='180096e5',after='280096e5')]
    spans=[(a,4) for a in PALETTE_SITES+(OWNER_SITE,)]
    need(len(spans)==5 and sum(n for _,n in spans)==20,'five spans twenty declared bytes')
    closures=[]
    for directory in BUILDS:
        before,palette,final=(read(directory/name) for name in ('shoot-child-rectangle.gba','shoot-palette-calls.gba','current-candidate.gba'))
        pm,om=(json.loads(read(directory/name)) for name in ('shoot-palette-calls.json','current-candidate.json'))
        need((pm['input_sha256'],pm['output_sha256'],om['input_sha256'],om['output_sha256'])==
             (BEFORE,PALETTE,PALETTE,FINAL),'full manifest identity chain')
        write_contract(before,palette,pm,palette_writes); write_contract(palette,final,om,owner_writes)
        inverse(final,before,spans)
        need(sum(a!=b for a,b in zip(before,palette))==pm['changed_bytes']==12 and
             sum(a!=b for a,b in zip(palette,final))==om['changed_bytes']==1 and
             sum(a!=b for a,b in zip(before,final))==13,'full image changed-byte counts')
        for at in (0x5C6FD4,0x6FFC04,0x5BC29C,0x5B9180,0x6FF380,0x7FFFFF):
            bad=bytearray(final);bad[at]^=1
            try: inverse(bytes(bad),before,spans)
            except ValueError: pass
            else: raise ValueError('outside-write corruption accepted')
        bm=json.loads(read(directory/'build-manifest.json'))
        need(bm.keys()-oldbm.keys()=={'shoot_palette_dim_calls','shoot_terminal_owner_link'} and not oldbm.keys()-bm.keys(),'two new sections only')
        for key,value in oldbm.items():
            if key not in ('claim_scope','layers'):
                need(bm[key]==value,'existing manifest contract retained '+key)
        for key,value in sections.items(): need(bm[key]==value,'new main literal contract '+key)
        entries=[]
        for key,subdir,const in (('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),
             ('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')):
            need(bm[key]==expected[const],'main expected manifest section '+key)
            for name,digest in bm[key].items():
                need(Path(name).name==name and sha(read(directory/subdir/name))==digest,'manifest closure '+name)
                entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=digest))
        need(len(entries)==119,'all119 manifest entries recomputed');closures.append(entries)
    need(inventory(BUILDS[0])==actual[0]==inventory(BUILDS[1]),'new inventories stable throughout audit')
    need(all(inventory(path)==old for path in baseline),'v74 remains unchanged after audit')
    for path,digest in pins.items(): need(sha(read(ROOT/path))==digest,'source still frozen '+path)
    return dict(status='PASS',files_each=307,manifest_entries_each=119,final_sha256=FINAL,
        sha256_by_relative_path=actual[0],source_tool_sha256=pins,builds=[p.relative_to(ROOT).as_posix() for p in BUILDS],
        trusted_v74_audit_sha256=PRIOR_SHA,exact_v74_predecessor=BEFORE,palette_intermediate=PALETTE,
        changed_shared_v74_paths=changed,new_relative_paths=sorted(NEW_PATHS),manifest_closures=closures,
        entire_relative_path_and_hash_inventories_match=True,all_previous_artifacts_and_proofs_retained=True,
        v74_194_declared_bytes_unchanged=True,new_written_spans=5,new_declared_bytes=20,new_changed_bytes=13,
        whole_new_layers_inverse_to_v74=True,isolated_component_QA_sha256=[PALETTE_QA,OWNER_QA],
        outside_boundary_corruption_negatives_each=6,independent_verifiers_rerun=[],runtime_acceptance=False,
        limits=['Completed outputs and identity/inverse/manifest closure only; no build or semantic rerun.',
                'No emulator, State/save access, main, ROM, evidence or Git modification by auditor.',
                'Actual guard acceptance and final-port completion are separate gates.'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root-completed',action='store_true');p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    result=audit(a.root_completed);a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
    print('PASS',result['files_each'],sha(read(a.report)))

if __name__=='__main__': main()
