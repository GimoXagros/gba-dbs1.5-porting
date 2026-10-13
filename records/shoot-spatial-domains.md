# Shoot spatial route gates — frozen source evidence

This appendix freezes the remaining camera and pursuit coordinate proof after
the v53 checkpoint. It changes no ROM, frozen builder, lower callback, terminal
callback, or main build pin. The analysis uses only the original USA GBA and
WSC 1.5 ROMs; no save file or emulator was used.

Reproduce from the repository root:

```text
py -3 tools/analyze_shoot_spatial_domains.py <USA.gba> <WSC15.wsc> --output build/shoot-spatial-gates-20261013/report.json
```

The analyzer checks both full input identities and 15 source/native byte-range
guards. It enumerates all 65,536 inputs to the source clear operation, completely
decodes the bounded terminal and stage-manager functions, and records the
remaining proof obligations. A PASS confirms these finite checks; it does not
close either gameplay route gate.

## Terminal camera and row clear

Source `71F0:19C6..19D7` (raw `7738C6..7738D7`) sets ES=0, computes
`DI=(0800+((BX<<6)&FFFF))&FFFF`, and stores 64 zero halfwords with 16-bit DI
wrapping. Across every 16-bit BX value, this yields 1,024 distinct starts and
covers all 32,768 source halfword addresses.

| Mathematical BX input | First address | Consequence of the source operation |
| --- | --- | --- |
| 0 | 0800 | First mapped screen area |
| 63 | 17C0 | Crosses the end of the currently bounded screen area |
| 224 | 4000 | Reaches a graphics owner |
| 480 | 8000 | Reaches another graphics owner |
| 736 | C000 | Includes current-task metadata at C008 |
| 984 | FE00 | Reaches the palette owner |
| 991 | FFC0 | Wraps through address 0000 |

These are arithmetic witnesses, **not evidence that gameplay reaches those
inputs**. An unrestricted tilemap-only GBA projection cannot preserve all these
effects. Closing the gate requires either the actual reachable input domain or
a complete mapping and ownership argument for every reached source owner.
The existing native clear remains bounded to camera Y values `0..62`.

The concrete producer is `4FFF:376D..377F` (raw `75375D..753771`): BG+12 receives
the 16-bit result of `pageY*144+inPageY`. Its unit is pixels, rather than a tile
row masked to 31 or 63. Input callback `4090:07D6` leaves BX as source
`1000:01E0` (BG0+12) and copies the value to `0C00:3A16`; the paired native
snapshot is `0300451E`. Root case 5 installs this input callback and a scene
task at priorities `0F00` and `0FF0`. Dispatcher `4FFF:B53..B81` preserves BX
across its bookkeeping, but the complete intervening-task/IRQ lifetime and
the terminal-entry value range are still unproved.

Initializer Y=0 is insufficient: source `155F` restores full input `4090:07FA`
and battle `4090:0D0B`. Shared camera paths at raw `7413C3..741419`,
`741543..74159D`, and `7416EE..741748` use fighter movement and call camera
helper `3367`. Stage dimensions alone therefore do not establish the terminal
live-in value.

## Terminal flags do not establish a general movement freeze

Complete direct flag-write inspection of terminal `1750..1E22` finds no clearing
of Shoot flag `0800`; this is a bounded function result, not whole-program flag
ownership. Battle callback `0B8B` and object wrapper `1899` gate their work on
`03CD` low three bits. The identified `03D4` bit `10` tests at raw
`742FCE/742FEA` and `743C59/743C8A` suppress conveyor displacement, rather than
all object or camera movement. Thus common flag `10` alone does not close the
camera/refill lifetime gate. This appendix makes no claim about the unresolved
`0DEC` IRQ path.

## Lower pursuit callback 8EF3

The frozen native lower callback retains the domain
`signed(currentX)<1E00` and `signed(capturedTargetY)<=1B00`. Source `8CDD`
copies target X and clears velocities/accelerations. `8D84` and `8E27` follow
target X using velocities `+/-0180`; `8DA9` captures target+28 into lower+8C,
and `8E27` clears X velocity before `8EF3`. These local producers do not prove
the complete bounds on target position, current position, or other displacement
writers.

The common world-limit producer at raw `740E28..740E47` shifts stage dimensions
left by four into `0C00:3A18/3A1A`. Its native counterpart
`080D1A70..080D1A94` writes `03004520/03004522`. Complete decoding of Shoot
manager `36C0..37C6` finds no direct dimension/cache access and only the two
resource far calls `4FFF:226E` and `4FFF:2389`. It therefore supplies no direct
cache-refresh proof. A literal-reference scan over raw `740900..79FFFE` found
the two direct cache stores at `740E41/740E44`; this does not exclude indirect
writers. The cached-height consumer at `743B6D/743B7B` releases an object beyond
the limit; it is not a clamp to `1B00`.

The remaining requirement is to identify the actual P1 collision and position
consumers, establish the relevant cache lifecycle, and cover all follower
displacements. Initializer positions or stage dimensions cannot substitute for
that proof. Neither a reachable invalid gameplay state nor unrestricted
equivalence has been established. Both coordinate gates remain open, and their
existing guarded implementations remain unchanged.
