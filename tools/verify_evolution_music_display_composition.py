"""Capture-free independent 16MiB music/display composition production gate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_shoot_terminal_display_epoch_production import WRITES, inverse as display_inverse

ROOT=Path(__file__).resolve().parents[1]
OWNER='46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
DISPLAY='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
AUDIO='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049'
FINAL='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
MUSIC_MANIFEST='AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91'
DISPLAY_MANIFEST='F8C53C3C4FCA703316F0638DE0DFC61AEA16F3A2D987D781DB7215A9D82F345B'
RESERVATIONS=((0xD33000,0xD40000),(0xD41000,0xD4B000),(0xD74000,0xD7E000))
OLD_WORDS=(0x37C2A4,0x37C2D8,0x37C324,0x37C378,0x37C3AC,0xD14A8,0xD14AC,0xD14B0,0xD14C4,0xD14D0,0xD14D8)
PINS={
 'tools/analyze_wsc_evolution_music.py':'2ED6FD43C11F636C11D38415AB07BA6B8FBE6E92531EB58890572BDCD09F8413',
 'tools/build_wsc_evolution_music.py':'E477925703C4DCD66A5239DCA1F0A806E208DAF02AD2FE95998C055330FC0077',
 'tools/build_shoot_terminal_display_epoch.py':'93BDB86A50E72E7227476369CA2DDFD8F9301B93BB3E40928291C48BFA16B260',
 'tools/verify_shoot_terminal_display_epoch_production.py':'E82C9F1A7EBC199DB13647776F93041AEA9F5A4600AA48491E5D696C185EE974',
 'tools/build_evolution_music_integration.py':'1BFF03992429A94CAF1143D02A84165581B19699A7597E7CC77FBB6905DB5794'}


def sha(blob):return hashlib.sha256(blob).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)


def inverse_music(after,music,before):
    need(len(after)==0x1000000 and len(before)==0x800000,'complete extent before music inverse')
    restored=bytearray(after)
    for row in music['writes']:
        a,n=row['offset'],row['size'];need(sha(after[a:a+n])==row['after_sha256'],'exact audio payload '+row['label'])
        restored[a:a+n]=bytes.fromhex(row['before_hex'])
    need(restored[:0x800000]==before and restored[0x800000:]==b'\xff'*0x800000,'entire music inverse to predecessor plus erased extension')


def audit(before,audio,after,music_raw,display_raw):
    for path,digest in PINS.items():need(sha((ROOT/path).read_bytes())==digest,'frozen source '+path)
    need(tuple(map(sha,(before,audio,after)))==(DISPLAY,AUDIO,FINAL),'complete input/output identities')
    need((len(before),len(audio),len(after))==(0x800000,0x1000000,0x1000000),'8/16/16MiB extents')
    need((sha(music_raw),sha(display_raw))==(MUSIC_MANIFEST,DISPLAY_MANIFEST),'fresh exact component manifests')
    music,display=json.loads(music_raw),json.loads(display_raw)
    need(music['input_sha256']==OWNER and music['output_sha256']==AUDIO and display['input_sha256']==OWNER and display['output_sha256']==DISPLAY,'parallel common predecessor')
    need(music['source']['source_sha256']==display['source_sha256']=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','same original WSC source')
    need(music['source']['retail_sha256']=='996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED','original native source')
    owner=bytearray(before)
    need(len(display['expected_writes'])==len(WRITES)==4,'four display spans')
    for row,(a,blob) in zip(display['expected_writes'],WRITES):
        need(row['offset']==a and row['after']==blob.hex() and before[a:a+len(blob)]==blob,'independent exact display words/body')
        old=bytes.fromhex(row['before']);need(len(old)==len(blob),'display equal span length');owner[a:a+len(blob)]=old
    owner=bytes(owner);need(sha(owner)==OWNER,'complete display inverse to owner46');display_inverse(owner,before)
    need(display['declared_bytes']==84 and display['changed_bytes']==69 and display['new_RAM_bytes']==display['additional_stack_bytes']==0,'retained display ownership/storage contract')
    need(before[0x6FF768:0x6FF800]==b'\xff'*0x98,'retained unused display-tail reservation')
    extended=owner+b'\xff'*0x800000;spans=[]
    need(len(music['writes'])==42 and sum(x['size'] for x in music['writes'])==104245,'exact music declared writes')
    for row in music['writes']:
        a,n=row['offset'],row['size'];old=bytes.fromhex(row['before_hex'])
        need(n>0 and 0<=a<a+n<=0x1000000 and len(old)==n and extended[a:a+n]==old,'complete expected audio write '+row['label'])
        need(sha(audio[a:a+n])==row['after_sha256'],'complete audio payload '+row['label']);spans.append((a,a+n))
        need(all(a+ n<=d or d+len(blob)<=a for d,blob in WRITES),'all audio/display spans disjoint')
        if a>=0x800000:need(any(x<=a and a+n<=z for x,z in RESERVATIONS),'audio reservation containment')
    spans.sort();need(all(a[1]<=b[0] for a,b in zip(spans,spans[1:])),'music placements mutually disjoint')
    need({(a,z-a) for a,z in spans if a<0x800000}=={(a,4) for a in OLD_WORDS},'exact eleven preexisting words only')
    need(tuple(map(tuple,music['reservations']))==RESERVATIONS and music['pointer_arm_inbound_encodings']==[],'retained music reservation/source proof')
    inverse_music(audio,music,owner);inverse_music(after,music,before)
    expected=bytearray(audio)
    for a,blob in WRITES:
        need(audio[a:a+len(blob)]==owner[a:a+len(blob)],'display predecessor bytes retained in isolated audio')
        expected[a:a+len(blob)]=blob
    need(bytes(expected)==after,'complete disjoint composition')
    restored=bytearray(after)
    for a,blob in WRITES:restored[a:a+len(blob)]=owner[a:a+len(blob)]
    need(bytes(restored)==audio,'complete display inverse preserves exact isolated audio')
    need(after[0xD33000:0xD33000+108*8]==owner[0x686800:0x686800+108*8],'all108 existing song entries preserved')
    # Only84 newly supplied display bytes can add incoming old-image encodings.
    sites={p for a,blob in WRITES for p in range(max(0,a-3),min(len(before)-3,a+len(blob)))}
    newrefs=[]
    for p in sorted(sites):
        word=struct.unpack_from('<I',before,p)[0]
        if any(0x08000000+a<=word<0x08000000+z for a,z in RESERVATIONS):newrefs.append((p,'pointer',word))
        if p%4==0 and word>>28!=15 and word&0x0E000000==0x0A000000:
            delta=word&0xFFFFFF;delta-=0x1000000 if delta&0x800000 else 0;target=p+8+4*delta
            if any(a<=target<z for a,z in RESERVATIONS):newrefs.append((p,'ARM',target))
    need(not newrefs,'display delta introduces no new music-reservation pointer/ARM encodings')
    rejected=[]
    for at in (0xD33000,0xD33380,0xD74000,0xFFFFFF,0x37C2A4,0x37C400,0x6FF720):
        bad=bytearray(after);bad[at]^=1
        try:inverse_music(bytes(bad),music,before)
        except ValueError:rejected.append(at)
        else:raise ValueError('inverse corruption accepted')
    try:inverse_music(audio,music,before)
    except ValueError:rejected.append('display-layer-dropped')
    else:raise ValueError('missing display accepted')
    return dict(status='INDEPENDENT_MUSIC_DISPLAY_COMPOSITION_PRODUCTION_PASS',before_sha256=DISPLAY,audio_sha256=AUDIO,after_sha256=FINAL,owner_sha256=OWNER,music_manifest_sha256=MUSIC_MANIFEST,display_manifest_sha256=DISPLAY_MANIFEST,source_tool_sha256=PINS,verifier_sha256=sha(Path(__file__).read_bytes()),output_size=0x1000000,display_spans=4,display_declared_bytes=84,display_changed_bytes=69,music_spans=42,music_declared_bytes=104245,music_changed_bytes=104216,all_music_display_spans_disjoint=True,music_inverse_to_exact280D_and_FF_extension=True,display_inverse_to_exactDD6=True,music_inverse_then_display_inverse_to_exact46B3=True,all108_previous_song_rows_preserved=True,reservations=RESERVATIONS,new_display_inbound_encodings=newrefs,inverse_controls_rejected=rejected,capture_dependency=False,author_builder_executed=False,old_semantic_suite_rerun=False,actual_audio_or_title_identity_claim=False,emulator_launched=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('before','audio','after','music-manifest','display-manifest','report'):parser.add_argument('--'+key,type=Path,required=True)
    args=parser.parse_args();need(not args.report.exists(),'fresh report required')
    inputs=[args.before,args.audio,args.after,args.music_manifest,args.display_manifest]
    need(len({p.resolve() for p in inputs+[args.report]})==6,'all source/report paths distinct')
    report=audit(*(p.read_bytes() for p in inputs));args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_bytes((json.dumps(report,indent=2)+'\n').encode('utf8'));print(report['status'],sha(args.report.read_bytes()))


if __name__=='__main__':main()
