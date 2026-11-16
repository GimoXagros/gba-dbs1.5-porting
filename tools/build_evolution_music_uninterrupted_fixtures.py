"""Four NEW render-only native fixtures with global song-zero stop disabled.

This intentionally changes test-ROM lifetime. It must never be a production
music layer. Existing source/native r1 fixtures and the main ROM remain intact.
"""
import argparse
import json
from pathlib import Path
import struct
from analyze_wsc_evolution_music import need,sha
from verify_shoot_attack_dispatch import Machine

NATIVE='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049'
PRIOR='FC885F9B64A8E5356A1D0A07877DAAC3E8E7160A03A220DDE5E176B329F3F95F'
SITE=0x37B47C
OLD=bytes.fromhex('c00900eb')
NOP=bytes.fromhex('0000a0e1')

def control(rom,zero,expect_stop):
    m=Machine(rom,seed=7);m.r[13]=0x03007F00;m.r[14]=0x09000000;m.r[8]=0 if zero else 1
    calls=[]
    m.services={0x0837DB84:lambda m:calls.append('global-stop'),
                0x0837DB78:lambda m:calls.append('play-song')}
    sp=m.r[13];before0=m.r[0]
    m.run(0x0837B44C,{0x09000000})
    need(m.r[13]==sp and m.r[14]==0x09000000,'retained actual stack/return ABI')
    need(calls==(['global-stop'] if expect_stop else [] if zero else ['play-song']),'actual zero/nonzero branch services')
    need(m.r[0]==before0,'test service boundary preserves R0')
    return dict(song_argument=m.r[8],calls=calls,stack_restored=True,
                service_boundary='M4A imported stop/play call observed; downstream synthesizer not modeled')

def main():
    p=argparse.ArgumentParser()
    for name in ('prior-directory','native','output-directory'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();paths=[a.prior_directory.resolve(),a.native.resolve(),a.output_directory.resolve()]
    need(len(set(paths))==3 and not a.output_directory.exists(),'fresh distinct output directory')
    raw=(a.prior_directory/'manifest.json').read_bytes();need(sha(raw)==PRIOR,'frozen r1 fixture manifest')
    prior=json.loads(raw);native=a.native.read_bytes();need(sha(native)==NATIVE,'frozen development component')
    need(native[0x37B478:0x37B488]==bytes.fromhex('00402de9c00900eb0040bde81eff2fe1'),'zero-branch call and exact unwind')
    need(native[0x37DB84:0x37DB90]==bytes.fromhex('00c09fe51cff2fe1b1c33708'),'real ARM→Thumb global-stop bridge')
    word=struct.unpack('<I',OLD)[0]
    need(0x08000000+SITE+8+(word&0xFFFFFF)*4==0x0837DB84,'actual replaced BL target')
    need(native[0x37C3B0:0x37C3D4]==bytes.fromhex('30b508480004000c002808d0064d041c286800f001fb0c35013c002cf8d130bc01bc0047'),
         'actual all-player loop and MPlayStop target')
    records=[];pending=[];cases=[control(native,True,True),control(native,False,False)]
    for entry in prior['fixtures']:
        if entry['platform']!='GBA':continue
        before=(a.prior_directory/entry['file']).read_bytes()
        need(sha(before)==entry['output_sha256'] and before[SITE:SITE+4]==OLD,'exact prior native fixture')
        after=bytearray(before);after[SITE:SITE+4]=NOP
        need([i for i,(x,y) in enumerate(zip(before,after,strict=True)) if x!=y]==[SITE,SITE+1,SITE+2,SITE+3],'only exact4B fixture delta')
        inverse=bytearray(after);inverse[SITE:SITE+4]=OLD
        need(bytes(inverse)==before,'r2→r1 fixture inverse')
        for write in entry['writes']:
            blob=bytes.fromhex(write['before_hex']);at=write['offset'];inverse[at:at+len(blob)]=blob
        need(bytes(inverse)==native,'full r2→development component inverse')
        cases.extend((control(bytes(after),True,False),control(bytes(after),False,False)))
        name=entry['file'].replace('-boot-fixture','-uninterrupted-fixture')
        pending.append((name,bytes(after)))
        records.append(dict(file=name,source_base_id=entry['source_base_id'],native_id=entry['native_id'],
                            prior_file=entry['file'],prior_sha256=sha(before),output_sha256=sha(after),
                            writes=[dict(offset=SITE,before_hex=OLD.hex(),after_hex=NOP.hex(),label='test-only omit global stop')],
                            inverse_chain=['exact r1 fixture','exact DD6D73B5 component']))
    need(len(records)==4,'four native fixtures only')
    report=dict(purpose='RENDER ONLY: global song-zero stop disabled, not normal gameplay proof',
                generator_sha256=sha(Path(__file__).read_bytes()),native_component_sha256=NATIVE,
                prior_fixture_manifest_sha256=PRIOR,fixtures=records,actual_ARM_cases=cases,
                guest_writes=False,emulator_executed=False,
                reason='Initial native38 audio was cut at normal boot global stop; source00 affects foreground slots only.',
                limits=['Suppresses every global song-zero stop in these four test ROMs, not just one observed invocation.',
                        'Other boot song replacements can still interrupt a score and must be logged.',
                        'No production change or ordinary evolution lifetime conclusion follows.'])
    a.output_directory.mkdir(parents=True)
    for name,data in pending:(a.output_directory/name).write_bytes(data)
    out=a.output_directory/'manifest.json';out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(sha(out.read_bytes()))

if __name__=='__main__':main()
