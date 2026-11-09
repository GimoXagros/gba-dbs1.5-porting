# Original Shoot checkpoint input replay

`tools/bizhawk_replay_wsc_shoot_checkpoint.lua` is a dedicated baseline replay
driver. It does not load the campaign input policy, any approval-bearing
driver, or a score/HP intervention module. The baseline first establishes
whether a genuine checkpoint and its recorded final inputs reproduce the
observed continuation. A changed controller or stage11 intervention remains
separate work.

Launcher interface: userdata `output`, `checkpoint_dir`, `frames`,
`source_sha256`, `callback_order`. Paths are distinct safe W:/build paths.
The launcher copies and pins these five immutable checkpoint artifacts:
`shoot-preactivation.State`, `shoot-preactivation.txt`,
`shoot-preactivation-ram.bin`, `shoot-preactivation-sram.bin`, and
`shoot-inputs.txt`. It also supplies `output/authorized-cartridge-copy.bin`
from the already authorized original-save copy. The source/core/executable,
configuration and artifact hashes remain launcher responsibilities.

Before loading, export the actual ROM and freshboot SRAM, then apply the
same complete 32KiB equality guard as A0AC: only the two positively bound
startup stores004E=01 and0073=00 transform the expected copy. A wrong initial
save fails before loading or applying any input. Parse the recorded input
stream before loading: all13 known Boolean button values, contiguous relative
and core frame numbers, at most3000 records, and a valid optional exit marker.
The frame budget must be1..3000 and no larger than the complete record count.
Button names include spaces; the parser splits at the explicit trailing
`payload=`/`invalid_payload=` marker rather than the first space.

Call `savestate.load(path,true)` exactly once at the safe outer Lua boundary,
before installing callbacks. Require true and exact initial64KiB RAM,32KiB
SRAM and core frame equality, plus stage11 and clear activation bit4. The
driver captures its new arguments before loading, then calls the official
`userdata.clear()` and restores only those five arguments. This removes the
checkpoint's old output, budget and approval token. The exact tag2.11.1
[userdata API](https://github.com/TASEmulators/BizHawk/blob/2.11.1/src/BizHawk.Client.Common/lua/CommonLibs/UserDataLuaLibrary.cs)
provides clear/set/get; state load behavior is documented in the separate
boundary-checkpoint QA record.

Immediately export fresh `restored.State`, RAM/SRAM and screenshot without
advancing. This enables independent comparison of the complete decompressed
native/managed core payload with the original checkpoint. UserData/container
bytes need not be identical because output and run arguments intentionally
change. Save return, actual nonempty ZIP and unchanged RAM/SRAM/frame are
checked. Neither these checks nor matching RAM alone establishes complete
native continuation equivalence; that requires the independent container and
runtime comparisons.

The driver loads frozen DI observerBD01 and boundary helperCEC38 directly.
The latter's activation, paired P1 loss and jump hooks remain applicable;
its initializer-dependent checkpoint/HP-write fallback is explicitly logged
inactive. No synthetic initializer, calibration or reconstructed Lua-local
state is introduced. Real750EBD calibration remains required by DI v3:
ordinary scheduler750B7F invokes this shared frame-wait helper independently
of the stage; runtime must still deliver the actual callback.

Replay each final13-key table unchanged, then require the recorded next core
frame, stage and complete FIRST context (callback, type/index/id, links,
owner16, HP, held/edge, position and flags). Boundary snapshots permit further
full RAM/SRAM and rendered-frame comparisons at matching events. At the
chosen final recorded frame export `final.State`, RAM/SRAM and screenshot,
finalize both observers, release physical keys without another frame, write
`done.txt=checkpoint-input-replay-complete`, and exit. The record separately
states whether the recorded exit was reached and any actual terminal/DI
evidence. A final-state equality claim needs a baseline state at that same
core frame; an arbitrary final campaign snapshot is insufficient.

Frozen driver SHA256:
`2DE2171C3D92FAB6C32C1D4CB9D7EEA7C71F467A9FEA73AAEF0BD6E3B475DB9F`.
Author check `build/wsc-shoot-boundary-20261109/replay-selfcheck.py` executes
the actual driver in Lua54 with mocked APIs/module endpoints. Ten scenarios
pass: normal two-frame replay and refusal of a relative gap, excessive budget,
wrong boot copy, false load, restored RAM/frame mismatch, missing state export,
stage divergence and FIRST context divergence. The normal case uses every
real space-containing button name, replaces the userdata bag during load,
and verifies one load, two state exports, exact exit and final marker.
Independent QA owns composition/launcher review and actual saved-state
validation. No emulator, original save or genuine checkpoint was accessed by
this author check; no actual terminal success is claimed here.
