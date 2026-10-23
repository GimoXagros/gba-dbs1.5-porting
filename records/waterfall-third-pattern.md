# Waterfall third pattern and successor records

Date: 2026-10-23. The source-backed component restores the missing third
Waterfall configuration and its native constructor, then corrects two
successor-row calculations in the retained hazard helper. It changes 156
declared bytes in four spans. Independent artifact verification and runtime
evidence are separate from the source proof and builder checks below.

## Observed failure and exact route

The parent-owned DBB long-run capture ended at PC `2D0020E8` with
`r8=2D0020E9`, `lr=083525C8`, and no screenshot. A generic invariant result
did not establish valid control flow. The object was a **stage entity** at
`02011198`, with presentation `02011244`; the selected ID14 fighter at
`02011710` still held a valid callback. The stage presentation retained
P1/P0/P2 `080D3DA4/080D30A0/080D3F90`.

The parent then captured the actual write at `0836D85C`, reported next PC
`0836D860`. It stores `2D0020E9` after reading callback-slot address
`FFFFFFFF`; `r9=08584CC0` is the Waterfall configuration base. The portable
observation is the captured register and memory state, not a claim that an
out-of-range read must produce that same word on other hardware.

| Evidence | SHA-256 |
|---|---|
| `build/runtime-result-pose-id14-screen-20261023/capture.json` | `30B00B4B75738A12F7F913E47DA3F98AE5B68E1D627CFC0441EAD7EE9F6DAD4B` |
| `build/runtime-invalid-callback-writer-20261023/probe.json` | `C49C2E376474C48807BE7FEC374976B6EF222A3BE14687C53A981D3F2AC2F773` |
| Root-owned portable fixture, `records/fixtures/waterfall-third-pattern-overread-20261023.json` | `5CA4ED6CB5FADD7D12BB5C5375CD2C63791856AC993181C4ABA1037B7E371751` |

The common dispatcher simply loads `[r4]` at `083525BC`, sets `lr`, and
branches through `r8` at `083525C4`. The invalid callback originates in the
configuration consumer, not that dispatcher or a character action table.

## Actual producer, selectors, and three-record extent

Source manager `4090:36C0`, raw `[743FC0,7440C7)`, reads stage at `74401D`
and selects `CS:462D + stage*4`. It stores the configuration near pointer to
`1000:0708`. Its second stage read at `744064` selects `CS:482D + stage*4`,
stores the cycle length to `1000:070C`, the pattern pointer to `1000:070D`,
and the initial remainder to `1000:0704`.

Native manager `[0836D224,0836D38C)` obtains logical stage9 from the existing
character14 route. Its configuration hook at `0836D2C0` calls the existing
index shim `08584D40`, using table `08584C00`. The config pointer is stored
to `03004CFC` at `0836D2DC`; alternate common-config owner `03004D00` is set
to `0836E200` at `0836D2E8`. The pattern pointer comes from table `08584B00`
through literal `0836D40C`; stores at `0836D330`, `0836D33C`, and `0836D348`
populate cycle length `03004D04`, pattern `03004D08`, and index `03004CF8`.
This component does not alter the shared stage selector.

Source config row raw `744F51` is `(3,47A1)` and the next stage's row at
`744F55` points to `47D1`. That fixes a 48-byte extent: **three** 16-byte
records. The first word `3` is retained without using it as an assumed
record count. The record extent and actual pattern selectors establish the
three consumed records independently.

The source pattern header at `745151` is `(3,4,497D)`: initial seed modulus
3, cycle length4, and pattern pointer. Native row `08584B48` is
`(3,4,08584B80)`. All 32 pattern bytes are retained exactly:

```text
(selector,timing) = (1,10),(0,10),(2,10),(1,10),
                    (0,10),(2,10),(1,10),(2,10)
```

The actual loop wraps its pattern index at4. Its reachable selector sequence
is `[1,0,2,1]`, including selector2. This is not an unreachable padding row.

Source consumer `[7442A9,744357)` reads the selector at `7442DA`, multiplies
by16, selects the normal or alternate configuration base, loads all seven
metadata halfwords, then reads through its callback slot at `74433B`.
Native consumer `[0836D77C,0836D8B4)` is unchanged from USA: `0836D7C8`
reads the selector, `0836D7D0` multiplies by20, `0836D7FC` adds the normal
base, `0836D848` loads the callback-slot pointer, and `0836D858/85C` load and
install the callback.

| Selector | Source record | Source slot → callback | Native record → slot → entry |
|---:|---|---|---|
| 0 | `7450A1`, `4090:47A1` | `481F → 3DFB` | `08584CC0 → 08584D88 → 08585200`, retained |
| 1 | `7450B1`, `4090:47B1` | `4821 → 3EE0` | `08584CD4 → 08584D8C → 08585500`, retained |
| 2 | `7450C1`, `4090:47C1` | `4823 → 3FCA` | `08584CE8 → 0862967C → 08629600`, restored |

Before this layer, only the first two native records existed. The third
record's twenty bytes at `[584CE8,584CFC)` were `FF`. The correct source
record is `000f0013800000008003ffff01002348`. The native conversion keeps
its first fourteen bytes, adds two zero pad bytes, and expands the callback
slot to 32 bits. All sixteen original USA records from eight retail stages
provide the same metadata conversion oracle. Both pre-existing Waterfall
records and their callback slots remain unchanged.

This corrects the earlier two-record assumption in
`records/object-config-conversion.md` and `records/stage-runtime.md`.
Their statements excluding `4090:3FCA` as unrelated to Waterfall are false:
selector2, the third record, and slot `4823` prove its actual ownership.

## Complete callback family and native reuse

Mode3 is source `4090:3FCA..40AE`, raw `[7448CA,7449AF)`, exactly229 bytes.
The final `retf` is at `7449AE`; the next independent constructor starts
at `7449AF`. The family contains constructor `3FCA`, wait `4019`, and
exit `406D`.

Its whole source body equals the existing mode1 family
`[7446FB,7447E0)` after precisely six changed bytes:

| Relative location | Mode1 | Mode3 | Meaning |
|---|---|---|---|
| `10` | `01` | `03` | Hazard mode |
| `3A` | `40` | `C0` | Initial sine phase |
| `48..49` | `3E4A` | `4019` | Wait callback relocation |
| `62..63` | `3E9E` | `406D` | Exit callback relocation |

The constructor preserves the source order: write hazard3; set presentation
event0; clear presentation flag bits `6000`; set horizontal velocity
`FF90`; clear the other motion fields; set phase `C0`, toggle0, and timer
`0100`; install the wait callback; perform the first wait update immediately.
Source object fields `26/32/34/36/38/7E/80/82` map respectively to native
`34/42/44/46/48/94/96/98`. The display flags stay at presentation `+08`.

The new native entry `[08629600,08629674)` retains the existing mode1
constructor's116 instruction bytes except the two source constants and four
necessary PC-relative relocations. Its literals are owner `0300256A` at
`08629674` and retained wait `08585274` at `08629678`; callback slot
`0862967C` points back to `08629600`.

The retained native wait `[08585274,08585310)` and exit
`[08585310,0858538C)` contain no mode1-only branch. Wait timer0 sets direction
bit4000, velocity0070, and the shared exit callback, then returns. Otherwise
it advances the presentation by1, stores signed sine/2 as vertical velocity,
toggles the one-bit counter, and advances phase modulo256/decrements timer
on every second update. Exit uses the source **signed** `X < 0F00` test;
at or beyond the boundary it calls the retained destruction service. The
exit update retains the same animation, sine, and phase cadence.

The four service mappings are backed by the unchanged commercial callback
`0836D8B4..0836D9C7` and the old/new source generic callbacks
`393F11..393FB5` / `744357..7443FB`. Those 165-byte source bodies match after
ten explicit service, continuation, and global-address relocations.

| Source service | Native service | Use |
|---|---|---|
| `4FFF:24CB` | `08012874` | Select event0 |
| `4FFF:2862` | `08012A84` | Advance presentation by1 |
| `4FFF:19A8` | `08012348` | Signed sine lookup |
| `4090:398E` | `0836D750` | Clear active gate and destroy stage entity |

All256 signed source sine entries at `[7519C9,751BC9)` equal the original
and retained native entries `[12360,12560)`, SHA-256
`9287394FA9384EEAAA175244A8CB0A9AF4B0FF78D0BB0F58869173D342410D30`.
The original resource constructor and P0/P1/P2 remain unchanged; event0 and
delta1 are the same requests already used by modes1/2. No new graphics,
presentation population, or palette resource is introduced.

ABI: `r4` is the stage object and `r5` its presentation. The new entry follows
the retained entry's clobber contract (`r0`, `r8`, native service effects,
and condition flags), saves/restores its caller's `lr`, and balances all
argument pushes. It makes no new assumption that `r11` is zero. The maximum
additional stack use before retained service entry is20 bytes, including
the shared wait's saved link. The new constructor's callback sequence is
entry `08629600 → wait08585274 → exit08585310`.

Same-bank pointer scans find `3FCA` only at source slot `4823`, and `4823`
only in record `47CF`. No encoded direct far-pointer/call alias to
`4090:3FCA` exists in the source ROM. The retained native wait has one direct
caller, mode1's `08585268`; this repair adds the new constructor's call.
Its exit is installed by the existing wait's PC-relative address operation.
These bounded scans do not assert absence of arbitrary computed callers.

## Mode3 downstream ownership and two phase2 corrections

Hazard `1000:0384 → 0300256A` is separate from display phase
`1000:0382 → 03002568` and palette owner `03003D30`. The C50 display callback
does not branch on the hazard mode, and the compact palette path uses its
own counters. Neither needs a new mode3 branch.

The retained hazard helper at `08584600` masks the hazard word with3 and
accepts modes1..3 inclusive. Its source/native three-pair table is identical:
`(5,7),(1,7),(1,3)`. The focused downstream check exposed a separate
off-by-one in the existing phase2 clears. Each invocation reloads the
original pair into `r5/r7`; increments made in phase1 cannot carry into a
later invocation.

Source phase1 explicitly decrements the first ID at `76AC37` to inspect
the original entity's row. Source phase2 at `76ACA9..76ACD8` multiplies the
original IDs by6 **without** decrementing, clearing their successor rows.
The native phase2 incorrectly subtracted1 before its stride8 calculation.
Only those two instructions change:

| Site | Before | After |
|---|---|---|
| `085846F4` | `E2451001`, `sub r1,r5,#1` | `E1A01005`, `mov r1,r5` |
| `08584704` | `E2471001`, `sub r1,r7,#1` | `E1A01007`, `mov r1,r7` |

Both old SUBs and new MOVs have `S=0`, preserving CPSR flags. They write the
same destination register only. Phase1's subtraction at `0858467C` remains
unchanged.

| Mode | Initial entity IDs | Successor IDs | Correct phase2 row indices | Remaining IDs |
|---:|---|---|---|---|
| 1 | 5,7 | 6,8 | 5,7 | 10,11 |
| 2 | 1,7 | 2,8 | 1,7 | 9,11 |
| 3 | 1,3 | 2,4 | 1,3 | 9,10 |

Native initializer `0801369C` clears sixteen iterations of four words from
`03001C68`, exactly256 bytes/32 eight-byte rows through `03001D68`. The next
live owner is the halfword at `03001D68`. Service `08013764` converts each
nonzero entity ID into `(ID-1)*8`. Every successor clear above is in-bounds,
as are all remaining IDs9..11. This proves the selected-data bounds and the
two source row corrections, not complete unrestricted hazard-service parity.

## Write ownership, reproduction, and verification

The predecessor is the frozen result-pose candidate DBB; the independent
review of that parent is tracked separately. No stage-priority helper is
installed here, and its proposed `[629500,629518)` region stays untouched.

| Item | SHA-256 |
|---|---|
| DBB predecessor | `DBB66875367C01CE60A60FD47819191F44FF04FBFD23C09F591100E738CF265C` |
| Candidate, both builds | `B31A46AEC0DD74736CB300339D1475DF23363E8A97E3D79846E3CE64073C3AF8` |
| Manifest, both builds | `769C744D08071DAA508F474B6AE300339B8FD415DB0F11137BF0A8C09626B428` |
| Source analysis, both runs | `73A8FF82C3CC0D825B555CA1EB127CE84BAE02670ECBA4D0DB7254E8777C0C6B` |
| `tools/analyze_waterfall_third_pattern.py` | `DB327A22961631CBEE0CEB725525BFBA06775115313C0F34504AF1D9CAE174A3` |
| `tools/build_waterfall_third_pattern.py` | `A24B850450A15FEAB16319B7FABACDEF7DF1D9FBC41ECE4901F7E6BC383B66F3` |

The independent source analysis checks all sixteen retail metadata records,
all three Waterfall records/slots, eight retained pattern pairs and the four
reachable cycle indices, full229-byte callback correspondence, all256 sine
entries, downstream row bounds, and19 rejected controlled mutations. Its
reports are under `build/waterfall-third-pattern-analysis-20261023`.

The builder produces byte-identical ROMs and manifests under
`build/waterfall-third-pattern-20261023-a` and `-b`. It writes exactly:

| Raw half-open span | Bytes | Purpose |
|---|---:|---|
| `[5846F4,5846F8)` | 4 | First successor row |
| `[584704,584708)` | 4 | Second successor row |
| `[584CE8,584CFC)` | 20 | Third configuration |
| `[629600,629680)` | 128 | 116 instruction bytes, two literals, callback slot |

Total declared156 bytes; actual changed151 bytes. Restoring only those four
spans reproduces the complete predecessor. Both new ranges are exact
predecessor `FF` space. All-alignment mirrored/interior pointer scans and
ARM/Thumb branch, literal, and ADR scans cover the proposed ranges and the
two existing instruction sites. One conservative hit is explicitly
classified: halfword `E310` at `085846D2` resembles a Thumb branch into the
third record, but it is the upper half of the guarded ARM instruction
`085846D0: E3100C02`, `tst r0,#200`. The surrounding complete ARM routine is
hash-guarded; no unclassified inbound reference remains.

Reproduce the builder with positional ROM paths and explicit manifest:

```powershell
python tools/build_waterfall_third_pattern.py `
  build/result-pose-routing-20261023-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/waterfall-third-pattern-20261023-a/current-candidate.gba `
  --manifest build/waterfall-third-pattern-20261023-a/manifest.json
```

The analyzer takes `CURRENT GBA OLD NEW OUTPUT_JSON`. Both CLIs reject
non-ROM input extensions and output/input aliases before reading inputs.
No emulator or save was opened by this component's author.

The separately authored `tools/verify_waterfall_third_pattern.py` is now
frozen PASS, SHA-256
`BFE3F8BAC6F3B9162B3B73025292B74EB8B090D24E19805B96FD063A2A63A2E4`.
Its `verification.json` reports in both build directories are byte-identical,
SHA-256 `0F30817BB70154F582B6E2FED3A286C440CBF84F97F7E2C1952962CAB9F1B4A1`.
It imports no builder/analyzer and uses neither manifest nor runtime fixture
as an oracle. Coverage includes all three complete records, active cycle
`[1,0,2,1]` and twelve seed/cycle routes, the complete229-byte source family,
124-byte entry and callback slot, retained wait/exit/services, all-mode
32-row bounds, both exact MOV corrections, classified ARM/Thumb overlap,
156-byte inverse ownership, and522 rejected negative controls.

```powershell
python tools/verify_waterfall_third_pattern.py `
  build/result-pose-routing-20261023-a/current-candidate.gba `
  build/waterfall-third-pattern-20261023-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/waterfall-third-pattern-20261023-a/verification.json
```

The parent-owned240-second B31 probe at
`build/runtime-waterfall-third-consumer-20261023/probe.json` reached a bounded
S02 timeout with no entry event; it does not establish third-pattern runtime
coverage. A first-round miss is explainable from the actual producer: the
initial index is `03002326 modulo3`, and the failed DBB capture had seed
`31F4`, hence index2 and selector2 on its first entity. That capture's three
schedule thresholds were `0A8C,FFFF,FFFF`, allowing only one ordinary
first-round trigger. With a different initial index, that single entity can
select pattern0 or1 instead. The remaining countdown is derived from the
existing battle words modulo`0665`, plus1. This is a diagnosis of coverage,
not a change to the seed or schedule. Runtime probes remain parent-owned;
no full-stage, full-round, or campaign claim follows from static PASS.

The later parent-owned natural-input probe on candidate389F did reach the
restored constructor. Its report is
`build/runtime-waterfall-third-targeted-20261023-a/probe.json`, SHA-256
`17CC88BF92185B6D19D3DFA7319CFAA6D817F73106670EBB16D21B736AF3247F`.
The first stop at `0836D348` observes initial index `r3=2`. The second at
`08629668`, immediately before the shared wait call, observes stage entity
`r4=02011198`, its installed callback `08585274`, phase byte `+94=C0`, and
the four bytes at `03002568` equal to `00 00 03 00` (display phase0, hazard
mode3). There are no guest writes, asynchronous stops, or timeout in that
probe. This is bounded runtime evidence for the constructor and its state;
it does not yet prove completion of the shared wait/exit, all hazard phases,
or a complete round. The earlier no-hit probe remains a separate observation.
