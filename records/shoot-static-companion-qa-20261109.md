# Independent static-companion component QA

The corrected isolated component passes independent source checks and bounded execution of its actual emitted ARM instructions. Approval applies only to the 30 recognized static companion P0 owners at logical base49 and clear BX261..288. It does not authorize the external Shoot route or claim a complete terminal clear.

## Frozen evidence

| Item | SHA256 |
| --- | --- |
| Exact v70 predecessor | `8EC8C50755B16E1C6AF7D6984CF4A5510335CD07AA67E265CAE67CF7F8366717` |
| Corrected component, `build/shoot-static-companion-20261109/fixed-component.gba` | `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` |
| Independent verifier, `tools/verify_shoot_static_companion_clear.py` | `CD2E7B85032AFEFD492E89CDBD1060E30B7E56FEF6B5934B81C8E4906684B943` |
| Independent report, `build/shoot-static-companion-qa-20261109/audit.json` | `DF06DEBA3B9BF1B405F6BFE81DE3188DC6002F935723491DEB45A0AB999422CC` |
| Retained interpreter dependency, `tools/verify_shoot_attack_dispatch.py` | `695ECA1DF385033BB48B3EC1054ECF1C21AF2E5DBF6DF5966D53489BB230E698` |
| Interpreter/scanner dependency, `tools/verify_shoot_caller_resident.py` | `7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D` |

The CLI checks original retail GBA `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` and original WSC1.5 `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`. The verifier and report use LF endings. It imports independent verification/interpreter code only, never a production builder or its manifest.

## Corrected real preload ABI

The first component `3179083005E8E3A669988028943577AE9F686F282E376C485B52B6D42C811DAE` is withdrawn. The interrupted partial verifier had fabricated a RAM resource record and put its pointer in R5. This concealed a real builder bug.

Actual retained instructions353348..353350 load the fighter ID and set R5 to `ID << 5`. Evolved construction353370..353380 adds `0860B000 - 084A80F8`; R5 is still a record byte offset at35346C. The old helper's `LDR [R5,#1E0]` therefore addresses low memory. With the corrected real fixture, the withdrawn component fails immediately at `uninitialized read 000001E0/4`.

The corrected helper resolves the descriptor through companion table `084A82D8 + R5`. Every preload fixture executes the actual retained offset producer, evolved delta when applicable, and35345C..353468 side selection before entering the installed hook at35346C. It never fabricates a RAM resource record. The verifier also positively checks the producer instructions and both evolved table literals. A mutation reverting to the old pointer interpretation is rejected independently of ROM hashes.

## Executed checks

| Check | Result |
| --- | --- |
| Owner search | 577 cases: every one of52 slots for all11 recognized phases, inactive/unrecognized owners, and exclusion of slot53 |
| Capture | 69 cases: BX224..289 plus0/FFFF/FFFFFFFF, exact four-tile mask, original clear-helper tail and original arguments/SP/LR |
| Dynamic dispatcher and renderer | 6,476 cases covering all30 P0s and219 native layouts, every BX261..288, plus sparse flags, both facings, native tile counts, alias P0 exclusion and boundary paths |
| Actual blanked parts | 2,236 logical parts across the full-layout clear sweep; each uses zero staging pixels while complete native OAM and dynamic indices remain exact |
| Preload expiration | 30,720 cases across all30 real record offsets, bases49/6D, partial/empty/full masks, interval boundaries and all16 NZCV combinations |
| Same-frame ordering | 120 cases executing native enqueue35298C, optional actual preload hook, then actual draw-list consumer37354C..37357C |
| Negative controls | 19 rejected:14 source/behavior/ABI mutations, two undeclared-write mutations and three conservative inbound reference families |

Record21 retains all nine retail layouts. Its sparse-mask test deliberately uses native layout3, which contains logical tile offsets0/1, and tests each live bit separately. The broader renderer sweep visits every one of its nine layouts. No asset conversion or repair is involved.

For the same-frame tests, actual enqueue instructions store the presentation in03004830 and increment0300482A without changing staging pixels. Side0 reconstruction after enqueue expires the blank flags before the actual battle6000 consumer draws; side1 reconstruction leaves the side0 flags live. Omitting the preload hook fails this actual instruction sequence. The retained scheduler insertion/link instructions and native task priorities2C00/3000 before6000 are checked separately, without asserting arbitrary scheduler-state validity.

All full dynamic-render comparisons include the entire1,024-byte OAM staging buffer and4,096-byte pixel staging buffer, not just the changed sprite parts. Sparse tests vary original tile-count starts and flags/palettes/priority/facing paths. Indexed flag2, base6D, inactive owners, empty masks, clipping and capacity boundaries retain their native behavior. Flag1 is checked through the actual unchanged dispatcher prefix and its unchanged background-renderer target; the background DMA renderer itself is not executed by this verifier.

Expiration preserves every register R0..R14 and CPSR, except for the exact displaced original R0 stack load. Its only non-stack write is the established scene mask halfword. Capture similarly writes only the dead scene case halfword, then forwards the original clear-helper call. The source physical clear at7738C6 is decoded as `(0800 + BX*64) & FFFF`,64 zero words; its address/length/zero-data instructions are explicitly checked.

## Ownership and negative controls

The strict scanner checks the entire predecessor ROM, including unaligned/mirrored pointers and ARM/Thumb candidate references, against the entirelyFF reservation6FE800..6FF000. It uses no data or interior exemptions. Local controls prove the same scanner detects an unaligned mirrored pointer, an ARM branch and a Thumb branch into that reservation.

The whole-ROM inverse restores only the four emitted blocks and three hooks: owner6FE800..6FE888, capture6FE900..6FE940, renderer6FEA00..6FEC88, expiration6FEE00..6FEE7C, and four bytes each at5CD314/12C50/35346C. All other bytes, including unused reservation padding, must equal the exact predecessor. Separate mutations prove that an outside byte and an unused padding byte are rejected.

Behavioral controls independently reject: missing final owner slot, wrong owner phase, wrong clear upper bound, wrong physical-to-logical subtraction, wrong renderer base, wrong per-part logical tile, ignored individual live bits, opaque zero tile, legacy R5 pointer interpretation, omitted expiry, lost condition flags, wrong displaced stack argument, omitted same-frame preload and changed source clear length. These checks execute or decode the relevant semantics instead of failing only on an output digest.

## Reproduction and limits

From the repository, use the pinned Python runtime:

```text
C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -u -X utf8 tools/verify_shoot_static_companion_clear.py build/repro-v70-20261106-a/current-candidate.gba build/shoot-static-companion-20261109/fixed-component.gba "C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba" "C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc" <distinct-output.json>
```

Only the verifier, its report and this QA record were authored by this QA task. No main builder, runtime, emulator, provided save/state, guest memory or Git state was changed. Tests use a bounded independent ARM model and actual ROM instruction bytes, not an actual game observation. The existing interpreter supports only reviewed instructions used by these fixtures.

Primary-fighter parity/queued uploads, lower common destinations, other fixed-tile owners, non-common destinations, unrestricted IRQ/camera ownership and actual external Shoot entry remain open. The root task separately owns full-build integration and hidden runtime verification.

## Independent completed ordinary-result capture audit

After root confirmed launcher exit0, completed capture `build/bizhawk-result-v71-20261109-a` passes frozen `tools/verify_result_language_capture.py`, SHA256 `249EDF4E32838E8DC623A2CCEDEE676AA6B62F63177902AD943E5E1034A4C381`. The captured full8MB loaded ROM and probe ROM both equal corrected35D4 from full buildA. Launch completion, unchanged observer/executable, private desktop, isolated paths, disabled state loading and no guest writes all pass. All61 top-level capture files are rehashed against the final launch inventory; eight full snapshot sets and1,508 visible Korean WIN pixels pass, including the five existing negative selfchecks.

The audit reuses already-reviewed v70 report `D7B85F2D0606FB4D26B499CFC1388E45D358A7B3CE908B3B8A204102218B8DC0`, verifies its launch/trace pins and rehashes every reused baseline artifact. It does not rerun the previous emulator session or inspect either run's SaveRAM tree.

| New artifact | SHA256 |
| --- | --- |
| `build/result-v71-runtime-qa-20261109/audit_capture.py` | `BC15D23CA7E3B80C71746DCF921A6F084560D0538407EAAF9DACB12A523EE33C` |
| `build/result-v71-runtime-qa-20261109/ko-audit.json` | `23F56022C242F78F6C224D8DFD08FE245829E9E7E2A94AA06A207E46DC25E5F1` |
| `build/result-v71-runtime-qa-20261109/v70-comparison.json` | `9BD4F553A1DF0CA26C4CC27AE7A874DBCE041AF09CFE468CF73EB30BA4D77DCF` |
| Completed launch | `D51B3404A763D0870E4B66C94ADAC0A0F469B70435D01271DF32275923A0B33F` |
| Actual trace | `9FC08B1C1A21E071AEDF1014F2EAED39D73EE28874BB3B3F89C960FD3B77CA1E` |

The new audit script and both reports use LF. Reproduction is the pinned Python runtime followed by `build/result-v71-runtime-qa-20261109/audit_capture.py`, from the repository. Neither frozen verifier nor capture/observer/launcher was changed by this independent audit.

Every one of the eight screenshot files, complete EWRAM buffers, VRAM buffers, palettes and OAM buffers is byte-identical to its corresponding v70 snapshot. The independent script asserts these equalities. The same mode/stage ordering,47 input key/release rows, native writer tag, seven initializer callback/object/resource triples, two unique draw callback/presentation rows and final summary fields match. The active WIN label remains event0/layout0,30 parts, palette bank2,1,508 matching pixels and105 active OAM entries. The full native copied renderer remains exact `D18F290027729112F393814CDAE81BA110F94192D2C82B75A8CBA40C4501F685`.

Timing is explicitly different; no frame values were silently normalized:

| Snapshot | v70 core | v71 core | Difference |
| --- | ---: | ---: | ---: |
| Options staged |3458|3458|0|
| Options committed |3558|3559|+1|
| Title committed |3559|3560|+1|
| Battle entry |3998|3999|+1|
| Result entry |11518|11519|+1|
| Result+120 |11638|11639|+1|
| First visible label |11775|11776|+1|
| Result+300 |11818|11819|+1|

Both sessions start at core1; the native writer entry is core3482 in both. The first logged timing divergence is mode20 after that write, old relative3495/new3496. Later ordinary input edges inherit the one-frame offset. All exact input/mode/stage/writer/draw/initializer frame pairs and deltas are preserved in the comparison report. Battle-entry to result-entry lasts7,520 core frames in both; the visible-label age remains257. These are observed milestones, not an explanation of the first timing difference or a performance-parity claim.

Raw IWRAM is not identical. Changed-byte counts per snapshot are4/2/6/2/5/2653/6/5 in the table's order; all exact changed ranges are retained in the report without attributing their producers. Two display-register dumps, battle entry and first label, each differ in36 bytes; the other six are exact. A frame-boundary register dump is not a scanline trace. These differences are not discarded, while the corresponding complete screenshots and active render buffers remain exact.

This confirms bounded ordinary Korean Options commit → title → natural battle → WIN rendering through the changed global dynamic-dispatch route. It does not exercise an active terminal mask, actual Shoot entry, LAST CHANCE/DRAW, full campaign, fresh-process language persistence, E5 resolution or hardware behavior. No extra emulator launch, provided save/state access, capture edit or guest write was performed.
