# Pause retirement before Shoot terminal — 2026-11-06

The normal case-5 producer cannot allocate the terminal scene while the pause task remains linked. This closes the concrete same-priority pause interposer identified in the earlier BX provenance record.

Source normal input sets pause flag 1 or 2 before allocating `8619:0193` at priority `0FF0`. Normal battle tests mask 7 at `74165E` and skips the case-5 producer at `7417E6..7417FB` whenever any tested flag is set. Unpause clears those flags at `7864A3`, then synchronously retires its own task at `7864E8`, before its optional case-1 root call or return. The retirement implementation clears task status and splices both neighbor links at `750A85..750A94`. It does not defer unlinking until a later frame. Terminal input `07D6` cannot create a new pause task.

The current native image retains the corresponding input flags, battle exclusion, unpause ordering and synchronous task unlinking. All four native flag consumers resolve to `03004529`; the checker compares those actual current-image ranges with the immutable retail original before checking their instructions.

`tools/verify_shoot_terminal_pause.py` passed 512 flag combinations and seven direct semantic mutations. Evidence: `build/shoot-terminal-pause-20261106/proof-a.json`. Checked current image SHA-256: `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738`.

Frozen checker SHA-256: `BD267F0225776FA7085EC7FE2C918D8C8CBD367523FDAD2BF42BCAAA09EEAA02`.
Evidence SHA-256: `A77E7BFD1F42E67D5C3ABA573782552785A8C9A290D72A4F56D944FA4D27EB3D`.

This proves normal-entry pause exclusion, not arbitrary forced task entry. Actual terminal camera range and source clear projection remain separate requirements. No ROM, emulator, save or guest memory was changed.
