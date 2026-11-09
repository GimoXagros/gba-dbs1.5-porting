# Guarded stationary transition IRQ independent QA — 2026-11-09

PASS for exact component18BB under the retained normal scene/task ownership and stationary base-ID0 family. This is resident component approval. Moving low-Y entry, exact interrupted-DI resolution, external Shoot entry and complete Shoot remain open. No emulator or user save was opened.

The approved ROM is 18BBA3DF3A2634828A80033F6BA5E788C58CD1C78B169F502C99663BE514EBD1 over exact v72 predecessor025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA. Its four writes total1576 declared bytes and1550 changed bytes: D0BE8 hook4;6FF600 adapter/tiny display288;6FF9C0 guard1092;6FFE10 IRQ/final/table192. Inverting those exact spans recovers the entire predecessor. Both complete erased reservations6FF600..6FF800 and6FF9C0..6FFED0 pass strict whole-ROM pointer/ARM/Thumb inbound checking without exemptions.

The independently normalized layout ledger binds all70 predecessor component manifests,1394 explicit intervals and416 conservative merged intervals. No declared object overlaps either cave, including an erased tail. The nearest real object ends6FF28C; the next begins712680. Apparent6FF9B2 is a Thumb encoding inside frozen ARM code; apparent6FFF68 comes from unchanged packed graphics inside the original4MiB ROM. Erased bytes alone were not accepted as allocation proof.

The positive native mappings are source held/edge1E/20→2C/2E; current26/28→34/36 and previous2A/2C→38/3A; motion32..38→42..48; current displacement3A/3C→4A/4C. Actual native constructor11AE4 sign-extends the task priority: source argumentF000 becomes FFFFF000. Five actual producer cases check this. The new52-slot helper passes109 active/inactive/out-of-pool cases. The guard passes380 cases with54 distinct predicate refusals, every blank-tile byte, both horizontal row endpoints and native row-wrap boundaries.

Shoot-specific mapping is important: source1000:020E→native03002388→F000/logical ports10/11, while01CE→2338→F800/ports12/13. Waterfall has a different object-to-hardware assignment. The guard checks actual text mode, character base0,4bpp, no mosaic, screen base30 and32×32 geometry, all32 common-tile0 bytes and current zero map rows. It checks native y=k+37 through159, using row((state8−29+y)&255)>>3. Source-only144-line reasoning would miss native bottom8 pixels. All32 columns must be zero; no horizontal DI value is substituted.

The heavy predicate runs after real17758 copies the prepared queue, in the owned current==last display task. Its sole callback is selected in existing storage. Four independent actual instruction chains execute installed D0BE8→adapter→17758→copied IWRAM C9000→line1 scheduling→actual1140C dispatcher→tiny callback→retained5E7400→empty C9000. Fourteen postcopy cases preserve the real17758 register outputs and all copying effects, adding only the recognized queue-pointer substitution. This is not a VBlank-only predicate or a claim that the next ordinary iteration cannot execute. The stationary-family argument relies on the retained neutral/control-zero/motion-zero/no-op actor and normal ownership contracts.

Each full chain then executes30 interrupts, eight matches and the final return. Old counters1/40/115/143 schedule first native compares8/47/122/150 and final compares38/77/152/180. These are actual ARM-model values, not captured LCD timing or a general performance benchmark.

The exact192-byte IRQ unit remains39B5D48FAC09792EAED50E903ECDE85C0CC17ED3DAF52FAF17C36D3A8BF8767D. Another720 cases execute actual retained C4C/F44/C10 instructions, including two independent C4C inputs and a third C10 hardware read. Checks cover source table0,2,4,7,10,13,17,21; full16-bit counter carry/wrap; match/mismatch scroll; exact ordered memory/MMIO effects; eighth-match callback replacement; and every live register/SP/LR/NZCV. Sixteen flag patterns verify that final BX LR has no effect. It does not compute source ES:[DI+A], invent DI=EA or replace the operand with constant zero.

The stale callback is checked144 times, including actual exit shape mode8/stage11/flags0D86, wrong stage and cleared0400 across all16 incoming flag patterns and all three retail IRQ arms. Registers and ordered memory/MMIO effects equal the existing route; stale IRQ slots are replaced. Intermediate condition flags differ in108 cases. They are dead IRQ-local flags: unchanged11420→11374..11398 has no conditional consumer and restores saved SPSR. They are not claimed byte-identical at the callback return.

Twenty-one controls independently reject wrong queue-copy/substitution/priority, lost mode exit, omitted native bottom8 rows, enabled mosaic, retained stale IRQ, omitted slot52, altered source offset table, byte-width counters, wrong eighth match, cached second compare, wrong fallback/compare bridge, lost IRQ flags, adjacent writes, undeclared ROM changes, new inbound encodings and an erased-but-owned cave tail. Semantic controls invoke behavior checks without first rejecting a changed output hash.

Earlier B3F was rejected because it required zero-extended0000F000 and was dead for the real native constructor. Intermediate3C09 was withdrawn because mode8 can retain stage11/0400. Only18BB is approved.

| Artifact | SHA-256 |
|---|---|
| tools/verify_shoot_guarded_transition_irq.py | 1B83BC650DAFF3FCA643DC92789A610962910D11829C34BE690DFCEFF4600054 |
| build/shoot-guarded-transition-qa-20261109/report.json | 555554FDADF48C80F74DE2A9700B7ECD6FC798F859C151B6A4AC440A9C6925FB |
| records/shoot-guarded-transition-layout-20261109.json | 89EAB41CBDD9E8812C52D75029D4904B9C1FEBB2D1A981209E8389D4A0699B33 |
| build/shoot-guarded-transition-20261109/component-c.json | D405CA91E56AEB76ED8606CE6E46EB9B23D68FD3E3E3D0A10366580A61E3005C |

Verifier, report and ledger are LF. Git attributes explicitly preserve LF for the verifier and ledger; the frozen source builder's manifest remains its original CRLF. Three inherited QA primitive hashes are checked explicitly; no production builder is imported.

Reproduce from repository root:

~~~powershell
& 'C:/Users/김기호/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -u -X utf8 tools/verify_shoot_guarded_transition_irq.py build/shoot-guarded-transition-20261109/component-c.gba build/repro-v72-20261109-a/current-candidate.gba 'C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba' 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --manifest build/shoot-guarded-transition-20261109/component-c.json --layout records/shoot-guarded-transition-layout-20261109.json --output build/shoot-guarded-transition-qa-20261109/report.json
~~~

