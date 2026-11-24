"""Validate result/name/cold boot evidence from the hidden native ROM playback."""
import argparse
import json
import struct
import zlib
from pathlib import Path

from verify_mode11_rank_capture import check_run
from verify_mode23_completion_save import sha

STATE='001DF714CC4EE525DBFB566D7F1BDDFCFDC4894EF4303D3EA9C8A8163746936A'
SOURCE='DB6DB2E7F3E1FF1E4E3AA6F155871CCA44476C8400AA0DD62041BB337A97BB4A'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source-run','run','rom','report'):p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    rom=a.rom.read_bytes()
    digest=sha(rom)
    d=a.run/'award'
    c=a.run/'cold'
    award=check_run(d,'award',digest)
    cold=check_run(c,'cold',digest)
    assert award['donor_sha256']==STATE
    packed=(d/'data/104/probe.SaveRAM').read_bytes()
    assert sha(packed)==cold['donor_sha256'] and (c/'data/104/probe.SaveRAM').read_bytes()==packed
    assert packed[512:]==b'\xff'*(len(packed)-512)
    tail=b''.join(packed[x:x+8][::-1] for x in range(216,272,8))
    assert tail[:8]==b'BS15TAG\1' and struct.unpack_from('<I',tail,52)[0]==zlib.crc32(tail[8:52])
    assert tail[22:26]==b'BCD\0' and struct.unpack_from('<11H',tail,26)==(0,)*10+(1,)
    src=json.loads((a.source_run/'launch.json').read_bytes())
    assert src['donor_state']==SOURCE and src['guest_writes']==[] and src['outcome']=='complete'
    stages=(a.source_run/'trace.txt').read_text().splitlines()
    assert any(x.startswith('103350 ') and '73d3-1562' in x for x in stages)
    assert any(x.startswith('104061 ') and '73d3-0378' in x for x in stages)
    assert any(x.startswith('104461 mode=20') for x in stages)
    def task(folder,scene,callback):
        buf=(folder/(scene+'-EWRAM.bin')).read_bytes()
        active=[i for i in range(0x10000,0x10000+52*0x118,0x118)
                if buf[i+16]&2 and struct.unpack_from('<I',buf,i)[0]==callback]
        assert len(active)==1
        return buf[active[0]+24:active[0]+0x118]
    pictures={}
    for scene,phase,age in (('score-fade-in',0,30),('score',0,390),('score-fade-out',0,690),
                            ('card',1,140),('fighter-arrival',1,420),('celebration',2,100),
                            ('editor',3,25)):
        buf=task(d,scene,0x08ea4810)
        assert struct.unpack_from('<3H',buf)==(age,phase,0x800a)
        assert buf[40:45]==b'2310\0'
        pictures[scene]=sha((d/(scene+'.png')).read_bytes())
    iw=(d/'score-IWRAM.bin').read_bytes()
    assert iw[0x231f]==2 and struct.unpack_from('<H',iw,0x3d02)[0]==2310
    assert (d/'card-PALRAM.bin').read_bytes()[:2]==bytes(2)
    assert (d/'card-IWRAM.bin').read_bytes()[0x12b7]==0
    assert task(d,'name-confirmation',0x08ea4810)[8:12]==b'BCD('
    assert task(d,'edited',0x08ea4810)[8:12]==b'BCD\0'
    t=task(c,'cold-special',0x08f7a71c)
    assert t[:4]==b'BCD\0' and t[24:27]==b'\x01\x00\x04'
    tr=(d/'trace.txt').read_text().splitlines()
    assert [x.split(' ',1)[1] for x in tr if 'award score=' in x]==['award score=2310 difficulty=2 result=800A count=1']
    assert [x.split(' ',1)[1] for x in tr if 'card-cue ' in x]==['card-cue 7B priority=1','card-cue 7E priority=4']
    assert tr[-1].endswith('successful-title-return')
    assert [x.split(' ',1)[1] for x in tr if 'name ' in x and 'key=A' in x]==[
        'name 0 byte=66 key=A','name 1 byte=67 key=A','name 2 byte=68 key=A','name 3 byte=40 key=A']
    audio=[x.split(' ',1)[1] for x in tr if 'native-audio ' in x]
    assert audio.count('native-audio 1E priority=1 delay=0')==6
    assert audio.count('native-audio 1F priority=1 delay=0')==3
    assert audio.count('native-audio 21 priority=2 delay=0')==1
    enabled=struct.unpack_from('<I',rom,0xea4f10)[0]
    assert enabled in (0,1)
    for s in ('native-audio 7B priority=1 delay=0','native-audio 7E priority=4 delay=0'):
        assert (s in audio)==bool(enabled)
    assert (c/'trace.txt').read_text().splitlines()[-1].endswith('viewer exit mode=20')
    pictures.update({k:sha((d/(k+'.png')).read_bytes()) for k in ('name-confirmation','edited','returned-title')})
    pictures['cold-special']=sha((c/'cold-special.png').read_bytes())
    pictures['cold-exit']=sha((c/'cold-exit.png').read_bytes())
    report=dict(status='MODE11_EARNED_PRESENTATION_AND_COLD_BCD_PASS',rom_sha256=digest,
                checker_sha256=sha(Path(__file__).read_bytes()),source_ordinary_probe=sha((a.source_run/'launch.json').read_bytes()),
                source_scene_frames={'score':710,'ordinary_card':399},native_checkpoint=STATE,
                award_launch=sha((d/'launch.json').read_bytes()),cold_launch=sha((c/'launch.json').read_bytes()),
                physical_eeprom_sha256=sha(packed),persisted_name='BCD',earned_count=1,
                scene_ids=[11,3,22,20],card_audio_enabled=bool(enabled),native_audio=audio,pictures=pictures,
                limitations='GBA stage-11 checkpoint continues a previously assisted campaign. Source captures show an ordinary rank; the native authentic played award is special. No save or emulator writes by these two probes.')
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()))


if __name__=='__main__':main()

