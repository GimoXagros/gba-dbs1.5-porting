# Terminal common-tile clear: upload lifetime and storage

This is the narrow implementation investigation after v70, followed below by an isolated static-companion component. It does not close the external route or change the main ROM build. Original C415 and retail996D, plus current8EC8, are the evidence inputs. The physical terminal clear is still exactly `(0800 + (BX << 6)) & FFFF`, 128 zero bytes; BX is a camera pixel value under the separately checked scheduler/pause contracts. Mapping every destination into native OBJ VRAM would be incorrect.

## Positive source upload lifecycle

Source presentation constructor752474/752478 initializes parity byte+14 and pending-upload handle+2A. Native0801283C/08012840 initializes the corresponding byte+16 and pointer+38. The independent review is `records/shoot-presentation-fields-qa-20261106.md`; it positively distinguishes nearby background/global offset matches and does not infer unrestricted free RAM.

Both source event setters restore graphics in the same order:

| Operation | Event24CB | Explicit-frame26CB |
|---|---|---|
| Check alternate/indexed flag2 | 7525FF | 752796 |
| Toggle parity | 75260C..615 | 7527A3..7AC |
| If pending, undo toggle, unlink pending task, zero handle | 75261F..640 | 7527B6..7D7 |
| Synchronously upload selected current frame/bank via2E6E | 752646..653 | 7527DD..7EA |
| For multi-row event, allocate next-frame F001 callback2E21 and store handle | 75266D..6A7 | 752804..83E |

The queued payload contains the presentation address, next frame's P0 descriptor index and opposite bank. Source update2862 toggles parity at752896; the nonloop terminal path undoes that toggle at7528B5. Normal advancement chooses the subsequent descriptor, cancels any pending task at7529A5..9B8, and installs a replacement at7529BB..9EC. Callback2E21 at752E11 reads its own payload, uploads via2E6E, clears presentation+2A at752E41 and unlinks itself at752E55.

Physical uploader2E6E computes `(fixed_base << P0.shift) + (bank ? P0.alternate_bytes : 0) + presentation.graphics_base` at752EBB..ED2. Descriptor length and bytes come from the actual indexed P0 table. Its CC6/D1E transfer calls are synchronous:750CBC..CC0 and750CFA..CFE poll DMA length port46 before and after the transfer; the chunked D1E variant similarly waits at750D73..77. Mask expiration therefore belongs to upload completion, not a later guessed IRQ event. Source standalone226E at75225E instead directly copies descriptor0 by REP MOVSW at7522A8; that is a separate writer population.

The source draw consumer adds P0.alternate_tiles when parity is nonzero. Native dynamic draw08012C7C..12D94 selects current descriptor and copies pixels to EWRAM according to a dynamic OAM index. It does not use fixed_base as the native VRAM destination. Native P0 headers retain the source alternate fields at+8..0F, so the logical fixed tile can be reconstructed without changing the normal dynamic staging index.

## Why a stage11 reset would be wrong

Shoot initialization747CF2 branches directly to747D6F when the first fighter is already in base form. It does not reconstruct that presentation; predecessor parity is retained. The evolved path reconstructs via2E74 then sets event0 at747D43. A stage11-only synthetic parity reset would therefore corrupt the logical tile identity for base-form entry.

A narrower potential tracking population is the identified first fighter during predecessor stage7 and Shoot stage11. Source74334A..743374 proves actor handles65C/65E are allocated before the generic constructors. Generic constructor74374D calls2E74, then743761 sets its first event, so the first-player identity exists before that initial event. The native paired sequence also publishes FIRST before initialization:352B80 supplies0300489C to allocator352BAC;35248C/352490 stores the new actor through that output pointer. The caller then loads FIRST and invokes3530BC. Its353240 resource constructor call precedes353248 presentation=actor+AC and35325C first event call. The stage scope and an additional pending-task capacity remain separate requirements before live hooks are installed; this ordering is not a complete queue endorsement.

Native allocator08011AC4 accepts stack words `[priority, ignored segment, callback]`, returns task-header pointerR0 and initializes status+10. It saves r1/r2/r4/r5/LR but uses r3/r8/r9 and flags. Native task-free08011BE4 takes `[ignored segment, task pointer]`, unlinks the header and clears status+10. Payload starts at header+18. Priority is stored sign-extended from16 bits; the insertion search08011F90 uses unsigned comparisons. Any F001 restoration must pass the sign-extended native value consistently.

## Existing scene field suitable for a compact mask

The current native common root positively owns scene payload+52:0833FD6C obtains the new payload,0833FD70 adds50, and0833FD78 stores the scene-case argument at+2. Generic case0..3 entry083400B4 reads this argument. The terminal case5 continuation instead follows the resident1750..1DC3 graph and has no further case-argument use.

The ordinary terminal timers occupy+50 and remain live throughout the sequence, so they cannot hold a persistent clear mask. Result presentation occupies0..4F; result coordinates overwrite+0/+2 and the timer is reset at+50. These fields cannot simply be declared dead at197A.

For the bounded common-tile projection BX224..288, first cleared tile is `2*BX-448` (0..128), with four consecutive tiles ending at most131. A packed halfword can hold that first tile in bits0..7 and four live blank bits in bits8..11. This fits the existing dead case-argument field+52; it requires no extension of the allocated payload and no unrelated global RAM.

The capture helper0833FDC0 uses fixed0203F000/0203E000 and hardware DMA, not scene payload. Fade0833FF00 likewise uses fixed0203F000/hardware and the divide helper. Exit08340C54 invokesD1B0C then retires the current task. Its cleanup callees use fixed actor-list030047A8, input/battle handles03004510/14 and existing mode/global state; native08012714 is a retained BX LR. These inspected consumers do not read the prior case argument. A final component must pin actual phase bytes/call contracts and initialize the packed state only on the established terminal owner before reusing it.

## Remaining implementation gates

A newly identified static population matters even when the primary fighter's two banks1..72 are disjoint. Source2E74 at743867 chooses companion base49hex for side0,6Dhex for side1;743873..743886 preloads descriptor0 through226E. It stores the companion resource record at actor+6C at7438B1..8B5. Actual child constructor781AFE reads this pointer,781B99..781BE0 passes the same base into23F4, and781C0E overwrites presentation flags with facing4000 plus stage-dependent2000. In particular bit2 is clear, so this consumer does not use indexed uploads or alternate-bank parity. Native3593E0 reads corresponding actor+80;3594F8/3594FC selects6D/49,35954C passes the base into127E4, and35956C performs the corresponding flags overwrite. All30 companion records15..29/45..59 have static P0 descriptor0; their side0 layout tile identities occupy73..108. These are a positive overlap with some BX>=261 clears, not unused graphics.

Native353464/353468 retains the preload's base selection even though the graphics copy itself was omitted. This is a concrete candidate expiration hook for a static-companion mask when2E74 reloads that resource. Source result preload773BD5..773BE4 uses base137hex, and orb preload7438EB..7438FA uses91hex; those positive writers are outside the companion interval. A complete static subset still needs companion later P4 writes, exact preload-before-draw ordering (or late restoration), and other positive overlaps accounted for. Sibling companion-consumer analysis and independent actor-lifetime analysis own those remaining narrow checks.

The static-companion subset needs no queued upload task. It may therefore be implemented separately from the primary-fighter parity restoration once its own consumer/reload interval closes. This would remain a partial terminal correction with the external route closed; it would not authorize ignoring lower common-tile destinations, non-common destinations, or the separately identified6D child population.

The prospective small projection records that packed mask on the existing terminal scene owner, preserves normal native dynamic rendering, and substitutes zero pixels only for live logical clear tiles. Source-equivalent uploads expire the relevant bits. Full upload timing matters: a draw may precede a queued upload, so applying a mask too early cannot be justified without the exact later owner/consumer interval.

The primary-fighter restoration still requires the scoped constructor/queue lifetime and task capacity. Existing P1 bounds1..72 and child6D retirement are not a complete alias census. Other standalone226E writers, non-common destinations, terminal IRQ/no-refill and external entry remain separate open gates. The following bounded static-companion implementation does not add a queue or claim a complete terminal clear.

## Actual draw ordering closes the static-companion blocker

The earlier proposed draw-before-preload objection confused presentation-list append with rendering. Source74241A..742424 and native0835298C..083529A0 append the companion presentation to the existing list, source0C00:3A22/native03004830 with count3A20/0300482A. The companion's pool2 priority2C00 does not execute the dynamic pixel copy there.

The actual scene battle consumer is source741495..7414B1/native08373550..0837357C. It walks that same list and calls source2A4B/native08012C28. Its task is positively created with priority6000 at native080D1BF0 and stored through03004514 at080D1C00. Callback replacement08011E7C changes only the callback, retaining that priority. The actor pool's FIRST3000 and SECOND3800 tasks, and all26 priorities read by its constructor, precede6000. Thus FIRST evolution/devolution can reload after the companion is queued but still before its actual dynamic renderer executes. The expiration shim can clear the mask before copying pixels; no late redraw or new metadata storage is needed.

The five direct source2E74 callers are74374D generic initialization,747D0C Shoot initialization,767503 evolution completion,7676D1 devolution completion and76BC62 boss reconstruction. The latter positively loads SECOND065E at76BC37, selecting companion base6D. The first two are initialization owners before the terminal mask. The form-completion calls run within the existing actor tasks before the priority6000 renderer. This does not assume FIRST stops updating or that all children have retired.

`tools/analyze_shoot_companion_draw_order.py` checks the paired append and actual consumer, same list pointers, priority producer, callback-only replacement, actor priorities/pools, side-dependent preload bases, resource-offset producer and five-call source population. It intentionally makes no arbitrary-scheduler-state claim.

## Isolated component and frozen outputs

`tools/build_shoot_static_companion_clear.py` now emits an isolated ROM from exact8EC8 and sourceC415. It uses only the existing terminal payload+52 dead case argument: low8 bits hold first logical clear tile, bits8..11 hold four live blank flags. The capture hook preserves the original clear helper. A clone of the retained native dynamic renderer preserves every normal OAM index, sprite position and tile-copy instruction, substituting one ROM zero tile only for recognized static companion P0 owners at logical base49 whose tile is still blank. The2E74 preload hook expires the actual descriptor0 byte-length overlap and then executes the displaced native load, preserving registers and condition flags.

The supported clear subset is BX261..288 and the30 exact static companion P0 pointers. Their side0 tiles are73..108; BX279..288 produces no matching companion tile. Primary fighter graphics, lower common destinations, side1 companions and unrelated fixed-tile owners retain their prior behavior. Record21 retains its retail nine-layout adaptation; source1.0 and1.5 content match, so no asset repair belongs in this component.

The initially proposed6FE100..6FF000 range failed the strict conservative inbound census at five destinations:6FE308,6FE3A0,6FE6A8,6FE6B0 and6FE756. No data/interior exemptions were made. The actual clean reservation is the entirelyFF suffix6FE800..6FF000, below the sibling6FF000 boundary. Full-ROM unaligned pointer, mirrored pointer, ARM and Thumb reference scanning finds no inbound reference to that suffix.

| Write | Raw offset | Bytes |
| --- | --- | ---: |
| Existing-task owner lookup |6FE800|136|
| Capture shim |6FE900|64|
| Retained renderer clone/data |6FEA00|648|
| Preload expiration |6FEE00|124|
| Clear-call hook |5CD314|4|
| Dynamic dispatcher pointer |12C50|4|
| Preload hook |35346C|4|

The dispatcher previously points to03000204, the relocated native renderer after its PUSH. The clone likewise omits that PUSH because08012C28 already saved r0..r5/LR, and restores its extra r9 save before the retained epilogue.

There are984 declared written bytes and964 actual changed bytes. A full inverse restores exact8EC8 with no undeclared write. Fifteen controls reject modifications to all seven component writes, an outside byte, source append, actual native draw, battle priority, side-dependent preload base, resource-offset producer, form delta and companion table. Independent actual-ARM QA is a separate approval gate.

The November6 outputs `build/shoot-static-companion-20261106/final-component.gba` SHA256 `3179083005E8E3A669988028943577AE9F686F282E376C485B52B6D42C811DAE` and manifest `BB9720EC87001328533500666B6D6563B2752D9D88D2ECF1354D51DF894F1DDC` are **superseded and must not be integrated**. Resumed source review found that the preload hook receives a byte offset inR5, not a main-resource pointer. Native353348..3350 computes `id << 5`;353370..3380 adds the evolved-table delta `0860B000 - 084A80F8` when selected. Only35349C..34A4 subsequently adds companion table084A82D8 and stores the resulting resource address. The old `[R5+1E0]` dereference was therefore wrong; synthetic pointer fixtures could conceal it.

The corrected shim obtains P0 through `[084A82D8 + R5]`, then reads descriptor0 length. This reaches the actual30 companion records, including evolved offsets; the remainder of the mask interval and register/flag restoration is unchanged. Producer instructions and their three table literals are now checked, with three added mutation controls. Fresh corrected outputs are `build/shoot-static-companion-20261109/fixed-component.gba` SHA256 `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` and `fixed-component.json` SHA256 `D8B5207060441EA60025ED88AC56F272B9E8615CD711C144BA94AEFF33476E75`. Builder SHA256 is `2546A5D26591F7B580799B639534B2FCB55CF7563CB54421FBCE48D7A98EC92C`; draw-order analyzer SHA256 is `675C0398AF0129873266592AD31DBC2D72BF75D6160258D46D12694DBF868B5F`. Both scripts use LF line endings. Independent QA must exercise real resource offsets and reject the superseded implementation before integration.

Reproduction uses the pinned Python runtime and:

```text
tools/build_shoot_static_companion_clear.py build/repro-v70-20261106-a/current-candidate.gba <original WSC1.5> <fresh output.gba> --manifest <fresh report.json>
```

No main builder, Git state, emulator, supplied save or guest memory was changed. The primary-parity/task-capacity, other-owner alias, non-common destination, IRQ/camera and external-entry gates remain open; this component closes only the described static-companion projection and its known preload lifetime.
