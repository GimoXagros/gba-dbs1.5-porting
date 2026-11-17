"""Restore the four source fifteen-fighter type8 reaction table views."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
from verify_shoot_static_companion_clear import Machine
from verify_character_p1_completion import far, source_events
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
INPUT = '933C9434C78F8ED3AE77227AAE974FFCC2346232A532C4F317A2ECE31C9B6775'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
OLD = '58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
TABLES = (0xD3FD04, 0xD3FD40, 0xD3FD7C, 0xD3FE90)
SPANS = ((0xD3FD04, 0xD3FDB8), (0xD3FE90, 0xD3FECC))
SCANNER = '7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'
SPECS = (
    (0x36BE44, 0x762FD2, 0x763258, 0x36C12C, (0x36F7AC,)),
    (0x36BE74, 0x762FF0, 0x7632D8, 0x36C1AC, (0x36F7B0,)),
    (0x36BEA4, 0x76300E, 0x763358, 0x36C22C, (0x36F7B4,)),
    (0x36BED4, 0x76302C, 0x7633D8, 0x36C2AC, (0x36CAA8, 0x36F7B8)),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data): return hashlib.sha256(data).hexdigest().upper()
def u(data, at): return struct.unpack_from('<I', data, at)[0]
def h(data, at): return struct.unpack_from('<H', data, at)[0]


def contract(before, gba, old, source):
    need(tuple(map(sha, (before, gba, old, source))) == (INPUT, GBA, OLD, SOURCE), 'four immutable inputs')
    need(before[0x36C12C:0x36C32C] == gba[0x36C12C:0x36C32C], 'all native reaction record bytes retained')
    need(before[0x36EC68:0x36EC98] == gba[0x36EC68:0x36EC98], 'four actual native selectors retained')
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    def sequence(at, end, expected):
        found = [i.mnemonic + (' ' + i.op_str if i.op_str else '') for i in decoder.disasm(source[at:end], at)]
        need(found == expected, 'source instructions ' + hex(at))
    sequence(0x76060E, 0x760632, [
        'mov bx, 0x3002', 'test word ptr [di + 6], 1', 'je 0x76061b',
        'mov bx, 0x3020', 'test word ptr [di + 8], 0x4000', 'je 0x76062f',
        'mov bx, 0x303e', 'test word ptr [di + 6], 1', 'je 0x76062f',
        'mov bx, 0x305c', 'jmp 0x760c05'])
    sequence(0x760C05, 0x760C23, [
        'xor ax, ax', 'mov al, byte ptr [di + 0x11]', 'shl ax, 1', 'add bx, ax',
        'mov bx, word ptr cs:[bx]', 'xor ax, ax', 'mov al, byte ptr [bp - 2]',
        'shl ax, 5', 'add bx, ax', 'push si', 'mov si, di', 'add di, 0x96', 'push cs'])
    sequence(0x7622FE, 0x762312, [
        'mov bx, 0x305c', 'mov ax, 0x5ffd', 'mov es, ax', 'xor ax, ax',
        'mov al, byte ptr [di + 0x11]', 'shl ax, 1', 'add bx, ax', 'mov bx, word ptr es:[bx]'])
    rows = []
    for k, (native, src, record, native_record, aliases) in enumerate(SPECS):
        retained_count = 13 if k == 3 else 12
        need(struct.unpack_from('<15H', source, src) == (record - 0x75FFD0,) * 15, 'all fifteen source identities')
        need(h(source, src + 30) != record - 0x75FFD0, 'next source table boundary')
        old_table, old_record = 0x3A6DDA + k * 24, 0x3A6FCE + k * 128
        need(struct.unpack_from('<'+str(retained_count)+'H', old, old_table) == (old_record - 0x3A45B0,) * retained_count, 'original source population')
        need(struct.unpack_from('<'+str(retained_count)+'I', gba, native) == (BASE + native_record,) * retained_count, 'commercial population')
        need(u(gba,native+4*retained_count) != BASE+native_record, 'actual short table boundary')
        need(before[native:native + 4*retained_count] == gba[native:native + 4*retained_count], 'actual short table retained')
        for variant in range(4):
            a, b, c = old_record + variant * 32, record + variant * 32, native_record + variant * 32
            need(old[a:a + 4] == source[b:b + 4] == before[c:c + 4], 'same source/native flags and event')
            need(old[a + 8:a + 32] == source[b + 8:b + 32], 'source reaction metadata unchanged')
            need(struct.unpack_from('<2H', source, b + 4) == ((0xFE2 if k % 2 == 0 else 0x1146), 0x5FFD), 'source reaction callback')
            need(u(before, c + 4) == (0x0836A834 if k % 2 == 0 else 0x0836AAC0), 'paired native reaction callback')
        pattern = struct.pack('<I', BASE + native)
        actual, at = [], -1
        while True:
            at = before.find(pattern, at + 1)
            if at < 0: break
            actual.append(at)
        need(tuple(actual) == aliases, 'all aligned/unaligned native aliases')
        rows.append(dict(source_table=src, source_record=record, old_table=native, retained_identity_count=retained_count,
                         native_record=native_record, aliases=list(aliases), events=[h(source, record + 32*j + 2) for j in range(4)]))
    domains = []
    for evolved, group in ((0, 0x4A80F8), (1, 0x60B000)):
        for ident in range(15):
            sp1 = far(source, 0x740000 + (ident + 30*evolved)*32 + 6)
            events, _, _, _ = source_events(source, sp1)
            p1 = u(before, group + ident*32 + 4) - BASE
            table = u(before, p1) - BASE
            count = (u(before, table + 4) - BASE - table) // 16
            chosen = sorted(set(rows[2*evolved]['events'] + rows[2*evolved+1]['events']))
            for event in chosen:
                need(event < len(events) and event < count, 'reaction event belongs to actual source/native resource')
                n, cmd, aa, bb = struct.unpack_from('<4I', before, table + event*16)
                need(0 < n <= 255 and BASE <= cmd <= BASE + len(before) - n*16, 'bounded native reaction commands')
                need(BASE <= aa < BASE + len(before) and (bb == 0 or BASE <= bb < BASE + len(before)), 'bounded native reaction metadata')
            domains.append(dict(id=ident, evolved=bool(evolved), source_P1=sp1, source_count=len(events), native_P1=BASE+p1, native_count=count, selected_events=chosen))
    return dict(tables=rows, resource_domains=domains, source_windows=[dict(start=a,end=z,sha256=sha(source[a:z])) for a,z in
                ((0x76060E,0x760632),(0x760C05,0x760C30),(0x7622FE,0x762323),(0x762FD2,0x76304A),(0x763258,0x763458))])


def ownership(before, paths):
    expected = ('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
                '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
                '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD',
                '54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55')
    blobs = [p.read_bytes() for p in paths]
    need(tuple(map(sha, blobs[:4])) == expected, 'frozen prior owner manifests')
    owners = list(map(json.loads, blobs))
    need([0xD33000,0xD40000] in owners[0]['reservations'], 'existing enclosing reservation')
    need(owners[4]['output_sha256'] == INPUT and owners[4]['allocation']['suballocation'] == [0xD3FEE0,0xD40000], 'immediate campaign consumer owner')
    for k, owner in enumerate(owners):
        for write in owner['writes']:
            a, z = write['offset'], write['offset'] + write['size']
            need(not any(max(a,start) < min(z,end) for start,end in SPANS), 'all prior writes disjoint')
            if k == 0:
                if 0xD33000 <= a < 0xD40000: need(sha(before[a:z]) == write['after_sha256'], 'audio owner retained')
            else: need(before[a:z] == bytes.fromhex(write['after_hex']), 'component owner retained')
    need(all(before[a:z] == b'\xff'*(z-a) for a,z in SPANS), 'complete new suballocations blank')
    need(sha(Path(scanner.__file__).read_bytes()) == SCANNER, 'reference scanner pinned')
    scan = types.FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=SPANS), argdefs=scanner.inbound.__defaults__)
    hits = scan(before)
    need(not hits, 'no incoming encoded references')
    return dict(enclosing=[0xD33000,0xD40000],suballocations=SPANS,owner_sha256=list(map(sha,blobs)),inbound_hits=hits,new_RAM_bytes=0)


def route(rom, ident, evolved, air, variant, flags):
    machine = Machine(rom, seed=5, flags=(flags << 28) | 0x1F)
    machine.r[4], machine.r[5], machine.r[11] = 0x02011710, 0x02011828, 0
    machine.put(machine.r[5]+6, air, 2)
    machine.put(machine.r[5]+8, evolved*0x4000, 2)
    machine.put(machine.r[5]+0x11, ident, 1)
    machine.put(0x03004D26, variant, 1)
    need(machine.run(0x0836EC68, {0x083555D0}) == 0x083555D0, 'actual native selector reaches generic record reader')
    record = machine.r[1]
    need(machine.run(0x083555D0, {0x08012874}) == 0x08012874, 'actual generic reader reaches event setter')
    return record, machine.get(machine.r[13]), machine


def validate(before, after):
    cases = old_cases = 0
    for ident in range(15):
        for evolved in range(2):
            for air in range(2):
                for variant in range(4):
                    for flags in range(16):
                        record, event, m = route(after, ident, evolved, air, variant, flags)
                        expected = BASE + SPECS[2*evolved+air][3] + variant*32
                        need(record == expected and event == h(after, expected-BASE+2), 'source prescribed record and event through actual ARM')
                        cases += 1
                        if ident < 12 or (ident == 12 and evolved and air):
                            rec0, event0, old = route(before, ident, evolved, air, variant, flags)
                            need((rec0,event0,old.r,old.cpsr,old.mem,old.writes) == (record,event,m.r,m.cpsr,m.mem,m.writes), 'all original identity native observable states preserved')
                            old_cases += 1
    return dict(actual_ARM_cases=cases,original_identity_equal_cases=old_cases,
                scope='ID0..14, both resource groups, ground/air, four metadata variants, all NZCV; source boss15 is not a fighter table identity')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('before','gba','old','source','output','manifest'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--owners',type=Path,nargs=5,required=True)
    args = parser.parse_args()
    paths = [args.before,args.gba,args.old,args.source,*args.owners,args.output,args.manifest]
    need(len(set(p.resolve() for p in paths)) == len(paths) and not args.output.exists() and not args.manifest.exists(), 'fresh distinct outputs')
    before,gba,old,source = (p.read_bytes() for p in paths[:4])
    proof = contract(before,gba,old,source)
    allocation = ownership(before,args.owners)
    after,writes = bytearray(before),[]
    for k,(native,src,record,target,aliases) in enumerate(SPECS):
        for at,blob,label in [(TABLES[k],struct.pack('<15I',*((BASE+target,)*15)),'fifteen source identities')]+[(a,struct.pack('<I',BASE+TABLES[k]),'native table alias') for a in aliases]:
            writes.append(dict(offset=at,size=len(blob),before_hex=before[at:at+len(blob)].hex(),after_hex=blob.hex(),label=label))
            after[at:at+len(blob)] = blob
    after=bytes(after)
    inverse=bytearray(after)
    for write in writes:
        a=write['offset'];inverse[a:a+write['size']]=bytes.fromhex(write['before_hex'])
    need(bytes(inverse)==before and len(writes)==9 and sum(w['size'] for w in writes)==260, 'complete inverse, four tables and five pointers only')
    validation=validate(before,after)
    report=dict(status='PASS',input_sha256=sha(before),output_sha256=sha(after),source_sha256=SOURCE,
                allocation=allocation,contract=proof,validation=validation,writes=writes,
                actual_changed_bytes=sum(a!=b for a,b in zip(before,after)),
                limits=['No emulator execution or dynamic emitter witness is claimed by this static/ARM contract.',
                        'No main build, existing assets, native reaction code, ROM source or prior outputs are modified.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.manifest.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_bytes(after)
    args.manifest.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='PASS',output_sha256=sha(after),manifest_sha256=sha(args.manifest.read_bytes()),validation=validation)))


if __name__ == '__main__':
    main()
