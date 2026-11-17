# Source stage10 outer palette route — independent gate

Frozen 574F passes `tools/verify_iraira_outer_palette_route.py`, SHA-256 `05D6DE4A61AA5420A99A86E0400D91F56D6F6C5E23EFA394BC4C9B6839C354A1`. Report `build/iraira-outer-palette-independent-20261117/report.json` is `852F0EEF217C0EBF36C7FD08A462A92AD8FE6757710F4E2CD517376EAA3FDF60`.

The two changes are a60-byte helper atD8B640 and the4-byte call atD0BD0. All64 declared bytes invert to3CB7 exactly;63 bytes differ. The128-byte reservation has no conservative inbound references. The mode20 layer, inner palette route, original retail stage3 handler and common continuation are unchanged.

Source stage10's outer handler769361 calls only the shared palette dispatcher, whose stage10 target is783B90. The native repair intercepts actual physical stage10 before the old10→3 mapping, reaches the existing new projector, and resumes080D0BE8. For every other byte-valued stage and all16 entry flags,4080 cases preserve registers,CPSR,SP andLR. Only the16 bytes of retired helper stack may differ; this is not a claim of whole-memory equality.

The independent gate runs64 complete native outer invocations from captured RAM with all16 entry flags and normal/dimmed/two-suppression modes. It executes the real17758 queue copy, existing6FF600 guard, captured IWRAM IRQ code and native interrupt-enable routine through the outer return, without service summaries. Explicit synthetic IE/IME inputs supplement the capture, which does not include those registers. Final registers and flags agree with the original path; all live memory agrees except intended palette colors. Dead stack differences are bounded to84 bytes, derived from the unchanged outer7-register and guard14-register frames.

With the source-initialized hardware backdrop zero, the old route writes033D while the corrected route preserves zero. All38 palette colors match original source phases and dimming; suppression gates preserve colors and all palette gaps. The earlier0112 gate supplies exhaustive inner phase coverage. Actual corrected emulator observation remains a separate requirement.

```powershell
python tools/verify_iraira_outer_palette_route.py --before build/mode20-title-assets-v85-20261117/component.gba --after build/iraira-outer-palette-v86-20261117/component.gba --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --capture build/bizhawk-ai-iraira-v84-20261117-a --report build/iraira-outer-palette-independent-20261117/report.json
```

Use a fresh report path when reproducing the gate.

For normal source builds, use the new portable companion `tools/verify_iraira_outer_palette_route_portable.py` with the same before/after/source arguments and a fresh report path, omitting `--capture`. Its report `build/iraira-outer-palette-portable-independent-20261117/report.json` is `C095EBCB4238A058BA763C2C322E70EF59B0D0C348B19F6282AD3034A10C1C8B`. The portable gate keeps all4080 non10 and64 complete outer cases, but seeds explicit source10 owner values, a valid native task, one queued line7 callback and inactive fade state. The IRQ code and literal pool are copied from the built ROM's native C9008–C9074 into their real IWRAM destination. No prior emulator output or ignored file is required. Frozen852F and its checker remain unchanged as supplemental captured-state evidence.

The positive runtime observer's minimal delta passes `build/iraira-palette-positive-delta-independent-20261117/report.json`, SHA-256 `6CABF43520F0F9C0C2DB7D8092CED29DC30585C283401C46E4B131B0F9A61454`. Actual Lua execution verifies both nested ROM bindings and the single changed opcode. Seven host substitutions invert exactly; all prior pins, game actions and the121-clock stop remain unchanged. This preflight does not claim the positive live result.
