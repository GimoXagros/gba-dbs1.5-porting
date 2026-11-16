# Evolution BGM pause/resume identity repair

Static consumer inspection exposed a concrete defect in unpublished C508:
the retained play adapter at `0837B454` caches only IDs passing the original
`CMP r8,#1E / BPL` predicate. Retail evolution ID `1C` updated the current-BGM
cache at `03004E98`; appended IDs `6C..6F` left the previous stage ID there.

Pause caller `08375364` invokes `0837B48C`; resume caller `0837579C` invokes
`0837B4A8`. Both load that cache. Their actual Thumb consumers at `0837C348`
and `0837C37C` select the song's player and require the active player's header
to equal the requested song's header (`37C364` and `37C398`). A stale stage
header differs from the active evolution header, so both operations skip
their stop/resume service. Sharing player zero does not avoid the defect.

The isolated repair changes only two spans: four bytes at `37B458` and twenty
bytes at `D7DFC0..D7DFD4`. The old BPL now visits a five-instruction ARM tail
which admits precisely unsigned `6C <= ID < 70` into the existing cache-store
block. Every other ID retains the original path; zero still globally stops.
The repair declares 24 bytes and changes 23. It preserves all scores, samples,
tables, selector mappings, input behavior and stage-return code.

The tail is inside the existing audio reservation `D74000..D7E000`.
All 64 bytes from `D7DFC0` to its end were FF. The full 16MiB conservative
unaligned-pointer, ARM and Thumb inbound scan found zero encodings entering
the twenty-byte span, with no exemptions. The remaining 44 bytes stay FF.
The complete inverse restores exact C508; the image remains 16MiB.

| Item | SHA-256 |
|---|---|
| Input C508 | `C5089F81C13FA381495C169AA7BA0538CD3D7FE599564894608F99596F8DD346` |
| `tools/build_evolution_music_pause_cache.py` | `7488DE49EC398BF0C1AD7FBFB4AA04A2EBB133ECBE17DC6227A6BE3123F03810` |
| `build/evolution-music-pause-cache-20261110/component.gba` | `C3448F183F886AF5AFD8878DF0839FEE5856DA1812BB94FE060301BAAB5E7278` |
| `component.json` | `32A7942A7945B12EF191995B908DC8844C1935DA33340B0484700E4813203B8B` |
| `tools/verify_evolution_music_pause_cache_author.py` | `EDD02F5DBF4437A703731FBBF22ED3AEAF6AB89BA4544A66589D99E65E8EF54B` |
| `author-report.json` | `EE3336BE88013E0CB69E233453D5E731BF188B728B3A7E0D80B83969660F5C15` |

Builder CLI: `--before <C508.gba> --output <fresh.gba> --manifest <fresh.json>`.
It rejects existing outputs and aliases before writing. Author checking runs
3904 actual ARM play cases: all IDs `00..6F`, ten further boundary values,
sixteen initial NZCV patterns, before and after. Eight actual ARM pause/resume
routes pass the corrected IDs with preserved R0, SP and LR. Three semantic
mutations are rejected. All non-cache write effects remain identical.
NZCV are scratch and may differ; the retained Thumb play entry changes them.
CPSR control bits are preserved. Downstream M4A functions are explicit service
boundaries in the author interpreter; independent QA must verify the actual
Thumb header consumers. No emulator or production-main change was performed
by this author, and actual ordinary pause/resume remains a separate test.
