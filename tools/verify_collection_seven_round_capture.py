"""Check the continuous final-candidate seven-round Collection clear and title return."""
import argparse
import json
import re
import struct
from pathlib import Path
from verify_collection_route_capture import sha

FINAL = "8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869"

def verify(directory):
    launch = json.loads((directory / "launch.json").read_bytes())
    assert launch["completed"] and launch["outcome"] == "collection-seven-round-win-returned"
    assert all(launch[key] for key in ("loaded_rom_exact","scripts_unchanged","checkpoint_copies_unchanged","CPU_bank_equal","native_extensions_equal","managed_suffix_equal"))
    assert not launch["visible"] and not launch["physical_background_input"] and not launch["supplied_save_used"]
    assert sha(directory/"loaded-rom.bin") == launch["rom_sha256"] == FINAL
    assert sha(directory/"checkpoint/healthy-activation.State") == "1493C8CD9C1525562B7477BE564E2CB9CD5719B5B2B183421AAC7FB77BE14350"
    for name, digest in launch["files"].items():
        assert sha(directory/name) == digest, name
    writes=(directory/"wholeplay-stage11-writes.txt").read_text().splitlines()
    assert len(writes)==1 and "address=0201188C bytes=2 before=37 requested=1" in writes[0]
    assert "event=hit-post core=89483" in (directory/"wholeplay-trace.txt").read_text()
    trace=(directory/"collection-trace.txt").read_text().splitlines()
    frames=[int(s.split()[0]) for s in trace]
    assert frames==sorted(frames)
    milestones=[s.split(" ",1)[1] for s in trace if "round=" not in s]
    assert milestones==["eligible-clear-writer mode=8","mode=3","mode=4","mode=23","scene-create mode=23",
                        "scene-playing mode=23","final-round-cleared mode=23","completion-save mode=23","success-exit mode=23","mode=20","mode=3"]
    rounds=[int(m[1]) for s in trace if (m:=re.fullmatch(r"\d+ round=(\d+)",s))]
    assert rounds==list(range(7))
    shots=[]
    for r in rounds:
        turns=[int(m[1]) for s in trace if (m:=re.fullmatch(rf"\d+ round={r} turn=(\d+) aim=\d+ power=\d+",s))]
        assert turns==list(range(1,len(turns)+1)) and turns
        shots.append(len(turns))
    def snapshot(prefix,domain):
        return (directory/f"{prefix}-{domain}.bin").read_bytes()
    def tasks(data):
        return [h for h in range(0x10000,0x10000+52*0x118,0x118) if word(data,h+16)&2]
    def word(data,off):
        return struct.unpack_from("<H",data,off)[0]
    def dword(data,off):
        return struct.unpack_from("<I",data,off)[0]
    menu=snapshot("english-shoot-selected","IWRAM")
    e=snapshot("english-shoot-selected","EWRAM")
    title,=[h for h in tasks(e) if dword(e,h)==0x08DFE048]
    assert e[title+28:title+31]==bytes([2,1,2]) and dword(e,title+52)==1
    assert word(menu,0x2AC8+14)==9 and dword(menu,0x2AC8+0x48)==149530656
    before=snapshot("shoot-playing","IWRAM")
    out=snapshot("shoot-exit","IWRAM")
    returned=snapshot("collection-return","IWRAM")
    assert [word(d,0x2310)for d in (menu,before,out,returned)]==[3,23,20,3]
    e=snapshot("collection-return","EWRAM")
    assert any(dword(e,h)==0x08090C7C for h in tasks(e))
    assert all(not 0x08DB0404 <= dword(e,h) < 0x08DB5C04 for h in tasks(e))
    assert sum(out[0x1120:0x11E0])==dword(out,0x11E0)
    return dict(status="PASS",image=FINAL,launch=sha(directory/"launch.json"),all_indexed_files=len(launch["files"]),
                rounds_played=7,human_shots_by_round=shots,observations=milestones,first_core=89405,last_mode_change=frames[-1],
                pending_unlock_before=before[0x2328],pending_unlock_at_exit=out[0x2328],
                permanent_flag_at_exit=out[0x2329],source_record_checksum=dword(out,0x11E0),
                scope="One continuous checkpoint run from genuine campaign stage 11 through ordinary earned menu entry, seven rounds and title. Power-cycle persistence is separate.")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture",type=Path)
    parser.add_argument("report",type=Path)
    args=parser.parse_args()
    report=verify(args.capture)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf8",newline="\n")
    print("PASS",sha(args.report))
