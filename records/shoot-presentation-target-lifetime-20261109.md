# Presentation target lifetime repair

The isolated D0 component retains the target in r6 across the native angle
and trigonometric helpers. It addresses the actual first-presentation stall
documented in `shoot-native-presentation-receiver-stall-20261109.md`.
The five expected instruction words change only their receiver register;
five individual bytes differ, within twenty declared bytes. No code cave,
RAM field, event producer, coordinate, health rule, or callback is added.

| Raw address | Before | After |
| --- | --- | --- |
| 5C9108 | 141094E5 | 146094E5 |
| 5C910C | F403D1E1 | F403D6E1 |
| 5C9120 | F633D1E1 | F633D6E1 |
| 5C9174 | F403D1E1 | F403D6E1 |
| 5C91A4 | F603D1E1 | F603D6E1 |

Source `7735D4..773650` retains its receiver in BX and uses it again at
`773611/773624` after angle/trig. The native body previously retained that
pointer in r1, but its actual helper graph `12560 -> 12650 -> 126A4` writes
r1 as the division denominator on both branches at `126DC/12700`.
The builder inventories all four receiver dereferences, pins each imported
body, and verifies that the complete native angle/trig instruction bodies
never write r6. The callback's original push/pop already saves and restores
r0-r12 and LR, including the newly used r6.

The author check runs the actual native angle and trig bodies, the ARM
division thunk, and the real release `3524C4`, pool lookup `352AF8`, and task
callback replacement `11E7C`. Only the Thumb BIOS SWI6 boundary is modeled;
its quotient/remainder outputs and preserved-register ABI are explicit.
The original runner was extended only for the native non-S MUL instructions
and register-offset LDRSH used by those bodies. No angle, trig, completion,
or release service is substituted.

For an independent primary implementation reference, mGBA commit
`9660a668f2093cb4aba5983f52bebf8878dc5b8b` implements SWI6 through `_Div`;
its register writes are r0, r1, and r3, preserving r6. This supports the
declared BIOS ABI boundary; it does not assert that this source revision is
the installed core or that the commercial BIOS body was executed.
[Pinned mGBA BIOS implementation](https://github.com/mgba-emu/mgba/blob/9660a668f2093cb4aba5983f52bebf8878dc5b8b/src/gba/bios.c#L250-L280).

The exact completed native capture is replayed inside the bounded ARM check:
presentation `020112B0` at `13A1/0CFB`, target `02011828` at `13A1/0D2B`,
and event word `03004508=0002`. The original body reaches its completion
load with r1=0 after real angle computation; it stops before reading BIOS
address0034, so no invented BIOS memory is used to make the old path fail.
The repaired body retains r6=02011828, writes the natural event word0012,
and executes native release bookkeeping on that presentation's actual pool.
All outer registers, LR, and SP return unchanged. Angle/trig velocity writes
before the completion check match the original.

Additional checks cover 384 combinations of inside/outside inclusive box
boundaries, both source angle offsets, quadrant/division branches, and entry
flags, plus all sixteen NZCV values for the unmodified captured pose. Both
native divide call sites execute. Ten controls reject malformed writes,
off-target changes, and reverted completion receivers. Whole-ROM inversion
restores exact D0, preserving the first-run ROM, current main, entry selector,
HUD bytes, and unopened nonfatal hook.

The unchanged atan(0,0) division-by-zero output is outside this modeled
execution set. This is an isolated author result; independent QA and actual
replay from the genuine stage7 checkpoint remain separate gates. No emulator,
save, running probe, main build, or Git state was changed by this work.

Frozen artifacts:

- Builder `tools/build_shoot_presentation_target_lifetime.py`, SHA256
  `8C099EAD5CCA7AFD86482DC810AD15FE90DA09F429D30C86AEE95F5A9EA3C783`.
- Component `build/shoot-presentation-target-lifetime-20261109/component.gba`,
  SHA256 `84D6FA3F6F80302B4A52B0DA2E3CCEBD0181CDA42FB6DE6318AB81C5CA5CA43B`.
- Author report `build/shoot-presentation-target-lifetime-20261109/component.json`,
  SHA256 `148A6143330E73A3439ABCD5A66A16DC805393392DEEA38D950F39C91F2BF31C`.
