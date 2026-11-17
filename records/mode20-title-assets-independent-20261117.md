# Native mode20 title assets — independent review, 2026-11-17

The isolated 3FE5 → 3CB7 change passes `tools/verify_mode20_title_assets.py`, SHA-256 `115720219E185AE284EF999EA747A94F79AA8A48DACE09585CBD093A2BD7EC03`. The frozen report is `build/mode20-title-independent-20261117/report.json`, SHA-256 `94DCC785AD5CF8305F4B0B95143E82AC82C9DE46D123FDF659FCC1F63BAB10F2`.

The four spans declare 60 bytes and change 58. Full-image inversion restores 3FE5; the new D8B400–D8B440 reservation is blank with no conservative incoming references. Existing Iraira writes and all shared title assets remain byte-identical. Source anchors independently bind the fixed Japanese branch to the existing title assets, including 504 map cells and 96 source palette colors.

Across all 16 NZCV states, the checker executes the actual native 08000B84 DMA routine and the complete mode20 continuation. DMA hardware transfers are modeled explicitly. The helper copies the two existing title tile segments to 06003200–06006500, within the old mode20 extent ending 06007200. Palette destination 05000020 and map destination 0600F800 remain unchanged. The final registers, flags, stack, callback and task-flag effects match the original continuation.

This is a static native-consumer result. It does not claim an emulator observation, repeat the earlier full title pixel audit, fix source/native timing differences, or implement mode23. The independent Iraira runtime palette mismatch discovered after the successful campaign remains a separate open issue.

```powershell
python tools/verify_mode20_title_assets.py --before build/iraira-render-repair-v84-20261117/component.gba --after build/mode20-title-assets-v85-20261117/component.gba --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --owner build/iraira-render-repair-v84-20261117/component.json --report build/mode20-title-independent-20261117/report.json
```

The report path must be fresh when reproducing this command.
