#!/usr/bin/env python3
"""Independently decode final CF/D1 M4A scores and source envelope tables."""
from __future__ import annotations
import argparse, hashlib, json, pathlib, struct

BASE=0x08000000
HASHES=('726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284',
        '0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103',
        '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED',
        '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735',
        'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7')

def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)

def read_track(rom,start):
    pos=start;time=0;notes=[];volumes={};voice=volume=mod=pan=tempo=None
    while True:
        op=rom[pos];pos+=1
        if op==0xB1:break
        if 0x81<=op<=0x98:
            for t in range(time,time+op-0x80):volumes[t]=volume
            time+=op-0x80
        elif op in (0xBC,0xBB,0xBD,0xBE,0xBF,0xC2,0xC4,0xC5):
            arg=rom[pos];pos+=1
            if op==0xBC:need(arg==0,'KEYSH')
            elif op==0xBB:tempo=arg
            elif op==0xBD:voice=arg
            elif op==0xBE:volume=arg
            elif op==0xBF:pan=arg
            elif op==0xC2:need(arg==16,'bounded LFOS analogue')
            elif op==0xC4:mod=arg
            else:need(arg==0,'MODT pitch')
        elif 0xD0<=op<=0xE7:
            key,velocity=rom[pos:pos+2];pos+=2
            need(velocity==127,'velocity')
            notes.append(dict(time=time,ticks=op-0xCF,key=key,voice=voice,mod=mod))
        else:raise ValueError(f'unexpected M4A {op:02X} at{pos-1:06X}')
        need(pos<start+512,'finite score boundary')
    need(tempo==75 and pan==127 and mod==0,'backend timing/pan/end modulation')
    return notes,volumes,time,pos

def source_envelope(wsc,mode,span,amplitude,duration):
    values=[]
    for age in range(duration):
        # Independent rendition of four successive x86 shift/subtract bits.
        quotient=0;remainder=age
        for _ in range(4):
            remainder*=2
            bit=remainder>=span
            if bit:remainder-=span
            quotient=quotient*2+int(bit)
        env=wsc[0x754DA0+mode*16+quotient]&0xF0
        nibble=wsc[0x754867+(env|amplitude)]//16
        values.append(round(nibble*127/15))
    return values

def inspect(before,after,gba,old,wsc):
    # These independent expected schedules are read directly from the source
    # packed note/duration pairs, including the A7 leading delay and 1F rests.
    cf_source=wsc[0x3F891A:0x3F8944]
    need(cf_source[:12]==bytes.fromhex('00000f00a202c100a177a707'),'CF setup/wait')
    cf=[];clock=7
    for p in range(12,40,4):
        rest,delay,note,ticks=cf_source[p:p+4]
        need((rest,delay,ticks)==(0x1F,3,7),'CF rest/note pair')
        clock+=delay;cf.append((clock,ticks,36+(note>>4)*12+(note&15),0,0,15,0,0));clock+=ticks
    need(clock==77 and cf_source[40:]==b'\xff\xff','CF complete duration')
    need(wsc[0x3F895E:0x3F8984]==bytes.fromhex('00000f01c240a31aa20016083010a204cb10a334a00f62061f02a00562081f04a0026206ffff'),'D1 score')
    d1=[(0,8,54,1,0x1A,15,2,64),(8,16,72,1,0x1A,15,2,64),
        (24,6,110,2,0x34,15,11,16),(32,8,110,2,0x34,5,11,16),
        (44,6,110,2,0x34,2,11,16)]
    need(sha(wsc[0x753E80:0x753F28])=='C2120D65701A09F44AE9D9C3DA5BC80DB1E182F4E98F83F2DC34B5763DC13CE1','source envelope consumer')
    need(sha(wsc[0x75445D:0x7547B3])=='3BCD7EE344CA919C4937CBC8A5159AE9F46859B07F18881C0FCFEDC8DC337CB6','source command/note/rest consumers')
    # Positive commercial timbre analogues: source A9 has A2=00 and native4D
    # voice17; source93 has A2=04 and native38 voice8 in its other voicegroup.
    need(old[0x2D83BA:0x2D83BE]==bytes.fromhex('a200a37a'),'wave00 oracle payload')
    need(old[0x2D81E0:0x2D81E4]==bytes.fromhex('a204cb10'),'wave04 oracle payload')
    need(struct.unpack_from('<III',gba,0x370AA8-12)==(0xE3A0804D,0xE3A09001,0xE3A0A000),'wave00 oracle request')
    need(struct.unpack_from('<III',gba,0x36EFA4-12)==(0xE3A08038,0xE3A09001,0xE3A0A000),'wave04 oracle request')
    need(gba[0x38753C:0x387542]==bytes.fromhex('bc00bb4bbd17'),'wave00 native voice')
    need(gba[0x387194:0x38719A]==bytes.fromhex('bc00bb4bbd08'),'wave04 native voice')
    intervals=[];details=[]
    for sid,start,schedule,total in ((0x5D,0x5CA000,cf,77),(0x5E,0x5CA100,d1,50)):
        entry=0x5BA400+sid*8
        need(struct.unpack_from('<IHH',after,entry)==(BASE+start,4,4),'new song table receiver')
        need(after[start:start+4]==bytes((1,0,40,128)),'one-track native header')
        need(struct.unpack_from('<II',after,start+4)==(BASE+0x5CA300,BASE+start+12),'voice/track pointers')
        notes,volumes,time,end=read_track(after,start+12)
        expected=[dict(time=t,ticks=d,key=k,voice=v,mod=m) for t,d,k,v,m,_,_,_ in schedule]
        need(notes==expected and time==total,'exact pitches/onsets/durations/voice/mod')
        for t,d,k,v,m,amplitude,mode,span in schedule:
            values=source_envelope(wsc,mode,span,amplitude,d) if mode else [127]*d
            need([volumes[x] for x in range(t,t+d)]==values,'independent per-note amplitude table')
        intervals.extend(((entry,entry+8),(start,end)))
        details.append(dict(id=sid,start=start,end=end,bytes=end-start,sha256=sha(after[start:end]),notes=notes,total_ticks=total))
    for n,original in enumerate((0x37E8E0+0x14*12,0x37E8E0+0x17*12,0x37EAA8+8*12)):
        actual=after[0x5CA300+n*12:0x5CA300+(n+1)*12]
        need(actual[:8]==gba[original:original+8] and actual[8:]==bytes((0,0,15,0)),'voice timbre fields and neutral envelope')
    intervals.append((0x5CA300,0x5CA324))
    allowed={x for start,end in intervals for x in range(start,end)}
    need(all(before[x]==255 for x in allowed),'Expected Write FF')
    changed=[i for i,(x,y) in enumerate(zip(before,after,strict=True)) if x!=y]
    need(changed and all(x in allowed for x in changed),'full-ROM diff containment')
    return dict(songs=details,intervals=intervals,changed_bytes=len(changed))

def main():
    p=argparse.ArgumentParser()
    for n in ('before','after','gba','wsc10','wsc15'):p.add_argument(n,type=pathlib.Path)
    p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args()
    data=[getattr(a,n).read_bytes() for n in ('before','after','gba','wsc10','wsc15')]
    for value,h in zip(data,HASHES,strict=True):need(sha(value)==h,'input hash')
    result=inspect(*data);rejected=[]
    for pos,new,label in ((0x5BA6E8,b'\x04','table target'),(0x5CA00C+5,b'\x40','pan'),
                          (0x5CA300,b'\x04','voice timbre'),(0x5CA308,b'\x01','hidden ADSR'),
                          (0x5CA104,b'\x04','voice pointer')):
        mutated=list(data);copy=bytearray(data[1]);copy[pos:pos+len(new)]=new;mutated[1]=copy
        try:inspect(*mutated)
        except ValueError:rejected.append(label)
        else:raise ValueError('negative control escaped '+label)
    result.update(input_hashes=list(HASHES),negative_controls=rejected,runtime_executed=False,
                  hardware_stereo_sweep_modulation_parity_verified=False)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(sha(a.output.read_bytes()))
    return 0
if __name__=='__main__':raise SystemExit(main())
