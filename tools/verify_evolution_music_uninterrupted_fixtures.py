"""Independent four-word render-only delta and ARM zero/nonzero path gate."""
from pathlib import Path
import hashlib,json,struct
from verify_shoot_attack_dispatch import Machine
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(v,s):
    if not v:raise ValueError(s)
def main():
    d=ROOT/'build/evolution-music-render-fixtures-20261110-r2';p=ROOT/'build/evolution-music-render-fixtures-20261110-r1'
    raw=(d/'manifest.json').read_bytes();need(sha(raw)=='CE2DC41BB52843B7022027A724115F30D9A5D9695302F7633655590A46028AD9','r2 manifest')
    m=json.loads(raw);prior=json.loads((p/'manifest.json').read_bytes());native=(ROOT/'build/wsc-evolution-music-20261110/component-r1.gba').read_bytes()
    need(sha(native)==m['native_component_sha256']=='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049','component')
    need(sha((p/'manifest.json').read_bytes())==m['prior_fixture_manifest_sha256']=='FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F','r1 manifest')
    need(sha((ROOT/'tools/build_evolution_music_uninterrupted_fixtures.py').read_bytes())==m['generator_sha256']=='E8FB33FC6C0857E8DEC4AD1D8D15695632305F24ADD0E3B260054D9A24A94C82','generator')
    site=0x37B47C;old=bytes.fromhex('c00900eb');nop=bytes.fromhex('0000a0e1');need(native[site:site+4]==old,'old BL')
    word=struct.unpack('<I',old)[0];need(0x8000000+site+8+(word&0xffffff)*4==0x837DB84,'BL target')
    need(native[0x37DB84:0x37DB90]==bytes.fromhex('00c09fe51cff2fe1b1c33708'),'actual stop bridge')
    cases=0;results=[];need([x['source_base_id'] for x in m['fixtures']]==[56,60,64,248],'four exact categories')
    for f in m['fixtures']:
        previous=next(x for x in prior['fixtures'] if x['file']==f['prior_file']);before=(p/f['prior_file']).read_bytes();after=(d/f['file']).read_bytes()
        need(sha(before)==f['prior_sha256']==previous['output_sha256'] and sha(after)==f['output_sha256'],'fixture pins')
        expected=bytearray(before);expected[site:site+4]=nop;need(after==expected,'entire image only four-byte NOP')
        inverse=bytearray(after);inverse[site:site+4]=old;need(inverse==before,'r2 inverse')
        for w in previous['writes']:
            at=w['offset'];blob=bytes.fromhex(w['before_hex']);inverse[at:at+len(blob)]=blob
        need(inverse==native,'whole chain inverse')
        for song in (0,1,108,111):
            snapshots=[]
            for rom in (before,after):
                cpu=Machine(rom,seed=29);cpu.r[8]=song;cpu.r[13]=0x03007E00;cpu.r[14]=0x09000000;initial=list(cpu.r);calls=[]
                cpu.services={0x0837DB84:lambda c:calls.append('stop'),0x0837DB78:lambda c:calls.append('play')}
                cpu.run(0x0837B44C,{0x09000000});need(cpu.r[13]==initial[13] and cpu.r[14]==initial[14],'stack and return');snapshots.append((list(cpu.r),calls));cases+=1
            need(snapshots[0][0]==snapshots[1][0],'register equivalence at stubbed service boundary')
            need(snapshots[0][1]==(['stop'] if song==0 else ['play']) and snapshots[1][1]==([] if song==0 else ['play']),'only zero stop omitted')
        results.append(dict(file=f['file'],sha256=sha(after),declared_bytes=4,changed_bytes=4))
    report=dict(status='PASS_RENDER_ONLY',verifier_sha256=sha(Path(__file__).read_bytes()),fixtures=results,actual_arm_boundary_cases=cases,limits=['Every global zero-song stop is suppressed in these test images, not only one invocation.','Imported M4A service boundary observed; synthesizer not executed here.','Other song replacements remain possible. No production/gameplay lifetime or completed playback claim.'])
    out=ROOT/'build/evolution-music-uninterrupted-fixtures-qa-20261110/report.json';out.parent.mkdir(exist_ok=True);need(not out.exists(),'fresh report');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(report_sha256=sha(out.read_bytes()),verifier_sha256=report['verifier_sha256'])))
if __name__=='__main__':main()
