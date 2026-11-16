# Bounded alignment follow-up

The weak nominal energy-envelope correlation should not be attributed directly to envelope mismatch. A bounded alignment search improves correlation to0.693586 at effectively zero initial offset and an additional+0.35% native rate adjustment beyond the independently predicted+0.242655% tempo difference.

Report `build/bgm-render-pair38-capture-qa-20261110/alignment-report.json` SHA256 `FF7E7C16F5A3CE8C6917E0ACE19040B0474090EA2CE5A05CE8C3BB8EC2D1D2FF`. It binds the same immutable actual WAV hashes and examines1071 candidates: offsets−0.25..+0.25seconds in0.01 steps; additional relative rates−0.5..+0.5% in0.05% steps. The overlap is0.3..37.5seconds after nominal initialization, using fixed50ms physical stereo RMS windows on both cores. Its nominal baseline0.078 differs from the first report0.151 because that report also scaled the native window width with tempo.

At nominal rate, independent segment searches give best native sampling offsets−25ms for0.3..12seconds, −60ms for12..25seconds, and−105ms for25..37.5seconds. This supports an accumulating timing difference over a constant latency explanation. It is consistent with a source duration beyond the simple schedule, but neither an instruction-level off-by-one nor its precise cause is established.

The optimized correlation is descriptive and subject to alignment fitting. No exact envelope, timing, audible or timbre parity follows. Native clipping by the boot stop and the previous capture provenance findings remain unchanged. No emulator was run or capture altered.
