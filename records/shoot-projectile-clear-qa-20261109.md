# Independent bounded93E7 selector QA

The isolated93E7-only extension passes independent actual emitted ARM verification. Relative to exact v71 `35D46BB3`, candidate `025C1C5E` adds only the76-byte selector6FF240..6FF28C and changes dispatcher pointer12C50. Existing static-companion capture, renderer, owner lookup and preload expiration bytes remain exact.

Approval is conditional on the already-proved normal43-lower/775-upper/790-borrowed source callback graph and exclusive ordinary scene/task ownership. It does not authorize external Shoot entry, arbitrary callback/scheduler states, side1 companion alias rendering or a complete terminal clear.

## Frozen identities

| Item | SHA256 |
| --- | --- |
| v71 input | `35D46BB3901C8C564A452432A8B2B90F44485B176526226CE6B7DA54A0A36A8A` |
| New component, `build/shoot-projectile-clear-explicit-20261109/component.gba` | `025C1C5EACC7E7A66873C06BA044EE8ECE8C2DBA2C14971365921F1C691732DA` |
| Independent verifier, `tools/verify_shoot_projectile_clear.py` | `21379A50F4C14C174D13E9DB7FFE02719914C867D39871A6DA43E988E283689D` |
| Report, `build/shoot-projectile-clear-qa-20261109/audit.json` | `95458CCEBEBDBCD5BE5D2CE703D32490F106629BE58DDEAAC280203DA0830C38` |
| Original source | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |
| Conditional no-reload proof | `2E96EEEBA7E42ECCB464F6E7AB8FFE80A7CC6D5BF490A39EF16591A7C84C8990` |
| Explicit lower-graph artifact | `37BAFE3EE49314F58024BD322DA1DEC33C8A7316DA0984242985FA4262DF5281` |

The verifier/report use LF. No production builder or converter is imported. The independent ARM primitives are the unchanged v71 verifier `CD2E7B85`, attack interpreter `695ECA1D` and scanner/interpreter `7CDD6E52`. The independent inverse-pixel reader is `872AE459`; the explicit-path no-reload analyzer is `CCCAC31E`. Their complete hashes are recorded in the report.

## Source and conditional upload lifetime

The verifier checks the original93E7 constructor/base6D and explicit pre-clear standalone226E preload, static event/frame/update upload gates and the event selection that changes only priority2000. The actual native constructor resolves P0 `085DB300`, tile base6D and static P1 header flags0. It compares all eight native layouts directly with source P0 raw3D44E0, and inversely decodes all768 native pixel bytes into the original source's24 four-plane tiles. No generated manifest supplies expected pixels.

The caller must supply both the no-reload report and lower graph explicitly. The report and graph hashes are checked; `analyze_shoot_p2_reload_eligibility.proof(original_source, explicit_lower_graph_path)` is recomputed and must equal the complete frozen2E96 proof, excluding only its already-recorded negative-control label list.

The source conclusion remains bounded: retained kind3 SECOND cannot run generic form completion through the checked normal/borrowed graph, FIRST reconstruction usesbase49, and the separate introduction reload owner retires before ordinary battle. Consequently the earlier93E7 preload remains the relevant pixel owner within those contracts; new static93E7 children and frame changes do not restore cleared pixels. No child-quiescence assumption is introduced.

The report keeps `full_post_clear_reload_exclusion_approved=false`, `external_entry_authorized=false` and `complete_terminal_clear=false`. The existing source4090:8F24 nonpattern0A80/EB4C/E59A domain remains excluded. Negative controls reject changing the conditional proof to unrestricted approval or omitting that external gate.

## Actual instruction execution

| Check | Cases |
| --- | ---: |
| Selector/real-owner/stack edges |456|
| Full93E7 dynamic renderer |3,669|
| Existing companion and unrelated fallback parity |460|
| Total |4,585|
| Rejected negative controls |19|

Selector edges cover all28 captured first-tile values74..128 and all16 live-bit states, using the actual owner scanner with the owner in native slot52. Recognized paths save R9 exactly once, preserve R5 and unsavedR6/R7, obtain the actual mask, translate nonzero masks by36 and enter086FEA50 at the expected stack depth. Zero masks, inactive/missing owners and unrecognized phases remainzero. Wrong base, indexed flag2,888B and an interior P0 identity tail directly into086FEA00 without an extra push.

The full renderer sweep executes08012C28 through the real selector, real owner lookup and retained renderer epilogue for all8 layouts ×28 clear positions ×16 live-bit combinations. Expected blank pixels use the independent direct predicate `109 + original_layout_tile - captured_first` and the original individual live bit. The sweep observes512 blanked sprite parts. Additional cases cover zero/inactive owners, clipping, saturation, indexed fallback, all facing combinations, priority flags and nonzero native tile-count starts.

Every full93E7 comparison checks the complete4,096-byte staging buffer, complete1,024-byte OAM staging buffer, dynamic tile count, original R0..R5/SP/LR return contract and the complete non-stack write address/size sequence. Only the selected pixel values may change. No task, mask, queue or persistent RAM write is added by the selector.

Fallback comparisons execute every one of the30 existing companion resources'219 layouts with both zero and active masks. They require exact v71 staging, OAM, flags and registers, except documented dispatcher-scratch R9. All18 excluded888B layouts and ordinary ID1/ID14 presentations retain their pixels. Both flag1 BG dispatch variants are executed through the unchanged dispatcher prefix and must reach08012DCC without entering the selector; the background DMA body itself is not executed here.

R9 is intentionally dispatcher scratch. Its saved/restored value becomes the new selector address086FF240 rather than old086FEA00. The proof requires the correct single save and retained epilogue, not equality of that scratch address with the old ROM.

## Ownership and independent rejection tests

The predecessor's entire76-byte reservation must beFF. The unchanged conservative scanner examines the complete predecessor ROM for unaligned/mirrored pointers and ARM/Thumb candidates into precisely6FF240..6FF28C, without data/interior exemptions. Local negative fixtures independently exercise mirrored unaligned pointer, ARM branch and Thumb branch detection.

An exact full-ROM inverse restores only the76-byte selector and four-byte dispatcher pointer, recovering the complete v71 predecessor. Mutations outside the span, immediately at its end, inside the retained renderer, at the retained preload hook or inside the retained zero tile are rejected.

Actual instruction controls reject wrong base6D, wrong indexed bit, wrong P0 literal, omitted R9 save, omitted real owner lookup, unconditional subtraction corrupting a zero mask, subtraction by35 and a wrong body continuation. A source-code mutation that changes the static event-upload gate is also rejected independently of input hashes. Together with the scope and inbound controls above,19 negatives pass.

## Reproduction and limits

Use the pinned Python runtime from the repository:

```text
python tools/verify_shoot_projectile_clear.py <exact-v71.gba> <candidate.gba> <original-C415.wsc> <distinct-output.json> --source-proof <explicit-2E96-proof.json> --lower-graph <explicit-37BA-graph.json>
```

The completed run used `build/repro-v71-20261109-a/current-candidate.gba`, `build/shoot-projectile-clear-explicit-20261109/component.gba`, `build/shoot-p2-reload-eligibility-20261109/final-proof.json` and `build/shoot-projectile-clear-explicit-20261109/lower-graph.json`.

This is bounded independent execution of actual ROM instructions, not an actual Shoot gameplay observation or a hardware/performance test. No emulator, supplied save/state, guest-memory write, main builder, frozen v71 implementation or Git state was changed by this QA task. Root owns subsequent full builds and hidden ordinary-result runtime regression.

## Independent completed v72 ordinary-result regression

After root confirmed launch exit0, `build/bizhawk-result-v72-20261109-a` passes frozen result-capture verifier `507D7A372E4519B5D41A460E9F1B800C600771A1C69F4C64B60AF70813F1D738`. The actual loaded8MB ROM and probe file equal025C from full buildA. The final private-desktop launch inventory validates all61 files, eight full snapshot sets,1,508 visible Korean WIN pixels and five negative selfchecks. The observer remains exact928186AE, and the copied native renderer remains exactD18F2900.

| Runtime artifact | SHA256 |
| --- | --- |
| `build/result-v72-runtime-qa-20261109/audit_capture.py` | `54BCA5287E4223940FFDA5A38EEC4DA316A71AC4E929B45AA970D34D1DC03C3E` |
| `build/result-v72-runtime-qa-20261109/ko-audit.json` | `62FE91FAE6245EA2F28DBD419D12E0AA70ED62CA65B5EEED37C6E75A0534BDB6` |
| `build/result-v72-runtime-qa-20261109/v71-comparison.json` | `5EAC3A7B4DDC3554897212DD6E3223BFFBBC28FCCC2818D6AFA77A6D1DC1A476` |
| Completed launch | `2D165FC08D0B96C5B364CEAD939DC70B6B320B9FF25C6E48D50D6FA83AF72B79` |
| Complete actual trace | `9FC08B1C1A21E071AEDF1014F2EAED39D73EE28874BB3B3F89C960FD3B77CA1E` |

The new script and reports use LF. Reproduction is the pinned Python runtime followed by `build/result-v72-runtime-qa-20261109/audit_capture.py`, from the repository. The comparison uses already-accepted v71 report23F56022 and rehashes every reused v71 artifact against its frozen launch inventory; it does not rerun the previous v71 verifier/emulator or repeat the v70 investigation.

The **complete trace is byte-identical to v71**, including every actual input edge, mode/stage row, initializer/draw callback, resource identity, frame number and final summary. Both captures show Options staged at core3458, committed3559, battle entry3999, result entry11519, first label11776 and result+300 at11819. Every typed timing pair has delta0; no frame value was normalized or omitted.

All eight screenshot files and every complete EWRAM/VRAM/palette/OAM snapshot buffer are byte-identical to v71. These equalities are asserted by the new audit. The natural WIN label remains event0/layout0,30 parts,1,508 pixels, palette bank2,105 active OAM entries and the exact retained winner-side palette. Both reports count one native language writer, seven initializer calls and88 draw calls with two unique draw rows.

The remaining raw differences are retained explicitly rather than treated as whole-RAM equality. Options-staged IWRAM7E58 and title-committed7EAC contain dispatcher-scratch address086FF240 instead of086FEA00, matching the new selector target. First-label IWRAM7F9C differs08→04; no producer claim is made for that stack byte. The first-label display-register dump differs in36 bytes, while the other seven display dumps are exact. Both corresponding screenshots and full render buffers are exact. A boundary register dump is not a scanline trace.

This establishes bounded ordinary Korean Options commit → title → natural battle → WIN and+300 display regression through the new global selector route. It does not observe an active93E7 terminal mask, actual Shoot entry, LAST CHANCE/DRAW, complete campaign, E5 resolution, fresh-process language persistence, hardware behavior or general performance parity. No additional emulator was launched and no capture/observer, supplied save/state, guest memory or frozen component verifier was changed by this independent runtime audit.
