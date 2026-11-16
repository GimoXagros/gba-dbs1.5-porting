"""Compose the two frozen disjoint layers without weakening either source builder."""
import argparse
import hashlib
import json
from pathlib import Path

DISPLAY = '280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
AUDIO = 'DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049'
OUTPUT = 'C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
DISPLAY_SPANS = ((0x6FF6E8,4),(0x6FF720,72),(0x6FFDE8,4),(0x6FFDEC,4))
OLD_WORDS = (
    (0x37C2A4,'00686808'),(0x37C2D8,'00686808'),(0x37C324,'00686808'),
    (0x37C378,'00686808'),(0x37C3AC,'00686808'),(0xD14A8,'02020201'),
    (0xD14AC,'01000000'),(0xD14B0,'00010102'),(0xD14C4,'24804fe2'),
    (0xD14D0,'23804fe2'),(0xD14D8,'2a804fe2'))

def sha(data): return hashlib.sha256(data).hexdigest().upper()

def need(ok,label):
    if not ok: raise ValueError(label)

def inverse_music(after):
    need(len(after)==0x1000000 and sha(after)==OUTPUT,'exact integrated16MiB')
    restored=bytearray(after[:0x800000])
    for at,old in OLD_WORDS: restored[at:at+4]=bytes.fromhex(old)
    need(sha(restored)==DISPLAY,'whole prior8MiB inverse')
    return bytes(restored)

def build(display,audio):
    need(sha(display)==DISPLAY and len(display)==0x800000,'frozen display layer')
    need(sha(audio)==AUDIO and len(audio)==0x1000000,'frozen production audio layer')
    after=bytearray(audio)
    for at,size in DISPLAY_SPANS: after[at:at+size]=display[at:at+size]
    after=bytes(after)
    need(sha(after)==OUTPUT and inverse_music(after)==display,'exact composition and music inverse')
    restored=bytearray(after)
    for at,size in DISPLAY_SPANS: restored[at:at+size]=audio[at:at+size]
    need(bytes(restored)==audio,'whole audio layer preserved by display inverse')
    return after

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('display','audio','output','manifest'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths=[getattr(a,n).resolve() for n in ('display','audio','output','manifest')]
    need(len(set(paths))==4 and not a.output.exists() and not a.manifest.exists(),'fresh nonalias outputs')
    after=build(a.display.read_bytes(),a.audio.read_bytes())
    report=dict(input_sha256=DISPLAY,audio_sha256=AUDIO,output_sha256=OUTPUT,
                input_size=0x800000,output_size=len(after),display_spans=DISPLAY_SPANS,
                music_declared_bytes=104245,music_changed_bytes=104216,
                prior_song_entries_preserved=108,test_stop_suppression=False,final_port_complete=False)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    print(OUTPUT)

if __name__=='__main__': main()
