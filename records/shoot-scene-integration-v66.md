# v66 Shoot resident scene integration — 2026-11-05

This checkpoint installs the source-ordered resident scene and its real initializer
call. It does not enable the external scene route or controller boundary and is
not a complete port. Resume HEAD was98e00e9111b63dfdac866b354ee1e00c732696dd.

## Reproducible build and independent final review

| Evidence | SHA-256 |
| --- | --- |
| v66 ROM | 428B1CF6B459E077972BD621A2C4C689DFE9E36FB1372BB2EB82DA5B3075F281 |
| Complete259-file A/B comparison | A7D7DAC45B1B4636A40954C245D776FD3D6F0C2F3FBFD37606C2C12E5DDAA9A5 |
| Build manifest | CF8EEAEBEB8EB92E26DBC391F0D9247B41FA6CB81D8E6C80C073659268FF9A04 |
| Scene independent verifier report | AC1D7CCFBC2753D1439B2AFCA364240F7AFC0D26C1E030860898B82ED99DD15D |
| Independent final main-artifact audit | FF3B019C0BB9B67B27B87B2A916A32EEDAB155F07FB4F7BE8E95F94B9D349F0D |
| Main builder source | B859F32E5056D75D7965D7DB52AB71A244D63EAB20BD5BC57AFB18C1C2AF72D2 |

Both `build/repro-v66-20261105-a` and `-b` were rebuilt from the exact three
original ROMs and licensed font. Every relative file path and hash matches.
The root comparison is `build/repro-v66-20261105-comparison.json`; the separate
specialist recomputed it and reran the independent scene checker on the actual
main ROM in `build/repro-v66-final-audit-20261105/audit.json`.

There are22 placements/3032 declared bytes/2948 changed bytes and648 ARM
instructions. Fifteen semantic and six ownership mutation controls pass. The
initializer is exactly140 bytes at08629800. Phase12C6 moved to085C9B00 because
four existing encoded references target gaps in the old reserved scene area;
all four targets and bytes are retained. Reversing all22 intervals reproduces
v65 byte for byte. The source snapshot-before-black order is preserved.
See [component proof](shoot-scene-resident-v66.md).

## Hidden runtime and the journal completion repair

The root ran a changed ordinary controller trajectory (`approach-jump`) for
18,000 frames on exact v65 and exact v66 using an isolated Windows desktop,
fresh task-local save directories, no physical background input, and no guest
memory writes. The exact loaded8MiB ROM, emulator and observer bytes were
checked. Each observed44,960 producers,44,984 list writes,51 scratch writes,
50 overlap calls and42 dispatch reads. No invalid type appeared.

The six final RAM/VRAM/OAM/palette/screen artifacts match across v65 and v66.
Input and event lines retain exact order; register dictionaries match after
sorting only their enumeration order. This is ordinary ID14 regression evidence,
not new Shoot execution or an E5 repair.

The initial runner watched the base observer's `done.txt`. That file was closed
before the wrapper's final128-record journal had finished. Root shutdown cut
34 journal lines from the first v65 observation. It did not truncate the earlier
RAM/screen capture or summary counts, but that file is not accepted as a complete
producer ring. The wrapper now closes `producer-done.txt` after the entire ring;
the runner waits for both files. A host-Lua check asserts that the marker exists
before exit. The fresh v66 `-b` rerun has all128 records and the same complete
memory, screen and ordered event trace as `-a`.

- Runtime directories: `build/bizhawk-producer-v65-20261105-a` and
  `build/bizhawk-producer-v66-20261105-{a,b}`.
- Comparison: `build/bizhawk-producer-v66-20261105-comparison.json`,
  SHA C00C7C5426C330E852FCC015DBC5EB59F37AA79D7A48832C933EC2FB7505BB4C.
- Current producer observer SHA146D7645A8F11557EE83E9DD5014A53A41AECD76F9DD0B0E269795E1D7781963.
- Its mocked checker SHA A6BAF511736A3E81526ED239B4A9825E88A4AFF52B74ADFAB703CE839DA6FA2D.

The historical coherent E5 failure remains unresolved; no rollback, type clamp
or guessed gameplay repair was installed. [Producer evidence](id14-collision-type.md)
distinguishes the earlier frozen observer hashes from this later completion fix.

## Source observation and graphics scope

The exact BizHawk2.11.1 WonderSwan managed/native callback order swaps execute
and write callbacks. The source observer now adapts that pinned backend and
requires positive opcode-fetch plus data-read/data-write calibration. Corrected
fresh4,500/30,000-frame runs passed calibration, but neither reached Shoot.
Failed pre-calibration runs are retained and excluded from proof. See
[consumer/lifetime evidence](shoot-lifetime-consumers-20261105.md).

The user authorized native code-based pixel work. A fresh102x16 Korean LAST
CHANCE mask and Japanese WIN/DRAW reuse passed separate source/pixel QA; a
subsequent user request enlarges the Digicode phrase. These art revisions and
the source1.5 title-background work are separate components, absent from v66.
No supplied WSC save was read or hashed. All binaries, captures and generated
source-derived assets remain outside Git.

Open: actual source storage consumers, terminal interrupted-DI/camera/tile
lifetime, reachable lower8EF3 domain, external route/controller, E5 cause,
remaining content/languages and final device QA. v66 is a development checkpoint.

Observer Lua line endings are pinned to LF, with the existing baseline GBA
observer retaining CRLF. This preserves source byte hashes on fresh Windows
checkouts; the six existing Python CRLF exceptions remain unchanged.
