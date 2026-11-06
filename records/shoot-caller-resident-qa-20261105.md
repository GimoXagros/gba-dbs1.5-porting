# Independent resident Shoot caller verification — 2026-11-05

The isolated A/B resident caller components pass independent source, actual-code,
ownership and whole-ROM inverse checks. This verifies two unconnected functions;
it does not establish a playable Shoot route, close terminal lifetime, or fix E5.
The main-build integration and its two fresh builds are separate checks.

The verifier imports no builder, assembler, producer profile, or producer proof.
It reads only ROM inputs and the supplied JSON manifest and writes its own JSON
report. It neither launches an emulator nor reads saves or writes guest memory.

## Actual source and consumers

Source raw `772553..77256E` reads `1000:005C`, compares its unsigned byte value
with 11, calls `71F0:1750` and returns for equality, and otherwise continues the
ordinary `0653` procedure. The complete instruction bytes and decoded branch,
far call, and return boundaries are checked independently. Retail stage code
`080B9E48` resolves its config literal to `03002310` and reads offset `0E`,
positively establishing the new router's owner `0300231E`.

Retail case-5 callback allocation resolves its actual literal to `0834059C`.
Both that ordinary callback and the original case-5 allocation remain byte exact.
The complete source controller `74A208..74A344` is guarded independently, and
all 64 native action-table tokens are inverted to the actual source targets.
Six retained SELECT/APPLY/table/lower/1750/ordinary-body spans are checked against
their previously verified exact fingerprints and against the actual output.

## Execution checks

A small strict ARM interpreter executes actual output words, rather than a
Boolean rewrite of the intended router. It supports only the reviewed ARMv4
instruction families and rejects unsupported instructions and uninitialized
RAM reads. The terminal router has **8,192 cases**: all 256 stage bytes, all
16 NZCV values, and two different CPSR control values. It must restore every
`r0-r12`, LR, SP and full CPSR before its tail destination. Only stage 11 reaches
`085CD000`; all other bytes reach `0834059C`. The only non-stack RAM read is
exactly one byte at `0300231E`; its adjacent byte is deliberately nonzero.

The interpreter also executes the actual controller and retained SELECT/APPLY
bodies in **8,960 cases**, with the existing RNG service modeled at its known
return/clobber ABI. These cover every difficulty byte and RNG low nibble, signed
difficulty clamping, all coordinate threshold partitions, forced/no-RNG cases,
both flag values, linked-object aliasing and HP halfword endpoints. All four
actions are reached. The checks require SELECT then APPLY, the same current
`r4`, three correct callback arguments, zero or one RNG calls as appropriate,
exact source-order writes, no adjacent object corruption, and restoration of
all `r0-r12`, LR and SP. Controller flags remain scratch under its existing ABI.
Only three literal loads intervene between the two calls in its complete code.

## Ownership and containment

The independent census scans the complete exact predecessor for pointers at
every byte alignment through the `08/0A/0C` mirrors, ARM B/BL/literal/ADR, and
Thumb literal/ADR/unconditional/conditional/BL/BLX references. It finds no
incoming references to either actual inserted span and uses no interior/data
exemption. Both spans are all FF before writing:

| Raw span | Declared bytes |
|---|---:|
| `5C6500..5C652B` | 44 |
| `6FC300..6FC333` | 52 |

Restoring only those **96 declared bytes** reconstructs the complete exact v67
predecessor; **90 bytes actually change**. This also proves that external scene,
display, progress, damage and controller hooks remain unchanged. The controller
boundary at `085C0A00` remains the original `BX LR`.

**35 direct negative controls** bypass top-level identity rejection and exercise
the checks themselves: missing calls, wrong family, lost r4 restore, stage access
width/address/predicate/branch, each flags restoration, both tail destinations,
source predicate/table changes, mirrored pointers at all four alignments, and
nine ARM/Thumb reference forms. None is accepted. Manifest allocations, hashes
and scope are cross-checked only after the independent actual-image checks.

## Reproduction and frozen artifacts

```text
python tools/verify_shoot_caller_resident.py BEFORE AFTER GBA WSC15 MANIFEST --output JSON
```

A/B ROM and manifest inputs are in `build/shoot-caller-resident-20261105-{a,b}`.
Independent reports are
`build/shoot-caller-resident-qa-20261105/independent-{a,b}.json`; their bytes match.
The verifier source has LF line endings and passes Python compilation.

| Artifact | SHA-256 |
|---|---|
| v67 predecessor | `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F` |
| Resident caller ROM | `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738` |
| A/B producer manifest | `58BD404A3EB33583F2EF23D02D265AE031C7946BBCE66B88330A188557EA0351` |
| Independent verifier | `7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D` |
| A/B independent report | `B079E66FA7DE910679E6D83539F8EAABF2BD1642A4B65D98F7140D10B67062F5` |

The interpreter is a bounded static execution model, not emulator or hardware
evidence. The RNG service recurrence itself is a retained earlier proof rather
than re-executed here. Neither tail body is executed by these router checks;
their identities and register-preserving entry conditions are verified. The
external route and complete terminal/spatial/IRQ lifetime remain separate work.

## Final main-build and runtime audit — 2026-11-06

Fresh full builds `build/repro-v68-20261106-e` and `-f` independently pass
complete relative-path and SHA-256 inventory comparison: **271 files each**,
with no missing, extra or differing file. All **108** manifest asset/ROM
entries per build and all three original ROM hashes were recomputed.
The audit imports no main builder or component producer. Its checks bind
main source `2C32FA2D…BD17687` and the unchanged frozen independent verifier
`7CDD6E52…9977DE5D` before reading the completed build artifacts.

Both actual `result-language.gba` images equal both complete previously
verified v67 predecessor files, SHA-256 `A4CB752A…85328F`. Both actual final
images are `9E22BCAD…2EF738`. Restoring only the two declared FF spans,
96 bytes total, reconstructs that exact complete v67 image; 90 bytes really
change. A direct outside-span mutation is rejected by the full-image inverse
without relying on a top-level digest gate. These bytes also prove that the
external scene/progress/controller hooks and terminal boundary remain closed.

The frozen verifier was rerun separately against each actual main-build
predecessor, final image, original GBA/WSC and caller manifest. Each output
is byte-identical to its corresponding main-build verification report and
the original frozen `B079E66F…7062F5`: 8,192 actual ARM router cases,
8,960 controller/SELECT/APPLY cases and 35 direct semantic negatives each.
Complete inventories were rehashed after these reruns and remained unchanged.

Root's separate hidden Korean ordinary-WIN capture on exact `9E22` was
also rerun through the updated capture verifier. The independent report is
byte-identical to root's `60504795…E54DF`: 61 capture files, eight snapshots,
and all 1,508 visible label pixels match. The verifier accepts this image
only after its complete 96-byte inverse produces the exact v67 result image.
Independent one-byte mutations inside caller code at raw `5C6500` and outside
at raw `001234` both fail before any capture-file read (verified with a read
trap). LAST CHANCE was not observed; this was an ordinary WIN regression,
not Shoot gameplay or a fresh-process save-persistence test.

| Artifact | SHA-256 |
| --- | --- |
| Canonical full inventory/inverse audit, `build/repro-v68-final-audit-20261106/audit.json` | `7512E3880FA0D60C2B38D8C8A8F1084966CEBE4D531C8C0139A8EDF317D82541` |
| Independent KO runtime/gate audit, same directory `ko-runtime-audit.json` | `D4BDCFD207F2A24547B6F00E8BD686E7E52D7A3B84505B2F6CEFB825BDFE0D7D` |
| Independent KO capture report, same directory `ko-runtime-verification.json` | `605047952C869EF50C10D724AED8DA066987CDE7EEE72FAB4A69D2EC097E54DF` |
| Current capture verifier | `CFCEECDACF375965F81E29B7A06EAEAC8BFF66507621211D24BEA5F4E20F1ECA` |

This reviewer launched no emulator, accessed no supplied save, wrote no guest
memory, and modified no ROM or builder. The interrupted old c/absent d builds
are not used as completed evidence. The exact v68 artifact is reproducible;
playable Shoot, reached terminal/spatial/IRQ/storage lifetimes, original E5,
remaining content/localization and whole-port completion remain separate work.
