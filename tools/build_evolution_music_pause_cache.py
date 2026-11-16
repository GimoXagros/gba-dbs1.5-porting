"""Admit only the four appended BGM IDs to the retained pause/resume cache."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import types
import verify_shoot_caller_resident as scanner

INPUT='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'
HOOK=0x37B458
TAIL=0xD7DFC0
END=TAIL+20
LIMIT=0xD7E000
BASE=0x08000000
SCANNER='7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'

def need(ok,label):
    if not ok: raise ValueError(label)

def sha(data): return hashlib.sha256(data).hexdigest().upper()
def branch(site,target,condition=14):
    delta=target-site-8
    need(delta%4==0 and -(1<<25)<=delta<(1<<25),'ARM branch range')
    return struct.pack('<I',(condition<<28)|0x0A000000|((delta//4)&0xFFFFFF))

def replacements():
    stub=(struct.pack('<I',0xE358006C)+branch(TAIL+4,0x37B464,3)+
          struct.pack('<I',0xE3580070)+branch(TAIL+12,0x37B464,2)+
          branch(TAIL+16,0x37B45C))
    need(len(stub)==20,'five ARM instructions')
    return ((HOOK,branch(HOOK,TAIL,5)),(TAIL,stub))

def ownership(before):
    need(before[TAIL:LIMIT]==b'\xff'*(LIMIT-TAIL),'entire owned64B reservation tail erased')
    need(sha(Path(scanner.__file__).read_bytes())==SCANNER,'frozen conservative scanner')
    scan=types.FunctionType(scanner.inbound.__code__,dict(scanner.__dict__,SPANS=((TAIL,END),)),
                            argdefs=scanner.inbound.__defaults__)
    hits=scan(before)
    need(not hits,'no predecessor pointer/ARM/Thumb inbound encodings into20B')
    return dict(scan_bytes=len(before),full_conservative_hits=hits,exemptions=[],
                reservation=[0xD74000,LIMIT],owned_erased_tail=[TAIL,LIMIT],used=[TAIL,END],
                scanner_sha256=SCANNER)

def build(before):
    need(len(before)==0x1000000 and sha(before)==INPUT,'exact C508 production composition')
    need(before[0x37B44C:0x37B464]==bytes.fromhex('0880b0e10800000a1e0058e30100005a24909fe5008089e5'),
         'exact old zero path and signed cache predicate/store')
    for sid in range(0x6C,0x70):
        header,player,priority=struct.unpack_from('<IHH',before,0xD33000+sid*8)
        need(player==priority==0 and BASE+0xD33000<=header<BASE+0xD7DFC0,'four bounded player0 songs')
    own=ownership(before)
    after=bytearray(before);writes=[]
    for at,blob in replacements():
        writes.append(dict(offset=at,size=len(blob),before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex()))
        after[at:at+len(blob)]=blob
    inverse=bytearray(after)
    for w in writes:inverse[w['offset']:w['offset']+w['size']]=bytes.fromhex(w['before_hex'])
    need(bytes(inverse)==before,'whole16MiB two-span inverse')
    need(after[END:LIMIT]==before[END:LIMIT],'unused44B tail remains erased')
    pins=[]
    for start,end,label in ((0x37B44C,0x37B4C4,'play/cache/pause/resume ARM'),
                            (0x37DB78,0x37DBA8,'ARM to Thumb bridges'),
                            (0x37C348,0x37C3B0,'actual header equality consumers'),
                            (0x375360,0x375368,'pause caller'),(0x37579C,0x3757A0,'resume caller'),
                            (0xD33000,0xD33380,'all112 song rows')):
        pins.append(dict(start=start,end=end,label=label,input_sha256=sha(before[start:end])))
    return bytes(after),dict(input_sha256=INPUT,output_sha256=sha(after),input_size=len(before),
        output_size=len(after),writes=writes,declared_bytes=24,
        changed_bytes=sum(a!=b for a,b in zip(before,after,strict=True)),ownership=own,source_pins=pins,
        cache_address='03004E98',additional_ids=[0x6C,0x6D,0x6E,0x6F],
        preserved='All other song IDs retain the original CMP#1E/BPL path; zero still globally stops.',
        flags='NZCV are caller-clobbered scratch; Thumb play entry overwrites flags. CPSR control bits retained.',
        purpose='Production pause/resume cache identity repair; no song/audio/input/timer modification.',
        runtime_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('before','output','manifest'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths=[getattr(a,n).resolve() for n in ('before','output','manifest')]
    need(len(set(paths))==3 and not a.output.exists() and not a.manifest.exists(),'fresh nonalias outputs')
    after,report=build(a.before.read_bytes())
    report['builder_sha256']=sha(Path(__file__).read_bytes())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True)
    a.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['output_sha256'])

if __name__=='__main__':main()
