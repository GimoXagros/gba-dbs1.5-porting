# Digimon Battle Spirit Ver. 1.5 GBA port survey

This workspace records a clean-room feasibility survey for extending the USA
GBA release of *Digimon: Battle Spirit* with content from the WonderSwan Color
release *Digimon Tamers: Battle Spirit Ver. 1.5*.

Original and patched ROM images are intentionally kept out of version control.
Tools accept ROM paths at runtime and identify inputs by strong hashes.

The user-supplied WonderSwan save is registered separately in
[`records/final-qa.md`](records/final-qa.md). It is intentionally not loaded or
inspected until the complete content port has passed static integration checks.

## Current scope

- Fix the exact source revisions.
- Identify code, compression, graphics, audio, and data boundaries.
- Decide which 1.5 features can reuse the GBA engine and which require new code.
- Reproduce the added fighters/evolutions, arenas and their mechanics, the
  alternate final-boss path, Digimon Shoot, progression/tag state, and opening
  changes in one reproducible GBA patch build.

Internal integration builds are not distribution artifacts. Emulator and
supplied-save validation are intentionally reserved for the fully integrated
release candidate, and only the resulting patch—not a ROM image—will be placed
in `outputs/`.

The recovery audit, actual-runtime matrix, and corrected progress baseline are
tracked in [`PORT_AUDIT.md`](PORT_AUDIT.md). The earlier implementation notes
and remaining release gates are retained in [`STATUS.md`](STATUS.md).
Implementation resumed on 2026-10-13. v51 adds resident Shoot rule, palette
and initializer components; the complete normal-play entry remains unconnected.
Start with [`RESUME.md`](RESUME.md) for the current implementation boundary.
A model-specific continuation package and copy-ready prompt are in
[`ASTRA_HANDOFF.md`](ASTRA_HANDOFF.md). The recommended setting for this
reverse-engineering milestone is GPT-6 Astra with `max` reasoning effort.
Reverse-engineering evidence is kept locally because
it contains source-derived captures and dumps; the committed tools regenerate
that evidence from user-supplied, hash-identified inputs.

The current static internal composite is **v51**, built from the three
hash-identified originals through twenty-two checked ROM layers. Its exact
image and manifest hashes, historical layers, and remaining gates are recorded
in [`PORT_AUDIT.md`](PORT_AUDIT.md#reproducibility-audit).
Each builder refuses an unexpected input SHA-256, so a layer change must
deliberately advance the downstream hashes before a new composite can be
produced. Exact v32, SHA-256
`1FB2449A5994FCB3E5343074BE96F4A3B6614CBA0A7ECDDC462F919191022291`,
remains the last runtime-evidenced candidate and passes the non-displaying
`BOOT -> TITLE -> MAIN MENU -> CHARACTER SELECT` runtime milestones; roster
correctness remains unverified. Retail character ID 0 also reaches the first
baseline battle and consumes one Right input through the retail player path,
but broader battle behavior remains unverified.

The single clean-build entry point is:

```powershell
py -3 tools/build_current_candidate.py "<USA-GBA-original>" "<WSC-1.0-original>" "<WSC-1.5-original>" "<new-output-directory>"
```

It regenerates the commercial WSC-to-GBA comparison corpora, every currently
consumed character/evolution/VS/stage/boss/opening asset, and all twenty-two ROM
layers. It fails on any unexpected source, intermediate, asset, or layer
SHA-256 and refuses populated output directories. Two independent empty-directory
runs reproduced exact v51, including all 131 output files, byte-for-byte. This is a
reproducibility result for the current incomplete candidate, not a complete
Ver. 1.5 port or a distributable ROM.
