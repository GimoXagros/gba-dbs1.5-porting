#!/usr/bin/env python3
"""Independent final-artifact proof for the disconnected Shoot tail.

No builder or manifest is imported. Exact instruction/CFG checks and existing
independent source inverses abstract valid native objects/resources; no CPU,
save, audio service, EEPROM, emulator or hardware is executed.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
import struct

import verify_shoot_initializer_storage as storage
import verify_shoot_other_player_binding as other
import verify_shoot_tail_resources as hud
import verify_shoot_palette_transition as palette

chain = storage.front.chain
need, sha, word, listing = chain.need, chain.sha, chain.word, chain.listing
BASE, ENTRY, WRITE, END = 0x08000000, 0x629800, 0x629878, 0x62988C
BEFORE = "66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF"
AFTER = "5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46"
SOURCE = "91EE7DCA7CF669DC17CF74BE804681668D9382FBAC5B45CDE917BC1797C14689"
CALLS = [0x085C1500, 0x085C1800, 0x085C1C00]
VERIFIERS = {
    "verify_shoot_initializer_storage": "8E8AF27A0C81F68C320B1A0461A69679264B8EC14ED941EA37761F36CE75DFD9",
    "verify_shoot_initializer_front": "39652942A0E480C7B08016F7E2B8CC93046A1163F29572490096AA3A9A3244CD",
    "verify_shoot_initializer_player_chain": "0D36464802D94FFFAD85FBBF6F40CF7AE38B8B820A0FAC0930B1B9256263B0B0",
    "verify_shoot_initializer_prefix": "408AE456D7B92FFC9DCECE4A84439475F93E020B45E1DF5BCDB07F038E13045F",
    "verify_shoot_other_player_binding": "A6D38984E9859879621D0C78EB31356D6352F3ECB8C0267703CB0CCBBB7F280B",
    "verify_shoot_tail_resources": "E5EECD5EF4C905242C672DE56BE8F9804C8D90350FEE973688CBE55053FAC76C",
    "verify_shoot_palette_transition": "C990E135FCA6531F40F4608E936DDBD0600F26072C35546625814D7925BB153B",
}
# Independently read complete instruction owners and literal/data intervals.
GUARDS = (
    (0x5C1500, 0x5C1614, "F610E2C891FABD57EEE4DB4BEEA235E1F0DBC30F94961DE074297834EDDF2C21"),
    (0x5C1800, 0x5C186C, "68C995EAA8035508E8646EA0D5DEC7A0DD245742D9A081607BAD24373EA7FC3D"),
    (0x5C1C00, 0x5C1CDC, "16645A9D5F1CFECC3AB744598F731D67E58111A3B38E3FC1828096DAB8EE59E6"),
    (0x5C2300, 0x5C2320, "F1BD23DD066344C83E9E110E97B61D75CEBC7876CE7717EC624A60B960AF7EAF"),
    (0x353304, 0x3534E0, "596381F2ED01DF36F2D2CFFE1D5570473943D847071D478FC49C6F4FA810A6F3"),
    (0x127E4, 0x1285C, "EF628791EF3580DEAD14EEC7400E44A43A696EF8012D62304FD0C7B6A45FD0C2"),
    (0x12874, 0x129C8, "1BBCE2EEE607287D2AEFA2B899D43A9C4C6890BFE5CCAF6533D8FAF6EBF2EBD4"),
    (0x132EC, 0x133A8, "10763A3BEEF3BFD0547E7680DC188F635EC3EA5D2B7D37E2A430BD7A968E3E1B"),
    (0xD15C0, 0xD15F0, "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"),
    (0x358254, 0x358264, "29922425BF9E209A3F7B1E004C1C7172892EEF080CBE93160740617AC6F4B73B"),
    (0x584940, 0x58496C, "797922C17ECE61A30D1307A67F2CB85BBF3E21203695211E1A49EAFF9DC9DFC6"),
    (0x4A80F8, 0x4A82D8, "336F628D90606B41CFF9BB6E37B8E0CEE7A5865B5F86EDE285B855E29BA2F627"),
    (0x4A82D8, 0x4A84B8, "03844B77030B7361D0068AB58AB4B01048CAC32F89FC083D453C6206536B4FFF"),
    (0xD2FD0, 0xD3050, "FED06ADACACA6083C841FD002EB50BFAAD16CD70BBDC5B7A7C476871B76C70C7"),
    (0xD3078, 0xD30A0, "6410DA9E5AF68D6D44199795D1B2DB6F1E5B7BFB8452017947C2C0BD94B431C0"),
    (0x485000, 0x48503C, "F7CAD416C7585138E2E1AF70A45848C0661B75CB3913632FF83A6430A023550F"),
    (0x4850B4, 0x48521C, "813B233AC5626FE2E323AD5D070FE70B1B41B05C13D5FAAA79D488F0960DF83A"),
    (0x353508, 0x353AA8, "24120F0AD9913D2D25574966CA13BAD4C15B0D40A008C282F603DB871BF05012"),
)
CODE = (
    (0x5C1500, 0x5C1608, (0x08353304, 0x08012874)),
    (0x5C1800, 0x5C185C, (0x080132EC,)),
    (0x5C1C00, 0x5C1CD0, ()),
    (0x353304, 0x3534B0, (0x080127E4, 0x08358254, 0x08584940, 0x080132EC, 0x080132EC)),
    (0x127E4, 0x1285C, ()),
    (0x12874, 0x129C8, (0x080D15C0, 0x080132EC, 0x080132EC)),
    (0x132EC, 0x133A8, ()),
    (0xD15C0, 0xD15EC, ()),
    (0x358254, 0x358264, ()),
    (0x584940, 0x584968, ()),
)


def source_contract(source):
    need(sha(source[0x747CF0:0x747E34]) == SOURCE, "entire source tail including original return")
    phases = [(0x73F0, 0x74A2), (0x74A2, 0x74DA), (0x74DA, 0x7534)]
    rows = [chain.source_listing(source, a, z) for a, z in phases]
    need([s for s in rows[0] if s.startswith("lcall")] == ["lcall 0x4090, 0x2e74", "lcall 0x4fff, 0x24cb"], "restoration and event call source order")
    need([s for s in rows[1] if s.startswith("lcall")] == ["lcall 0x4fff, 0x226e", "lcall 0x4fff, 0x2389"], "HUD tiles precede palette")
    need(rows[1][-1] == "mov word ptr es:[0x720], 0", "scroll clear precedes selective capture")
    need(rows[2][-11:] == ["pop ds", "pop es", "pop di", "pop si", "pop bx", "pop dx", "pop cx", "pop ax", "mov sp, bp", "pop bp", "retf "], "source tail returns, with no later snapshot")
    return [dict(start=f"{a:04X}", end=f"{z:04X}", instruction_count=len(r), instructions=r) for (a, z), r in zip(phases, rows)]


def artifact_contract(before, after):
    need(len(before) == len(after) == 0x800000, "exact eight-MiB extents")
    need(before[WRITE:END] == struct.pack("<2I", 0xE8BD4800, 0xE12FFF1E) + b"\xff" * 12, "exact old return and erased extension")
    need(struct.unpack_from("<5I", after, WRITE) == (0xEBFE5F20, 0xEBFE5FDF, 0xEBFE60DE, 0xE8BD4800, 0xE12FFF1E), "five exact independently specified tail words")
    need(listing(after, WRITE, END) == ["bl #0x85c1500", "bl #0x85c1800", "bl #0x85c1c00", "pop {fp, lr}", "bx lr"], "source-ordered calls and return, no snapshot")
    restored = bytearray(after); restored[WRITE:END] = before[WRITE:END]
    need(restored == before, "full ROM inverse; retained storage and every other byte unchanged")
    need(after[0x5C7800:0x5C8000] == b"\xff" * 0x800, "full initializer allocation remains absent")


def dependencies(image):
    for a, z, expected in GUARDS:
        need(sha(image[a:z]) == expected, f"complete dependency {a:06X}..{z:06X}")
    literals = []
    for a, z, calls in CODE:
        rows = chain.decode(image, a, z)
        need(tuple(i.operands[0].imm for i in rows if i.mnemonic == "bl") == calls, f"complete synchronous direct call graph at {a:06X}")
        for i in rows:
            if i.mnemonic == "ldr" and len(i.operands) == 2 and i.reg_name(i.operands[1].mem.base) == "pc":
                at = i.address - BASE + 8 + i.operands[1].mem.disp
                need(any(x <= at and at + 4 <= y for x, y, _ in GUARDS), "every reachable PC literal has a complete independent owner")
                literals.append(dict(instruction=f"{i.address:08X}", at=f"{at:06X}", value=f"{word(image, at):08X}"))
    need(word(image, 0xD15EC) == 0x030022F0 and word(image, 0x584968) == 0x03002310, "sound request and logical-stage literal identities")
    need(listing(image, 0x353320, 0x35332C) == ["ldr sb, [sp, #0x1c]", "cmp sb, #0xf", "bne #0x8353334"], "invalid ID15 path explicitly excluded by valid-character precondition")
    return literals


def stack_contract(image):
    proofs = {}
    for start, stop, allowed in CODE:
        rows = {i.address - BASE: i for i in chain.decode(image, start, stop)}
        pending, seen, calls, returns, deepest = [(start, 0)], set(), [], [], 0
        while pending:
            at, depth = pending.pop()
            if (at, depth) in seen: continue
            seen.add((at, depth)); need(at in rows and len(seen) < 1000, "bounded local CFG")
            i = rows[at]
            if i.mnemonic == "push" or (i.mnemonic == "stmdb" and i.op_str.startswith("sp!,")):
                depth += 4 * (len(i.operands) - (i.mnemonic == "stmdb"))
            elif i.mnemonic == "pop": depth -= 4 * len(i.operands)
            elif i.mnemonic == "str" and i.op_str.endswith(", [sp, #-4]!"): depth += 4
            elif i.mnemonic == "add" and i.op_str.startswith("sp, sp, #"): depth -= i.operands[2].imm
            else: need("sp" not in [i.reg_name(r) for r in i.regs_access()[1]], "known stack mutation")
            need(0 <= depth <= 256, "nonnegative bounded local stack"); deepest = max(deepest, depth)
            if i.mnemonic == "bl": calls.append((at, i.operands[0].imm - BASE, depth))
            elif i.mnemonic.startswith("bx"):
                need(i.op_str == "lr" and depth == 0, "every return balances its stack")
                returns.append(at)
                if i.mnemonic == "bx": continue
            elif i.mnemonic.startswith("b") and i.mnemonic != "bic":
                pending.append((i.operands[0].imm - BASE, depth))
                if i.mnemonic == "b" or at == 0x353328: continue
            pending.append((at + 4, depth))
        need(returns, "each local function has a return")
        proofs[start] = dict(local_max_bytes=deepest, calls=sorted(set(calls)), returns=sorted(set(returns)), states=len(seen))
    def total(start):
        p = proofs[start]
        return max([p["local_max_bytes"]] + [depth + total(target) for _, target, depth in p["calls"]])
    for start, stop, _ in CODE[:3]:
        need(word(image, start) == 0xE92D5FFF and word(image, stop - 8) == 0xE8BD5FFF, "all three phase frames restore r0-r12 and LR")
    for start, stop, _ in CODE:
        for i in chain.decode(image, start, stop):
            if "fp" in [i.reg_name(r) for r in i.regs_access()[1]]:
                need(i.mnemonic in ("pop", "mov") and (i.mnemonic == "pop" or i.op_str == "fp, #0"), "native zero register retained")
    return dict(functions={f"{BASE + a:08X}": p for a, p in proofs.items()},
                synchronous_tail_stack_bytes=8 + max(total(a - BASE) for a in CALLS),
                asynchronous_and_full_entry_bound_claimed=False, excluded_character=15)


def abi_contract(image):
    cases = 0
    for flags, sp, fp, lr in itertools.product(range(16), (0x03007EFC, 0x03007F00), (0, 1, 0x80000000, 0xFFFFFFFF), (0x0833FD1C, 0x0833FD1D)):
        regs = [0x12340000 + n * 0x1111 for n in range(15)]
        regs[11], regs[13], regs[14] = fp, sp, lr
        initial = tuple(regs); saved = (fp, lr); regs[11], regs[13] = 0, sp - 8
        order = []
        for at in range(WRITE, END, 4):
            value = word(image, at)
            need(value >> 28 == 14, "tail independent of incoming flags")
            if value >> 24 == 0xEB:
                need(regs[11] == 0 and regs[13] == sp - 8, "post-storage tail frame and zero-register ABI")
                order.append(chain.prefix.target(at, value)); regs[14] = BASE + at + 4
                flags ^= 15  # Each verified all-register phase may change flags.
            elif value == 0xE8BD4800: regs[11], regs[14] = saved; regs[13] += 8
            elif value == 0xE12FFF1E: need(tuple(regs) == initial, "all registers, SP and return ISA bit restored")
            else: raise ValueError("instruction outside exact tail ABI model")
        need(order == CALLS, "other player, HUD, selective palette, then return")
        cases += 1
    return dict(cases=cases, incoming_NZCV_states=16, stack_modulo8=[0, 4], preserved="r0-r12,LR,SP", flags="clobbered", return_ISA_states=2)


def scan(data, origin=0):
    hits = []
    def inside(value): return ENTRY <= (value & 0x01FFFFFF) < END and (value & 0xFE000000) in (BASE, 0x0A000000, 0x0C000000)
    for alignment in range(4):
        stop = len(data) - ((len(data) - alignment) % 4)
        for n, (value,) in enumerate(struct.iter_unpack("<I", data[alignment:stop])):
            if inside(value): hits.append(("pointer", origin + alignment + n * 4, value))
    for n, (value,) in enumerate(struct.iter_unpack("<I", data[:len(data) // 4 * 4])):
        at, pc = origin + n * 4, BASE + origin + n * 4 + 8
        if value & 0x0E000000 == 0x0A000000 and inside(chain.prefix.target(at, value)):
            hits.append(("ARM branch", at, chain.prefix.target(at, value)))
        if value & 0x0F7F0000 in (0x051F0000, 0x055F0000):
            target = pc + (value & 0xFFF) * (1 if value & 0x800000 else -1)
            if inside(target): hits.append(("ARM literal", at, target))
        if value & 0x0FFF0000 in (0x028F0000, 0x024F0000):
            imm, rotate = value & 255, ((value >> 8) & 15) * 2
            if rotate: imm = ((imm >> rotate) | (imm << (32 - rotate))) & 0xFFFFFFFF
            target = pc + (imm if value & 0x01E00000 == 0x00800000 else -imm)
            if inside(target): hits.append(("ARM ADR", at, target))
    for n, (value,) in enumerate(struct.iter_unpack("<H", data[:len(data) // 2 * 2])):
        at, pc = origin + n * 2, BASE + origin + n * 2 + 4
        if value & 0xF800 in (0x4800, 0xA000):
            target = (pc & ~3) + (value & 255) * 4
            if inside(target): hits.append(("Thumb literal/ADR", at, target))
        if value & 0xF800 == 0xE000:
            imm = value & 0x7FF; target = pc + 2 * (imm - (0x800 if imm & 0x400 else 0))
            if inside(target): hits.append(("Thumb B", at, target))
        if value & 0xF000 == 0xD000 and value & 0x0F00 < 0x0E00:
            imm = value & 255; target = pc + 2 * (imm - (256 if imm & 128 else 0))
            if inside(target): hits.append(("Thumb conditional B", at, target))
        if value & 0xF800 == 0xF000 and n * 2 + 4 <= len(data):
            tail = struct.unpack_from("<H", data, n * 2 + 2)[0]
            if tail & 0xF800 in (0xF800, 0xE800):
                imm = value & 0x7FF; target = pc + ((imm - (0x800 if imm & 0x400 else 0)) << 12) + ((tail & 0x7FF) << 1)
                if tail & 0xF800 == 0xE800: target &= ~3
                if inside(target): hits.append(("Thumb BL/BLX", at, target))
    return hits


def ownership(image, final, hits):
    pop = END - 8 if final else WRITE
    expected = [("ARM branch", 0x629830, 0x08629848), ("ARM branch", 0x629858, 0x08629870),
        ("Thumb literal/ADR", 0x629510, 0x08629874), ("Thumb literal/ADR", 0x629620, 0x08629870),
        ("Thumb literal/ADR", ENTRY, BASE + ENTRY + 4), ("Thumb conditional B", 0x62981C, 0x08629830),
        ("Thumb conditional B", 0x629870, 0x08629884),
        ("Thumb literal/ADR", pop, BASE + pop + 4)]
    need(hits == expected, "only retained internal references and positively owned ARM halfwords")
    for a, z, digest in storage.OWNER_GUARDS: need(sha(image[a:z]) == digest, "external false-ADR instruction owners")
    need(word(image, ENTRY) == 0xE92D4800 and word(image, pop) == 0xE8BD4800 and word(image, 0x62981C) == 0xE24DD008, "exact local false Thumb owners")
    need(word(image, 0x629870) == 0xE28DD008 and listing(image, 0x629870, 0x629874) == ["add sp, sp, #8"], "new-range Thumb-looking D008 is retained ARM buffer cleanup")
    return hits


def negatives(before, after, source):
    rejected = []
    def reject(label, check):
        try: check()
        except (ValueError, KeyError, struct.error) as error: rejected.append(dict(case=label, reason=str(error)))
        else: raise ValueError("accepted negative control: " + label)
    for at in (*range(WRITE, END), ENTRY, WRITE - 1, END, 0x5C7800):
        wrong = bytearray(after); wrong[at] ^= 1
        reject(f"artifact byte {at:06X}", lambda: artifact_contract(before, wrong))
    for a, z, _ in GUARDS:
        for at in (a, z - 1):
            wrong = bytearray(after); wrong[at] ^= 1
            reject(f"dependency boundary {at:06X}", lambda: dependencies(wrong))
    for at in (0x747CF0, 0x747DA1, 0x747DA2, 0x747DD9, 0x747DDA, 0x747E33):
        wrong = bytearray(source); wrong[at] ^= 1
        reject(f"source boundary {at:06X}", lambda: source_contract(wrong))
    for label, targets in (("reversed phase order", CALLS[::-1]), ("snapshot instead of selective capture", CALLS[:2] + [0x085C1900])):
        wrong = bytearray(after)
        for n, target in enumerate(targets):
            at = WRITE + n * 4; struct.pack_into("<I", wrong, at, 0xEB000000 | (((target - BASE - at - 8) // 4) & 0xFFFFFF))
        reject(label, lambda: abi_contract(wrong))
    wrong = bytearray(after); struct.pack_into("<I", wrong, 0x129B0, 0xEB000000)
    reject("callee after former truncated12960 boundary", lambda: dependencies(wrong))
    for label, at, value in (("tail fails to restore fp", END - 8, 0xE8BD4000), ("tail conditional call", WRITE, 0x0BFE5F20)):
        wrong = bytearray(after); struct.pack_into("<I", wrong, at, value)
        reject(label, lambda: abi_contract(wrong))
    wrong = bytearray(after); struct.pack_into("<I", wrong, 0x5C1540, 0xE28DD008)
    reject("other-player argument stack leak", lambda: stack_contract(wrong))
    controls = 0
    for mirror, offset, alignment in itertools.product((BASE, 0x0A000000, 0x0C000000), (0, 1, 127, 128, 139), range(4)):
        sample = bytearray(b"\xff" * 64); struct.pack_into("<I", sample, alignment, mirror + ENTRY + offset)
        need(any(h[0] == "pointer" for h in scan(sample)), "scanner covers complete old/new allocation and mirrors"); controls += 1
    for value in (0xEA00003E, 0xEB00003E, 0xE59F80F8, 0xE28F00F8):
        need(scan(struct.pack("<I", value) + b"\xff" * 60, ENTRY - 0x100), "ARM scanner control"); controls += 1
    for value in (0x483F, 0xA03F, 0xE07E, 0xD07E):
        need(scan(struct.pack("<H", value) + b"\xff" * 62, ENTRY - 0x100), "Thumb scanner control"); controls += 1
    for value in (0xF87E, 0xE87E):
        need(scan(struct.pack("<HH", 0xF000, value) + b"\xff" * 60, ENTRY - 0x100), "Thumb BL/BLX scanner control"); controls += 1
    return rejected, controls


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("before", "after", "gba", "old", "source", "output"): parser.add_argument(name, type=Path)
    args = parser.parse_args(); names = ("before", "after", "gba", "old", "source")
    need(all(getattr(args, n).suffix.lower() == ".gba" for n in names[:3]) and all(getattr(args, n).suffix.lower() == ".wsc" for n in names[3:]), "ROM-only inputs")
    need(args.output.suffix.lower() == ".json" and args.output.resolve() not in {getattr(args, n).resolve() for n in names}, "distinct JSON output")
    before, after, gba, old, source = (getattr(args, n).read_bytes() for n in names)
    need(tuple(map(sha, (before, gba, old, source))) == (BEFORE, *chain.prefix.ORIGINALS), "exact storage predecessor and three immutable originals")
    for name, digest in VERIFIERS.items(): need(sha(Path(__file__).with_name(name + ".py").read_bytes()) == digest, "frozen independent verifier " + name)
    artifact_contract(before, after)
    src, literals = source_contract(source), dependencies(after)
    other.check_phase(after); physics = other.check_consumers(gba, source, after)
    hud.check_phases(after); hud_proof = hud.check_consumers(after, source)
    palette.check_code(after); palette.check_consumers(after, source); color = palette.check_algebra()
    stack, abi = stack_contract(after), abi_contract(after)
    before_refs, after_refs = ownership(before, False, scan(before)), ownership(after, True, scan(after))
    rejected, controls = negatives(before, after, source)
    need(sha(after) == AFTER, "final identity after independent semantic and negative checks")
    report = dict(schema=1, status="PASS", kind="independent-shoot-initializer-tail-chain-verification",
        input_sha256=sha(before), output_sha256=sha(after), original_sha256=list(chain.prefix.ORIGINALS),
        verifier_dependencies=VERIFIERS, inherited_storage_proof_reexecuted=False,
        source_sha256=SOURCE, source=src, source_end_exclusive="4090:7534", native_entry="08629800",
        write_half_open=["629878", "62988C"], declared_bytes=20, appended_bytes=12,
        changed_bytes=sum(a != b for a, b in zip(before, after)), full_inverse=True,
        first_120_entry_bytes_retained=True, call_order=[f"{a:08X}" for a in CALLS], ABI=abi, stack=stack,
        dependencies=[dict(start=f"{a:06X}", end=f"{z:06X}", sha256=h) for a, z, h in GUARDS],
        literal_owners=literals, physics_records=physics, HUD=hud_proof, palette_algebra=color,
        before_references=before_refs, after_references=after_refs, external_callers_added=0,
        negative_controls=rejected, scanner_negative_controls=controls, negative_control_count=len(rejected) + controls,
        full_initializer_absent=True, snapshot_added=False, new_persistent_RAM_bytes=0,
        preconditions=["Inherited front/storage contracts, initialized functional EEPROM and valid aligned stack.",
            "Valid other-player object, character ID0..14, slot0..1, initialized resources and exclusively owned display/scene.",
            "Earlier snapshot085C1900 must precede destructive source1073 colors; canonical mirror ownership remains exclusive through source1331.",
            "Existing dynamic P0/P1/P2/P4 payloads and native asynchronous sound/task lifetimes remain inherited contracts."],
        limits=["Static artifact and bounded models; no emulator, game, EEPROM, save, audio or hardware execution.",
            "Synchronous direct call graph and PC literals closed; no complete dynamic payload/async consumer or IRQ stack bound.",
            "Source body endpoint does not install full initializer, controller/scene caller, snapshot or terminal/camera lifecycle.",
            "Finite reference scan excludes enumerated static patterns; computed entry exclusion is not claimed."],
        input_ROMs_written=False, supplied_save_accessed=False)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", output_sha256=sha(after), ABI_cases=abi["cases"], negative_control_count=report["negative_control_count"])))


if __name__ == "__main__":
    main()
