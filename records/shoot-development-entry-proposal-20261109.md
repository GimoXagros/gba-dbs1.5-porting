# Bounded native Shoot entry experiment proposal

Read-only proposal against frozen resident component `6A1AEBDD3751D3E2684C7F7D26A28F0473EB6733BE6371F50F0E9C2A12A033B7`.
No development ROM was emitted or launched. This is a possible separate
development experiment, not approval of complete external entry in the final ROM.

The minimum connection can reuse the selector already reviewed in
`build_shoot_scene_route.py` / `verify_shoot_scene_route.py`: 104 bytes at raw
`5C9900`, plus one four-byte branch at `33FD04` replacing `E59F80A8`.
It preserves r0/r1/r12/LR/SP and NZCV, sets only the normal callback argument
r8, and continues at `0833FD08`. The actual existing allocator call remains
`0833FD18 -> 08011AC4`, with priority `0FF0`. There is no additional task,
descriptor, constructor, or forced mode/stage/HP/register intervention.

Source `771F84..771FF4` selects `71F0:0EEA` exactly when
`stage != 11 && (difficulty == 3 || (difficulty != 0 && !(progress & 0400)))`.
Native fields are byte `0300231E`, byte `0300231F`, word `0300232A`.
The translated callback is `085C8000`; the default is resident `086FC300`,
which selects `085CD000` for stage11/source1750 and retail `0834059C` otherwise.
The original callback literal is at `0833FDB4`. Noncase5 paths are untouched.

The native normal producer at `083736B0` is reached under game kind word
`03004502 == 2`, control byte `03004529 & 7 == 0`, and SECOND signed HP<=0.
The common scene root already replaces input and battle callbacks before its
one scene allocation. This removes their normal pause/repeated-match-end
producers. The reused scene obtains the actual current task via `0801201C`;
it does not require a synthetic current-task pointer. Its saved health and
temporary HP1 operations are existing translated source scene behavior.
Normal initialized battle, live engine-owned actors/lists and a single scene
owner remain the bounded experiment's entry conditions.

The draft's separate 84-byte progress producer at `5C9A00` and hook `0B9E68`
are not necessary just to observe selection from the real current progress
word. The smallest experiment should read that word without changing it.
Complete source progression behavior would be a separate source-derived layer,
including the existing stage7 `0200` rule and stage-not7/not11 `0400` rule.

Current byte checks confirm the 104-byte selector reservation remains FF.
The ordered initializer `08629800` remains 140 bytes with SHA256
`8FEDEC3D4115A92339E37D1F78CAC2A1DE4A435A074CF641339FF22EC90B5F13`;
the terminal router remains 52 bytes with SHA256
`3B528805D97B87A3C35CE298E929AE3B46BCE2BDF8009A165A04BFB4EB175474`.
Existing caller, palette, storage and task-lifetime proofs supply these
dependencies; none was rerun here.

## First concrete native consumer risk

The conditional generic-grab path is the first identified direct invalid
native data consumer to watch. `08354FB0..08354FB8` selects victim event
`48` hexadecimal through `08012874`. On entry to that consumer, stack `+0`
is the event and stack `+8` the presentation argument. Upper P1 has only six
declared events. Its table `085D0008 + (48 << 4)` is `085D0488`, whose current
four words are `00000010, 00000000, 00000000, 0008FF03`.
`080128A4` loads the zero frame pointer and `080128BC` dereferences it.
The source's out-of-table bytes differ. This is a concrete conditional
consumer mismatch; ordinary-input reachability remains unproved, and no
runtime failure is claimed. Observing this exact call with the live upper
presentation would resolve the relevant reachability question. No generic
grab suppression or idle substitution is proposed.

## Existing guard outcomes observable without new guest RAM

At `085CC0D0` (8EF3), read signed captured target Y at current r4+`A2` and
signed lower X at r4+`34`. The retained rejection returns r0=0 through
`085CC1C0/1C4` when Y>`1B00`, or Y>`1600` and X>=`1E00` after the v70
extension. The caller has already selected idle before this result and skips
the pattern transition on zero. This is an observable incomplete-source
boundary, not an out-of-table native access. It needs no guard removal.

The terminal row-clear helper retains unsigned camera-row<=62; a refusal
performs no clear. The v73 transition guard has its existing local allow/refuse
result and tiny-wrapper stage/mode predicates. Their current task, fields,
callback and return values can be logged through read-only hooks. A bounded
experiment can therefore distinguish source-scene progress, live guard
refusals and the specific event48 consumer without adding guest diagnostic
state or asserting that every legal entry is supported.
