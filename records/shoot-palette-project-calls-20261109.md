# Terminal palette-call stall and isolated repair

The completed `bizhawk-gba-shoot-terminal-20261109-a` run reached the genuine fatal hit and terminal scene, but did not complete. The first terminal blink set `03004529=7`. Its scene timer then remained 120 and the scene/FIRST/SECOND/auxiliary task slots were unchanged from core69016 through71927. This is not evidence that their callbacks need forced timers or scheduler bypasses.

Independent saved-CPU inspection found PC/LR `085C6F50`, SP `03007E94`, in the palette projector. Actual ROM calls at `5C6F4C`, `5C6F5C`, `5C6F88`, and `5C6FBC` all contain `1BFFFFFE`: each conditional BL targets itself. The first nonzero blink takes the first loop, preventing the next game update while hardware frames continue. The first call's captured tuple is R0=001B, R2=3, R4=08586812, R5=03003D30, R6=739C, R7=7, R8=05000010. Executing the original fragment reproduces the self-loop and LR=085C6F50. The pre-existing auxiliary-link IRQ guard has not been reached; it is not this observed stall's cause.

The frozen `build_shoot_graphics_initializer.py::palette_project()` intends all four calls to reach its local `dim` helper at `085C6FD4`. Regenerating that function reproduces the complete current 268-byte hash `A5BF5D31A6DD7679945E0EBAB3059B09FC2A91F16422C5C8BC3AE9B6FA47E6E3`, including the bad calls. A minimal reproduction in the vendored assembler is `blne dim; bx lr; dim: bx lr`: it emits `FEFFFF1B`. The corresponding unconditional `bl dim` and `bne dim` resolve to the label; numeric `blne 0x085C6FD4` at `085C6F4C` emits the correct `2000001B`. This establishes the local conditional-call label encoding failure, without asserting a diagnosis of the assembler's internal implementation. The old structural/hash verifier did not execute this dimmed path. A bounded scan of all ten published graphics function bodies finds precisely these four self-targeting BL instructions; these are also every BL in the projector.

Source WSC1.5 `783C9E..783EAF` (SHA `BFF39248475A90CEFFBCC5FC52D8E3940EE9F9FADB951D68F6005FC1FDD156A1`) selects normal output when CX=0, otherwise halves each RGB444 channel. Its 19 selected colors (6+8+5) produce 35 palette stores (6+24+5). The existing native helper implements that same operation after native RGB555 conversion, using mask739C and nonzero-channel low bits; the earlier complete4096-color proof is reused. The full native frame preserves r0-r12/LR and SP; the helper changes only r0/flags. The existing call-site comparisons, loop counters, 32-byte palette state owner, destination cells, and stage dispatch remain unchanged.

New `tools/build_shoot_palette_dim_calls.py` encodes checked PC+8-relative BLNE words directly, after exact predecessor/source/dependency/projector pins. It preserves the historical generators and applies only:

| ROM offset | Old word | New word | Target |
|---|---|---|---|
| 5C6F4C | 1BFFFFFE | 1B000020 | 085C6FD4 |
| 5C6F5C | 1BFFFFFE | 1B00001C | 085C6FD4 |
| 5C6F88 | 1BFFFFFE | 1B000011 | 085C6FD4 |
| 5C6FBC | 1BFFFFFE | 1B000004 | 085C6FD4 |

There are 16 declared bytes, 12 changed bytes, no allocation/cave/RAM changes, and an exact whole-ROM inverse to1477. Future use of this final component cannot silently retain the four bad encodings: it validates every replacement's condition/link bits and local target, plus the final output hash. Production `build(before, source)` reads no capture or ignored historical manifest. Optional author checks consume explicitly named completed RAM fixtures separately.

Frozen output `build/shoot-palette-project-calls-20261109/component.gba`: `FF3A9D54F74225E77B36EAF156589169D49FAC71A81DA511754CA7FE8E3590A8`.

Builder SHA: `66E70D72AB1401A526ADB16A560FB0EFB18E42BE2F56B3A411358DEB1FB6BE91`.
Manifest SHA: `6E44701A7465E6CEBDD5E8C0B4ADA1EE48C398EA8DF2EF804530076EF3D0C310`.
Author report SHA: `2CCE16AA1259D5B48B69DC147922E5B545EA689EC26F9F063ADA214265B34B3F`.

Author checks passed80 actual ARM interpreter executions across16 entry-NZCV values, blink0/1/7 and both existing early-return gates; 11 nonstage11 original joins; a completed-capture palette-state execution; the original self-loop counterexample; and four malformed replacement refusals. Checks cover exact ordered35 writes, all other palette bytes, state32, registers/SP/LR and helper call population. No BIOS/service models or emulator replay were used. Independent QA owns the captured real stack/caller proof and its own execution cases. This repair is not a claim of completed native ending, mode8, or subsequent IRQ-guard acceptance; those still require root's controlled runtime trial.
