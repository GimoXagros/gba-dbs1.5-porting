"""Install Tamer Tag card and score-reel cues in the live native M4A bank."""
import argparse
import json
from pathlib import Path
import struct

from analyze_mode23_looped_music import initial_state, pcm_data, split_track, stable_loop
from analyze_wsc_evolution_music import BANK, WSC_SHA, extract, parse, sha
from build_character_select_name_scene import Allocator, BASE, exclude
from build_mode23_audio_assets import LOADERS, WAITS, compact_track, music_track, noise_pcm, sample_blob
from build_wsc_evolution_music import compile_channel, pitch_divisor

CUES = ((0xD4,0x7B,1,4), (0x104,0x7C,4,0), (0x108,0x7D,4,0), (0x100,0x7E,4,0), (0xB6,0x7F,1,3))
OLD_COUNT = 0x7B
OLD_SHA = "2D7D12CC1C335FAF0414202DF24E7439069144CFD88230CE38CB3443A6A18ECE"
VOICES = (1,8,9,10,14,"noise0")
EXTERNAL = {1:0xD33398, 9:0xD33400, 10:0xD33434, 14:0xD3349C, "noise0":0xD334D0}


def descriptor(source, index):
    if index != 0x10B:
        return extract(source,index)
    # Last of 268 descriptors, so there is no next descriptor to delimit it.
    state,channel,offset=struct.unpack_from("<3H",source,BANK+index*6)
    assert (state,channel,offset)==(294,3,0xEA98)
    raw=BANK+offset
    block=source[raw:raw+6]
    assert block==bytes.fromhex("00000000ffff") and source[raw+6:raw+16]==b"\xff"*10
    return block,dict(id=index,state_offset=state,hardware_channel=channel,raw=raw,size=len(block),sha256=sha(block))


def compiled_tracks(source):
    ids={voice:i for i,voice in enumerate(VOICES)}
    tracks={}
    for base,_,count,_ in CUES:
        group=[]
        for index in range(base,base+count):
            data,info=descriptor(source,index)
            if (base==0x100 and index!=0x103) or base==0xB6:
                first,repeat,_,_=split_track(data)
                proof=stable_loop(first,repeat,initial_state(data),info["hardware_channel"],data[0])
                repeats=3 if base==0xB6 else 5
                assert proof["nonsteady_loop_count"] in (0,1) and proof["steady_loop_count"]==repeats
                stream,details=music_track(source,dict(payload=data,info=info,first=first,repeat=repeat,proof=proof,quiet=False),1,repeats,ids)
                assert (details["intro_updates"],details["repeat_updates"])==((5,16) if base==0xB6 else (1330,4096))
            else:
                score=parse(data)
                assert score["finite"] and not score["silent_infinite_rest"]
                full,details=compile_channel(source,info|score,ids)
                stream=b"\xbc\x00\xbb\x5f"+compact_track(full)+b"\xb1"
                details=dict(updates=score["driver_updates"],notes=sum(n["midi_note"] is not None for n in score["notes"]),
                             max_pitch_error_cents=details["max_pitch_error_cents"])
            group.append((stream,dict(source_id=index,source_raw=info["raw"],source_bytes=len(data),source_sha256=sha(data),**{k:v for k,v in details.items() if k!="source_id"})))
        tracks[base]=group
    return tracks


def build(before,source,raw_owner,input_hash,owner_hash,presentation_owner=None):
    owner=json.loads(raw_owner)
    assert sha(before)==owner["output_sha256"]==input_hash and sha(raw_owner)==owner_hash and sha(source)==WSC_SHA
    old_table=struct.unpack_from("<I",before,LOADERS[0])[0]-BASE
    previous=before[old_table:old_table+8*OLD_COUNT]
    assert sha(previous)==OLD_SHA and all(struct.unpack_from("<I",before,at)[0]==BASE+old_table for at in LOADERS)
    assert before[0x37DE44:0x37DE44+len(WAITS)]==bytes(WAITS)
    assert all(source[x:x+12]==bytes.fromhex("6a006a0168d4009ab8011987") for x in (0x7740DF,0x77443E))
    for address,index in ((0x774177,0x104),(0x7741A0,0x108),(0x7744DC,0x100),(0x774505,0x108)):
        assert source[address:address+20]==bytes.fromhex("c74402")+struct.pack("<H",index)+bytes.fromhex("c7440e0400c744060000814c100001")
    assert source[0x775340:0x775348]==bytes.fromhex("68b6009ab8011987")
    assert source[0x7753c3:0x7753ca]==bytes.fromhex("6a069ab8011987")
    assert descriptor(source,0x06)[1]["state_offset"]==descriptor(source,0xB6)[1]["state_offset"]==252
    extents=owner["prior_excluded_extents"]+[[r["start"],r["end"]] for r in owner["allocations"]]
    alloc=Allocator(before)
    exclude(alloc,extents)
    image=bytearray(before)
    writes=[]
    def reserve(n,label):
        at=alloc.allocate(n,label,4)
        assert all(at+n<=a or b<=at for a,b in extents) and before[at:at+n]==b"\xff"*n
        return at
    def write(at,data,label):
        old=before[at:at+len(data)]
        assert image[at:at+len(data)]==old
        image[at:at+len(data)]=data
        writes.append(dict(offset=at,size=len(data),purpose=label,before_sha256=sha(old),after_sha256=sha(data)))
    tracks=compiled_tracks(source)
    placements={}
    # Protect the longest steady-loop tracks first on a fragmented cartridge.
    for code,info in sorted((entry for row in tracks.values() for entry in row),key=lambda v:-len(v[0])):
        label=f'result cue {info["source_id"]:03X} track'
        at=reserve(len(code),label)
        if "loop_offset" in info:
            assert code[-5:]==b"\xb2"+bytes(4)
            code=code[:-4]+struct.pack("<I",BASE+at+info["loop_offset"])
        write(at,code,label)
        placements[info["source_id"]]=dict(offset=at,size=len(code),**info)
    hz=round(3072000*4*1024/pitch_divisor(source,0))
    voice_bytes=bytearray()
    sample_rows=[]
    for v in VOICES:
        pcm=noise_pcm(0)[0] if v=="noise0" else pcm_data(source,v)
        sample=sample_blob(pcm,0,hz)
        if v in EXTERNAL:
            at=EXTERNAL[v]
            assert before[at:at+len(sample)]==sample
        else:
            at=reserve(len(sample),"result source waveform 08")
            write(at,sample,"result source waveform 08")
        voice_bytes+=bytes((0,60,0,0))+struct.pack("<I",BASE+at)+bytes((255,0,255,0))
        sample_rows.append(dict(voice=v,at=at,size=len(sample),sha256=sha(sample)))
    voice=reserve(len(voice_bytes),"result cue voicegroup")
    write(voice,voice_bytes,"result cue voicegroup")
    rows=bytearray(previous)
    songs=[]
    for src,dst,count,player in CUES:
        addresses=[placements[src+i]["offset"] for i in range(count)]
        assert dst==len(rows)//8 and before[0x37FBB4+12*player+8]>=count
        header=bytes((count,0,40 if count==1 else 0,128))+struct.pack("<I",BASE+voice)+b"".join(struct.pack("<I",BASE+at) for at in addresses)
        at=reserve(len(header),f"result song {dst:02X}")
        write(at,header,f"result song {dst:02X}")
        rows+=struct.pack("<IHH",BASE+at,player,player)
        songs.append(dict(source=src,native=dst,priority=count,delay=0,player=player,header_raw=at,tracks=[placements[src+i] for i in range(count)]))
    table=reserve(len(rows),"native song table 00-7F")
    write(table,rows,"native song table 00-7F")
    for at in LOADERS:write(at,struct.pack("<I",BASE+table),"native song table reader")
    gate=None
    if presentation_owner is not None:
        assert sha(presentation_owner)=="876C1468C10DCDD66520D65E673D4D0C1ABDC3F3DF27B6E9C0BFFF7F7F5A91A9"
        presentation=json.loads(presentation_owner)
        helper=presentation["symbols"]["m11_tag_audio"]-BASE
        gate=presentation["symbols"]["m11_tag_audio_ready"]-BASE
        assert (helper,gate)==(0xEA4ED4,0xEA4F10)
        assert before[helper:gate+4]==bytes.fromhex("ff5f2de934209fe5002092e5010052e30800001a7b0050e30600003a7e0050e30400008a0080a0e10190a0e100a0a0e300b0a0e3140300ebff9fbde800000000")
        assert any(a<=helper and gate+4<=b for a,b in extents)
        assert all(struct.unpack_from("<I",image,at)[0]==BASE+table for at in LOADERS)
        assert len(rows)//8==128 and all(struct.unpack_from("<I",image,table+8*r["native"])[0]==BASE+r["header_raw"] for r in songs)
        write(gate,struct.pack("<I",1),"enable installed native ending result cues")
    output=bytes(image)
    return output,dict(input_sha256=input_hash,prior_owner_sha256=owner_hash,source_sha256=WSC_SHA,output_sha256=sha(output),
                       prior_excluded_extents=extents,allocations=alloc.allocations,storage_exports=owner["storage_exports"],
                       writes=writes,sounds=songs,samples=sample_rows,voicegroup=voice,table=table,song_count=len(rows)//8,
                       old_table=old_table,old_rows_sha256=OLD_SHA,ending_gate=gate,builder_sha256=sha(Path(__file__).read_bytes()))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("input","source","owner","output"):
        parser.add_argument("--"+name,required=True,type=Path)
    for name in ("input-sha256","owner-sha256"):
        parser.add_argument("--"+name,required=True)
    parser.add_argument("--presentation-owner",type=Path)
    a=parser.parse_args()
    image,meta=build(a.input.read_bytes(),a.source.read_bytes(),a.owner.read_bytes(),a.input_sha256,a.owner_sha256,a.presentation_owner.read_bytes() if a.presentation_owner else None)
    a.output.mkdir(parents=True,exist_ok=False)
    (a.output/"component.gba").write_bytes(image)
    result=a.output/"manifest.json"
    result.write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(sha(image),sha(result.read_bytes()))
