# Mode 20 uses a signed task priority

The E212 r3 replay directly observed the final-card readiness on core 102729 and its native exit request on core 102806. The mode word changed 11 → 20 on core 102807. The original process exited with code 1 because its art owner check compared a signed 32-bit task field to an unsigned 16-bit constant. The actual art owner met each remaining guard.

At the frame-boundary capture on core 102839, current owner `02010230` is active and has callback `0804074C`, priority word `FFFFF100`, and scene flags `0003`. Its screenshot and five native memory regions remain part of the finalized capture. The actual state agrees exactly with all five exported regions.

WSC 1.5 mode 20 constructor `782535` supplies the task priority `F100` as a 16-bit stack word. E212 native constructor `08040470` supplies the same field at `080404C0`, sign-extends it at `080404C4/C8`, and calls the allocator. The allocator sign-extends the argument at `08011AE8/EC` and stores the 32-bit word at header +4. Executing the installed constructor and allocator confirms priorities `00001000` and `FFFFF100` with initial callbacks `080404F8` and `0804063C`.

The r4 preflight verified that its sole Lua delta changes the expected word to `FFFFF100`. It preserves the active owner, callback, hardware scene flag, request and title guards, the same E212 ROM and checkpoint, ordinary inputs, guarded one-time boss write, and frame and host bounds. The new host reverses exactly to r3 after versioned output and probe names are restored. Six pinned files and the nine existing Lua fixture cases agree.

| Artifact | SHA-256 |
| --- | --- |
| Actual r3 launch manifest | `D0CF2E41FC42EEFDAAAC31B2C93B73CC20EB77DE86AA1D70C79468543AA5195A` |
| r4 probe | `6533778C81A901F173DEC973EAD1365A9511AEBB1E76AD3144A663F25388B311` |
| r4 launcher | `66DCE81003CBACF61A6FFE224387C6431FB37A29DB525F5D323C2EE9FE84F994` |
| r4 reviewed pins | `6FAFA233B0ED5B18D4D633E66325B3F0DC452833CB46B2C09D5C70CEC005577A` |
| r4 author fixture | `3DC2AA66D267131F557C4D6AE05554AA9EE0AA8B725EC70B79321196808B2DA8` |
