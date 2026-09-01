#!/usr/bin/env python3
"""Independently verify the bounded WSC Ver. 1.5 D2 sound reconstruction."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


BEFORE_SHA256 = "AC54D27E33F1C7A8072761B6F4CBAD7AAD89C4EC6184568020B0089037D7218E"
AFTER_SHA256 = "7BB890FEC50BBAB796B5F94FE7761EAE9C4A284BB8E3CC9FA75A12FD20FB2264"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

SONG_TABLE = 0x5BA400
OLD_TABLE_BYTES = 0x5C * 8
OLD_TABLE_SHA256 = "E2F3C91FFD89DADF3FA0614CBF6C2C49E24B6EAD7206846A36C7844F48CFD047"
NEW_SOUND_ID = 0x5C
NEW_ENTRY = 0x5BA6E0
NEW_ENTRY_BYTES = bytes.fromhex("40 A7 5B 08 04 00 04 00")
NEW_ENTRY_SHA256 = "14491F9D820F7D318C9EBA406EFC4AA8159CE183C3C17776939275A1CF6C0659"
NEW_SONG = 0x5BA740
NEW_SONG_BYTES = 67
NEW_SONG_SHA256 = "E85983F5523E73C17A8D3404F98BC0EA8F0A96DA7FF41FB69A254078A1FE662F"
NEW_TRACK = NEW_SONG + 12
TRACK = bytes.fromhex(
    "BC 00 BB 4B BD 1F BE 7F BF 7F C2 10 C4 20 C5 00 "
    "EC 3C 7F 9D D4 38 7F 85 D4 37 7F 85 D4 36 7F 85 "
    "D4 35 7F 85 D4 34 7F 85 D4 33 7F 85 D4 32 7F 85 "
    "D4 31 7F 85 C4 00 B1"
)
TRACK_SHA256 = "BC7F825311EE760F7D91C65F0EE7047E16F67D6BC2B76C5BE91E15983511B35A"
VOICEGROUP = 0x0837E8E0
REUSED_VOICE = 0x1F
REUSED_VOICE_BYTES = bytes.fromhex("04 3C 00 00 00 00 00 00 00 02 0A 01")
REUSED_VOICE_SHA256 = "8010A2A5E255DC761E08F135F293FDCB5ADCFDCC6E0FCF9BB1A9709DC0154110"

D2_ENTRY_OFFSET = 0x3F04EC
D2_ENTRY = bytes.fromhex("54 00 02 00 84 89")
D2_ENTRY_SHA256 = "5EA90B816BE59A873B44FC1854C7350E9D49F7ABA35D876C2B5CA66424944509"
D2_PAYLOAD_OFFSET = 0x3F8984
D2_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A1 09 A2 01 C1 00 A3 20 "
    "20 28 18 05 17 05 16 05 15 05 14 05 13 05 12 05 11 05 FF FF"
)
D2_PAYLOAD_SHA256 = "740A62271CDCF1636D420486F526461D81DD4271EF705D3DAEC09D2871928641"

WSC10_B5_PAYLOAD_OFFSET = 0x2D849C
WSC10_B5_PAYLOAD = bytes.fromhex("08 00 0F 01 A2 01 C2 18 00 02 1F 01 00 08 FF FF")
WSC10_B5_PAYLOAD_SHA256 = "97BD88AB91C648C8A5E58D7DB46C4E70C25EC0D8E63C0DD92EDD4FBB53625FF7"
GBA_56_TABLE_OFFSET = 0x37FED0
GBA_56_TABLE_ENTRY = bytes.fromhex("10 77 38 08 04 00 04 00")
GBA_56_TABLE_SHA256 = "C1CC7BCC206F80B91289DF00BE53DBB6CD9885F34CF03CBD4214B68BB31D3C1C"
GBA_56_TRACK_OFFSET = 0x3876FC
GBA_56_TRACK_PREFIX = bytes.fromhex("BC 00 BB 4B BD 1F BE 78 BF 40 D4 3C")
GBA_56_TRACK_PREFIX_SHA256 = "50663547EA23EF49EA58E60561653697E4911AE3C3197268D6E8CE87F6731EC8"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require_hash(data: bytes, expected: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected:
        raise SystemExit(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")


def require_exact(data: bytes, expected: bytes, expected_sha: str, label: str) -> None:
    require_hash(data, expected_sha, label)
    if data != expected:
        raise SystemExit(f"{label} bytes changed")


def aligned_word_refs(data: bytes, value: int) -> list[int]:
    encoded = struct.pack("<I", value)
    return [
        offset
        for offset in range(0, len(data) - 3, 4)
        if data[offset:offset + 4] == encoded
    ]


def wsc_note_to_midi(note: int) -> int:
    semitone = note & 0x0F
    if semitone > 0x0B:
        raise SystemExit(f"invalid packed WSC note 0x{note:02X}")
    return 36 + (note >> 4) * 12 + semitone


def verify_wsc_d2(payload: bytes) -> dict[str, object]:
    require_exact(payload, D2_PAYLOAD, D2_PAYLOAD_SHA256, "WSC D2 payload")
    if payload[:12] != bytes.fromhex("00 00 0F 01 A1 09 A2 01 C1 00 A3 20"):
        raise SystemExit("D2 setup sequence changed")
    notes = []
    for cursor in range(12, len(payload) - 2, 2):
        packed_note, ticks = payload[cursor:cursor + 2]
        notes.append((packed_note, wsc_note_to_midi(packed_note), ticks))
    expected = [
        (0x20, 60, 40), (0x18, 56, 5), (0x17, 55, 5),
        (0x16, 54, 5), (0x15, 53, 5), (0x14, 52, 5),
        (0x13, 51, 5), (0x12, 50, 5), (0x11, 49, 5),
    ]
    if notes != expected or payload[-2:] != bytes((0xFF, 0xFF)):
        raise SystemExit(f"D2 note schedule or terminator changed: {notes}")
    return {
        "setup": {"A1": 9, "A2": 1, "C1": 0, "A3": 32},
        "stereo_volume": 0x0F,
        "left_volume": 0,
        "right_volume": 15,
        "notes": [
            {"packed_note": packed, "midi_note": midi, "ticks": ticks}
            for packed, midi, ticks in notes
        ],
        "total_ticks": sum(ticks for _, _, ticks in notes),
    }


def verify_track(track: bytes) -> dict[str, object]:
    require_exact(track, TRACK, TRACK_SHA256, "D2 M4A track")
    prefix = bytes.fromhex("BC 00 BB 4B BD 1F BE 7F BF 7F C2 10 C4 20 C5 00")
    if track[:len(prefix)] != prefix:
        raise SystemExit("D2 M4A setup changed")
    cursor = len(prefix)
    rows = []
    expected = [(0xEC, 60, 0x9D, 40)] + [
        (0xD4, note, 0x85, 5) for note in range(56, 48, -1)
    ]
    for note_opcode, midi_note, wait_opcode, ticks in expected:
        actual = tuple(track[cursor:cursor + 4])
        if actual != (note_opcode, midi_note, 0x7F, wait_opcode):
            raise SystemExit(f"D2 M4A event changed at +0x{cursor:X}: {actual}")
        rows.append({"midi_note": midi_note, "ticks": ticks})
        cursor += 4
    if track[cursor:] != bytes((0xC4, 0, 0xB1)):
        raise SystemExit("D2 M4A MOD shutdown/FINE changed")
    return {
        "key_shift": 0,
        "tempo": 75,
        "voice": REUSED_VOICE,
        "volume": 127,
        "pan": 127,
        "lfo_speed": 16,
        "mod_depth": 32,
        "mod_type": "pitch",
        "notes": rows,
        "total_ticks": sum(row["ticks"] for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=pathlib.Path)
    parser.add_argument("after", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc10", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    before = args.before.read_bytes()
    after = args.after.read_bytes()
    gba = args.gba.read_bytes()
    wsc10 = args.wsc10.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(before, BEFORE_SHA256, "v42 candidate")
    require_hash(after, AFTER_SHA256, "v43 D2 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")
    if len(before) != 0x800000 or len(after) != len(before):
        raise SystemExit("candidate size changed")

    require_hash(before[SONG_TABLE:SONG_TABLE + OLD_TABLE_BYTES], OLD_TABLE_SHA256, "v42 table IDs 00..5B")
    if after[SONG_TABLE:SONG_TABLE + OLD_TABLE_BYTES] != before[SONG_TABLE:SONG_TABLE + OLD_TABLE_BYTES]:
        raise SystemExit("existing song IDs 00..5B changed")
    require_exact(after[NEW_ENTRY:NEW_ENTRY + 8], NEW_ENTRY_BYTES, NEW_ENTRY_SHA256, "new ID 5C entry")
    if before[NEW_ENTRY:NEW_ENTRY + 8] != bytes([0xFF]) * 8:
        raise SystemExit("new ID 5C entry was not blank before integration")

    require_exact(wsc15[D2_ENTRY_OFFSET:D2_ENTRY_OFFSET + 6], D2_ENTRY, D2_ENTRY_SHA256, "WSC D2 entry")
    wsc_semantics = verify_wsc_d2(wsc15[D2_PAYLOAD_OFFSET:D2_PAYLOAD_OFFSET + len(D2_PAYLOAD)])

    require_exact(
        wsc10[WSC10_B5_PAYLOAD_OFFSET:WSC10_B5_PAYLOAD_OFFSET + len(WSC10_B5_PAYLOAD)],
        WSC10_B5_PAYLOAD,
        WSC10_B5_PAYLOAD_SHA256,
        "WSC B5 A2=01 oracle",
    )
    require_exact(gba[GBA_56_TABLE_OFFSET:GBA_56_TABLE_OFFSET + 8], GBA_56_TABLE_ENTRY, GBA_56_TABLE_SHA256, "GBA 56 table oracle")
    require_exact(gba[GBA_56_TRACK_OFFSET:GBA_56_TRACK_OFFSET + 12], GBA_56_TRACK_PREFIX, GBA_56_TRACK_PREFIX_SHA256, "GBA 56 voice oracle")
    voice_offset = (VOICEGROUP - GBA_BASE) + REUSED_VOICE * 12
    require_exact(gba[voice_offset:voice_offset + 12], REUSED_VOICE_BYTES, REUSED_VOICE_SHA256, "GBA voice 1F")

    song = after[NEW_SONG:NEW_SONG + NEW_SONG_BYTES]
    track = song[12:]
    require_hash(song, NEW_SONG_SHA256, "new D2 song")
    m4a_semantics = verify_track(track)
    header = struct.unpack_from("<BBBBII", song, 0)
    if header != (1, 0, 0x28, 0x80, VOICEGROUP, GBA_BASE + NEW_TRACK):
        raise SystemExit(f"D2 song header changed: {header}")
    if wsc_semantics["total_ticks"] != m4a_semantics["total_ticks"]:
        raise SystemExit("WSC-to-M4A total timing changed")
    if [row["midi_note"] for row in wsc_semantics["notes"]] != [row["midi_note"] for row in m4a_semantics["notes"]]:
        raise SystemExit("WSC-to-M4A pitch sequence changed")
    if [row["ticks"] for row in wsc_semantics["notes"]] != [row["ticks"] for row in m4a_semantics["notes"]]:
        raise SystemExit("WSC-to-M4A note timing changed")

    allowed = set(range(NEW_ENTRY, NEW_ENTRY + 8)) | set(range(NEW_SONG, NEW_SONG + NEW_SONG_BYTES))
    changed = {
        offset
        for offset, (left, right) in enumerate(zip(before, after, strict=True))
        if left != right
    }
    if len(changed) != 75 or changed != allowed:
        raise SystemExit(f"D2 diff containment changed: {len(changed)} bytes")
    if aligned_word_refs(after, GBA_BASE + NEW_SONG) != [NEW_ENTRY]:
        raise SystemExit("D2 song pointer population changed")
    if aligned_word_refs(after, GBA_BASE + NEW_TRACK) != [NEW_SONG + 8]:
        raise SystemExit("D2 track pointer population changed")

    result = {
        "schema": 1,
        "kind": "independent-shoot-d2-native-sound-verification",
        "claim_scope": (
            "static exact-diff, preserved IDs 00..5B, source D2 semantics, commercial "
            "A2=01/voice-1F oracle, and native pitch/timing/stereo/controller checks; "
            "upper-state requests, conditional channel-3 sweep parity, runtime, and "
            "audibility excluded"
        ),
        "before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256,
        "changed_bytes": len(changed),
        "old_table_sha256": OLD_TABLE_SHA256,
        "new_sound_id": NEW_SOUND_ID,
        "entry_sha256": NEW_ENTRY_SHA256,
        "song_sha256": NEW_SONG_SHA256,
        "track_sha256": TRACK_SHA256,
        "wsc_d2": wsc_semantics,
        "m4a_reconstruction": m4a_semantics,
        "commercial_timbre_oracle": {
            "wsc_sound_id": 0xB5,
            "wsc_A2_wave": 1,
            "gba_sound_id": 0x56,
            "gba_voice": REUSED_VOICE,
            "voice_sha256": REUSED_VOICE_SHA256,
        },
        "external_requests_connected": False,
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
