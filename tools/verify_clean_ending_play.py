"""Verify cold start, campaign coverage, both physical attacks and the authorized assist journal."""
import argparse,json,re,struct,zlib
from pathlib import Path
from run_clean_ending_play import sha

def check(folder,rom):
    manifest=json.loads((folder/'launch.json').read_bytes())
    assert manifest['outcome']=='PASS' and manifest['loaded_rom_exact'] and not manifest['visible']
    assert manifest['script_sha256']==sha(Path(__file__).with_name('bizhawk_clean_ending_play.lua'))
    assert manifest['rom_sha256']==sha(rom)==sha(folder/'loaded-rom.bin')
    assert not manifest['initial_save_files'] and not manifest['state_loads'] and not manifest['supplied_save_used']
    for file,value in manifest['files'].items(): assert sha(folder/file)==value
    lines=(folder/'play.txt').read_text().splitlines()
    modes=[tuple(map(int,m.groups())) for line in lines if (m:=re.fullmatch(r'(\d+) mode=(\d+) stage=(\d+) level=(\d+)',line))]
    assert modes[0][0]<4 and modes[0][1]==0 and modes[-1][1]==3 and all(m!=9 for _,m,_,_ in modes)
    battles=[s for _,m,s,d in modes if m==7 and d==2]
    assert len(battles)==len(set(battles))==12 and set(battles)==set(range(12)) and battles[-2:]==[7,11]
    assert [mode for _,mode,_,_ in modes][-6:]==[8,12,13,11,20,3]
    assert all((folder/f'stage-{s}.png').is_file() for s in battles)
    hits=[int(line.split()[-1]) for line in lines if 'player attack defeated boss ' in line]
    assert hits==[7,11] and any('shoot-last-exit' in line for line in lines) and any(' ending' in line for line in lines)
    scores=0;bosses=[]
    for line in (folder/'assist-ledger.txt').read_text().splitlines():
        row=dict(token.split('=',1) for token in line.split())
        assert row['bytes']=='2' and int(row['P1HP'])>0 and row['verified']=='true'
        pos=int(row['address'],16);s=int(row['stage'])
        if row['kind']=='score':
            scores+=1
            assert s not in (7,11) and pos==int(row['FIRST'],16)+0x66 and row['after']==row['requested']=='999'
        else:
            assert row['kind']=='boss' and pos==int(row['SECOND'],16)+0x64 and row['after']==row['requested']=='1'
            bosses.append(s)
    assert scores and bosses==[7,11]
    save=folder/'data/104/probe.SaveRAM'
    packed=save.read_bytes()
    assert len(packed)>=512 and all(b==255 for b in packed[512:])
    logical=b''.join(packed[i:i+8][::-1] for i in range(0,272,8))
    assert sum(logical[:192])==struct.unpack_from('<I',logical,192)[0]
    assert logical[216:224]==b'BS15TAG\x01' and zlib.crc32(logical[224:268])==struct.unpack_from('<I',logical,268)[0]
    assert logical[238:242]==b'AAA\x00' and struct.unpack_from('<11H',logical,242)==(0,)*10+(1,)
    return dict(rom_sha256=sha(rom),start=modes[0][0],finish=modes[-1][0],stage_ids=battles,
                normal_score_assists=scores,boss_hit_stages=hits,save_sha256=sha(save),
                cold_start=True,state_loads=0,continues=0,visible=False,tag='MASTER',name='AAA')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('run','rom','output'): p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();report=check(a.run,a.rom)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS',report)
