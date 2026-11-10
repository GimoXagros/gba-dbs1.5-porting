# Independent v76 ordinary Korean KO capture

PASS for completed `build/bizhawk-result-v76-20261110-a`, exact280D ROM,
unchanged observer, no guest writes and finalized successful launch.
All62 listed artifacts plus launch.json are verified:63 top-level files.

All eight PNG files, all five complete RAM regions including entire IWRAM,
and all display dumps exactly equal v75. The entire128-line trace is
byte-identical. There are no normalized bytes, raw-line differences or
frame deltas. The eight capture cores remain3458,3559,3560,3999,11519,
11639,11776 and11819. Native writer/init/draw populations remain1/7/88;
the complete WIN label retains30 parts and1508 matching pixels.

The new directory adds config.saving.json relative to v75. Shared files
change only for config.json,launch.json,probe.gba andloaded-rom.bin. Both
final inventories remained unchanged throughout independent review.

The host requests audio method3 and the completed v76 config records3,
with sound disabled and autoload/autosave disabled. Prior v75 saved method1.
The first run of the new draft v76 checker inherited that prior-specific
method1 assertion and failed before producing reports. Only the new v76
checker was adjusted to require the actually observed method3. This initial
failure and qualification are retained in the comparison report; no frozen
v75 checker or capture was modified. No audio quality or playback parity
is claimed from this silent ordinary-KO test.

| Artifact | SHA256 |
|---|---|
| tools/verify_result_v76_capture.py | D5A9BAB2CC5924C05AC2185FFB7173BE85673C6E48C89A42EF9CA9514B77F244 |
| build/result-v76-runtime-qa-20261110/ko-audit.json | 2547A5562752AE0313E8928D72465BBF4EAFB7FAAC0AA92DDC2B7EB196FBD8D1 |
| build/result-v76-runtime-qa-20261110/v75-comparison.json | 1E2C54B19978097345CC6241EE777F8F25815B080B0D724028984B3BE0595DFC |

The unchanged generic665A verifier ran its full ordinary-capture audit.
The completed capture's own exact ROM was used; incomplete full-build
directories were not read. No emulator, original save/State, old manual
suite, main/runtime/host/Git edit or capture mutation was performed.
Full-build inventory and terminal-mode8 evidence remain separate reviews.
