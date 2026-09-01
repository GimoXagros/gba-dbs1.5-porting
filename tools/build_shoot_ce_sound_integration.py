#!/usr/bin/env python3
"""Install a bounded GBA-native reconstruction of WSC Ver. 1.5 sound CE."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


INPUT_SHA256 = "35B2F717A96573B0823E43433A547B5398CC13129DAEECED6646153FC69F5492"
GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

OLD_SONG_TABLE = 0x37FC20
OLD_SONG_COUNT = 0x5B
NEW_SOUND_ID = 0x5B
NEW_SONG_TABLE = 0x5BA400
NEW_SONG = 0x5BA700
OWNERSHIP_START = 0x5BA400
OWNERSHIP_END = 0x5BA800
VOICEGROUP = 0x0837E8E0
REUSED_VOICE = 0x14

TABLE_LITERAL_SITES = (0x37C2A4, 0x37C2D8, 0x37C324, 0x37C378, 0x37C3AC)
OLD_TABLE_SHA256 = "8AFEDFFA4774585E60486D780DD2308CD1D07F913B683313656CB2E3D8159AF8"
LOOKUP_LOADERS_SHA256 = "5FF8CE7F82748AEBB232EE58FF4ABF48CE7DFF907E4168D85BEF71F7E64F8078"
REUSED_VOICE_SHA256 = "1E65392E06FA504CD467F2C2471D540ED25CBA145F7EAE045379C5D3D11D2B94"
WSC15_CE_ENTRY_OFFSET = 0x3F04D4
WSC15_CE_ENTRY_SHA256 = "5D3262C7097F3AFD35B942F2CA418EFB33786E408B05551847E53690EA8A505F"
WSC15_CE_PAYLOAD_OFFSET = 0x3F88FC
WSC15_CE_PAYLOAD_END = 0x3F891A
WSC15_CE_PAYLOAD_SHA256 = "79BB15C2643DA24DAC1A16D7B760977257A7ABCA0B3DAE82383F85EFEF7C80B6"


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
    octave = note >> 4
    semitone = note & 0x0F
    if semitone > 0x0B:
        raise SystemExit(f"invalid packed WSC note 0x{note:02X}")
    return 36 + octave * 12 + semitone


def wsc_volume_to_m4a(volume: int) -> int:
    if not 0 <= volume <= 0x0F:
        raise SystemExit(f"invalid WSC volume {volume}")
    return (volume * 127 + 7) // 15


def build_track() -> bytes:
    # CE is one packed note 0x10 for 0x14 ticks followed by four volume steps
    # separated by A7 waits of 0x0A ticks.  N72 keeps the note gated across the
    # complete 60-tick schedule.  Commercial square voice 0x14 is reused as a
    # bounded channel-2 timbre analogue; audible parity is deliberately left
    # for final non-displaying QA.
    note = wsc_note_to_midi(0x10)
    volumes = [wsc_volume_to_m4a(value) for value in (0x09, 0x06, 0x03, 0x01)]
    track = bytes([
        0xBC, 0x00,       # KEYSH 0
        0xBB, 0x4B,       # TEMPO 75, matching the commercial SFX population
        0xBD, REUSED_VOICE,
        0xBE, 0x7F,       # initial WSC volume 0x0F
        0xBF, 0x40,       # centered pan
        0xF7, note, 0x7F, # N72, packed note 0x10, velocity 127
        0x94,             # W20
        0xBE, volumes[0], 0x8A,
        0xBE, volumes[1], 0x8A,
        0xBE, volumes[2], 0x8A,
        0xBE, volumes[3], 0x8A,
        0xB1,             # FINE
    ])
    return track


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("gba", type=pathlib.Path)
    parser.add_argument("wsc15", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--manifest", type=pathlib.Path)
    args = parser.parse_args()

    source = args.input.read_bytes()
    gba = args.gba.read_bytes()
    wsc15 = args.wsc15.read_bytes()
    require_hash(source, INPUT_SHA256, "v39 candidate")
    require_hash(gba, GBA_SHA256, "USA GBA source")
    require_hash(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    old_table = gba[OLD_SONG_TABLE:OLD_SONG_TABLE + OLD_SONG_COUNT * 8]
    require_hash(old_table, OLD_TABLE_SHA256, "commercial GBA song table")
    require_hash(
        gba[0x37C27C:0x37C3B0], LOOKUP_LOADERS_SHA256, "commercial song lookup loaders"
    )
    voice_offset = (VOICEGROUP - GBA_BASE) + REUSED_VOICE * 12
    require_hash(
        gba[voice_offset:voice_offset + 12], REUSED_VOICE_SHA256, "reused square voice"
    )
    require_hash(
        wsc15[WSC15_CE_ENTRY_OFFSET:WSC15_CE_ENTRY_OFFSET + 6],
        WSC15_CE_ENTRY_SHA256,
        "WSC Ver. 1.5 CE entry",
    )
    ce_payload = wsc15[WSC15_CE_PAYLOAD_OFFSET:WSC15_CE_PAYLOAD_END]
    require_hash(ce_payload, WSC15_CE_PAYLOAD_SHA256, "WSC Ver. 1.5 CE payload")
    if ce_payload != bytes.fromhex(
        "00 00 0F 01 A2 02 C1 00 A1 72 10 14 A0 09 A7 0A "
        "A0 06 A7 0A A0 03 A7 0A A0 01 A7 0A FF FF"
    ):
        raise SystemExit("WSC Ver. 1.5 CE command semantics changed")

    if source[OWNERSHIP_START:OWNERSHIP_END] != bytes([0xFF]) * (
        OWNERSHIP_END - OWNERSHIP_START
    ):
        raise SystemExit("CE sound ownership window is not blank")
    refs_before = aligned_pointer_refs(source, OWNERSHIP_START, OWNERSHIP_END)
    if refs_before:
        raise SystemExit(f"pre-existing pointer reaches CE sound window: {refs_before}")
    for offset in TABLE_LITERAL_SITES:
        if struct.unpack_from("<I", source, offset)[0] != GBA_BASE + OLD_SONG_TABLE:
            raise SystemExit(f"song-table literal changed at 0x{offset:X}")

    track = build_track()
    song = (
        bytes((1, 0, 0x28, 0x80))
        + struct.pack("<I", VOICEGROUP)
        + struct.pack("<I", GBA_BASE + NEW_SONG + 12)
        + track
    )
    new_entry = struct.pack("<IHH", GBA_BASE + NEW_SONG, 4, 4)
    new_table = old_table + new_entry
    if len(new_table) != (OLD_SONG_COUNT + 1) * 8:
        raise SystemExit("expanded song-table length changed")

    placements = (
        (NEW_SONG_TABLE, new_table, "relocated_song_table_00_5B"),
        (NEW_SONG, song, "wsc15_ce_gba_song_5B"),
    )
    patched = bytearray(source)
    allowed = set()
    expected_writes = []
    for offset in TABLE_LITERAL_SITES:
        before = bytes(patched[offset:offset + 4])
        after = struct.pack("<I", GBA_BASE + NEW_SONG_TABLE)
        patched[offset:offset + 4] = after
        allowed.update(range(offset, offset + 4))
        expected_writes.append({
            "label": "song_table_literal",
            "target": offset,
            "bytes": 4,
            "before_sha256": sha256(before),
            "after_sha256": sha256(after),
        })
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
        raise SystemExit("CE sound integration contains an unexplained diff")

    output = bytes(patched)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    result = {
        "schema": 1,
        "kind": "internal-shoot-ce-native-sound-build",
        "claim_scope": (
            "bounded GBA M4A reconstruction of WSC Ver. 1.5 CE command timing, "
            "packed pitch, and four-step volume decay using a commercial square "
            "voice analogue; audible/timbre parity and runtime playback unverified"
        ),
        "input_sha256": INPUT_SHA256,
        "output_sha256": sha256(output),
        "output_bytes": len(output),
        "ownership": {
            "start": OWNERSHIP_START,
            "end": OWNERSHIP_END,
            "preexisting_aligned_pointer_refs": refs_before,
        },
        "expected_writes": expected_writes,
        "wsc_source": {
            "sound_id": 0xCE,
            "entry_offset": WSC15_CE_ENTRY_OFFSET,
            "entry_sha256": WSC15_CE_ENTRY_SHA256,
            "payload_offset": WSC15_CE_PAYLOAD_OFFSET,
            "payload_bytes": len(ce_payload),
            "payload_sha256": WSC15_CE_PAYLOAD_SHA256,
        },
        "gba_reconstruction": {
            "sound_id": NEW_SOUND_ID,
            "song_table": GBA_BASE + NEW_SONG_TABLE,
            "song": GBA_BASE + NEW_SONG,
            "track": GBA_BASE + NEW_SONG + 12,
            "voicegroup": VOICEGROUP,
            "reused_voice": REUSED_VOICE,
            "packed_wsc_note": 0x10,
            "midi_note": wsc_note_to_midi(0x10),
            "wsc_note_ticks": 0x14,
            "wsc_decay_volumes": [0x09, 0x06, 0x03, 0x01],
            "m4a_decay_volumes": [wsc_volume_to_m4a(v) for v in (9, 6, 3, 1)],
            "wsc_decay_wait_ticks": [0x0A] * 4,
            "track_bytes": len(track),
            "track_sha256": sha256(track),
            "song_bytes": len(song),
            "song_sha256": sha256(song),
        },
        "external_request_connected": False,
        "runtime_audibility_verified": False,
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"[shoot-ce-sound] output SHA-256 {result['output_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
