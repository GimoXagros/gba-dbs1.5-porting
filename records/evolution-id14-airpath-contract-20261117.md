# ID14 airborne-return discriminator

This is a source/native contract for a new ordinary-input observation, not an E5 fix or observed airborne result. The v78 production image C91E8EE2 remains unchanged.

## Lifetime and actual branch

Source74356F..7435A8 decrements actor+56 while actor+8 bit4000 is set. Only signed negative expires; zero remains active. Actor+A bit1000 and actor+6 bit20 block the return callback668E:C6F (source ROM76754F).

Native0835A3D0/D4 initializes actor+6A to600. Common update08352FB8..FD8 increments shared byte030048BA by40, subtracting1 plus carry from this signed lifetime. Negative lifetime with the corresponding blockers clear installs0835A4BC at08353028/2C. Scheduler083525BC/C4 executes the current callback before the common update at083525E8. Expiry therefore schedules the return for the next eligible callback.

The return routine clears velocities but preserves actor+6 bit0. Instructions0835A544..550 use that bit to select ground or air. Observe the actual table register and selected event at0835A558: old ID14 air uses0835A596 and signed FFFFE3A0; the repaired table uses08D3F03C and25. Merely visiting the conditional ARM instruction0835A550 does not prove its condition passed.

## One ordinary input attempt

After seeing the same valid evolved P1 ID14 with lifetime above48, open a window at47..48. Fire once if the actor is idle0835620C, ordinary kind0, linked to its real opponent, evolved bit4000 set, actor+6 bits61 clear, actor+A bit1000 clear, A previously released, mode7, and gameplay pause byte03004529 low nibble clear. Eligibility may arrive at47 after an ineligible48. Falling below47 before firing is a missed attempt, not permission to retry or change the timer.

Press only A for20 outer frames, then release for at least one. Native idle0835620C first tests attack/down/drop-through; with only A, those decline before0835624C→0835582C consumes fresh edge actor+2E bit40 and installs jump callback08356B78. Held A is actor+2C bit40.

The earlier “16-frame preparation” shorthand refers to an initial counter, not a mandatory delay. Preparation calls08356C10 each update; takeoff depends on presentation+A bit2000 and sets airborne at08356C54/C5C. Evolved ID14 P1 is0861DB48; event4 row0861DB90 contains two commands0861DE90/DEA0, durations2/3, flags0. Animation tick finishes after six ticks, allowing takeoff on the following preparation callback when uninterrupted. Evolved physics084851F4 uses velocity/gravity(-1011,25); the rookie parameters do not apply here.

Gameplay pause is03004529: Start sets bits01/02 at08375278..284 /083752AC..2B8, pause UI sets08 at083753CC..3D8, actor-update gate08352598→08352B10 tests07, and resume08375718..728 clears03|08 before music resume0837579C. The unrelated03004506 bit80 is stage-music eligibility.

The proposal leaves at least24 eligible decrements before expiry even under carry on every update. It does not promise a universal frame count or airborne success: hits, terrain, and callback interruptions remain possible. Actual air-selected state and the existing paired collision metadata/dispatch witnesses decide the result. No E5 observation means the historical E5 producer remains unproved.
