# Authorized original P1 score999: independent composition review

The frozen original-only score module, DI observer, driver and launcher have no remaining prelaunch blocker. The independent actual-Lua composition passes without launching an emulator or reading a save. This is permission-scoped development observation; the final GBA remains cheat-free.

| Item | SHA256 |
| --- | --- |
| Actual-module composition audit | `0618B374551F953BD939489955523386BECDAED23389E56DDC784778D0440CF8` |
| Rerunnable `build/wsc-score999-independent-qa-20261109/audit.py` | `703D1E972538B7A8CB52DF1F4A83263C920EDEE27DBD84A8946D724DCAC0C074` |
| Driver | `A0ACBDA61D4CC5629637E385E5F8697C7FA4B682AE6D35505C28B83A0ABA287E` |
| Score module | `F94DA2687D8445F4464F68B427B7088A00FC296E4B56D618BABA596B864EB8F8` |
| DI observer | `BD01DF5A399D5D33B9859BBC484F0068B6E6406EFCD7DAAD07AB7AF38DD0E15B` |
| Launcher | `19AC4B67C9AB2AEA5CB4C3788FEA09F76DD4F07BD3ECF397BDDFA113453F0057` |
| Explicit three-module reviewed-pins JSON | `35B8483A4C93527A0D48888F680CD598364C5F0DEE6385EA31ED9EFEE346BDB1` |

The new audit/script use LF. Reproduce with the pinned Python runtime and `build/wsc-score999-independent-qa-20261109/audit.py`, from the repository.

The author source/module proof `CA7006BA` already covers66 guard cases and ten negatives. It establishes score WORD actor+52, ordinary single-player eligibility, the post-award/pre-HUD/pre-timeout hook, source pickup cap250, HUD limit999 and result export AL231. The separate driver proof covers19 synthetic policy routes with doubled module interfaces. Those suites and the earlier65,536-value DI suite were not rerun here.

The distinct test executes the **actual driver, actual score module and actual DI module together**, plus all five frozen Lua composition layers. Only the final expanded gameplay-policy body is replaced with a controlled scenario. Seven cases cover successful paired-DI completion, bounded completion, pair-only, terminal-only, pending pair, wrong boot data and the wrong save-userdata key. Four mutations reject an HP write, value998, a false successful completion marker and omitted score finalization.

The real score callback performs exactly one two-byte write to validated P1+52 with value999, skips a second write while already999, and makes no write at stage7 or11. A full64K synthetic RAM comparison preserves every other byte, including HP, adjacent fields and P2 score. Both real modules finalize before the driver writes its completion marker; finished score callbacks are inert. Legacy collector operand-owner hooks are removed, leaving their inaccurate old `diA` expression outside the executed composition. The new driver has no RAM/register/savestate write API.

The launcher independently matches the three explicit reviewed module pins, five frozen policy hashes and pinned emulator/core. It uses exact originalC415, an isolated authorized-save-copy wrapper, fresh output, disabled autoload/background physical input,120,000 frames and a1,500-second host bound. Its stop request is scoped to the run. Reviewed pin-file and launcher bytes are checked before/after execution; intentional partial runs retain honest status.

One draft mismatch was corrected before launch: the host initially passed `supplied_copy_sha256`, while the driver requires `save_copy_sha256`. The current launcher uses the correct key. The actual-Lua wrong-key case fails before module enablement or input, and the boot equality guard similarly checks the full32K expected source-startup image before enabling anything.

No HP, stage, register, progress, source ROM, save file or GBA implementation is changed by the cheat module. Native award/result behavior remains unchanged: transient pickup clamping may reduce the score to250 before the next guarded callback restores999, and999 exports low byte231. This is documented source behavior, not authorization to patch extra fields.

This review does not claim an actual campaign result, HUD screenshot, source Shoot entry or observed final IRQ. Root owns the separately running hidden observation; completed capture evidence requires a later independent audit. A score counter write and a visible HUD update may occur on different captured frames.
