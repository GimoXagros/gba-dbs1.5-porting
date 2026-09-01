#!/usr/bin/env python3
"""Bound WSC Ver. 1.5 sound D2 and its commercial GBA timbre oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib


GBA_SHA256 = "996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED"
WSC10_SHA256 = "58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735"
WSC15_SHA256 = "C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7"
GBA_BASE = 0x08000000

D2_ENTRY_OFFSET = 0x3F04EC
D2_ENTRY = bytes.fromhex("54 00 02 00 84 89")
D2_ENTRY_SHA256 = "5EA90B816BE59A873B44FC1854C7350E9D49F7ABA35D876C2B5CA66424944509"
D2_PAYLOAD_OFFSET = 0x3F8984
D2_PAYLOAD = bytes.fromhex(
    "00 00 0F 01 A1 09 A2 01 C1 00 A3 20 "
    "20 28 18 05 17 05 16 05 15 05 14 05 13 05 12 05 11 05 FF FF"
)
D2_PAYLOAD_SHA256 = "740A62271CDCF1636D420486F526461D81DD4271EF705D3DAEC09D2871928641"

INTERPRETER_SIGNATURES = {
    "A0_volume": bytes.fromhex("3C A0 75 16 26 8A 07 43 88 44 08"),
    "A1_sweep": bytes.fromhex("3C A1 75 10 26 8A 07 43 88 44 0A"),
    "A2_wave": bytes.fromhex("3C A2 75 20 26 8A 07 43"),
    "A3_pitch_modulation": bytes.fromhex("3C A3 75 2B 26 8A 07 43"),
}

# WSC 1.0 B5 uses A2 01 and maps commercially to USA GBA sound 56.
# The first native 56 track selects voice 1F, making it the local timbre oracle.
WSC10_B5_ENTRY_OFFSET = 0x2D043E
WSC10_B5_ENTRY = bytes.fromhex("54 00 03 00 9C 84")
WSC10_B5_ENTRY_SHA256 = "57E14F4EED61E0BFC3750BB58375E487576AF8973F480A4EFA33EFF1CA89888B"
WSC10_B5_PAYLOAD_OFFSET = 0x2D849C
WSC10_B5_PAYLOAD = bytes.fromhex(
    "08 00 0F 01 A2 01 C2 18 00 02 1F 01 00 08 FF FF"
)
WSC10_B5_PAYLOAD_SHA256 = "97BD88AB91C648C8A5E58D7DB46C4E70C25EC0D8E63C0DD92EDD4FBB53625FF7"
GBA_56_TABLE_OFFSET = 0x37FED0
GBA_56_TABLE_ENTRY = bytes.fromhex("10 77 38 08 04 00 04 00")
GBA_56_TABLE_SHA256 = "C1CC7BCC206F80B91289DF00BE53DBB6CD9885F34CF03CBD4214B68BB31D3C1C"
GBA_56_SONG_OFFSET = 0x387710
GBA_56_SONG_HEADER = bytes.fromhex("01 00 28 80 E0 E8 37 08 FC 76 38 08")
GBA_56_SONG_HEADER_SHA256 = "693CD24EEE9B8D26A71D844026BD94AF444BC43D56C8EE03D75092CF44021813"
GBA_56_TRACK_OFFSET = 0x3876FC
GBA_56_TRACK_PREFIX = bytes.fromhex("BC 00 BB 4B BD 1F BE 78 BF 40 D4 3C")
GBA_56_TRACK_PREFIX_SHA256 = "50663547EA23EF49EA58E60561653697E4911AE3C3197268D6E8CE87F6731EC8"
VOICEGROUP = 0x0837E8E0
REUSED_VOICE = 0x1F
REUSED_VOICE_BYTES = bytes.fromhex("04 3C 00 00 00 00 00 00 00 02 0A 01")
REUSED_VOICE_SHA256 = "8010A2A5E255DC761E08F135F293FDCB5ADCFDCC6E0FCF9BB1A9709DC0154110"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def require(data: bytes, expected: bytes, expected_sha: str, label: str) -> None:
    actual_sha = sha256(data)
    if data != expected or actual_sha != expected_sha:
        raise SystemExit(f"{label} mismatch: SHA-256 {actual_sha}")


def require_source(data: bytes, expected_sha: str, label: str) -> None:
    actual = sha256(data)
    if actual != expected_sha:
        raise SystemExit(f"{label} SHA-256 mismatch: {actual}")


def unique_offset(data: bytes, pattern: bytes, label: str) -> int:
    hits = []
    cursor = 0
    while True:
        cursor = data.find(pattern, cursor)
        if cursor < 0:
            break
        hits.append(cursor)
        cursor += 1
    if len(hits) != 1:
        raise SystemExit(f"{label} is not unique: {[hex(hit) for hit in hits]}")
    return hits[0]


def wsc_note_to_midi(note: int) -> int:
    semitone = note & 0x0F
    if semitone > 0x0B:
        raise SystemExit(f"invalid packed WSC note 0x{note:02X}")
    return 36 + (note >> 4) * 12 + semitone


def parse_d2() -> dict[str, object]:
    if D2_PAYLOAD[:12] != bytes.fromhex("00 00 0F 01 A1 09 A2 01 C1 00 A3 20"):
        raise SystemExit("D2 setup commands changed")
    notes = []
    for cursor in range(12, len(D2_PAYLOAD) - 2, 2):
        packed_note, ticks = D2_PAYLOAD[cursor:cursor + 2]
        notes.append({
            "packed_note": packed_note,
            "midi_note": wsc_note_to_midi(packed_note),
            "ticks": ticks,
        })
    expected = [
        (0x20, 40), (0x18, 5), (0x17, 5), (0x16, 5), (0x15, 5),
        (0x14, 5), (0x13, 5), (0x12, 5), (0x11, 5),
    ]
    if [(row["packed_note"], row["ticks"]) for row in notes] != expected:
        raise SystemExit(f"D2 note schedule changed: {notes}")
    if D2_PAYLOAD[-2:] != bytes((0xFF, 0xFF)):
        raise SystemExit("D2 terminator changed")
    return {
        "channel_header": {
            "flags": 0,
            "initial_wave": 0,
            "stereo_volume": 0x0F,
            "initial_channel_control": 1,
        },
        "setup": {
            "A1_hardware_sweep": 0x09,
            "A2_wave_index": 1,
            "C1_control_slot": 0,
            "A3_pitch_modulation": 0x20,
        },
        "notes": notes,
        "total_ticks": sum(row["ticks"] for row in notes),
        "stereo": {
            "left_nibble": 0,
            "right_nibble": 15,
            "native_pan_target": 127,
        },
    }


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
    require_source(gba, GBA_SHA256, "USA GBA source")
    require_source(wsc10, WSC10_SHA256, "WSC 1.0 source")
    require_source(wsc15, WSC15_SHA256, "WSC Ver. 1.5 source")

    require(wsc15[D2_ENTRY_OFFSET:D2_ENTRY_OFFSET + 6], D2_ENTRY, D2_ENTRY_SHA256, "D2 entry")
    require(
        wsc15[D2_PAYLOAD_OFFSET:D2_PAYLOAD_OFFSET + len(D2_PAYLOAD)],
        D2_PAYLOAD,
        D2_PAYLOAD_SHA256,
        "D2 payload",
    )
    d2 = parse_d2()

    interpreter_offsets = {"wsc_10": {}, "wsc_15": {}}
    for label, signature in INTERPRETER_SIGNATURES.items():
        interpreter_offsets["wsc_10"][label] = unique_offset(wsc10, signature, f"WSC 1.0 {label}")
        interpreter_offsets["wsc_15"][label] = unique_offset(wsc15, signature, f"WSC 1.5 {label}")

    require(
        wsc10[WSC10_B5_ENTRY_OFFSET:WSC10_B5_ENTRY_OFFSET + 6],
        WSC10_B5_ENTRY,
        WSC10_B5_ENTRY_SHA256,
        "WSC 1.0 B5 entry",
    )
    require(
        wsc10[WSC10_B5_PAYLOAD_OFFSET:WSC10_B5_PAYLOAD_OFFSET + len(WSC10_B5_PAYLOAD)],
        WSC10_B5_PAYLOAD,
        WSC10_B5_PAYLOAD_SHA256,
        "WSC 1.0 B5 payload",
    )
    require(gba[GBA_56_TABLE_OFFSET:GBA_56_TABLE_OFFSET + 8], GBA_56_TABLE_ENTRY, GBA_56_TABLE_SHA256, "GBA 56 table entry")
    require(gba[GBA_56_SONG_OFFSET:GBA_56_SONG_OFFSET + 12], GBA_56_SONG_HEADER, GBA_56_SONG_HEADER_SHA256, "GBA 56 song header")
    require(gba[GBA_56_TRACK_OFFSET:GBA_56_TRACK_OFFSET + 12], GBA_56_TRACK_PREFIX, GBA_56_TRACK_PREFIX_SHA256, "GBA 56 track prefix")
    voice_offset = (VOICEGROUP - GBA_BASE) + REUSED_VOICE * 12
    require(gba[voice_offset:voice_offset + 12], REUSED_VOICE_BYTES, REUSED_VOICE_SHA256, "GBA voice 1F")

    result = {
        "schema": 1,
        "kind": "digimon-shoot-d2-sound-boundary",
        "sources": {
            "gba_sha256": GBA_SHA256,
            "wsc_10_sha256": WSC10_SHA256,
            "wsc_15_sha256": WSC15_SHA256,
        },
        "interpreter_offsets": interpreter_offsets,
        "interpreter_semantics": {
            "A0": "stereo channel volume byte stored at state+8",
            "A1": "channel-3 hardware sweep control stored at state+0x0A and emitted through ports 0x8C/0x8D",
            "A2": "wave index, shifted by four to select a 16-byte/32-sample waveform",
            "A3": "per-tick pitch-modulation selector and update interval",
        },
        "wsc_15_d2": {
            "sound_id": 0xD2,
            "entry_offset": D2_ENTRY_OFFSET,
            "entry_sha256": D2_ENTRY_SHA256,
            "payload_offset": D2_PAYLOAD_OFFSET,
            "payload_bytes": len(D2_PAYLOAD),
            "payload_sha256": D2_PAYLOAD_SHA256,
            **d2,
        },
        "commercial_timbre_oracle": {
            "wsc_10_sound_id": 0xB5,
            "wsc_10_payload_sha256": WSC10_B5_PAYLOAD_SHA256,
            "shared_A2_wave_index": 1,
            "commercial_gba_sound_id": 0x56,
            "commercial_gba_voice": REUSED_VOICE,
            "commercial_gba_voice_sha256": REUSED_VOICE_SHA256,
        },
        "native_plan": {
            "assigned_gba_sound_id": 0x5C,
            "request_type": 2,
            "voice": REUSED_VOICE,
            "midi_notes": [row["midi_note"] for row in d2["notes"]],
            "note_ticks": [row["ticks"] for row in d2["notes"]],
            "total_ticks": d2["total_ticks"],
            "pan": 127,
            "pitch_modulation": "represent A3 through native M4A MOD; final audible parity deferred",
            "hardware_sweep": "A1 is conditional on WSC hardware channel 3; final native response remains an audible-QA boundary",
        },
        "claim_scope": (
            "static D2 command decode, exact packed-note/timing/stereo schedule, unique "
            "source-interpreter handlers, and commercial A2=01 to GBA voice 0x1F timbre "
            "oracle; no emulator, save, runtime playback, or audible-equivalence claim"
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
