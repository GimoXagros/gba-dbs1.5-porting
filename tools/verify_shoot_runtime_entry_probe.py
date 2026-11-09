#!/usr/bin/env python3
"""Independent development-only case5 entry probe QA; no builder imports."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_ARCH_X86, CS_MODE_16
from verify_shoot_guarded_transition_irq import Machine, PRIMITIVES
import verify_shoot_caller_resident as scanner

BASE, START, LIMIT, HOOK = 0x08000000, 0x6FF380, 0x6FF400, 0x33FD04
BEFORE = '6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
LAYOUT = '89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33'
RETURN = 0x09000000


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(blob):
    return hashlib.sha256(blob).hexdigest().upper()


def read(path):
    need(path.suffix.lower() not in ('.sav', '.state'), 'ROM/proof inputs only')
    return path.read_bytes()


def u(data, at):
    return struct.unpack_from('<I', data, at)[0]


def branch(data, at):
    word = u(data, at)
    need(word & 0x0E000000 == 0x0A000000, 'actual ARM branch')
    value = word & 0xFFFFFF
    return BASE + at + 8 + (value - (0x1000000 if value & 0x800000 else 0)) * 4


def arm(data, at, length):
    return [i.mnemonic + ' ' + i.op_str for i in
            Cs(CS_ARCH_ARM, CS_MODE_ARM).disasm(data[at:at + length], BASE + at)]


def expected(stage, difficulty, progress):
    return 0x085C8000 if stage != 11 and (difficulty == 3 or
                       difficulty != 0 and progress & 0x400 == 0) else 0x086FC300


def selector_case(data, stage, difficulty, progress, flags):
    m = Machine(data, (stage + difficulty) % 19, flags)
    for address, value, size in ((0x0300231E, stage, 1), (0x0300231F, difficulty, 1),
                                 (0x0300232A, progress, 2)):
        m.put(address, value, size)
    m.r[14] = RETURN
    old, sp = m.r[:15], m.r[13]
    m.run(BASE + HOOK, {0x0833FD08})
    want = old[:]
    want[8] = expected(stage, difficulty, progress)
    need(m.r[:15] == want and m.cpsr == flags, 'exact R8 callback selection and all other registers/SP/LR/CPSR')
    need(all(sp - 16 <= at and at + size <= sp for at, value, size in m.writes),
         'selector writes only its own16-byte stack frame')
    return m


def selector_cases(data):
    count = 0
    for stage in (0, 7, 11, 255):
        for difficulty in range(256):
            for progress in (0, 0x400, 0xFFFF):
                selector_case(data, stage, difficulty, progress, ((count % 16) << 28) | 0xD3)
                count += 1
    return count


def allocated_case(data, stage, difficulty, progress):
    m = Machine(data, 4, 0xB0000010)
    for start, size in ((0x03000000, 0x8000), (0x02010000, 52 * 0x118)):
        for at in range(start, start + size, 4):
            m.put(at, 0)
    root, fighter = 0x02010000, 0x02010118
    for header, callback, priority in ((root, 0x083735BC, 0x6000),
                                       (fighter, 0x0835620C, 0x3000)):
        m.put(header, callback)
        m.put(header + 4, priority)
        m.put(header + 0x10, 2, 2)
    m.put(fighter + 8, fighter)
    m.put(fighter + 12, root)
    m.put(root + 8, fighter)
    m.put(root + 12, root)
    for at, value in ((0x03001338, 2), (0x03001340, fighter), (0x03001344, root),
                       (0x0300133C, root), (0x0300489C, fighter + 0x18)):
        m.put(at, value, 2 if at == 0x03001338 else 4)
    for address, value, size in ((0x0300231E, stage, 1), (0x0300231F, difficulty, 1),
                                 (0x0300232A, progress, 2)):
        m.put(address, value, size)
    m.r[11], m.r[14] = 0, RETURN  # retained native zero-register call ABI
    sp = m.r[13]
    m.run(BASE + HOOK, {0x0833FD20}, max_steps=30000)
    header = 0x02010230
    need(m.r[13] == sp and m.get(header) == expected(stage, difficulty, progress),
         'actual allocator consumes selected R8 callback argument')
    need(m.get(header + 4) == 0xFF0 and m.get(header + 0x10, 2) == 2 and
         m.get(0x03001338, 2) == 3, 'one actual native0FF0 task, not an extra allocator')
    need(sum(call[1] == 0x08011AC4 for call in m.calls) == 1,
         'exactly one retained33FD18 allocation executes')
    need(m.get(0x0300133C) == root and m.get(0x0300232A, 2) == progress,
         'allocation does not forge current task or progression')
    # Actual engine current-task getter is what the existing scene entry calls.
    m.put(0x0300133C, header)
    m.r[14] = RETURN
    m.run(0x0801201C, {RETURN})
    need(m.r[0] == header + 0x18, 'actual current-task header resolves payload+18')
    return m, header


def source_contract(source, retail, before, after):
    rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[0x771F84:0x771FA3], 0x771F84))
    need([i.mnemonic + ' ' + i.op_str for i in rows] == [
        'cmp ax, 0xb', 'pop ax', 'je 0x771fa3',
        'cmp byte ptr es:[0x5d], 3', 'je 0x771fcd',
        'cmp byte ptr es:[0x5d], 0', 'je 0x771fa3',
        'test word ptr es:[0x68], 0x400', 'je 0x771fcd'],
        'actual source case5 unsigned byte/word predicate')
    need(arm(retail, 0x33FD08, 24) == [
        'stmdb sp!, {r8}', 'stmdb sp!, {fp}', 'mov r8, #0xff0',
        'stmdb sp!, {r8}', 'bl #0x8011ac4', 'add sp, sp, #0xc'],
        'retained native one-allocation R8 argument ABI')
    need(before[0x33FD08:0x33FDC0] == after[0x33FD08:0x33FDC0] == retail[0x33FD08:0x33FDC0],
         'native allocation and all neighboring cases unchanged')
    need(sha(after[0x629800:0x62988C]) == '8FEDEC3D4115A92339E37D1F78CAC2A1DE4A435A074CF641339FF22EC90B5F13',
         'current real source-ordered initializer retained')
    need(branch(after, 0x5C853C) == 0x08629800 and arm(after, 0x5C8000, 16) == [
        'push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, ip, lr}',
        'mov fp, #0', 'bl #0x801201c', 'mov r4, r0'],
        'existing source scene entry/current-task ABI and later initializer call')
    need(sha(after[0x6FC300:0x6FC334]) == '3B528805D97B87A3C35CE298E929AE3B46BCE2BDF8009A165A04BFB4EB175474',
         'source0653 terminal router is default, not an absent former callback')
    need(after[0xB9E68:0xB9E6C] == before[0xB9E68:0xB9E6C] and
         after[0x36E5EC:0x36E5F0] == before[0x36E5EC:0x36E5F0],
         'progress producer and approved native fatal hook unchanged')
    return {'source_predicate': 'stage!=11 && (difficulty==3 || (difficulty!=0 && !(progress&0400)))',
            'real_allocator': '0833FD18 ->08011AC4, R8 callback argument,0FF0',
            'scene_entry': '085C8000', 'later_initializer': '08629800',
            'current_task_payload_bias': 24, 'progress_producer_unchanged': True,
            'native_fatal_hook_retained': True}


def structural(before, after, ledger_bytes, scan=True):
    need(len(before) == len(after) == 0x800000, 'complete8MiB ROMs')
    need(before[START:LIMIT] == b'\xff' * (LIMIT - START), 'complete128-byte cave erased')
    restored = bytearray(after)
    for at, length in ((HOOK, 4), (START, 104)):
        restored[at:at + length] = before[at:at + length]
    need(restored == before, 'exact108-byte ownership and whole-ROM inverse')
    need(branch(after, HOOK) == BASE + START and u(after, HOOK) >> 24 == 0xEA and
         branch(after, START + 76) == 0x0833FD08, 'nonlinking selector entry and tail rejoin')
    original = bytearray(after[START:START + 104])
    displacement = (0x33FD08 - (0x5C9900 + 76) - 8) // 4
    struct.pack_into('<I', original, 76, 0xEA000000 | (displacement & 0xFFFFFF))
    need(sha(original) == '9408A3EE46D6FE57F025611FD9C5BDDA2D92A51341F2382B33A3DBD8F51A39E7',
         'only tail branch word differs from reviewed104-byte selector')
    need(sha(ledger_bytes) == LAYOUT, 'frozen native ownership ledger')
    ledger = json.loads(ledger_bytes)
    owned = [[0, 0x400000]] + ledger['merged_union'] + [
        [0x6FF600, 0x6FF800], [0x6FF9C0, 0x6FFED0], [0xD0BE8, 0xD0BEC], [0x36E5EC, 0x36E5F0]]
    need(not any(a < LIMIT and START < z for a,z in owned), 'old plus approved6A layout disjoint even for FF tails')
    if scan:
        scanner.SPANS = ((START, LIMIT),)
        need(not scanner.inbound(before), 'strict all-alignment mirrored pointer/ARM/Thumb inbound scan without exemptions')
    return {'declared_bytes': 108, 'changed_bytes': sum(a != b for a,b in zip(before, after)),
            'reservation': [START, LIMIT], 'whole_ROM_inverse': True,
            'all_previous_main_layers_unchanged': True}


def negatives(data, before, ledger):
    def rejected(name, fn):
        try:
            fn()
        except ValueError as error:
            return {'mutation': name, 'rejected_by': str(error)}
        raise ValueError('semantic mutation survived: ' + name)
    rows = []
    for name, offset, word in (
        ('stage11 exclusion lost', 24, 0xE1A00000),
        ('difficulty3 exception lost', 36, 0xE1A00000),
        ('zero difficulty exclusion lost', 44, 0xE1A00000),
        ('progress polarity inverted', 60, u(data, START + 60) ^ 0x10000000),
        ('condition flags not restored', 68, 0xE1A00000),
    ):
        bad = bytearray(data)
        struct.pack_into('<I', bad, START + offset, word)
        rows.append(rejected(name, lambda: selector_cases(bytes(bad))))
    bad = bytearray(data); bad[0xB9E68] ^= 1
    rows.append(rejected('progress producer modified', lambda: structural(before, bad, ledger, False)))
    bad = bytearray(data); bad[START + 104] ^= 1
    rows.append(rejected('unused erased cave tail changed', lambda: structural(before, bad, ledger, False)))
    bad = bytearray(data); bad[0x629800] ^= 1
    rows.append(rejected('existing initializer changed', lambda: structural(before, bad, ledger, False)))
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('candidate', 'predecessor', 'retail', 'source'):
        p.add_argument(name, type=Path)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--layout', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    need(sha((ROOT/'tools/verify_shoot_guarded_transition_irq.py').read_bytes()) ==
         '1B83BC650DAFF3FCA643DC92789A610962910D11829C34BE690DFCEFF4600054',
         'frozen independent ARM primitive')
    for name, digest in PRIMITIVES.items():
        need(sha((ROOT/'tools'/name).read_bytes()) == digest, 'frozen inherited primitive ' + name)
    after, before, retail, source = [read(getattr(args,name)) for name in ('candidate','predecessor','retail','source')]
    need((sha(before),sha(retail),sha(source)) == (BEFORE,GBA,SOURCE), 'exact inputs')
    ledger = read(args.layout)
    manifest_bytes = read(args.manifest)
    manifest = json.loads(manifest_bytes)
    need(manifest['output_sha256'] == sha(after) and manifest['release_approved'] is False and
         manifest['complete_external_entry_approved'] is False, 'explicit development-only manifest')
    structure = structural(before, after, ledger)
    contract = source_contract(source, retail, before, after)
    count = selector_cases(after)
    for values in ((7,3,0x400),(7,0,0),(11,3,0),(255,255,0)):
        allocated_case(after, *values)
    controls = negatives(after, before, ledger)
    report = dict(schema=1, status='INDEPENDENT_EXPERIMENTAL_ENTRY_PROBE_PASS',
                  candidate_sha256=sha(after), predecessor_sha256=sha(before),
                  source_sha256=sha(source), retail_sha256=sha(retail),
                  manifest_sha256=sha(manifest_bytes), verifier_sha256=sha(Path(__file__).read_bytes()),
                  layout_ledger_sha256=sha(ledger), primitive_sha256=PRIMITIVES,
                  structure=structure, source_and_native=contract,
                  actual_selector_cases=count, actual_native_allocator_joins=4,
                  semantic_controls=controls, emulator_or_save_access=False,
                  release_approved=False, complete_external_entry_approved=False,
                  scope='Separate development probe only. No main/progression producer/forced mode edits; existing unresolved scene/gameplay lifetimes remain unresolved.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print('PASS development-only probe: '+str(count)+' selector cases;4 actual native allocations')


if __name__ == '__main__':
    main()

