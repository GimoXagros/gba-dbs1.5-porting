#!/usr/bin/env python3
"""Independently verify the resident Shoot parent callback chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct
import sys


SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "vendor"))

from capstone import CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_LITTLE_ENDIAN, Cs  # type: ignore


INPUT_SHA256 = "9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B"
OUTPUT_SHA256 = "B192AC03F75FB1B55B3BCB3BA6363836EDDFCBBAC8379DAF6D9DAB08B9AD2E06"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

PLACEMENTS = {
    "parent_9083": (0x5BA800, 136, "54FDA0B58692F92B87A62EB2877DFAE9E55AF9FA70617AC97E5823CE86ED3E96"),
    "parent_90F3": (0x5BAC00, 116, "07A29D0C7A562B7F1B498C26935B88850BACCCECFC3438A8532F9F719DC2DE50"),
    "parent_912A": (0x5BB000, 192, "90F62ACD55E5EEFC65864E037645CBB476EE958A5A275076B7E2D9774E682C6E"),
    "parent_91AB": (0x5BB400, 144, "D35948D908961E3857369C619FA3EA2C93A82B846C535EC4ADBB6C07A288495B"),
    "parent_91EF": (0x5BB800, 116, "C1874133AC6E3F0B6521CD1923D3BFAC834C8457C23F8AC3F17BCDD9344A5033"),
    "idle_88F7": (0x5BBC00, 4, "379BEC29DCCD0A93C94826144D7EF6E42FAB64EF195A3B8313A16926F66F388F"),
}
CODE_BYTES = {
    "parent_9083": 132,
    "parent_90F3": 112,
    "parent_912A": 184,
    "parent_91AB": 140,
    "parent_91EF": 112,
    "idle_88F7": 4,
}
EXPECTED_CALLS = {
    "parent_9083": [0x08012874, 0x080D15C0],
    "parent_90F3": [0x08012A84, 0x08012874],
    "parent_912A": [0x08012348, 0x085B9400, 0x08012874, 0x080D15C0, 0x08012A84],
    "parent_91AB": [0x08012348, 0x08012874, 0x08012A84],
    "parent_91EF": [0x08012A84],
    "idle_88F7": [],
}
EXPECTED_CHAIN_REFS = [
    (0x5BA884, 0x085BAC00),
    (0x5BAC70, 0x085BB000),
    (0x5BB0BC, 0x085BB400),
    (0x5BB48C, 0x085BB800),
    (0x5BB870, 0x085BBC00),
]
WSC_RANGES = {
    "parent_9083": (0x749983, 0x7499F3, "E2F13CA4D554572C9E39C990ECCEBA95590AC62B38A44B69A49849EAA034C1EF"),
    "parent_90F3": (0x7499F3, 0x749A2A, "FC706E9021C458B6CB85B8C212AFA55AE28B72E27C54521E48D8BB892A692F5D"),
    "parent_912A": (0x749A2A, 0x749AAB, "71F987BAD4678D260548F6CBBD17E2B644AC8DFA5DF468108668AFAABE2FBC8B"),
    "parent_91AB": (0x749AAB, 0x749AEF, "6A8E13247F7BCD455F32BD0AABF52FFB5A8F614C08FBE31BFA3FF096617E41DD"),
    "parent_91EF": (0x749AEF, 0x749B29, "5389D0B3AA322CCCEDB896E497643CC12D707EB7A936EE12AAFF1D8FC191F374"),
    "idle_88F7": (0x7491F7, 0x7491F8, "383E5D7D58CAA41CE723CF16AF471B38F6EE9065C032D07FA6BEF1678CB72F1D"),
}
GBA_ORACLE_RANGES = {
    "commercial_child_family": (0x372110, 0x3723D8, "DF86BE1070A859F610416FEA03ECB5EABA1F1EA4E34118EE9DE35255E65793EC"),
    "native_presentation_event": (0x012874, 0x0128A4, "CC3B4B100C5BD7E06609D7C6D409C71481FB5362A86497C23D25A132770E0139"),
    "native_presentation_update": (0x012A84, 0x012AB4, "C3152EF1C9ADE9513E577FE5D5B690F562C2E817856D5F00DD5A76C4017E2EA7"),
    "native_trig_y": (0x012348, 0x012378, "366663ECC1E1BC7E342706C6AA04B8726861DC72FB06809763812337FB9FDF50"),
    "native_sound_request": (0x0D15C0, 0x0D15F0, "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def arm_branch_target(address: int, word: int) -> int:
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def disassemble_function(blob: bytes, address: int) -> tuple[list[dict[str, object]], list[int]]:
    engine = Cs(CS_ARCH_ARM, CS_MODE_ARM | CS_MODE_LITTLE_ENDIAN)
    instructions = list(engine.disasm(blob, address))
    if sum(instruction.size for instruction in instructions) != len(blob):
        raise SystemExit(f"ARM disassembly does not cover 0x{address:08X}")
    forbidden = {"movw", "movt", "blx", "bxj", "ldrex", "strex", "clz"}
    bad = [instruction.mnemonic for instruction in instructions if instruction.mnemonic in forbidden]
    if bad:
        raise SystemExit(f"non-ARM7TDMI instruction in 0x{address:08X}: {bad}")
    calls = []
    rendered = []
    for instruction in instructions:
        word = struct.unpack("<I", instruction.bytes)[0]
        if word & 0x0F000000 == 0x0B000000:
            calls.append(arm_branch_target(instruction.address, word))
        rendered.append({
            "address": instruction.address,
            "mnemonic": instruction.mnemonic,
            "op_str": instruction.op_str,
        })
    return rendered, calls


def aligned_refs(data: bytes, start: int, end: int) -> list[tuple[int, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + start <= value < GBA_BASE + end:
            refs.append((offset, value))
    return refs


def require_words(data: bytes, assertions: dict[int, tuple[int, ...]]) -> None:
    for offset, expected in assertions.items():
        actual = struct.unpack_from(f"<{len(expected)}I", data, offset)
        if actual != expected:
            raise SystemExit(f"parent semantic words changed at 0x{offset:X}: {actual}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    gba = args.gba.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, INPUT_SHA256, "v40 candidate")
    require_hash(after, OUTPUT_SHA256, "v41 Shoot-parent candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != 0x800000 or len(after) != len(before):
        raise SystemExit("candidate size changed")
    for label, (start, end, digest) in WSC_RANGES.items():
        require_hash(wsc15[start:end], digest, label)
    for label, (start, end, digest) in GBA_ORACLE_RANGES.items():
        require_hash(gba[start:end], digest, label)

    allowed = set()
    functions = {}
    for label, (offset, size, digest) in PLACEMENTS.items():
        if before[offset:offset + size] != bytes([0xFF]) * size:
            raise SystemExit(f"{label} preimage is not blank")
        blob = after[offset:offset + size]
        require_hash(blob, digest, label)
        instructions, calls = disassemble_function(
            blob[:CODE_BYTES[label]], GBA_BASE + offset
        )
        if calls != EXPECTED_CALLS[label]:
            raise SystemExit(f"{label} call graph changed: {calls}")
        functions[label] = {
            "target": offset,
            "bytes": size,
            "code_bytes": CODE_BYTES[label],
            "literal_bytes": size - CODE_BYTES[label],
            "sha256": digest,
            "instruction_count": len(instructions),
            "call_targets": calls,
        }
        allowed.update(range(offset, offset + size))
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("Shoot parent layer has an unexplained diff")

    refs_before = aligned_refs(before, 0x5BA800, 0x5BC100)
    refs_after = aligned_refs(after, 0x5BA800, 0x5BC100)
    if refs_before:
        raise SystemExit("v40 already references the Shoot parent window")
    if refs_after != EXPECTED_CHAIN_REFS:
        raise SystemExit(f"Shoot parent callback chain changed: {refs_after}")

    require_words(after, {
        # 9083: four motion clears, target pointer/position, linked object flag,
        # and CE -> native 0x5B request arguments.
        0x5BA804: (0xE3A08000, 0xE1C484B2, 0xE1C484B4, 0xE1C484B6, 0xE1C484B8),
        0x5BA818: (0xE5941018, 0xE1D103F4, 0xE1C403B4, 0xE1D103F6, 0xE2400C03, 0xE1C403B6),
        0x5BA854: (0xE5941028, 0xE1D18AB0, 0xE3888001, 0xE1C18AB0),
        0x5BA864: (0xE3A0805B, 0xE3A09001, 0xE3A0A000),
        # 90F3: WSC +7E/+80 become GBA +94/+96 and preserve 60 ticks.
        0x5BAC34: (0xE3A08000, 0xE1C489B4, 0xE3A0803C, 0xE1C489B6),
        # 912A: low-byte phase, Y sine / 8, 0x40 Shoot flag, event-2 timer,
        # and A7 -> native 0x4A request arguments.
        0x5BB004: (0xE1D489B4, 0xE2888001, 0xE20880FF, 0xE1C489B4),
        0x5BB020: (0xE1A001C0, 0xE1C404B4),
        0x5BB044: (0xE1D890B0, 0xE3899040, 0xE1C890B0),
        0x5BB06C: (0xE3A08026, 0xE1C489B6, 0xE3A0804A, 0xE3A09001, 0xE3A0A000),
        # 91AB repeats phase/Y motion and emits event 3.
        0x5BB404: (0xE1D489B4, 0xE2888001, 0xE20880FF, 0xE1C489B4),
        0x5BB448: (0xE3A08003, 0xE52D8004),
        # 91EF restores object/link flags, offscreen X and source +94 -> GBA +AA.
        0x5BB834: (0xE1D480B4, 0xE3888020, 0xE1C480B4, 0xE3A08B3F, 0xE1C483B4),
        0x5BB848: (0xE3A08000, 0xE1C48ABA, 0xE5941028, 0xE1D18AB0, 0xE3C88001, 0xE1C18AB0),
        0x5BBC00: (0xE12FFF1E,),
    })

    result = {
        "schema": 1,
        "kind": "independent-shoot-parent-integration-verification",
        "claim_scope": (
            "exact diff containment, ARM7TDMI final-placement disassembly, native call "
            "graphs, translated object-field/timer/event semantics, internal parent chain, "
            "child-generator edge, and 0x5B/0x4A sound request arguments; controller "
            "9908/9A1B entry, runtime reachability, and audible playback excluded"
        ),
        "before_sha256": INPUT_SHA256,
        "after_sha256": OUTPUT_SHA256,
        "changed_bytes": len(changed),
        "functions": functions,
        "chain_refs_before": [],
        "chain_refs_after": [
            {"offset": offset, "value": value} for offset, value in refs_after
        ],
        "child_generator": 0x085B9400,
        "audio_requests": [
            {"wsc_sound_id": 0xCE, "gba_sound_id": 0x5B, "request_type": 1},
            {"wsc_sound_id": 0xA7, "gba_sound_id": 0x4A, "request_type": 1},
        ],
        "external_entry_connected": False,
        "runtime_reachability_verified": False,
        "runtime_audibility_verified": False,
        "known_exclusion": "controller 9908/9A1B callback assignment to parent 9083",
    }
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
