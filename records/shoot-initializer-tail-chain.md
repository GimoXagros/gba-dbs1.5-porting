# Disconnected Shoot initializer tail composition (2026-11-05)

This layer appends the three existing phases for source `4090:73F0..7534`
to entry `08629800`, after the two storage operations and their cleanup.
The body now composes the retained source initializer through its final RETF
under the component contracts below. There is still no external scene caller,
earlier snapshot caller, or completed scene/controller lifetime proof.

## Frozen artifacts

- Builder: `tools/build_shoot_initializer_tail_chain.py`, SHA-256
  `79864D12BDCBC06A083196F3533AC523BD6A14C200EE97EBFFAC2197D7B82D0A`.
- Exact predecessor:
  `build/shoot-initializer-storage-20261103-a/current-candidate.gba`, SHA-256
  `66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF`.
- Fresh outputs: `build/shoot-initializer-tail-chain-20261105a` and `20261105b`.
  Their complete two-file path/hash populations match.
- Both `current-candidate.gba` files: SHA-256
  `5C625010E5D08C7E5B4AE07997D649EA37154D76AA2C01AD3286DBB9EA7C8B46`.
- Both `manifest.json` files: SHA-256
  `4C3064AB05DC7D1E19DB65779DA68600BC4BB820C0E4B3DA9D6B726348AB3083`.
- Comparison: `build/shoot-initializer-tail-chain-20261105-comparison.json`,
  SHA-256 `164A1EB26864D941550707CD367394288DBE4A63A76E103110200230EEFBEFCC`.

The interrupted `20261103-a/-b` tail artifacts remain unchanged. The candidate
ROM is byte-identical to those earlier results; the new manifests strengthen
the dependency checks. Existing output or report paths are now rejected before
any input is read. Separate CLI checks verified both refusals with nonexistent
ROM input paths, unchanged existing artifacts, and no new output.

Independent final-artifact verification was completed separately on 2026-11-05.
`tools/verify_shoot_initializer_tail_chain.py` has SHA-256
`D11DC18DE0BE86EFF54BB8B2B5BE52B68697537FBCA0F2705076F8E1D6ED2F27`.
The two output directories now also contain identical
`independent-verification.json` reports, SHA-256
`9C530F9BB055BAEB5CE52B279110721E063C07973297EBBE0FDB0A182937BC50`.
The earlier two-file comparison covers builder outputs before these reports
were added. Independent checks cover 256 ABI cases, 142 negative controls,
ten synchronous functions, 23 PC literal owners, 18 dependency intervals and
the full inverse. The synchronous tail stack bound is 176 bytes including
the outer frame; asynchronous/live-scene bounds remain excluded. This checker
does not import the builder or consume its manifest. Main integration and
runtime evidence are recorded separately in `shoot-initializer-integration-v65.md`.

## Source order and exact write

The complete raw source tail is `[747CF0,747E34)`, 324 bytes, SHA-256
`91EE7DCA7CF669DC17CF74BE804681668D9382FBAC5B45CDE917BC1797C14689`.
It includes the return at source `7533` and excludes the gray table at `7534`.
Existing independent phase readers check the native instruction populations,
the current fifteen-record physics routing, source HUD pixel and palette
inverses, and selective palette behavior. They are reused without modifying
the existing phases.

| Source interval | Existing native phase | Role |
|---|---|---|
| `73F0..74A2` | `085C1500` | Other-player reset and conditional base-form restoration |
| `74A2..74DA` | `085C1800` | Late HUD tiles, P2 and scroll clear |
| `74DA..7534` | `085C1C00` | Selective palette capture, gray zeros and white projection |

The only Expected Write is raw `[629878,62988C)`, 20 declared bytes,
19 actually different. It replaces the old two-word return and twelve FF
bytes with:

```text
EBFE5F20 EBFE5FDF EBFE60DE E8BD4800 E12FFF1E
```

These are three ARM BLs in the table's order, followed by the original
`POP {r11,LR}; BX LR`. The storage cleanup at `08629870/74` is unchanged;
it releases the eight-byte storage buffer and restores scratch registers
before the first tail call. No frame, RAM allocation, clamp, snapshot call,
callback or scene entry is added. Restoring the single write recovers the
entire exact storage predecessor. Full-initializer reservation
`085C7800..085C8000` remains FF.

The complete composed entry occupies raw `[629800,62988C)`, 140 bytes.
The finite encoded-reference scan finds one apparent Thumb conditional branch
into the twelve new bytes: the low half `D008` of retained ARM instruction
`08629870:E28DD008` appears to target `08629884`. Positive ARM ownership
classifies it as `ADD SP,SP,#8`. No other scanned pointer, mirrored pointer,
ARM/Thumb branch, literal or ADR candidate enters the extension. This does
not exclude arbitrary computed aliases.

## Dependency review

The interrupted builder guarded only `[12874,12960)` of the event setter.
Actual branches reach `08012978`, `080129BC` and the return at `080129C4`;
the P2 calls at `0801296C/080129B0` also lay beyond that truncated guard.
The new guard covers the entire `[12874,129C8)` consumer, SHA-256
`1BBCE2EEE607287D2AEFA2B899D43A9C4C6890BFE5CCAF6533D8FAF6EBF2EBD4`.

Direct synchronous code/literal dependencies are now pinned as follows:

| Consumer | Raw guarded interval | Boundary |
|---|---|---|
| Resource reconfiguration | `[353304,3534E0)` | Complete body and PC literals through `3534DC` |
| Presentation constructor | `[127E4,1285C)` | Entry through its `BX LR`; unrelated next function excluded |
| Event setter | `[12874,129C8)` | All branches, both P2 calls and final return |
| Event sound request | `[0D15C0,0D15F0)` | Request body and `030022F0` literal |
| P4 assignment | `[358254,358264)` | Four instructions; does not call following P4 dispatcher |
| Stage flag helper | `[584940,58496C)` | Body and `03002310` literal |
| P2 loader | `[132EC,133A8)` | Complete native palette consumer |
| Base resource records | `[4A80F8,4A82D8)` | Fifteen complete main records |
| Base companion records | `[4A82D8,4A84B8)` | Fifteen complete companion records |

The reconfiguration call passes form zero, so its evolved-table branch is
not taken. Its ID15 path has an unbalanced push/return and is excluded by the
existing character-ID `0..14` precondition. No ID is silently clamped.
The complete resource-table literals are guarded even where the selected
call does not take that alternative.

The manifest records all nineteen fixed dependency intervals and hashes,
including retained front code, the three phases, earlier snapshot code,
gray table, HUD pixels/P2, BG alias helper and current physics blob. Tests
mutate both ends of every interval. This pins the synchronous code and base
tables; it does not invent a full closure proof over dynamically addressed
P0/P1/P2 payloads, future P4 dispatch, asynchronous sound consumption or
the full scene. Valid existing presentation/resource payloads remain an
inherited caller precondition.

## ABI and lifetime limits

The entry preserves `r0-r12`, LR and SP; flags may change. Its original
eight-byte frame stays live, and each retained tail helper saves 56 bytes.
The late HUD P2 path uses `56+20+16=92` bytes below its entry, or 100 bytes
including the retained outer frame. The directly inspected reconfiguration
constructor path uses `8+56+12+24+60+16=176` bytes. These are bounded direct
paths, not a proved live-scene maximum or asynchronous IRQ stack allowance.

The other-player handle `0300489C` and presentation at object `+AC` must be
valid, with native character ID `0..14`, valid slot/resources and the matching
base/evolved physics pointer at object `+60`. The retained front's engine,
stack, player/auxiliary handles and exclusive display ownership still apply.

Earlier snapshot `085C1900` must already have run before source `1073`'s
destructive colors. It is guarded but is deliberately not called inside
source `7168`. The final phase captures 384 selected bytes, sets sixteen
gray color-zero entries, and projects white to 528 hardware bytes. Nonzero
OBJ colors in rows `8/12/14/15` remain inherited snapshot data; the conditional
other-player phase refreshes rows `8/12`. The canonical mirror must remain
owned until source `1331` restores it. Competing startup, pause or cutscene
owners are outside the retained normal case-5 lifetime argument.

The storage predecessor's initialized functional EEPROM and serialized
DMA3/timer-2/IRQ service preconditions remain unchanged. Failed-device data
equivalence is not claimed. No storage behavior is replaced by this layer.

Builder self-checks reject 76 mutations: each output byte, changes outside
the write, dependency endpoints, occupied reservation, changed source tail,
reordered calls and an unaligned mirrored pointer into the new bytes.
No emulator, physical storage operation, supplied save or runtime transition
was used. External scene entry, snapshot timing, terminal IRQ/camera lifetime
and full gameplay completion remain open.

## Reproduction

Run from the repository with a fresh output directory; use `20261105b` and
the matching storage `-b` predecessor for the second invocation:

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -X utf8 tools/build_shoot_initializer_tail_chain.py `
  build/shoot-initializer-storage-20261103-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-tail-chain-20261105a/current-candidate.gba `
  --manifest build/shoot-initializer-tail-chain-20261105a/manifest.json
```
