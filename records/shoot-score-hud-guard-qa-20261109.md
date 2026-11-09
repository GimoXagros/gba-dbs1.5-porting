# Independent stage11 score HUD guard QA — 2026-11-09

PASS for the separate development component
`C8E810258B41A979A4DCE514119D8CAF139D615D63355F18F1C2E49AD72332F6`
over frozen experimental entry ROM
`D0A01A7FD0EE768A22BA4A1CC197FCB7B132E38BB52D1810093B571F4AE9DE7C`.
This fixes the narrow source score-HUD exclusion for stage11. It does not
approve full Shoot entry/ending, E5 resolution, main integration or release.
The independent reviewer did not run an emulator, open a save or edit the
author's files, first observation ROM, main builder or Git state.

The verifier imports only frozen independent ARM/scanner primitives, not the
production builder. It independently constructs the four-byte373ED8 branch
and16-byte6FF400 wrapper: CMP stage11, conditional return, retained CMP7,
then unconditional return to the original conditional return at373EDC.
Exactly20 bytes are declared and19 bytes change. Reversing these two spans
recovers the complete D0 ROM. The remaining HUD body, progression producer,
entry selector, IRQ/fatal layers and every other byte remain identical.

Ownership uses the pinned complete1394-interval/70-layer layout, original4MiB
extent, v73 IRQ reservations/hooks, fatal hook and the entire entry128-byte
reservation6FF380..400, including its erased tail. The new16-byte reservation
6FF400..410 is disjoint and fully erased. Conservative pointer scans at all
four byte alignments and08/0A/0C mirrors, ARM branch/literal/ADR and Thumb
literal/ADR/branch/conditional/BL/BLX scans find no inbound reference in the
predecessor. No data/interior exemption is used.

Actual source78769E..6AA skips stages7 and11 to the same register/flags restore
epilogue. The original native consumer skips7 only. The exact source/native
stage owners and source epilogue are pinned. An entire-ROM aligned direct
branch census finds only the three real BL callers373538/3735A4/37364C; an
all-alignment absolute-pointer search finds no HUD entry pointer.

All256 stage bytes ×16 incoming NZCV combinations execute the real patched
ARM prefix,4,096 cases. Stage11 returns with the retained prefix's exact
register/SP/LR state, reading only the actual stage byte: no actor pointer,
actor score, selection global, stack, BIOS service or VRAM access occurs.
For every non11 stage, registers, complete CPSR, ordered data reads and absence
of writes/calls exactly match the original at373EDC. The original stage7 return
and ordinary body routes then agree. The unchanged body is certified by this
exact entry-state join and whole-ROM identity, not by invented divider behavior.

The ARM-to-Thumb BIOS Div thunk bytes are pinned and unchanged. This verifier
does not execute the Thumb thunk, BIOS SWI or remaining score-rendering body,
and installs zero service models. The author's explicitly qualified BIOS
service checks are separate evidence; this PASS does not relabel them as
hardware execution or whole-body instruction execution.

Stage11 changes intermediate NZCV, so direct caller liveness is explicit.
The first two callers return unconditionally to the retained ordinary task
scheduler; actual11DD8..11DEC restores context and performs a full CMP before
any conditional use. The third caller performs its own full CMP at373658.
Forty-eight real linked stage11 caller executions pass. An additional variation
of all16 flags at each post-HUD return site confirms that these tails have no
incoming-NZCV dependency before those CMP instructions. This is scoped to the
positively bound ordinary scheduler callback ABI, not arbitrary foreign callers.

Thirty-three controls reject wrong source/stage predicates, removed/inverted
early return, missing/wrong CMP7 flags, wrong rejoin, off-target body/progress/
fatal/selector-tail writes, an adjacent cave write, every mirrored unaligned
pointer and the actual ARM/Thumb inbound encoding families. Predicate controls
execute semantic checks before expected-byte/hash validation.

| Frozen artifact | SHA-256 |
| --- | --- |
| `tools/verify_shoot_score_hud_guard.py` | `AB2B16EBFFEFD5617ED0C7275F64B459077548473AF545159FCED2618BBB0407` |
| `build/shoot-score-hud-guard-qa-20261109/final-report.json` | `23AF8303B25DBC560FE65D62D85A0AB408A4FA1C7BEBF9D5E05BB6CEE6EEE3BF` |
| Source builder | `7D5C647547E4FECD6707A0B8AB6411B6A0FC3233442B04465820F27823634B32` |
| Component manifest | `BD1DF6DC17B0E3474F969CA617031B3BEB56FCF6CB300209A12976F28CBD4DAD` |

Reproduce to a fresh report path from the repository root:

~~~powershell
python -u -X utf8 tools/verify_shoot_score_hud_guard.py build/shoot-score-hud-guard-20261109/component.gba build/shoot-runtime-entry-probe-20261109/experimental.gba 'C:/Users/김기호/Downloads/JUS/Digimon - Battle Spirit (USA).gba' 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --manifest build/shoot-score-hud-guard-20261109/component.json --output build/shoot-score-hud-guard-qa-20261109/new-report.json
~~~

The first report was retained after adding further explicit Thumb scanner
controls; `final-report.json` is the frozen complete33-control result. No
unchanged legacy suite, emulator trajectory or original-game fight was rerun.
