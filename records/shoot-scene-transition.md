# Guarded Shoot scene translation draft

Recorded 2026-10-13. These generators and independent verifiers are saved
drafts. **No scene or route ROM was emitted, and no entry hook was installed.**
The complete `7168` initializer at proposed native `085C7800` remains
blocked by the [source SRAM observer gate](shoot-sram-boundary.md). An absent
initializer is rejected even when its `FF` bytes have the expected hash.

## Scene implementation

`tools/build_shoot_scene_transition.py` translates source `71F0:0EEA..15A8`
and presentation `15C9..174F` using the existing current-task, object-pool,
presentation, palette, audio, angle, and trigonometric services. It adds no
scene allocation or RAM globals. Every callable preserves `r0-r12`, LR,
and SP; flags are clobbered. The proposed native task data fields are timer
`+50`, delay `+52`, and saved HP `+54`.

The 22 proposed placements contain 648 ARM instructions and 3,032 total
bytes, occupying selected intervals from raw `5C8000` through `5C9868`.
They cover the original entry cleanup and HP save, positioning, palette
snapshot and white transition, the audio reset/full-initializer call,
black transition, hold and D2 request, palette restore, eight moving
presentations, HP/count display, and final input/battle callback restoration.
The scene source counters `151, 200, 5, 100, 6, 32, 150, 30, 20` are retained.

Several receiver details are material:

- Source `1020` has already replaced SI with the first player. Its store of
  `5` therefore writes the player's field `+42` (native `+52`), not the
  scene timer. The scene keeps `200`, then reaches `199` on the same call
  through `1043`.
- Source `106E` clears current-task field `+1E`. The translation uses the
  proved native task halfword at `+2C`; it does not overwrite a presentation
  pointer by assuming the two layouts match.
- Source `155F` restores input `4090:07FA` and battle `4090:0D0B` before
  retiring the scene. Native counterparts are `08374FF4` and `083735BC`.
  Active Shoot gameplay can therefore move the camera; its Y position is
  not permanently zero after initialization.

The eight presentation objects reuse the exact commercial resources at
native P1 `08350248`, P0 `083505E8`, and P2 `08352240`. Independent comparison
covers seven P1 commands, 42 items, 17 nonzero tail references/11 unique
tail records, 15 P0 layouts/648 bytes, 21 tile descriptors/6,304 tile bytes,
and the converted palette. Their callback uses existing pool 2 and retires
through the actual object release service.

Source sound `9A/type1` uses the proved native `5A/type1` lineage; source
`06/type2` uses native `0/type2`. Source `4FFF:50F2` calls the real native
reset `0801565C`. The eight channel/side calls use the retail backend
`080158C8`, which is itself a return-only function. The lack of an
intermediate channel-volume fade is an explicit native backend limitation,
not an implemented fade or a newly invented stub.

`tools/verify_shoot_scene_transition.py` imports no generator. It binds
complete code/literal profiles, original source receiver/branch contracts,
actual native resource consumers, counter and position algebra, palette
channel algebra, register preservation, and twelve semantic mutations.
Its full predecessor/output check has **not** been run without the required
real full initializer.

## Conditional route draft

`tools/build_shoot_scene_route.py` and
`tools/verify_shoot_scene_route.py` describe two later guarded hooks:

| Existing instruction | Proposed adapter | Preserved continuation |
|---|---|---|
| `0833FD04`, case-5 callback load | `085C9900`, 104 bytes | `0833FD08` |
| `080B9E68`, progress-path load | `085C9A00`, 84 bytes | `080B9E6C` |

The selector changes only the callback argument to the **existing single
allocation** at `0833FD18`. Case 4 and every other case retain their
existing paths. The source predicate is exactly:

```text
stage != 11 &&
(difficulty == 3 || (difficulty != 0 && (progress & 0x0400) == 0))
```

The progress word is source `1000:0068`, independently bound through
commercial source/native producers to native `0300232A`. The added producer
sets `0400` only when stage is neither 7 nor 11. The existing stage-7 `0200`
producer and unrelated bits remain unchanged. Both adapters preserve CPSR
flags and all registers except the original load destination (`r8` or `r1`).
They branch back without creating a new object or a new RAM owner.

The independent route contract covers all 131,072 combinations of 256
stage bytes, 256 difficulty bytes, and both `0400` states. It also checks
262,144 full-word progress cases, six semantic mutations, and every one of
the 36 ARM instruction encoding round trips. These are static and algebraic
checks; no CPU or game was run.

## Frozen evidence and next dependency

The in-memory draft checks are recorded at
`build/shoot-scene-draft-20261013/static-draft.json`, SHA-256:
`CAB854CF5990B6B399ED60C0E599BD98D132395D5CD3A56E98200127514237F9`.
It explicitly records that neither full ROM verifier ran and no ROM was
written. This is separate from the earlier scene-ownership report at
`build/shoot-scene-20261013/verification.json`.

Once the SRAM gate is actually closed and the real full initializer is
implemented, the scene builder requires an exact predecessor hash and an
initializer entry/extent/hash. Its independent verifier requires entry
`085C7800` and checks the entire emitted scene against the fixed profiles.
The route layer then requires exact predecessor, scene, and initializer
hashes. Normal battle ownership, object lifetime, all downstream rules,
graphics/display dependencies, and restoration paths must be satisfied
before that external route is installed. None of those gates is waived by
the static draft results above.
