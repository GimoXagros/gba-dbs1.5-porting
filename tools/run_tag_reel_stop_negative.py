"""Negative control for the score-reel stop while a different retail song owns player 3."""
import argparse
import json
import math
from array import array
from pathlib import Path
import struct
import wave

from build_character_select_name_scene import Allocator, BASE, exclude
from mgba_headless_gdb_capture import PrivateDesktopProcess
from mode23_linker import compose
from verify_mode23_audio_assets import sha


def branch(origin,target):
    delta=target-origin-8
    assert delta%4==0 and -(1<<25)<=delta<1<<25
    return struct.pack("<I",0xEB000000|((delta//4)&0xffffff))


def run(root,out,rom,header,request,existing):
    if existing:
        assert (out/"fixture.gba").read_bytes()==rom
    else:
        out.mkdir()
        alias="W:/"+out.relative_to(root).as_posix()
        cfg=json.loads((root/"build/bizhawk-gba-diagnostic-20261026/config.json").read_text(encoding="utf-8-sig"))
        for i,entry in enumerate(cfg["PathEntries"]["Paths"]):
            entry["Path"]=alias+"/data/"+str(i)
            Path(entry["Path"]).mkdir(parents=True)
        cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,
                   SoundEnabledNormal=False,SoundVolume=0,SoundVolumeRWFF=0,SpeedPercent=1000)
        (out/"config.json").write_text(json.dumps(cfg,indent=2),encoding="utf-8")
        (out/"fixture.gba").write_bytes(rom)
        exe=root/"local/BizHawk-2.11.1/EmuHawk.exe"
        assert sha(exe.read_bytes())=="F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD"
        args=["--lua=W:/tools/bizhawk_observe_tag_reel_negative.lua","--userdata=output:"+alias+";request:"+str(request),"--gdi",
              "--config="+alias+"/config.json","--dump-type=wave","--dump-name="+alias+"/render.wav",
              "--dump-length=1050","--dump-close",alias+"/fixture.gba"]
        with PrivateDesktopProcess(exe,args,exe.parent) as proc:
            assert proc._wait_process(proc.process.hProcess,180000)==0
    lines=(out/"trace.txt").read_text().splitlines()
    active=[x for x in lines if f"mplay3 {header:08X} 00000001" in x]
    assert len(active)==1 and any("completed stop comparisons=" in s for s in lines)
    comparisons=int(next(s for s in lines if "completed stop comparisons=" in s).split("=")[-1])
    assert not any(f"mplay3 {header:08X} 80000000" in row for row in lines)
    with wave.open(str(out/"render.wav")) as w:
        assert (w.getnchannels(),w.getframerate(),w.getsampwidth())==(2,44100,2)
        raw=array("h",w.readframes(w.getnframes()))
    return raw,dict(active_frame=int(active[0].split()[0]),comparisons=comparisons,wav_sha256=sha((out/"render.wav").read_bytes()),
                    trace_sha256=sha((out/"trace.txt").read_bytes()),fixture_sha256=sha(rom))


def main(a):
    root=Path(__file__).resolve().parents[1]
    rom=a.image.read_bytes();m=json.loads(a.manifest.read_bytes());assert sha(rom)==m["output_sha256"] and m["song_count"]==128
    base=bytearray(rom);at=m["table"];row=rom[at+8*0x55:at+8*0x56]
    header,player,alias=struct.unpack("<IHH",row);assert (header,player,alias)==(0x083876f0,3,3)
    wanted,player,alias=struct.unpack_from("<IHH",rom,at+8*0x7f);assert player==alias==3 and wanted!=header
    base[at+8:at+16]=row
    assert base[0x2bc:0x2c0]==branch(0x080002bc,0x080d1500)
    alloc=Allocator(rom)
    exclude(alloc,m["prior_excluded_extents"]+[[r["start"],r["end"]] for r in m["allocations"]])
    raw=alloc.allocate(128,"isolated score-reel stop observation",4)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=a.verify_existing)
    results=[];waves=[]
    for active in (False,True):
        call="bx r12" if active else "nop"
        code=f"""
negative_reel:
    push {{r0-r12,lr}}
    mrs r7,cpsr
    push {{r7}}
    ldr r0,=0x03006c90
    ldr r1,[r0]
    ldr r2,={header:#x}
    cmp r1,r2
    bne negative_done
    ldrh r1,[r0,#4]
    cmp r1,#0
    beq negative_done
    mov r0,#0x7f
    ldr r12,=0x0837c349
    mov lr,pc
    {call}
negative_done:
    pop {{r7}}
    msr cpsr_f,r7
    pop {{r0-r12,lr}}
    b 0x080d1500
    .ltorg
"""
        payload=compose((code,),BASE+raw,("negative_reel",))[0]
        assert len(payload)<=128 and not any(x!=255 for x in base[raw:raw+len(payload)])
        data=bytearray(base);data[raw:raw+len(payload)]=payload;data[0x2bc:0x2c0]=branch(0x080002bc,BASE+raw)
        audio,report=run(root,out/("stop" if active else "control"),data,header,wanted,a.verify_existing)
        results.append(report);waves.append(audio)
    assert results[0]["comparisons"]==0 and results[1]["comparisons"]>150
    assert results[0]["active_frame"]==results[1]["active_frame"]
    lo=int(560*44100/59.7275)*2;hi=int(950*44100/59.7275)*2
    assert min(max(abs(i) for i in w[lo:hi]) for w in waves)>0
    reference,treatment=(w[lo:hi] for w in waves)
    count=len(reference)
    equal=sum(a==b for a,b in zip(reference,treatment))
    correlation=sum(a*b for a,b in zip(reference,treatment))/math.sqrt(sum(a*a for a in reference)*sum(b*b for b in treatment))
    assert equal/count>0.99 and correlation>0.99
    # Both recordings continue for every half second of the observation.
    for cursor in range(0,count,44100):
        for stream in (reference,treatment):
            assert max(map(abs,stream[cursor:cursor+44100]))>1000
    report=dict(status="PASS",physical_display_visible=False,guest_writes=False,production=sha(rom),
                owner=hex(header),requested=hex(wanted),checks=results,observed_stereo_frames=count//2,identical_sample_fraction=equal/count,correlation=correlation)
    path=out/"report.json";path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS",sha(path.read_bytes()))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("image","manifest","output"):p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--verify-existing",action="store_true")
    main(p.parse_args())
