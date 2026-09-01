#!/usr/bin/env python3
"""Prove the commercial sound-request mapping needed by Shoot helper 9229."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
WSC10_OVERLAY_BASE = 0x390900
WSC15_OVERLAY_BASE = 0x740900
WSC10_SOUND_BANK = 0x2D0000
WSC15_SOUND_BANK = 0x3F0000
GBA_BASE = 0x08000000
GBA_SOUND_REQUEST = 0x080D15C0

# The commercial object overlay preserves these eleven source requests and
# their GBA call sites in the same order.  That complete local population is
# the oracle for ID conversion and request-type preservation.
COMMERCIAL_ROWS = (
    (0x44B1, 0xA9, 1, 0x370598, 0x4D, 1),
    (0x459A, 0xA6, 1, 0x370708, 0x4B, 1),
    (0x47C3, 0xA9, 1, 0x370AA8, 0x4D, 1),
    (0x48ED, 0xA9, 1, 0x370C7C, 0x4D, 1),
    (0x4C09, 0xA6, 1, 0x37101C, 0x4B, 1),
    (0x4C89, 0xB5, 1, 0x3710D8, 0x56, 1),
    (0x4E54, 0xA5, 1, 0x371374, 0x4A, 1),
    (0x525E, 0xA7, 2, 0x3719C0, 0x4C, 2),
    (0x54E4, 0xA9, 1, 0x371DD0, 0x4D, 1),
    (0x58A5, 0xA5, 1, 0x3723F8, 0x4A, 1),
    (0x5A3D, 0x9E, 1, 0x3726BC, 0x43, 1),
)

WSC15_TARGETS = {
    "parent_9083_initial": (0x90D3, 0xCE, 1),
    "parent_912A_post_generator": (0x918B, 0xA7, 1),
    "generator_9229_post_event": (0x9313, 0xA7, 1),
}

# Both sound banks begin with six-byte entries.  The final word is the offset
# of the corresponding command payload in the same 64 KiB bank.  Ver. 1.5
# inserted effects into this table, so equal numeric IDs are not sufficient
# evidence of equal sound content.
WSC10_A5_PAYLOAD_SHA256 = (
    "CDD28BC3E81D811B70ABFDA759D8A5EDFF046DDF732F5774527D4867C35C00EB"
)
WSC10_A7_PAYLOAD_SHA256 = (
    "68CA1B6E09B82F7BAB3F0BA06D37FFF0FB539E0D85A75BAEBCBA12DEE89736FF"
)
WSC15_CE_PAYLOAD_SHA256 = (
    "79BB15C2643DA24DAC1A16D7B760977257A7ABCA0B3DAE82383F85EFEF7C80B6"
)

NATIVE_REQUEST_SHA256 = (
    "00927E579F643E6FA62BB58C826DCB7ED6FEA4E9367EC84295C9EF48257B6685"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"refusing unknown {label}: {actual}")


def branch_target(address: int, word: int) -> int:
    if word & 0x0F000000 != 0x0B000000:
        raise SystemExit(f"expected ARM BL at 0x{address:08X}")
    displacement = word & 0x00FFFFFF
    if displacement & 0x00800000:
        displacement -= 0x01000000
    return (address + 8 + displacement * 4) & 0xFFFFFFFF


def check_wsc_request(bank: bytes, offset: int, sound_id: int, request_type: int) -> None:
    expected = (
        bytes.fromhex("C7 44 02")
        + struct.pack("<H", sound_id)
        + bytes.fromhex("C7 44 0E")
        + struct.pack("<H", request_type)
        + bytes.fromhex("C7 44 06 00 00 81 4C 10 00 01")
    )
    if bank[offset:offset + len(expected)] != expected:
        raise SystemExit(f"WSC sound request changed at overlay offset 0x{offset:04X}")
    if bytes.fromhex("BE 0E 39") not in bank[max(0, offset - 16):offset]:
        raise SystemExit(f"WSC sound-request base was not selected at 0x{offset:04X}")


def check_gba_request(
    gba: bytes,
    call_offset: int,
    sound_id: int,
    request_type: int,
) -> None:
    expected_words = (
        0xE3A08000 | sound_id,
        0xE3A09000 | request_type,
        0xE3A0A000,
    )
    actual_words = struct.unpack_from("<III", gba, call_offset - 12)
    if actual_words != expected_words:
        raise SystemExit(f"GBA sound arguments changed at 0x{GBA_BASE + call_offset:08X}")
    call_word = struct.unpack_from("<I", gba, call_offset)[0]
    if branch_target(GBA_BASE + call_offset, call_word) != GBA_SOUND_REQUEST:
        raise SystemExit(f"GBA sound target changed at 0x{GBA_BASE + call_offset:08X}")


def sound_entry(data: bytes, bank: int, sound_id: int) -> tuple[int, int, int]:
    return struct.unpack_from("<HHH", data, bank + sound_id * 6)


def sound_payload(data: bytes, bank: int, sound_id: int) -> bytes:
    start = sound_entry(data, bank, sound_id)[2]
    end = sound_entry(data, bank, sound_id + 1)[2]
    if not (0x400 <= start < end <= 0xFFFF):
        raise SystemExit(
            f"invalid sound payload boundary for ID 0x{sound_id:02X}: "
            f"0x{start:04X}..0x{end:04X}"
        )
    return data[bank + start:bank + end]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    old = wsc10[WSC10_OVERLAY_BASE:WSC10_OVERLAY_BASE + 0x10000]
    new = wsc15[WSC15_OVERLAY_BASE:WSC15_OVERLAY_BASE + 0x10000]

    rows = []
    for old_offset, old_id, old_type, gba_call, gba_id, gba_type in COMMERCIAL_ROWS:
        check_wsc_request(old, old_offset, old_id, old_type)
        check_gba_request(gba, gba_call, gba_id, gba_type)
        rows.append({
            "wsc10": {
                "request_offset": old_offset,
                "sound_id": old_id,
                "request_type": old_type,
            },
            "gba": {
                "call_address": GBA_BASE + gba_call,
                "sound_id": gba_id,
                "request_type": gba_type,
                "third_argument": 0,
                "target": GBA_SOUND_REQUEST,
            },
        })

    native_request = gba[0x0D15C0:0x0D15F0]
    require_hash(native_request, NATIVE_REQUEST_SHA256, "native GBA sound request")
    if struct.unpack_from("<I", native_request, 0x2C)[0] != 0x030022F0:
        raise SystemExit("native GBA sound-request state pointer changed")

    old_a5 = sound_payload(wsc10, WSC10_SOUND_BANK, 0xA5)
    old_a7 = sound_payload(wsc10, WSC10_SOUND_BANK, 0xA7)
    new_a7 = sound_payload(wsc15, WSC15_SOUND_BANK, 0xA7)
    new_ce = sound_payload(wsc15, WSC15_SOUND_BANK, 0xCE)
    require_hash(old_a5, WSC10_A5_PAYLOAD_SHA256, "WSC 1.0 sound A5 payload")
    require_hash(old_a7, WSC10_A7_PAYLOAD_SHA256, "WSC 1.0 sound A7 payload")
    require_hash(new_a7, WSC10_A5_PAYLOAD_SHA256, "WSC 1.5 sound A7 payload")
    require_hash(new_ce, WSC15_CE_PAYLOAD_SHA256, "WSC 1.5 sound CE payload")
    if new_a7 == old_a7:
        raise SystemExit("WSC 1.5 A7 unexpectedly still matches WSC 1.0 A7")

    # B9 is the final WSC 1.0 table entry and has no following table pointer,
    # so compare CE against the 185 independently bounded payloads 00..B8.
    a7_old_matches = [
        sound_id
        for sound_id in range(0xB9)
        if sound_payload(wsc10, WSC10_SOUND_BANK, sound_id) == new_a7
    ]
    if a7_old_matches != [0xA5]:
        raise SystemExit(f"WSC 1.5 A7 payload lineage is not unique: {a7_old_matches}")
    ce_old_matches = [
        sound_id
        for sound_id in range(0xB9)
        if sound_payload(wsc10, WSC10_SOUND_BANK, sound_id) == new_ce
    ]
    if ce_old_matches:
        raise SystemExit(f"WSC 1.5 CE unexpectedly matches old sounds: {ce_old_matches}")

    old_a5_rows = [row for row in rows if row["wsc10"]["sound_id"] == 0xA5]
    if len(old_a5_rows) != 2 or any(row["gba"]["sound_id"] != 0x4A for row in old_a5_rows):
        raise SystemExit("commercial WSC 1.0 A5 to GBA 0x4A mapping is not stable")

    targets = {}
    for label, (offset, sound_id, request_type) in WSC15_TARGETS.items():
        check_wsc_request(new, offset, sound_id, request_type)
        targets[label] = {
            "request_offset": offset,
            "sound_id": sound_id,
            "request_type": request_type,
            "mapped_gba_sound_id": 0x4A if sound_id == 0xA7 else None,
            "mapped_gba_request_type": request_type,
            "mapped_gba_third_argument": 0,
            "mapped_gba_target": GBA_SOUND_REQUEST,
            "mapping_status": (
                "exact payload identity with WSC 1.0 A5"
                if sound_id == 0xA7
                else "Ver. 1.5-only payload; no commercial GBA mapping"
            ),
        }

    if any(row["wsc10"]["request_type"] != row["gba"]["request_type"] for row in rows):
        raise SystemExit("commercial sound request types do not map identically")

    result = {
        "schema": 1,
        "kind": "digimon-shoot-audio-request-lineage",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc_10_sha256": WSC10_SHA256,
            "wsc_15_sha256": WSC15_SHA256,
        },
        "commercial_oracle": rows,
        "native_gba_request": {
            "address": GBA_SOUND_REQUEST,
            "state": 0x030022F0,
            "bytes": len(native_request),
            "sha256": NATIVE_REQUEST_SHA256,
            "semantics": (
                "when state+6 is zero, store r8 at +2, r9 at +0xE, r10 at +6, "
                "and set state+0x10 bit 0x100"
            ),
        },
        "wsc_payload_lineage": {
            "entry_bytes": 6,
            "wsc_10_bank": WSC10_SOUND_BANK,
            "wsc_15_bank": WSC15_SOUND_BANK,
            "wsc_15_a7": {
                "entry": sound_entry(wsc15, WSC15_SOUND_BANK, 0xA7),
                "payload_bytes": len(new_a7),
                "payload_sha256": sha256(new_a7),
                "exact_wsc_10_sound_id": 0xA5,
                "exact_matches_in_bounded_wsc_10_ids_00_b8": a7_old_matches,
                "does_not_match_wsc_10_same_id": True,
            },
            "wsc_10_a5": {
                "entry": sound_entry(wsc10, WSC10_SOUND_BANK, 0xA5),
                "payload_bytes": len(old_a5),
                "payload_sha256": sha256(old_a5),
                "commercial_gba_sound_id": 0x4A,
            },
            "wsc_10_a7": {
                "entry": sound_entry(wsc10, WSC10_SOUND_BANK, 0xA7),
                "payload_bytes": len(old_a7),
                "payload_sha256": sha256(old_a7),
                "commercial_gba_sound_id": 0x4C,
            },
            "wsc_15_ce": {
                "entry": sound_entry(wsc15, WSC15_SOUND_BANK, 0xCE),
                "payload_bytes": len(new_ce),
                "payload_sha256": sha256(new_ce),
                "exact_matches_in_bounded_wsc_10_ids_00_b8": ce_old_matches,
                "commercial_gba_sound_id": None,
            },
        },
        "wsc_15_targets": targets,
        "proved_mapping": {
            "wsc_15_sound_id": 0xA7,
            "exact_wsc_10_payload_id": 0xA5,
            "gba_sound_id": 0x4A,
            "request_type": "preserved",
            "third_argument": 0,
            "target": GBA_SOUND_REQUEST,
        },
        "unresolved_mapping": {
            "wsc_15_sound_id": 0xCE,
            "reason": "Ver. 1.5-only command payload with no exact WSC 1.0 payload",
            "required_action": "reconstruct a GBA-native sound asset before parent 9083 is connected",
        },
        "claim_scope": (
            "static commercial WSC 1.0/GBA request lineage plus exact WSC payload "
            "identity proving Ver. 1.5 A7 maps through WSC 1.0 A5 to GBA 0x4A; "
            "Ver. 1.5-only CE reconstruction, audible playback, and timing unverified"
        ),
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
