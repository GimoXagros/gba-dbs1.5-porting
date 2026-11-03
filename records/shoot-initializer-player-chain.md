# Disconnected Shoot prefix/player composition (2026-10-26)

This layer adds one 24-byte entry at `08629800`. It calls the verified prefix
`08629700` and then the existing player phase `085C1000`, composing source
`4090:7168..7394` at the retained component boundary. The new entry has no
external caller. Full initializer `085C7800` and scene/controller routes
remain absent.

## Frozen artifacts

- Builder: `tools/build_shoot_initializer_player_chain.py`.
- Exact predecessor: `build/shoot-initializer-prefix-20261026-a/current-candidate.gba`,
  SHA-256 `4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC`.
- Outputs: `build/shoot-initializer-player-chain-20261026-a` and `-b`.
- `current-candidate.gba` SHA-256:
  `2C9C96129EBECF30FCB915E077899CE91FBA979F4AC44C027EE39F4C9A8C4BC7`.
- `manifest.json` SHA-256:
  `A3C0E86A04334090B18051AE8FE33621403EF4BF967D070295A7978D8C1931EF`.
- Both ROM and manifest match between builds. Comparison report
  `build/shoot-initializer-player-chain-20261026-comparison.json` SHA-256:
  `DCDAFB5741F501E38A2CA4AA97DDBC7F3044EDEF5271054E5F13EC2B50E3C56C`.

This is based on the native port checkpoint; it does not require the separate
result-language candidate. The earlier prefix's independent verification is
recorded in `records/shoot-initializer-prefix.md`.

## Pre-write contract review

The read-only report was produced before the ROM write:
`build/shoot-initializer-player-chain-contract-20261026.json`, SHA-256
`614FE2AAC7055F34EA40F0B5D0B9D5321FEF931D2FA98B5379AEB82AAD231CF6`.
It records all fifteen dependency intervals and their current byte hashes,
the actual source resources, the reserved range, and the planned six words.

The complete source player phase is raw `[747AD1,747C94)`: 451 bytes,
129 decoded x86 instructions, SHA-256
`9B65CB9B0866AB0B2137B34BBAEAD2B367760B276C9EB3C6666575AA2D428774`.
The existing native phase `[5C1000,5C11A4)` remains exactly the reviewed v47
420-byte placement (96 instructions plus nine literals), SHA-256
`AEF73AB400F8B6611201CBAF3F24E19693D62BA7D84976A8479FFA33A46D2843`.
No phase instruction or constructor argument was changed.

Actual source pushes at `729A` and `7353` resolve to these resources, and the
actual native constructor loads establish P1/P0/P2 roles at presentation
`+44/+48/+4C`:

| Object | Source P1 / P0 / P2 | Native P1 / P0 / P2 |
|---|---|---|
| Active | `3CF410 / 3D5F80 / 3D4B20` | `085D0000 / 085D1000 / 085B9300` |
| Auxiliary | `3BD730 / 3914E0 / 3D7640` | `085D029C / 085D1100 / 085DB700` |

Independent existing readers check both P1 containers: 19 commands,
143 payload items, A records and null/non-null B records. P0 inversion covers
89 descriptors, 39,200 tile bytes, 54 layouts and 2,278 bounded layout tile
reads. In particular, the active P0 retains its repaired descriptor pointer
to `085F3B20`; the obsolete empty-descriptor resource hash is not reused.
Both palettes recover all 32 source colors exactly.

The fifteen HP table entries remain source-identical. Finite checks cover
all 3,840 character/difficulty-byte cases and both 16-bit object flag domains
(131,072 mask cases). Existing constructor arguments and active/other links
are checked from final instructions. Auxiliary entry `085C1300` saves the
matching frame and jumps to `085BC244`, after allocation, reusing the object
at `03004D3C` without allocating a duplicate.

The retained player's contract covers source-equivalent fields and service
order. It does not promise every intermediate store is identical: the
native HP calculation coalesces the source's initial/subsequent HP stores,
and the existing auxiliary body writes some fields in a different internal
order. This layer preserves those components unchanged and makes no new
claim about interrupt-time observation of intermediate object state.

## Exact write and ABI

The only Expected Write is erased `[629800,629818)`, with words:

```text
E92D4800 E3A0B000 EBFFFFBC EBFE5DFB E8BD4800 E12FFF1E
```

These decode as save `r11,LR`, set `r11=0`, call `08629700`, call `085C1000`,
restore `r11,LR`, and `BX LR`. Both callees already preserve `r0-r12`, so
another fourteen-register frame is unnecessary. The entry therefore
preserves `r0-r12`, LR and SP, permits flag changes, and adds eight stack
bytes. It contains no literal data and allocates no RAM.

The declared write is 24 bytes; 21 bytes differ from FF. Restoring the single
range recovers the exact entire 4BA predecessor. The prefix, player phase,
auxiliary body, resources, callbacks and all other bytes remain unchanged.

A whole-predecessor ownership scan found no all-alignment pointer, mirrored
`08/0A/0C` pointer, ARM/Thumb branch, literal or ADR reference into the range.
Full inverse plus the two decoded outgoing calls preserves that absence of
an external caller. A raw final-image Thumb scan can mistake the `4800`
halfwords inside the two ARM push/pop words for Thumb literal loads; these
are the reviewed ARM entry/restore instructions, not incoming control flow.

The known direct constructor path uses
`8 + 56 + 36 + 60 + 16 = 176` bytes for chain, player, auxiliary-reuse frame,
arguments and constructor frame. This is **not** a proved maximum over every
transitive helper, and no live scene caller's available stack is established.
The entry requires a valid native stack with eight bytes beyond the retained
callees' requirements.

Builder checks reject 48 mutations: every new byte, writes outside the
reservation, changes to each pinned dependency, occupied ownership, missing
full-initializer boundary, and changed source. These are builder self-checks;
a separately authored final-artifact verifier is a separate review step.

## Reproduction

Run from the repository, replacing `-a` with `-b` for the second unused output
directory:

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/build_shoot_initializer_player_chain.py `
  build/shoot-initializer-prefix-20261026-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-player-chain-20261026-a/current-candidate.gba `
  --manifest build/shoot-initializer-player-chain-20261026-a/manifest.json
```

## Explicit preconditions and remaining work

The three object handles at `030048A0`, `0300489C`, `03004D3C` must already
be valid; the other character ID must be in `0..14`; exclusive scene/display
ownership must hold throughout both calls. The existing pool-survival proof
in `records/shoot-scene-object-pools.md` concerns the normal case-5 pool-0
cleanup, not arbitrary entry or an entire new scene's lifetime. The stage
manager does not allocate these player/auxiliary objects.

The next source interval is `7394..73A9`, already represented by the
disconnected OBJ-slot-5 palette loader `085C1700`; it must follow the player
phase before any later initializer work. This record does not connect it.

Source SRAM `1000:3CD8/3CDA`, terminal interrupted DI, camera lifetime,
remaining initializer/tail sequencing, and external scene/controller entry
remain open. No emulator, supplied save, runtime transition, audio, or
gameplay test was performed. Main pipeline and runtime probe changes belong
to the coordinating task, not this layer.
