"""Independently decode the installed result bank, source events, samples and native dispatch bounds."""
import argparse
import json
from pathlib import Path
import struct

from verify_mode23_audio_assets import (compare_notes, decode_native, pcm_noise, pcm_wave, raw_pitch, sha,
                                        source_events, source_tick)

BASE=0x08000000
READERS=(0x37C2A4,0x37C2D8,0x37C324,0x37C378,0x37C3AC)
ROWS=((0xD4,4,1),(0x104,0,4),(0x108,0,4),(0x100,0,4),(0xB6,3,1))
SOURCE="C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
OLD="2D7D12CC1C335FAF0414202DF24E7439069144CFD88230CE38CB3443A6A18ECE"


def pointer(data,at):
    return struct.unpack_from("<I",data,at)[0]-BASE


def original_score(src, sid, root):
    row=0x3F0000+sid*6
    lane,hardware,offset=struct.unpack_from("<3H",src,row)
    if sid in (0x103,0x107,0x10B):
        assert (lane,hardware)==(294,3 if sid!=0x103 else 2)
        assert src[0x3F0000+offset:0x3F0000+offset+6]==bytes.fromhex("00000000ffff")
        return [],0,None,0,False
    if sid==0xB6:
        assert (lane,hardware)==(252,2)
        assert src[0x3F0000+offset:0x3F0000+offset+18]==bytes.fromhex("01000c00a201c604fdf055041f01b0f0ffff")
        state=dict(level=12,wave=1,pan=255,sweep=0,kind=0,noise=0,envelope=(6,4),vibrato=254)
        notes=[]
        for tick in range(0,20,5):
            start,end=source_tick(1,tick),source_tick(1,tick+4)
            notes.append(dict(packed=0x55,tick=tick,start=start,end=end,voice="1",sweep=0,states=[(start,end,state)]))
        return notes,source_tick(1,20),source_tick(1,5),1,False
    return source_events(src,sid,0x79 if root==0x100 else 0)


def audit(source,previous,after,manifest):
    assert sha(source)==SOURCE and sha(previous)==manifest["input_sha256"] and sha(after)==manifest["output_sha256"]
    old=pointer(previous,READERS[0]);table=pointer(after,READERS[0])
    assert all(pointer(previous,r)==old and pointer(after,r)==table for r in READERS)
    assert after[table:table+8*123]==previous[old:old+8*123] and sha(previous[old:old+8*123])==OLD
    assert table==manifest["table"] and manifest["song_count"]==128
    inverse=bytearray(after);used=set()
    for action in manifest["writes"]:
        lo,n=action["offset"],action["size"]
        assert not used.intersection(range(lo,lo+n))
        used.update(range(lo,lo+n))
        assert sha(previous[lo:lo+n])==action["before_sha256"] and sha(after[lo:lo+n])==action["after_sha256"]
        inverse[lo:lo+n]=previous[lo:lo+n]
    assert inverse==previous
    wait=after[0x37DE44:0x37DE44+49]
    labels=["1","8","9","10","14","noise0"]
    hz=round(3072000*4*1024/raw_pitch(source,0))
    assert [s["native"] for s in manifest["sounds"]]==list(range(123,128))
    results=[]
    for i,(root,player,lanes) in enumerate(ROWS):
        native=0x7B+i
        header,p,q=struct.unpack_from("<IHH",after,table+8*native)
        assert p==q==player
        h=header-BASE
        assert after[h:h+4]==bytes((lanes,0,40 if lanes==1 else 0,128))
        voice=pointer(after,h+4)
        for index,label in enumerate(labels):
            at=voice+index*12
            assert after[at:at+4]==bytes((0,60,0,0)) and after[at+8:at+12]==bytes((255,0,255,0))
            raw=pointer(after,at+4)
            if label=="noise0":
                pcm,loop=pcm_noise(0)
            else:
                pcm,loop=pcm_wave(source,int(label))
            assert struct.unpack_from("<4I",after,raw)==(0x40000000,hz,loop,len(pcm))
            assert after[raw+16:raw+16+len(pcm)+1]==pcm+pcm[loop:loop+1]
        facts=[]
        for channel in range(lanes):
            sid=root+channel
            at=pointer(after,h+8+4*channel)
            extent=next(r for r in manifest["allocations"] if r["start"]==at)
            length=extent["size"]
            events,duration,marker,jump=decode_native(after[at:at+length],wait,BASE+at)
            expected,deadline,loop,speed,inherited=original_score(source,sid,root)
            assert (duration,marker,inherited)==(deadline,loop,False)
            error=compare_notes(source,expected,events,speed,labels,hz,True)
            if jump is not None:
                loop_events,loop_duration,_,_=decode_native(after[at:at+length],wait,BASE+at,first=jump)
                assert loop_duration==duration-marker and len(loop_events)==sum(n["start"]>=marker for n in events)
            facts.append(dict(source=sid,notes=len(events),updates=duration,loop_start=marker,
                              recurrence=None if marker is None else duration-marker,peak_pitch_error_cents=round(error,4)))
        results.append(dict(source=root,native=native,player=player,tracks=facts))
    # Literal at 0837C378 belongs to conditional m4aSongNumStop. It compares
    # the playing header with the song header before reaching MPlayStop.
    assert after[0x37c35e:0x37c36a]==previous[0x37c35e:0x37c36a]
    assert struct.unpack_from("<H",after,0x37c364)[0]==0x4281
    assert after[0xea4f10:0xea4f14]==bytes((1,0,0,0)) and previous[0xea4f10:0xea4f14]==bytes(4)
    return dict(status="PASS",source=SOURCE,parent=sha(previous),image=sha(after),song_table_raw=table,original_rows=123,
                new_rows=5,total_rows=128,native_table_readers=list(READERS),PCM_voices=labels,results=results,
                unchanged_whole_image_outside_declared_writes=True,checker_sha256=sha(Path(__file__).read_bytes()))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("source","parent","image","manifest","report"):p.add_argument("--"+arg,type=Path,required=True)
    a=p.parse_args()
    report=audit(a.source.read_bytes(),a.parent.read_bytes(),a.image.read_bytes(),json.loads(a.manifest.read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("PASS",sha(a.report.read_bytes()))
