# AI producer observer independent review — 2026-11-17

Independent delta preflight passed for observer `4A2AE9672BAF2C1BC53EE3B8A6F891DCB66B7EE77C0163966CA2F123F15C4C30` on frozen ROM `75BD7C17D32CC7567815FFFF42EFE383696E7317BFF34E09437C28DFDB99F32F`. This is instrumentation evidence; actual first-writer provenance remains a separate runtime result.

`tools/check_ai_producer_delta_independent.py` (`044E9ECC24667F690C05651723DE3703D9B38FA0D45CD8CD2DF716B464B04512`) produced `build/ai-producer-delta-independent-20261117/report.json` (`F6491ADA5182D17032235C40ACCC2A6E723E3E834FEC6860336E053B50069F19`). The test executes the new wrapper using Lua 5.4, checks its exact one-edit composition over frozen corrected observer 844C and the exact two insertions into frozen campaign F393, and validates eight native execution opcodes plus the selector write watch. It deliberately supplies stage 9 / CPU 14 / progress 2 before active actor pointers exist, preserving initialization evidence. Across 151 modeled events, six initial facts survive a 128-row ring rollover. A valid target continues; invalid index 15 is reported before BX without changing R9. No new guest write or input operation is present.

Host `build/run_ai_provenance_v82_20261117.py` has SHA-256 `BBB6960EB4C55A927946F190399BFD947695B64A830BA3C149769BC653531FC3`. Independently reversing the six declared edit groups reproduces the prior host bytes (`18DDDFCFE48DD615B6F64A2B46755D270831428FE951B72A2859CCB747366864`) exactly. Pin file `build/ai-provenance-reviewed-pins-20261117.json` is `C994BC261745B10FCA9B156BA70C43254E95A9AD1572CC351BEFED3E17B421A3`: all prior pins remain equal and only the new observer is added. ROM, frame budget, input sequence, and authorized write guards therefore retain the previous host behavior. The expected terminal result changes to the first invalid AI target observation.

## Native facts and causal limits

The initializer reads CPU identity at 080C6D60 and multiplies the effective identity by 17 at 080C6D70. Its native parameter table 080C6C7C has eight rows. Raw identity 14 therefore addresses 080C6D6A, inside ARM instructions. Copies target the 0x26-byte AI owner at 03004D88. Source identity normalization and source ten-row data are independently being reconstructed by the source author.

The normalized identity is also pushed and later multiplied by 384 into AI owner +0A. The behavior reader at 080C64D8–080C64E8 adds that value to its local index and reads the table addressed by literal 080C658C (080C3FC0). That native table has eight 384-byte rows. Completing only the 17-byte parameter view would leave this downstream reader outside its table for new normalized identities 8 and 9.

The native 18-byte action table at 080C4FC4 has seven aligned literal readers, including interior aliases: 080C6A2C (+0E), 080C6A3C (+0), 080C6B2C (+0), 080C6B34 (+0), 080C6BB4 (+10), 080C6BB8 (+11), and 080C6BBC (+10). The initial and continuation readers copy nine halfwords; the byte reader dispatches through action fields +10/+11. A relocated complete view must retain those offsets.

The dispatch table at 080C65F4 contains twelve callbacks, followed by three RAM literals. Index 15 reads opcode E3A00000 at 080C6630 as a target. This agrees with the preceding finalized capture's undefined-mode LR E3A00004. It does **not** by itself prove that the invalid parameter read produced selector 15. The new read-only write watch and actual runtime chain must establish the selector's producer; no clamp, extra dispatch state, or causal assertion follows from this preflight.

No emulator, production ROM, main build, or Git operation was performed by this review. Full campaign completion and actual repaired-path evidence are outside this report.

## Finalized actual first-writer capture

Root's run `build/bizhawk-ai-provenance-v82-20261117-a` completed with its expected first-invalid-target result. Independent checker `tools/verify_ai_producer_capture_independent.py` produced `build/ai-producer-capture-independent-20261117/report.json`, SHA-256 `3B0BDBEE266450836A3C285A2E3F58B134E509AA8C6BDBBF7A0E38FA70C7B8DA`.

The actual 32-event journal observes raw/effective identity 14, the ARM-code parameter row at 080C6D6A, and all fifteen copied parameter fields at core 19961. At core 20165 the first selector value 000F is written by the native halfword copier: reported PC 080110EC, LR 080C69B8, offset 0011FFEE (FFFF × 18), destination 03003D50, source register 081E4FB4 after the first halfword postincrement. All eighteen destination bytes exactly match ROM 081E4FB2. The next recorded dispatch reads E3A00000 from slot 080C6630 and presents it at the BX boundary. Thus the selector is demonstrably produced by the out-of-range action copy.

The snapshot retains AI behavior offset 1500 (14 × 384). Applying the native selector instructions to its captured distances, thresholds, RNG, difficulty and actor flags reconstructs behavior address 080C554A, whose halfword is FFFF. This lookup address is a reconstruction from captured owners, **not a directly hooked observation**. The invalid ordinal's subsequent multiply and copy are directly recorded. Both parameter and behavior offsets derive from the same unnormalized identity; the evidence does not attribute the branch to one particular corrupted threshold.

All 1,920 source behavior cells are within action indices 0–262; all 264 source continuation fields remain below 264. The source low-state population is exactly 0, 1, 2, 3, 5, 6, 7, 8, 9 and 10, excluding 15. These facts support correcting source identity and data domains while retaining the existing dispatch implementation.

## Corrected observer delta

`tools/check_ai_corrected_delta_independent.py` produced `build/ai-corrected-delta-independent-20261117/report.json`, SHA-256 `12F002F22FA470582CBA27EAEC3259A0F8481B23D4007C6AD9584B8D3D27A1F9`. It executes the actual corrected wrapper `45490F604352C49539A73E54A9F7AE9FF1A2DDDDA8508A1C4BA28372B45085A4`, checking exactly five changes over the frozen 4A2 observer: the ROM pin, nested corrected-ROM binding, first selector-load retention, first target retention and one bounded first action-copy fact. Hook opcodes, invalid-target guards, input and guest-write paths remain unchanged. The nested 844C binding propagates DEEE to the frozen campaign; repeated adaptation fails closed.

The corrected host `F1397304FFEF2CEAAACC4DECEE774CE442A5317FAF101BA0A56F0B70C110706D` reverses exactly through eight declared substitutions to the frozen BBB host. Pins `D7A7625DBEFBD84ACDE7C15F6AE41AF8557659A5A0CE862542943DB873660D7A` retain all prior files and add only the corrected wrapper. The expected terminal result is restored to strict complete-campaign success. This delta check is not repaired-runtime evidence.
