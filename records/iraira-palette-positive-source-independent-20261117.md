# Iraira corrected palette — actual original-source verification

Root's original positive session65800 completed with exit0 on frozen574F. The diagnostic stopped at core36476 after121 native clock samples. The loaded ROM and observer scripts matched their pins.

`tools/verify_iraira_palette_positive_source_capture.py`, SHA-256 `5042904ADB9717AE32F271921E54E0688A8297E4F4752C2C4F7D620B16CCCFF9`, produced `build/iraira-palette-positive-source-independent-20261117/report.json`, SHA-256 `83F38E0B356551799F8D8C908161DD346168F19ACD6E0D392329D572D4497781`, status `IRAIRA_PALETTE_ACTUAL_SOURCE_PASS`.

All121 samples have hardware palette0 equal to black and the RAM backdrop owner zero. The three watched animated group starts at offsets42,82 andC2 match their current phases directly decoded from original WSC data76AD13. Native clocks decrement once per consecutive core frame. The legacy stage3 branch, handler and gradient are absent throughout the scoped journal; the new palette front door and projector run during the active interval.

Five complete retained projector invocations, at cores36471–36475, enter with LR080D0BE8 and supply all38 source-exact color operands in order. For every store, the checker matches the observed valueR0, destinationR2 and already-advanced source pointerR1 to the original WSC phase row. Counter and suppression state stay consistent within each invocation. This directly verifies the restored outer caller reaches the intended producer.

The38-color proof concerns actual pre-store operands. Physical bus watches directly cover palette0 and starts42/82/C2; it does not claim38 separately watched physical destinations. This bounded witness is not another complete campaign or a mode20 runtime test. The earlier3FE5 complete campaign, separate AI proofs and intentional17-font-tile source match remain separately scoped evidence. No actual type8 event16 witness is inferred.

```powershell
python tools/verify_iraira_palette_positive_source_capture.py --capture build/bizhawk-iraira-palette-positive-v86-20261117-a --source 'C:/Users/김기호/Downloads/JUS/Digimon Tamers - Battle Spirit Ver 1.5.wsc' --report build/iraira-palette-positive-source-independent-20261117/report.json
```

Use a fresh report path when reproducing the check.
