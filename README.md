# Digimon Battle Spirit Ver. 1.5 GBA port survey

This workspace records a clean-room feasibility survey for extending the USA
GBA release of *Digimon: Battle Spirit* with content from the WonderSwan Color
release *Digimon Tamers: Battle Spirit Ver. 1.5*.

Original and patched ROM images are intentionally kept outside this directory.
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

The dated implementation snapshot and remaining release gates are tracked in
[`STATUS.md`](STATUS.md). Reverse-engineering evidence is kept locally because
it contains source-derived captures and dumps; the committed tools regenerate
that evidence from user-supplied, hash-identified inputs.

The current internal composite is built in three checked layers: stage v30,
progression/unlocks v5, then the Zeed boss layer (composite v31). Each builder refuses an
unexpected input SHA-256, so a later stage change must deliberately advance
the two downstream hashes before a new composite can be produced.
