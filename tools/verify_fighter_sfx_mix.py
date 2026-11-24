"""Overlap the installed C6 with natural retail music and observe wave-channel reclamation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import struct
import wave
import numpy as np

from build_character_select_name_scene import Allocator, BASE, exclude, sha
from mgba_headless_gdb_capture import PrivateDesktopProcess
from mode23_linker import compose
from render_fighter_sfx import ascii_output_drive,isolated_config,EXE


def branch(from_bus,to_bus):
    dist=to_bus-from_bus-8
    assert dist%4==0 and abs(dist)<1<<25
    return struct.pack('<I',0xeb000000+(dist//4&0xffffff))


def fixture(rom,raw,bgm,header,enabled):
    issue='bx r12' if enabled else 'nop'
    body=f"""
fighter_mix:
    push {{r0-r12,lr}}
    mrs r7,cpsr
    push {{r7}}
    ldr r0,=0x03006b40
    ldr r1,[r0]
    ldr r2,={bgm:#x}
    cmp r1,r2
    bne finish
    ldr r1,[r0,#12]
    cmp r1,#48
    blo finish
    cmp r1,#52
    bhs finish
    ldr r0,=0x03006c00
    ldr r1,[r0]
    ldr r2,={header:#x}
    cmp r1,r2
    beq finish
    mov r0,#0x60
    ldr r12,=0x0837c27d
    mov lr,pc
    {issue}
finish:
    pop {{r7}}
    msr cpsr_f,r7
    pop {{r0-r12,lr}}
    b 0x080d1500
    .ltorg
"""
    code=compose((body,),BASE+raw,('fighter_mix',))[0]
    assert len(code)<=160 and rom[raw:raw+len(code)]==bytes([255])*len(code)
    after=bytearray(rom)
    after[raw:raw+len(code)]=code
    assert rom[0x2bc:0x2c0]==branch(BASE+0x2bc,0x080d1500)
    after[0x2bc:0x2c0]=branch(BASE+0x2bc,BASE+raw)
    return after


def render(out,drive,rom,exe,existing):
    if existing:
        assert (out/'fixture.gba').read_bytes()==rom
    else:
        out.mkdir()
        alias=drive+out.name
        (out/'config.json').write_text(json.dumps(isolated_config(alias)),encoding='utf-8')
        (out/'fixture.gba').write_bytes(rom)
        args=['--gdi','--config='+alias+'/config.json','--lua='+drive+'observer.lua','--userdata=output:'+alias,
              '--dump-type=wave','--dump-name='+alias+'/mix.wav','--dump-length=800','--dump-close',alias+'/fixture.gba']
        with PrivateDesktopProcess(exe,args,exe.parent)as proc:
            assert proc._wait_process(proc.process.hProcess,120000)==0
    entries=[tuple(int(v,10 if i==0 else 16) for i,v in enumerate(s.split())) for s in (out/'mix.txt').read_text().splitlines()]
    with wave.open(str(out/'mix.wav'))as w:pcm=np.frombuffer(w.readframes(w.getnframes()),'<i2').reshape(-1,2)
    return entries,pcm


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('image','owner','output'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--emulator',type=Path,default=Path(__file__).resolve().parents[1]/'local/BizHawk-2.11.1/EmuHawk.exe')
    p.add_argument('--verify-existing',action='store_true')
    a=p.parse_args()
    rom=a.image.read_bytes()
    meta=json.loads(a.owner.read_bytes());assert meta['output_sha256']==sha(rom)
    table=struct.unpack_from('<I',rom,0x37c2a4)[0]-BASE
    bgm=struct.unpack_from('<I',rom,table+8)[0]
    wanted=struct.unpack_from('<I',rom,table+8*0x60)[0]
    alloc=Allocator(rom)
    exclude(alloc,meta['prior_excluded_extents']+[[r['start'],r['end']] for r in meta['allocations']])
    raw=alloc.allocate(160,'diagnostic concurrent C6 and retail music',4)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=a.verify_existing)
    exe=a.emulator.resolve();assert sha(exe.read_bytes())==EXE
    observer=Path(__file__).with_name('bizhawk_fighter_sfx_mix.lua')
    if a.verify_existing:assert observer.read_bytes()==(out/'observer.lua').read_bytes()
    else:shutil.copyfile(observer,out/'observer.lua')
    with ascii_output_drive(out)as drive,ThreadPoolExecutor(max_workers=2)as pool:
        both=list(pool.map(lambda b:render(out/('cue' if b else 'control'),drive,fixture(rom,raw,bgm,wanted,b),exe,a.verify_existing),(False,True)))
    (control,quiet),(actual,mixed)=both
    sounding=[row for row in actual if row[4]==wanted and row[5]&0xffff]
    assert sounding and not any(row[4]==wanted for row in control)
    held=[row for row in sounding if row[6]&0xc7 and row[7]==0x030051c0]
    assert held
    lo,hi=sounding[0][0],sounding[-1][0]
    after=[row for row in actual if hi+5<=row[0]<=hi+100]
    assert after and all(row[7]!=0x030051c0 for row in after)
    baseline={r[0]:r for r in control}
    reclaimed=[r for r in after if r[6]&0xc7 and r[7]==0x03004f40 and r[6:]==baseline[r[0]][6:]]
    assert len(reclaimed)>20
    window=[r for r in actual if lo<=r[0]<=hi+60]
    assert all(r[1:4]==baseline[r[0]][1:4] and r[1]==bgm and r[2]&0xffff for r in window)
    assert len({r[3] for r in window})>60
    start,end=[round(fr*44100/(16777216/280896)) for fr in (hi+20,hi+75)]
    x=quiet[start:end].astype(float).ravel();y=mixed[start:end].astype(float).ravel()
    corr=float(np.corrcoef(x,y)[0,1])
    assert np.std(y)>100
    # Retriggering wave RAM resets oscillator phase. Compare the music's
    # spectral shape separately from exact sample correlation after return.
    similarities=[]
    for start_frame in range(hi+20,hi+70,10):
        z=[]
        first,last=[round(t*44100/(16777216/280896)) for t in (start_frame,start_frame+10)]
        for signal in (quiet,mixed):
            vals=signal[first:last].mean(axis=1)
            z.append(np.abs(np.fft.rfft((vals-vals.mean())*np.hanning(len(vals)))))
        similarities.append(float(z[0]@z[1]/(np.linalg.norm(z[0])*np.linalg.norm(z[1]))))
    assert min(similarities)>.90
    report=dict(status='C6_WAVE_CHANNEL_RELEASE_AND_RETAIL_MUSIC_PASS',image_sha256=sha(rom),native_bgm=hex(bgm),
                cue_header=hex(wanted),m4a_active_frames=[lo,hi],wave_owned_frames=[held[0][0],held[-1][0]],
                wave_owner_gone_samples=len(after),original_wave_track_reclaimed_frame=reclaimed[0][0],
                matched_music_header_status_and_clock_frames=len(window),post_effect_spectral_cosines=similarities,
                post_effect_retail_stereo_correlation=round(corr,6),phase_bit_identity=False,isolated_diagnostic=True,guest_writes=False,
                evidence={b:{n:sha((out/b/n).read_bytes()) for n in ('fixture.gba','mix.wav','mix.txt')} for b in ('control','cue')})
    path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['status'],sha(path.read_bytes()))


if __name__=='__main__':main()

