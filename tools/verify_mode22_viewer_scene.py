"""Exercise native mode 22 and the installed storage reader against a block device."""
import argparse
import hashlib
import json
import struct
import zlib
from pathlib import Path

from verify_mode23_scene_component import CONFIG, POOL, allocate_native, empty, fill, flush_oam, memory

BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BASELINE = 'D390CA3B9620A2A9F3DAC214F2EC9DD3C8D0D8A91787BA78735AB8AC2E11749F'
RESULT = '63D7B68138CF7C1EBD96CEE168E1AFCD414A7591EDD9FBD8329A7E64C96F6248'
OWNER = '3500FD488577E1F849B1A063CA8098FF1B70ED06893993156AE29DEDE2136195'
READ, WRITE, SENTINEL = 0x0837DB60, 0x0837DB54, 0x0B000000


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def invoke(m, address, record=b'', fault=None):
    stack = m.r[13]
    m.r[14] = SENTINEL
    ops = []
    while True:
        address = m.run(address, {SENTINEL, READ, WRITE}, max_steps=350000)
        if address == SENTINEL:
            break
        assert address == READ
        block, dst = m.r[:2]
        assert 27 <= block <= 33 and stack-0x180 <= dst < stack
        ops.append(block)
        if block != fault:
            start = (block-27)*8
            fill(m, dst, record[start:start+8])
        for reg in (1,2,3,12):
            m.r[reg] = 0xEEAA1000+reg
        m.r[0] = 0x8000 if block == fault else 0
        address = m.r[14]
    assert m.r[13] == stack
    return ops


def record(snapshot, kind):
    payload = bytes(snapshot)+bytes(2)
    valid = b'BS15TAG\x01'+payload+struct.pack('<I', zlib.crc32(payload))
    if kind == 'erased':
        return bytes([255])*56
    if kind == 'bad CRC':
        return valid[:-1]+bytes([valid[-1]^1])
    return valid


def map_entry(word):
    return ((word & 511) | ((word >> 13 & 1) << 9) | ((word >> 14 & 3) << 10) |
            ((word >> 9 & 15) << 12))


def maps(source, snapshot, branch, highest):
    result = bytearray(0x1000)
    bank, code = 0x2D9360, 0x7848F0
    def copy(offset, destination, width, rows=1):
        for y in range(rows):
            for x in range(width):
                word = struct.unpack_from('<H', source, bank+offset+2*(width*y+x))[0]
                struct.pack_into('<H', result,destination+64*y+2*x,map_entry(word))
    def fg(offset,x,y,w,h):
        copy(offset,0x800+64*y+2*x,w,h)
    copy(0x5B78,0,32,18)
    if branch == 4:
        copy(0x5AF8,0,32)
        copy(0x5B38,0x440,32)
        fg(0x3A20,9,4,10,6)
        fg(0x6198,0,12,28,2)
    else:
        copy(0x5AB8,0,32)
        copy(0x5AB8,0x440,32)
        if branch == 2:
            fg(0x3DD8,10,6,8,6)
            raw = struct.unpack_from('<H',source,code+0x3EB+2*highest)[0]
            fg(raw,10,8,8,2)
            for i in reversed(range(10)):
                if snapshot[18+2*i]:
                    raw,width,x,y=struct.unpack_from('<4H',source,code+0x36F+i*8)
                    fg(raw,x,y,width,4)
        else:
            labels={1:b'YOU HAVE NO TAGS',8:b'TAG READ ERROR',16:b'INVALID TAG DATA'}
            for i, char in enumerate(labels[branch]):
                struct.pack_into('<H',result,0xA0C+2*i,0x8000+char-31)
    return result


def obj_checks(m,source,snapshot,branch):
    objects=[]
    if branch == 4:
        for i,letter in enumerate(snapshot[14:18]):
            if letter == 0:
                break
            objects.append((letter-31,100+8*i,62,8))
    if branch == 2:
        for i in reversed(range(10)):
            count=struct.unpack_from('<H',snapshot,18+2*i)[0]
            if count:
                y,x=source[0x7848F0+0x5A5+2*i:0x7848F0+0x5A7+2*i]
                objects += [(count+1,x,y,15),(11,x-8,y,15)]
    assert m.get(0x030012CA,1)==len(objects)
    for i,(tile,x,y,bank) in enumerate(objects):
        words=struct.unpack('<4H',memory(m,0x03001428+8*i,8))
        assert words==(y+8,x+8,(bank<<12)|0x400|i,0)
        assert memory(m,0x02000000+32*i,32)==memory(m,0x06000000+tile*32,32)
    flush_oam(m,len(objects))
    return len(objects)


def lifecycle(rom,source,sym,kind,rank,branch,exit_key):
    snap=bytearray(42)
    snap[14:18]=b'AGU\x00'
    for i in range(rank+1):
        struct.pack_into('<H',snap,18+2*i,(i%9)+1)
    raw=record(snap,kind)
    m=empty(rom)
    assert allocate_native(m,0x080159B4,0xF0000000)==POOL
    m.put(0x0300133C,POOL)
    m.r[5]=CONFIG
    m.put(CONFIG,22,2)
    m.raw(0x04000006,160,2)
    m.raw(0x04000200,0x10B,2)
    m.raw(0x04000202,0x0105,2)
    m.put(0x030012E0,0x0801F5EC)
    m.put(0x030012B6,0x6107,2)
    ops=invoke(m,0x080159B4,raw,30 if kind=='fault' else None)
    assert ops == list(range(27,31 if kind=='fault' else 34))
    rr,cc=POOL+0x118,POOL+0x230
    assert m.get(POOL)==0x08015AB4 and m.get(rr)==sym['m22_render'] and m.get(cc)==sym['m22_controller']
    assert m.get(cc+0x114)==rr and m.get(rr+0x18+26,1)==branch
    assert m.get(0x030012B6,2)==0x6107 and m.get(0x030012E0)==sym['m22_line_irq']
    assert m.get(0x03001338,2)==3 and memory(m,0x0600F000,0x1000)==maps(source,snap,branch,rank)
    assert m.get(0x030012BB,1)==(252 if branch in (1,8,16) else 0)
    assert m.get(0x04000008,2)==0x1F02 and m.get(0x0400000A,2)==0x1E03
    assert m.get(0x04000200,2) == 0x10B and m.get(0x04000202,2)==0x101
    m.put(0x0300133C,rr)
    full_cycle=(kind=='valid' and rank==9)
    frames=76 if full_cycle else 1
    for frame in range(1,frames+1):
        m.raw(0x04000006,160,2)
        invoke(m,sym['m22_render'])
        assert m.get(0x030012B8,1)==-frame%256
        assert m.get(0x04000200,2)==0x10F and m.get(0x04000004,2)>>8==16
        m.raw(0x04000006,16,2)
        invoke(m,sym['m22_line_irq'])
        assert m.get(0x04000004,2)>>8==144 and m.get(0x04000014,2)&255==248
        m.raw(0x04000006,144,2)
        invoke(m,sym['m22_line_irq'])
        assert m.get(0x04000014,2)&255==(frame-8)%256
        if full_cycle and frame%19==0:
            phase=(frame//19)%4
            for i in range(4):
                green=0x01E0
                assert struct.unpack('<3H',memory(m,0x05000002+i*6,6)) == ((0,green,green) if i==phase else (green,green,0))
    assert m.audio == [('start',122)]
    m.put(0x0300133C,cc)
    m.put(0x0300130A,1,2)
    invoke(m,sym['m22_controller'])
    objects=obj_checks(m,source,snap,branch)
    assert m.get(CONFIG+4,2)==0
    m.put(0x0300130A,exit_key,2)
    invoke(m,sym['m22_controller'])
    assert m.get(0x03001338,2)==1 and m.get(0x030012E0)==0x0801F5EC
    assert m.get(0x04000200,2)==0x10B and not m.get(0x04000004,2)&0x20
    assert [m.get(CONFIG+i,2) for i in (4,6,8)]==[1,0,0]
    m.put(0x0300133C,POOL)
    invoke(m,0x08015AB4)
    assert m.get(CONFIG,2)==20 and m.get(POOL)==0x080159B4
    return dict(storage=kind,highest_input=rank,branch=branch,eeprom_reads=len(ops),frames=frames,objects=objects,exit_key=exit_key)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for flag in ('before','after','source','owner','report'):
        parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args()
    assert not a.report.exists()
    before,rom,source,owner=[p.read_bytes() for p in (a.before,a.after,a.source,a.owner)]
    assert [sha(x) for x in (before,rom,source,owner)]==[BASELINE,RESULT,SOURCE,OWNER]
    meta=json.loads(owner)
    inverse=bytearray(rom)
    for row in meta['writes']:
        at,n=row['offset'],row['size']
        assert sha(rom[at:at+n])==row['after_sha256'] and sha(before[at:at+n])==row['before_sha256']
        inverse[at:at+n]=before[at:at+n]
    assert inverse==before and meta['new_global_RAM_bytes']==0
    new=meta['song_table']-BASE
    assert rom[new:new+122*8]==before[0xD9D940:0xD9D940+122*8]
    assert struct.unpack_from('<I',rom,new+122*8)[0]==meta['audio_address']+3180
    matrix=[('erased',-1,1),('valid',-1,1)]+[('valid',i,2) for i in range(10)]+[('valid',10,4),('fault',9,8),('bad CRC',10,16)]
    cases=[lifecycle(rom,source,meta['symbols'],kind,rank,branch,(0x40,0x80)[i%2]) for i,(kind,rank,branch) in enumerate(matrix)]
    report=dict(status='MODE22_INSTALLED_VIEWER_CPU_PASS',image_sha256=RESULT,cases=cases,
                full_tilemap_bytes_per_case=4096,mode22_to_mode20_cases=len(cases),physical_block_device='fixture',
                native_audio_request=122,native_audio_start_calls_per_case=1,
                checker_sha256=sha(Path(__file__).read_bytes()))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(report['status'],len(cases),sha(a.report.read_bytes()))


if __name__=='__main__':
    main()

