# Terminal BX dispatcher provenance — 2026-11-06

The actual source dispatcher does **not** restore BX to a task pointer after
input callback `07D6`. It preserves only ES, DI and CX around each indirect task
call. Its complete body and frame-wait helper never assign BX. Therefore,
under the normal exclusive scene queue, the value consumed at `7738CA` is the
preceding input callback's BG0 pixel-camera snapshot, not a tile-row index or
task-header pointer.

## Positive source chain

- Normal battle initialization `740CB3..740CC6` requests the priority-zero
  sound task, creates the actor pool, then creates input and battle tasks.
- Creator `740FC1..740FE8` gives input priority `0F00` and battle priority
  `6000`, storing their handles at `1000:03DE/03E0`.
- Scene root replaces those callbacks with `4090:07D6` and `4090:0B8B`.
  The callback replacement helper writes only task+0/+2. Priority is retained.
  The root allocates the terminal `71F0:0653` task at priority `0FF0`.
- Allocator insertion search `750C6D..750CB5` sorts ascending unsigned
  priorities. Thus battle `0B8B` runs after the scene, not between its input
  snapshot and `197A`. All 26 priorities read by the actual actor-pool creator
  are greater than `0FF0`. The positive creator population has adjacent input
  and scene entries.
- Input `7410D6..7410F9` loads BX from `1000:01E0` and stores the same value at
  `0C00:3A16` as its last BX operation. It then returns.
- Dispatcher `750B57..750B73` saves/restores ES, DI and CX and follows task+8.
  No instruction in the entire dispatcher mentions BX; frame wait preserves it.
- Successful `193B` temporarily puts the current task in BX only inside its
  push/pop pair at `773861/773879`. The following `197A` prefix has no BX
  operation or callee before `7738CA`. Direct `197A` dispatch has the same
  unchanged incoming BX.
- Transition line handlers `0D87` and `0DEC` explicitly push/pop BX. Their
  internal use of BX does not overwrite the interrupted value on return.

These checks reject the proposed scheduler-restores-task-pointer explanation.
The positive normal creator population is not an exhaustive live queue dump:
In particular, pause task `8619:0193` is positively allocated at the same
`0FF0` priority by `7861E7..7861F4`. Since equal priorities insert after existing
entries, an older live pause task could intervene before a newly created scene.
Its retirement/exclusion and other enabled IRQ callbacks still require their
normal-entry/exclusivity contracts. This is a concrete possible interposer,
not an observed concurrent pause. The checker keeps that scope explicit and
does not turn a representative sorted queue into arbitrary-state reachability.

## Checked artifact

`tools/analyze_shoot_terminal_bx.py` reads only the immutable WSC1.5 original.
It checks complete instruction ranges, the positive priority producers,
callback replacement fields, input live-out, the successful ground-wait path,
and both transition IRQ BX save/restore pairs. Eight direct semantic mutations
bypass the full-source hash and must fail the actual instruction checks.

The source clear remains `(0800 + (BX << 6)) & FFFF` followed by 64 zero
halfword stores. Its unrestricted 16-bit arithmetic has 1,024 distinct starts;
provenance by itself does not establish a camera bound. In particular, this
work does not establish that the reached destination lies in the native
helper's mapped `BX=0..62` domain.

No ROM, game callback, native owner mapping, emulator state, save or guest
memory was modified. Actual terminal camera range and a source-correct mapping
of the reached destination remain open. No clamp, ignored write, or speculative
graphics projection was introduced.

A separate read-only reviewer independently confirmed dispatcher BX behavior,
ascending insertion (ties follow existing entries), the complete input snapshot,
and the 193B restoration. The reviewer identified the same-priority pause
interposer above. The conditional scope was retained.

Frozen analyzer SHA-256: `C9E801846EB981EEE2B815FFA15E4AB2ADE042A752DE13C98B3FB031BE5C4150`.
Final evidence SHA-256: `8929F536C61D7E4ED0B8197E58123ABBBA117F05344C35779CE633218F1F8B62`.
