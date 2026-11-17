"""Independent source/native campaign producer and bounded ROM allocation review."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_16
from verify_shoot_static_companion_clear import Machine as ArmMachine
import verify_shoot_caller_resident as scanner

BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
BEFORE = 'FBD9CD19FB1F8EB65675D11403774189040BB181791DB71C98587920BB6885FD'
AFTER = 'ADBF5D521A3EB2C672F11633104F625520004BCE59B7393005C32E96C3B6FDB9'
MANIFEST = '54F238FF67C1D97E9C85DBE321C06A32A32646E347E5190CFC0A4639314ADF55'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
CONFIG, SCENE, RETURN = 0x03002310, 0x02010000, 0x08001234
PRODUCER = 0x0808B638
FIRST, LIMIT = 0xD3FB10, 0xD3FB80
TABLES = (0xD3FB10, 0xD3FB18, 0xD3FB40, 0xD3FB50)


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest().upper()


def word(raw, at):
    return struct.unpack_from('<I', raw, at)[0]


def exact(data, at, expected, arm=False):
    c = Cs(CS_ARCH_ARM if arm else CS_ARCH_X86, CS_MODE_ARM if arm else CS_MODE_16)
    base = BASE if arm else 0
    got = [(i.mnemonic + ' ' + i.op_str).strip() for i in c.disasm(data[at:at+256], base+at, len(expected))]
    need(got == expected, f'exact instruction anchor {at:06X}: {got!r}')


def source_contract(source, before, gba):
    need(sha(source) == SOURCE and sha(before) == BEFORE and sha(gba) == GBA, 'immutable source/input pins')
    first = list(source[0x778674:0x778679])
    rows = [list(source[0x778679+i*5:0x77867E+i*5]) for i in range(8)]
    cpus = list(source[0x7786A1:0x7786AC])
    dispatch = struct.unpack_from('<11H', source, 0x7786AC)
    need(first == [8, 1, 9, 6, 10] and cpus == [0, 1, 2, 5, 6, 4, 3, 15, 13, 14, 11], 'source stage/CPU tables')
    need(dispatch == (0x17E9,)*5 + (0x17F3,)*5 + (0x180D,), 'source eleven dispatch entries')
    need(all(sorted(row) == [0, 2, 3, 4, 5] for row in rows), 'each RNG row visits remaining five stages')
    need(all(sorted(first+row+[7]) == list(range(11)) for row in rows), 'each complete campaign visits eleven stages exactly once')
    exact(source, 0x778703, ['xor bx, bx', 'mov bl, byte ptr [si + 0x1f]', 'push bx',
        'add bx, bx', 'add bx, bx', 'sub ax, 5', 'add bx, ax', 'pop ax', 'add bx, ax',
        'mov bl, byte ptr cs:[bx + 0x1769]'])
    exact(source, 0x778725, ['mov byte ptr [si + 0xe], bl', 'test byte ptr [si + 0x25], 1',
        'je 0x778731', 'call 0x7785e5', 'xor bh, bh', 'mov al, byte ptr cs:[bx + 0x1791]'])
    exact(source, 0x7786E8, ['and word ptr [si + 0x1a], 0xffef', 'or word ptr [si + 0x1a], 0x20',
        'xor bx, bx', 'mov al, 0xb', 'jmp 0x778738'])
    exact(source, 0x778738, ['mov byte ptr [si + 0xc], al', 'mov byte ptr [si + 0xd], bh',
        'cmp byte ptr [si + 0xa], al', 'jne 0x77874b', 'mov al, byte ptr [si + 0xb]',
        'xor al, 1', 'mov byte ptr [si + 0xd], al'])
    exact(source, 0x78074F, ['lcall 0x4fff, 0x1cb5', 'and ax, 7', 'mov byte ptr es:[di + 0x1f], al'])
    exact(source, 0x777AE3, ['test word ptr es:[si + 0x1a], 1', 'jne 0x777af4',
        'inc byte ptr es:[si + 0x1e]', 'lcall 0x76f1, 0x17b2'])
    need(before[0x8B638:0x8B728] == gba[0x8B638:0x8B728], 'retained retail producer baseline')
    for lo, hi in ((0x91144, 0x911A4), (0x8A6E8, 0x8A710)):
        need(before[lo:hi] == gba[lo:hi], 'retained initializer/seed/progress lineage')
    need(word(before, 0x8B714) == CONFIG and word(before, 0x582C74) == CONFIG and
         word(before, 0x584A60) == CONFIG, 'actual config owner for producer and both getters')
    exact(before, 0x91198, ['bl #0x8012600', 'and r0, r0, #7', 'strb r0, [r4, #0x1f]'], True)
    exact(before, 0x8A6E8, ['ldrh r8, [r4, #0x1a]', 'tst r8, #1', 'bne #0x808a704',
        'ldrb r8, [r4, #0x1e]', 'adds r8, r8, #1', 'strb r8, [r4, #0x1e]', 'bl #0x808b638'], True)
    return dict(first=first, rows=rows, cpus=cpus, source_dispatch=list(dispatch),
        source_window_sha256=sha(source[0x778674:0x77874F]),
        default_mode='source config+25 bit0 clear; alternate challenge mode not implemented',
        persisted_progress='config+1E', rng_row='config+1F = RNG & 7; not difficulty',
        dedicated_flag10='preserves physical stage and progress, sets CPU11 and flag20 while clearing10')


class Machine(ArmMachine):
    def __init__(self, *args, **kwargs):
        self.rom_reads = []
        super().__init__(*args, **kwargs)

    def get(self, address, size=4):
        if BASE+FIRST <= address < BASE+LIMIT:
            self.rom_reads.append((address, size))
        return super().get(address, size)


def fixture(rom, progress=0, row=0, player=0, form=0, flags=0, stage=0xA5, mode=0):
    m = Machine(rom, seed=7, flags=0xA0000010)
    for i in range(0x40):
        m.put(CONFIG+i, (i*17+3)&255, 1)
        m.put(SCENE+i, (i*19+7)&255, 1)
    for off, value in ((0x1E, progress), (0x1F, row), (0xA, player), (0xB, form), (0xE, stage), (0x25, mode)):
        m.put(CONFIG+off, value, 1)
    m.put(CONFIG+0x1A, flags, 2); m.put(SCENE+0x1A, 0xFFFF, 2)
    m.r[5], m.r[14] = SCENE, RETURN
    return m


def expected_stage(model, progress, row):
    return model['first'][progress] if progress < 5 else model['rows'][row][progress-5] if progress < 10 else 7


def producer_case(rom, model, progress, row, player=0, form=0, flags=0, stage=0xA5, mode=0):
    m = fixture(rom, progress, row, player, form, flags, stage, mode)
    initial, regs = m.mem.copy(), m.r[:]
    physical = stage if flags & 0x10 else expected_stage(model, progress, row)
    cpu = 11 if flags & 0x10 else model['cpus'][physical]
    wanted = dict(initial)
    def set_value(address, value, size):
        for i in range(size): wanted[address+i] = (value >> (i*8)) & 255
    set_value(SCENE+0x1A, 0xFFEF, 2)
    if flags & 0x10:
        set_value(CONFIG+0x1A, (flags & ~0x10)|0x20, 2)
    else:
        set_value(CONFIG+0xE, physical, 1)
    set_value(CONFIG+0xC, cpu, 1)
    set_value(CONFIG+0xD, form ^ 1 if player == cpu else 0, 1)
    m.run(PRODUCER, {RETURN})
    need(all(m.mem[a] == v for a, v in wanted.items()), 'source producer complete config/scene outcome')
    need(all(m.r[r] == regs[r] for r in list(range(8)) + [10, 11, 12, 13, 14]), 'retained producer register/stack ABI')
    need(not m.calls, 'source default mode invokes no challenge or extra service')
    if flags & 0x10:
        need(not m.rom_reads, 'flag10 bypasses progress/RNG tables including out-of-domain values')
    else:
        reads = [(BASE+TABLES[3]+progress*4, 4)]
        if progress < 5: reads.append((BASE+TABLES[0]+progress, 1))
        elif progress < 10: reads.append((BASE+TABLES[1]+row*5+progress-5, 1))
        reads.append((BASE+TABLES[2]+physical, 1))
        need(m.rom_reads == reads, 'exact table indexes/typed widths')
    allowed = set(wanted) | set(range(regs[13]-16, regs[13]))
    need(set(m.mem) <= allowed, 'no new writable global/pool owner')
    return physical, cpu


def behavior(rom, model):
    normal = 0
    for progress, row, player, form in itertools.product(range(11), range(8), range(16), range(2)):
        producer_case(rom, model, progress, row, player, form); normal += 1
    flags_count = 0
    for progress, row, flags in itertools.product(range(11), range(8), (1, 0x20, 0x40, 0x1000, 0xFFEF)):
        producer_case(rom, model, progress, row, flags=flags); flags_count += 1
    dedicated = 0
    for progress, row, stage, player, form, flags in itertools.product((0, 10, 11, 255), (0, 7, 8, 255),
            (0, 7, 8, 9, 10, 11), (0, 11), (0, 1), (0x10, 0x11, 0x50, 0xFFFF)):
        producer_case(rom, model, progress, row, player, form, flags, stage); dedicated += 1
    getters = 0
    for entry, stage, player in itertools.product((0x08582C40, 0x08584A00), range(12), range(16)):
        m = fixture(rom, player=player, stage=stage); regs, memory = m.r[:], m.mem.copy()
        m.run(entry, {RETURN})
        value = stage if entry == 0x08582C40 else {8:0, 9:6, 10:3, 11:7}.get(stage, stage)
        need(m.r[0] == value and m.mem == memory, 'physical stage getter independent of player selection')
        need(all(m.r[r] == regs[r] for r in range(1,15) if r != 8), 'getter register ABI')
        getters += 1
    seed_cases = 0
    for value in (0, 1, 7, 8, 15, 255, 0x80000000, 0xFFFFFFFF):
        m = fixture(rom); m.r[4] = CONFIG; before = m.mem.copy()
        m.services[0x08012600] = lambda cpu, v=value: cpu.r.__setitem__(0, v)
        m.run(0x08091198, {0x080911A4})
        need(m.get(CONFIG+0x1F,1) == value & 7 and len(m.calls) == 1, 'actual masked RNG producer')
        need(all(m.mem[a] == v for a,v in before.items() if a != CONFIG+0x1F), 'RNG affects only persisted row')
        seed_cases += 1
    m = fixture(rom, progress=255, row=255); m.r[4] = CONFIG
    m.run(0x08091144, {0x08091154})
    need([m.get(CONFIG+x,1) for x in (0xE,0x1E,0x1F)] == [0,0,0], 'retained fresh-campaign initialization')
    successors = 0
    for progress, row, lock in itertools.product(range(10), range(8), (0,1)):
        m = fixture(rom, progress, row, flags=lock); m.r[4] = CONFIG
        m.run(0x0808A6E8, {0x0808A704})
        need(m.get(CONFIG+0x1E,1) == progress+(not lock) and m.get(CONFIG+0x1F,1) == row,
             'retained persisted progress and row on ordinary win successor')
        need(len(m.calls) == (not lock), 'flag1 suppresses successor producer call')
        if not lock:
            need(m.get(CONFIG+0xE,1) == expected_stage(model, progress+1,row), 'actual successor selects next source stage')
        successors += 1
    return dict(normal_producer_cases=normal, retained_flag_cases=flags_count, dedicated_flag10_cases=dedicated,
        getter_cases=getters, rng_cases=seed_cases, initializer_cases=1, successor_cases=successors,
        invalid_progress_domain='not tested as normal input; source has exactly11 entries; flag10 intentionally bypasses tables',
        final_progress='successor tested0..9; stage7 terminal completion remains separately proven existing flow')


def structural(before, after, manifest, model, owner_bytes):
    need(sha(after) == AFTER, 'frozen reviewed campaign candidate')
    expected = {TABLES[0]:bytes(model['first']), TABLES[1]:bytes(sum(model['rows'], [])), TABLES[2]:bytes(model['cpus']),
        TABLES[3]:struct.pack('<11I', *([0x0808B698]*5+[0x0808B6A8]*5+[0x0808B6C8]))}
    for at, value in {0x8B718:BASE+TABLES[3], 0x8B71C:BASE+TABLES[0], 0x8B720:BASE+TABLES[1], 0x8B724:BASE+TABLES[2],
        0x8B6AC:0xE0911101, 0x8B6B0:0xE1A01001, 0x8B6B4:0xE2500005, 0x8B6D8:0xE1A00000,
        0x582C44:0xEA000008, 0x584A04:0xEA000008}.items():
        expected[at] = struct.pack('<I', value)
    need(len(expected) == 14 and sum(map(len, expected.values())) == 140, 'independent exact14-span definition')
    actual = {w['offset']:bytes.fromhex(w['after_hex']) for w in manifest['writes']}
    need(len(manifest['writes']) == len(actual) and actual == expected, 'manifest matches independent semantic writes')
    restored = bytearray(after)
    for w in manifest['writes']:
        at, size = w['offset'], w['size']
        need(size == len(expected[at]) and after[at:at+size] == expected[at] and
             before[at:at+size] == bytes.fromhex(w['before_hex']), 'exact before/after span')
        restored[at:at+size] = before[at:at+size]
    need(restored == before and len(after) == len(before) == 0x1000000 and
         sum(a != b for a,b in zip(before, after)) == 126, 'whole16MiB inverse and126-byte actual difference')
    pins = ('AC3BC1D7B9865C8BD241B1FDBBF415AB8F339B58E7F8AAEDBB4703EB094B7D91',
        '4A7E7C0292C96D0408850B235407AADDA5235DB466E6683593FC084DB2CBE9F6',
        '64D6123494AFD4D85445C57E5AF327D149AB9CF776CAE7A1CA88BB2818FA1DBD')
    need(tuple(map(sha, owner_bytes)) == pins, 'frozen audio/table/ID13 owners')
    owners = list(map(json.loads, owner_bytes))
    need([0xD33000,0xD40000] in owners[0]['reservations'] and
         owners[1]['allocation']['remaining_tail'] == [0xD3F05A,0xD40000] and
         owners[2]['allocation']['suballocation'] == [0xD3F100,0xD3FA00], 'positive enclosing and prior suballocation ownership')
    prior_count = 0
    for k, owner in enumerate(owners):
        for w in owner['writes']:
            lo, hi = w['offset'], w['offset']+w['size']
            need(max(lo,FIRST) >= min(hi,LIMIT), 'no previous owned write overlaps new suballocation')
            if k == 0:
                if not 0xD33000 <= lo < 0xD40000: continue
                need(sha(before[lo:hi]) == w['after_sha256'], 'earlier audio contents retained')
            else:
                need(before[lo:hi] == bytes.fromhex(w['after_hex']), 'earlier table/ID13 contents retained')
            need(after[lo:hi] == before[lo:hi], 'all prior owned bytes survive new component')
            prior_count += 1
    need(before[FIRST:LIMIT] == b'\xff'*(LIMIT-FIRST), 'entire specifically owned unused range')
    scan = types.FunctionType(scanner.inbound.__code__, dict(scanner.__dict__, SPANS=((FIRST,LIMIT),)),
                              argdefs=scanner.inbound.__defaults__)
    hits = scan(before); need(not hits, 'no incoming pointers/branches/literals/ADR; no scan exceptions')
    need(manifest['allocation']['suballocation'] == [FIRST,LIMIT] and manifest['allocation']['new_RAM_bytes'] == 0,
         'precise bounded new allocation claim')
    return dict(spans=14, declared_bytes=140, changed_bytes=126, whole_inverse=True,
        suballocation=[FIRST,LIMIT], prior_owned_writes_checked=prior_count, inbound_hits=hits,
        prior_owner_sha256=pins, new_RAM_bytes=0)


def mutations(before, after, model):
    rejected = []
    def reject(label, at, blob, check):
        changed = bytearray(after); changed[at:at+len(blob)] = blob
        try:
            check(bytes(changed))
        except (ValueError, IndexError):
            rejected.append(label)
        else:
            raise ValueError('mutation survived: '+label)
    def producer(progress, row, **kw):
        return lambda rom: producer_case(rom, model, progress, row, **kw)
    def getter(entry, stage, player, expected):
        def check(rom):
            m = fixture(rom, stage=stage, player=player); m.run(entry,{RETURN})
            need(m.r[0] == expected, 'mutated getter result')
        return check
    reject('first added stage replaced by retail0', TABLES[0], b'\0', producer(0,0))
    reject('RNG row stride4 instead of5', 0x8B6AC, struct.pack('<I',0xE1B01101), producer(5,1))
    reject('retail opening threshold3 instead of5', 0x8B6B4, before[0x8B6B4:0x8B6B8], producer(5,0))
    reject('RNG owner read from adjacent field', 0x8B6A8, struct.pack('<I',0xE5D4101D), producer(5,0))
    reject('final dispatch enters RNG block', TABLES[3]+10*4, struct.pack('<I',0x0808B6A8), producer(10,7))
    reject('added CPU13 erased', TABLES[2]+8, b'\0', producer(0,0,player=13))
    reject('unconditional retail challenge restored', 0x8B6D8, before[0x8B6D8:0x8B6DC], producer(0,0))
    reject('dedicated flag10 selects CPU15', 0x8B690, struct.pack('<I',0xE3A0000F), producer(255,255,flags=0x10,stage=11))
    reject('physical getter character override restored', 0x582C44, before[0x582C44:0x582C48], getter(0x08582C40,9,13,9))
    reject('legacy getter character override restored', 0x584A04, before[0x584A04:0x584A08], getter(0x08584A00,9,13,6))
    return rejected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before','after','manifest','source','gba','audio-manifest','table-manifest','id13-manifest','report'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); need(not a.report.exists(), 'fresh report required')
    paths = (a.before,a.after,a.source,a.gba)
    before,after,source,gba = (x.read_bytes() for x in paths)
    for name, pin in {
        'verify_shoot_static_companion_clear.py':'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
        'verify_shoot_attack_dispatch.py':'695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698',
        'verify_shoot_caller_resident.py':'7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D'}.items():
        need(sha((ROOT/'tools'/name).read_bytes()) == pin, 'frozen actualARM/scanner dependency '+name)
    manifest_bytes = a.manifest.read_bytes(); need(sha(manifest_bytes) == MANIFEST, 'frozen reviewed manifest')
    model = source_contract(source,before,gba)
    allocation = structural(before,after,json.loads(manifest_bytes),model,
        [x.read_bytes() for x in (a.audio_manifest,a.table_manifest,a.id13_manifest)])
    cases = behavior(after,model); negatives = mutations(before,after,model)
    report = dict(status='CAMPAIGN_PRODUCER_INDEPENDENT_PASS', before_sha256=sha(before),after_sha256=sha(after),
        manifest_sha256=MANIFEST, verifier_sha256=sha(Path(__file__).read_bytes()), source=model,
        allocation=allocation, actual_ARM=cases, rejected_semantic_mutations=negatives,
        production_builder_imported=False, emulator_launched=False, runtime_verified=False,
        limitations=['Source equivalence is for default mode config+25 mask0001 clear; no alternate-mode implementation claim.',
            'Normal progress0..10 and RNGrow0..7 are source domains; no fabricated recovery for corrupt indexes.',
            'Direct physical-stage and progress display consumers require separately scoped review before integration.',
            'No campaign playthrough, stage11 requalification or full-port completion claim.'])
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(report['status'],sha(a.report.read_bytes()))


if __name__ == '__main__':
    main()
