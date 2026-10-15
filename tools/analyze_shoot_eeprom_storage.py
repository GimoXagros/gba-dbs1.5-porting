#!/usr/bin/env python3
"""Read-only proof of a possible four-byte Shoot backing store.

No EEPROM operation is performed.  This checks the retail native protocol,
record allocation, and its encoded callers in the exact v53 candidate.  An
unused physical block is not proof that source observers were translated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from capstone import CS_ARCH_ARM, CS_ARCH_X86, CS_MODE_ARM, CS_MODE_THUMB, CS_MODE_16, Cs

HASHES = {
    "gba": "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED",
    "candidate": "455F98AFB4DCAA22D7666BB5AA5C0A4AA93EAAC48755563A191092A0162B0D48",
    "source": "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7",
}
RANGES = ((0x280, 0x294), (0x3BC, 0x3C0), (0x1FBD0, 0x1FD30),
          (0x37D5EC, 0x37DA06), (0x37DADC, 0x37DAF4), (0x37DB54, 0x37DB6C),
          (0x3877C4, 0x3877F0))
ARM_TARGETS = {0x37DADC: [0x284], 0x37DAE8: [0x290],
               0x37DB54: [0x1FC7C], 0x37DB60: [0x1FCC0]}
THUMB_TARGETS = {0x37D5EC: [], 0x37D65C: [], 0x37D7E4: [0x37D998],
                 0x37D894: [0x37D9E2], 0x37D970: [0x37D9F2], 0x37D9C8: []}
POINTER_TARGETS = {0x0837D5ED: [0x37DAE4], 0x0837D65D: [0x37DAF0],
                   0x0837D7E5: [0x37DB68], 0x0837D895: [],
                   0x0837D971: [], 0x0837D9C9: [0x37DB5C],
                   0x0837DB54: [], 0x0837DB60: []}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def anchor(data: bytes, raw: int, expected: list[str], thumb: bool = False) -> None:
    decoder = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    rows = list(decoder.disasm(data[raw:raw + 256], 0x08000000 + raw))[:len(expected)]
    need([f"{i.mnemonic} {i.op_str}".strip() for i in rows] == expected,
         f"native instruction contract changed at {raw:06X}")


def contracts(data: bytes) -> dict:
    anchor(data, 0x280, ["mov r0, #4", "bl #0x837dadc", "mov r0, #2",
                        "ldr r1, [pc, #0x128]", "bl #0x837dae8"])
    need(struct.unpack_from("<I", data, 0x3BC)[0] == 0x030000F0, "timer IRQ slot")
    anchor(data, 0x37D5F4, ["cmp r0, #4", "bne #0x837d608", "ldr r1, [pc, #4]",
                           "ldr r0, [pc, #8]", "str r0, [r1]", "b #0x837d624"], True)
    need(struct.unpack_from("<2I", data, 0x37D600) == (0x03006CD0, 0x083877D0), "selected EEPROM config")
    need(struct.unpack_from("<IHHB", data, 0x3877D0) == (512, 64, 0x0300, 6), "512-byte protocol geometry")
    anchor(data, 0x1FC64, ["mov r2, #0x19", "ldr r1, [pc, #0x34]", "str sb, [r1, #0xc0]",
                           "mov r3, #0", "push {r1, r2, r3}", "mov r0, r3", "bl #0x837db54",
                           "pop {r1, r2, r3}", "orrs r0, r0, r0", "bne #0x801fc9c",
                           "add r1, r1, #8", "add r3, r3, #1", "subs r2, r2, #1", "bgt #0x801fc74"])
    anchor(data, 0x1FCAC, ["mov r2, #0x19", "ldr r1, [pc, #0x4c]", "mov r3, #0",
                           "push {r1, r2, r3}", "mov r0, r3", "bl #0x837db60",
                           "pop {r1, r2, r3}", "orrs r0, r0, r0", "bne #0x801fcf8",
                           "add r1, r1, #8", "add r3, r3, #1", "subs r2, r2, #1", "bgt #0x801fcb8"])
    need(struct.unpack_from("<I", data, 0x1FCA4)[0] == 0x03001120 and
         struct.unpack_from("<I", data, 0x1FD04)[0] == 0x03001120, "record buffer pointer")
    anchor(data, 0x1FD0C, ["ldr r8, [pc, #0x18]", "mov sb, #0", "mov sl, #0xc0",
                           "ldrb fp, [r8], #1", "add sb, sb, fp", "subs sl, sl, #1",
                           "bgt #0x801fd18", "bx lr"])
    need(struct.unpack_from("<I", data, 0x1FD2C)[0] == 0x03001120, "checksum buffer")
    for raw, target in ((0x37DB54, 0x0837D9C9), (0x37DB60, 0x0837D7E5)):
        anchor(data, raw, ["ldr ip, [pc]", "bx ip"])
        need(struct.unpack_from("<I", data, raw + 8)[0] == target, "ARM/Thumb API veneer")
    anchor(data, 0x37D9DA, ["cmp r6, #2", "bhi #0x837d9fe", "adds r0, r4, #0",
                            "adds r1, r5, #0", "bl #0x837d894", "lsls r0, r0, #0x10",
                            "lsrs r2, r0, #0x10", "cmp r2, #0", "bne #0x837d9d4",
                            "adds r0, r4, #0", "adds r1, r5, #0", "bl #0x837d970",
                            "lsls r0, r0, #0x10", "lsrs r2, r0, #0x10", "cmp r2, #0",
                            "bne #0x837d9d4", "adds r0, r2, #0"], True)
    anchor(data, 0x37D8CA, ["ldrh r2, [r5]", "adds r5, #2", "movs r0, #0"], True)
    anchor(data, 0x37D8E0, ["adds r0, r1, #1", "lsls r0, r0, #0x18", "lsrs r1, r0, #0x18",
                            "cmp r1, #3", "bls #0x837d8ca"], True)
    anchor(data, 0x37D916, ["movs r1, #0xd0", "lsls r1, r1, #0x14"], True)
    anchor(data, 0x37D8A2, ["ldrh r0, [r0, #4]", "cmp r4, r0", "blo #0x837d8b4"], True)
    anchor(data, 0x37D858, ["movs r4, #0", "movs r6, #1"], True)
    anchor(data, 0x37D876, ["strh r1, [r5]", "subs r5, #2", "adds r0, r4, #1",
                            "lsls r0, r0, #0x18", "lsrs r4, r0, #0x18", "cmp r4, #3",
                            "bls #0x837d85c"], True)
    need(25 * 8 == 200 and 200 + 8 <= 512, "reserved-block arithmetic")
    return {"physical_bytes": 512, "physical_blocks": 64, "block_bytes": 8,
            "native_record_blocks_half_open": [0, 25], "native_record_bytes_half_open": [0, 200],
            "native_record_RAM": 0x03001120, "checksum_payload_bytes": 192,
            "checksum_bytes_half_open": [192, 196], "record_trailing_bytes_half_open": [196, 200],
            "write_API_ARM_entry": 0x0837DB54, "read_API_ARM_entry": 0x0837DB60,
            "write_contract": "r0=block index, r1=at least8 readable bytes; r0=16-bit status, zero success; caller must preserve caller-saved registers",
            "write_attempt_limit": 3, "readback_verification": True, "allocated_timer_index": 2,
            "allocated_timer_IRQ_slot": 0x030000F0,
            "proposed_exclusive_block": 25, "proposed_exclusive_bytes_half_open": [200, 208],
            "proposed_source_bytes_half_open": [0x13CD8, 0x13CDC],
            "proposed_padding_bytes_half_open": [204, 208]}


def census(data: bytes) -> dict:
    arm = {k: [] for k in ARM_TARGETS}
    thumb = {k: [] for k in THUMB_TARGETS}
    for raw in range(0, len(data) - 3, 2):
        a, b = struct.unpack_from("<2H", data, raw)
        if a & 0xF800 == 0xF000 and b & 0xF800 == 0xF800:
            displacement = (a & 0x7FF) * 4096 + (b & 0x7FF) * 2
            if displacement & 0x400000:
                displacement -= 0x800000
            target = raw + 4 + displacement
            if target in thumb:
                thumb[target].append(raw)
        if raw % 4 == 0:
            word = a | b << 16
            if word & 0x0E000000 == 0x0A000000:
                displacement = word & 0xFFFFFF
                if displacement & 0x800000:
                    displacement -= 0x1000000
                target = raw + 8 + displacement * 4
                if target in arm:
                    arm[target].append(raw)
    pointers = {}
    for target in POINTER_TARGETS:
        pattern = struct.pack("<I", target)
        positions = []
        position = data.find(pattern)
        while position >= 0:
            positions.append(position)
            position = data.find(pattern, position + 1)
        pointers[target] = positions
    need(arm == ARM_TARGETS, "unexpected ARM API inbound edge")
    need(thumb == THUMB_TARGETS, "unexpected Thumb API inbound edge")
    need(pointers == POINTER_TARGETS, "unexpected API pointer representation")
    return {"ARM_B_BL_encoded_edges": arm, "Thumb_BL_encoded_edges": thumb,
            "all_byte_function_pointer_patterns": pointers,
            "denominator_bytes": len(data),
            "scope": "all encoded branches/pointers to these actual API entries; not a proof excluding arbitrary computed jumps or independent manual EEPROM protocols"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gba", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = {key: getattr(args, key).read_bytes() for key in HASHES}
    for key, expected in HASHES.items():
        need(digest(data[key]) == expected, f"immutable {key} input mismatch")
    for a, z in RANGES:
        need(data["gba"][a:z] == data["candidate"][a:z], f"native storage dependency modified at {a:06X}")
    facts = contracts(data["gba"])
    source_store = data["source"][0x747CD6:0x747CF0]
    need(digest(source_store) == "E9A7773BC80C92BBF1BD6DD942C0E3A5A0E0FF69244448A8F60CE8964CB96686", "source store range")
    source_rows = list(Cs(CS_ARCH_X86, CS_MODE_16).disasm(source_store, 0x747CD6))
    need([f"{i.mnemonic} {i.op_str}" for i in source_rows] == ["mov ax, 0x1000", "mov es, ax",
          "mov word ptr es:[0x660], 0", "mov word ptr es:[0x3cd8], 0", "mov word ptr es:[0x3cda], 0"], "source ordered zero stores")
    call_reports = {key: census(data[key]) for key in ("gba", "candidate")}
    rejected = []
    for raw, replacement, label in (
        (0x280, struct.pack("<I", 0xE3A00040), "boot switches to64-kbit protocol"),
        (0x3877D4, struct.pack("<H", 63), "physical block count changed"),
        (0x1FC64, struct.pack("<I", 0xE3A0201A), "retail record grows into proposed block"),
        (0x1FD14, struct.pack("<I", 0xE3A0A0C4), "checksum payload expanded"),
        (0x37DB5C, struct.pack("<I", 0x0837D7E5), "write veneer changed toread"),
        (0x37D9DA, struct.pack("<H", 0x2E03), "write retry bound changed"),
        (0x37D8E6, struct.pack("<H", 0x2904), "writer source extent grows beyond8bytes"),
    ):
        mutated = bytearray(data["gba"]); mutated[raw:raw + len(replacement)] = replacement
        try:
            contracts(mutated)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError(f"accepted semantic mutation: {label}")
    report = {"schema": 1, "result": "BOUNDED_NATIVE_BACKING_STORE_OPTION_OBSERVER_CLOSURE_UNRESOLVED",
              "inputs": HASHES, "native_storage_contract": facts, "API_census": call_reports,
              "pinned_native_ranges": [{"start": a, "end": z, "sha256": digest(data["gba"][a:z])} for a, z in RANGES],
              "semantic_mutations_rejected": rejected,
              "policy_adopted": False, "source_observer_translation_closed": False,
              "full_initializer_gate_closed": False, "ROM_or_EEPROM_written": False,
              "new_persistent_RAM_required": False,
              "remaining_contracts": ["Choose how the scene handles the native writer's nonzero status and synchronous wait.",
                                      "A source observer of13CD8..DB must consume this representation; backing bytes alone do not implement that observer.",
                                      "Source SRAM updates are byte-addressable; the new native block would have four explicitly reserved padding bytes.",
                                      "No cross-platform power-failure atomicity or timing equality is claimed."],
              "source_runtime_watch": {"SRAM_backing_half_open": [0x3CD8, 0x3CDC],
                                       "bus_aliases_half_open": [[0x13CD8, 0x13CDC], [0x1BCD8, 0x1BCDC]],
                                       "distinct_IRAM_timer_half_open": [0xFCD8, 0xFCDC],
                                       "expected_write_CS_IP": [[0x4090, 0x73E2], [0x4090, 0x73E9]],
                                       "observe_through": "7168 entry,155F restored gameplay,1750 terminal,and following normal stage/menu/save",
                                       "capture": ["access kind", "CS:IP", "DS", "ES", "BX", "SI", "DI", "C1", "current task callback"]},
              "no_game_CPU_execution_emulator_or_save_access": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "sha256": digest(args.output.read_bytes()),
                      "semantic_mutations_rejected": len(rejected), "output": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
