#!/usr/bin/env python3
"""Independent bounded93E7 selector/source/actual-ARM QA; no builder or game I/O."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
import verify_shoot_static_companion_clear as prior
import verify_shoot_caller_resident as scanner
from verify_character_p0_completion import source_descriptor, inverse_pixels
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

BASE = 0x08000000
BEFORE = '35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
PROOF = '2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990'
LOWER = '37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281'
FIRST, LIMIT, POINTER = 0x6FF240, 0x6FF28C, 0x12C50
ENTRY, OLD, BODY = BASE + FIRST, 0x086FEA00, 0x086FEA50
P0, P1, SOURCE_P0 = 0x5DB300, 0x5C4800, 0x3D44E0
need, sha, u, h = prior.need, prior.sha, prior.u, prior.h


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state'), 'save/state paths forbidden')
    return path.read_bytes()


def xs(data, at, size):
    ins = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(data[at:at + size], at))
    return [i.mnemonic + ' ' + i.op_str for i in ins]


def structural(before, after, inbound=True):
    need(len(before) == len(after) == 0x800000, 'complete ROM extent')
    need(before[FIRST:LIMIT] == bytes([255]) * 76, 'entire76byte reservation erased')
    need(u(before, POINTER) == OLD and u(after, POINTER) == ENTRY, 'actual dispatcher pointer replacement')
    restored = bytearray(after)
    restored[FIRST:LIMIT] = before[FIRST:LIMIT]
    restored[POINTER:POINTER + 4] = before[POINTER:POINTER + 4]
    need(restored == before, 'exact80byte ownership and whole-ROM inverse')
    need(prior.listing(after, 0x6FEA50, 12) == [
        'ldr ip, [pc, #0x190]', 'ldr r0, [pc, #0x190]', 'ldrb r0, [r0]'] and
        prior.listing(after, 0x6FEBDC, 12) == [
            'pop {sb}', 'pop {r0, r1, r2, r3, r4, r5, lr}', 'bx lr'],
        'retained renderer body entry and single R9 epilogue')
    if inbound:
        scanner.SPANS = ((FIRST, LIMIT),)
        need(not scanner.inbound(before), 'strict whole-ROM pointer/ARM/Thumb inbound census')


def scope_contract(proof):
    need(proof['status'] == 'BOUNDED_P2_NO_RELOAD_COMPOSITION_PASS' and
         proof['composition']['bounded_post197A_no_side1_companion_reload'] is True and
         proof['composition']['resident_93E7_extension_supported'] is True and
         proof['full_post_clear_reload_exclusion_approved'] is False,
         'bounded normal graph supported; unrestricted reload exclusion remains false')
    need(proof['composition']['lower_callbacks'] == 43 and
         proof['upper_callback_instructions'] == 775 and
         proof['borrowed_graph']['instructions'] == 790 and
         '0A80/EB4C/E59A' in proof['composition']['external_gate'],
         'explicit normal43lower/775upper/790borrowed scope and unchanged external gate')


def source_contract(source, before, proof_bytes, lower_bytes):
    need(sha(proof_bytes) == PROOF and sha(lower_bytes) == LOWER, 'exact conditional source proof and lower graph')
    scope_contract(json.loads(proof_bytes))
    need(xs(source, 0x749CE7, 9)[:2] == ['push 5', 'push 0x6d'] and
         xs(source, 0x747CA9, 23)[:7] == ['push 0x6d', 'push 0x4000', 'push 0xbd',
             'push 0x244e', 'push 0', 'lcall 0x4fff, 0x226e', 'add sp, 0xa'],
         'actual child base and pre-clear standalone preload identity')
    for at, size, expected in (
        (0x7525FF, 14, ['mov dx, word ptr es:[di + 8]', 'and dx, 2', 'jne 0x75260c', 'jmp 0x7526aa']),
        (0x752796, 14, ['mov dx, word ptr es:[di + 8]', 'and dx, 2', 'jne 0x7527a3', 'jmp 0x752841']),
        (0x752984, 13, ['mov ax, word ptr es:[di + 8]', 'and ax, 2', 'jne 0x752990', 'jmp 0x7529f5']),
    ):
        need(xs(source, at, size)[:4] == expected, 'static event/frame/update does not restore pixels')
    need(xs(source, 0x749D2C, 20)[:6] == ['push 0', 'push 0xc00', 'push di',
         'lcall 0x4fff, 0x24cb', 'add sp, 6', 'or word ptr [di + 8], 0x2000'],
         '93E7 event selection changes only priority flag')
    need(u(before, 0x5C4580) == BASE + P0 and u(before, 0x5C4588) == 0x6D and
         u(before, P1 + 4) == 0, 'actual native constructor P0/base and static P1 flags')
    source_layouts = (h(source, SOURCE_P0 + 18) - 16) // 4
    table, desc = u(before, P0) - BASE, u(before, P0 + 4) - BASE
    need(source_layouts == 8 and before[P0 + 8:P0 + 16] == source[SOURCE_P0 + 8:SOURCE_P0 + 16] and
         h(source, SOURCE_P0 + 14) == 8, 'eight source/native static layouts and exact header constants')
    for layout in range(8):
        n, offset = struct.unpack_from('<2H', source, SOURCE_P0 + 16 + layout * 4)
        nn, ptr = struct.unpack_from('<2I', before, table + layout * 8)
        need(nn == n and before[ptr - BASE:ptr - BASE + n * 4] ==
             source[SOURCE_P0 + offset:SOURCE_P0 + offset + n * 4], 'every original93E7 layout part exact')
    segment, bank = struct.unpack_from('<2H', source, SOURCE_P0 + 4)
    source_table = (bank & 127) * 0x10000 + segment * 16 - 0x20000
    length, pixels = source_descriptor(source, source_table)
    need(length == u(before, desc) == 768 and
         inverse_pixels(before[u(before, desc + 4) - BASE:u(before, desc + 4) - BASE + length]) == source[pixels:pixels + length],
         'all24 native tile pixels inverse to original source descriptor0')
    return (P0, P1, table, 8, desc)


def fixture(rom, resource, **kwargs):
    kwargs.setdefault('base', 0x6D)
    return prior.fixture(rom, resource, **kwargs)


def edge_cases(after, resource):
    count = 0
    for first, bits in itertools.product(range(74, 129, 2), range(16)):
        mask = first | bits << 8
        m = fixture(after, resource, mask=mask, owner_index=51)
        initial = m.r[:15]
        stop = m.run(0x08012C28, {OLD, BODY})
        need(stop == BODY and m.r[9] == mask - 36 and m.r[5] == prior.PRESENT and
             m.r[6:8] == initial[6:8] and m.r[13] == initial[13] - 32 and
             m.get(initial[13] - 32) == ENTRY, 'real last-slot owner mask translation and exactly one saved R9')
        count += 1
    for owner, mask, index, phase in (
        (True, 0, 0, prior.PHASES[0]), (False, 0, 0, prior.PHASES[0]),
        (False, 0xF6C, 0, prior.PHASES[0]), (True, 0xF6C, 0, 0x0834059C),
    ):
        m = fixture(after, resource, owner=owner, mask=mask, owner_index=index)
        if owner:
            m.put(prior.POOL + index * 0x118, phase)
        initial = m.r[:15]
        need(m.run(0x08012C28, {OLD, BODY}) == BODY and m.r[9] == 0 and
             m.r[13] == initial[13] - 32, 'recognized no-owner/zero/unrecognized-phase keeps zero mask')
        count += 1
    for base, flags, p0 in ((0x49, 0x2000, BASE + P0), (0x6D, 0x2002, BASE + P0),
                            (0x6D, 0x2000, 0x085DB400), (0x6D, 0x2000, 0x085DB304)):
        m = fixture(after, resource, base=base, flags=flags)
        m.put(prior.PRESENT + 0x48, p0)
        initial = m.r[:15]
        need(m.run(0x08012C28, {OLD, BODY}) == OLD and m.r[13] == initial[13] - 28 and
             m.r[6:8] == initial[6:8], 'unrecognized selector tails unchanged without extra save')
        count += 1
    return count


def execute_pair(before, after, resource, mask, *, bits=None, **kwargs):
    old = fixture(before, resource, mask=mask, **kwargs)
    new = fixture(after, resource, mask=mask, **kwargs)
    if bits is not None:
        for m in (old, new):
            index = kwargs.get('owner_index', 0)
            m.put(prior.POOL + index * 0x118 + 0x18 + 0x52, (mask & 255) | bits << 8, 2)
    initial = new.r[:15]
    for m in (old, new):
        m.run(0x08012C28, {initial[14]})
    need(new.r[:6] == old.r[:6] == initial[:6] and new.r[13:15] == old.r[13:15] == initial[13:15],
         'actual dispatcher/full renderer caller ABI, SP and return')
    need(prior.buffer(old, 0x03001428, 1024) == prior.buffer(new, 0x03001428, 1024) and
         old.get(0x030012CA, 1) == new.get(0x030012CA, 1), 'full OAM and native tile indices unchanged')
    need([(a, n) for a, _, n in old.writes if a < 0x03007000] ==
         [(a, n) for a, _, n in new.writes if a < 0x03007000], 'identical complete non-stack write address/size sequence')
    return old, new


def projectile_cases(before, after, resource):
    count, blanked = 0, 0
    for layout, bx, bits in itertools.product(range(8), range(261, 289), range(16)):
        first = 2 * bx - 448
        old, new = execute_pair(before, after, resource, first | bits << 8, layout=layout)
        expected = bytearray(prior.buffer(old, 0x02000000, 4096))
        parts = u(after, resource[2] + layout * 8 + 4) - BASE
        for part in range(u(after, resource[2] + layout * 8)):
            relative = 109 + after[parts + part * 4] - first
            if 0 <= relative < 4 and bits & (1 << relative):
                expected[part * 32:(part + 1) * 32] = bytes(32)
                blanked += 1
        need(prior.buffer(new, 0x02000000, 4096) == expected, 'actual93E7 full staging equals direct source109 tile predicate')
        count += 1
    for flags, start, x, y, owner, mask in (
        (0x2000, 0, 100, 100, True, 0), (0x2000, 0, 100, 100, False, 0xF6C),
        (0x2000, 127, 100, 100, True, 0xF6C), (0x2000, 0, -100, -100, True, 0xF6C),
        (0x2002, 0, 100, 100, True, 0xF6C),
    ):
        old, new = execute_pair(before, after, resource, mask, flags=flags, count=start, x=x, y=y, owner=owner)
        need(prior.buffer(old, 0x02000000, 4096) == prior.buffer(new, 0x02000000, 4096),
             'zero/inactive/saturated/clipped/indexed path exact')
        count += 1
    for layout, flags, start in itertools.product(range(8), (0, 0x2000, 0x6000, 0xA000, 0xE000), (0, 7)):
        old, new = execute_pair(before, after, resource, 0x56C, layout=layout, flags=flags, count=start)
        expected = bytearray(prior.buffer(old, 0x02000000, 4096))
        parts = u(after, resource[2] + layout * 8 + 4) - BASE
        for part in range(u(after, resource[2] + layout * 8)):
            relative = 109 + after[parts + part * 4] - 108
            if 0 <= relative < 4 and 5 & (1 << relative):
                expected[(start + part) * 32:(start + part + 1) * 32] = bytes(32)
        need(prior.buffer(new, 0x02000000, 4096) == expected, 'facings/palette priority/native tile start preserve sparse source mask')
        count += 1
    need(blanked > 0, 'positive actual source tile overlap population')
    return dict(cases=count, layouts=8, clear_positions=28, live_bit_states=16, blanked_parts=blanked)


def fallback_cases(before, after):
    count = 0
    for resource in prior.resource_rows(after):
        for layout, mask in itertools.product(range(resource[3]), (0, 0xF49)):
            old, new = prior.rendered(before, after, resource, layout=layout, mask=mask)
            need(prior.buffer(old, 0x02000000, 4096) == prior.buffer(new, 0x02000000, 4096) and
                 old.r[:9] == new.r[:9] and old.r[10:15] == new.r[10:15] and old.cpsr == new.cpsr,
                 'every companion layout falls through to exact v71 execution except dispatcher-scratchR9')
            count += 1
    for flags in (0x2001, 0x2003):
        for rom in (before, after):
            m = fixture(rom, child_resource(rom), flags=flags)
            initial_sp = m.r[13]
            need(m.run(0x08012C28, {0x08012DCC, ENTRY}) == 0x08012DCC and
                 m.r[13] == initial_sp - 28, 'BG flag1 dispatch never enters selector')
        count += 1
    for p0, p1, base, flags in (
        (0x5DB400, 0x5C4C00, 0x137, 0x2000),
        (u(after, 0x4A8118) - BASE, u(after, 0x4A811C) - BASE, 1, 0x2002),
        (u(after, 0x4A82B8) - BASE, u(after, 0x4A82BC) - BASE, 1, 0x2002),
    ):
        resource = (p0, p1, u(after, p0) - BASE, 1, u(after, p0 + 4) - BASE)
        layouts = 18 if p0 == 0x5DB400 else 1
        for layout in range(layouts):
            old, new = execute_pair(before, after, resource, 0xF6C, layout=layout, base=base, flags=flags)
            need(prior.buffer(old, 0x02000000, 4096) == prior.buffer(new, 0x02000000, 4096),
                 '888B and ordinary ID1/14 presentations retain v71 pixels')
            count += 1
    return count


def child_resource(rom):
    return (P0, P1, u(rom, P0) - BASE, 8, u(rom, P0 + 4) - BASE)


def negatives(before, after, source, resource, proof_bytes, lower_bytes):
    rejected = []

    def reject(label, check):
        try:
            check()
        except (ValueError, KeyError, IndexError, struct.error):
            rejected.append(label)
        else:
            raise ValueError('negative control accepted: ' + label)

    def changed(at, word):
        bad = bytearray(after)
        struct.pack_into('<I', bad, at, word)
        return bytes(bad)

    for at, word, label in (
        (FIRST + 4, 0xE350006C, 'wrong child fixed base'),
        (FIRST + 16, 0xE3100004, 'wrong indexed exclusion bit'),
        (FIRST + 72, 0x085DB304, 'wrong exact P0 literal'),
        (FIRST + 40, 0xE1A09009, 'missing one R9 save'),
        (FIRST + 48, 0xE1A00000, 'missing actual owner lookup'),
        (FIRST + 64, 0xE2499024, 'unconditional mask subtraction corrupts zero'),
        (FIRST + 64, 0x12499023, 'wrong36tile mask translation'),
        (FIRST + 68, 0xEAFFFFEE, 'wrong renderer body continuation'),
    ):
        reject(label, lambda at=at, word=word: edge_cases(changed(at, word), resource))
    for at in (0x100, LIMIT, 0x6FEA00, 0x35346C):
        reject('undeclared write ' + hex(at), lambda at=at: structural(before, changed(at, u(after, at) ^ 1), False))
    bad = bytearray(source)
    bad[0x752606] ^= 1
    reject('static event upload gate', lambda: source_contract(bad, before, proof_bytes, lower_bytes))
    bad = bytearray(after)
    bad[0x6FEBF0] = 1
    reject('retained blank tile corrupted', lambda: structural(before, bad, False))
    bad_proof = json.loads(proof_bytes)
    bad_proof['full_post_clear_reload_exclusion_approved'] = True
    reject('conditional source proof promoted to global closure', lambda: scope_contract(bad_proof))
    bad_proof = json.loads(proof_bytes)
    bad_proof['composition']['external_gate'] = ''
    reject('source nonpattern external gate omitted', lambda: scope_contract(bad_proof))
    scanner.SPANS = ((FIRST, LIMIT),)
    for kind, origin, payload in (
        ('unaligned mirrored pointer', 0, b'\x00' + struct.pack('<I', 0x0C000000 + FIRST) + bytes(3)),
        ('ARM branch', FIRST - 0x100, struct.pack('<I', 0xEA00003E)),
        ('Thumb branch', FIRST - 0x100, struct.pack('<H', 0xE07E)),
    ):
        need(scanner.inbound(payload, origin), 'strict inbound control: ' + kind)
        rejected.append(kind)
    return rejected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('before', 'after', 'source', 'output'):
        p.add_argument(name, type=Path)
    p.add_argument('--source-proof', type=Path, required=True)
    p.add_argument('--lower-graph', type=Path, required=True)
    a = p.parse_args()
    need(a.output.suffix.lower() == '.json' and all(a.output.resolve() != v.resolve()
         for k, v in vars(a).items() if k != 'output'), 'distinct JSON output only')
    before, after, source, proof_bytes, lower_bytes = map(read, (a.before, a.after, a.source, a.source_proof, a.lower_graph))
    need((sha(before), sha(source)) == (BEFORE, SOURCE), 'exact v71 and original source inputs')
    need(sha((ROOT / 'tools/verify_shoot_static_companion_clear.py').read_bytes()) ==
         'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943', 'frozen v71 ARM verification primitives')
    structural(before, after)
    resource = source_contract(source, before, proof_bytes, lower_bytes)
    # Recompute the relevant existing source proof with the caller's explicit graph.
    import analyze_shoot_p2_reload_eligibility as reload
    expected = json.loads(proof_bytes)
    expected.pop('negative_controls_rejected')
    need(reload.proof(source, a.lower_graph) == expected, 'actual original source recomposes exact conditional no-reload proof')
    report = dict(status='BOUNDED_93E7_SELECTOR_QA_PASS', before_sha256=sha(before), after_sha256=sha(after),
        verifier_sha256=sha(Path(__file__).read_bytes()), source_sha256=sha(source), source_proof_sha256=sha(proof_bytes),
        lower_graph_sha256=sha(lower_bytes), edge_cases=edge_cases(after, resource),
        projectile=projectile_cases(before, after, resource), fallback_cases=fallback_cases(before, after),
        negatives=negatives(before, after, source, resource, proof_bytes, lower_bytes),
        whole_ROM_inverse=True, strict_inbound=True, external_entry_authorized=False,
        full_post_clear_reload_exclusion_approved=False, complete_terminal_clear=False,
        scope='Exact93E7/static6D under normal43lower/775upper/790borrowed graph and exclusive ordinary ownership only',
        dependencies={name: sha((ROOT / 'tools' / name).read_bytes()) for name in (
            'verify_shoot_static_companion_clear.py', 'verify_shoot_attack_dispatch.py',
            'verify_shoot_caller_resident.py', 'verify_character_p0_completion.py',
            'analyze_shoot_p2_reload_eligibility.py')})
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print('PASS', sha(read(a.output)))


if __name__ == '__main__':
    main()
