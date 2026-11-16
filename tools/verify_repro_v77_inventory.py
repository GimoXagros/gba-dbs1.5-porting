"""Completed v77 inventory and independent parallel-layer inverses; no build rerun."""
import argparse,ast,json
from pathlib import Path
from verify_repro_v74_inventory import ROOT,need,sha,read,inventory
PRIOR=ROOT/'build/repro-v76-final-audit-20261110/audit.json'
PRIOR_SHA='130361D12CC96B26EDA90042A832F1D86304C8E725F459AD3AE5B76D1A5EBB5F'
DISPLAY='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
AUDIO='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049'
COMPOSED='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
OUTPUT='C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278'
PINS={
 'tools/build_evolution_music_pause_cache.py':'7488DE49EC398BF0C1AD7FBFB4AA04A2EBB133ECBE17DC6227A6BE3123F03810',
 'tools/verify_evolution_music_pause_cache.py':'E678081D5082ACA480722743FBE90491A6FD6D6478706F1FC796DD07B8AFB462',
 'tools/build_current_candidate.py':'15DC1DAB1DAE7766D312A0F666E23D3F5EACEF78B9CEB680DE55FEF2BB0A47CF',
 'tools/verify_result_language_capture.py':'DA8D3AA45AFE81D6EDF328F084B69F333E138CF8FAEEA71BAA0AAF94347D1085',
 'tools/build_evolution_music_integration.py':'1BFF03992429A94CAF1143D02A84165581B19699A7597E7CC77FBB6905DB5794',
 'tools/verify_evolution_music_display_composition.py':'00612F8F332D8C4217F7C35DC3625D11AD212E5D0F82F175989CBE36F712F6A5',
 'tools/analyze_wsc_evolution_music.py':'2ED6FD43C11F636C11D38415AB07BA6B8FBE6E92531EB58890572BDCD09F8413',
 'tools/build_wsc_evolution_music.py':'E477925703C4DCD66A5239DCA1F0A806E208DAF02AD2FE95998C055330FC0077',
 'tools/verify_wsc_evolution_music_author.py':'E7AA94C393372062C9B526B3C5AF941553AA8013F0A8DA892CA99B71AAB330A9'}
ADDED={'evolution-music-display.gba','evolution-music-display.json','intermediate/evolution-music-pause-verification.json','shoot-display-epoch.gba','shoot-display-epoch.json','evolution-music.gba','evolution-music.json','intermediate/evolution-music-author-verification.json','intermediate/evolution-music-integration-verification.json'}
SPANS=((0x6FF6E8,4),(0x6FF720,72),(0x6FFDE8,4),(0x6FFDEC,4))
BUILDS=[ROOT/'build'/('repro-v77-20261110-'+x) for x in ('c','d')]
EXCLUDED_SAVE = BUILDS[1] / 'current-candidate.sav'


def completed_inventory(directory):
    paths = sorted(path for path in directory.rglob('*') if path.is_file())
    artifacts = {
        path.relative_to(directory).as_posix(): sha(read(path))
        for path in paths if path != EXCLUDED_SAVE
    }
    return artifacts, len(paths)


def audit(completed):
    need(completed,'root confirms both complete before output reads')
    need(sha(read(PRIOR))==PRIOR_SHA,'frozen completed v76 audit');prior=json.loads(read(PRIOR));old=prior['sha256_by_relative_path']
    need(prior['status']=='PASS' and prior['final_sha256']==DISPLAY and len(old)==310,'v76 baseline')
    pins={**prior['source_tool_sha256'],**PINS,'tools/'+Path(__file__).name:sha(read(Path(__file__)))}
    for path,h in pins.items():need(sha(read(ROOT/path))==h,'frozen source '+path)
    baseline=[ROOT/'build'/('repro-v76-20261110-'+x) for x in ('a','b')];need(all(inventory(p)==old for p in baseline),'old builds retained')
    snapshots = [completed_inventory(directory) for directory in BUILDS]
    actual = [artifacts for artifacts, _ in snapshots]
    physical_counts = [count for _, count in snapshots]
    need(physical_counts == [319, 320] and EXCLUDED_SAVE.is_file(), 'only d has the extra save path')
    need(actual[0] == actual[1], 'fresh complete build artifact inventories equal')
    need(not old.keys()-actual[0].keys() and actual[0].keys()-old.keys()==ADDED,'nine exact additions no loss')
    need(len(actual[0])==len(old)+len(ADDED)==319,'derived319 files')
    changed=sorted(k for k in old.keys()&actual[0].keys() if old[k]!=actual[0][k]);need(changed==['build-manifest.json','current-candidate.gba','current-candidate.json'],'three shared changes only')
    artifacts={'evolution-music-display.gba':COMPOSED,'current-candidate.json':'32A7942A7945B12EF191995B908DC8844C1935DA33340B0484700E4813203B8B','intermediate/evolution-music-pause-verification.json':'1E30456EC7394CF98D74B94D4AB3EBA49D7F1D084A4094E71EFE4BEF987EE022','shoot-display-epoch.gba':DISPLAY,'shoot-display-epoch.json':old['current-candidate.json'],'evolution-music.gba':AUDIO,'evolution-music.json':'AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91','current-candidate.gba':OUTPUT,'intermediate/evolution-music-author-verification.json':'D7B0A1E03B1AA25F7B627FF0CA316DF09364FEF12F6664FC7B17AEA3FF20B0FD','intermediate/evolution-music-integration-verification.json':'FAFF1A4105F0F9A555FAB4FA18B3599EBA27915B6796E51C19AF27F4A1A38FD0'}
    for p,h in artifacts.items():need(actual[0][p]==h,'artifact '+p)
    tree=ast.parse(read(ROOT/'tools/build_current_candidate.py'));expected={};sections={}
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id.startswith('EXPECTED_'):expected[t.id]=ast.literal_eval(n.value)
    for n in ast.walk(tree):
        if isinstance(n,ast.Dict):
            for k,v in zip(n.keys,n.values):
                if isinstance(k,ast.Constant) and k.value in ('claim_scope','original_evolution_music'):sections[k.value]=ast.literal_eval(v)
    need(len(sections)==2,'literal music and claim contracts');oldbm=json.loads(read(baseline[0]/'build-manifest.json'));closures=[]
    for directory in BUILDS:
        owner=read(directory/'shoot-owner-link.gba');display=read(directory/'shoot-display-epoch.gba');audio=read(directory/'evolution-music.gba');final=read(directory/'evolution-music-display.gba');patched=read(directory/'current-candidate.gba')
        need(len(owner)==len(display)==0x800000 and len(audio)==len(final)==len(patched)==0x1000000,'exact extents')
        combined=bytearray(audio)
        for at,size in SPANS:combined[at:at+size]=display[at:at+size]
        need(combined==final,'whole disjoint composition')
        back=bytearray(final)
        for at,size in SPANS:back[at:at+size]=owner[at:at+size]
        need(back==audio,'whole display inverse to audio')
        music=json.loads(read(directory/'evolution-music.json'));inverse=bytearray(audio);whole=bytearray(final);covered=set()
        for w in music['writes']:
            at=w['offset'];size=w['size'];blob=bytes.fromhex(w['before_hex']);need(len(blob)==size and not covered.intersection(range(at,at+size)),'disjoint exact write');covered.update(range(at,at+size))
            need(sha(audio[at:at+size])==w['after_sha256'],'music payload hash');inverse[at:at+size]=blob;whole[at:at+size]=blob
        need(not any(covered.intersection(range(at, at + size)) for at, size in SPANS), 'disjoint display and music writes')
        need(inverse==owner+b'\xff'*0x800000 and whole==display+b'\xff'*0x800000,'whole music inverses and erased extension')
        need(len(covered)==104245 and sum(a!=b for a,b in zip(audio,owner+b'\xff'*0x800000))==104216,'actual music byte counts')
        need(final[0x37B47C:0x37B480]==bytes.fromhex('c00900eb'),'production global stop retained')
        manifest=json.loads(read(directory/'evolution-music-display.json'));need(manifest['input_sha256']==DISPLAY and manifest['audio_sha256']==AUDIO and manifest['output_sha256']==COMPOSED and manifest['test_stop_suppression'] is False,'composition manifest')
        pause=json.loads(read(directory/'current-candidate.json'));restored=bytearray(patched)
        need(pause['input_sha256']==COMPOSED and pause['output_sha256']==OUTPUT and pause['declared_bytes']==24 and pause['changed_bytes']==23,'pause manifest')
        need([(w['offset'],w['size']) for w in pause['writes']]==[(0x37B458,4),(0xD7DFC0,20)],'pause spans')
        for w in pause['writes']:
            at=w['offset'];size=w['size'];need(bytes.fromhex(w['before_hex'])==final[at:at+size] and bytes.fromhex(w['after_hex'])==patched[at:at+size],'pause bytes');restored[at:at+size]=bytes.fromhex(w['before_hex'])
        need(restored==final and sum(a!=b for a,b in zip(final,patched))==23,'whole pause inverse')
        bm=json.loads(read(directory/'build-manifest.json'));need(bm.keys()-oldbm.keys()=={'original_evolution_music'} and not oldbm.keys()-bm.keys(),'one added metadata section')
        for key,value in oldbm.items():
            if key not in ('claim_scope','layers'):need(bm[key]==value,'retained metadata '+key)
        for key,value in sections.items():need(bm[key]==value,'new literal '+key)
        entries=[]
        for key,subdir,const in (('assets','converted-assets','EXPECTED_ASSETS'),('stage_assets','stage-assets','EXPECTED_STAGE_ASSETS'),('opening_assets','opening-assets','EXPECTED_OPENING_ASSETS'),('shoot_assets','shoot-assets','EXPECTED_SHOOT_ASSETS'),('layers','','EXPECTED_LAYERS')):
            need(bm[key]==expected[const],'complete closure '+key)
            for name,h in bm[key].items():
                need(Path(name).name==name and sha(read(directory/subdir/name))==h,'actual closure '+name);entries.append(dict(section=key,path=(Path(subdir)/name).as_posix(),sha256=h))
        need(len(entries)==prior['manifest_entries_each']+3==123,'derived123 entries');closures.append(entries)
    need([completed_inventory(directory) for directory in BUILDS] == snapshots, 'fresh inventories unchanged')
    need(all(inventory(directory) == old for directory in baseline), 'v76 unchanged')
    for p,h in pins.items():need(sha(read(ROOT/p))==h,'sources remain frozen '+p)
    return dict(status='PASS',files_each=len(actual[0]),
        builds=[directory.relative_to(ROOT).as_posix() for directory in BUILDS],
        physical_file_counts=physical_counts,
        excluded_path=EXCLUDED_SAVE.relative_to(ROOT).as_posix(),
        excluded_path_read_or_hashed=False,
        completion_evidence='Both build-manifest.json files are emitted after the build gates. Historical process exit codes are unavailable.',
        manifest_entries_each=len(closures[0]),final_sha256=OUTPUT,sha256_by_relative_path=actual[0],source_tool_sha256=pins,manifest_closures=closures,trusted_v76_audit_sha256=PRIOR_SHA,changed_shared_v76_paths=changed,new_relative_paths=sorted(ADDED),whole_parallel_layer_inverses=True,music_declared_bytes=104245,music_changed_bytes=104216,pause_declared_bytes=24,pause_changed_bytes=23,whole_pause_inverse=True,production_global_stop_retained=True,all_previous_artifacts_and_proofs_retained=True,independent_verifiers_rerun=[],full_build_executed=False,emulator_launched=False,final_port_complete=False)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root-completed',action='store_true');p.add_argument('--report',type=Path,required=True);a=p.parse_args();need(not a.report.exists(),'fresh report');r=audit(a.root_completed);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode());print('PASS',r['files_each'],r['manifest_entries_each'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
