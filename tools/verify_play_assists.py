"""Exercise the actual native option consumers for every fixed number and both boss forms."""
import argparse
import hashlib
import json
from pathlib import Path
from verify_mode23_scene_component import empty

TASK, PLAYER, OPPONENT, AUX = 0x02011EA0,0x02011710,0x02011828,0x02011940
CONFIG, HANDLE, KINDS = 0x03002310,0x03004514,0x03004502
INIT,TICK,NATIVE = 0x080d1c04,0x08373638,0x08373928


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def verify(prior,rom,owner_raw):
    meta=json.loads(owner_raw)
    assert sha(prior)==meta['input_sha256'] and sha(rom)==meta['output_sha256']
    inv=bytearray(rom)
    for row in meta['writes']:
        at=row['offset'];end=at+row['size']
        assert sha(rom[at:end])==row['after_sha256'] and sha(prior[at:end])==row['before_sha256']
        inv[at:end]=prior[at:end]
    assert inv==prior
    m=empty(rom)
    get,put=m.get,m.put
    def register(word):
        m.r[0],m.r[8]=TASK,HANDLE
        saved=m.r[:15];flags=m.cpsr
        m.run(INIT,{meta['assist_read']})
        m.r[0]=word
        m.run(m.r[14],{INIT+4})
        assert m.r[:15]==saved and m.cpsr==flags
        assert get(HANDLE)==TASK and get(TASK+0x114)==word
    def tick():
        saved=m.r[:14];flags=m.cpsr
        m.run(TICK,{NATIVE})
        assert m.r[:14]==saved and m.r[14]==TICK+4 and m.cpsr==flags
    put(CONFIG,7,2)
    put(CONFIG+0x1a,0x180,2)
    put(0x0300489c,PLAYER);put(0x030048a0,OPPONENT);put(0x03004d3c,AUX)
    for p,q,index in ((PLAYER,OPPONENT,0),(OPPONENT,PLAYER,1)):
        put(p+0x14,p);put(p+0x18,q);put(p+0x10,index,1)
    put(PLAYER+0x64,8,2);put(OPPONENT+0x64,37,2)
    put(OPPONENT+4,1,1);put(KINDS,0,2)
    for number in range(1000):
        register(number+1)
        put(PLAYER+0x66,654,2)
        tick();assert get(PLAYER+0x66,2)==number
        assert get(PLAYER+0x64,2)==8 and get(OPPONENT+0x64,2)==37
    for setting,mode,link in ((0,7,0),(1001,7,0),(1000,19,0),(1000,7,1)):
        register(setting);put(CONFIG,mode,2);put(CONFIG+0x1a,link,2)
        put(PLAYER+0x66,345,2);tick()
        assert get(PLAYER+0x66,2)==345
    put(CONFIG,7,2);put(CONFIG+0x1a,0,2)
    put(KINDS,2,2);put(OPPONENT+4,3,1);put(OPPONENT+0x11,15,1)
    put(OPPONENT+0x28,AUX);put(AUX+0x28,OPPONENT)
    for stage,kind in ((7,3),(11,6)):
        put(CONFIG+0xe,stage,1);put(AUX+4,kind,1)
        put(OPPONENT+0x64,37,2);register(1000);tick()
        assert get(OPPONENT+0x64,2)==37
        register(0x400);put(AUX+4,0,1);tick()
        assert get(OPPONENT+0x64,2)==37
        put(AUX+4,kind,1);put(OPPONENT+0x64,0,2);tick()
        assert get(OPPONENT+0x64,2)==0 and get(TASK+0x116,1)==0
        put(OPPONENT+0x64,37,2);tick();assert get(OPPONENT+0x64,2)==1
        for hp in (0,7,65535):
            put(OPPONENT+0x64,hp,2);tick();assert get(OPPONENT+0x64,2)==hp
        register(0x400);put(OPPONENT+0x64,23,2);tick()
        assert get(OPPONENT+0x64,2)==1 and get(TASK+0x116,1)==stage
        assert get(PLAYER+0x64,2)==8 and get(PLAYER+0x66,2)==345
    return dict(output_sha256=sha(rom),owner_sha256=sha(owner_raw),fixed_range=[0,999],
                disabled_preserves_score=True,link_unchanged=True,both_bosses_once_per_encounter=True,
                native_call_abi=True,whole_image_inverse=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('prior','image','owner','report'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args()
    result=verify(a.prior.read_bytes(),a.image.read_bytes(),a.owner.read_bytes())
    with a.report.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(result,indent=2)+'\n')
    print('PASS',sha(a.report.read_bytes()))
