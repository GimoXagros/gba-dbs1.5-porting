# v73 independent runtime QA — 2026-11-09

PASS for the completed private-desktop ordinary Korean Options save→title→battle→WIN observation of exact v73 ROM6A1A. Root's run exited0 and normally finalized its launch report. This is an ordinary-result regression observation, not active Shoot or whole-port completion.

The frozen runtime verifier989EA9640E4CB7AF35F73A9FAC6BFC73093EEF92F31CBB4BB8CDA9BC517235FE adds exactly14 source lines. Removing those two new inverse cases reconstructs the entire previously frozen507D7A372E4519B5D41A460E9F1B800C600771A1C69F4C64B60AF70813F1D738 verifier byte-for-byte. Direct whole-ROM inversion confirms final6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7 fatal hook→guarded18BB→exact v72 025C.

The actual new audit function accepts both final6A1A and guarded18BB through all inverse gates up to a blocked launch-file read. Eight corruptions—fatal hook, late queue hook, adapter, guard, IRQ, undeclared gap, outside byte and ROM length—fail before any capture I/O. No capture, emulator or original save was opened, and no prior renderer/hardware corpus was repeated.

Frozen launcherB0DED582D07658950E0E8F27B0EC048E54074E09E11E40C2BEB30EB0AA2C1FCA is byte-exactly the prior v72 launcher44B7F0BAD732C1264923DDC6A24D3B493170617D4B36CF73E0AF298203B87DCF after v73 names, the exact6A1A ROM pin and SoundOutputMethod3. SoundEnabledFalse, private desktop, isolated paths and disabled autoload/autosave remain intact.

Preflight checker build/result-v73-inverse-qa-20261109/preflight.py:
C333AA72D349BAD1138CE292B313C459E93549D2F5ECBFEBDB69778569389A7E.
LF report preflight.json:
40ECAB2D918186B3A7F22AB08C7B275CE21C4D6A928F929111CA85B8F03102EB.

The completed capture is build/bizhawk-result-v73-20261109-a. Full frozen989EA audit verifies62 inventoried files, eight snapshots, the exact loaded ROM, unchanged observer, private input isolation and Dummy3/SoundEnabledFalse. The one added filename relative to v72 is config.saving.json. The ordinary run has no observer guest writes; no emulator was launched by this auditor and no original save was read.

The complete trace is byte-identical to v72. Every core/relative timing comparison is exactly equal, including eight capture cores3458/3559/3560/3999/11519/11639/11776/11819. The typed populations are47 inputs,11 mode rows,8 stage rows,1 native writer entry,2 unique draw rows,7 initializers and1 summary. Initializer values observed before full object initialization remain outside the compared semantic identity fields.

All eight PNGs and complete EWRAM/VRAM/palette/OAM/display buffers are byte-identical to v72. The only raw IWRAM differences are8 bytes at result-enter and7 bytes at each subsequent result snapshot:7E10..12 and7E14..17, plus7F9C at result-enter. The aligned words change7E10:0804087C→0801140C,7E14:0801140C→030000DC, and initially7F9C:08011204→08011208. These values remain in the comparison report; they are not normalized away or claimed to establish complete RAM or performance equivalence.

The actual WIN label matches1508 pixels with the full captured screenshot. Five controls reject checksum, OAM shape, copied renderer, actual label VRAM and actual label palette corruptions. The captured Korean commit, title, battle, result, first label and+120/+300 observations all pass; last-chance mode was not observed. This does not test the new IRQ branch during Shoot, campaign completion, historical E5 resolution or hardware timing parity.

| Artifact | SHA-256 |
|---|---|
| build/result-v73-runtime-qa-20261109/audit_capture.py | 8E1D8D84C9992FEC21C2D2E5DC8769635652F7259C423DD2741BA12F10212583 |
| build/result-v73-runtime-qa-20261109/ko-audit.json | 27F1FF44F9C36B177387E3BCA5ED14B50D59BD0427A18D5183C4546150CD24DF |
| build/result-v73-runtime-qa-20261109/v72-comparison.json | EC6453B5018EE57B6EB0C77FAE54DBE3B614212DA1FF14874E45B1D1E2905CFA |
| Reused v72 baseline audit | 62FE91FAE6245EA2F28DBD419D12E0AA70ED62CA65B5EEED37C6E75A0534BDB6 |

The new checker and reports are LF. Run the new capture auditor with the pinned Python after capture completion; it reads only generated flat capture artifacts and the immutable ROM/observer inputs.

