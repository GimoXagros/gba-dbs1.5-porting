#!/usr/bin/env python3
"""Bounded, read-only evidence for the unresolved source SRAM zero stores.

This is an inventory and a positive serialization-layout proof, not a claim
that the stores are dead. It does not execute a CPU, read a save, or infer
segment equivalence from equal 16-bit offsets.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import pathlib
import re
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "vendor"))
from capstone import Cs, CS_ARCH_X86, CS_MODE_16  # type: ignore
from capstone.x86_const import X86_OP_IMM, X86_OP_MEM, X86_OP_REG  # type: ignore

SHA = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
BEGIN, END = 0x700000, 0x800000
RANGES = (
    (0x747CD6, 0x747CF0, "E9A7773BC80C92BBF1BD6DD942C0E3A5A0E0FF69244448A8F60CE8964CB96686"),
    (0x785E5B, 0x785F66, "5B9C2CCFBFAC8D4C9ED9749EB204ACEF2A51A8B9E11CFB2FD81CEEE4672A2ED9"),
    (0x7860CF, 0x786147, "D4861B6BB6EE391BD16ED49B2DAF6CC15D2050D04EFCB1BC37CA8B4EAAF08483"),
    (0x7432E4, 0x74333C, "9FF8BCECB7293927D6AA8ADB00E4A29A12A9479CC04B3E3CA691FE9A512F3E32"),
    (0x753B9E, 0x753E80, "CF03BDA1F07D9A37864EFC575AB6E88B3D285F4463F1C2149DFA8B1FA79150F9"),
    (0x768F70, 0x769067, "6D67B76C6F224D31ACF45E2C72BD8DF2E8DBD53A957CA95CD9FB3DF2967B6C48"),
    (0x769367, 0x769372, "DD58EBD7D784B49A34726CAEEF882693D90C55446628B5A28C479701C739F259"),
    (0x7693AC, 0x769410, "8C2E97BB8E1DC088B6A9CD164621148D4618C8BFDC5DB4FDB434EBA07FBFF48A"),
    (0x76AFD7, 0x76B03B, "439B3D9B6D1FBAAAED26AAF2E8F0B22406B70D0A6ECE29EA4347315B9E6498A4"),
    (0x76B1DB, 0x76B312, "15FB86F94E592B3B00FE836F14C634DF840ADEC98CA3E3F39950DF4BB7092072"),
    (0x740900, 0x74092C, "29268A76D6D9E712E8EB96CD73F665A675368F2729D26AFC980EEB1071FB195D"),
    (0x78370E, 0x78378C, "230C505415173C2958B4FCED9551AEA4D19DFC686CB85EB5495995C3632440B9"),
    (0x783C9E, 0x783EAF, "BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1"),
    (0x75FCAB, 0x75FE03, "31405427B84E0B8A7732461307D3D5E8087BB654AA15DAD7FE439C61F8E04301"),
    (0x3B5178, 0x3B51A8, "DB9B26744B3869741DE021CA571E4282736886329F39A79E3A6365C18602F4F4"),
    (0x750928, 0x750A22, "01E9958B77AF27A5C34DDEBDC9C795BBCEBC06E0685D542FA19C3DC86D3A0605"),
    (0x741F6E, 0x741FCE, "D26577BCBF2514CEA8CAC2D4F1C7EFD3EAF09CC8B66828A02C9A502C96BB3369"),
    (0x74202A, 0x74211E, "D855573FE2DF49D006A7E8DC022DBEBDD592A9F7DBE4596FACD74B00E1E68755"),
    (0x752168, 0x7521A9, "11BD02EED8B7187F76646E3EDD0CECD636598B7F693DB8522ADAF0E49087C4B7"),
    (0x76B671, 0x76B687, "01914C269497B484CB9C2DD0C43BBBECBD3B35620AF19B924D67E5ED87FC5E1C"),
    (0x76BF40, 0x76BF86, "168033D5AAD0FECB08B568C74D111B4A34B0F0E143D324090F880AD864FF426E"),
    (0x76C361, 0x76C377, "01914C269497B484CB9C2DD0C43BBBECBD3B35620AF19B924D67E5ED87FC5E1C"),
)


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest().upper()


def need(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def decode(data: bytes, start: int, length: int):
    engine = Cs(CS_ARCH_X86, CS_MODE_16)
    engine.detail = True
    return list(engine.disasm(data[start:start + length], start))


def anchor(data: bytes, start: int, text: list[str]) -> None:
    rows = decode(data, start, 128)[:len(text)]
    need([f"{i.mnemonic} {i.op_str}".strip() for i in rows] == text,
         f"source instruction contract changed at {start:X}")


def serialization(data: bytes) -> dict:
    # 85DE:02EF calls its sanitizers before loading CX. The subsequent read
    # branch and all three valid write-dispatch destinations preserve CX.
    anchor(data, 0x7860E3, ["mov cx, 0xe8", "cmp word ptr [bp + 8], 0",
                          "je 0x786102", "mov ax, 0x1000", "mov ds, ax",
                          "mov si, 0x76", "mov ax, 0xc00", "mov es, ax",
                          "mov di, 0x392c", "cld", "rep movsb byte ptr es:[di], byte ptr [si]"])
    anchor(data, 0x786102, ["mov ax, 0x1000", "mov es, ax", "mov di, 0x4e",
                          "mov ax, 0xc00", "mov ds, ax", "mov si, 0x392c",
                          "mov bx, word ptr [bp + 6]", "add bx, bx",
                          "jmp word ptr cs:[bx + 0x2d9]"])
    table = struct.unpack_from("<11H", data, 0x785DE0 + 0x2D9)
    need(set(table) == {0x33C, 0x346, 0x34F}, "save dispatch destinations changed")
    anchor(data, 0x78611C, ["mov ax, word ptr es:[di + 0x1c]", "mov word ptr [si + 0x10], ax", "jmp 0x78612f"])
    anchor(data, 0x786126, ["xor ax, ax", "mov al, byte ptr es:[di + 0x19]", "mov word ptr [si + 0x12], ax"])
    anchor(data, 0x78612F, ["mov ax, 0x1000", "mov es, ax", "mov di, 0x76",
                          "cld", "rep movsb byte ptr es:[di], byte ptr [si]"])
    anchor(data, 0x785E9D, ["mov di, 0x392c", "push di", "mov cx, 0xe8",
                          "xor ax, ax", "cld", "rep stosb byte ptr es:[di], al"])
    serialized = set(range(0x76, 0x76 + 0xE8))
    target = {0x3CD8, 0x3CD9, 0x3CDA, 0x3CDB}
    need(not serialized & target, "SRAM target entered serialized record")
    return {"entry": "85DE:02EF", "raw_range": [0x7860CF, 0x786147],
            "SRAM_half_open": [0x76, 0x15E], "internal_half_open": [0xF92C, 0xFA14],
            "bytes": 0xE8, "valid_mode_entries": list(table),
            "target_disjoint": True,
            "scope": "this positively identifies the game's E8-byte record; it does not prove all other SRAM reads absent"}


def occurrences(data: bytes, pattern: bytes) -> list[int]:
    result, cursor = [], BEGIN
    while True:
        cursor = data.find(pattern, cursor, END)
        if cursor < 0:
            return result
        result.append(cursor)
        cursor += 1


def alias_inventory(data: bytes) -> dict:
    far = []
    for at in range(BEGIN, END - 3):
        offset, segment = struct.unpack_from("<HH", data, at)
        physical = (segment << 4) + offset
        if physical in (0x13CD8, 0x13CDA, 0x1BCD8, 0x1BCDA):
            far.append([at, offset, segment])
    patterns = {key: occurrences(data, bytes.fromhex(key)) for key in
                ("d83c", "da3c", "d8bc", "dabc", "d03c", "d0bc", "e83c", "e03c", "f83c")}
    need(not far and not patterns["d8bc"] and not patterns["dabc"], "new simple alias candidate")
    return {"range": [BEGIN, END], "all_byte_aligned_offset_segment_pairs": far,
            "operand_bytes": patterns,
            "scope": "byte candidates only; computed pointers, split literals, register copies and inherited segments are not eliminated"}


def segment_inventory(data: bytes) -> dict:
    # Deliberately an over-inclusive byte pattern, followed by same-register
    # validation. This is not a complete disassembly or a CFG/liveness pass.
    groups = defaultdict(list)
    mismatches = []
    prefix = rb"[\xb8-\xbf]..\x8e[\xc0-\xc7\xd8-\xdf]"
    for match in re.finditer(prefix, data[BEGIN:END], re.DOTALL):
        at = BEGIN + match.start()
        immediate = struct.unpack_from("<H", data, at + 1)[0]
        if not 0x3CE <= immediate <= 0x1BCD:
            continue
        rows = decode(data, at, 5)
        need(len(rows) == 2, "adjacent segment setter decode differs")
        if rows[0].operands[0].reg != rows[1].operands[1].reg:
            if immediate == 0x1000:
                mismatches.append(at)
            continue
        groups[immediate].append(at)
    need(len(groups[0x1000]) == 684 and len(mismatches) == 6,
         "immediate segment candidate denominator changed")
    return {"range": [BEGIN, END], "candidate_1000_population": 690,
            "same_register_1000_population": 684, "different_register_1000_candidates": mismatches,
            "potential_SRAM_reaching_segment_values": {f"{k:04X}": v for k, v in sorted(groups.items())},
            "scope": "adjacent immediate/register setters only; excludes paired-register, memory-loaded, stack-restored and inherited segment values"}


def indirect_families(data: bytes) -> dict:
    anchor(data, 0x753BA2, ["mov ax, 0x1073", "mov es, ax", "xor ax, ax",
                          "mov di, 0xc0", "mov word ptr es:[di], ax", "mov di, 0",
                          "mov cx, 0x60", "cld", "rep stosw word ptr es:[di], ax",
                          "mov di, 0xc2", "mov cx, 0x54", "cld", "rep stosw word ptr es:[di], ax"])
    anchor(data, 0x753CCF, ["mov di, 0xc0", "mov di, word ptr [di]",
                          "mov word ptr [bp - 0x1a], di", "mov di, 0",
                          "mov si, word ptr [bp - 0x12]"])
    return {
        "1073_background_animation": {
            "initializer": [0x753B9E, 0x753BC6],
            "initialized_relative_ranges": [[0, 0xC0], [0xC0, 0xC2], [0xC2, 0x16A]],
            "initialized_SRAM_half_open": [0x730, 0x89A],
            "target_relative_offsets": [0x35A8, 0x35AA, 0xB5A8, 0xB5AA],
            "fixed_record_readers": [0x769C3B, 0x76A189, 0x76A2A3, 0x76A5E1, 0x76A659, 0x76AC3A, 0x76ACA4],
            "generic_queue_reader": [0x753BC6, 0x753C16],
            "generic_record_reader_writer": [0x753C4C, 0x753E86],
            "bounded_Shoot_dispatch": shoot_background_family(data),
            "remaining": "the generic producer and queue are excluded from the two stage-11 dispatches below; arbitrary indirect callers and other-stage queue accumulation remain outside this proof"
        },
        "1000_common_work_state": {
            "known_live_scene_reads": ["006x", "03CD..03E8", "065C", "065E", "066E/0670 list", "071E"],
            "palette_snapshot_half_open": [0x3EA, 0x5EA],
            "remaining": "inherited DS/ES pointers and generic-reader argument ranges after normal callbacks resume"
        },
        "0C00_object_and_global_data": {
            "ordinary_HP_cache_linear": [0xFCD8, 0xFCDA],
            "would_need_offsets_for_SRAM_alias": [0x7CD8, 0x7CDA, 0xFCD8, 0xFCDA],
            "remaining": "use allocator/array bounds, not equal low offsets, to exclude computed aliases"
        },
        "palette_and_graphics_segments": {
            "candidates": [0x400, 0x800, 0xBDE, 0xFE0, 0xFEE, 0xFF0],
            "remaining": "independently bind each read/copy argument extent before claiming no SRAM overlap"
        }
    }


def exact_far_calls(data: bytes, segment: int, offset: int) -> list[int]:
    pattern = b"\x9a" + struct.pack("<HH", offset, segment)
    return [m.start() for m in re.finditer(re.escape(pattern), data)]


def shoot_background_family(data: bytes) -> dict:
    """Bind the particular animation owner to the actual stage-11 dispatch.

    This is not a whole-program CFG. The full-ROM direct-call census and the
    finite stage tables make the stated dispatcher exclusion reviewable.
    """
    expected = {
        0x3BAE: [0x77CF17, 0x77DCF8],
        0x3BD6: [0x76907E, 0x76911B, 0x76922C, 0x7692E1, 0x7692FC, 0x769356],
        0x3C26: [0x769CDB, 0x769DED, 0x76A308, 0x76A609, 0x76A681, 0x76ABFB,
                 0x76AC0B, 0x76AC5D, 0x76AC6E, 0x76ACE9, 0x76FAA7, 0x77D6F7],
        0x3C5C: [0x769464, 0x769B9F, 0x769BC2, 0x76A044, 0x76A17A, 0x76A5BA, 0x76AA3B],
    }
    for offset, sites in expected.items():
        need(exact_far_calls(data, 0x4FFF, offset) == sites,
             f"1073 family direct-call census changed at {offset:X}")
    # Deliberately count byte candidates, not decoded reachable calls. Finding
    # none suffices to exclude that particular near E8/E9 encoding in this CS.
    near_candidates = []
    for ip in range(0xFFFE):
        at = 0x74FFF0 + ip
        if data[at] in (0xE8, 0xE9):
            target = (ip + 3 + struct.unpack_from("<h", data, at + 1)[0]) & 0xFFFF
            if target in expected:
                near_candidates.append([at, target])
    need(not near_candidates, "new 1073 family near-call candidate")
    before = struct.unpack_from("<12H", data, 0x768F70)
    update = struct.unpack_from("<12H", data, 0x7693AC)
    palette = struct.unpack_from("<12H", data, 0x78370E)
    need(before[11] == 0x3F7 and update[11] == 0x2067 and palette[11] == 0x82E,
         "stage-11 dispatch selection changed")
    anchor(data, 0x768FA7, ["mov di, 0x1000", "mov ds, di", "mov di, 0x4e",
                          "xor ax, ax", "mov al, byte ptr [di + 0xe]"])
    anchor(data, 0x768FC6, ["mov ax, 0x1000", "mov ds, ax", "add bx, bx",
                          "call word ptr cs:[bx]"])
    anchor(data, 0x7693E8, ["mov di, 0x1000", "mov ds, di", "mov di, 0x4e",
                          "xor ax, ax", "mov al, byte ptr [di + 0xe]"])
    anchor(data, 0x7693F7, ["mov bx, ax", "xor cx, cx", "add bx, bx",
                          "call word ptr cs:[bx + 0x43c]"])
    anchor(data, 0x769367, ["lcall 0x4090, 0", "lcall 0x8347, 0x2b6", "ret"])
    anchor(data, 0x76B02F, ["lcall 0x5eea, 0xe0b", "call 0x76b1db",
                          "mov sp, bp", "pop bp", "ret"])
    local_ranges = ((0x740900, 0x74092C), (0x769367, 0x769372),
                    (0x76AFD7, 0x76B03B), (0x76B1DB, 0x76B312),
                    (0x783C9E, 0x783EAF), (0x75FCAB, 0x75FE03))
    calls = []
    for a, z in local_ranges:
        instructions = decode(data, a, z - a)
        need(sum(i.size for i in instructions) == z - a, "stage family decode extent")
        for ins in instructions:
            if ins.mnemonic in ("call", "lcall"):
                calls.append([ins.address, ins.mnemonic, ins.op_str])
            # There is no direct 1073 setter in these fully decoded ranges.
            if ins.mnemonic == "mov" and len(ins.operands) == 2:
                rhs = ins.operands[1]
                need(not (rhs.type == X86_OP_IMM and rhs.imm == 0x1073),
                     "stage-11 family gained 1073 segment value")
    need(calls == [[0x769367, "lcall", "0x4090, 0"], [0x76936C, "lcall", "0x8347, 0x2b6"],
                   [0x76B02F, "lcall", "0x5eea, 0xe0b"], [0x76B034, "call", "0x76b1db"],
                   [0x75FCE3, "lcall", "0x4fff, 0x3367"], [0x75FCFC, "lcall", "0x4fff, 0x3367"],
                   [0x75FDE2, "lcall", "0x4fff, 0x3367"]], "stage-11 call edges changed")
    # The generic record reader uses a byte starting index and a byte loop
    # count, so even header corruption within those widths cannot reach 35A8.
    anchor(data, 0x753CDD, ["mov ch, byte ptr es:[si]", "mov bx, si",
                          "mov si, word ptr es:[bx + 2]", "xor ax, ax",
                          "mov al, byte ptr es:[bx + 1]", "mov bx, 6", "mul bx", "add di, ax"])
    anchor(data, 0x753E5A, ["add si, 8", "add di, 6", "dec ch", "jne 0x753e41"])
    record_end = 6 * 255 + 6 * 255 + 6
    need(record_end == 0xBFA and record_end < 0x35A8, "generic record bound")
    # +14 of a ROM BG descriptor becomes +2E of its runtime BG record. Zero
    # is not a sentinel: the table at offset zero contains three animations.
    anchor(data, 0x753003, ["mov ax, word ptr [di + 0x14]", "mov word ptr es:[si + 0x2e], ax"])
    descriptors = []
    for index in (0x27, 0x28):
        at = 0x3B4DD0 + index * 24
        animation = struct.unpack_from("<H", data, at + 20)[0]
        need(animation == 0, "Shoot descriptor animation field changed")
        descriptors.append({"index": index, "raw": at, "animation_offset": animation})
    need(data[0x42DE00:0x42DE04] == bytes.fromhex("03000600"), "zero animation header changed")
    maps = []
    for layer in range(2):
        record = 0x3B5178 + layer * 24
        need(struct.unpack_from("<HH", data, record) == (2, 3), "source Shoot map geometry")
        descriptor_offset, segment = struct.unpack_from("<HH", data, record + 8)
        need((descriptor_offset, segment) == (0x318 + layer * 0x18, 0x383F), "source BG map fields")
        for index in range(6):
            bank, mode, offset = struct.unpack_from("<BBH", data, 0x3B4970 + descriptor_offset + index * 4)
            need((bank, mode) == (0xC9, 1), "source BG map pointer class")
            physical = segment * 16 + offset
            need(0x30000 <= physical and physical + 0x3F0 <= 0x40000, "source map escaped ROM window")
            raw = (bank & 127) * 0x10000 + (physical & 0xFFFF)
            need(raw == 0x49C4D0 + (layer * 6 + index) * 0x3F0, "source map linear domain")
            maps.append([raw, raw + 0x3F0])
    return {
        "precondition": "actual source stage byte 1000:005C is 11 and these engine dispatchers are used",
        "full_ROM_direct_call_sites": {f"4FFF:{k:04X}": v for k, v in expected.items()},
        "near_E8_E9_candidates_in_CS4FFF": near_candidates,
        "stage_tables": {"before": list(before), "update": list(update), "palette": list(palette)},
        "stage11_entries": [0x769367, 0x76AFD7, 0x783C9E],
        "stage11_calls": calls,
        "generic_1073_reader_or_producer_called_by_stage11_dispatch": False,
        "source_initializer_queue_reset": 0x77DCF8,
        "generic_record_relative_half_open_for_all_byte_headers": [0, record_end],
        "generic_record_target_disjoint": True,
        "descriptor_fields": descriptors,
        "zero_animation_header_is_empty": False,
        "palette_state_SRAM_half_open": [0x174, 0x1B4],
        "BG_map_read_domains": maps,
        "BG_map_target_disjoint": True,
        "map_consumer_external_proof": "tools/verify_shoot_stage_assets.py; report 213203E94233DA124057CC5BE7D9481BBA98F838D475F40C03EEC28EDAEE1E25",
        "scope": "finite stage-11 dispatch and direct-caller census; does not eliminate arbitrary indirect calls or prove every other-stage queue bound",
    }


def object_pool(data: bytes) -> dict:
    anchor(data, 0x750928, ["mov ax, 0xc00", "mov es, ax"])
    anchor(data, 0x750960, ["mov di, 0x14", "mov cx, 0x1ba0", "xor ax, ax",
                          "rep stosw word ptr es:[di], ax"])
    anchor(data, 0x750978, ["mov ax, 0xc00", "mov ds, ax", "mov bx, 0x14",
                          "mov cx, word ptr [bx + 0xa]", "and cx, 2", "je 0x750990",
                          "add bx, 0x110", "jmp 0x750980"])
    anchor(data, 0x750A14, ["mov ax, di", "mov dx, 0xc00"])
    anchor(data, 0x741FA5, ["mov cx, 0x1a", "xor bx, bx", "push word ptr cs:[bx + 0x16ce]",
                          "push 0x4090", "push 0x1bc4", "lcall 0x4fff, 0x980",
                          "add sp, 6", "mov word ptr [si], ax", "add si, 2", "add bx, 2",
                          "loop 0x741faa"])
    anchor(data, 0x742081, ["mov ax, 0xc00", "mov ds, ax", "sub di, 0x640", "shl di, 1",
                          "add di, 0x60c", "mov di, word ptr es:[di]"])
    anchor(data, 0x7420A3, ["add di, 0x10", "inc byte ptr es:[0x658]"])
    need(struct.unpack_from("<6H", data, 0x742042) == (0x174E, 0x1757, 0x175D, 0x1766, 0x176C, 0x1772),
         "typed object pool dispatch")
    size, slots = 0x1BA0 * 2, 52
    need(size == slots * 0x110, "task pool slot population")
    spans = [(0xC000 + 0x14 + i * 0x110 + 0x10, 0xC000 + 0x14 + (i + 1) * 0x110)
             for i in range(slots)]
    need(spans[0][0] == 0xC024 and spans[-1][1] == 0xF754, "owned task payload bound")
    need(all(not a <= target < z for a, z in spans for target in (0x13CD8, 0x13CDA, 0x1BCD8, 0x1BCDA)),
         "task payload intersects target")
    return {"initializer": [0x750928, 0x750970], "allocator": [0x750970, 0x750A22],
            "task_slots": slots, "slot_bytes": 0x110, "header_bytes": 0x10, "payload_bytes": 0x100,
            "owned_payload_linear_envelope": [0xC024, 0xF754], "object_handle_table": [0x1060C, 0x10640],
            "object_handle_count": 26, "object_flag_table": [0x10640, 0x1065A],
            "target_disjoint": True,
            "precondition": "valid engine-owned task/object handles; field accesses stay inside their 0x100-byte payload; allocator has an available owned slot",
            "allocator_has_exhaustion_guard": False,
            "scope": "positive allocator representation; does not prove every imported caller supplies a typed object handle or bounded field index"}


def generic_copy_family(data: bytes) -> dict:
    need(exact_far_calls(data, 0x4FFF, 0x2178) == [0x76B67F, 0x76BF7E, 0x76C36F],
         "generic copy direct-caller population")
    anchor(data, 0x752173, ["mov di, word ptr [bp + 6]", "mov es, word ptr [bp + 8]",
                          "mov si, word ptr [bp + 0xa]", "mov ds, word ptr [bp + 0xc]",
                          "mov cx, word ptr [bp + 0xe]", "shr cx, 1",
                          "rep movsw word ptr es:[di], word ptr [si]"])
    for at in (0x76B671, 0x76C361):
        anchor(data, at, ["push 0x200", "push 0x1000", "push 0x3ea", "push 0", "push 0xfe00",
                          "lcall 0x4fff, 0x2178", "add sp, 0xa"])
    anchor(data, 0x76BF45, ["mov al, 0xca", "out 0xc3, al", "mov ax, 0", "mov bx, 0x3000"])
    anchor(data, 0x76BF57, ["mov al, 0xcb", "out 0xc3, al", "mov ax, 0", "mov bx, 0x3000"])
    anchor(data, 0x76BF69, ["mov al, 0xcb", "out 0xc3, al", "mov ax, 0", "mov bx, 0x3614"])
    anchor(data, 0x76BF73, ["push 0xe0", "push bx", "push ax", "push 0x1000", "push 0x3ea",
                          "lcall 0x4fff, 0x2178", "add sp, 0xa"])
    return {"entry": "4FFF:2178", "raw": [0x752168, 0x7521A9],
            "direct_callers": [0x76B67F, 0x76BF7E, 0x76C36F],
            "SRAM_read_half_open": [0x3EA, 0x5EA], "SRAM_write_half_open": [0x3EA, 0x4CA],
            "ROM_read_half_open_choices": [[0x4A0000, 0x4A00E0], [0x4B0000, 0x4B00E0], [0x4B6140, 0x4B6220]],
            "target_disjoint_for_all_direct_callers": True,
            "scope": "all encoded direct far callers of the generic byte-copy helper; arbitrary indirect calls are not eliminated"}


def argument_reader_inventory(data: bytes) -> dict:
    # This diagnostic population is deliberately not treated as a call graph.
    # Segment loads through resource fields and inherited DS/ES are separate.
    ds = occurrences(data, b"\x8e\x5e")
    es = occurrences(data, b"\x8e\x46")
    need(len(ds) == 36 and len(es) == 31, "argument-segment byte candidate population")
    return {"scope": "all-byte fixed-ROM candidates for mov DS/ES,[BP+disp8], not all live readers",
            "DS_sites": ds, "ES_sites": es,
            "classified_non4FFF_DS_sites": {
                "object_release": [0x742127], "object_callback_and_state": [0x760E9F],
                "particle_presentation_state": [0x76F249], "collision_object_and_BG": [0x76F87C, 0x76FB30],
                "BG_scroll": [0x77DF3B, 0x77DFEA], "object_write_only": [0x780EA9]},
            "remaining_first_milestone_import_gates": [
                {"entry": "4FFF:226E/22CA resource-copy family", "sites": [0x752273, 0x7522CF, 0x75228E, 0x7522EA],
                 "gate": "bind each live P0/P1 descriptor's loaded segment/offset/byte-count to the already decoded ROM assets; segment values are loaded again through ES resource fields"},
                {"entry": "4FFF palette segment-argument family", "sites": [0x751DD3, 0x751E9E, 0x751EF6, 0x751F7C, 0x751FE0, 0x75206A],
                 "gate": "bind every live imported call's source/destination segment, starting offset and count, including restored normal callbacks; scene-only snapshot bounds are insufficient"},
                {"entry": "6B4A collision imports", "sites": [0x76F87C, 0x76FB30],
                 "gate": "show all restored common callback argument pairs are an owned object plus the actual stage-11 BG state; allocator bounds alone do not prove the caller arguments"},
                {"entry": "generic transfers after leaving stage11", "sites": [0x753BC6, 0x753C4C],
                 "gate": "bound any observer before the next owner initialization; no persistence claim follows from the canonical E8-byte save-record proof"}],
            "not_a_complete_segment_flow_proof": True}


def analyze(data: bytes) -> dict:
    need(digest(data) == SHA, "wrong WSC1.5 input")
    for a, z, expected in RANGES:
        need(digest(data[a:z]) == expected, f"source range changed {a:X}")
    save = serialization(data)
    negatives = []
    for at, value, label in ((0x7860E4, 0xE9, "save record byte count changed"),
                             (0x7860F2, 0x78, "save source offset changed"),
                             (0x786135, 0x78, "save destination offset changed")):
        changed = bytearray(data)
        changed[at] = value
        try:
            serialization(changed)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"negative survived: {label}")
    for at, value, label in ((0x7693C2, 0x66, "stage11 update table target changed"),
                             (0x753CED, 7, "generic record stride changed"),
                             (0x3B518C, 1, "Shoot descriptor animation changed")):
        changed = bytearray(data)
        changed[at] = value
        try:
            shoot_background_family(changed)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"negative survived: {label}")
    for function, at, value, label in ((object_pool, 0x75098B, 0x11, "task allocation stride changed"),
                                       (generic_copy_family, 0x76B672, 1, "generic copy byte count changed")):
        changed = bytearray(data)
        changed[at] = value
        try:
            function(changed)
        except ValueError:
            negatives.append(label)
        else:
            raise ValueError(f"negative survived: {label}")
    return {"schema": 1, "kind": "shoot-source-SRAM-boundary-inventory", "source_sha256": SHA,
            "result": "UNRESOLVED_OBSERVER", "save_record": save,
            "simple_alias_inventory": alias_inventory(data), "segment_inventory": segment_inventory(data),
            "indirect_families": indirect_families(data), "object_pool": object_pool(data),
            "generic_copy_family": generic_copy_family(data),
            "argument_segment_inventory": argument_reader_inventory(data), "semantic_negatives": negatives,
            "source_store_linear": [0x13CD8, 0x13CDA], "source_ordinary_HP_linear": [0xFCD8, 0xFCDA],
            "dead_store_proven": False, "native_storage_mapping_proven": False,
            "scoped_first_milestone_no_observer_proven": False,
            "no_CPU_execution": True, "no_save_access": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    report = analyze(args.wsc15.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-SRAM-boundary] record/alias inventory PASS; observer remains unresolved; SHA {digest(args.output.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
