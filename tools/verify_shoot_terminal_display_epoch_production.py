"""Capture-free independent display-epoch packaging gate."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT='46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
OUTPUT='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR='93BDB86A50E72E7227476369CA2DDFD8F9301B93BB3E40928291C48BFA16B260'
MANIFEST='F8C53C3C4FCA703316F0638DE0DFC61AEA16F3A2D987D781DB7215A9D82F345B'
STUB=bytes.fromhex('0103a0e3b010d0e1070011e3f0ffff1aba10d0e1cc0011e3edffff1a1c009fe5001090e5000051e3e9ffff1a501090e5000051e3e6ffff1a04009fe5279ffbea5423000310fe6f08')
WRITES=((0x6FF6E8,bytes.fromhex('0c0000eb')),(0x6FF720,STUB),(0x6FFDE8,bytes.fromhex('cc000000')),(0x6FFDEC,bytes(4)))

def need(ok,label):
    if not ok: raise ValueError(label)
def sha(b): return hashlib.sha256(b).hexdigest().upper()
def inverse(before,after):
    need(len(before)==len(after)==0x800000,'complete eight MiB')
    restored=bytearray(after)
    for a,b in WRITES:
        need(after[a:a+len(b)]==b,'independent exact emitted words/body')
        restored[a:a+len(b)]=before[a:a+len(b)]
    need(bytes(restored)==before,'whole-ROM inverse')

def audit(before,after,source,manifest_blob):
    need(tuple(map(sha,(before,after,source)))==(INPUT,OUTPUT,SOURCE),'approved identities')
    need(sha((ROOT/'tools/build_shoot_terminal_display_epoch.py').read_bytes())==AUTHOR,'frozen builder')
    need(sha(manifest_blob)==MANIFEST,'new frozen manifest')
    manifest=json.loads(manifest_blob);inverse(before,after)
    expected=[dict(offset=a,before=before[a:a+len(b)].hex(),after=b.hex()) for a,b in WRITES]
    need(manifest['expected_writes']==expected and manifest['input_sha256']==INPUT and
         manifest['output_sha256']==OUTPUT and manifest['source_sha256']==SOURCE and
         manifest['declared_bytes']==84 and manifest['changed_bytes']==69 and
         manifest['new_RAM_bytes']==manifest['additional_stack_bytes']==0,'manifest independent contract')
    need(before[0x6FF720:0x6FF800]==b'\xff'*0xE0,'entire preexisting adapter tail erased')
    for data,key in ((before,'native_pins'),(source,'source_pins')):
        for a,z,h in manifest[key]: need(sha(data[a:z])==h,key+hex(a))
    rejected=[]
    for a in (0x6FF6E8,0x6FF720,0x6FF767,0x6FF768,0x6FFDE8,0x6FFDEC,0x6FFC30,0x6FFEA0,0x7FFFFF):
        bad=bytearray(after);bad[a]^=1
        try: inverse(before,bytes(bad))
        except ValueError: rejected.append(a)
        else: raise ValueError('corruption accepted')
    return dict(status='INDEPENDENT_SOURCE_ONLY_DISPLAY_EPOCH_PRODUCTION_PASS',input_sha256=INPUT,output_sha256=OUTPUT,
        source_sha256=SOURCE,builder_sha256=AUTHOR,manifest_sha256=MANIFEST,expected_writes=expected,
        declared_bytes=84,changed_bytes=69,whole_ROM_inverse=True,new_RAM_bytes=0,additional_stack_bytes=0,
        inverse_mutations_rejected=rejected,historical_capture_dependency=False,semantic_cases_rerun=False,
        verifier_sha256=sha(Path(__file__).read_bytes()),actual_runtime_acceptance=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('before','after','source','manifest','report'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    r=audit(*(getattr(a,k).read_bytes() for k in ('before','after','source','manifest')))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode())
    print(r['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
