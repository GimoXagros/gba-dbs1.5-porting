"""Independent original-score/PCM/native-stream/selector/extent audit."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from verify_shoot_attack_dispatch import Machine

ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest().upper()
def need(ok,label):
    if not ok:raise ValueError(label)
def u(b,a):return struct.unpack_from('<I',b,a)[0]
def h(b,a):return struct.unpack_from('<H',b,a)[0]
PINS={'tools/analyze_wsc_evolution_music.py':'2ED6FD43C11F636C11D38415AB07BA6B8FBE6E92531EB58890572BDCD09F8413',
      'tools/build_wsc_evolution_music.py':'E477925703C4DCD66A5239DCA1F0A806E208DAF02AD2FE95998C055330FC0077'}

def decode_source(data):
    speed,wave,vol,effect=data[:4];need(speed<16,'source speed domain')
    vib,pan,env,period=254,255,0,0;tick=0;notes=[]
    for at in range(4,len(data),2):
        op,arg=data[at:at+2]
        if op==255:
            need(arg==255 and at+2==len(data),'unique exact terminal');break
        if op==160:vol=arg
        elif op==162:wave=arg
        elif op==163:vib=arg
        elif op==164:effect=arg
        elif op==165:pan=arg
        elif 192<=op<=207:env=op-192;period=arg
        elif op in (176,253):need(data[4:]==bytes.fromhex('a000fdf01f01b0f0ffff'),'only bounded exact silent loop')
        else:
            need(op<160 and arg>0,'source supported note/rest')
            onset=lambda t:0 if t==0 else ((t-1)*16)//(16-speed)+1
            notes.append(dict(tick=tick,duration=arg,packed_note=op,midi_note=None if op%16>=12 else 36+(op//16)*12+op%16,
                wave=wave,volume=vol,effect=effect,vibrato=vib,stereo_ceiling=pan,envelope_mode=env,envelope_period=period,
                update=onset(tick),duration_updates=onset(tick+arg)-onset(tick)))
            tick+=arg
    else:raise ValueError('missing terminal')
    return notes,0 if tick==0 else ((tick-1)*16)//(16-speed)+1

def amplitude(wsc,n,age):
    v=n['volume'];p=n['envelope_period']
    if age and p and n['envelope_mode']:
        # Reproduce the V30 AL-width carry/subtract quotient, not Python division.
        al=min(age-1,p);q=0
        for _ in range(4):
            al=(al<<1)&255;q<<=1
            if al>=p:al-=p;q|=1
        shape=wsc[0x754DA0+16*n['envelope_mode']+q]&240
        v=wsc[0x754867+shape+n['volume']]>>4
    return min(v,n['stereo_ceiling']>>4),min(v,n['stereo_ceiling']&15)

def stream(data):
    p=t=0;control={};active=None;notes=[]
    while p<len(data):
        op=data[p];p+=1
        if op==129:
            if active is not None:active['curve'].append(tuple(control[k] for k in (190,191,192)))
            t+=1
        elif op in (187,188,189,190,191,192,193):
            need(p<len(data) and data[p]<128,'native scalar');control[op]=data[p];p+=1
        elif op==207:
            need(active is None and data[p+1]==127,'native tie domain')
            active=dict(update=t,key=data[p],voice=control[189],bend_range=control[193],curve=[]);p+=2
        elif op==206:
            need(active is not None and data[p]==active['key'],'matched native EOT');p+=1
            active['duration_updates']=t-active['update'];notes.append(active);active=None
        elif op==177:
            need(p==len(data) and active is None and control[187]==95 and control[188]==0,'clean full native stream')
            return t,notes
        else:raise ValueError('unsupported native opcode')
    raise ValueError('missing FINE')

def audit():
    for p,d in PINS.items():need(sha((ROOT/p).read_bytes())==d,'author frozen '+p)
    folder=ROOT/'build/wsc-evolution-music-20261110'
    before=(ROOT/'build/shoot-terminal-owner-link-20261109/component.gba').read_bytes()
    after=(folder/'component-r1.gba').read_bytes();mb=(folder/'component-r1.json').read_bytes();m=json.loads(mb)
    need(sha(before)=='46B37BAA3741E13A1C9873C3C5B496B9A6BD05B33F541162271D53EC3AB3C22B' and sha(after)=='DD6D73B51B867E3EA2EE5D691252FB2A8F15FE82F8BFD3C172FCBCACAA7A6049','frozen ROMs')
    need(sha(mb)=='AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91','frozen manifest')
    wsc=Path('C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc').read_bytes()
    need(sha(wsc)=='C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7','original source')
    need(len(before)==0x800000 and len(after)==0x1000000,'16MiB extension')
    extended=before+b'\xff'*0x800000;restored=bytearray(after);spans=[];writes={}
    for row in m['writes']:
        a,n=row['offset'],row['size'];spans.append((a,a+n));writes[row['label']]=row
        need(sha(after[a:a+n])==row['after_sha256'] and extended[a:a+n]==bytes.fromhex(row['before_hex']),'actual declared write')
        restored[a:a+n]=extended[a:a+n]
    need(bytes(restored)==extended and len(spans)==42 and sum(z-a for a,z in spans)==104245,'complete extension inverse')
    spans.sort();need(all(x[1]<=y[0] for x,y in zip(spans,spans[1:])),'all placements nonoverlapping')
    oldsites=(0x37C2A4,0x37C2D8,0x37C324,0x37C378,0x37C3AC,0xD14A8,0xD14AC,0xD14B0,0xD14C4,0xD14D0,0xD14D8)
    need({(a,z-a) for a,z in spans if a<0x800000}=={(a,4) for a in oldsites},'exact eleven old words only; existing engine unchanged')
    intervals=((0xD33000,0xD40000),(0xD41000,0xD4B000),(0xD74000,0xD7E000))
    need(all(any(a<=x and y<=z for a,z in intervals) for x,y in spans if x>=0x800000),'extension placement bounds')
    refs=[]
    for at in range(len(before)-3):
        word=u(before,at)
        if any(0x08000000+a<=word<0x08000000+z for a,z in intervals):refs.append(at)
        if at%4==0 and word>>28!=15 and word&0x0E000000==0x0A000000:
            off=word&0xFFFFFF;off-=0x1000000 if off&0x800000 else 0
            if any(a<=at+8+off*4<z for a,z in intervals):refs.append(at)
    need(not refs,'independent conservative old-image pointer/ARM census')
    need(after[0xD33000:0xD33000+108*8]==before[0x686800:0x686800+108*8],'all108 original native songs exact')
    waveids=m['source_wave_ids'];freq=round(3072000*4096/h(wsc,0x754837))
    for wave in waveids:
        row=writes[f'original_wave_{wave:02X}'];a=row['offset'];packed=wsc[0x754CC0+16*wave:0x754CD0+16*wave]
        pcm=bytes(((byte>>shift&15)*16-120)&255 for byte in packed for shift in (0,4))
        need(after[a:a+16]==struct.pack('<IIII',0x40000000,freq,0,32) and after[a+16:a+49]==pcm+pcm[:1],'source waveform signed PCM and loop guard')
    nr=writes['wsc_noise_mode0'];a=nr['offset'];reg=0;noise=[]
    for _ in range(32767):
        bit=1^((reg>>7)&1)^((reg>>14)&1);reg=((reg<<1)|bit)&32767;noise.append(120 if reg&1 else 136)
    need(reg==0 and after[a:a+16]==struct.pack('<IIII',0x40000000,freq,0,32767) and after[a+16:a+16+32768]==bytes(noise+[noise[0]]),'full source mode0 XNOR sequence and PCM loop')
    voices=writes['original_wave_voices'];voicebase=voices['offset']
    for i in range(len(waveids)+1):
        label=f'original_wave_{waveids[i]:02X}' if i<len(waveids) else 'wsc_noise_mode0'
        need(after[voicebase+12*i:voicebase+12*i+12]==bytes((0,60,0,0))+struct.pack('<I',0x08000000+writes[label]['offset'])+bytes((255,0,255,0)),'source PCM voices only')
    count=0;curves=0;maxerr=0;durations=[]
    for song in m['source']['songs']:
        totals=[]
        for c in song['channels']:
            sid=c['id'];state,hardware,off=struct.unpack_from('<HHH',wsc,0x3F0000+6*sid);end=h(wsc,0x3F0000+6*(sid+1)+4)
            data=wsc[0x3F0000+off:0x3F0000+end];notes,updates=decode_source(data)
            need(notes==c['notes'] and updates==c['driver_updates'] and hardware==c['hardware_channel'],'independent original parser and closed-form fractional onset')
            row=writes[f'source_{sid:02X}_native_track'];ticks,actual=stream(after[row['offset']:row['offset']+row['size']])
            if c['silent_infinite_rest']:need(ticks==0 and not actual,'explicit silent-loop lifetime collapse');continue
            totals.append(updates);need(ticks==updates,'whole native finite timeline')
            pitched=[n for n in notes if n['midi_note'] is not None];need(len(pitched)==len(actual),'all native notes present')
            for n,d in zip(pitched,actual):
                voice=len(waveids) if hardware==3 and n['effect'] else waveids.index(n['wave'])
                need((d['update'],d['duration_updates'],d['key'],d['voice'])==(n['update'],n['duration_updates'],n['midi_note'],voice),'independent onset/duration/key/voice')
                for age,(volume,pan,bend) in enumerate(d['curve']):
                    left,right=amplitude(wsc,n,age);total=left+right
                    need(volume==round(total*127/30) and pan==(min(127,round(128*right/total)) if total else 64),'every native stereo/envelope scalar')
                    elapsed=n['update']+age;prior=max(0,elapsed-1);delta=0;v=n['vibrato']
                    if v!=254 and age and prior-prior*data[0]//16-n['tick']>=2*(v&15):
                        delta=wsc[0x754967+(v&240)+(elapsed&15)];delta=delta-256 if delta>=128 else delta
                    divisor=(h(wsc,0x754837+2*(n['packed_note']&15))>>(n['packed_note']>>4))-delta
                    ideal=12*math.log2((3072000/divisor)/((freq/1024)*2**((d['key']-60)/12)))
                    expected=max(-64,min(63,round(ideal*64/d['bend_range'])))
                    need(bend-64==expected,'every native pitch bend against original divisor')
                    maxerr=max(maxerr,abs((bend-64)*d['bend_range']/64-ideal)*100);curves+=1
                count+=1
        durations.append(max(totals))
    need(durations==[3309,2753,2972,2089] and count==1917,'four exact source schedules')
    categories=wsc[0x787267:0x787277];cases=0
    for character,category in enumerate(categories):
        for busy in (0,1,123,65535):
            mm=Machine(after,seed=character);mm.r[13]=0x03007F00;mm.r[14]=0x09000000;sp=mm.r[13];saved=mm.r[:3]
            for addr,value in ((sp,character),(0x030022F6,busy),(0x030022F2,0x1234),(0x030022FE,0x5678),(0x03002300,0x20)):mm.put(addr,value,4 if addr==sp else 2)
            mm.run(0x080D14BC,{0x09000000});need(mm.r[:3]==saved and mm.r[13]==sp,'real selector ABI')
            expected=(108+category,4,1770,288) if busy==0 else (0x1234,0x5678,busy,32)
            need(tuple(mm.get(a,2) for a in (0x030022F2,0x030022FE,0x030022F6,0x03002300))==expected,'real selector category/busy gate');cases+=1
    return dict(status='INDEPENDENT_AUDIO_RECONSTRUCTION_STRUCTURAL_PASS',component_sha256=sha(after),manifest_sha256=sha(mb),
        input_size=len(before),output_size=len(after),writes=42,declared_bytes=104245,changed_bytes=sum(a!=b for a,b in zip(extended,after)),
        complete_inverse=True,old_words_changed=11,prior_song_entries_preserved=108,old_image_inbound_encodings=0,
        original_source_channels=16,source_updates=durations,native_notes=count,independently_checked_curve_updates=curves,
        max_quantized_pitch_error_cents=maxerr,actual_ARM_selector_cases=cases,source_wave_ids=waveids,noise_period=32767,
        tempo_relative_error=((16777216/280896)*(95/75))/(3072000/(256*159))-1,
        risks=['Not yet based on280D; audio predecessor is46B3. Integration must preserve display-epoch layer separately.',
               'No executed M4A player/audio capture: parsed streams and native selector only.',
               'Native cooldown1770 retained versus source2220 on different platform clocks; request override/lifetime parity unqualified, numeric mismatch alone is not a regression.',
               'Global vibrato phase0, PCM note-phase restart, amplitude/pan quantization, tempo error and silent-loop FINE differ from source.',
               'Song title identity and audible fidelity are unverified; arbitrary/malformed character IDs outside0..15 not qualified.'],
        author_sources=PINS,verifier_sha256=sha(Path(__file__).read_bytes()),emulator_launched=False,audible_parity=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    need(not a.report.exists(),'fresh report');r=audit();a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_bytes((json.dumps(r,indent=2)+'\n').encode());print(r['status'],sha(a.report.read_bytes()))
if __name__=='__main__':main()
