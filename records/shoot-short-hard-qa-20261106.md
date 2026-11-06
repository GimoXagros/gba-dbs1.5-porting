# Independent review: ordinary-input short/hard probe

Accepted the revised observer wrapper for a fresh root-owned run. This is host-script review and mock execution, not evidence that a real campaign reaches Shoot.

- Wrapper `tools/bizhawk_probe_wsc_shoot_short_hard.lua`: `E382D2D1462B7507090483548FD12DBC97A0342BA0C90D617268D6460A63ABD0`.
- Mock checker `tools/verify_wsc_shoot_short_hard.py`: `2479D74DFA73F84E85EBECE0F047171F7401E9448B254DAE1D223EEC7AF3DE83`.
- Independently rerun report `build/shoot-short-hard-qa-20261106/mock-independent.json`: `A13034C95FA2586A2274DD15DBD7C269AE7F9F2B9E3D6DAFB45F3886BCD2597C`, identical to the author's final report.
- Frozen observer dependency: `0CC9B17CAE00E7B7EFA33976788B1A66F595F15473EE78A597A77ADF68F42D69`; frozen collector: `2AD5BB33BB5FA85A654E5A36ECDF002195076CC85FB62C4E7A7033797BA37A17`.

The wrapper navigates actual Options through joypad input to difficulty3 and timer selector0. Source timer rows yield6750/9000/13500 updates; selector0 is the90-second setting at the source75Hz rate. The stage7 boss retains its separate18000-update budget. Disabling the score-orb collector override specifically during stage7 preserves ordinary chase/attack inputs needed for boss HP depletion; it does not change HP, scores, timers, flags, RNG or callbacks.

Review caught two defects in the initial wrapper. First, it required two row-clear callbacks even though one actual197A clear is sufficient; the initial mock unrealistically repeated the callback each frame. Second, the final all-buttons-up input passed through the collector and could be replaced with movement when a bounded run ended beside an orb. The final wrapper counts only stage11 row-clear/IRQ events, accepts one row clear, and calls the original joypad setter captured before collector installation for final release. The private load environment exposes that setter only to the final release call.

The final actual-Lua mock covers all12 initial timer/difficulty combinations plus bounded boss, bounded ordinary-orb, missing Shoot row-clear and missing Shoot IRQ routes. It injects pre-Shoot row/IRQ callbacks to verify they cannot qualify early completion. All16 routes and five mutations pass. Successful early completion requires positive stage11 row-clear and stage11 final-IRQ observations plus300 observed Shoot frames. Bounded completion does not pretend those events occurred. Original owner hooks, snapshots, callback/address calibration and final release remain present.

The code reads frozen scripts and writes observation files beneath the explicit build output directory. The mocked environment supplies no guest-memory-write, register-write or savestate API. No emulator was launched during this review. The launcher must verify all three script hashes, use a fresh output directory, and retain the original ROM/save isolation already owned by the parent.
