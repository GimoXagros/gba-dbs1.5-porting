#!/usr/bin/env python3
"""Source-only four-call packaging gate; no historical RAM or semantic rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT=Path(__file__).resolve().parents[1]
INPUT='1477F90EB06820D533F85F28EEC20130933660E0BFD1B728EF7953EDB0941FAC'
OUTPUT='FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
AUTHOR='66E70D72AB1401A526ADB16A560FB0EFB18E42BE2F56B3A411358DEB1FB6BE91'
MANIFEST='6E44701A7465E6CEBDD5E8C0B4ADA1EE48C398EA8DF2EF804530076EF3D0C310'
REUSED='18FBCD5B3FCD0B2D64B07604EBBAE61DBB05927DD8CA85807005582D1C03E6F6'
SITES=(0x5C6F4C,0x5C6F5C,0x5C6F88,0x5C6FBC)
WORDS=(0x1B000020,0x1B00001C,0x1B000011,0x1B000004)

def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def inverse(before,after):
    need(len(before)==len(after)==0x800000,'unchanged eight MiB')
    restored=bytearray(after)
    for at,value in zip(SITES,WORDS):
        need(before[at:at+4]==struct.pack('<I',0x1BFFFFFE)and after[at:at+4]==struct.pack('<I',value),'exact NE/link call words')
        need(at+8+4*(value&0xFFFFFF)==0x5C6FD4,'all four PC+8 targets existing dim helper')
        restored[at:at+4]=before[at:at+4]
    need(bytes(restored)==before,'whole four-word inverse')

def audit(before,after,source,manifest_blob):
    need(tuple(map(sha,(before,after,source)))==(INPUT,OUTPUT,SOURCE),'exact original source and approved ROMs')
    need(sha((ROOT/'tools/build_shoot_palette_dim_calls.py').read_bytes())==AUTHOR,'frozen production author')
    need(sha(manifest_blob)==MANIFEST,'fresh author manifest identity')
    manifest=json.loads(manifest_blob);inverse(before,after)
    need(sha(source[0x783C9E:0x783EAF])=='BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1','source bright/half-nibble projection body')
    expected=[dict(offset=a,before=struct.pack('<I',0x1BFFFFFE).hex(),after=struct.pack('<I',v).hex())for a,v in zip(SITES,WORDS)]
    need(manifest['expected_writes']==expected and manifest['input_sha256']==INPUT and manifest['output_sha256']==OUTPUT and
         manifest['declared_bytes']==16 and manifest['changed_bytes']==12 and manifest['new_storage']is False and manifest['new_RAM_owner']is False,'manifest exact independent four-call repair')
    for at,end,digest in manifest['native_pins']:
        need(sha(before[at:end])==digest,'retained original native pin')
    for name,digest in manifest['dependency_hashes'].items():need(sha((ROOT/'tools'/name).read_bytes())==digest,'tracked dependency '+name)
    need(after[0x5C6FD4:0x5C700C]==before[0x5C6FD4:0x5C700C]and
         after[0x5C7100:0x5C7124]==before[0x5C7100:0x5C7124]and
         after[0x5CD0D8:0x5CD104]==before[0x5CD0D8:0x5CD104],'existing helper/stage gate/blink producer unchanged')
    rejected=[]
    for at in SITES+(0x5C6FD4,0x5C7100,0x5CD0F4,0x352B10,0x6FF600,0x7FFFFF):
        bad=bytearray(after);bad[at]^=1
        try:inverse(before,bytes(bad))
        except ValueError:rejected.append(at)
        else:raise ValueError('inverse corruption accepted')
    return dict(status='INDEPENDENT_SOURCE_ONLY_PALETTE_DIM_CALL_PRODUCTION_PASS',input_sha256=INPUT,output_sha256=OUTPUT,
        source_sha256=SOURCE,builder_sha256=AUTHOR,manifest_sha256=MANIFEST,writes=expected,declared_bytes=16,changed_bytes=12,
        whole_ROM_inverse=True,new_storage=False,new_RAM_owner=False,prior_actual_ARM_QA_sha256=REUSED,prior_QA_artifact_read=False,
        historical_capture_dependency=False,semantic_cases_rerun=False,inverse_mutations_rejected=rejected,
        dependencies={**manifest['dependency_hashes'],Path(__file__).name:sha(Path(__file__).read_bytes())},
        qualification='Source-only identity/target/inverse packaging. Captured286 projector128helper cases cited by hash without loading old report/RAM/State. Actual terminal and later guard acceptance remain separate.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in('before','after','source','manifest','report'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    result=audit(*(getattr(a,k).read_bytes()for k in('before','after','source','manifest')))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(result,indent=2)+'\n').encode('utf8'))
    print(result['status'],sha(a.report.read_bytes()))

if __name__=='__main__':main()
