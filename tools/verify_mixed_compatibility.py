"""Verify the legacy cable profile against retail ARM, the WSC policy and final readback."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from verify_mode23_scene_component import empty

BASE = 0x08000000
CONFIG = 0x03002310
SELECT = 0x03004738
USA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
WSC = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
V94 = 'EF8BBC67DB243A8CCAFA25744EFB371CC097C323F45D25060419B33B577B75BA'


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def word(data, at):
    return struct.unpack_from('<I', data, at)[0]


def instruction_contract(usa, source, prior, final, meta):
    assert sha(usa) == USA and sha(source) == WSC and sha(prior) == V94
    assert len(final) == len(prior) == 0x1000000 and len(usa) == 0x400000
    assert meta['input_sha256'] == V94 and meta['output_sha256'] == sha(final)
    assert meta['prior_owner_sha256'] == 'CD910DA852DF621FED7362EFB1C7D83CF8F62DEC6AC6B58F2669ED3A4D60B8A0'
    assert meta['source_sha256'] == WSC
    # Original WSC selects 0..10, then 13/14 only in normal mode, and one or two unlock bits.
    assert sha(source[0x7787DB:0x778847]) == '9BABC5510A2FADE32E501D968E337747C7BCD67168D79453132DC1556187D263'
    assert source[0x742ACD:0x742ADD] == bytes.fromhex('3d0800754b26f6067300017426807d11')
    assert usa[0x3546FC:0x354704] == bytes.fromhex('0b0058e30c00001a')
    assert usa[0xB5AB8:0xB5AE8] == final[0xB5AB8:0xB5AE8]
    assert usa[0xB5A30:0xB5A37] == final[0xB5A30:0xB5A37] == bytes((0,1,2,6,5,3,4))
    assert final[0x37A98C:0x37AAEC] == usa[0x37A98C:0x37AAEC]
    assert final[0x151AC:0x15278] == usa[0x151AC:0x15278]
    assert usa[0x81E5C:0x81E68] == bytes.fromhex('013983e30f3083e308002de9')
    # Reachable base and evolved assets and actions for both actual battle engines.
    for evolved, count in ((False,12),(True,11)):
        usa_table, port_table = (0xD42B8,0x60B000) if evolved else (0xD3FB8,0x4A80F8)
        assert usa[usa_table:usa_table+32*count] == final[port_table:port_table+32*count]
    for row in range(14):
        size = (12 if row < 8 else 11)*4
        old, new = 0x35515C+row*48,0x629000+row*60
        assert usa[old:old+size] == final[new:new+size]
    for i in range(12):
        raw = word(usa,0x3534D8+i*4)-BASE
        assert word(final,0x485000+i*4) == BASE+raw
        assert usa[raw:raw+120] == final[raw:raw+120]

    allocation, = meta['allocations']
    lo, hi = allocation['start'], allocation['end']
    assert 0x400000 <= lo < hi <= len(final) and prior[lo:hi] == b'\xff'*(hi-lo)
    assert all(hi<=a or lo>=b for a,b in meta['prior_excluded_extents'])
    sites = {0x8170C,0x81D04,0x81FF4,0x83238,0x354700,0x81E60}
    spans = {(i,4) for i in sites} | {(lo,hi-lo)}
    assert sorted(spans) == sorted((r['offset'],r['size']) for r in meta['writes'])
    clone = bytearray(final)
    for row in meta['writes']:
        a=row['offset']
        end=a+row['size']
        assert sha(prior[a:end]) == row['before_sha256'] and sha(final[a:end]) == row['after_sha256']
        clone[a:end]=prior[a:end]
    assert clone == prior
    for site in sites:
        insn=word(final,site)
        assert insn>>24 == 0xea
        signed=((insn&0xffffff)^0x800000)-0x800000
        assert lo <= site+8+signed*4 < hi


def exercise(rom, usa):
    m = empty(rom)
    regs = m.r[:15]
    retail = empty(usa)
    def init(machine, unlock, version, connection, flags=0):
        machine.r[:15] = regs
        machine.cpsr = 31 | flags<<28
        machine.put(CONFIG+0x19,unlock,1)
        machine.put(CONFIG+0x1A,connection,2)
        machine.put(CONFIG+0x25,version,1)
        machine.put(regs[13],SELECT)
        machine.writes.clear()
    # Every retail save bit combination runs through the unmodified producer.
    for unlock in range(32):
        init(retail,unlock,0,1)
        retail.run(0x080816B4,{0x0808171C})
        ids = list(range(7))+[i for i in range(7,12) if unlock & 1<<(i-7)]
        assert retail.get(SELECT+8,2) == len(ids)-1
        assert [retail.get(0x03004710+2*i,2) for i in range(len(ids))] == ids

    cases=lookups=0
    for unlock in (0,0x0f,0x10,0x20,0x30,0x7f,0xff):
        for connection,version in ((0,0),(0,1),(0x180,0xff),(1,0),(0x81,2),(1,1),(0x81,0xff)):
            mixed = bool(connection&1 and version&1)
            ids=list(range(11))
            if not mixed:
                ids.extend((13,14))
            if unlock & 16:
                ids.append(11)
            if not mixed and unlock & 32:
                ids.append(12)
            init(m,unlock,version,connection)
            m.put(0x03004728,0x02010360)
            m.run(0x080816B4,{0x0808171C})
            assert m.get(SELECT+8,2) == len(ids)-1 and m.get(0x03004728)==0x02010360
            assert m.r[4]==SELECT and m.r[13]==regs[13]+4 and m.r[14]==regs[14]
            for hook, dst, end in ((0x81D04,4,0x81D10),(0x81FF4,4,0x82000),(0x83238,8,0x83240)):
                for index, ident in enumerate(ids):
                    init(m,unlock,version,connection,index%16)
                    m.r[1] = index*(2 if dst==8 else 1)
                    original=m.r[:15]
                    m.run(BASE+hook,{BASE+hook+4})
                    original[dst]=m.r[dst]
                    assert m.r[:15]==original and m.cpsr==31 | (index%16)<<28
                    if dst==8:
                        # Frozen CPU model supports immediate halfwords; execute register-indexed LDRH arithmetically.
                        assert word(rom,hook+4)==0xE19810B1
                        resolved=m.get(m.r[8]+m.r[1],2)
                    else:
                        m.run(BASE+hook+4,{BASE+end})
                        resolved=m.r[1]
                    assert resolved==ident
                    lookups+=1
            for flagbits in range(16):
                init(m,unlock,version,connection,flagbits)
                m.r[3]=0x4030
                before=m.r[:15]
                m.run(0x08081E60,{0x08081E64})
                before[3] |= 0x0f if mixed else 0x4f
                assert m.r[:15]==before and m.cpsr==31 | flagbits<<28
            for actor_id in range(16):
                init(m,unlock,version,connection)
                m.r[5]=0x02010018
                m.put(m.r[5]+0x11,actor_id,1)
                m.run(0x083546F8,{0x08354700})
                state,flags=m.r[:15],m.cpsr
                stop=m.run(0x08354700,{0x08354704,0x08354738})
                assert m.r[15]==(0x08354704 if mixed and actor_id==11 else 0x08354738)
                assert m.r[:15]==state and m.cpsr==flags
            cases+=1
    return dict(retail_unlock_profiles=32,port_profiles=cases,active_character_lookups=lookups,
                handshake_inputs=cases*16,calumon_inputs=cases*16)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('prior','image','owner','gba','source','report'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    usa, source, prior, final, raw = (f.read_bytes() for f in (a.gba,a.source,a.prior,a.image,a.owner))
    instruction_contract(usa,source,prior,final,json.loads(raw))
    report=dict(result='PASS',prior=sha(prior),image=sha(final),owner=sha(raw),usa=sha(usa),wsc15=sha(source),
                whole_image_inverse=True,usa_stage_ids=[0,1,2,6,5,3,4],**exercise(final,usa))
    with a.report.open('x',encoding='utf8',newline='\n') as out:
        out.write(json.dumps(report,indent=2)+'\n')
    print('PASS',sha(a.report.read_bytes()))

if __name__=='__main__':
    main()

