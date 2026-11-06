# Independent terminal BX review — 2026-11-06

Reviewed `tools/analyze_shoot_terminal_bx.py` and its source predicates, then
independently decoded the original scheduler, queue insertion, input, terminal,
and both transition line callbacks. The bounded provenance result is supported;
the file correctly leaves complete live-queue and other enabled IRQ ownership
open. No sibling file, ROM, emulator, save or guest state was changed.

## Supported source facts

- `750B57..750B5F` saves/restores only ES, DI and CX around the task call.
  The subsequent dispatcher bookkeeping uses SI/AX/DI and preserves callback
  BX. The pre-`F000` scheduler path does not introduce a wait between an input
  task at `0F00` and the scene at `0FF0`.
- Queue insertion `750C73..750CB5` is unsigned ascending, placing new equal
  priorities after existing equal priorities. Input allocation `740FC1..740FD2`
  writes its real handle to `1000:03DE`; battle allocation uses priority `6000`
  and handle `03E0`. Terminal entry retargets these handles without changing
  their task priorities and creates the actual `71F0:0653` task at `0FF0`.
- The full input `07D6` body finishes with BX equal to `1000:01E0`, BG0's pixel
  camera-Y field, and writes that same value to `0C00:3A16`. Its sole local
  callee precedes this final load and cannot change the value afterward.
- In `193B`, the temporary task-pointer BX is balanced by the push at `773861`
  and pop at `773879`. From there through `197A`'s `7738CA` consumer, there is
  no BX write or callee. The direct `197A` entry likewise consumes its incoming
  BX. It is not implicitly a task pointer or a tile-row index.
- Both complete transition handlers `75FC27..75FC8B` and `75FC8C..75FCA2`
  restore BX on their actual return paths. This does not establish every other
  enabled interrupt's register contract.

Thus, **if input and scene are adjacent in the live queue, and intervening
interrupts preserve BX**, the clear consumes the preceding input camera
snapshot. This establishes neither the camera value nor the owner of the
resulting wrapped destination `(0800 + (BX << 6)) & FFFF`.

## Concrete remaining queue question

There is an additional real task creator, beyond the checker's normal-creator
fixture: pause code `7861E7..7861F0` allocates `8619:0193` at priority `0FF0`.
Because equal priorities insert after existing equals, an older live pause
task would precede a newly allocated scene. This is not a claim that pause and
the terminal scene actually coexist. Its retirement/control-flag lifetime is
the specific exclusion required before upgrading the fixture to an exhaustive
normal-route adjacency claim.

The two dynamic-priority allocator wrappers also deserve caller-sensitive
treatment rather than being ignored by a literal scan. Independently inspected
examples narrow them: normal battle calls the `1D68` wrapper with priority zero;
the concrete serial-wrapper caller at `77BB70` passes `1000`, outside the gap.
Neither fact alone closes all wrappers or callbacks. The sibling checker
explicitly limits its conclusion accordingly, so no blocker or correction to
its existing bounded claims was found.

## Reproduction

Reran the final checker on the immutable source into
`build/shoot-terminal-bx-review-20261106/recheck-final.json`. All eight semantic
mutation negatives pass. The result is byte-identical to the sibling's
`build/shoot-terminal-bx-20261106/evidence-final.json`.

- Checker SHA-256: `C9E801846EB981EEE2B815FFA15E4AB2ADE042A752DE13C98B3FB031BE5C4150`.
- Both final report SHA-256 values: `8929F536C61D7E4ED0B8197E58123ABBBA117F05344C35779CE633218F1F8B62`.
- Source SHA-256: `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7`.

The final checker adds the exact four-instruction pause allocation at `7861E7`
and replaces one remaining-condition string with the explicit pause condition.
Removing that one predicate line and reversing that one string replacement
in memory reconstructs the entire previously reviewed checker SHA-256
`8C97744D317320446B45AD8A80F362018F2F957C8437931EE89292C1623A8458`.
The added predicate matches the original independently decoded instructions;
there are no other checker changes. Earlier `recheck.json` and `evidence-a.json`
remain historical outputs, not the final reviewed version.

This review does not enable the external Shoot route, approve the bounded
native clear for a wider domain, or replace an actual reached-camera proof.
