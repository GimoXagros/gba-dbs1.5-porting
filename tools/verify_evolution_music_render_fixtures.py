"""Independent exact fixture inverses and observed boot-row binding; no emulator."""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)
def main():
    folder=ROOT/'build/evolution-music-render-fixtures-20261110-r1'
    raw=(folder/'manifest.json').read_bytes()
    need(sha(raw)=='FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F','frozen fixture manifest')
    m=json.loads(raw)
    need(sha((ROOT/'tools/build_evolution_music_render_fixtures.py').read_bytes())==m['fixture_generator_sha256']=='DAB6E9274AF918B3FAA4BC9D34FB5A4E15892336437BD827868F137628EDD8E1','frozen generator')
    wsc=(Path.home()/'Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc').read_bytes()
    gba=(ROOT/'build/wsc-evolution-music-20261110/component-r1.gba').read_bytes()
    cm=(ROOT/'build/wsc-evolution-music-20261110/component-r1.json').read_bytes()
    need(sha(wsc)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','original WSC')
    need(sha(gba)=='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049','isolated native r1')
    need(sha(cm)==m['component_manifest_sha256'],'component manifest')
    component=json.loads(cm);writes={x['label']:x for x in component['writes']}
    source=(ROOT/'build/bgm-wsc-boot-discovery-20261110-a/music-requests.txt').read_bytes()
    native=(ROOT/'build/bgm-gba-boot-discovery-20261110-a/music-requests.txt').read_bytes()
    need(sha(source)==m['source_discovery_sha256'] and sha(native)==m['native_discovery_sha256'],'actual boot logs')
    lines=source.decode().splitlines();boot=[x for x in lines if x.startswith('frame=521 ')];need(len(boot)==1,'unique source initialization')
    need(any(x.startswith('frame=520 id=00DC type=0004 ') for x in lines),'source request preceding initialization')
    for i in range(4):
        state,channel,offset=struct.unpack_from('<HHH',wsc,0x3F0528+6*i)
        need(state==168+42*i and channel==i and f'slot{4+i}={offset:04X}/ch{32+i}' in boot[0],'source initialized original descriptor')
    need(native.decode().splitlines()[-2:]==['frame=534 id=0001 type=0004 flags=0100','frame=535 id=0001 type=0004 flags=0000'],'native request then consumed flag')
    results=[];need(len(m['fixtures'])==8,'eight fixtures')
    for idx,f in enumerate(m['fixtures']):
        cat=idx//2;sid=(0x38,0x3C,0x40,0xF8)[cat];isw=idx%2==0
        need((f['category'],f['source_base_id'],f['platform'])==(cat,sid,'WSC' if isw else 'GBA'),'ordered exact category coverage')
        before=wsc if isw else gba;after=(folder/f['file']).read_bytes();expected=bytearray(before)
        if isw:
            descriptors=wsc[0x3F0000+6*sid:0x3F0000+6*(sid+4)]
            need(sorted(struct.unpack_from('<H',descriptors,6*i+2)[0] for i in range(4))==list(range(4)),'four source hardware voices')
            expected[0x3F0528:0x3F0540]=descriptors
            expected[-2:]=struct.pack('<H',sum(expected[:-2])&65535)
            spans=[(0x3F0528,24),(len(wsc)-2,2)]
        else:
            row=gba[0xD33000+8*(108+cat):0xD33000+8*(109+cat)]
            ptr,player,second=struct.unpack('<IHH',row);header=ptr-0x08000000
            need((player,second)==(0,0) and header==component['schedules'][cat]['header'],'exact native row/player')
            need(gba[header]==4 and struct.unpack_from('<I',gba,header+4)[0]==0x08000000+writes['original_wave_voices']['offset'],'four tracks/source voice bank')
            for i in range(4):
                track=struct.unpack_from('<I',gba,header+8+4*i)[0]-0x08000000
                need(0x800000<=track<len(gba) and gba[track] in (0xBB,0xBC),'bounded native track entry')
            expected[0xD33008:0xD33010]=row;spans=[(0xD33008,8)]
        need(after==expected,'independently reconstructed whole fixture')
        need(sha(before)==f['input_sha256'] and sha(after)==f['output_sha256'],'fixture pins')
        need([(x['offset'],len(bytes.fromhex(x['before_hex']))) for x in f['writes']]==spans,'exact manifest spans')
        inverse=bytearray(after)
        for x,(at,size) in zip(f['writes'],spans):
            need(bytes.fromhex(x['before_hex'])==before[at:at+size] and bytes.fromhex(x['after_hex'])==after[at:at+size],'manifest old/new bytes')
            inverse[at:at+size]=before[at:at+size]
        need(inverse==before,'whole inverse')
        changed=sum(a!=b for a,b in zip(before,after));need(changed==f['changed_bytes'],'changed count')
        results.append(dict(file=f['file'],sha256=sha(after),changed_bytes=changed))
    report=dict(status='PASS',verifier_sha256=sha(Path(__file__).read_bytes()),fixtures=results,boot_evidence='Original source DC requested520 initialized521; native01 requested534 consumed535',limits=['No fixture runtime or audio was executed by this audit.','Boot substitutions do not prove evolution activation, complete playback, title identity or audible parity.','Later ordinary boot requests may interrupt these scores.'])
    out=ROOT/'build/evolution-music-render-fixtures-qa-20261110/report.json';out.parent.mkdir(exist_ok=True)
    need(not out.exists(),'fresh report');out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',report_sha256=sha(out.read_bytes()),verifier_sha256=report['verifier_sha256'])))
if __name__=='__main__':main()
