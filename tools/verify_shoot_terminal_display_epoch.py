"""Independent affected ARM, ownership and temporal-boundary QA."""
import argparse
import json
import struct
import types
from pathlib import Path
import verify_shoot_guarded_transition_irq as old
from verify_shoot_terminal_display_epoch_production import audit,need,sha,ROOT

OVERLAPS=((0x6FF3B4,0xE1D010B0,0x086FF75A),(0x6FFBE8,0xE59F11D4,0x086FF72C),
 (0x6FFBF4,0xE5950028,0x086FF724),(0x6FFC00,0xE5960028,0x086FF732),
 (0x6FFC0C,0xE59F01B4,0x086FF750),(0x6FFC1C,0xE59F01A8,0x086FF760),(0x6FFC20,0xE5900000,0x086FF746))

def fixture(rom,flags=0x10,counter=40):
    m,f,s,a,h=old.prepared_fixture(rom,flags,counter)
    m.put(a+0x18,f);m.put(a+0x28,s);m.put(0x0400000A,0x1F03,2)
    m.writes.clear();return m,f,s,a,h

def structure(before,after,source):
    need(old.text(after,0x6FF720,64)==[
        'mov r0, #0x4000000','ldrh r1, [r0]','tst r1, #7','bne #0x86ff6f4',
        'ldrh r1, [r0, #0xa]','tst r1, #0xcc','bne #0x86ff6f4','ldr r0, [pc, #0x1c]',
        'ldr r1, [r0]','cmp r1, #0','bne #0x86ff6f4','ldr r1, [r0, #0x50]',
        'cmp r1, #0','bne #0x86ff6f4','ldr r0, [pc, #4]','b #0x85e7400'],'complete independent stub disassembly')
    need(old.branch(after,0x6FF6E8)==0x086FF720 and old.u(after,0x6FF6E8)>>24==0xEB,'linking call and same continuation')
    need(before[0x6FFC30:0x6FFDE8]==after[0x6FFC30:0x6FFDE8] and
         before[0x6FFE10:0x6FFED0]==after[0x6FFE10:0x6FFED0],'all early velocity/mode/blank-row instructions and IRQ unchanged')
    need(old.branch(before,0x33FD04)==0x086FF380 and
         sha(before[0x6FF380:0x6FF3E8])=='B337C3187857E37930ACF81B8047C8B757E34E865DB934DC3864520541742AFF' and
         old.branch(before,0x6FF694)==0x086FF9C0,'positive ARM owners for apparent Thumb overlaps')
    scan=types.FunctionType(old.scanner.inbound.__code__,dict(old.scanner.__dict__,SPANS=((0x6FF720,0x6FF768),)),argdefs=old.scanner.inbound.__defaults__)
    incoming=scan(before)
    need(incoming==[('Thumb B',a+2,d) for a,_,d in OVERLAPS],'full conservative inbound enumeration')
    need(all(old.u(before,a)==w for a,w,_ in OVERLAPS),'all seven containing ARM words pinned')
    old.layout_contract((ROOT/'records/shoot-guarded-transition-layout-20261109.json').read_bytes(),0x6FF600,0x6FF800)
    need(source[0x75FAE6:0x75FAEA]==bytes.fromhex('b021e607'),'source MOV AL21 OUT7')
    need(old.text(after,0x5E7418,8)==['mov r0, #0x21','bl #0x8000fec'] and after[0x1031]==0x1E,'actual unconditional planned mapping')
    return incoming

def mapping(after):
    # Execute the affected actual guard control-word block for every 16-bit value.
    m=old.Machine(after);accepted=0
    for control in range(65536):
        m.put(0x0400000A,control,2)
        stop=m.run(0x086FFC80,{0x086FFC9C,0x086FFD3C},max_steps=16)
        expected=(((control&255)|0x1E00)&0xDFCC)==0x1E00
        need((stop==0x086FFC9C)==expected,'all-control actual early predicate versus planned mapping')
        accepted+=expected;m.writes.clear();m.reads.clear()
    # Independent native FEC execution establishes high replacement and low preservation.
    for low in range(256):
        for high in (0,0x1E,0x1F,0xFF):
            m=old.Machine(after);m.r[0]=0x21;m.r[14]=old.RETURN
            m.put(0x0400000A,high*256+low,2);m.put(0x04000008,0xA593,2)
            m.run(0x08000FEC,{old.RETURN})
            need(m.get(0x0400000A,2)==0x1E00+low and m.get(0x04000008,2)==0x1F93,'actual FEC both outputs and preserved low bytes')
    return dict(actual_guard_words=65536,accepted_words=accepted,actual_FEC_cases=1024)

def early(before,after):
    a,*_=fixture(before);a.run(0x086FF9C0,{old.RETURN});need(a.r[0]==0,'old hardware high1F refusal')
    b,f,s,aux,_=fixture(after);b.run(0x086FF9C0,{old.RETURN});need(b.r[0]==1,'new prospective bounded acceptance')
    cases=[('velocity'+hex(a),a,v,2) for a in (0x03002354,0x03002356,0x030023A4,0x030023A6) for v in (1,0x200,0xFFFF)]
    cases += [('tile0',0x06000000,1,4),('maprow',0x0600F000+29*64,1,4),
              ('reverseowner',aux+0x28,f,4),('forwardowner',s+0x28,f,4),('FIRSTmotion',f+0x42,1,2),
              ('renderer',0x0300482A,2,2),('mode',0x04000000,3,2),('8bpp',0x0400000A,0x1F83,2)]
    for label,address,value,size in cases:
        m,*_=fixture(after);m.put(address,value,size);m.run(0x086FF9C0,{old.RETURN})
        need(m.r[0]==0,'unchanged early rejection '+label)
    return len(cases)

def consumption(after):
    mutations=[(a,v,2) for a in (0x03002354,0x03002356,0x030023A4,0x030023A6) for v in (1,0xFFFF)]
    mutations += [(0x04000000,v,2) for v in (1,3,7)]
    mutations += [(0x0400000A,0x1F03|v,2) for v in (4,8,0x40,0x80)]
    mutations += [(0x03002310,8,2),(0x0300231E,7,1),(0x0300450A,0,2)]
    count=0
    for flags in range(16):
        for arm in (0,2,4):
            for address,value,size in mutations:
                a,*_=fixture(after,(flags<<28)|0x10);b,*_=fixture(after,(flags<<28)|0x10)
                for m in (a,b):m.put(address,value,size);m.put(0x03004506,arm,2);m.writes.clear()
                sp=a.r[13];a.run(old.DISPLAY,{old.RETURN},max_steps=70000);b.run(0x08587200,{old.RETURN},max_steps=70000)
                need(a.r[:15]==b.r[:15] and old.nonstack_writes(a,sp)==old.nonstack_writes(b,sp),'actual stale route ABI and full effects')
                need((a.cpsr^b.cpsr)&0x0FFFFFFF==0,'only dead dispatcher flags differ')
                count+=1
    for flags in range(16):
        m,*_=fixture(after,(flags<<28)|0x10);initial=m.r[:15];sp=m.r[13]
        m.run(old.DISPLAY,{0x086FF75C});need(m.r[0]==old.IRQ and m.r[14]==0x086FF6EC and m.r[13]==sp-12,'success argument/link/frame')
        need(m.r[2:13]==initial[2:13] and not old.nonstack_writes(m,sp),'cheap stub no nonstack writes or extra register clobber')
        m.run(0x086FF75C,{old.RETURN},max_steps=70000)
        need(m.r[:15]==initial and m.get(0x0400000A,2)==0x1E03 and m.get(old.SLOT)==old.IRQ,'actual display restores all registers and installs mapping/IRQ')
    chains=[]
    for counter in (1,143):
        m,*_=fixture(after,counter=counter);sp=m.r[13]
        m.run(0x080D0BE8,{0x080D0C10},max_steps=70000)
        need(m.get(0x03004574)==0 and m.get(old.SLOT)==old.DISPLAY and m.get(0x04000004,2)==0x12B,'actual copy/pop/line1 schedule')
        m.run(0x0801140C,{0x08011420},max_steps=70000)
        need(m.get(old.SLOT)==old.IRQ and m.get(0x04000004,2)>>8==counter+7 and m.r[13]==sp,'actual cheap consumer and first compare')
        chains.append(dict(counter=counter,first_compare=counter+7,stack_preserved=True))
    return dict(stale_cases=count,valid_ABI_cases=16,actual_queue_first_compare=chains,cycle_timing_measured=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('before','after','source','manifest','report'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();need(not a.report.exists(),'fresh report')
    before,after,source,manifest=(getattr(a,k).read_bytes() for k in ('before','after','source','manifest'))
    packaging=audit(before,after,source,manifest);incoming=structure(before,after,source)
    result=dict(status='INDEPENDENT_DISPLAY_EPOCH_ARM_PASS',packaging=packaging,incoming=incoming,
                mapping=mapping(after),early_refusal_cases=early(before,after),consumption=consumption(after),
                telemetry_evidence='F25BB7845FCB4196A3E555D1F8807057D1173588C811F939C0CFCE3735E99796',
                telemetry_qualification='69932 shake velocity refused;69933 actual hardware1F refused; actual FEC21 not observed in window',
                service_models=[],actual_runtime_acceptance=False,first_line8_deadline_proven=False,
                retained_stationary_family='Existing bounded555554FD typed/blank-row proof reused; no universal DMA or arbitrary-task claim',
                verifier_sha256=sha(Path(__file__).read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(result['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
