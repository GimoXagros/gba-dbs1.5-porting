"""Read the actual mixed-link captures and cross-check both physical saves and both cable lanes."""
import argparse
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

from run_mixed_link import RETAIL
from verify_link_tag_capture import EXE,POINTS

ROW=re.compile(r'^(\d+) pc=([0-9A-F]+) role=(\d+) side=(\d+) score=(\d+):(\d+) cfg=([0-9A-F]+) out=(\S+) in=(\S+) (\S+)',re.M)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_capture(d,expected,retail,kind):
    meta=json.loads((d/'launch.json').read_bytes())
    assert meta['scenario']==kind and meta['exe_sha256']==EXE and meta['script_sha256']==sha(d/'probe.lua')
    assert meta['guest_writes']==[] and meta['visible'] is False
    assert not re.search(r'emu:(?:write|loadState|setRegister)',(d/'probe.lua').read_text())
    traces=[]
    for c in meta['cartridges']:
        n=c['core']
        assert c['profile']==('retail' if n==retail else 'port') and c['status']=='PASS'
        assert c['sha256']==c['loaded_sha256']==sha(d/f'loaded-{n}.bin')==(RETAIL if n==retail else expected)
        assert c['bytes']==(0x400000 if n==retail else 0x1000000)
        assert c['save']==f'player{n}.sav' and c['save_out']==sha(d/c['save'])
        traces.append((d/f'trace-{n}.txt').read_text())
    return meta['cartridges'],traces


def save(path):
    raw=path.read_bytes()
    assert len(raw)==512
    data=b''.join(raw[i:i+8][::-1] for i in range(0,512,8))
    assert data.startswith(b'DIMPS Ver0.72') and sum(data[:192])==int.from_bytes(data[192:196],'little')
    return data


def matches(d,expected,retail,previous):
    carts,traces=load_capture(d,expected,retail,'match')
    rows=[]
    peer_scores=None
    observed_sides=set()
    winners=set()
    for c,t in zip(carts,traces):
        n=c['core']
        initial=previous.get(n)
        if initial is None:assert c['initial_save']=='erased (no file)'
        else:assert c['initial_save']==sha(initial)
        before=(0,0) if initial is None else struct.unpack_from('<HH',save(initial),142)
        assert re.search(r'retail root=1' if n==retail else r'port tree=1 row=1',t)
        assert 'two results returned' in t and 'mode=24 ' not in t
        steps=re.findall(r'^\d+ mode=(\d+) cfg=',t,re.M)
        canon=[m for i,m in enumerate(steps) if i==0 or steps[i-1]!=m]
        assert ['3','4','5','6','7'] in [canon[j:j+5] for j in range(len(canon)-4)] and canon[-2:]==['8','4']
        points=ROW.findall(t)
        assert len(points)%8==0 and points
        rounds=[];scores=[]
        for i in range(0,len(points),8):
            group=points[i:i+8]
            assert [int(x[1],16) for x in group]==POINTS
            frames=[int(x[0]) for x in group];assert frames==sorted(frames)
            _,_,role,side,s1,s2,*_=group[4]
            role,side,s1,s2=map(int,(role,side,s1,s2))
            assert (role,side) in ((8,0),(0,1))
            payload=f"0082/{s1+(s2<<8):04X}/{s1+s2:04X}/1CD9"
            assert group[4][-3:]==(payload,payload,payload)
            scores.append((s1,s2));observed_sides.add(side)
            if s1!=s2 and (s1>s2)==(side==0):winners.add(n)
            rounds.append(dict(scores=[s1,s2],role=role,side=side,accepted=frames[4],dispatched=frames[-1]))
        assert peer_scores is None or peer_scores==scores
        peer_scores=scores
        p=d/c['save'];data=save(p)
        wins,played=struct.unpack_from('<HH',data,142)
        assert played==before[1]+len(rounds)
        assert wins==before[0]+sum(s!=t and (s>t)==(side==0) for s,t in scores)
        if n==retail:assert data[200:]==bytes([255])*312
        else:
            tag=data[216:272]
            assert tag[:8]==b'BS15TAG\1' and tag[8:52]==bytes(44) and int.from_bytes(tag[52:56],'little')==zlib.crc32(tag[8:52])
        if initial is not None:assert data[200:]==save(initial)[200:]
        previous[n]=p
        rows.append(dict(core=n,profile=c['profile'],loaded=c['loaded_sha256'],rounds=rounds,
                         result_save=c['save_out'],stats_before=before,stats_after=[wins,played],trace=sha(d/f'trace-{n}.txt')))
    assert observed_sides=={0,1}
    return rows,winners


def placement(runs,cold,boundary,wrong,expected,retail,extra):
    previous={}
    rows=[];winners=set()
    for d in runs:
        checked,won=matches(d,expected,retail,previous)
        winners.update(won);rows.append(checked)
    assert winners=={1,2}
    carts,logs=load_capture(cold,expected,retail,'cold')
    for c,t in zip(carts,logs):
        n=c['core'];donor=previous[n]
        assert sha(donor)==c['initial_save']==c['save_out']
        assert save(donor)[:196]==(cold/f'cold-native-{n}.bin').read_bytes()
        assert 'retail root=0' in t if n==retail else 'port tree=0 row=0' in t
    carts,logs=load_capture(boundary,expected,retail,'boundary')
    rosters=[]
    common=None
    for c,t in zip(carts,logs):
        n=c['core'];shows={}
        for idx,fighter,limit in re.findall(r'selector index=(\d+) id=(\d+) max=(\d+)',t):
            assert int(idx)<=int(limit)
            shows[int(idx)]=int(fighter)
        count=7 if n==retail else (12 if extra else 11)
        assert shows==dict(enumerate(range(count)))
        observed=re.search(r'common fighters (\d+)/(\d+)',t)
        assert observed
        pair=list(map(int,observed.groups()))
        assert sorted(pair)==sorted([6,11 if extra else 10])
        assert common is None or pair==common
        common=pair;rosters.append(list(shows[i] for i in sorted(shows)))
        assert (boundary/f'p{n}-boundary-arena.png').is_file()
    _,logs=load_capture(wrong,expected,retail,'wrong')
    assert any('4F0F/0F4F' in t or '0F4F/4F0F' in t for t in logs)
    for n,t in enumerate(logs,1):
        before,after=t.split('ordinary cancel returned, retry legacy')
        assert ('offer op=0F' if n==retail else 'offer op=4F') in before
        assert 'cancel mismatched version' in before and 'mode=7 ' not in before and 'mode=5 ' not in before
        assert 'recovered with normal link retry' in after and 'mode=7 ' in after
        if n!=retail:assert 'offer op=0F' in after
        assert (wrong/f'p{n}-cancelled-title.png').is_file()
    return dict(retail_core=retail,matches=rows,observed_winning_cores=sorted(winners),cold=str(cold),
                verified_cold_prefix_bytes=196,selectable_ids=rosters,confirmed_live_pair=common,
                cancelled_wrong_version_then_reconnected=True,wrong_capture=str(wrong),boundary_capture=str(boundary))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for i in (1,2):
        p.add_argument('--matches'+str(i),required=True,nargs='+',type=Path)
        for k in ('cold','boundary','wrong'):p.add_argument('--'+k+str(i),required=True,type=Path)
    p.add_argument('--contact',required=True,type=Path)
    p.add_argument('--locales',required=True,nargs=4,type=Path)
    p.add_argument('--expected',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    rows=[placement(getattr(a,'matches'+str(i)),getattr(a,'cold'+str(i)),getattr(a,'boundary'+str(i)),
                    getattr(a,'wrong'+str(i)),a.expected,i,i==2) for i in (1,2)]
    carts,logs=load_capture(a.contact,a.expected,1,'contact')
    assert carts[1]['initial_save']=='9ED07A84BA49A9B08D7066D11CF6FF177E1103EB8E8034FE17B07CE1CC70EF20'
    for t in logs:
        assert re.search('hit attack=[A-F0-9]+ target=[A-F0-9]+ flags=0001/0002',t)
        assert 'native hit and ordinary nonzero score' in t
    languages=[]
    for language,folder in enumerate(a.locales):
        c,t=load_capture(folder,a.expected,1,'locale')
        probe=t[1]
        for returned,filename in ((0,'legacy-version'),(1,'returned-version')):
            assert f'version locale={160+language:02X} row=1 returned={returned}' in probe
            assert (folder/f'p2-{filename}.png').is_file()
        assert 'cancel before fighter confirm' in probe and (folder/'p2-actual-select.png').is_file()
        assert c[1]['initial_save']==c[1]['save_out']
        languages.append(dict(language=language,port_save=c[1]['save_out'],capture=str(folder)))
    result=dict(status='MIXED_LINK_PASS',retail_sha256=RETAIL,final_sha256=a.expected,placements=rows,
                assists_enabled_in_port_contact=True,language_menu_selection_return=languages,
                tool_sha256=sha(Path(__file__)))
    with a.output.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print(result['status'],sha(a.output))


if __name__=='__main__':main()
