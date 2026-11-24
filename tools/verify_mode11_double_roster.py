"""Audit the real no-continue campaign, paired ending, fixed animations, and cold selection."""
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

OLD = "78447E05AE135C71B7A1C3AA3C4D606EF6ACF984412FB30B5650730D16494924"
FIX = "543F19927D5A21FA80C7EF70D50F571768E8F9C67F75847A13BAAFEEEA7ADA23"
SOURCE = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate(path, outcome, digest):
    record=json.loads((path/"launch.json").read_bytes())
    assert record["outcome"]==outcome and record["rom_sha256"]==sha(path/"loaded-rom.bin")==digest
    assert record["loaded_rom_exact"] and not record["visible"] and not record["supplied_save_used"]
    for name,expected in record["files"].items():
        assert sha(path/name)==expected, name
    return record


def check(a):
    opening=validate(a.opening,"failure",OLD)
    battle=validate(a.battle,"failure",OLD)
    stalled=validate(a.stalled,"failure",OLD)
    fixed=validate(a.fixed,"permanent-award-title",FIX)
    cold=validate(a.cold,"both-portraits-loaded",FIX)
    assert fixed["guest_writes"] == cold["guest_writes"] == []
    assert sha(a.opening/"campaign-stage-11.State")==sha(a.battle/"campaign.State")
    assert sha(a.battle/"permanent-award.State")==sha(a.stalled/"campaign.State")==sha(a.fixed/"campaign.State")
    early=(a.opening/"rank-start.txt").read_text()
    assert all(s in early for s in ["102458 initial earned SPECIAL 10","102533 returned both roster flags zero","103024 new campaign, no roster flags"])
    stages=re.findall(r"^\d+ mode=7 stage=\d+ flags=0 progression=(\d+)$",(a.opening/"promotion-trace.txt").read_text(),re.M)
    assert tuple(map(int,stages))==tuple(range(11))+(10,)
    trace=(a.battle/"promotion-trace.txt").read_text()
    for signal in ("189229 real-P1-hit P2-before=1 after=0","189230 terminal-entry",
                   "190721 config-write address=03002328 prior=0010 value=0030","202220 selected-mask-commit pending=30 permanent=00 saved=00 R0=00003030",
                   "202220 after-permanent-commit pending=30 permanent=30 saved=00","202220 record-or pending=00 permanent=30 saved=00"):
        assert signal in trace
    slots=(a.battle/"rank-start.txt").read_text()
    assert re.findall(r"display portrait ID=(\d+) slot=(\d+)", slots)==[("11","0"),("12","1")]
    head=(a.battle/"two-portraits-IWRAM.bin").read_bytes()
    assert struct.unpack_from("<3H",head,0x3CF0)==(11,12,2)
    earned=[]
    for directory in (a.opening,a.battle):
        for line in (directory/"assist-ledger.txt").read_text().splitlines():
            item=dict(e.split("=",1) for e in line.split())
            if directory==a.opening and int(item["core"])>=187835:
                continue
            assert item["bytes"]=="2" and item["verified"]=="true"
            if item["kind"]=="score":
                assert item["requested"]=="999" and int(item["address"],16)==int(item["FIRST"],16)+0x66
            else:
                assert item["kind"]=="boss" and item["requested"]=="1" and int(item["address"],16)==int(item["SECOND"],16)+0x64
            earned.append(item)
    assert [int(e["stage"]) for e in earned if e["kind"]=="boss"]==[7,11]
    original=(a.battle/"loaded-rom.bin").read_bytes()
    final=(a.fixed/"loaded-rom.bin").read_bytes()
    owner=json.loads(a.manifest.read_bytes())
    assert owner["input_sha256"]==OLD and owner["output_sha256"]==FIX and sha(a.source)==SOURCE
    src=a.source.read_bytes()
    table=struct.unpack_from("<I",final,0xC0C60)[0]-0x08000000
    assert table==owner["table"] and original[0xC08DC:0xC08F0]==final[table:table+20]
    assert struct.unpack_from("<I",final,table+20)[0]==0x08000000+table+24
    offsets=struct.unpack_from("<6H",src,0x77ADEF)
    assert 0x779F50+offsets[5]==0x77AE1F
    assert src[0x77AE1F:0x77AE23]==final[table+24:table+28]==bytes.fromhex("6c00ffff")
    inverse=bytearray(final)
    for w in owner["writes"]:
        o,n=w["offset"],w["size"]
        inverse[o:o+n]=original[o:o+n]
    assert inverse==original
    err=(a.stalled/"rank-start.txt").read_text()
    assert "name-entry observation exhausted" in err and "pc=080C0D28" not in err
    old=(a.stalled/"ending-1000-EWRAM.bin").read_bytes()
    anim=[h for i in range(52) if (h:=0x10000+i*280) and old[h+16]&2 and struct.unpack_from("<I",old,h)[0]==0x080C090C]
    assert len(anim)==1 and struct.unpack_from("<I",old,anim[0]+0x18+0x1c)[0]==0xFFFF005C
    events=(a.fixed/"rank-start.txt").read_text()
    assert all(e in events for e in ["202838 pc=080C0C70","202912 pc=080C0D28","202912 pc=080C0E04 R0=000000FF","m=20"])
    assert fixed["natural_process_exit"]
    save=a.fixed/"data/104/probe.SaveRAM"
    assert sha(save)==cold["copied_genuine_completion_save"]==sha(a.cold/"data/104/probe.SaveRAM")
    physical=save.read_bytes()
    logical=b"".join(physical[i:i+8][::-1] for i in range(0,272,8))
    assert logical[18:20]==bytes((48,0)) and sum(logical[:192])==struct.unpack_from("<I",logical,192)[0]
    assert logical[216:224]==b"BS15TAG\x01" and zlib.crc32(logical[224:268])==struct.unpack_from("<I",logical,268)[0]
    rank=struct.unpack_from("<H",logical,224+0x26)[0]
    assert rank==1
    display=(a.cold/"trace.txt").read_text()
    for ident,offset in [(11,0xA1080),(12,0xE60020)]:
        assert f"actual-portrait {ident}\n" in display
        iw=(a.cold/f"fighter-{ident}-IWRAM.bin").read_bytes()
        vram=(a.cold/f"fighter-{ident}-VRAM.bin").read_bytes()
        assert iw[0x2328:0x232a]==b"\0\x30" and iw[0x1120:0x11e4]==logical[:196]
        assert vram[0x5780:0x5a80]==final[offset:offset+768]
    return dict(status="PASS",source=SOURCE,before=OLD,after=FIX,stage_sequence=stages,live_slots=[[11,0],[12,1]],
                award_frame=202220,actual_last_hit=189229,actual_name_accept=202912,
                score_999_writes=sum(e["kind"]=="score" for e in earned),boss_hp_1_stages=[7,11],cold_save=sha(save),
                save_sum=sum(logical[:192]),physical_tag_special=rank,cold_fighters=[11,12],
                launch_sha256={n:sha(getattr(a,n)/"launch.json") for n in ("opening","battle","stalled","fixed","cold")},
                checker_sha256=sha(Path(__file__)))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("opening","battle","stalled","fixed","cold","source","manifest","report"):
        parser.add_argument("--"+name,type=Path,required=True)
    arg=parser.parse_args()
    result=check(arg)
    arg.report.parent.mkdir(parents=True,exist_ok=True)
    arg.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS",sha(arg.report))
