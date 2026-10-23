# Stage-manager priority proof

## Finding and scope

The two native stage-manager reads at `0836D28C` and `0836D2F8` can select
the wrong object configuration when the dedicated logical stage is Shoot
(`11`) and the selected character is `11`, `13`, or `14`. The source reads
the logical stage byte at both corresponding sites. The port's shared
getter instead applies its temporary character routes before reading that
byte. This is a static discrepancy, not a runtime reproduction or a claim
that the complete Shoot scene entry is ready.

This investigation read ROM bytes and decoded instructions only. It made no
ROM, builder, pipeline, emulator, save, or other component changes. The
proposed correction below is not installed.

Examined checkpoints:

| Input | SHA-256 |
|---|---|
| Hit checkpoint, `build/character-hit-routing-20261023/current-candidate.gba` | `A3E0B217C2F077CC628D1543434567CE4B6B77AAF766DFA1903033ECB6474E61` |
| Prospective result-pose parent, `build/result-pose-routing-20261023-a/current-candidate.gba` | `DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C` |
| Ver. 1.5 source | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| Original USA GBA | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |

The relevant getter, manager, expanded tables, and resident Shoot subset are
byte-identical between the two examined checkpoints. Checking the prospective
parent's identity and these bytes does not independently approve its result
component.

## Source condition order and field identity

Source manager `4090:36C0` occupies raw `[743FC0,7440C7)`. Both inline reads
explicitly set `DS=1000`, `DI=004E`, zero `AX`, and execute
`mov al,[di+0E]` at raw `74401D` and `744064`. They restore `DI` and `DS`
afterward. Thus the value is the unsigned byte at `1000:005C`, the logical
stage; neither read accesses the selected-character byte at owner `+0A`.

The first read is followed by this order:

1. Compare the stage with `5` at `744022`.
2. Set bit `0002` of `1000:0713` on equality, otherwise clear only that bit
   with mask `FFFD`.
3. Zero-extend the stage into `BX`, multiply by four, and read the
   `(resource-bank, configuration-near-pointer)` row from `CS:462D`.

The second read independently rereads the stage, multiplies it by four,
and reads `(count byte, stride byte, pattern-near-pointer)` from `CS:482D`.
It computes the existing seed modulo the count and stores the selected
stride and pattern. There is no character condition before either lookup.

The dedicated Shoot entry makes the intended priority concrete:
raw `747A95` writes byte `11` to `ES:[004E+0E]`, calls the graphics helper,
initializes the timer/flags, then calls `4090:36C0` at `747AC2`. It does not
rewrite the character byte to avoid a route override. The native resident
subset does the corresponding stage-byte write at `085C4310` and calls the
manager at `085C433C`.

The source itself does not contain a special "stage 11 before character"
test: it reads the actual logical stage directly. The proposed priority
test is a compatibility adaptation around the port's existing temporary
character-routing policy, preserving that policy outside the dedicated
Shoot case.

## Current native routing and concrete consequences

Retail getter `080D1C78` originally loads `r8=03002310`, reads byte `+0E`
into `r0`, and returns. The current entry branches to `08582C40`, which
implements these ordered conditions:

| Condition on `0300231A`, the owner `+0A` character byte | Returned logical stage |
|---|---:|
| character `11` | `10`, Iraira Room |
| character `13` | `8`, train |
| character `14` | `9`, Waterfall |
| all other characters | byte `0300231E`, owner `+0E` |

The manager still calls this shared getter at both affected sites. Its
configuration hook at `0836D2C0` indexes the twelve-row table `08584C00`;
its pattern literal at raw `36D40C` selects the twelve-row table `08584B00`.
These tables already contain correct separate Shoot rows. The defect is the
selected index, not a missing thirteenth row or a table conversion gap.

| Stage | Source configuration row, raw `744F2D + stage*4` | Native configuration | Source pattern row, raw `74512D + stage*4` | Native pattern |
|---:|---|---|---|---|
| 8 | `(2,4781)` | `(2,08584C80)` | `(2,4,495D)` | `(2,4,0836E328)` |
| 9 | `(3,47A1)` | `(3,08584CC0)` | `(3,4,497D)` | `(3,4,08584B80)` |
| 10 | `(2,47D1)` | `(2,08584D00)` | `(2,4,499D)` | `(2,4,08584BA0)` |
| 11 | `(2,47F1)` | `(2,08584DC0)` | `(2,4,49BD)` | `(2,4,08584BC0)` |

All four configuration pairs differ. Shoot's two callback-table pointers
are source `4829/482B`, native `08584D98/08584D9C`; the competing stages
select their own callback pairs. Pattern bytes for stages `10` and `11`
happen to be identical, although their source and native pointers are
distinct. Therefore character `11` on Shoot demonstrably changes the
configuration selection, but it must not be described as changing the
pattern payload. Character `14` also changes the pattern count from `2`
to `3` through the Waterfall row.

## Exact local correction and ABI

Use a private getter only at the two manager call sites:

```text
read unsigned stage byte 0300231E
if stage == 11: return 11
otherwise: tail-call the unchanged shared getter 080D1C78
```

An exhaustive arithmetic comparison over all `256*256` combinations of
character and stage bytes gives exactly three changed results:

| Character | Actual stage | Current result | Proposed result |
|---:|---:|---:|---:|
| 11 | 11 | 10 | 11 |
| 13 | 11 | 8 | 11 |
| 14 | 11 | 9 | 11 |

All `3069` other combinations in the supported stage domain `0..11` remain
unchanged. This comparison models the decoded conditions; it is not CPU or
game emulation. Values outside the supported stage domain remain outside
the twelve-row table contract. No fallback or clamp is proposed.

The 24-byte ARM helper can consist of:

```asm
ldr   r8, owner
ldrb  r0, [r8, #0x0E]
cmp   r0, #11
bxeq  lr
b     0x080D1C78
owner: .word 0x03002310
```

Its only register outputs are `r0` and `r8`, exactly as with the existing
getter; `r8` remains the battle-state owner. It preserves `r1-r7`, `r9-r12`,
`lr`, and `sp`, performs no writes, and tail-branches instead of creating a
second link. In particular, the second site enters with `r3=0` from
`0836D2F4`; that value and its saved `r5` remain intact. The enclosing
manager saves/restores `r0`, `r1`, and `lr`, and separately saves/restores
`r3` and `r5` around the second lookup.

Condition flags may be changed, as they already are by the current getter.
No affected caller consumes its incoming or returned flags: the first site
immediately executes `cmp r0,#5` at `0836D290`. The second executes `and`
without `S`, a literal load, then `adds` at `0836D304` before any conditional
use. Both caller continuations must remain byte-identical.

Keep both unsigned-byte reads and both independent calls. Preserve the
existing `and r1,r0,#FF` index masks at `0836D2BC` and `0836D2FC`, the
stage-5 flag operations, and every table and RAM owner. The native flag
owner is `03004D10`; its `orr #2` / `bic #2` operations affect only bit 1 of
the existing halfword, matching source mask `FFFD`.

## Callers and shared users

The full eight-MiB checkpoints contain three aligned direct ARM calls to
manager `0836D224`: `08377AFC`, `083785FC`, and `085C433C`. The first two are
existing native scene-state callbacks. The third is the resident Shoot
subset, which currently has no direct caller or embedded pointer reference
in this checkpoint. Source direct far calls to `4090:36C0` are at raw
`76B7DB`, `76C390`, and `747AC2`, respectively. No same-bank near call to
that source entry was found. Do not infer that the unconnected Shoot subset
is already reached by normal gameplay.

The current shared getter has these sixteen aligned direct ARM call sites:

| Native call site(s) | Immediate consumer and priority status |
|---|---|
| `0803EE5C` | Scene setup, stores stage to `03002656`, then initializer dispatch; no local stage-11 guard |
| `080C8264` | Shared object-update entry; its direct getter result is discarded before the following update |
| `080C829C` | Shared object update retains stage in `r11` as a discriminator |
| `080C86CC` | Compares returned stage with retail stage 6 |
| `080C87CC` | Stores returned stage to runtime owner `03003D8A` |
| `0835B384` | Shared auxiliary constructor compares returned stage with stage 3 |
| `0836D28C`, `0836D2F8` | The two unguarded manager lookups targeted here |
| `08627904` | Logical-stage spawn bridge; no local stage-11 guard |
| `08627D14`, `08627D94` | Renderer-flag adapters call only when the actual stage byte is not 11 |
| `08628694`, `086286D4` | Waterfall palette adapters bypass their route when actual stage is 11 |
| `086EEF94`, `086EEFD4` | Train palette adapters bypass their route when actual stage is 11 |
| `086EF14C` | Update adapter bypasses getter when incoming logical-stage `r1` is 11 |

The sole direct branch to implementation `08582C40` is the public getter
entry `080D1C78`. Four separate legacy users at `080C4BC4`, `080C4CC8`,
`080D0BD0`, and `080D1408` instead call analog selector `08584A00`; it has
its own character-first policy and maps added stages to bounded retail
analogs. They are outside this correction.

All byte alignments were searched for embedded canonical and `0A`/`0C`
mirrored ARM/Thumb pointer values to the getter, its implementation, and the
manager; none were found. The halfword-aligned Thumb BL/BLX scan found no
additional direct calls to those targets. These are structural reference
checks, not proof against every dynamically computed target.

A global getter replacement would affect the setup, shared-object, spawn,
and other users above. It would also leave the separate analog selector's
policy unchanged. That wider semantic change is neither needed for this
two-consumer repair nor established by this record. Shared-stage reachability
and the remaining complete Shoot entry remain separate work.

## Proposed write ownership and pins

The prospective DBB parent has a distinct unused code reservation at raw
`[629500,629518)`, native `08629500..08629517`. Its 24 bytes are all `FF`.
It is separated from the preceding result pointer pool ending `6294C0` by
64 untouched `FF` bytes. This is a proposal, not an allocation already
written. The final builder must recheck the exact predecessor and range.

An all-alignment pointer scan including `08/0A/0C` mirrors and interior
destinations found no reference to the proposed 24-byte region. Aligned ARM
B/BL, PC-relative immediate LDR/LDRB, ADD/SUB ADR, and halfword-aligned Thumb
LDR/ADR, B, conditional B, BL/BLX target scans also found no inbound matches.

Only three write spans are needed: four bytes at raw `36D28C`, four at
`36D2F8`, and the 24-byte helper. The existing call words are respectively
`EBF59279` and `EBF5925E`; both decode to `bl 080D1C78`. Total proposed
declared writes are 32 bytes. Preserve all prior code and tables, including
the public getter and its implementation.

Useful exact half-open range SHA-256 guards:

| Region | SHA-256 |
|---|---|
| Source manager `[743FC0,7440C7)` | `A0074B6C754439F96D0DD04BDFF59D0A8FBA4D23F6FE698B0819934BBA5BD2D6` |
| Source Shoot prefix `[747A68,747AC7)` | `1A1B4E6046E15687E8087FF14AF909546AF8F41AE3BC95964C16FB2D992CF447` |
| Source config table `[744F2D,744F5D)` | `4B39652E9E58AF83F0CEE17A3C671A067828DD215104DBA7D4F10B1E5D70AB5C` |
| Source pattern table `[74512D,74515D)` | `EB0D4BAD3FF27220F16B465C45778C43286FF3248B4913513BD0FE7BAE98C8D7` |
| Native manager `[36D224,36D38C)` | `BAD85987BF89590DF2DE5BB72B3CECAB5DDB2118531ED25AF847FE132418F471` |
| Native getter implementation `[582C40,582C78)` | `EDC7EA0D1CBBB0D76547636A2D3F5E22E4A454181B5F40EB92196CEA76A62EEB` |
| Native config table `[584C00,584C60)` | `17DDA5211D60EF553341981E26447E93E02C6A145307DD255371BD277B151F75` |
| Native pattern table `[584B00,584B60)` | `825C46426C772F27E08376179CB1AF3749382C87E2DC06E010C3D762A433B570` |
| Native resident Shoot subset `[5C4300,5C4354)` | `715D48A742EC4B7046E8822615D2E5A2599A7627FFCEFDC04587D338C72A272D` |

Before a future repair is frozen, independently verify exact helper decoding,
both call destinations, the three changed byte-domain cases, register and
flag liveness, all full-ROM inverse writes, and controlled negative cases.
No runtime claim is attached to this read-only proof.

## Installed private manager layer (2026-10-23)

The parent implemented the three proposed spans after the independently
checked Waterfall third-pattern layer. The earlier allocation proposal is
now installed by `tools/build_stage_priority_routing.py`; the public getter,
its other callers, tables, and RAM owners remain unchanged.

| Artifact | SHA-256 |
|---|---|
| B31 predecessor | `B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8` |
| Candidate in both stage build directories | `389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1` |
| Manifest in both stage build directories | `F236202C1A18FDEF595E3647844FC63DDA37D67FC266034F0519B9E216F4DAA7` |
| Parent a/b comparison | `8FBCDDC329C1AA989C67568CE1E74200F27E916DDE78C88B66D201EA8A0D8802` |
| Independent verification and repeat | `0D922956162CB291190290EE0B1FA5083FA2826D49619A1AD061880BBD6465B3` |
| `tools/verify_stage_priority_routing.py` | `52C2C2BB8074A5BFF4970C94B4A49D547FABFD86F2A8E3597330AD9131E18976` |

The stage build directories are `build/stage-priority-routing-20261023-a`
and `-b`. Their `current-candidate.gba` and `manifest.json` are byte-identical.
The comparison is `build/stage-priority-routing-20261023-comparison.json`.
The independent reports are `verification.json` and
`verification-repeat.json` in the `-a` directory, also byte-identical.

The exact installed changes are `36D28C: EBF59279 -> EB0AF09B`,
`36D2F8: EBF5925E -> EB0AF080`, and the 24-byte helper at
`[629500,629518)`. The helper words are:

```text
E59F800C E5D8000E E350000B 012FFF1E EAEAA1D8 03002310
```

Both new BL instructions target `08629500`. The helper reads the actual
stage byte first, returns it immediately when it is 11, and otherwise tails
the unchanged public getter at `080D1C78`. These three spans declare32 bytes
and change29 bytes. Restoring only them reconstructs the entire B31 ROM.

The independent checker imports no builder or analyzer. It checks the
actual encoded instructions across all65,536 character/stage byte pairs,
finding only the three source-required differences listed above. Another
320 incoming-flag/caller cases prove register/LR/SP preservation and flag
liveness at both continuations. There are no RAM writes. All-alignment
mirrored and interior pointers, ARM/Thumb branches, literals, and ADR
references are checked, including the helper's own literal reference.
All103 negative controls pass:46 artifact/source mutations and57 reference
scanner controls. The older source ROM supplies identity context; direct
priority proof uses the actual Ver.1.5 manager and commercial native getter.

```powershell
python tools/verify_stage_priority_routing.py `
  build/waterfall-third-pattern-20261023-a/current-candidate.gba `
  build/stage-priority-routing-20261023-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/stage-priority-routing-20261023-a/verification.json
```

This closes the two manager lookups' priority discrepancy. It does not
establish execution of stage11, complete Shoot initialization, its external
scene route, or campaign behavior. No runtime claim is attached to this layer.
