#!/usr/bin/env python3
"""Independently verify the bounded WSC Ver. 1.5 CE sound reconstruction."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492"
OUTPUT_SHA256 = "9219F992A90CDBF29006663BFB3752FE615000DE14C6594A86D9976695CFC66B"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OLD_TABLE = 0x37FC20
OLD_TABLE_BYTES = 0x5B * 8
OLD_TABLE_SHA256 = "8AFEDFFA4774585E60486D780DD2308CD1D07F913B683313656CB2E3D8159AF8"
NEW_TABLE = 0x5BA400
NEW_TABLE_BYTES = 0x5C * 8
NEW_TABLE_SHA256 = "E2F3C91FFD89DADF3FA0614CBF6C2C49E24B6EAD7206846A36C7844F48CFD047"
NEW_SOUND_ID = 0x5B
NEW_SONG = 0x5BA700
NEW_SONG_BYTES = 39
NEW_SONG_SHA256 = "928A5A4515B441E64AB4C08701D7A129B3631EAA92A26C1C3706E6B4727C8D5E"
NEW_TRACK = NEW_SONG + 12
TRACK_SHA256 = "78142A6B701612C117ECE3CAC845DC3ABEC777BC2040CCF291396BED399B06D2"
VOICEGROUP = 0x0837E8E0
REUSED_VOICE = 0x14
REUSED_VOICE_SHA256 = "1E65392E06FA504CD467F2C2471D540ED25CBA145F7EAE045379C5D3D11D2B94"
LITERAL_SITES = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)

CE_ENTRY_OFFSET = 0x3F04D4
CE_ENTRY = bytes.fromhex("54 00 02 00 FC 88")
CE_ENTRY_SHA256 = "5D3262C7097F3AFD35B942F2CA418EFB33786E408B05551847E53690EA8A505F"
CE_PAYLOAD_OFFSET = 0x3F88FC
CE_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A2 02 C1 00 A1 72 10 14 A0 09 A7 0A "
    "A0 06 A7 0A A0 03 A7 0A A0 01 A7 0A FF FF"
)
CE_PAYLOAD_SHA256 = "79BB15C2643DA24DAC1A16D7B760977257A7ABCA0B3DAE82383F85EFEF7C80B6"
TRACK = bytes.fromhex(
    "BC 00 BB 4B BD 14 BE 7F BF 40 F7 30 7F 94 "
    "BE 4C 8A BE 33 8A BE 19 8A BE 08 8A B1"
)
M4A_NOTE_DURATIONS = (
    *range(1, 25), 28, 30, 32, 36, 40, 42, 44, 48, 52, 54, 56, 60,
    64, 66, 68, 72, 76, 78, 80, 84, 88, 90, 92, 96,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def aligned_word_refs(data: bytes, value: int) -> list[int]:
    encoded = struct.pack("<I", value)
    return [offset for offset in range(0, len(data) - 3, 4) if data[offset:offset + 4] == encoded]


def verify_wsc_semantics(payload: bytes) -> dict[str, object]:
    if payload != CE_PAYLOAD:
        raise SystemExit("WSC CE payload bytes changed")
    if payload[:8] != bytes.fromhex("00 00 0F 01 A2 02 C1 00"):
        raise SystemExit("WSC CE setup commands changed")
    if payload[8:12] != bytes((0xA1, 0x72, 0x10, 0x14)):
        raise SystemExit("WSC CE note or duration changed")
    cursor = 12
    decay = []
    while cursor < len(payload) - 2:
        if payload[cursor] != 0xA0 or payload[cursor + 2] != 0xA7:
            raise SystemExit(f"WSC CE decay command changed at +0x{cursor:X}")
        decay.append((payload[cursor + 1], payload[cursor + 3]))
        cursor += 4
    if decay != [(9, 10), (6, 10), (3, 10), (1, 10)]:
        raise SystemExit(f"WSC CE decay schedule changed: {decay}")
    if payload[cursor:] != bytes((0xFF, 0xFF)):
        raise SystemExit("WSC CE terminator changed")
    packed_note = payload[10]
    midi_note = 36 + (packed_note >> 4) * 12 + (packed_note & 0x0F)
    return {
        "packed_note": packed_note,
        "midi_note": midi_note,
        "initial_ticks": payload[11],
        "decay": [{"volume": volume, "wait_ticks": wait} for volume, wait in decay],
        "total_schedule_ticks": payload[11] + sum(wait for _, wait in decay),
    }


def verify_m4a_track(track: bytes) -> dict[str, object]:
    if track != TRACK:
        raise SystemExit("reconstructed M4A track bytes changed")
    prefix = [(0xBC, 0), (0xBB, 75), (0xBD, REUSED_VOICE), (0xBE, 127), (0xBF, 64)]
    cursor = 0
    for opcode, argument in prefix:
        if tuple(track[cursor:cursor + 2]) != (opcode, argument):
            raise SystemExit(f"M4A prefix changed at +0x{cursor:X}")
        cursor += 2
    if tuple(track[cursor:cursor + 3]) != (0xF7, 48, 127):
        raise SystemExit("M4A N72 note event changed")
    note_opcode = track[cursor]
    if not 0xD0 <= note_opcode <= 0xFF:
        raise SystemExit("M4A note opcode is outside the N01..N96 range")
    gate_ticks = M4A_NOTE_DURATIONS[note_opcode - 0xD0]
    if gate_ticks != 72:
        raise SystemExit(f"M4A note gate is N{gate_ticks}, expected N72")
    cursor += 3
    if track[cursor] != 0x94:
        raise SystemExit("M4A initial W20 changed")
    cursor += 1
    decay = []
    while cursor < len(track) - 1:
        if track[cursor] != 0xBE or track[cursor + 2] != 0x8A:
            raise SystemExit(f"M4A decay command changed at +0x{cursor:X}")
        decay.append(track[cursor + 1])
        cursor += 3
    if decay != [76, 51, 25, 8] or track[cursor] != 0xB1:
        raise SystemExit(f"M4A volume schedule or FINE changed: {decay}")
    return {
        "key_shift": 0,
        "tempo": 75,
        "voice": REUSED_VOICE,
        "initial_volume": 127,
        "pan": 64,
        "gate_ticks": gate_ticks,
        "midi_note": 48,
        "velocity": 127,
        "initial_wait_ticks": 20,
        "decay_volumes": decay,
        "decay_wait_ticks": [10, 10, 10, 10],
        "total_schedule_ticks": 60,
    }


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
    require_hash(before, INPUT_SHA256, "v39 candidate")
    require_hash(after, OUTPUT_SHA256, "v40 CE-sound candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != 0x800000 or len(after) != len(before):
        raise SystemExit("candidate size changed")

    old_table = gba[OLD_TABLE:OLD_TABLE + OLD_TABLE_BYTES]
    require_hash(old_table, OLD_TABLE_SHA256, "commercial GBA song table")
    if before[OLD_TABLE:OLD_TABLE + OLD_TABLE_BYTES] != old_table:
        raise SystemExit("v39 commercial song table differs from the USA source")
    voice_offset = (VOICEGROUP - GBA_BASE) + REUSED_VOICE * 12
    require_hash(gba[voice_offset:voice_offset + 12], REUSED_VOICE_SHA256, "reused square voice")

    ce_entry = wsc15[CE_ENTRY_OFFSET:CE_ENTRY_OFFSET + len(CE_ENTRY)]
    ce_payload = wsc15[CE_PAYLOAD_OFFSET:CE_PAYLOAD_OFFSET + len(CE_PAYLOAD)]
    require_hash(ce_entry, CE_ENTRY_SHA256, "WSC Ver. 1.5 CE entry")
    require_hash(ce_payload, CE_PAYLOAD_SHA256, "WSC Ver. 1.5 CE payload")
    if ce_entry != CE_ENTRY:
        raise SystemExit("WSC Ver. 1.5 CE sound-table entry changed")
    wsc_semantics = verify_wsc_semantics(ce_payload)

    ownership_start = NEW_TABLE
    ownership_end = 0x5BA800
    if before[ownership_start:ownership_end] != bytes([0xFF]) * (ownership_end - ownership_start):
        raise SystemExit("v39 CE ownership window is not blank")
    allowed = set()
    for site in LITERAL_SITES:
        allowed.update(range(site, site + 4))
    allowed.update(range(NEW_TABLE, NEW_TABLE + NEW_TABLE_BYTES))
    allowed.update(range(NEW_SONG, NEW_SONG + NEW_SONG_BYTES))
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("CE sound layer has an unexplained diff")

    old_pointer = GBA_BASE + OLD_TABLE
    new_pointer = GBA_BASE + NEW_TABLE
    if aligned_word_refs(before, old_pointer) != list(LITERAL_SITES):
        raise SystemExit("v39 commercial song-table references changed")
    if aligned_word_refs(after, old_pointer):
        raise SystemExit("a stale commercial song-table reference remains")
    if aligned_word_refs(after, new_pointer) != list(LITERAL_SITES):
        raise SystemExit("relocated song-table references are incomplete")

    new_table = after[NEW_TABLE:NEW_TABLE + NEW_TABLE_BYTES]
    require_hash(new_table, NEW_TABLE_SHA256, "relocated/expanded song table")
    if new_table[:OLD_TABLE_BYTES] != old_table:
        raise SystemExit("relocated table does not preserve IDs 00..5A exactly")
    entry = struct.unpack_from("<IHH", new_table, NEW_SOUND_ID * 8)
    if entry != (GBA_BASE + NEW_SONG, 4, 4):
        raise SystemExit(f"new sound 5B table entry changed: {entry}")

    song = after[NEW_SONG:NEW_SONG + NEW_SONG_BYTES]
    track = after[NEW_TRACK:NEW_SONG + NEW_SONG_BYTES]
    require_hash(song, NEW_SONG_SHA256, "new sound 5B song")
    require_hash(track, TRACK_SHA256, "new sound 5B track")
    tracks, blocks, priority, reverb = struct.unpack_from("<BBBB", song, 0)
    voicegroup, track_pointer = struct.unpack_from("<II", song, 4)
    if (tracks, blocks, priority, reverb) != (1, 0, 0x28, 0x80):
        raise SystemExit("new sound 5B song header changed")
    if voicegroup != VOICEGROUP or track_pointer != GBA_BASE + NEW_TRACK:
        raise SystemExit("new sound 5B voicegroup or track pointer changed")
    m4a_semantics = verify_m4a_track(track)
    if wsc_semantics["midi_note"] != m4a_semantics["midi_note"]:
        raise SystemExit("WSC-to-M4A pitch translation changed")
    if wsc_semantics["total_schedule_ticks"] != m4a_semantics["total_schedule_ticks"]:
        raise SystemExit("WSC-to-M4A timing translation changed")

    result = {
        "schema": 1,
        "kind": "independent-shoot-ce-native-sound-verification",
        "claim_scope": (
            "static verification of exact diff containment, complete song-table relocation, "
            "WSC CE payload semantics, and an exact GBA M4A reconstruction of pitch/timing/"
            "volume decay; parent request connection, audible timbre parity, and runtime "
            "playback are excluded"
        ),
        "before_sha256": INPUT_SHA256,
        "after_sha256": OUTPUT_SHA256,
        "changed_bytes": len(changed),
        "literal_sites": list(LITERAL_SITES),
        "old_table_sha256": OLD_TABLE_SHA256,
        "new_table_sha256": NEW_TABLE_SHA256,
        "new_sound_id": NEW_SOUND_ID,
        "song_sha256": NEW_SONG_SHA256,
        "track_sha256": TRACK_SHA256,
        "wsc_ce": wsc_semantics,
        "m4a_reconstruction": m4a_semantics,
        "external_request_connected": False,
        "runtime_audibility_verified": False,
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
