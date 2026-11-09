# Native Shoot nonfatal caller readiness

Read-only proposal against frozen experimental D0A01A7F, whose normal-hit site
is still retail. No ROM, builder, observer, save, or emulator was changed here.

The existing resident adapter can be reached with one four-byte replacement:
raw `36E634`, `5C809FE5` (`LDR r8,[pc,#5C]`) to `D97C09EA`
(`B 085CD9A0`). No new storage or cave is needed. Resident `5CD9A0..5CDA3C`
is 156 bytes, SHA256
`FAF0C722D88D307D08C32F20B2F5E06A9713ADC116B54CC2E22805C51CAF7404`.
Its original author/verifier are `build_shoot_terminal.py` and
`verify_shoot_terminal.py`; their existing proof deliberately kept this hook
closed. This finding is readiness for a separate component, not a connected
runtime claim.

## Exact branch and frame contract

Source positive-HP branch `760229..7602AA` selects stage11 at `76023A`.
The Shoot branch loads its flash palette, sets victim source `+60` to 8,
conditionally flashes palette zero entries under source flags `4030`, then
joins common attacker processing at `76006F`. Unlike the non11 branch it does
not call the old lower-object refresh routine.

Native `36E5C8..36E5E8` already reads the damage byte, halves it for attacker
`+8 & 4000`, performs signed HP subtraction, stores victim `+64`, and branches
to `36E634` only for a positive result. The proposed hook is after all of that;
fatal hook `36E5EC` and its cleanup remain untouched.

Collision entry `36E348` saves `{r1,r2,r3,r4,r5,lr}`. At adapter entry r4 is
the attacker and r5 the victim. The stage11 adapter pushes five words for native
palette loader `080132EC`: resource `085C0B00`, three zeros, then destination
slot 1. It balances all 20 bytes. The actual loader saves/restores r2/r4/r5/lr,
reads palette index 0, and copies 15 halfwords into `05000222..0500023E`.
The common collision return `36E484..36E488` restores the enclosing saved LR;
the adapter's internal BL therefore needs no additional return-frame patch.

Stage11 then writes victim `+74 = 8`. If `0300450A & 4030` is clear it writes
red `001F` to BG0..15 and OBJ0..7 color-zero entries, and joins `36E438`.
It neither changes an actor callback nor allocates, releases, or retypes a task.
Normal actor ownership and the already initialized Shoot resources remain
prerequisites supplied by the real collision route, not repaired by this hook.

Non11 restores exactly displaced literal `0834F836` and rejoins `36E638`.
All general registers match the original instruction at that join. Its new
stage CMP changes NZCV, but the palette loader has no flag consumers; the
following old lower refresh reaches `3730F8 CMP` before a condition uses them.
Stage11 rejoins the same attacker tail `36E438` already covered by the fatal
route's bounded per-bit flag-lifetime proof. For the actual default fighter
kind0, `36F558` reloads victim kind into r0 before using it; common return
restores saved r1/r2/r3. This is not an assertion that arbitrary untyped callers
can enter the adapter safely.

## Flash lifetime is already connected

`3700F4 -> 586B00` selects the existing stage11 main loop `586C00`.
At `586C6C..586C90`, SECOND's `+74` decrements and, on reaching zero,
the loop calls `587000` with that actor. Thus the timer is eight eligible main
loop updates, not an unconditional promise of eight video frames.

`587000` selects the HP-threshold palette from `587100/587128/587150`, loads
it through the same native palette ABI, and calls `586E00` when flags `4030`
are clear. The latter restores/advances the sixteen BG color-zero entries.
It does not restore the eight OBJ color-zero writes; those are transparent
sprite entries. Avoid describing this as restoration of all 24 written entries.
The normal-hit adapter uses no new lifetime owner or private RAM counter.

## Small remaining acceptance scope

Before connection, the separate author/reviewer should pin the exact four-byte
site and resident block and prove the whole-ROM inverse. Linked actual ARM
checks should cover all non11 stage bytes at the original join, flag liveness,
the positive-HP/evolved-damage boundary, the real native palette loader and
balanced collision return, both flash-mask branches, and timer 8 through zero
with the already connected palette-restoration owner. Existing resident finite
checks are not a substitute for this newly connected caller validation.

The concrete runtime gap is a healthy, initialized stage11 collision with
positive post-hit HP: typed FIRST/SECOND/aux resources, pre/post HP, `+74 = 8`,
actual adapter entry/return, palette writes, and subsequent expiry while normal
input/controller callbacks remain active. An HP1 lethal-hit observation cannot
establish this normal-hit path. No additional broad source or E5 replay is
needed to answer this one-caller question.
