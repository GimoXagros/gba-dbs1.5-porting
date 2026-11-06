# Shoot synchronous resident callers — 2026-11-05

This component adds actual controller and terminal-entry code over exact v67.
It changes no external hook, task allocation, damage hook, display router, or
controller boundary. It does not claim that the complete Shoot path is ready.

## Missing source continuation

Source `71F0:0653` at raw `772553..77256E` reads the stage byte and compares it
with 11. For stage 11 it calls `71F0:1750` and returns; every other value continues
into the ordinary result procedure at `77256F`. The retained retail callback
`0834059C` starts that ordinary procedure directly, with its countdown and object
cleanup. It contains no corresponding stage-11 branch.

The existing gated scene-route draft therefore needs more than its initial
Shoot predicate: its default callback must be the new terminal-entry router,
not `0834059C`. The stage test belongs at callback execution, as in the source.
The initial predicate still excludes stage 11 from starting a new Shoot scene.
No second task or immediate call during allocation is needed.

## Emitted code and ownership

| Entry | Bytes | Effect |
|---|---:|---|
| `085C6500` | 44 | Call real SELECT, load three real lower callbacks, call APPLY in the same invocation |
| `086FC300` | 52 | Stage 11 tail-calls resident `085CD000`; all other stage bytes tail-call retail `0834059C` |

The controller uses the same `r4` object for both operations and preserves
`r0-r12`, LR and SP; its flags remain scratch under the existing controller ABI.
Only three literal loads intervene, so there is no game update between decision
and assignment. All callback targets and the complete lower family are pinned
to the previously verified resident bodies. The action-3 parent assignment is
already implemented by APPLY; no extra parent callback is fabricated.

The exit router saves `r0/r12/LR`, tests the real stage byte at `0300231E`,
restores flags and registers on both branches, and tail-calls the selected body.
Its stack is balanced before either target runs. Resident `1750` already does
its source same-update fallthrough to `17DF`.

Both actual spans are FF in the complete exact predecessor and pass the existing
conservative all-alignment mirrored-pointer and ARM/Thumb branch/literal/ADR
ownership scan with **no exceptions**. Proposed nearby exit slots `5C6540` and
`5C65C0` were rejected because the scan found existing Thumb-like destinations;
those words and destinations are preserved, without classifying them as data.
All enclosing gaps and external hooks are unchanged by whole-ROM inversion.

## Reproduction and checks

`tools/build_shoot_caller_resident.py` accepts:

```text
BEFORE GBA WSC15 OUTPUT --manifest JSON
```

It refuses existing outputs before reading inputs. The actual source exit
instructions, original identities, resident SELECT/APPLY/lower/terminal body
hashes, retail ordinary callback and case-5 allocation owner are checked. Both
emitted instruction sequences are decoded completely; ARM status-register
reserved bits are checked separately. The 256-byte-valued stage cases preserve
exact equality with 11. Nine semantic mutations are rejected, covering missing
SELECT, wrong family, lost register restore, access width, stage, branch, flags,
terminal destination and stage owner. This is builder-side checking; an
independent review remains a separate step.

A/B output directories are `build/shoot-caller-resident-20261105-a` and `-b`.
Their ROM and manifest bytes match. There are 96 declared bytes and 90 changes.

| Artifact | SHA-256 |
|---|---|
| v67 predecessor | `A4CB752A8E0CFA3D639E645531B5AFCCB0CE25DD3BF202F62FE132E97385328F` |
| Resident caller ROM | `9E22BCAD6078BB5653FF62F12798E7365D7AB75B434298E9DA7F4BF4A72EF738` |
| Manifest | `58BD404A3EB33583F2EF23D02D265AE031C7946BBCE66B88330A188557EA0351` |
| Builder | `DB5C7573D5F12EDB28328D530ECD79EA4E9E50E1464BC6CFC810F7477B8654CB` |

## Connection contract

The future complete route must bind its default callback to `086FC300`, connect
`085C0A00` to `085C6500`, retain the existing initial scene predicate, connect the
source damage branches, and install a proven transition display/IRQ path.
Opening only the initial scene entry cannot be described as a robust ordinary
route: normal play then reaches these controller and terminal dependencies.

The remaining concrete contracts are terminal `197A` live-BX destination,
final IRQ visibility while rows and common tile zero remain preserved, and the
separately assigned player/lower spatial lifetime. Distinct SRAM writes already
remain distinct in EEPROM block 25; hypothetical unidentified readers are not
an extra invented prerequisite. No forced entry, clamp, fallback, rollback,
emulator launch, supplied save access or guest write was used.

## Separate independent verification

The separate reviewer completed `tools/verify_shoot_caller_resident.py`, SHA256
`7CDD6E52B069FD50C8607E0FAD3DBF2A51835338429668CF7343BC5E9977DE5D`.
Its A/B reports in `build/shoot-caller-resident-qa-20261105/independent-{a,b}.json`
are byte-identical, SHA256
`B079E66FA7DE910679E6D83539F8EAABF2BD1642A4B65D98F7140D10B67062F5`.
It imports no builder, independently checks strict ownership/full inversion and
the source64-entry action table, and uses a bounded host ARM interpreter for
8,192 exit-router and 8,960 controller-plus-SELECT/APPLY cases. Thirty-five direct
negative controls are rejected. This is static component verification, not an
emulator or gameplay test, and does not open the documented external gates.
