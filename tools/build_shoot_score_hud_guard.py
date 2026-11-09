#!/usr/bin/env python3
"""Separate experimental D0 component: omit the source stage11 score HUD."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from analyze_waterfall_third_pattern import no_inbound, branch_target
from verify_shoot_static_companion_clear import Machine, listing
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

ROOT = Path(__file__).resolve().parents[1]
BASE, ENTRY, HOOK, CAVE = 0x08000000, 0x373ED0, 0x373ED8, 0x6FF400
BODY, JOIN, RETURN = 0x08373EE0, 0x08373EDC, 0x09000000
INPUT = 'D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C'
GBA = '996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED'
SOURCE = 'C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7'
DEPENDENCIES = {
    'analyze_waterfall_third_pattern.py': 'DB327A22961631CBEE0CEB725525BFBA06775115313C0F34504AF1D9CAE174A3',
    'verify_shoot_static_companion_clear.py': 'CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943',
}
PINS = (
    (ENTRY, 0x373F68, '6479A80848E81976F2FDE192F233364FC663078DA433B9124B7DA8CCF8EE3B4A'),
    (0x373538, 0x373544, '5A05556D2CF0F5B75168FC3B4235518380491EE48E5357A649D6445212B7D31C'),
    (0x3735A4, 0x3735B0, '9B14870E7D3C45DA2353F6D94805C93BED5C4E85A6E3489ED73B8CA02EDDFBC4'),
    (0x37364C, 0x373660, '5F989200CD5E31E86953CAB8F50D369839F8095EF7D26332F0D937BA395B505D'),
)


def need(ok, label):
    if not ok:
        raise ValueError(label)


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def branch(at, target):
    delta = target - at - 8
    need(delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25), 'ARM branch range')
    return 0xEA000000 | ((delta // 4) & 0xFFFFFF)


def source_contract(before, gba, source):
    for start, end, digest in PINS:
        need(sha(before[start:end]) == digest and before[start:end] == gba[start:end], 'retained native HUD/caller pin')
    need(sha(source[0x78768C:0x7876F5]) == '8119592B6032FC462770AE561830DF57F639BDA61A2F38408EEEB09013130224', 'complete source score HUD pin')
    ins = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source[0x78769E:0x7876AC], 0x78769E))
    need([(i.mnemonic, i.op_str) for i in ins] == [
        ('cmp', 'byte ptr [0x5c], 7'), ('je', '0x7876ec'),
        ('cmp', 'byte ptr [0x5c], 0xb'), ('je', '0x7876ec')], 'source exact stage7/11 exclusion')
    need(source[0x7876EC:0x7876F5] == bytes.fromhex('9D1F075E5B5A5958CB'), 'source shared flags/register restore and far return')
    need(listing(before, HOOK, 8) == ['cmp sb, #7', 'bxeq lr'], 'displaced compare and retained return')
    need(before[0x37DB3C:0x37DB48] == bytes.fromhex('00C09FE51CFF2FE1E9D53708') and
         before[0x37D5E8:0x37D5EC] == bytes.fromhex('06DF7047'), 'retained thunk to BIOS Div SWI6')
    callers = []
    for index, (word,) in enumerate(struct.iter_unpack('<I', before)):
        if word & 0x0E000000 == 0x0A000000 and branch_target(index * 4, word) == BASE + ENTRY:
            callers.append((index * 4, word))
    need(callers == [(0x373538, 0xEB000264), (0x3735A4, 0xEB000249), (0x37364C, 0xEB00021F)], 'all aligned direct HUD callers')
    need(before.find(struct.pack('<I', BASE + ENTRY)) == -1, 'no unaligned absolute HUD pointer')
    # Non11 NZCV is preserved at JOIN. Stage11's new return is dead at these callers.
    for start in (0x37353C, 0x3735A8):
        need(listing(before, start, 8) == ['ldm sp!, {lr}', 'bx lr'], 'HUD caller immediately returns without flag consumer')
    need(listing(before, 0x373650, 16) == ['ldr r8, [pc, #0xc8]', 'ldrh sb, [r8, #2]',
         'cmp sb, #2', 'bne #0x83736bc'], 'battle caller overwrites all NZCV before conditional branch')
    return {'source_return_epilogue': 0x7876EC, 'source_far_return': 0x7876F4, 'source_restores_flags': True,
            'direct_callers': [a for a, _ in callers],
            'non11_flags': 'Exact original CMP7 at existing BXEQ; stage11 caller tails do not consume HUD flags'}


def fixture(data, stage, seed=0, flags=0x10, owner=0, score=999):
    m = Machine(data, seed, flags=flags)
    m.r[14] = RETURN
    for address, value, size in ((0x0300231E, stage, 1), (0x03004528, owner, 1),
        (0x0300489C, 0x02010018, 4), (0x030048A0, 0x02010248, 4),
        (0x0201007E, score if owner == 0 else 17, 2),
        (0x020102AE, score if owner == 1 else 23, 2), (0x03004502, 2, 2)):
        m.put(address, value, size)
    def divide(machine):
        # The unchanged native thunk invokes BIOS SWI6; only this service is modeled.
        need(machine.r[1] in (10, 100) and 0 <= machine.r[0] <= 999, 'bounded positive BIOS Div arguments')
        quotient, remainder = divmod(machine.r[0], machine.r[1])
        machine.r[0], machine.r[1], machine.r[3], machine.r[12] = quotient, remainder, quotient, 0x0837D5E9
    m.services[0x0837DB3C] = divide
    return m


def semantics(before, after):
    entries = 0
    for stage in range(256):
        for flags in range(16):
            old = fixture(before, stage, flags % 3, (flags << 28) | 0xD3)
            new = fixture(after, stage, flags % 3, (flags << 28) | 0xD3)
            old_stop = old.run(BASE + ENTRY, {BODY, RETURN})
            new_stop = new.run(BASE + ENTRY, {BODY, RETURN})
            need(new_stop == (RETURN if stage in (7, 11) else BODY), 'exact source early-return predicate')
            need(old.r[:15] == new.r[:15] and old.reads == new.reads and not new.writes, 'entry registers/reads and no writes')
            if stage != 11:
                need(old_stop == new_stop and old.cpsr == new.cpsr, 'non11 original flags and route')
            entries += 1
    runs = 0
    score_cases = (0, 1, 9, 10, 99, 100, 998, 999, 1000, 65535)
    cases = [(stage, stage % 2, score_cases[stage % len(score_cases)], stage % 16) for stage in range(256)]
    cases += [(stage, owner, score, flags) for stage in (0, 7, 11, 255)
              for owner in (0, 1) for score in score_cases for flags in (0, 5, 10, 15)]
    for stage, owner, score, flags in cases:
        old = fixture(before, stage, flags % 3, (flags << 28) | 0xD3, owner, score)
        new = fixture(after, stage, flags % 3, (flags << 28) | 0xD3, owner, score)
        old.run(BASE + ENTRY, {RETURN}); new.run(BASE + ENTRY, {RETURN})
        if stage != 11:
            need(old.r[:15] == new.r[:15] and old.cpsr == new.cpsr and old.reads == new.reads and
                 old.writes == new.writes and old.calls == new.calls, 'complete non11 HUD exact registers/flags/ordered effects')
        writes = [(a, v, n) for a, v, n in new.writes if 0x06000000 <= a < 0x06018000]
        if stage in (7, 11):
            need(not new.writes and not new.calls and new.reads == [(0x0300231E, 1)], 'excluded stages touch neither actor, stack, BIOS nor VRAM')
        else:
            value = min(score, 999)
            digits = (value // 100, value // 10 % 10, value % 10)
            need(writes == [(0x0600D804 + 2 * k, 0x73EF + v, 2) for k, v in enumerate(digits)], 'exact retained score digits/clamp/VRAM halfwords')
        runs += 1
    callers = 0
    for call in (0x373538, 0x3735A4, 0x37364C):
        for stage in (0, 7, 11):
            for flags in range(16):
                old = fixture(before, stage, 1, (flags << 28) | 0xD3)
                new = fixture(after, stage, 1, (flags << 28) | 0xD3)
                for m in (old, new):
                    m.put(m.r[13], RETURN)
                stop = 0x0837365C if call == 0x37364C else RETURN
                old.run(BASE + call, {stop}); new.run(BASE + call, {stop})
                if stage != 11:
                    need(old.r[:15] == new.r[:15] and old.cpsr == new.cpsr and old.writes == new.writes, 'real BL caller preserves non11 behavior')
                else:
                    need(new.r[:8] == old.r[:8] and new.r[11] == old.r[11] and new.r[13:15] == old.r[13:15], 'real stage11 caller preserved live registers/SP/LR')
                    if call == 0x37364C:
                        need(new.cpsr == old.cpsr, 'actual battle caller kills differing HUD flags')
                    need(not new.writes, 'stage11 callers have no HUD writes')
                callers += 1
    return {'actual_ARM_entry_cases': entries, 'complete_ARM_HUD_cases': runs,
            'actual_BL_caller_cases': callers, 'division_boundary': 'Retained native ARM thunk/Thumb SWI6 bytes pinned; BIOS positive quotient/remainder service modeled, no BIOS/hardware execution',
            'all_256_stages': True, 'all_16_entry_NZCV': True}


def build(before, gba, source):
    need((sha(before), sha(gba), sha(source)) == (INPUT, GBA, SOURCE), 'exact D0 experimental predecessor and originals')
    for name, digest in DEPENDENCIES.items():
        need(sha((ROOT / 'tools' / name).read_bytes()) == digest, 'frozen helper ' + name)
    proof = source_contract(before, gba, source)
    ledger_bytes = (ROOT / 'records/shoot-guarded-transition-layout-20261109.json').read_bytes()
    irq_bytes = (ROOT / 'build/shoot-guarded-transition-20261109/component-c.json').read_bytes()
    need(sha(ledger_bytes) == '89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33', 'complete ownership ledger pin')
    need(sha(irq_bytes) == 'D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C', 'v73 IRQ reservations pin')
    ledger, irq = json.loads(ledger_bytes), json.loads(irq_bytes)
    need(ledger['normalized_interval_count'] == 1394 and ledger['layer_count'] == 70, 'all existing layout intervals')
    owned = [[0, 0x400000]] + ledger['merged_union'] + irq['reservations'] + [
        [0xD0BE8, 0xD0BEC], [0x36E5EC, 0x36E5F0], [0x33FD04, 0x33FD08], [0x6FF380, 0x6FF400]]
    need(0x6FF400 <= CAVE and CAVE + 16 <= 0x6FF5F0, 'bounded approved search window')
    need(not any(lo < CAVE + 16 and CAVE < hi for lo, hi in owned), 'new cave disjoint from complete reservations including erased tails')
    need(before[CAVE:CAVE + 16] == b'\xff' * 16, 'whole new cave erased')
    ownership = no_inbound(before, [(CAVE, CAVE + 16)])
    need(not ownership['classified_instruction_interiors'], 'strict zero exemptions')
    code = struct.pack('<4I', 0xE359000B, 0x012FFF1E, 0xE3590007, branch(CAVE + 12, JOIN - BASE))
    writes = [(HOOK, struct.pack('<I', branch(HOOK, CAVE))), (CAVE, code)]
    after = bytearray(before)
    for address, data in writes:
        after[address:address + len(data)] = data
    def expected_write(candidate):
        need(len(candidate) == len(before), 'unchanged ROM size')
        inverse = bytearray(candidate)
        for address, data in writes:
            need(candidate[address:address + len(data)] == data, 'exact expected hook/code bytes')
            inverse[address:address + len(data)] = before[address:address + len(data)]
        need(inverse == before, 'whole-ROM inverse preserves every other byte')
    expected_write(after)
    checks = semantics(before, bytes(after))
    negatives = []
    for label, at in [('hook', HOOK), ('stage11 compare', CAVE), ('retained stage7 compare', CAVE + 8),
                      ('join branch', CAVE + 12), ('adjacent unowned byte', CAVE + 16),
                      ('entry selector', 0x6FF380), ('progress producer', 0xB9E68), ('VRAM store', 0x373F20)]:
        bad = bytearray(after); bad[at] ^= 1
        try:
            expected_write(bad)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError('ineffective expected-write negative ' + label)
    # Semantic control precedes expected-byte checking: compare10 incorrectly retains11.
    bad = bytearray(after); struct.pack_into('<I', bad, CAVE, 0xE359000A)
    m = fixture(bytes(bad), 11)
    need(m.run(BASE + ENTRY, {BODY, RETURN}) == BODY, 'semantic stage mutation must demonstrably fail source predicate')
    negatives.append('semantic wrong-stage predicate')
    return bytes(after), dict(schema=1, status='EXPERIMENTAL_STAGE11_SCORE_HUD_GUARD_PASS',
        input_sha256=INPUT, output_sha256=sha(after), gba_sha256=GBA, source_sha256=SOURCE,
        source_contract=proof, checks=checks, reservations=[[CAVE, CAVE + 16]], ownership=ownership,
        layout_ledger_sha256=sha(ledger_bytes), IRQ_manifest_sha256=sha(irq_bytes),
        writes=[dict(raw=a, bytes=len(d), before=before[a:a + len(d)].hex().upper(), after=d.hex().upper()) for a, d in writes],
        declared_bytes=20, changed_bytes=sum(x != y for x, y in zip(before, after)), whole_ROM_inverse=True,
        negative_controls_rejected=negatives, new_RAM_or_task=False, new_storage_writes=False,
        first_run_D0_unchanged=True, runtime_executed=False, independent_QA_pending=True,
        complete_entry_ending_E5_claim=False,
        dependencies={**DEPENDENCIES, Path(__file__).name: sha(Path(__file__).read_bytes())})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('input', 'gba', 'source', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    paths = (args.input, args.gba, args.source, args.output, args.manifest)
    need(len({p.resolve() for p in paths}) == len(paths), 'distinct paths')
    need(not args.output.exists() and not args.manifest.exists(), 'fresh outputs only')
    result, report = build(args.input.read_bytes(), args.gba.read_bytes(), args.source.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_bytes((json.dumps(report, indent=2) + '\n').encode('utf8'))
    print('[EXPERIMENTAL ONLY] ' + report['output_sha256'])


if __name__ == '__main__':
    main()
