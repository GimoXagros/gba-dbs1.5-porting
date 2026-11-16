"""Execute actual ARM cache admission and retained pause/resume caller ABI."""
import argparse
import json
from pathlib import Path
import struct
from analyze_wsc_evolution_music import need,sha
from verify_shoot_attack_dispatch import Machine

RETURN=0x09000000
CACHE=0x03004E98
INPUT='C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346'

def play(rom,sid,flags):
    m=Machine(rom,seed=5,flags=(flags<<28)|0x1F)
    m.r[8]=sid;m.r[13]=0x03007F00;m.r[14]=RETURN;m.put(CACHE,0xF)
    original=m.r[:];calls=[]
    m.services={0x0837DB78:lambda m:calls.append(('play',m.r[0])),
                0x0837DB84:lambda m:calls.append(('stop-all',None))}
    need(m.run(0x0837B44C,{RETURN})==RETURN,'bounded real play entry')
    need(m.r[0]==original[0] and m.r[8]==sid and m.r[13:15]==original[13:15],'play ABI/argument preservation')
    need(m.cpsr&0x0FFFFFFF==0x1F,'CPSR control bits retained')
    need(calls==([('stop-all',None)] if sid==0 else [('play',sid)]),'unchanged service call argument')
    return m,calls

def verify(before,after):
    ids=list(range(0x70))+[0x70,0x71,0xFFFF,0x10000,0x7FFFFFFF,0x80000000,0x8000001D,0x8000001E,0xFFFFFFFE,0xFFFFFFFF]
    count=0;new=[]
    for sid in ids:
        for flags in range(16):
            old,c0=play(before,sid,flags);fixed,c1=play(after,sid,flags)
            added=0x6C<=sid<0x70
            need(fixed.get(CACHE)==(sid if added else old.get(CACHE)),'only four additional IDs cached')
            need(c0==c1,'same play/stop service')
            for r in range(15):
                if added and r==9:continue # Retained cache-store block uses R9 as cache address.
                need(old.r[r]==fixed.r[r],'retained general registers and stack')
            need([w for w in fixed.writes if w[0]!=CACHE]==[w for w in old.writes if w[0]!=CACHE],
                 'all noncache writes identical')
            if not added:need(old.writes==fixed.writes,'all other IDs exact write effects')
            if added and flags==0:new.append(dict(id=sid,old_cache=old.get(CACHE),new_cache=fixed.get(CACHE)))
            count+=2
    routes=[]
    for sid in range(0x6C,0x70):
        m,_=play(after,sid,0)
        active=struct.unpack_from('<I',after,0xD33000+sid*8)[0]
        stale=struct.unpack_from('<I',before,0xD33000+0xF*8)[0]
        need(active!=stale,'distinct stage and evolution headers')
        for entry,service,label in ((0x0837B48C,0x0837DB90,'pause'),(0x0837B4A8,0x0837DB9C,'resume')):
            m.r[14]=RETURN;m.r[13]=0x03007F00;calls=[];original=m.r[:]
            m.services={service:lambda m:calls.append(m.r[0])}
            m.run(entry,{RETURN})
            need(calls==[sid] and m.r[0]==original[0] and m.r[13:15]==original[13:15],
                 'actual ARM pause/resume passes corrected ID with ABI retained')
            routes.append(dict(id=sid,route=label,passed_id=calls[0],active_header=active,
                               stale_header=stale,header_match_fixed=True,header_match_before=False))
    return dict(actual_ARM_cases=count,ids=ids,initial_NZCV_patterns=16,additional_cache_cases=new,
        actual_ARM_pause_resume_routes=routes,
        boundaries=['M4A imported play/stop functions are explicit services in this ARM gate.',
                    'Thumb header comparison is source-pinned by builder; independent QA must execute it.',
                    'NZCV scratch can differ; original Thumb play immediately updates condition flags.'])

def main():
    p=argparse.ArgumentParser()
    for n in ('before','after','manifest','report'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();paths=[getattr(a,n).resolve() for n in ('before','after','manifest','report')]
    need(len(set(paths))==4 and not a.report.exists(),'fresh nonalias author report')
    before=a.before.read_bytes();after=a.after.read_bytes();manifest=json.loads(a.manifest.read_text())
    need(sha(before)==INPUT and sha(after)==manifest['output_sha256'],'frozen component identities')
    report=verify(before,after)
    rejected=[]
    for label,at,blob in [('missing new hook',0x37B458,before[0x37B458:0x37B45C]),
                         ('admit SFX',0xD7DFC0,struct.pack('<I',0xE358001E)),
                         ('exclude last song',0xD7DFC8,struct.pack('<I',0xE358006F))]:
        bad=bytearray(after);bad[at:at+4]=blob
        try:verify(before,bytes(bad))
        except ValueError:rejected.append(label)
        else:raise ValueError('mutation accepted: '+label)
    report.update(result='PASS_AUTHOR',input_sha256=sha(before),output_sha256=sha(after),
                  manifest_sha256=sha(a.manifest.read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),
                  rejected_semantic_mutations=rejected,emulator_executed=False)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(sha(a.report.read_bytes()))

if __name__=='__main__':main()
