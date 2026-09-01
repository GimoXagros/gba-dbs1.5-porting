#!/usr/bin/env python3
"""Append a bounded GBA-native reconstruction of WSC Ver. 1.5 sound D2."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

SONG_TABLE = 0x5BA400
EXISTING_SONG_COUNT = 0x5C
EXISTING_TABLE_BYTES = EXISTING_SONG_COUNT * 8
EXISTING_TABLE_SHA256 = "E2F3C91FFD89DADF3FA0614CBF6C2C49E24B6EAD7206846A36C7844F48CFD047"
NEW_SOUND_ID = 0x5C
NEW_ENTRY = SONG_TABLE + NEW_SOUND_ID * 8
NEW_SONG = 0x5BA740
VOICEGROUP = 0x0837E8E0
REUSED_VOICE = 0x1F
REUSED_VOICE_SHA256 = "8010A2A5E255DC761E08F135F293FDCB5ADCFDCC6E0FCF9BB1A9709DC0154110"

D2_ENTRY_OFFSET = 0x3F04EC
D2_ENTRY_SHA256 = "5EA90B816BE59A873B44FC1854C7350E9D49F7ABA35D876C2B5CA66424944509"
D2_PAYLOAD_OFFSET = 0x3F8984
D2_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A1 09 A2 01 C1 00 A3 20 "
    "20 28 18 05 17 05 16 05 15 05 14 05 13 05 12 05 11 05 FF FF"
)
D2_PAYLOAD_SHA256 = "740A62271CDCF1636D420486F526461D81DD4271EF705D3DAEC09D2871928641"
WSC10_B5_PAYLOAD_OFFSET = 0x2D849C
WSC10_B5_PAYLOAD = bytes.fromhex(
    "08 00 0F 01 A2 01 C2 18 00 02 1F 01 00 08 FF FF"
)
WSC10_B5_PAYLOAD_SHA256 = "97BD88AB91C648C8A5E58D7DB46C4E70C25EC0D8E63C0DD92EDD4FBB53625FF7"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def aligned_pointer_refs(data: bytes, start: int, end: int) -> list[dict[str, int]]:
    refs = []
    for offset in range(0, len(data) - 3, 4):
        value = struct.unpack_from("<I", data, offset)[0]
        if GBA_BASE + start <= value < GBA_BASE + end:
            refs.append({"offset": offset, "value": value})
    return refs


def wsc_note_to_midi(note: int) -> int:
    semitone = note & 0x0F
    if semitone > 0x0B:
        raise SystemExit(f"invalid packed WSC note 0x{note:02X}")
    return 36 + (note >> 4) * 12 + semitone


def build_track() -> tuple[bytes, list[dict[str, int]]]:
    schedule = [(0x20, 40)] + [(note, 5) for note in range(0x18, 0x10, -1)]
    if sum(ticks for _, ticks in schedule) != 80:
        raise SystemExit("D2 schedule length changed")
    duration_opcodes = {40: (0xEC, 0x9D), 5: (0xD4, 0x85)}
    track = bytearray([
        0xBC, 0x00,       # KEYSH 0
        0xBB, 0x4B,       # TEMPO 75, commercial SFX convention
        0xBD, REUSED_VOICE,
        0xBE, 0x7F,       # source right-channel volume nibble is 0xF
        0xBF, 0x7F,       # source 0x0F is left 0 / right 15
        0xC2, 0x10,       # LFOS: native controller for A3 modulation
        0xC4, 0x20,       # MOD: bounded A3=0x20 analogue
        0xC5, 0x00,       # MODT pitch
    ])
    rendered = []
    for packed_note, ticks in schedule:
        note_opcode, wait_opcode = duration_opcodes[ticks]
        midi_note = wsc_note_to_midi(packed_note)
        track.extend((note_opcode, midi_note, 0x7F, wait_opcode))
        rendered.append({
            "packed_wsc_note": packed_note,
            "midi_note": midi_note,
            "ticks": ticks,
            "note_opcode": note_opcode,
            "wait_opcode": wait_opcode,
        })
    track.extend((0xC4, 0x00, 0xB1))  # disable MOD, FINE
    return bytes(track), rendered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(source, INPUT_SHA256, "v42 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    existing_table = source[SONG_TABLE:SONG_TABLE + EXISTING_TABLE_BYTES]
    require_hash(existing_table, EXISTING_TABLE_SHA256, "v42 song table IDs 00..5B")
    require_hash(wsc15[D2_ENTRY_OFFSET:D2_ENTRY_OFFSET + 6], D2_ENTRY_SHA256, "D2 entry")
    d2_payload = wsc15[D2_PAYLOAD_OFFSET:D2_PAYLOAD_OFFSET + len(D2_PAYLOAD)]
    require_hash(d2_payload, D2_PAYLOAD_SHA256, "D2 payload")
    if d2_payload != D2_PAYLOAD:
        raise SystemExit("D2 payload bytes changed")
    b5_payload = wsc10[WSC10_B5_PAYLOAD_OFFSET:WSC10_B5_PAYLOAD_OFFSET + len(WSC10_B5_PAYLOAD)]
    require_hash(b5_payload, WSC10_B5_PAYLOAD_SHA256, "WSC 1.0 B5 payload")
    if b5_payload != WSC10_B5_PAYLOAD or bytes((0xA2, 1)) not in b5_payload:
        raise SystemExit("commercial A2=01 timbre oracle changed")
    voice_offset = (VOICEGROUP - GBA_BASE) + REUSED_VOICE * 12
    require_hash(gba[voice_offset:voice_offset + 12], REUSED_VOICE_SHA256, "commercial GBA voice 1F")

    track, schedule = build_track()
    song = (
        bytes((1, 0, 0x28, 0x80))
        + struct.pack("<I", VOICEGROUP)
        + struct.pack("<I", GBA_BASE + NEW_SONG + 12)
        + track
    )
    entry = struct.pack("<IHH", GBA_BASE + NEW_SONG, 4, 4)
    placements = (
        (NEW_ENTRY, entry, "song_table_entry_5C"),
        (NEW_SONG, song, "wsc15_d2_gba_song_5C"),
    )

    refs_before = (
        aligned_pointer_refs(source, NEW_ENTRY, NEW_ENTRY + len(entry))
        + aligned_pointer_refs(source, NEW_SONG, NEW_SONG + len(song))
    )
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches D2 ownership bytes: {refs_before}")
    patched = bytearray(source)
    allowed = set()
    expected_writes = []
    for offset, blob, label in placements:
        before = bytes(patched[offset:offset + len(blob)])
        if before != bytes([0xFF]) * len(blob):
            raise SystemExit(f"{label} Expected Write input is not all FF")
        patched[offset:offset + len(blob)] = blob
        allowed.update(range(offset, offset + len(blob)))
        expected_writes.append({
            "label": label,
            "target": offset,
            "bytes": len(blob),
            "before_sha256": sha256(before),
            "after_sha256": sha256(blob),
        })

    changed = {
        offset
        for offset, (left, right) in enumerate(zip(source, patched, strict=True))
        if left != right
    }
    if not changed or not changed <= allowed:
        raise SystemExit("D2 sound integration contains an unexplained diff")

    output = bytes(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-d2-native-sound-build",
        "claim_scope": (
            "GBA-native D2 reconstruction preserving exact packed pitches, 80-tick "
            "schedule, source stereo direction, commercial A2=01 timbre lineage, and "
            "a native pitch-modulation controller; upper-state request connection, "
            "conditional WSC channel-3 sweep parity, audibility, and runtime excluded"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "expected_writes": expected_writes,
        "changed_bytes": len(changed),
        "preexisting_aligned_pointer_refs": refs_before,
        "wsc_source": {
            "sound_id": 0xD2,
            "entry_offset": D2_ENTRY_OFFSET,
            "entry_sha256": D2_ENTRY_SHA256,
            "payload_offset": D2_PAYLOAD_OFFSET,
            "payload_bytes": len(D2_PAYLOAD),
            "payload_sha256": D2_PAYLOAD_SHA256,
            "setup": {"A1": 0x09, "A2": 0x01, "C1": 0x00, "A3": 0x20},
        },
        "gba_reconstruction": {
            "sound_id": NEW_SOUND_ID,
            "song_table": GBA_BASE + SONG_TABLE,
            "entry": GBA_BASE + NEW_ENTRY,
            "song": GBA_BASE + NEW_SONG,
            "track": GBA_BASE + NEW_SONG + 12,
            "voicegroup": VOICEGROUP,
            "reused_voice": REUSED_VOICE,
            "reused_voice_sha256": REUSED_VOICE_SHA256,
            "pan": 127,
            "schedule": schedule,
            "total_ticks": sum(row["ticks"] for row in schedule),
            "track_bytes": len(track),
            "track_sha256": sha256(track),
            "song_bytes": len(song),
            "song_sha256": sha256(song),
        },
        "external_requests_connected": False,
        "runtime_audibility_verified": False,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-d2-sound] output SHA-256 {result['output_sha256']}")
    print(f"[shoot-d2-sound] song SHA-256 {result['gba_reconstruction']['song_sha256']}")
    print(f"[shoot-d2-sound] track SHA-256 {result['gba_reconstruction']['track_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
