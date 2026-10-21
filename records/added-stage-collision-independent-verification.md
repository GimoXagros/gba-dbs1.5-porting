# Added-stage collision repair: independent verification

Verified 2026-10-16 by `tools/verify_added_stage_collision.py`, which imports
no generator. Input is the player-spawn repair
`1B1AA23C4913881B2F7FCAF28692D7A7EAC7B046D1A5E1F09ED3D77CC4054995`.
Output is
`7FB315945EEA965CBD5DDF0FAD84B6FCCFF9D6364974769964022281E92445DD`.
No save or emulator was accessed by this verifier.

## Complete source grids and actual consumers

| Arena | Source resource records | Source raw / bytes | Native resources | Output raw |
| --- | --- | --- | --- | --- |
| Train | 33 | `380000` / `1F80` | 21 | `622000` |
| Iraira | 37, 38 | `381F80` / `1F80` | 25, 26 | `624000` |
| Waterfall | 35, 36 | `38E240` / `17A0` | 27, 28 | `626000` |

The source resource records are 24 bytes at `3B4DD0`; their collision bank,
offset, segment, width, and height are independently resolved. Train and
Iraira are 2x2 screens; Waterfall is 1x3. Each screen contributes 28x18
four-byte cells, giving **5,544 distinct-position cell inverses** across
the three payloads. Both halfwords of every cell are preserved. Five native
descriptor fields at `580000 + resource*24 + 0C` change from null to the
corresponding payload; every other field, including Train resources 22..24,
is unchanged.

Seven commercial WSC1.0/GBA grid pairs independently establish the unchanged
four-byte representation. Native `08013BF8` copies descriptor `+0C` to
background `+28`, and copies dimensions to background `+0C/+0E`.
Movement path `08373A08 -> 080C86B4 -> 080C87C0` consumes that exact pointer.
The source `6F76:048A` counterpart selects its bank and segment, multiplies
screen dimensions by 28 and 18, and addresses each cell with a four-byte
stride. Its horizontal/vertical sample accumulation matches native
`080C8988..899C` and `080C8BE4..8BFC`.

Low two-bit blocking tests, boundary `8000`, `6000` return suppression,
and the separate floor helper's `2000/4000` displacement cases are pinned
to actual source/native instructions. This is stronger than claiming that
new flag combinations are safe because their individual bits appeared in
old grids. It still does not establish every later actor behavior.

## Classifier defect found and repaired during independent review

The stationary floor path `08373B24 -> 080C8258 -> 080C8294` reads both
cell words and stores them in actor `+5A/+5C`, corresponding to source
actor `+4A/+4C`. It extracts `(first_word & 3C) >> 2` and indexes a
16-byte stage row.

Retail native table `080C84B8` contains nine rows. The source 1.5 table
`6F76:0000`, raw `76F760..76F820`, contains twelve. Without the repair,
Train stage 8 kind 1 incorrectly becomes zero. Iraira stage 10 kind 1
reads byte `90` from native instruction data and then indexes a 16-entry
function table with 144. Iraira's actual grid contains kind 1; this is a
concrete consumer-domain defect, not merely an undocumented effect.

The repair copies all 192 source table bytes to `08627800`. At
`080C8438`, a nonlinking branch replaces the original ADR and enters
`086278C0`:

```asm
ldr r4, [pc]       ; literal 08627800
b   080C843C
.word 08627800
```

This defines exactly the original ADR destination `r4`, preserves all
other registers, SP, LR, and CPSR, and resumes the unchanged lookup.
All source table outputs are below 16. The verifier independently reverses
every table byte and checks all **786,432** combinations of twelve stages
and a complete 16-bit first word, including preservation of unrelated flags.
The first eight stage rows remain identical to retail. Arbitrary OR
combinations of sampled cells in each added grid produce only kinds 0 or 1.

Both 16-entry collision-helper dispatcher tables retain exact source/native
function identity. In particular, source class 14 in these two tables
dispatches onward and then returns; the corresponding existing native
`080C856C -> 080C8638` path already exists. This fact applies only to the
collision helper's dispatchers.

## Separate, concrete Iraira behavior gap

The later fighter dispatcher is a different consumer:
source `4090:2309` at raw `742C09`, table `742C1F`, versus native
`083549E0`, table `083549FC`. Source entry 14 selects `4090:25BF`
(raw `742EBF`); the native entry still selects return `08354DD4`.
The source handler uses the timer's low three bits to choose a launch row,
can request sound, invokes release and animation helpers, and installs
another actor callback. The new collision/classification layer does not
implement that behavior. It must be translated using actual native field,
sound, helper, and callback lineage, rather than assigning a convenient
effect number or guessing RAM adjacency.

Consequently this PASS covers complete grid binding, representation,
classifier safety, and classifier dispatch. It is not a full Iraira
gameplay or Train graphics completion claim. Train graphics/initialization
are being repaired in a separate layer; runtime validation remains separate.

## Verification boundaries

The predecessor is FF over each exact new payload/table/bridge span. A
whole-ROM scan rejects any byte-aligned encoded pointer, aligned ARM
B/BL-like reference, or PC-relative literal reference into those spans.
This finite scan does not claim exclusion of arbitrary computed references.
The full 8 MiB ROM diff is limited to those spans, five descriptor words,
and the original ADR hook. Gaps and all other bytes are preserved.

Sixteen semantic mutations are rejected without checking the final-ROM
hash: missing/wrong grid bindings, wrong geometry, either cell halfword or
last byte corruption, missing Train/Iraira classifier entries, out-of-range
class, wrong bridge register, linking return branch, interior table pointer,
unowned gap write, low-bit semantic change, dispatcher change, and an
unrelated Train resource mutation.

Reproduce:

```powershell
python tools/verify_added_stage_collision.py `
  build/player-spawn-literal-repair-20261016/current-candidate.gba `
  build/added-stage-collision-20261016/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/added-stage-collision-20261016/verification.json
```
