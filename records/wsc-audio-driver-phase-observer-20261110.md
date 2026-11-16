# Read-only source audio driver diagnostic

New observer `tools/bizhawk_observe_wsc_audio_driver_phase.lua` is frozen at `D657CE693873BDC2622453EA5EDD188E71777873CD288C148ED5393A9B1CEA16`. This supersedes interim6A811, which lacked the per-frame driver flags.

Source and observer check report: `build/wsc-audio-driver-phase-observer-qa-20261110/report.json`, SHA256 `812AF1EDE68D71D2AA898655770FDE00466C5B8C3C2B93142A4F994DE9E6D9B9`.

Original C415 bytes at75418B and7542F6 are both FE06EE06, INC byte[06EE]. The former belongs to the normal driver, the latter the alternate driver. Each observer iteration adds read-only phase06EE, flagsF91E and168 raw bytes0642..06E9 to a separate file. Existing09D3 request observer lines and4400 advances are preserved; line endings are normalized, not byte-identical. No hooks, writes, input or state manipulation are introduced.

Four42-byte states begin0642/066C/0696/06C0. Source-confirmed fields: cursor+0u16 (FFFF ended), channel/modulation+2u8, payload+3u16, speed+6u8, fraction+7u8, volume+8u8, countdown+9u8, envelope mode/period/age+D/E/F, pitch+10u16, stereo+12u8 and modulation delay+13/+14u8.

Phase differences are modulo256 and alone cannot exclude256 unseen increments. Flags permit alternate-driver qualification. Actual WAV and request-log identity against the previous source38 capture remains a subsequent runtime gate; this authoring check does not establish noninterference or the cause of timing drift.
