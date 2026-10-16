"""Decode native character scores independently; no builder imports or emulator."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

BEFORE = '973E06247F43C1E70EB69C6BB27135D6A6C634AAFCF0C0770E7621708A078A3D'
AFTER = '10372B5606647673F829EC676853C1987F17E64BA19EA51EB751F92FA22B3354'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BASE, TABLE = 0x08000000, 0x683200
LITERALS = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
# Explicit source phrase transcription, including C6's initial eight-tick rest.
# onset, duration, packed source note, waveform, right volume
PHRASES = (
    [(0,20,0x30,1,15)],
    [(8+4*n,4,note,4,vol) for n,(note,vol) in enumerate(
        [(0x79,15),(0x77,15),(0x75,15),(0x73,15),
         (0x79,9),(0x77,9),(0x75,9),(0x73,9),(0x79,6),(0x77,6)])],
    [(0,5,0x50,2,15),(5,40,0x30,2,15)],
    [(0,10,0x20,1,15),(10,10,0x39,1,15)],
    [(0,10,0x60,1,15),(10,10,0x40,1,6),(20,10,0x40,1,4),
     (30,10,0x40,1,2),(40,10,0x40,1,1)],
)
SOURCE_WINDOWS = ((0xBC,0x3F872C,14),(0xC6,0x3F8816,38),(0xC8,0x3F8848,16),
                  (0xCB,0x3F88BE,18),(0xCC,0x3F88D0,32))


def sha(b): return hashlib.sha256(b).hexdigest().upper()
def need(ok, label):
    if not ok: raise ValueError(label)


def decode(data, at):
    start = at
    keyshift = volume = voice = None
    tempo = pan = None
    clock = 0
    notes = []
    while at - start < 512:
        op = data[at]; at += 1
        if op == 0xB1:
            return notes, clock, at, (keyshift, tempo, pan)
        if op == 0x81:
            clock += 1
        elif op in (0xBC,0xBB,0xBF,0xBD,0xBE):
            v = data[at]; at += 1
            if op == 0xBC: keyshift = v if v < 128 else v-256
            elif op == 0xBB: tempo = v
            elif op == 0xBF: pan = v
            elif op == 0xBD: voice = v
            else: volume = v
        elif 0xD0 <= op <= 0xE7 or op == 0xEC:
            key, velocity = data[at:at+2]; at += 2
            need(key < 128 and velocity == 127 and None not in (keyshift,volume,voice), 'explicit native note')
            duration = 40 if op == 0xEC else op-0xCF
            notes.append((clock,duration,key+keyshift,voice,volume))
        else:
            raise ValueError(f'unexpected native track opcode {op:02X}')
    raise ValueError('unterminated native score')


def source_phrase(wsc, raw, length):
    blob = wsc[raw:raw+length]
    need(blob[:3] == bytes((0,0,15)), 'source initial amplitude')
    volume, wave, clock = 15, 0, 0
    notes = []
    for pos in range(4, len(blob), 2):
        op,arg = blob[pos:pos+2]
        if (op,arg) == (255,255):
            need(set(blob[pos:]) == {255}, 'source terminal padding')
            return notes,clock
        if op == 0xA0: volume = arg
        elif op == 0xA2: wave = arg
        elif op == 0xA1: need(arg in (7,9,10), 'documented source sweep limits')
        elif op == 0xC1: need(arg == 0, 'zero-period source envelope')
        else:
            need(op < 0xA0 and arg > 0, 'finite source note/wait')
            if op % 16 < 12: notes.append((clock,arg,op,wave,volume))
            clock += arg
    raise ValueError('source termination missing')


def inspect(before,after,gba,wsc):
    allowed = set()
    for at in LITERALS:
        need(struct.unpack_from('<I',before,at)[0] == 0x085BA400, 'old lookup literal')
        need(struct.unpack_from('<I',after,at)[0] == BASE+TABLE, 'new lookup literal')
        allowed.update(range(at,at+4))
    need(after[TABLE:TABLE+760] == before[0x5BA400:0x5BA6F8], 'all95 previous native entries')
    allowed.update(range(TABLE,TABLE+800))
    voice_at = TABLE+800
    for n,raw in enumerate((0x37EA54,0x37E9D0,0x37EB08)):
        need(after[voice_at+n*12:voice_at+n*12+8] == gba[raw:raw+8], 'commercial timbre analogue')
        need(after[voice_at+n*12+8:voice_at+n*12+12] == bytes((0,0,15,0)), 'neutral native ADSR')
    allowed.update(range(voice_at,voice_at+36))
    details = []
    for n, ((source_id,raw,length), phrase) in enumerate(zip(SOURCE_WINDOWS,PHRASES,strict=True)):
        actual_phrase,total = source_phrase(wsc,raw,length)
        need(actual_phrase == phrase, 'independent source phrase transcription')
        need(0x3F0000+struct.unpack_from('<H',wsc,0x3F0000+source_id*6+4)[0] == raw,'source table pointer')
        pointer,player,other = struct.unpack_from('<IHH',after,TABLE+(0x5F+n)*8)
        song = pointer-BASE
        need((player,other)==(4,4) and voice_at+36 <= song < 0x683A00, 'new song receiver')
        need(after[song:song+4]==bytes((1,0,40,128)), 'native song header')
        need(struct.unpack_from('<II',after,song+4)==(BASE+voice_at,BASE+song+12),'native voice/track pointers')
        notes,ticks,end,setup = decode(after,song+12)
        expected=[(t,d,36+12*(note//16)+note%16,{1:0,2:1,4:2}[wave],round(v*127/15))
                  for t,d,note,wave,v in phrase]
        need(notes==expected and ticks==total, 'all score notes, onsets, durations and volumes')
        need(setup==((12 if n==1 else 0),75,127), 'key shift, tempo and right pan')
        need(end<=0x683A00,'reserved extent')
        allowed.update(range(song,end))
        details.append(dict(source_id=source_id,native_id=0x5F+n,start=song,end=end,
                            notes=notes,total_ticks=ticks,source_payload_sha256=sha(wsc[raw:raw+length])))
    need(all(before[n]==255 for n in allowed if TABLE<=n<0x683A00), 'Expected Write blank payloads')
    changed={n for n,(a,b) in enumerate(zip(before,after,strict=True)) if a!=b}
    need(changed and changed<=allowed,'whole-ROM diff containment')
    # Actual commercial KEYSH -> effective transpose -> note-key consumers.
    for lo,hi in ((0x37BACC,0x37BADE),(0x37CB1C,0x37CB44),(0x37BDE4,0x37BE1A),
                  (0x37CB50,0x37CBA6),(0x37C140,0x37C154)):
        need(after[lo:hi]==gba[lo:hi], 'preserved actual native pitch consumers')
    need(gba[0x37BAD2:0x37BAD4]==bytes.fromhex('8b72'),'KEYSH writes track+A')
    need(gba[0x37CB74:0x37CB7A]==bytes.fromhex('3b2d00d93b25'),'noise index clamp retained and disclosed')
    return dict(songs=details,actual_changed_bytes=len(changed),native_noise_limit='source frequency parity excluded')


def main():
    p=argparse.ArgumentParser()
    for name in ('before','after','gba','wsc15','output'):p.add_argument(name,type=Path)
    a=p.parse_args()
    data=[getattr(a,n).read_bytes() for n in ('before','after','gba','wsc15')]
    need(tuple(map(sha,data))==(BEFORE,AFTER,GBA,WSC),'input identities')
    report=inspect(*data)
    negatives=[]
    sites=[(TABLE,'old song entry'),(LITERALS[0],'lookup literal'),(TABLE+808,'ADSR'),
           (0x485030,'unrelated physics pointer')]
    for song in report['songs']:
        sites.append((song['start']+13,'key shift'))
        sites.append((song['end']-1,'score terminator'))
    for at,label in sites:
        mutant=bytearray(data[1]);mutant[at]^=1
        try:inspect(data[0],mutant,data[2],data[3])
        except (ValueError,IndexError,struct.error):negatives.append(dict(offset=at,label=label))
        else:raise ValueError('negative accepted: '+label)
    report.update(input_sha256=BEFORE,output_sha256=AFTER,negative_cases=negatives,
                  claim_scope='bounded native score conversion; timbre, A1 sweep, noise pitch parity and audible QA excluded')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PASS '+sha(a.output.read_bytes()))


if __name__=='__main__':main()
