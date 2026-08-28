# WSC object-configuration conversion

## Evidence boundary

This record compares the clean Ver. 1.5 WSC ROM with the exact USA GBA ROM.
It is static conversion evidence only; no emulator or supplied-save claim is
attached.

## Stage table

The WSC twelve-entry table is at physical `0x744F2D` (logical
`4090:462D`). Each four-byte entry is `(resource-bank word, configuration
near-pointer word)`. The corresponding retail GBA table begins at ROM
`0x36D38C` and contains eight entries of `(32-bit bank, ARM pointer)`.

The WSC configuration pointers are:

| Stage | Bank | Near pointer | Meaning |
|---:|---:|---:|---|
| 0–7 | 2 | `0x4661` through `0x4741` | retail stages |
| 8 | 2 | `0x4781` | train |
| 9 | 3 | `0x47A1` | waterfall |
| 10 | 2 | `0x47D1` | Iraira Room |
| 11 | 2 | `0x47F1` | Digimon Shoot |

## Record rule

Every stage points to two consecutive 16-byte WSC records. The commercial
GBA conversion represents each as 20 bytes:

1. copy WSC bytes `0x00..0x0D` unchanged;
2. insert two zero padding bytes at GBA `0x0E..0x0F`;
3. replace the final WSC callback-table near pointer with a 32-bit ARM pointer
   at GBA `0x10..0x13`.

`tools/build_stage_integration.py` checks this rule independently for both
records of every retail stage before it converts any Ver. 1.5-only record.
The relocated GBA table at ROM `0x584C00` has twelve bounded entries and is
selected by a hook at `0x0836D2C0`.

## Native train entry

Stage 8 uses WSC physical `0x745081..0x7450A0`. Its two callback-table
pointers are `0x481B` and `0x481D`, which resolve to WSC functions
`4090:3CD5` and `4090:3D7B`. Static ARM translations are placed at ROM
`0x584E00` and `0x585000` and referenced through slots at `0x584D80`.

Commercial callback comparisons establish the field mapping used by both
translations:

| WSC object field | GBA object field | Use |
|---:|---:|---|
| `+0x26` | `+0x34` | X position |
| `+0x28` | `+0x36` | Y position |
| `+0x32` | `+0x42` | X velocity |
| `+0x34` | `+0x44` | animation/render result |
| `+0x36` | `+0x46` | secondary velocity |
| `+0x38` | `+0x48` | secondary accumulator |
| `+0x7E` | `+0x94` | animation frame |
| `+0x80` | `+0x96` | counter |
| `+0x82` | `+0x98` | timer/flags |

The translated callbacks retain the source direction flag, signed position
thresholds (`0x0F00`, `0x0C80`, and `0x1D00`), velocities, animation-frame
cadence, and object destruction calls. Stages 9–11 remain explicit temporary
analogs in v21 and are not claimed as native.

## Corrected waterfall interpretation

Stage 9's records at physical `0x7450A1` reference callback-table entries
`0x481F` and `0x4821`, whose functions are `4090:3DFB` and `4090:3EE0`.
They produce waterfall modes 1 and 2. The earlier v20 assumption that
`4090:3FCA` was a stage-9 initializer producing mode 3 was therefore removed;
the native stage-9 callbacks must be translated directly.
