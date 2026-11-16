"""Independent bounded audit of completed neutral counter1 capture."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import struct
from verify_gba_shoot_entry_capture_v2 import checkpoint_core,parse_checkpoint,OFFSETS
from analyze_wsc_evolution_music import need,sha

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'build/bizhawk-gba-shoot-counter1-20261110-a'
SOURCE=ROOT/'build/bizhawk-gba-shoot-terminal-display-store-20261110-a'
ROM='280DAF9F7587FCE7A860C29DEFB144DB80729965C13939841CA8093774C05FB7'
CORE='32A904634D2E9F941853496BE03431EBE276234A1C7E28A9DAD3129387C05583'
PINS={
 'tools/bizhawk_probe_gba_shoot_counter1_v2.lua':'053FD747027B9B5ED68769643EBA138BB5313249DFBAC4384427375F6F4F64A6',
 'tools/bizhawk_probe_gba_shoot_counter1.lua':'C625D710C9B2DE44D128D1846066B4F5C2326E7EC37B6875FFF98805B0A59C6C',
 'build/run_gba_shoot_counter1_v2_20261110.py':'D7D1627BF2B0CCAD089C3128F764D7953D466BAD499B124DA0F1A965D632735D'}
def u(b,p,n=4):return int.from_bytes(b[p:p+n],'little')
def fields(line):return dict(re.findall(r'([A-Za-z_][A-Za-z_0-9]*)=([^\s}]+)',line))
def row(line):
    f=fields(line);result={}
    for k,v in f.items():
        if k in ('core','VCOUNT','mode','stage'):result[k]=int(v)
        elif k in ('base','counter','index','slot','DISPSTAT','BG1CNT','scene') or re.fullmatch(r'R\d+',k):result[k]=int(v,16)
        else:result[k]=v
    return result

def check_trace(lines):
    rows=[row(line) for line in lines];counts=Counter(r['kind'] for r in rows)
    need(counts=={'start':1,'display-success':1,'counter1-initialized':1,'first-IRQ-entry':1,
                  'IRQ-compare':30,'IRQ-match':8,'IRQ-match-stored':8,'IRQ-final-install':1,'IRQ-final-called':1},'complete52-row event population')
    need(rows[0]['core']==69935 and all(r['core']==70122 for r in rows[1:]),'one fresh target core only')
    need(all((r['mode'],r['stage'],r['scene'],r['BG1CNT'])==(7,11,0x085CD510,0x1E03) for r in rows),'bounded terminal owner and mapping')
    need([r['kind'] for r in rows[:4]]==['start','display-success','counter1-initialized','first-IRQ-entry'],'selection then initialization then IRQ')
    display,init,entry=rows[1:4]
    need(display['observed_core']=='70122' and display['observed_PC']=='086FF760' and display['observed_LR']=='086FF6EC','actual successful consumption stub witness')
    need('observed_state={base=0001 counter=000A index=0008 slot=086FF6B4' in lines[1],'new selected display replaces previous completed cycle')
    need((init['base'],init['counter'],init['index'],init['slot'],init['VCOUNT'],init['R5'],init['R15'])==(0,1,0,0x086FFE10,1,0x03004710,0x085E74DC),'counter1 initializer and early line1')
    need(entry['VCOUNT']==8 and entry['R15']==0x086FFE14,'first IRQ at actual line8')
    offsets=(0,2,4,7,10,13,17,21);matched=0;last=None;pending=None;comparisons=[];matches=[]
    for r in rows[4:]:
        kind=r['kind']
        if kind=='IRQ-compare':
            need(pending is None and matched<8,'no skipped pending store')
            line=r['R0'];target=matched+1+offsets[matched]
            need((r['index'],r['counter'],r['R4'],r['R5'],r['R6'],r['R1'])==(matched,matched+1,0x03004710,matched,offsets[matched],target),'all actual compare operands')
            need(line==(((r['DISPSTAT']>>8)-8)&255) and line<=target and r['VCOUNT']==line+8 and r['R15']==0x086FFE4C,'DISPSTAT compare and separate VCOUNT')
            need(line==len(comparisons),'every programmed line0..29 without gap')
            if not comparisons:need(line<=1 and r['VCOUNT']<=9,'first deadline')
            comparisons.append(r);last=r
        elif kind=='IRQ-match':
            need(last is not None and pending is None and r['R0']==r['R1']==last['R0']==last['R1'] and r['index']==matched and r['R5']==matched and r['R15']==0x086FFE54,'actual equality branch after compare')
            pending=r;matches.append(r)
        elif kind=='IRQ-match-stored':
            need(pending is not None and r['VCOUNT']==pending['VCOUNT'] and r['R0']==r['counter']==matched+2 and r['R5']==r['index']==matched+1 and r['R15']==0x086FFE78,'actual counter/index stores')
            need(r['R10']==0xB0-offsets[matched],'retained scroll calculation operand after F44')
            matched+=1;pending=None;last=None
        elif kind=='IRQ-final-install':
            need(matched==8 and pending is None and r['counter']==9 and r['index']==8 and r['R0']==0x030012E0 and r['R1']==0x086FFEBC and r['R15']==0x086FFE88,'final callback store operand')
        elif kind=='IRQ-final-called':
            need(rows[-1] is r and matched==8 and r['slot']==0x086FFEBC and r['VCOUNT']==38 and r['counter']==9 and r['index']==8 and r['R15']==0x086FFEC0,'actual final callback on following line')
        else:raise ValueError('unapproved target event')
    need([r['VCOUNT'] for r in matches]==[9,12,15,19,23,27,32,37],'all eight actual match scanlines')
    return dict(target_core=70122,initializer_VCOUNT=1,first_IRQ_VCOUNT=8,first_compare_line=0,
                first_compare_target=1,match_VCOUNT=[r['VCOUNT'] for r in matches],final_VCOUNT=38,
                compare_count=len(comparisons),matches=matched,rows=len(rows))

def metadata(iw,ew,frame):
    p,q=u(iw,0x489C),u(iw,0x48A0)
    values=dict(core=frame,mode=u(iw,0x2310,2),stage=iw[0x231E],difficulty=iw[0x231F],progress=u(iw,0x232A,2),
                FIRST=p,SECOND=q,flags=u(iw,0x450A,2),P1HP=u(ew,p-0x02000000+0x64,2),P2HP=u(ew,q-0x02000000+0x64,2),
                fighter=ew[p-0x02000000+0x11],base=(u(ew,p-0x02000000+8,2)>>8)&1,input_task=u(iw,0x4510),battle_task=u(iw,0x4514))
    return {k:format(v,'X') if k in ('progress','FIRST','SECOND','flags','input_task','battle_task') else str(v) for k,v in values.items()}

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',required=True,type=Path);a=p.parse_args();need(not a.report.exists(),'fresh report')
    raw=(D/'launch.json').read_bytes();launch=json.loads(raw)
    need(launch['completed'] and not launch['host_deadline_reached'] and launch['outcome']=='earliest-counter1-irq-complete','completed bounded host')
    need(not any(launch[k] for k in ('visible','physical_background_input','supplied_save_used','guest_memory_writes')),'private neutral read-only continuation')
    inventory={p.relative_to(D).as_posix():sha(p.read_bytes()) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='launch.json'}
    need(inventory==launch['files'],'complete immutable capture inventory')
    for name,digest in launch['pins'].items():need(sha((ROOT/name).read_bytes())==digest,'actual executed dependency pin')
    need(all(launch['pins'][k]==v for k,v in PINS.items()),'frozen wrapper/base/host identities')
    gate=ROOT/'build/shoot-counter1-independent-review-20261110/report.json'
    need(sha(gate.read_bytes())=='401AD2150307FABC1FD3866098241448B103246E863F877B50EEB2D9BEB7D5BC','independent preflight gate')
    audit=ROOT/'build/gba-shoot-terminal-display-store-capture-qa-20261110/final-report.json'
    need(sha(audit.read_bytes())==launch['source_audit_sha256']=='9F909134E5CF5DC73A3C53ED96D212441B878E536C8F466CA2D210DCCFE5DA8F','prior source checkpoint audit')
    need(sha((SOURCE/'launch.json').read_bytes())==launch['source_launch_sha256'],'source inventory provenance')
    rom=(D/'probe.gba').read_bytes();need(sha(rom)==ROM and rom==(D/'loaded-rom.bin').read_bytes()==(SOURCE/'probe.gba').read_bytes(),'loaded exact280D ROM')
    for name,digest in launch['checkpoint_pins'].items():
        blob=(D/'checkpoint'/name).read_bytes()
        need(sha(blob)==digest and blob==(SOURCE/name).read_bytes(),'immutable genuine checkpoint copy')
    cfg=json.loads((D/'config.json').read_bytes())
    need(all(cfg[k] is False for k in ('AcceptBackgroundInput','AutoLoadLastSaveSlot','AutosaveSaveRAM','SoundEnabled')),'private input/save/audio settings')
    need(all(e['Path'].startswith('W:/build/'+D.name+'/data/') for e in cfg['PathEntries']['Paths']),'isolated generated data paths')
    source,_=checkpoint_core((D/'checkpoint/19-irq-final-install.State').read_bytes());need(sha(source)==CORE,'exact source Core')
    states={}
    for name,frame in (('restored',69935),('counter1-first',70123),('final',70123)):
        regions={r:(D/f'{name}-{r}.bin').read_bytes() for r in OFFSETS}
        iw,ew=regions['iwram'],regions['ewram']
        parsed=parse_checkpoint((D/f'{name}.State').read_bytes(),metadata(iw,ew,frame),regions,rom)
        need(parsed['state']['mode']==7 and parsed['state']['stage']==11 and parsed['state']['P1HP']==1 and parsed['state']['P2HP']==0,'retained terminal owner, no new mode8 claim')
        need(u(iw,0x489C)==0x02011710 and u(iw,0x48A0)==0x02011828 and u(iw,0x4D3C)==0x02011940,'typed actor identities')
        need(u(ew,0x121E8)==0x085CD510,'scene remains terminal wait')
        if name=='restored':
            need(all(regions[r]==(SOURCE/f'19-irq-final-install-{r}.bin').read_bytes() for r in regions),'all5 restored RAM exact')
        else:
            need((u(iw,0x4712,2),u(iw,0x4714,2),u(iw,0x4716,2),u(iw,0x12E0))==(0,9,8,0x086FFEBC),'outer capture retains completed counter1 cycle')
        states[name]=parsed
    need((D/'counter1-first.State').read_bytes()==(D/'final.State').read_bytes(),'no intervening frame between two final captures')
    restored,_=checkpoint_core((D/'restored.State').read_bytes());length=u(source,0)
    diff=[dict(offset=i,source=x,restored=y) for i,(x,y) in enumerate(zip(source,restored,strict=True)) if x!=y]
    need(diff==launch['Core_byte_differences'] and [d['offset'] for d in diff]==[0x180,0x181,0x188,0x189,0x18C,0x18D],'exact six raw Core differences retained')
    need(not launch['restored_whole_Core_exact'] and restored!=source,'strict whole Core mismatch not normalized away')
    need(source[0x24:0x134]==restored[0x24:0x134] and source[4+0x61000:4+length]==restored[4+0x61000:4+length] and source[4+length:]==restored[4+length:],'CPU/extensions/managed suffix exact')
    serializer=ROOT/'build/gba-shoot-entry-capture-v2-qa-20261109/source/serialize.h'
    need(sha(serializer.read_bytes())=='B7437677E104AF90838FC0D54530779CE0063B9EA6EA91130192A3F716D2EAFF','source-bound audio field classification')
    lines=(D/'counter1-trace.txt').read_text(encoding='utf-8').splitlines();timing=check_trace(lines)
    summary=fields((D/'counter1-summary.txt').read_text())
    need(summary['outcome']==launch['outcome'] and int(summary['final'])-int(summary['start'])==188<=200 and summary['target_core']=='70122' and summary['matches']=='8','summary bound and target identity')
    need((D/'counter1-done.txt').read_text()=='earliest-counter1-irq-complete\n','done output')
    controls=[]
    mutations=[('latefirst',lines[4].replace('VCOUNT=8','VCOUNT=10'),4),
               ('crossframe',lines[-1].replace('core=70122','core=70123'),len(lines)-1),
               ('wrongoperand',lines[4].replace('R1=00000001','R1=00000002'),4)]
    for label,replacement,index in mutations:
        altered=lines.copy();altered[index]=replacement
        try:check_trace(altered)
        except ValueError:controls.append(label)
        else:raise AssertionError(label)
    try:check_trace([line for n,line in enumerate(lines) if n!=7])
    except ValueError:controls.append('missingstore')
    else:raise AssertionError('missingstore')
    report=dict(status='ACTUAL_COUNTER1_SAME_CORE_DEADLINE_PASS',launch_sha256=sha(raw),
                auditor_sha256=sha(Path(__file__).read_bytes()),inventory_files=len(inventory),
                source_Core_sha256=CORE,restored_Core_sha256=sha(restored),strict_whole_Core_equal=False,
                raw_Core_differences=diff,
                difference_classification='Native17C..17D channel4 LFSR,184..185 last event,188..189 next event; functional audio state, not padding.',
                CPU_extensions_managed_equal=True,all5_restored_RAM_equal=True,genuine_states=states,
                actual_timing=timing,neutral_advanced_frames=188,trace_negative_controls=controls,
                limits=['Actual timing applies to this restored bounded run; raw source Core differs in six functional audio bytes.',
                        'No full-Core normalization or new independent loader-cause claim.',
                        'This probe stops at counter1 final IRQ; scene remainsCD510/mode7. Prior mode8/cleanup proof is separate.',
                        'No emulator launched, original capture/source/main/Git unchanged.'])
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(sha(a.report.read_bytes()))

if __name__=='__main__':main()
