"""Drive clean native Options menus and reopen a physically written save in a fresh process."""

import argparse
import json
import os
import shutil
import struct
import time
from pathlib import Path

from build_character_select_name_scene import sha
from mgba_headless_gdb_capture import PrivateDesktopProcess

ROOT=Path(__file__).resolve().parents[1]


def session(out,rom,language,fixed,boss,donor=None):
    assert os.path.samefile("W:/",ROOT)
    out.mkdir(parents=True,exist_ok=False)
    alias="W:/"+out.relative_to(ROOT).as_posix()
    exe=ROOT/"local/BizHawk-2.11.1/EmuHawk.exe"
    assert sha(exe.read_bytes())=="F8CDB93551A544F680BF3876D9D8D72643859E7A44A23B04E1A25B92E48F80CD"
    config=json.loads((ROOT/"build/bizhawk-gba-diagnostic-20261026/config.json").read_text(encoding="utf-8-sig"))
    for i,item in enumerate(config["PathEntries"]["Paths"]):
        item["Path"]=alias+"/data/"+str(i)
        Path(item["Path"]).mkdir(parents=True)
    config.update(AcceptBackgroundInput=False,AutoLoadLastSaveSlot=False,AutosaveSaveRAM=False,
                  SoundEnabled=False,SoundOutputMethod=3)
    (out/"config.json").write_text(json.dumps(config),encoding="utf-8")
    save=out/"data/104/probe.SaveRAM"
    if donor:shutil.copyfile(donor,save)
    shutil.copyfile(rom,out/"probe.gba")
    args=["--gdi","--config="+alias+"/config.json","--lua=W:/tools/bizhawk_probe_battle_assist.lua",
          f"--userdata=output:{alias};language:{language};cold:{int(donor is not None)};fixed:{fixed};boss:{boss}",alias+"/probe.gba"]
    with PrivateDesktopProcess(exe,args,exe.parent) as process:
        deadline=time.monotonic()+150
        while time.monotonic()<deadline and not (out/"done.txt").is_file():time.sleep(.25)
        result=(out/"done.txt").read_text() if (out/"done.txt").exists() else "timeout"
        if result=="PASS" and not donor:
            deadline=time.monotonic()+12
            while time.monotonic()<deadline and not save.exists():time.sleep(.2)
    loaded=(out/"loaded-rom.bin").read_bytes()
    assert loaded==rom.read_bytes() and result=="PASS",(out,result)
    packed=save.read_bytes()
    value=fixed+1+1024*boss
    assert packed[272:280][::-1]==struct.pack("<4sHH",b"BAS1",value,value^65535),packed[272:280].hex()
    record=dict(status=result,rom_sha256=sha(loaded),save_sha256=sha(packed),guest_writes=[],
                ordinary_controls=True,visible=False,language=language,cold=donor is not None,fixed=fixed,boss_hp_one=bool(boss),
                trace_sha256=sha((out/"trace.txt").read_bytes()))
    (out/"report.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf8",newline="\n")
    print(out,record,flush=True)
    return save


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--language",type=int,choices=range(4),required=True)
    p.add_argument("--fixed",type=int,choices=(0,999),default=999)
    p.add_argument("--boss",type=int,choices=(0,1),default=1)
    a=p.parse_args();out=a.output.resolve()
    save=session(out/"clean",a.image,a.language,a.fixed,a.boss)
    session(out/"cold",a.image,a.language,a.fixed,a.boss,save)
