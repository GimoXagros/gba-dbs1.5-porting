#!/usr/bin/env python3
"""Correct the terminal guard's reciprocal auxiliary owner field, one word."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_shoot_stage11_runtime_probe import Machine

ROOT=Path(__file__).resolve().parents[1]
INPUT='FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8'
OUTPUT='46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B'
SOURCE='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
SITE=0x6FFC00
OLD=bytes.fromhex('180096E5')
NEW=bytes.fromhex('280096E5')
PINS=(
 (0x5BC200,0x5BC3B4,'057F6AFC5062972F877D27D299CACD5F9EB1AFAEA6EB34EE38C0C5C88AA5F67F'),
 (0x5CD960,0x5CD9A0,'49143F7C3B0DE43EE6E190BEDDD57921964C1054736DD5167523F9820545E246'),
 (0x5BF204,0x5BF230,'CF607E167C38BCC3ABDCB10EC3CDBBDDA6E176E62888A172D698E0B1ED111BD6'),
 (0x5BF400,0x5BF430,'2CA41960811DFFD2C571720284E9E29CE16337625FBD762219F0A524734F3C15'),
 (0x5BF600,0x5BF604,'379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F'),
 (0x5CDA70,0x5CDA84,'BA53B2FCD96DE56648A47EEB11C5B1235310FDCA52BD21BA9ED6984106A0A889'),
 (0x6FF9C0,0x6FFE04,'5E30F5865D8DEBD530ACD554E3AF87CB2FB7659BFFFCBB0913D9A9BE17926DB5'))
SOURCE_PINS=(
 (0x747A68,0x747E72,'F0F825AE96C188F14EA8ED89A78C18D9F5D752EAD123FE2C02FD0056AB51B8C3'),
 (0x74868D,0x7486D9,'16F553B4BBF982C90DDE99B358EFAF4A72A92AD7AE2F0CCF482C3E20CF60023F'))


def need(ok,label):
    if not ok:raise ValueError(label)
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def u(b,a):return struct.unpack_from('<I',b,a)[0]


def inverse(before,after):
    need(len(before)==len(after)==0x800000,'complete unchanged extent')
    need(before[SITE:SITE+4]==OLD and after[SITE:SITE+4]==NEW,'ExpectedWrite')
    restored=after[:SITE]+OLD+after[SITE+4:]
    need(restored==before,'whole-ROM inverse')


def build(before,source):
    need(sha(before)==INPUT and sha(source)==SOURCE,'exact FF3A and WSC1.5')
    for data,pins in ((before,PINS),(source,SOURCE_PINS)):
        for a,z,d in pins:need(sha(data[a:z])==d,'source/native contract '+hex(a))
    need((u(before,0x5BC398),u(before,0x5BC39C))==(0x030048A0,0x0300489C),'constructor owner/opponent globals')
    need(tuple(u(before,a)for a in (0x5BC29C,0x5BC2A8,0x5BC380))==(0xE5846028,0xE5847018,0xE5864028),'positive reciprocal constructor stores')
    need(before[SITE:SITE+4]==OLD,'expected old auxiliary opponent load')
    after=before[:SITE]+NEW+before[SITE+4:];inverse(before,after)
    need(sha(after)==OUTPUT,'frozen output')
    return after,dict(input_sha256=INPUT,output_sha256=OUTPUT,source_sha256=SOURCE,
        expected_writes=[dict(offset=SITE,before=OLD.hex(),after=NEW.hex())],
        declared_bytes=4,changed_bytes=1,whole_ROM_inverse=True,new_storage=False,new_RAM_owner=False,
        predicate='SECOND+28 == AUX and AUX+28 == SECOND',
        preserved_opponent='AUX+18 == FIRST by source/constructor/capture; no new guard predicate added',
        native_pins=PINS,source_pins=SOURCE_PINS,
        limits='Full actual acceptance not claimed: final outer BG1CNT is1F03, instruction-time guard trace is1E03. Runtime trial still required.')


def execute(rom,snapshot,overrides=()):
    m=Machine(rom,3,0x10,snapshot=snapshot);m.r[14]=0x09000000
    for a,v,n in overrides:m.put(a,v,n)
    m.writes.clear()
    stop=m.run(0x086FF9C0,{0x086FFD34,0x086FFD3C})
    return stop,m


def checks(before,after,capture):
    snap={base:(capture/('18-bounded-no-completion-'+name+'.bin')).read_bytes()
          for name,base in (('ewram',0x02000000),('iwram',0x03000000),('vram',0x06000000),('display',0x04000000))}
    old,m=execute(before,snap)
    need(old==0x086FFD3C and m.r[0]==0x02011710,'actual native old owner refusal')
    new,m=execute(after,snap)
    need(new==0x086FFD3C and (m.r[0],m.r[1])==(0x1F00,0x1E00),'actual outer IO phase refusal retained')
    need(m.get(0x02011958)==0x02011710 and m.get(0x02011968)==0x02011828,'captured opponent and reciprocal owner')
    # Explicitly mixed-epoch boundary model, NOT an actual same-instruction capture.
    mixed=((0x0400000A,0x1E03,2),)
    stop,m=execute(after,snap,mixed)
    need(stop==0x086FFD34,'modeled hook-time mapping passes all remaining exact native predicates')
    need(all(0x03007000<=a<0x03008000 for a,_,_ in m.writes),'guard has stack writes only')
    cases=[]
    for label,address,value in (('wrong reverse owner',0x02011968,0x02011710),
                                 ('wrong forward owner',0x02011850,0x02011710),
                                 ('inactive auxiliary',0x02011938,0),
                                 ('wrong auxiliary resource',0x02011A30,0)):
        stop,_=execute(after,snap,mixed+((address,value,4),))
        need(stop==0x086FFD3C,label+' refused');cases.append(label)
    for label,address,value,size in (('moving FIRST',0x02011752,1,2),('bad BG velocity',0x03002354,1,2),
                                      ('extra renderer',0x0300482A,2,2),('wrong final callback',0x02011940,0x085BF400,4)):
        stop,_=execute(after,snap,mixed+((address,value,size),))
        need(stop==0x086FFD3C,label+' refused');cases.append(label)
    controls=0
    for at in (SITE,SITE+1,SITE+2,SITE+3,SITE+4):
        bad=bytearray(after);bad[at]^=1
        try:inverse(before,bytes(bad))
        except ValueError:controls+=1
        else:raise ValueError('inverse accepted mutation')
    return dict(status='PASS',actual_final_old_guard='owner refusal',actual_final_repaired_guard='outer IO mapping refusal',
        mixed_epoch_model='final71927 RAM/VRAM plus hook69932 BG1CNT1E03: exact native guard reaches accept; not actual acceptance evidence',
        negative_controls=cases,inverse_controls=controls,capture_sha256={hex(a):sha(b)for a,b in snap.items()},
        service_models=[],runtime_acceptance=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--capture-dir',type=Path);p.add_argument('--author-report',type=Path)
    a=p.parse_args();before=a.input.read_bytes();after,manifest=build(before,a.source.read_bytes())
    if a.author_report:
        need(a.capture_dir is not None,'explicit completed capture required')
        report=checks(before,after,a.capture_dir);a.author_report.parent.mkdir(parents=True,exist_ok=True)
        a.author_report.write_text(json.dumps(report,indent=2)+'\n')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(after)
    a.manifest.parent.mkdir(parents=True,exist_ok=True);a.manifest.write_text(json.dumps(manifest,indent=2)+'\n');print(OUTPUT)


if __name__=='__main__':main()
