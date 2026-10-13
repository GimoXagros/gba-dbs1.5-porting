#!/usr/bin/env python3
"""Independent ROM-bound verifier; no generator imports or CPU execution."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "vendor"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from capstone.arm_const import (ARM_INS_ADD, ARM_INS_AND, ARM_INS_B, ARM_INS_BIC,
                               ARM_INS_BL, ARM_INS_BX, ARM_INS_CMP, ARM_INS_LDR,
                               ARM_INS_LDRB, ARM_INS_LDRH, ARM_INS_LSL, ARM_INS_LSR,
                               ARM_INS_MOV, ARM_INS_ORR, ARM_INS_POP, ARM_INS_PUSH, ARM_INS_RSB,
                               ARM_INS_STR, ARM_INS_STRB, ARM_INS_STRH, ARM_INS_SUB,
                               ARM_INS_TST)

BASE = 0x08000000
BEFORE = "00C4A8F4710BC0E2F4A31810CDD6FE2610D9670D9A989273162ADF33167211E7"
AFTER = "F793AB2389B6F03812717709C5FECB05F9406451F79F5CF5C249C2FFE2EF4CEF"
ORIGINALS = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "wsc10": "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735",
    "wsc15": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
CODE = (
    (0x5E7000, 460, 424, "649BFCFB88655584AA49E71AE4C91D6E732C740943BEAFE30A375506B8033579",
     (0x03004710, 0x0300450A, 0x03002388, 0x0300456E, 0x030012B9,
      0x0600F240, 0x0600F000, 0x03002338, 0x0300456C), {0x08013DD4, 0x08001064}),
    (0x5E7400, 328, 292, "019D8C1BCE934C7D91CDC31E8243C7F48A4D26AEC0BAF4BB1E558E3D12C08CDD",
     (0x0300456C, 0x0300450A, 0x030012E0, 0x085E7800, 0x03004D44,
      0x08586A00, 0x03004710, 0x03004506, 0x04000200),
     {0x08000FEC, 0x08000F2C, 0x08000F44, 0x08000F5C, 0x08000F74,
      0x08000CE8, 0x08000CFC, 0x08000C10, 0x080C9000}),
    (0x5E7800, 100, 92, "D96879AAA481F9C9B8067329084912D66C34884C81BE20D86DC9CC11DB2F0A91",
     (0x03004D48, 0x08586A00), {0x08000CD8, 0x08000CF8, 0x08000C10}),
)
ALLOWED = {ARM_INS_ADD, ARM_INS_AND, ARM_INS_B, ARM_INS_BIC, ARM_INS_BL,
           ARM_INS_BX, ARM_INS_CMP, ARM_INS_LDR, ARM_INS_LDRB, ARM_INS_LDRH,
           ARM_INS_LSL, ARM_INS_LSR, ARM_INS_MOV, ARM_INS_ORR, ARM_INS_POP,
           ARM_INS_PUSH, ARM_INS_RSB, ARM_INS_STR, ARM_INS_STRB, ARM_INS_STRH, ARM_INS_SUB,
           ARM_INS_TST}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(test: bool, message: str) -> None:
    if not test:
        raise ValueError(message)


def target(site: int, word: int) -> int:
    delta = word & 0xFFFFFF
    if delta & 0x800000:
        delta -= 0x1000000
    return site + 8 + 4 * delta


def proof_sources(old: bytes, source: bytes, gba: bytes) -> dict:
    # Independent fixed byte populations and literal decoding establish the
    # native owner, without using the generated mapping manifest.
    guards = ((old, 0x3B5B21, 0x3B5B79, "61E02649780D78BDB36373804D772E547D38CE8914AF31DEBC2F16A97226F6E9"),
              (old, 0x3B6B34, 0x3B6B5F, "C7A7F22468472F2C7EB61955CE9F78728950DEE23F0F87951CBDB46101A8ED27"),
              (gba, 0x893F0, 0x89450, "22012BA7FC417397A7225FCC2968CA7C35813993E128299B1F6B161983032937"),
              (gba, 0x8AD00, 0x8AD2C, "3D0B5A48B61EFF723D7596A9452A34450AA11D6C99628853358A6C80390EC87C"),
              (source, 0x75FADA, 0x75FE03, "E4B0AC7FCC0253B9BE437C951368C3F222FDD867583CE723637C91EC1AC9FA93"),
              (source, 0x77387A, 0x7738C6, "E816020DE72D5E59C1111D761C865133D097C8B9C36DA41E5EE08842477EAA04"),
              (old, 0x3BF8E1, 0x3BF923, "E8DE9C31909E2AA74C1720C4AF6CFE2524D57784C3F0F647F5982837A669A00A"),
              (old, 0x3BFB6A, 0x3BFB9F, "F76E677DB04D1F63CCF6697B00CA3D0FFB507B0F9DFDDAE542AC821DFBB84A54"),
              (gba, 0xC90F0, 0xC9164, "C129DCDEB1F40C76AFE27CC964C5568B03B775C4FB4E174802E885E0CD24FC4E"),
              (gba, 0xC92C8, 0xC9328, "77C754F8CBBB2BFAB7840074E1EF467D27DA00624104884884C238D25821E196"),
              (old, 0x39072C, 0x3907D5, "12D365B246D5459A8B9F60F10CFAB557F2831FDE7EFC452EB99FA6DC144CE9C2"),
              (gba, 0xC97B8, 0xC9814, "9A77CD62FCCEA58C61D50BF51B23C836647BD1B70CE6CA5B1B81FC7A72999089"),
              (gba, 0xC98EC, 0xC9900, "DE2BCD70F36F8EFCAA8C26FE6BEADBC2A115A5339DDC528A6C565410FEC1B335"),
              (gba, 0xF2C, 0xFBC, "017E9D723C55F2A21663EFE680F9C2718D5DF2BE43A97EFE7F48B28E5F4CFCC5"),
              (old, 0x3BC801, 0x3BC898, "5A35E1EE297FFB43480DA8B49182B1779CA29D1C7F8B0DCA3272773ADE69FB45"),
              (gba, 0xD0B24, 0xD0BC0, "BEB7F435B56D93A439220C563B84C8F268D5EBCC3BC9C49E3600F05EDBBB8463"))
    for rom, a, b, expected in guards:
        need(sha(rom[a:b]) == expected, f"source/native oracle {a:X}")
    need(struct.unpack_from("<4I", gba, 0x89730) == (0x03004710, 0x7FFF, 0x1F3F, 0x23D), "first native owner/color oracle")
    need(struct.unpack_from("<4I", gba, 0x8ADAC) == (0x03004710, 0x7FFF, 0x1F3F, 0x23D), "second native owner/color oracle")
    need(gba[0x1030:0x1038] == bytes.fromhex("1E1E1F1F1C1D1B1B"), "native map-index table")
    need(0x06000000 + gba[0x1031] * 0x800 == 0x0600F000, "source0800 map projection")
    need(old[0x390774:0x390776] == bytes.fromhex("E612") and old[0x39077D:0x39077F] == bytes.fromhex("E613"), "source BG0 ports12/13")
    need(target(0xC97CC, struct.unpack_from("<I", gba, 0xC97CC)[0]) == 0xF5C and target(0xC97E0, struct.unpack_from("<I", gba, 0xC97E0)[0]) == 0xF74, "paired BG0 native helpers")
    need(old[0x39079F:0x3907A1] == bytes.fromhex("E710"), "source other layer ports10/11")
    need(target(0xC9808, struct.unpack_from("<I", gba, 0xC9808)[0]) == 0xF2C and target(0xC9810, struct.unpack_from("<I", gba, 0xC9810)[0]) == 0xF44, "paired other-layer native helpers")
    need(struct.unpack_from("<I", gba, 0xFAC)[0] == 0x030012B9, "logical source IN11 shadow")
    need(source[0x75FC98:0x75FC9C] == bytes.fromhex("268B450A"), "source0DEC really reads DI+A")
    need(source[0x75FC95:0x75FC98] == bytes.fromhex("BBEA00"), "source0DEC initializes BX only")
    need(source[0x750F25:0x750F3C] == bytes.fromhex("501E9CB8000C8ED8FF1E5E37E4B60C10E6B69D1F58FBCF"), "IRQ dispatcher live-DI evidence")
    return {"owner": "0300:00EA -> 03004710, two independent commercial consumers",
            "source_owner_bytes_proved": 20, "used_bytes": 14,
            "map": "source0800..1000 -> native0600F000..F800",
            "scanline_bridge": "two commercial source OUT03 producer/consumer pairs establish native compare=(source+8)&255",
            "scroll_bridge": "source ports12/13 -> F5C/F74; ports10/11 -> F2C/F44; IN11 -> byte030012B9",
            "unresolved_dependency": "0DEC reads ES:[DI+A]; dispatcher and previous callback do not establish DI=EA; interrupted main-program DI/timing remains unproved"}


def finite_checks() -> dict:
    # Source 8-bit DEC and target reconstruction retain AH even at AL=0.
    for value in range(65536):
        ax = (value & 0xFF00) | (((value & 255) - 1) & 255)
        r1 = (value - 1) & 255
        r0 = (value & ~255) | r1
        need(ax == r0 and ((ax & 255) == 0) == (r1 == 0), "display AL decrement")
    # Source AX/BL operations matter: the explicit 8-bit additions discard
    # carry before signed BX>>3; state8 is zero-extended IN-port11, so BH=0.
    rows = 0
    for base in range(256):
        for count in range(0, 256, 8):
            ax = (-((count - 0x90) & 65535)) & 65535
            bx = (((base + 0x90) & 255) - (ax & 255)) & 255
            source_offset = ((bx >> 3) << 6) & 65535
            native_offset = (((base + count) & 255) >> 3) * 64
            need(source_offset == native_offset and 0 <= native_offset <= 0x7C0, "wipe row address")
            rows += 1
    shake = 0
    for count in range(65536):
        for requested_stop in (False, True):
            source_stop = requested_stop and not count & 8
            target_stop = requested_stop and count & 8 == 0
            need(source_stop == target_stop, "shake stop phase")
            if not source_stop:
                value = (count + 1) & 65535
                source_mode = None if value & 3 else (1 if value & 4 else 4)
                native_mode = None if (count + 1) & 3 else (1 if (count + 1) & 4 else 4)
                need(source_mode == native_mode, "shake wrapped mode")
            shake += 1
    remaining = 0x154
    modes = []
    for _ in range(0x154):
        modes.append(9 if remaining & 1 else 2)
        remaining = (remaining - 1) & 65535
    need(remaining == 0 and modes.count(2) == 170 and modes.count(9) == 170, "camera countdown")
    need(0xF240 + 0x1C0 * 2 == 0xF5C0, "initial wipe geometry")
    for value in range(256):
        native = (value + 8) & 255
        need((native - 8) & 255 == value, "scanline affine inverse")
    for index in range(32):
        source_high = ((index if index < 16 else 31 - index) << 4) & 255
        target_high = ((index if index < 16 else 31 - index) * 16) & 255
        need(source_high == target_high, "normal IRQ palette control")
    return {"AL_decrement_cases": 65536, "row_cases": rows, "shake_counter_cases": shake,
            "camera_countdown_calls": 340, "initial_clear_halfwords": 448,
            "scanline_values": 256, "normal_IRQ_palette_indices": 32,
            "scope": "integer effect models only; no CPU or display execution"}


def verify(before: bytes, after: bytes, originals: dict[str, bytes]) -> dict:
    need(sha(before) == BEFORE and sha(after) == AFTER, "fixed-chain hash mismatch")
    need(len(before) == len(after) == 0x800000, "ROM length")
    for name, expected in ORIGINALS.items():
        need(sha(originals[name]) == expected, "original hash " + name)
    source_proof = proof_sources(originals["wsc10"], originals["wsc15"], originals["gba"])
    need(before[0x5E7000:0x5E9000] == b"\xFF" * 0x2000, "nonblank ownership")
    pointers, branches = [], []
    for raw in range(0, len(before), 4):
        word = struct.unpack_from("<I", before, raw)[0]
        if 0x085E7000 <= word < 0x085E9000:
            pointers.append(raw)
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000 and 0x5E7000 <= target(raw, word) < 0x5E9000:
            branches.append(raw)
    need(not pointers and not branches, "predecessor inbound")
    allowed = set(range(0x586244, 0x586248))
    count = 0
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    code_metadata = []
    for raw, size, code_size, expected, literals, calls in CODE:
        blob = after[raw:raw + size]
        need(sha(blob) == expected, "reviewed code body changed")
        need(struct.unpack_from("<" + "I" * len(literals), blob, code_size) == literals, "literal contract")
        need(blob[:4] == bytes.fromhex("FF5F2DE9") and blob[code_size - 8:code_size] == bytes.fromhex("FF5FBDE81EFF2FE1"), "complete register-save shape")
        ins = list(decoder.disasm(blob[:code_size], BASE + raw))
        addresses = {i.address for i in ins}
        need(len(ins) * 4 == code_size and all(i.size == 4 and i.id in ALLOWED for i in ins), "ARMv4T instruction classes")
        got_calls = set()
        for i in ins:
            word = int.from_bytes(i.bytes, "little")
            need(word >> 28 != 15, "unconditional ARMv5 encoding")
            if word & 0x0E000000 == 0x0A000000:
                dest = target(i.address, word)
                need(dest in addresses or (word & 0x01000000 and dest in calls), "branch contract")
                if word & 0x01000000:
                    got_calls.add(dest)
            if word & 0x0FFF0000 == 0x059F0000:
                literal = i.address + 8 + (word & 4095)
                need(BASE + raw + code_size <= literal <= BASE + raw + size - 4, "literal read leaves owner")
        need(got_calls == calls, "native call population")
        allowed.update(range(raw, raw + size))
        count += len(ins)
        code_metadata.append({"raw": raw, "bytes": size, "code_bytes": code_size, "sha256": expected})
    old_word, new_word = (struct.unpack_from("<I", x, 0x586244)[0] for x in (before, after))
    need(old_word >> 24 == new_word >> 24 == 0xEB, "update hook opcode")
    need(target(0x586244, old_word) == 0x173BC and target(0x586244, new_word) == 0x5E7000, "update hook targets")
    changed = {i for i, (x, y) in enumerate(zip(before, after, strict=True)) if x != y}
    need(changed and changed <= allowed and len(changed) == 877, "full-ROM Expected Write diff")
    # Resident display entry has neither an installed pointer nor an inbound
    # B/BL; its required IRQ live-in is therefore not synthesized by a caller.
    for raw in range(0, len(after), 4):
        if 0x5E7400 <= raw < 0x5E7548:
            continue
        word = struct.unpack_from("<I", after, raw)[0]
        need(word != 0x085E7400, "unapproved display entry pointer")
        if word >> 28 != 15 and word & 0x0E000000 == 0x0A000000:
            need(target(raw, word) != 0x5E7400, "unapproved display branch")
    return {"status": "PASS", "input_sha256": BEFORE, "output_sha256": AFTER,
            "changed_bytes": len(changed), "ARM_instructions": count, "code": code_metadata,
            "source_consumer_proof": source_proof, "finite_checks": finite_checks(),
            "main_update_connected": True, "display_entry_connected": False,
            "IRQ_gate": "source interrupted-DI read in0DEC unresolved",
            "runtime_or_save_test": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    for name in ORIGINALS:
        parser.add_argument(name, type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = verify(args.before.read_bytes(), args.after.read_bytes(), {n: getattr(args, n).read_bytes() for n in ORIGINALS})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[verify-shoot-stage-handshake] PASS " + AFTER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
