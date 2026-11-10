"""Narrow author checks: real ARM selector ABI and whole native score decoding."""
import argparse
import json
from pathlib import Path
import struct
from analyze_wsc_evolution_music import need,sha,CATEGORIES
from verify_shoot_attack_dispatch import Machine

BASE=0x08000000
RETURN=0x09000000

def selector(rom):
    cases=[]
    for character,category in enumerate(CATEGORIES):
        for busy in (0,123):
            m=Machine(rom,seed=character)
            m.r[13]=0x03007F00;m.r[14]=RETURN
            saved=list(m.r[:3]);sp=m.r[13]
            m.put(sp,character)
            m.put(0x030022F6,busy,2)
            m.put(0x030022F2,0x1234,2)
            m.put(0x030022FE,0x5678,2)
            m.put(0x03002300,0x20,2)
            m.writes.clear()
            need(m.run(0x080D14BC,{RETURN})==RETURN,'actual selector returns')
            need(m.r[:3]==saved and m.r[13]==sp and m.r[14]==RETURN,'actual retained selector stack/ABI')
            expected=(0x6C+category,4,0x6EA,0x120) if not busy else (0x1234,0x5678,busy,0x20)
            actual=tuple(m.get(a,2) for a in (0x030022F2,0x030022FE,0x030022F6,0x03002300))
            need(actual==expected,'actual native typed request and occupied gate')
            cases.append(dict(character=character,category=category,busy=busy,queue=list(actual)))
    return cases

def decode(data):
    tick=0;at=0;active=None;notes=[];commands={}
    while at<len(data):
        op=data[at];at+=1
        if op==0x81: tick+=1
        elif op in (0xBC,0xBB,0xBD,0xBE,0xBF,0xC0,0xC1):
            need(at<len(data) and data[at]<128,'whole native scalar argument')
            commands[op]=data[at];at+=1
        elif op==0xCF:
            need(active is None and at+2<=len(data),'non-overlapping native TIE')
            key,velocity=data[at:at+2];at+=2
            need(key<128 and velocity==127,'native note arguments')
            active=dict(update=tick,key=key,voice=commands[0xBD],bend_range=commands[0xC1])
        elif op==0xCE:
            need(active is not None and at<len(data) and data[at]==active['key'],'matched native EOT')
            at+=1;active['duration_updates']=tick-active['update'];notes.append(active);active=None
        elif op==0xB1:
            need(active is None and at==len(data),'clean whole-stream native FINE')
            return tick,notes
        else:raise ValueError(f'unsupported native byte {op:02X}')
    raise ValueError('native stream has no FINE')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--rom',required=True,type=Path)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    paths=[a.rom.resolve(),a.manifest.resolve(),a.report.resolve()]
    need(len(set(paths))==len(paths) and not a.report.exists(),'fresh nonalias author report')
    rom=a.rom.read_bytes();manifest=json.loads(a.manifest.read_text(encoding='utf-8'))
    need(sha(rom)==manifest['output_sha256'],'component identity')
    cases=selector(rom)
    writes={w['label']:w for w in manifest['writes']}
    counts=[]
    for source,schedule in zip(manifest['source']['songs'],manifest['schedules'],strict=True):
        for channel,native in zip(source['channels'],schedule['channels'],strict=True):
            w=writes[f'source_{channel["id"]:02X}_native_track']
            data=rom[w['offset']:w['offset']+w['size']]
            tick,notes=decode(data)
            expected=[{k:n[k] for k in ('update','key','voice','bend_range','duration_updates')} for n in native['notes']]
            need(notes==expected,'all generated native notes decoded with exact key/duration/voice')
            need(tick==(0 if channel['silent_infinite_rest'] else channel['driver_updates']),'whole finite native timeline')
            counts.append(dict(source_id=channel['id'],notes=len(notes),updates=tick))
    negative=[]
    for label,site in [('category literal',0xD14A8),('song literal',0xD14AC),('selector instruction',0xD14C4)]:
        changed=bytearray(rom);changed[site]^=4
        try:selector(bytes(changed))
        except (ValueError,AssertionError,IndexError,KeyError):negative.append(label)
        else:raise AssertionError('selector corruption accepted '+label)
    report=dict(component_sha256=sha(rom),manifest_sha256=sha(a.manifest.read_bytes()),
                actual_ARM_selector_cases=cases,native_streams=counts,negative_controls=negative,
                limits=['Author test, not independent QA or emulator/audio comparison.',
                        'Actual ARM domain covers canonical IDs0..15 only; caller identity reused from existing port contracts.',
                        'All declared timing/pitch/pan/phase differences remain in component manifest.'])
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(sha(a.report.read_bytes()))

if __name__=='__main__':main()
