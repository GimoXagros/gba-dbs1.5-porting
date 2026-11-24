"""Check installed code, every valid persistent assist choice and the prior EEPROM owners."""

import argparse
import json
import struct
from pathlib import Path

from build_ending_awards_main_tail import verify_writes
from verify_mode23_completion_save import Machine, dump, fill, sha

BASE=0x08000000
READ,WRITE=0x0837db60,0x0837db54
SOURCE="D432DBE9B221A0EFC15B644B8E76A0D39D374DFF1087165A917EF977A3E8BD99"
FINAL="C95C8B85C5FCC882E2BD14E8BB5A453F606D6C8560B4D8311D0AFD37489DF7A3"
OWNER="5413E876EFEB74F9B2CD4F798AD6E2A9D5380B98386D8370119A4788ED505055"


def prior_census(data):
    sites={READ:[],WRITE:[]}
    for i,(word,) in enumerate(struct.iter_unpack("<I",data)):
        if word&0x0e000000==0x0a000000:
            dest=BASE+4*i+8+4*((word&0x7fffff)-(word&0x800000))
            if dest in sites:
                sites[dest].append(i*4)
    assert sites=={WRITE:[0x1fc7c,0x629844,0x62986c],READ:[0x1fcc0,0x629828,0x629850]}
    for api,expected in ((WRITE,[0xd8d2dc,0xfb6300]),(READ,[0xd8d2e4,0xeeaae0,0xfb6308])):
        refs=[]
        at=0
        while (at:=data.find(struct.pack("<I",api),at))>=0:
            refs.append(at)
            at+=1
        assert refs==expected


def device_call(rom,symbol,value,device,failure=False):
    vm=Machine(rom,seed=3,flags=31)
    vm.r[0]=value
    initial=vm.r[:]
    pc=symbol
    seen=[]
    while True:
        pc=vm.run(pc,{initial[14],READ,WRITE})
        if pc==initial[14]:break
        block,pointer=vm.r[:2]
        assert block==34 and pointer%4==0 and not seen
        seen.append(pc)
        if not failure:
            if pc==READ:fill(vm,pointer,device[272:280])
            else:device[272:280]=dump(vm,pointer,8)
        vm.r[0]=0x8000 if failure else 0
        for i in (1,2,3,12):vm.r[i]=0x300+i
        pc=vm.r[14]
    assert initial[1:15]==vm.r[1:15]
    return vm.r[0],seen


def check(prior,rom,owner):
    assert (sha(prior),sha(rom),sha(owner))==(SOURCE,FINAL,OWNER)
    meta=json.loads(owner)
    prior_census(prior)
    get,put=(meta["symbols"][s] for s in ("assist_read","assist_write"))
    assert (get,put)==(0x08dcc204,0x08dcc274)
    original=bytes((i*19+17)&255 for i in range(512))
    base=bytearray(original)
    for boss in (0,1024):
        for value in range(1001):
            packed=value|boss
            assert device_call(rom,put,packed,base)==(0,[WRITE])
            assert base[:272]==original[:272] and base[280:]==original[280:]
            assert base[272:280]==struct.pack("<4sHH",b"BAS1",packed,packed^65535)
            assert device_call(rom,get,0,base)==(packed,[READ])
    good=bytes(base)
    for bit in range(64):
        damaged=bytearray(good)
        damaged[272+bit//8]^=1<<(bit%8)
        assert device_call(rom,get,0,damaged)==(0,[READ])
    for value in (*range(1001,1024),*range(2025,2049),65535,0xffffffff):
        assert device_call(rom,put,value,base)[1]==[] and base==good
        if value<=65535:
            invalid=bytearray(good)
            invalid[272:280]=struct.pack("<4sHH",b"BAS1",value,value^65535)
            assert device_call(rom,get,0,invalid)==(0,[READ])
    for byte in (0,255):
        blank=bytearray([byte])*512
        assert device_call(rom,get,0,blank)==(0,[READ]) and blank==bytes([byte])*512
    assert device_call(rom,put,1,base,True)==(0x8000,[WRITE]) and base==good
    assert device_call(rom,get,1,base,True)==(0,[READ]) and base==good
    bounds=[]
    for resource in meta["assets"]:
        frames=resource["frames"]
        parts=[f[4] for f in frames]
        max_value=max(parts[6], 3*max(parts[9:19]))
        worst=sum(parts[1:6])+max(parts[8],parts[19])+parts[20]+max(parts[6:8])+max_value
        assert worst<128 and max(f[1] for f in frames)<=100
        bounds.append(worst)
    return dict(status="PASS",rom_sha256=FINAL,owner_sha256=OWNER,whole_image_inverse=True,
                valid_settings=2002,both_legacy_fill_values=True,single_bit_faults=64,
                bad_record_and_io_fail_closed=True,read_only_open_cancel=True,
                max_submenu_sprite_parts=bounds,previous_eeprom_blocks=[0,33],new_eeprom_block=34,
                limits="The block interface simulates faults. Physical controller and cold saves are separate.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("prior","image","owner","report"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    verify_writes(a.prior,a.image,a.owner)
    report=check(*(f.read_bytes() for f in (a.prior,a.image,a.owner)))
    report["checker_sha256"]=sha(Path(__file__).read_bytes())
    with a.report.open("x",encoding="utf8",newline="\n") as f:
        f.write(json.dumps(report,indent=2)+"\n")
    print("PASS",sha(a.report.read_bytes()))


if __name__=="__main__":main()
