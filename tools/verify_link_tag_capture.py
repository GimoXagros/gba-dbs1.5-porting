"""Check two local cables, both result ABIs and both physical EEPROM records."""
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

EXE='0D9A2779ADD78D41A093C3AF8CEC7D72CC07A5451C8A1E1B167B48CD54950288'
ROW=re.compile(r'pc=([0-9A-F]+) f=(\d+) role=(\d+) side=(\d+) score=(\d+):(\d+) cfg=([0-9A-F]+) ver=(\d+) out=(\S+) in=(\S+) (\S+)')
POINTS=[0x083404E0,0x0837AB1C,0x0837AB34,0x0837AB50,0x0837AB8C,0x0837AB90,0x08015B18,0x08015B28]


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def eeprom(path):
    physical=path.read_bytes()
    assert len(physical)==512
    logical=b''.join(physical[i:i+8][::-1] for i in range(0,512,8))
    assert struct.unpack_from('<I',logical,0xc0)[0]==sum(logical[:0xc0])
    s=logical[216:272]
    assert s[:8]==b'BS15TAG\1' and s[20]==0 and s[50:52]==bytes(2)
    assert struct.unpack_from('<I',s,52)[0]==zlib.crc32(s[8:52])
    return logical,bytearray(s[8:50])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--capture',required=True,type=Path)
    p.add_argument('--rom-sha256',required=True)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args();cap=a.capture
    launch=json.loads((cap/'launch.json').read_text())
    assert launch['host_sha256']==EXE==sha((cap/'mGBA.exe').read_bytes())
    assert launch['rom_sha256']==a.rom_sha256 and launch['finished']==[True,True]
    assert launch['visible'] is False and launch['physical_input'] is False and launch['guest_writes']==[]
    script=(cap/'probe.lua').read_text(encoding='utf-8')
    assert not re.search(r'emu:(?:write|loadState|reset|setRegister)',script)
    players=[]
    for n in (1,2):
        assert sha((cap/f'player{n}.gba').read_bytes())==a.rom_sha256
        log=(cap/f'p{n}.txt').read_text()
        matches=ROW.findall(log)
        assert len(matches)%len(POINTS)==0 and matches
        rounds=[matches[i:i+len(POINTS)] for i in range(0,len(matches),len(POINTS))]
        for earlier in rounds[:-1]:
            assert [int(r[0],16) for r in earlier]==POINTS
            assert earlier[4][4]==earlier[4][5] and int(earlier[-1][6],16)&0x1000
        matches=rounds[-1]
        assert [int(r[0],16) for r in matches]==POINTS
        assert not int(matches[-1][6],16)&0x1000
        ordered=[int(m[1]) for m in matches]
        assert ordered==sorted(ordered)
        assert 'tree=0 row=1' in log and 'tree=1 row=0' in log
        mode=[int(v) for v in re.findall(r'^f=\d+ mode=(\d+)',log,re.M)]
        steps=[v for j,v in enumerate(mode) if not j or mode[j-1]!=v]
        assert all(v in steps for v in (3,4,5,6,7,8)) and [7,8,4] in [steps[j:j+3] for j in range(len(steps)-2)]
        row=matches[4]
        role,side,first,second,ver=map(int,(row[2],row[3],row[4],row[5],row[7]))
        assert (role,side) in ((8,0),(0,1))
        slots=[tuple(int(h,16) for h in lane.split('/')) for lane in row[9:11]]
        assert all(s[:3]==(0x82,first+(second<<8),first+second) for s in slots)
        assert slots[side]==tuple(int(h,16) for h in row[8].split('/'))
        before,old=eeprom(cap/f'initial-{n}.bin')
        after,new=eeprom(cap/f'player{n}.sav')
        assert before[200:216]==after[200:216] and before[272:]==after[272:]
        players.append(dict(player=n,role=role,side=side,score=(first,second),version=ver,slots=slots,old=old,new=new,
                            rematches=len(rounds)-1,accept_frame=ordered[4],dispatch_frame=ordered[7],native_stat_bytes_changed=[i for i in range(192) if before[i]!=after[i]],
                            trace_sha256=sha((cap/f'p{n}.txt').read_bytes()),final_save_sha256=sha((cap/f'player{n}.sav').read_bytes())))
    first,second=players
    assert {first['side'],second['side']}=={0,1} and first['slots']==second['slots'] and first['score']==second['score']
    assert first['version']==second['version']
    legacy=bool(first['version']&1)
    if 'version' in launch:
        assert legacy==(launch['version']=='legacy')
        assert launch['script_sha256'] in (sha(Path(__file__).with_name('mgba_probe_link_tag_result.lua').read_bytes()),'30B421E762AD14E8C3EDA140BD938FCA98A0EB4A307B5388834AC1466394198E')
    def ranks(data):
        return list(struct.unpack_from('<11H',data,18))
    sent=[0,0]
    for peer in players:
        sent[peer['side']]=max((i for i,v in enumerate(ranks(peer['old'])) if v),default=65535)
    output=[]
    for peer in players:
        side=peer['side'];old=peer.pop('old');new=peer.pop('new')
        expected=old.copy()
        if legacy:
            assert all(s[3]==0x1CD9 for s in peer['slots'])
        else:
            assert [s[3] for s in peer['slots']]==sent
            scores=peer['score'];winner=scores[side]>scores[1-side];loser=scores[side]<scores[1-side]
            if winner:
                idx=sent[1-side]
                assert idx<10 and ranks(old)[idx]<9
                struct.pack_into('<H',expected,18+2*idx,ranks(old)[idx]+1)
            elif loser:
                idx=sent[side]
                assert idx<10
                struct.pack_into('<H',expected,18+2*idx,ranks(old)[idx]-1)
            streak=struct.unpack_from('<H',old,40)[0]
            struct.pack_into('<H',expected,40,min(999,(streak+1)&65535) if winner else 0)
        assert new==expected
        peer.update(name=bytes(new[14:18]).rstrip(bytes(1)).decode('ascii'),ranks_before=ranks(old),ranks_after=ranks(new),
                    streak_before=struct.unpack_from('<H',old,40)[0],streak_after=struct.unpack_from('<H',new,40)[0])
        output.append(peer)
    report=dict(status='TWO_NATIVE_CARTRIDGES_LINK_RESULT_PASS',rom_sha256=a.rom_sha256,emulator=EXE,legacy=legacy,
                fixture='Separate legal pre-match 512-byte cartridge saves; live CPU memory read-only.',players=output,
                checker_sha256=sha(Path(__file__).read_bytes()))
    with a.report.open('x',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(report,indent=2)+'\n')
    print(report['status'],sha(a.report.read_bytes()),first['score'],[i['streak_after'] for i in output])


if __name__=='__main__':
    main()
