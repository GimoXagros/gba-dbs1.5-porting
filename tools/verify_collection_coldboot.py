"""Compare the exact completion EEPROM copy with the cold game RAM and unlocked menu."""
import argparse
import json
import struct
from pathlib import Path
from verify_collection_route_capture import sha

def verify(final,cold):
    old=json.loads((final/"launch.json").read_bytes())
    new=json.loads((cold/"launch.json").read_bytes())
    assert old["outcome"]=="collection-seven-round-win-returned" and new["outcome"]=="cold-collection-loaded"
    assert new["loaded_rom_exact"] and new["script_unchanged"] and not new["visible"]
    assert old["rom_sha256"]==new["rom_sha256"]=="8C6D6CC077013FEEEC60F70D702750268E81044C1A1DF6DBB6E70FF4A51BC869"
    for folder,record in ((final,old),(cold,new)):
        for name,digest in record["files"].items():
            assert sha(folder/name)==digest,name
    save_rel="data/104/probe.SaveRAM"
    assert sha(final/save_rel)==new["copied_genuine_completion_save"]==sha(cold/save_rel)
    raw=(final/save_rel).read_bytes()
    logical=b"".join(raw[i:i+8][::-1] for i in range(0,27*8,8))
    iw=(cold/"cold-iwram.bin").read_bytes()
    final_iw=(final/"collection-return-IWRAM.bin").read_bytes()
    assert logical[:196]==iw[0x1120:0x11E4]==final_iw[0x1120:0x11E4]
    assert sum(logical[:192])==struct.unpack_from("<I",logical,192)[0]
    assert logical[208:216]==bytes.fromhex("425331354d323301")
    assert logical[18:20]==bytes(2) and final_iw[0x2328:0x232A]==bytes([16,0]) and iw[0x2328:0x232A]==bytes(2)
    e=(cold/"cold-ewram.bin").read_bytes()
    h,=[h for h in range(0x10000,0x10000+52*0x118,0x118) if struct.unpack_from("<H",e,h+16)[0]&2 and struct.unpack_from("<I",e,h)[0]==0x08DFE048]
    assert e[h+28]==2 and struct.unpack_from("<I",e,h+52)[0]==1
    assert struct.unpack_from("<H",iw,0x2AD6)[0]==9
    start,end=map(int,(cold/"frames.txt").read_text().split())
    assert start<5 and end>start
    return dict(status="PASS",original_save=sha(final/save_rel),cold_launch=sha(cold/"launch.json"),cold_start=start,cold_menu=end,
                menu_eligibility=True,source_record_and_checksum_bytes=196,source_checksummed_bytes=192,
                pending_before_reset=16,permanent_before_reset=0,pending_after_reset=0,permanent_after_reset=0)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("final","cold","report"):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    result=verify(args.final,args.cold)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS",sha(args.report))
