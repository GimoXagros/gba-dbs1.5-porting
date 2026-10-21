# Added-stage collision binding, 2026-10-16

The ID13 battle capture on the spawn-repaired ROM reached the Train graphics
route but BG0's collision pointer was zero. Both fighters subsequently fell
outside the screen. This is separate from the repaired spawn-literal defect:
the new capture uses ROM
`1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995`.

`build/runtime-spawn-repair-id13-20261016` records BG0 at `03002338`, dimensions
`2x2`, map descriptor pointer `08580400`, and collision pointer `[BG0+28]=0`.
Player 0 world coordinates are `0060,D08A`; player 1 coordinates are
`0385,AD7F`. The actual progress/stage byte is still `1`, while the existing
character-based selector at `08582C40` returns logical stage `8` for character
`0D`. Unifying those logical-stage consumers is a separate implementation item;
this layer does not overwrite progression or modify spawn values.

## Payload and consumer proof

Source resource entries are 24 bytes at `3B4DD0 + index*24`. Their collision
offset/segment fields are `+0C/+0E`, and byte `+5` selects C2. The complete
collision window stays within physical `20000..2FFFF`. The ROM address is
`(bank & 7F)*10000 + (segment*16 + offset & FFFF)`.

| Stage | Source records | Source grid | Dimensions | Bytes | Native records | New grid |
| --- | --- | --- | --- | --- | --- | --- |
| Train | 33 | `380000` | 2×2 | `1F80` | 21 | `622000` |
| Iraira | 37, 38 | `381F80` | 2×2 | `1F80` | 25, 26 | `624000` |
| Waterfall | 35, 36 | `38E240` | 1×3 | `17A0` | 27, 28 | `626000` |

Source `76FC1B..76FC41` derives dimensions from BG fields `+0C/+0E`, multiplies
by 28×18 cells per resource, then selects the collision bank and address.
`76FD04..76FD23` uses four bytes per cell and ORs both halfwords across the
sampled row. Native `08013C38..08013C3C` binds resource field `+0C` to BG field
`+28`; `080C87EC..080C881C` derives the same dimensions and pointer;
`080C8968..080C8994` reads the same four-byte cells. Source
`76FD48/76FD54` and native `080C89E0/080C89F0` classify the same low two bits.

Seven complete commercial source/native grid pairs are checked, without
heuristic flag conversion: native resource rows 0,4,10,12,14,16,18 correspond
to old-source `26CB60,270000,271F80,273F00,275E80,1F9BA0,1FCAE0` respectively.
Each added grid is copied exactly, including all high flag bits and both
halfwords. The added grids use flag combinations absent from the retail
corpus, although every individual bit position already occurs there. This
observation alone is not a proof of every downstream stage effect.

Train source record34 is a 48×2 background without collision. Native Train
records22..24 are intentionally untouched by this collision layer; their
incorrect graphics/initializer representation is handled separately.

## Required classification-table repair

Binding the data alone would expose an existing out-of-bounds stage lookup.
Native `080C8438` obtains a table at `080C84B8` with only nine rows. Source
`76F760..76F820` supplies twelve 16-byte rows. In particular, source stage8
kind1 maps to class5, while stage10 kind1 maps to class14. Reading native row10
instead accesses instruction bytes and can produce handler index `90`.

The layer installs the complete source table at `08627800`. Its first eight
rows are identical to retail; all 192 entries are within the existing
16-handler domain. A two-instruction bridge at `086278C0` loads only `r4` with
the new table address and branches back to `080C843C`. The old `ADD r4,pc,#78`
at `080C8438` becomes the branch into that bridge. Other registers, condition
flags, LR, and SP are preserved. Both native dispatch arrays remain intact.

Source first-dispatch class14 at `76F840` routes to `6F76:02D9`, matching
native `080C856C`; its second-dispatch target is `6F76:034F`, matching the
native return at `080C8638`. Thus class14 does not require invented behavior
inside this collider. A later fighter-effect dispatcher is a distinct issue:
source `4090:25BF` implements an Iraira timer-dependent launch, whereas native
slot14 at table `083549FC` currently returns. Its source-global ownership and
callback translation remain an explicit implementation item.

## Layer and reproduction

New tool: `tools/build_added_stage_collision.py`. It preserves the frozen
predecessor and writes only three complete grids, five resource pointer words,
the source classification table, a 12-byte bridge including its literal, and
the one branch word. Every exact new span passes blank-byte, unaligned pointer,
aligned ARM branch, and aligned immediate PC-relative load guards. The gaps
between allocated spans remain unchanged. No new RAM or task callback is added.

```powershell
py -3 tools/build_added_stage_collision.py `
  build/player-spawn-literal-repair-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/added-stage-collision-20261016/current-candidate.gba `
  --manifest build/added-stage-collision-20261016/manifest.json
```

Candidate SHA-256:
`7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD`.

The independent verifier `tools/verify_added_stage_collision.py` passed all
5,544 cells, 192 classification bytes, 32 classifier-dispatch identities,
786,432 flag cases, and 16 semantic mutations, with full-ROM inverse and inbound
ownership checks. Report `build/added-stage-collision-20261016/verification.json`
has SHA-256
`B7B695D12609FFACF06F84C10E26E7A797D2CCD5C90F508AE1AE2221B99A5AD0`.
Manifest SHA-256 is
`0306A6DD9B628DC702D3548975B4D7EF4662272548B4FEB14A898DA92695071F`.

The parent-run collision-only capture
`build/runtime-collision-id13-20261016` used this exact candidate and reached
character 13/progress 1 with active BG0 collision pointer `08622000`. Its first
fighter ended at world `129F,0BC4`, and hardware OAM contained 32 enabled
objects, compared with zero in the earlier missing-collision capture. Capture
manifest SHA-256 is
`20DA6F22D16A58D46840F5A1293C6B593F94BF41F5DF5DB75C868036CE1A53BA`;
the bounded runtime invariant report is
`6262D559B5ED2B942A67C4E8AC9FDE9C3B752AC832FE8D06BE1195086EC87766`.
The run ended with stop status S02, no asynchronous fault, and the copied native
renderer intact. No screenshot was available from that emission, so this record
does not claim visual correctness.

This layer restores exact collision data and safe source-defined class selection;
it does not claim the remaining Train graphics, stage-lifecycle, or Iraira launch
effect is complete.
