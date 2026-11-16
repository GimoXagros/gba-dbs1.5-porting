"""Create isolated boot-music fixtures; these are not gameplay builds.

Original and native drivers start the requested scores through ordinary boot.
Only existing boot table rows (plus the source checksum) are substituted.
No save, RAM, register, input, emulator, or production-image modification.
"""
import argparse
import json
from pathlib import Path
import struct
from analyze_wsc_evolution_music import need,sha,WSC_SHA,SONGS

NATIVE='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049'
MANIFEST='AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91'
SOURCE_BOOT=0x3F0000+0xDC*6
NATIVE_TABLE=0xD33000

def image(before,patches):
    after=bytearray(before);writes=[];allowed=set()
    for at,blob,label in patches:
        old=before[at:at+len(blob)]
        need(len(old)==len(blob),'bounded fixture write')
        after[at:at+len(blob)]=blob;allowed.update(range(at,at+len(blob)))
        writes.append(dict(offset=at,before_hex=old.hex(),after_hex=blob.hex(),label=label))
    changed={i for i,(a,b) in enumerate(zip(before,after,strict=True)) if a!=b}
    need(changed and changed<=allowed,'exact fixture diff containment')
    inverse=bytearray(after)
    for w in writes:
        blob=bytes.fromhex(w['before_hex']);inverse[w['offset']:w['offset']+len(blob)]=blob
    need(bytes(inverse)==before,'complete fixture inverse')
    return bytes(after),dict(input_sha256=sha(before),output_sha256=sha(after),
                            changed_bytes=len(changed),writes=writes)

def main():
    p=argparse.ArgumentParser()
    for key in ('wsc','native','component-manifest','source-discovery','native-discovery','output-directory'):
        p.add_argument('--'+key,required=True,type=Path)
    a=p.parse_args()
    paths=[getattr(a,k).resolve() for k in ('wsc','native','component_manifest','source_discovery','native_discovery','output_directory')]
    need(len(set(paths))==len(paths),'distinct fixture paths')
    need(not a.output_directory.exists(),'fresh fixture directory')
    wsc=a.wsc.read_bytes();native=a.native.read_bytes();manifest_bytes=a.component_manifest.read_bytes()
    need((sha(wsc),sha(native),sha(manifest_bytes))==(WSC_SHA,NATIVE,MANIFEST),'frozen original and isolated component')
    manifest=json.loads(manifest_bytes)
    need(manifest['preserved_song_entries']==108 and manifest['source']['source_sha256']==WSC_SHA,'source-bound appended entries')
    source_log=a.source_discovery.read_text(encoding='utf-8')
    native_log=a.native_discovery.read_text(encoding='utf-8')
    need('frame=520 id=00DC type=0004' in source_log and
         'slot4=8A94/ch32 slot5=8C60/ch33 slot6=8FF4/ch34 slot7=9332/ch35' in source_log,
         'observed ordinary source boot request and four initialized payloads')
    need('frame=534 id=0001 type=0004 flags=0100' in native_log and
         'frame=535 id=0001 type=0004 flags=0000' in native_log,'observed ordinary native boot request consumption')
    need(wsc[SOURCE_BOOT:SOURCE_BOOT+24]==bytes.fromhex('a8000000948ad2000100608cfc000200f48f260103003293'),'source boot group descriptors')
    need(struct.unpack_from('<H',wsc,len(wsc)-2)[0]==sum(wsc[:-2])&65535,'original source checksum')
    outputs=[];pending=[]
    for category,sid in enumerate(SONGS):
        descriptors=wsc[0x3F0000+sid*6:0x3F0000+(sid+4)*6]
        checksum=(sum(wsc[:-2])-sum(wsc[SOURCE_BOOT:SOURCE_BOOT+24])+sum(descriptors))&65535
        after,details=image(wsc,[(SOURCE_BOOT,descriptors,'boot DC..DF descriptors from selected original group'),
                                 (len(wsc)-2,struct.pack('<H',checksum),'source ROM checksum')])
        need((sum(after[:-2])&65535)==struct.unpack_from('<H',after,len(after)-2)[0],'fixture source checksum')
        name=f'wsc-source-{sid:02X}-boot-fixture.wsc'
        pending.append((name,after));outputs.append(dict(platform='WSC',category=category,source_base_id=sid,file=name,**details))
        row=NATIVE_TABLE+(0x6C+category)*8
        entry=native[row:row+8]
        pointer,player,second=struct.unpack('<IHH',entry)
        need((player,second)==(0,0) and pointer==0x08000000+manifest['schedules'][category]['header'],'exact appended native BGM entry')
        need(native[pointer-0x08000000]==4,'native four-track song header')
        after,details=image(native,[(NATIVE_TABLE+8,entry,'boot native song01 row from appended selected score')])
        name=f'gba-source-{sid:02X}-boot-fixture.gba'
        pending.append((name,after));outputs.append(dict(platform='GBA',category=category,source_base_id=sid,native_id=0x6C+category,file=name,**details))
    report=dict(purpose='isolated audio-driver render fixtures; explicitly not normal gameplay proof',
                fixture_generator_sha256=sha(Path(__file__).read_bytes()),
                component_manifest_sha256=MANIFEST,source_discovery_sha256=sha(a.source_discovery.read_bytes()),
                native_discovery_sha256=sha(a.native_discovery.read_bytes()),
                fixtures=outputs,emulator_executed=False,guest_writes=False,
                recommended_dump_frames=4400,
                capture_requirements=['Log later boot music replacements; a complete score is not assumed from dump duration.',
                                      'Compare driver starts, note events, finite ends, stereo output and rendered duration.',
                                      'Names remain unassigned until source arrangements are independently identified.',
                                      'No correctness of ordinary evolution activation follows from these table-row fixtures.'])
    a.output_directory.mkdir(parents=True)
    for name,data in pending:(a.output_directory/name).write_bytes(data)
    out=a.output_directory/'manifest.json'
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(manifest_sha256=sha(out.read_bytes()),fixtures=len(outputs))))

if __name__=='__main__':main()
