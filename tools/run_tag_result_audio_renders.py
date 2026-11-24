"""Render the installed native Tamer Tag rows through the real game boot and M4A player."""
import argparse
from array import array
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import struct
import wave

from mgba_headless_gdb_capture import PrivateDesktopProcess


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def render(root, folder, base_image, manifest, item):
    number=item["native"]
    out=folder/f"song-{number:02X}"
    out.mkdir()
    alias="W:/"+out.relative_to(root).as_posix()
    cfg=json.loads((root/"build/bizhawk-gba-diagnostic-20261026/config.json").read_text(encoding="utf-8-sig"))
    for i,entry in enumerate(cfg["PathEntries"]["Paths"]):
        entry["Path"]=alias+"/data/"+str(i)
        Path(entry["Path"]).mkdir(parents=True)
    cfg.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,SoundEnabled=False,
               SoundEnabledNormal=False,SoundVolume=0,SoundVolumeRWFF=0,SpeedPercent=1000)
    (out/"config.json").write_text(json.dumps(cfg,indent=2),encoding="utf-8")
    table=manifest["table"]
    row=base_image[table+number*8:table+number*8+8]
    header,player,mirror=struct.unpack("<IHH",row)
    assert player==mirror==item["player"] and header==0x08000000+item["header_raw"]
    change=table+8
    fixture=base_image[:change]+row+base_image[change+8:]
    assert fixture[:change]+base_image[change:change+8]+fixture[change+8:]==base_image
    (out/"fixture.gba").write_bytes(fixture)
    emulator=root/"local/BizHawk-2.11.1/EmuHawk.exe"
    assert sha(emulator.read_bytes())=="F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD"
    state=struct.unpack_from("<I",base_image,0x37FBB4+player*12)[0]-0x03000000
    args=["--lua=W:/tools/bizhawk_observe_tag_result_audio.lua","--userdata=output:"+alias+";player:"+str(state)+";song:"+str(header),
          "--gdi","--config="+alias+"/config.json","--dump-type=wave","--dump-name="+alias+"/render.wav",
          "--dump-length=1050","--dump-close",alias+"/fixture.gba"]
    with PrivateDesktopProcess(emulator,args,emulator.parent) as proc:
        assert proc._wait_process(proc.process.hProcess,180000)==0
    events=(out/"player.txt").read_text().splitlines()
    samples=[(int(t),int(h,16),int(f,16)) for t,h,f in [x.split() for x in events]]
    active=[v for v in samples if v[1]==header and v[2]&0xFFFF]
    assert active and 400<active[0][0]<700
    with wave.open(str(out/"render.wav")) as wav:
        assert wav.getnchannels()==2 and wav.getsampwidth()==2 and wav.getframerate()==44100
        raw=array("h",wav.readframes(wav.getnframes()))
    onset=active[0][0]
    lo=int((onset+3)*44100/59.7275)*2
    hi=int((onset+24)*44100/59.7275)*2
    peaks=[max(map(abs,raw[lo+i:hi:2])) for i in (0,1)]
    assert min(peaks)>0
    finishes=[t for t,h,fl in samples if t>onset and h==header and not(fl&0xFFFF)]
    looping=item["source"] in (0x100,0xB6)
    assert bool(finishes)!=looping
    return dict(source=item["source"],native=number,player=player,observed_start=onset,observed_finish=finishes,
                measured_window_peak_stereo=peaks,fixture_sha256=sha(fixture),row_substitution=[change,8],
                wav_sha256=sha((out/"render.wav").read_bytes()),trace_sha256=sha((out/"player.txt").read_bytes()))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("image","manifest","output"):
        p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    repo=Path(__file__).resolve().parents[1]
    data=a.image.read_bytes()
    meta=json.loads(a.manifest.read_bytes())
    assert sha(data)==meta["output_sha256"] and meta["song_count"]==128
    folder=a.output.resolve()
    folder.mkdir(parents=True,exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs=list(pool.map(lambda row:render(repo,folder,data,meta,row),meta["sounds"]))
    rec=dict(status="PASS",production_rom=sha(data),fixture_only=True,guest_memory_writes=False,physical_audio_requested=False,
             physical_display_visible=False,renders=runs)
    path=folder/"report.json"
    path.write_text(json.dumps(rec,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS",sha(path.read_bytes()))
