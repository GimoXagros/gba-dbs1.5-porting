# Character AI tables independent verification — 2026-11-17

**Runtime qualification:** the finalized DEEE run exposed an ARM7 odd-address halfword behavior omitted by the bounded interpreter. The static source-field execution claim below does not establish hardware source parity for odd parameter rows. Frozen report B1B21 remains historical evidence of the image, allocation and modeled checks, with this limitation; it must not be treated as an unqualified fifteen-field source-parity gate.

The isolated DEEE correction passes the independent gate. `tools/verify_character_ai_tables.py` SHA-256 is `2A7FA8725CCF3BDD396060AA6A78DD83D9A22370618990DC1D1937A65C5237A1`. Its frozen report is `build/character-ai-independent-final-20261117/report.json`, SHA-256 `B1B21A1C119028B2EBD70602BCCB82F6580CF02A38932E69EB58187A7B885FC7`.

The verifier reconstructs the entire corrected image from immutable 75BD and the source ROMs, without importing the production builder. It checks the ten 17-byte parameter rows, ten 384-byte behavior blocks, 264 action records, normalization before the saved identity, fifteen parameter references, the sole behavior reference and all seven action references including their interior offsets. The exact result is `DEEE43414D5145CCA6B9B857013B401D228C1535BA9FA8EF58FD9D7F13ADCD98`: 28 spans, 8,890 declared bytes, 8,128 changed bytes. Reversing those changes yields the complete prior image. All 113 writes in six pinned prior-owner manifests remain unchanged.

The whole new reservation D88800–D8AB00 is blank in the input and has no incoming references under the existing conservative scanner, without exemptions. It is disjoint from the six checked owners and their reservations. Padding remains FF, and no RAM is allocated.

Actual ARM execution under the independent bounded interpreter covers:

- 176 helper cases across all sixteen NZCV combinations for the eleven normal CPU identities.
- All fifteen copied parameter fields and the saved behavior offset for each identity.
- 429 full initializer cases over three difficulties and thirteen progress values; 351 retained-identity cases have equal complete register, flags and memory state.
- All 1,920 behavior cells through the actual native halfword reader.
- 528 actual nine-halfword action copies through both initial and continuation readers.
- All 264 interior-byte reader cases, including zero-kind bypass and value/kind ordering.

The source low-state set remains 0, 1, 2, 3, 5, 6, 7, 8, 9 and 10. Every behavior index is below 264, as is every continuation index. The existing dispatch table is preserved.

The ordinary CPU domain is 0–7, 11, 13 and 14. Identity 11 maps to 7, while 13 and 14 map to 8 and 9. The verifier separately checks the source and native stage-7 mode selection and native dedicated boss constructor branch: it skips the ordinary AI initializer. This is not a general invalid-input clamp or a claim that every raw byte is a playable identity.

The one retained commercial exception is action 42, field +0C: native 007E is preserved although both source versions contain FF7E. Native 080C67F0 reads the complete halfword; 080C6820 uses it to AND the actor input word at +2C. Therefore this exception is semantically meaningful and remains an explicit source-parity limit. No generic mask conversion is inferred.

The actual old-ROM writer evidence is separately frozen in `records/ai-producer-observer-independent-20261117.md` and report `3B0BDBEE`. That capture directly observes the invalid action copy and target, while the earlier behavior lookup is labeled as a reconstruction from captured owners. No repaired emulator run or complete campaign success is claimed here.

## CLI contract

Run `python tools/verify_character_ai_tables.py` with `--before` pointing to the saved 75BD type8 component, `--after` to the resulting DEEE image, `--source` to WSC 1.5, `--old` to WSC 1.0, `--gba` to the retail GBA, and `--report` to a fresh path. `--owners` takes six manifests in this order: evolution music, evolution transition, ID13 air relaunch, campaign stage progression, campaign progress consumers, and the saved type8 table component. The source paths are read-only. No emulator, main builder or Git operation is performed by this verifier.

## Actual corrected prefix and newly exposed parameter discrepancy

Root's original session 97662 completed with exit 0; its full guarded route reached healthy Shoot at core 89405. The separate campaign QA owns that outcome. The scoped independent validator produced `build/ai-corrected-capture-independent-20261117/report.json`, SHA-256 `D469F3BA5D11B8E2F68A19AD3DBD8B4AFBF131F99179B453FC5A92109B434AC5`, status `AI_CORRECTED_ACTION_PREFIX_PASS_WITH_PARAMETER_MISMATCH`.

At core 19961 the real CPU normalizes identity 14 to 9 and addresses source-shaped row 08D88899. The observer's byte-based read sees source halfword 02E4. The native odd-address LDRH instead produces R0=0F0000E4 from aligned halfword E40F, and its store writes 00E4 to 03004D8A. The complete copied buffer confirms this difference. Fourteen of fifteen parameter fields match the source row; the first does not. The bounded interpreter had read an unaligned halfword as adjacent bytes and therefore missed this hardware behavior. Retained odd rows also contain first halfwords 0250/02E4, so this behavior predates the extended table and needs an explicit source-versus-commercial decision.

The corrected downstream path is directly witnessed: at core 20199 the saved behavior bank is 0D80 (9 × 384), the native copier selects action 00CC from relocated address 08D8A658, and its eighteen source bytes and first state 0008 agree with the corrected action table. The first dispatch loads slot 080C6614 and branches to its valid native target 080C6630. This resolves the prior out-of-range action-copy chain in the observed prefix. It does not erase the newly measured parameter discrepancy or establish type8 event16 execution.
