"""Independently trace source-mapped child contact state and native ARM calls."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from verify_shoot_static_companion_clear import Machine, Cs, CS_ARCH_X86, CS_MODE_16
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM


ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
MODULE = ROOT / 'tools/shoot_child_contact_callbacks.py'
MODULE_PIN = '8520DA8E5ECB4163936759FCD7FA690222A8A1498B74FC51CFEBC740905EFA98'
PREDECESSOR = '574FD26186CB94D447A8A6F9B60EAE65795CB9BA5AAE4350DBF861A0B2FAED76'
SITE, TAIL = 0x0836F77C, 0x0836E484
CALLBACK, WAIT, RELEASE = 'child_contact_966a', 'child_contact_96e6', 'child_contact_973e'
EFFECT, SOUND, SET_EVENT, UPDATE, RETIRE = 0x0835972C, 0x080D15C0, 0x08012874, 0x08012A84, 0x083524C4
CHILD, TARGET, PARENT, CREATOR = 0x020112B0, 0x02011828, 0x02011710, 0x020115F8
PRESENT = CHILD + 0xAC
STAGE, MATCH_FLAGS, SCROLL = 0x0300231E, 0x0300450A, 0x03004D40
STACK_START, STACK_LIMIT, RETURN = 0x03007000, 0x03008000, 0x08001234
SOURCE_LINES = {
    0x760E57: 'mov al, byte ptr [di + 0xe]',
    0x760E5C: 'cmp al, 0xb',
    0x760E60: 'mov word ptr [si], 0x67df',
    0x760E69: 'and word ptr [si + 4], 0x3eff',
    0x760E71: 'mov word ptr [bx + 0x62], 0x465',
    0x760E79: 'mov word ptr [si], 0x966a',
    0x760E82: 'and word ptr [si + 4], 0x3eff',
    0x760E87: 'mov bx, word ptr [si + 0x12]',
    0x760E8A: 'mov bx, word ptr [bx + 0x1c]',
    0x760E8D: 'mov word ptr [bx + 0x62], 0x465',
    0x760E92: 'jmp 0x760097',
    0x749F6A: 'mov bx, word ptr [si + 0x14]',
    0x749F6D: 'or word ptr [bx + 8], 0x10',
    0x749F72: 'and word ptr [bx + 8], 0xf7ff',
    0x749F77: 'or word ptr [bx + 8], 0x8000',
    0x749F86: 'lcall 0x86bf, 0',
    0x749F8E: 'mov word ptr [si + 0x7e], 0x465',
    0x749FA3: 'mov word ptr [si + 2], 0xa7',
    0x749FA8: 'mov word ptr [si + 0xe], 1',
    0x749FAD: 'mov word ptr [si + 6], 0',
    0x749FB9: 'push 1',
    0x749FBF: 'lcall 0x4fff, 0x24cb',
    0x749FC7: 'mov word ptr [si], 0x96e6',
    0x749FD6: 'or word ptr es:[0x3d8], 0x10',
    0x749FDD: 'mov word ptr es:[0x720], 0xffff',
    0x749FE6: 'push 1',
    0x749FEC: 'lcall 0x4fff, 0x2862',
    0x749FF7: 'test word ptr [bx + 8], 0x4000',
    0x749FFE: 'mov word ptr [si + 0x7e], 1',
    0x74A003: 'dec word ptr [si + 0x7e]',
    0x74A008: 'jmp 0x74a071',
    0x74A00E: 'and word ptr [bx + 8], 0xffef',
    0x74A013: 'or word ptr [bx + 8], 0x800',
    0x74A018: 'push 2',
    0x74A01E: 'lcall 0x4fff, 0x24cb',
    0x74A026: 'mov word ptr [si], 0x973e',
    0x74A035: 'and word ptr es:[0x3d8], 0xffef',
    0x74A03E: 'test word ptr [di + 0xa], 0x2000',
    0x74A045: 'push 1',
    0x74A04B: 'lcall 0x4fff, 0x2862',
    0x74A05A: 'lcall 0x4090, 0x181e',
    0x74A068: 'and word ptr es:[0x3d8], 0xffbf',
    0x74A071: 'xor word ptr [si + 4], 0x20',
    0x74A079: 'mov ax, word ptr [bx + 0x9e]',
    0x74A07D: 'and ax, 0x4000',
    0x74A080: 'and word ptr [di + 8], 0xbfff',
    0x74A085: 'or word ptr [di + 8], ax',
    0x74A088: 'mov ax, word ptr [bx + 0x26]',
    0x74A08B: 'mov word ptr [si + 0x26], ax',
    0x74A08E: 'mov ax, word ptr [bx + 0x28]',
    0x74A091: 'sub ax, 0x100',
    0x74A094: 'mov word ptr [si + 0x28], ax',
}


def need(cond, detail):
    if not cond:
        raise ValueError(detail)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def u(data, address):
    return struct.unpack_from('<I', data, address-BASE)[0]


def patch(data, address, blob):
    index = address-BASE
    need(0 <= index <= len(data)-len(blob), 'in-ROM placement')
    return data[:index]+blob+data[index+len(blob):]


def branch(site, target):
    delta = target-site-8
    need(delta%4 == 0 and -0x2000000 <= delta < 0x2000000, 'ARM branch range')
    return 0xEA000000 | ((delta//4) & 0xFFFFFF)


def source_oracle(source):
    need(sha(source) == SOURCE, 'immutable source')
    x86 = Cs(CS_ARCH_X86, CS_MODE_16)
    ranges = ((0x760E4B, 0x760E95), (0x749F6A, 0x749FE6), (0x749FE6, 0x74A03E), (0x74A03E, 0x74A098))
    ins = {i.address: i.mnemonic + (' '+i.op_str if i.op_str else '')
           for lo, hi in ranges for i in x86.disasm(source[lo:hi], lo)}
    need(all(ins.get(at) == opcode for at, opcode in SOURCE_LINES.items()), 'independent source instruction anchors')
    need([ins[a] for a in (0x749F7C, 0x749F7E, 0x749F80, 0x749F82, 0x749F85)] ==
         ['push 3', 'push 0', 'push 0', 'push 0xc00', 'push bx'], 'source visual argument order')
    return [dict(start=lo, end=hi, sha256=sha(source[lo:hi])) for lo, hi in ranges]


class Witness(Machine):
    def __init__(self, rom, seed=0, flags=0x10):
        super().__init__(rom, seed, flags)
        self.timeline = []
        self.low_stack = self.r[13]

    def put(self, address, value, size=4, log=False):
        super().put(address, value, size, log)
        if log:
            if STACK_START <= address < STACK_LIMIT:
                self.low_stack = min(address, self.low_stack)
            else:
                self.timeline.append(wrote(address, value, size))


def wrote(address, value, size=2):
    return ('write', address, value & ((1 << (size*8))-1), size)


def called(address, *args):
    return ('call', address, *args)


def args(m, length):
    return tuple(m.get(m.r[13]+4*i) for i in range(length))


def setup(rom, stage=11, child_flags=0xDB6D, target_flags=0x28E7, timer=9, presentation_flags=0x6235,
          presentation_done=0, face=0x4000, xy=(0x83BA, 0x0080), match=0xA45F, seed=0, flags=0x10):
    m = Witness(rom, seed, flags)
    m.r[4], m.r[5] = CHILD, PRESENT
    for address, value, size in (
        (STAGE, stage, 1), (CHILD, 0x085B9C00, 4), (CHILD+4, child_flags, 2), (CHILD+0x14, PARENT, 4),
        (PARENT+0x20, CREATOR, 4), (CHILD+0x18, TARGET, 4), (PARENT+0x76, 0x2584, 2), (CREATOR+0x76, 0x8365, 2),
        (TARGET+0x76, 0x6651, 2), (CHILD+0x94, timer, 2), (TARGET+8, target_flags, 2),
        (PRESENT+8, presentation_flags, 2), (PRESENT+0xA, presentation_done, 2), (PRESENT+0xE, 0, 2),
        (TARGET+0xB4, face, 2), (TARGET+0x34, xy[0], 2), (TARGET+0x36, xy[1], 2),
        (CHILD+0x34, 0xB361, 2), (CHILD+0x36, 0x2BD6, 2), (MATCH_FLAGS, match, 2), (SCROLL, 0x8100, 2)
    ):
        m.put(address, value, size)

    def effect(mm):
        mm.timeline.append(called(EFFECT, *args(mm, 5), mm.r[5], mm.r[11]))
        # The local save must keep the child/presentation pair available after the call.
        mm.r[4], mm.r[5], mm.r[8], mm.r[11] = 0x12221333, 0x50500404, 0xFFFF, 0xAB00

    def sound(mm):
        mm.timeline.append(called(SOUND, *mm.r[8:11]))
        for i in range(6, 11):
            mm.r[i] = 0xBAD50000+i

    def event(mm):
        step, bank, p = args(mm, 3)
        mm.timeline.append(called(SET_EVENT, step, bank, p))
        mm.put(p+0xE, step, 2, log=True)

    def update(mm):
        mm.timeline.append(called(UPDATE, *args(mm, 3)))

    def retire(mm):
        mm.timeline.append(called(RETIRE, *args(mm, 2)))

    m.services = {EFFECT: effect, SOUND: sound, SET_EVENT: event, UPDATE: update, RETIRE: retire}
    return m


def collision_frame(m):
    sp = m.r[13]
    saved = [0x87650000+i*0x35 for i in range(5)] + [RETURN]
    for i, value in enumerate(saved):
        m.put(sp+4*i, value)
    return sp, saved


def run_body(m, entry):
    before = m.r[:15]
    need(m.run(entry, {RETURN}) == RETURN, 'returned to caller')
    need(m.r[:15] == before, f'callback whole register and stack return {entry:08X}')


def test_routes(previous, current, labels):
    stages = tuple(x for x in range(22) if x != 11) + (0x7F, 0xFF)
    ordinary_cases = 0
    for stage in stages:
        for nzcv in range(16):
            opts = dict(stage=stage, seed=stage+nzcv, flags=(nzcv<<28)|0xD3,
                        child_flags=(0xD300+stage*0x29+nzcv*7)&0xFFFF)
            native, revised = (setup(data, **opts) for data in (previous, current))
            sp, _ = collision_frame(native)
            collision_frame(revised)
            for m in (native, revised):
                need(m.run(SITE, {RETURN}) == RETURN, 'original collision tail return')
            w = [wrote(CHILD, 0x083723E0, 4), wrote(CHILD+4, opts['child_flags']&0x3EFF),
                 wrote(PARENT+0x76, 0x465)]
            need(native.r[:15] == revised.r[:15] and native.r[13] == revised.r[13] == sp+24
                 and native.cpsr == revised.cpsr == opts['flags']
                 and native.timeline == revised.timeline == w, 'non-stage11 complete observed collision-tail parity')
            need(revised.get(CREATOR+0x76, 2) == 0x8365 and revised.get(TARGET+0x76, 2) == 0x6651,
                 'ordinary direct parent neither creator nor target')
            ordinary_cases += 1
    for nzcv in range(16):
        m = setup(current, flags=(nzcv<<28)|0x10)
        sp, saved = collision_frame(m)
        initial = m.r[:15]
        need(m.run(SITE, {RETURN}) == RETURN, 'stage11 original-tail return')
        expected = [wrote(CHILD, labels[CALLBACK], 4), wrote(CHILD+4, 0xDB6D&0x3EFF), wrote(CREATOR+0x76, 0x465)]
        need(m.timeline == expected, 'stage11 source-linked creator cooldown and write order')
        need(m.get(PARENT+0x76, 2) == 0x2584 and m.get(TARGET+0x76, 2) == 0x6651, 'direct parent and target untampered')
        need(m.r[0] == initial[0] and m.r[1:6] == saved[:5] and m.r[13] == sp+24 and m.r[14] == RETURN,
             'stage11 same retired tail ABI')
        need(all(m.r[i] == initial[i] for i in (6, 7, 10, 11, 12))
             and m.r[8] == (0xDB6D&0x3EFF) and m.r[9] == 0x465 and m.cpsr&255 == 0x10,
             'stage11 caller scratch outputs and system state')
    return dict(nonstage11_comparable_cases=ordinary_cases, stage11_routed_cases=16)


def follow(flags, face, presentation_flags, xy):
    return [wrote(CHILD+4, flags^0x20), wrote(PRESENT+8, (presentation_flags&0xBFFF)|(face&0x4000)),
            wrote(CHILD+0x34, xy[0]), wrote(CHILD+0x36, xy[1]-0x100)]


def test_callbacks(rom, labels):
    first_cases = 0
    values = (0, 0xFFFF, 0x10, 0x8800, 0x4000, 0x2805)
    for flags in values:
        m = setup(rom, target_flags=flags)
        run_body(m, labels[CALLBACK])
        need(m.timeline == [wrote(TARGET+8, (flags|0x8010)&0xF7FF),
                            called(EFFECT, 3, 0, 0, 0, TARGET, TARGET, 0),
                            wrote(CHILD+0x94, 0x465), called(SOUND, 0x4A, 1, 0),
                            called(SET_EVENT, 1, 0, PRESENT), wrote(PRESENT+0xE, 1),
                            wrote(CHILD, labels[WAIT], 4), wrote(MATCH_FLAGS, 0xA45F|0x10), wrote(SCROLL, 0xFFFF)],
             '966A target → visual → timer → sound → event1 → callback → flags → scroll')
        first_cases += 1
    wait_cases = follow_cases = retire_cases = 0
    for dead in (False, True):
        target = 0x9031 | (0x4000 if dead else 0)
        for timer in (0, 1, 2, 0x465, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF):
            m = setup(rom, target_flags=target, timer=timer)
            run_body(m, labels[WAIT])
            result = 0 if dead else (timer-1)&0xFFFF
            expect = [called(UPDATE, 1, 0, PRESENT)]
            if dead:
                expect.append(wrote(CHILD+0x94, 1))
            expect.append(wrote(CHILD+0x94, result))
            if result:
                expect.extend(follow(0xDB6D, 0x4000, 0x6235, (0x83BA, 0x80)))
                need(m.get(PRESENT+0xE, 2) == 0, 'wait callback cannot emit release event early')
            else:
                expect.extend([wrote(TARGET+8, (target&0xFFEF)|0x800), called(SET_EVENT, 2, 0, PRESENT),
                               wrote(PRESENT+0xE, 2), wrote(CHILD, labels[RELEASE], 4),
                               wrote(MATCH_FLAGS, 0xA45F&0xFFEF)])
            need(m.timeline == expect, f'96E6 timer/flags/event order at timer={timer:04X} force={dead}')
            wait_cases += 1
    for facing in (0, 0x4000, 0xFFFF):
        for flags in (0, 0x000A, 0x2036, 0xFFFF):
            m = setup(rom, presentation_done=flags, face=facing, xy=(0xFE87, 0))
            run_body(m, labels[RELEASE])
            if flags&0x2000:
                expect = [called(RETIRE, 0, CHILD), wrote(MATCH_FLAGS, 0xA45F&0xFFBF)]
                retire_cases += 1
            else:
                expect = [called(UPDATE, 1, 0, PRESENT)] + follow(0xDB6D, facing, 0x6235, (0xFE87, 0))
                follow_cases += 1
            need(m.timeline == expect, '973E retire versus valid follow/16-bit Y underflow')
    return dict(first_callback_cases=first_cases, wait_callback_cases=wait_cases,
                release_follow_cases=follow_cases, release_retire_cases=retire_cases)


def assembled(source, entry):
    module_bytes = MODULE.read_bytes()
    need(sha(module_bytes) == MODULE_PIN, 'reviewed candidate module bytes')
    # The production module supplies only the candidate assembly. All execution
    # fixtures, source contracts and output checks above are independent.
    namespace = {}
    exec(compile(module_bytes, str(MODULE), 'exec'), namespace)
    body = namespace['assembly'](source, EFFECT)
    names = (CALLBACK, WAIT, RELEASE)
    with_symbols = body+'\n'+''.join(f'.word {name}\n' for name in names)
    blob = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(with_symbols, entry)[0])
    payload = blob[:-12]
    labels = dict(zip(names, struct.unpack('<3I', blob[-12:]), strict=True))
    need(all(entry <= label < entry+len(payload) and label%4 == 0 for label in labels.values()), 'in-range callback labels')
    return payload, labels


def negatives(image, labels, entry, size):
    end = entry+size
    fixture = setup(image)
    collision_frame(fixture)
    fixture.run(SITE, {RETURN})
    require_value = fixture.get(CREATOR+0x76, 2)
    need(require_value == 0x465, 'baseline cooldown')
    code = image[entry-BASE:end-BASE]
    replacements = (
        ('wrong parent', struct.pack('<I', 0xE5911020), struct.pack('<I', 0xE1A00000)),
        ('wrong cooldown', struct.pack('<I', 0x465), struct.pack('<I', 0x466)),
    )
    rejected = []
    for name, old, new in replacements:
        at = code.find(old)
        need(at >= 0, 'negative fixture target')
        corrupted = patch(image, entry+at, new)
        m = setup(corrupted)
        collision_frame(m)
        m.run(SITE, {RETURN})
        need(m.get(CREATOR+0x76, 2) != 0x465, f'negative witness {name}')
        rejected.append(name)
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--installed', type=Path)
    parser.add_argument('--entry', type=lambda n: int(n, 0), default=0x08FFF000)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    need(not args.report.exists(), 'fresh report required')
    source, before = (args.source.read_bytes(), args.before.read_bytes())
    source_ranges = source_oracle(source)
    need(len(before) == 0x1000000 and sha(before) == PREDECESSOR, 'pinned predecessor 16 MiB')
    need(u(before, SITE) == 0xE59F8108 and u(before, TAIL) == 0xE8BD403E, 'retained original hook and common pop')
    payload, labels = assembled(source, args.entry)
    hook = struct.pack('<I', branch(SITE, args.entry))
    if args.installed:
        image = args.installed.read_bytes()
        for at, data in ((SITE, hook), (args.entry, payload)):
            need(image[at-BASE:at-BASE+len(data)] == data, 'installed bytes equal exact loaded module placement')
        binding = 'installed-component'
    else:
        need(before[args.entry-BASE:args.entry-BASE+len(payload)] == b'\xFF'*len(payload), 'in-memory fixture region erased')
        image = patch(patch(before, args.entry, payload), SITE, hook)
        binding = 'in-memory-ARM-fixture'
    need(len(image) == len(before), 'bounded image')
    sites = (0x0836F780, TAIL, EFFECT, SOUND, SET_EVENT, UPDATE, RETIRE)
    need(all(u(image, a) == u(before, a) for a in sites), 'existing helper entry and legacy tail opcodes preserved')
    routes = test_routes(before, image, labels)
    callbacks = test_callbacks(image, labels)
    result = dict(status='SHOOT_CHILD_CONTACT_ARM_QA_PASS', binding=binding, image_sha256=sha(image),
                  predecessor_sha256=sha(before), module_sha256=MODULE_PIN, checker_sha256=sha(Path(__file__).read_bytes()),
                  route_entry=args.entry, opcode_hook=u(image, SITE), candidate_bytes=len(payload),
                  callback_addresses=labels, source_ranges=source_ranges, source_instruction_anchors=len(SOURCE_LINES),
                  **routes, **callbacks, negative_controls=negatives(image, labels, args.entry, len(payload)),
                  helper_boundaries={'visual': EFFECT, 'audio': SOUND, 'event': SET_EVENT, 'update': UPDATE, 'retire': RETIRE},
                  limits=['Callbacks execute generated ARM with typed helper ABI fixtures. Helper implementation and resources are reviewed separately.',
                          'No emulator or live game state was used. No ROM file was generated by this checker.'])
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(result['status'], sha(args.report.read_bytes()))


if __name__ == '__main__':
    main()
