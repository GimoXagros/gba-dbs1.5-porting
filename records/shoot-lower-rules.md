# Lower Shoot rule callbacks

This work continues committed v51 (`edb622d`), whose exact final candidate is
`726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`.
It adds original-order native implementations of the three lower rule
families selected by `4090:9908`. It does not replace the existing `085C0A00`
boundary or install an external scene caller. Static implementation and an
actually playable first milestone remain different claims.

## Source population and actual consumers

All source offsets below are logical offsets in the object overlay whose raw
base is `740900`. The generator treats callbacks, literal pools, palette data,
motion data, spatial tables and spawn permutations separately.

- `810D` enters a movement family through `813F/81AB/81D1/81EA/8266`.
  It handles endpoint movement, HP interruption and paired-object retirement;
  `8526` follows the active target and creates three fan children through
  `881A`, with parameters `0,+1,-1`. `86D9/86FC/876A` restore the palette and
  return to the already resident `7DD9` callback.
- `8AB8/8B28/8B53/8B8A/8C86/8CB4` position the linked object, enter the special
  palette/scroll state, request CF/type2 and signal the active object's `+62`.
  The `8B28 -> 8B53` fallthrough occurs during the same invocation.
- `8CDD/8D4D/8D84/8E27/8E7F/8EC1` follow the target, select a spatial pattern,
  and create its two or three children through `933B`. The source leaves
  acceleration `+36` untouched at `8E27` expiration; only `+32/+34/+38` clear.
- `9798` releases the short-lived child. `97BB/984D/9879` implement the fan
  child, including angle-dependent velocities and the same-invocation
  `984D -> 9879` fallthrough.

These are native functions operating on the existing engine's `r4` object
and `r5` presentation. They use its existing links (`+14/+18/+28`), position
(`+34/+36`), movement (`+42/+44/+46/+48`), target delta (`+56/+58`), HP (`+64`),
timer (`+76`) and source-owned scratch words (`+94..+AA`). The presentation
begins at object `+AC`. No new persistent RAM is allocated.

The commercial object/generator lineage already established by v40/v41 and
v47 is retained. New consumer checks extend it at these concrete functions:

| Source operation | Native consumer and evidence |
| --- | --- |
| `4FFF:0BA4` task priority | `08011E54` loads stack priority and task pointer, stores priority to task `+4`, then calls `08011E8C`. The latter unlinks and reinserts the existing task, comparing its priority and relinking `+8/+C`. Source object minus `10` becomes native object minus `18`, as the retail allocator adds `18` before returning the payload. |
| Commercial priority lineage | Source raw `750B94..750BB7` and WSC1.0 raw `3976C6..3976E9` are byte-identical except their relocated relink far call (`4FFF:0BE5` versus `96B2:0BE7`). |
| `4FFF:26CB` event with frame | `080129C8` consumes stack `[frame,event,ignored,presentation]`, stores event to presentation `+E`, selects the event table, and stores frame to `+1A`. WSC source helper raw `7526BB..7526ED` equals commercial raw `39900B..39903D`. |
| `19BF/19A8` trig | `0801233C/08012348` mask the argument to eight bits and return a signed table halfword in `r0`; only `r8/r9` are scratch. A retained target pointer in `r1` and fan angle in `r6` survive these calls. |
| `4090:172A` allocator | Existing `08352374`, selector0/ID4104, writes the allocated native payload pointer to existing handle `03004D54`. No custom allocation scheme is introduced. |
| `4090:181E` release | Existing `083524C4` consumes stack `[ignored,object]`, marks the object hidden/released, and schedules its existing native task for cleanup. |

Both new child generators preserve the source parent/target links before
allocation. They change the existing task priority to `4000`, then call the
already verified v51 resource adapters: `085C4600` for source `888B` and
`085C4500` for source `93E7`. These adapters retain the complete P1/P0/P2
constructor layout and native draw consumers. The new layer does not copy an
older constructor's superseded resource order.

The source `ES1000:0720` dependency is existing native `03004D40`, used by the
resident `08586E00` translation of source `7642..76D0`. This is an actual
signed increment/decrement/settle consumer, not an inferred adjacent offset.
The helper writes sixteen BG row-zero aliases from the existing converted
scroll table. Lower transitions write `1` on activation and `3F` on restore.
Their seven-row palette copy writes only colors1..15 of BG rows0..6, so those
row-zero aliases survive.

## Arithmetic and timing contracts

The ARM implementation retains 16-bit wrapping for decrements, the `HP+3`
comparison, coordinate dead-zone arithmetic and stored velocities. Source
`JS/JNS` endpoint tests use the low-halfword sign bit; they are not replaced
by signed greater/less comparisons. The source direction-frame selector uses
eight-bit `AL` addition/subtraction and `SF`, including wraparound. It is not
replaced by an angle division. Endpoint crossing also keeps the source's
strict negative-direction `JG` and X-before-Y order.

Elapsed counters use the existing commercial 75-to-60 convention:
375/225/75/105/20/18 source ticks become 300/180/60/84/16/14 native ticks.
The initial spawn delay remains one native callback; source permutation
indices and RNG-derived values are retained. Orbit phase advances by the
source `+1` per native callback. No fractional-phase storage was invented;
its visible cadence remains part of later runtime QA.

CE/type1 uses already installed native `5B`. A9/type2 is native `4C`: the
Ver.1.5 A9 payload at raw `3F85B0` (16 bytes,
`68CA1B6E09B82F7BAB3F0BA06D37FFF0FB539E0D85A75BAEBCBA12DEE89736FF`)
equals retail WSC A7; its commercial request at `083719B4..083719C0` loads
native `4C`, type2 and zero delay. CF and D1 use the independently verified
lower-audio layer's native `5D` (type2) and `5E` (type1). Exact song/table/voice
hashes are required by this builder; numeric ID resemblance is not accepted.
Native timbre and modulation remain analogues; source sweep/stereo audibility
is unverified.

## Spatial input boundary

`8EF3` has five signed Y rows and bounded X lists. Its valid domain is signed
captured target Y `<=1B00` and signed current X `<1E00`. Every valid source
table result is 0..9. Index0 selects the source's explicit unsigned clamp to
`0580..1680`; indices1..9 select one of nine complete position/count records.
These records and all child permutations have a reversible source mapping.

Outside that domain, the original loops can step past their declared table
populations. The native helper explicitly rejects the call without reading
outside those populations or inventing a coordinate clamp; the caller keeps
the idle callback it already wrote before calling `8EF3`. This is a bounded
native behavior outside the equivalence claim. An upstream range proof is
still required before counting complete reachable-domain equivalence or
removing the controller boundary.

## Ownership and verification

Tentative reservation raw `5CB000..5D0000` is not treated as a proof of free
space. Every actual Expected Write is checked independently for all-FF
predecessor bytes, overlap, and inbound candidates. All byte-aligned pointer
patterns and aligned ARM B/BL encodings are scanned. Candidate targets are
preserved byte-for-byte without claiming their origins are data or code:
`5CB7A0`, `5CC6F8`, `5CDBA0`, `5CE1A0`, `5CE1E0`, `5CE210`, `5CED34`,
`5CED50`, `5CFB84`, `5CFE70`. Enclosing gaps remain untouched.

`tools/verify_shoot_lower_rules.py` does not import the generator, assemble
instructions or execute either CPU. It decodes the complete final code,
checks reviewed code/literal identities, every native call sequence, static
stack joins and returns, source data inverses, and final diff containment.
Finite mathematical checks cover all 65,536 halfword decrement/HP inputs,
all 256 direction inputs, 485,376 signed spatial partitions and all 20 legal
child-pattern choices. Palette copies retain all row-zero entries and write
exactly 105 halfwords. Negative controls cover both code and table corruption.

The final lower layer has 33 code blocks, 1,336 ARM7 instructions, 40 Expected
Writes and 6,037 changed bytes. Its enclosing footprint ends at raw `5CC920`.
The entry addresses required by the controller are `810D -> 085CB000`,
`8AB8 -> 085CB970`, `8CDD -> 085CBD80`. Child generators are
`881A -> 085CC1D0` and `933B -> 085CC2E0`.

- Input audio predecessor: `0F05DD3A5BEBE663A29D0241E1AD6D460763E2DE5D16BCEB4F7092D596B70103`.
- Output `build/shoot-lower-20261013/lower.gba`: `223C64C6D19ACE7610CC7FE7D276DC24CE47748C424894D2A589220F48B21C6E`.
- Build manifest: `3F081B93E3BA18637628E60794762CB80513DEAAEEF4DF3085EFA7B5118A946B`.
- Independent report: `313105EF1A8D5C26A42F690DB93A7BE0B25F89771168D0036FC3071E9CE26030`.

The independent report also covers 18,400 endpoint/crossing branch partitions,
17,664 pursuit/reversal partitions and 19 altered-code/data/gap negative
controls. Every static stack join and return balances. Runtime, emulator,
audibility and supplied-save QA have not been performed.
