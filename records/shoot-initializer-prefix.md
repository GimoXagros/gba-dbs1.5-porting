# Disconnected Shoot initializer prefix (2026-10-26)

The bounded source prefix `4090:7168..71D1` is now installed at native
`08629700`, with no external caller. It composes the existing IRQ/display and
dedicated graphics services with the source-ordered timer/flag/manager work.
This does not install the complete initializer or make Shoot playable.

## Frozen inputs and artifacts

The predecessor is the native port checkpoint
`build/stage-priority-routing-20261023-a/current-candidate.gba`, SHA-256
`389F56FF566EDB139729DCC51AEED56A807C502A3FBEEDC037A218041EABD7F1`.
The separate result-language candidate is not a prerequisite. Existing options
and title language content in the predecessor is retained byte-for-byte.

- Builder: `tools/build_shoot_initializer_prefix.py`.
- Independent verifier: `tools/verify_shoot_initializer_prefix.py`.
- Two builds: `build/shoot-initializer-prefix-20261026-a` and `-b`.
- `current-candidate.gba` SHA-256:
  `4BA39E7EBBBE3AA41AEFFC2FFAA3B5BB038694301B58F0F5FE45714485B4C7FC`.
- `manifest.json` SHA-256:
  `DCEF1A1C3BB72F9F1285E52A5AA034FC88441E1C718822409CBAC5507D7EFE54`.
- `verification.json` SHA-256:
  `58B559ADDB89ED4279A000447E276FDAAE68F0C90EBB4A6D5345E3B6C7F05BEB`.
- All three relative paths and hashes agree between the two builds.
  `build/shoot-initializer-prefix-20261026-comparison.json` SHA-256:
  `F0A4AFF91E5E8353F5837C7AF67C28AB5DAB41ED653CB00FC340E6C070715882`.

Only the erased range `[629700,62975C)` is written: 20 ARM instructions and
three local literals, 92 declared bytes and 89 changed bytes. Restoring this
range reconstructs the entire exact predecessor. No existing instruction,
resource, entry point, pointer, or RAM allocation is changed.

## Source order and native contract

The actual source bytes `[747A68,747AD1)` have SHA-256
`DB1395FB28D6E4EEB226D1189145B62403F3E440880070F4ED7D8793B66093C5`.
All 37 source instructions, including the source prologue and the next phase's
segment setup, are decoded independently. Source segment setup is represented
by the established native address owners rather than new mutable segment state.

| Order | Source effect | Installed native effect |
|---|---|---|
| 1 | `7176..718D` IRQ/display preamble | Call `085C7200` |
| 2 | `ES1000:005C = 11`, one byte | `0300231E = 11`, one byte |
| 3 | Far call `7CCF:0FC4` | Call dedicated graphics `085C6800` |
| 4 | `DS1000:03CE = 18000` | `03004500 = 14400`, halfword |
| 5 | Clear `03D4`, `03D6`, `03D8` in order | Clear `03004506`, `03004508`, `0300450A`, halfwords |
| 6 | OR `03D4` with `10` after all clears | Store `0010` to `03004506` |
| 7 | Far call `4090:36C0` | Call existing manager `0836D224` |

The OR is equivalent to the installed store because the same ordered prefix
has just cleared that field. The old `085C4300` component remains unchanged
and uncalled: calling it here would store stage 11 again after graphics.

The timer is derived from actual commercial producer/consumer lineage:
`18000 / 75 * 60 = 14400`. The verifier compares the complete old/new source
timer producers after the five established global relocations, both source
HUD divisors, the native producer, the native HUD divisor, and the native
halfword decrement at `0837500C`; its owner literal is at raw `375170`.

Entry has no arguments. It saves `r0-r12` and LR in a 56-byte frame, sets
native service register `r11` to zero, and restores all saved registers and
SP before returning. Flags may change. The existing preamble and graphics
entries preserve registers; the manager is allowed to clobber all work
registers within the prefix's saved frame. Ordinary initialized native
globals and exclusive scene/display ownership remain preconditions.

The predecessor retains the independently checked graphics/preamble family,
the old timer subset, the stage-manager body, and the private stage getter.
The existing graphics verifier rechecks its reviewed code/literals and source
resources. All 256 character-byte values with actual stage 11 reach stage 11
through the private manager getter. This does not alter the shared getter's
other users.

## Independent verification

The new verifier imports no builder, converter, or build manifest. Its only
project imports are the existing independent graphics and stage-priority
verifiers. It reads actual source instructions, derives the effect sequence,
then checks the final ARM instructions, three owned literals, and full-ROM
inverse independently of payload generation.

- 128 bounded ABI/effect cases cover all 16 incoming NZCV combinations, two
  stack alignments, and four incoming `r11` values; all restore the complete
  caller register frame and match the source effect order.
- Whole-ROM scans cover every pointer byte alignment, the `08/0A/0C` ROM
  mirrors, interior addresses, ARM branches/literals/ADR, and Thumb
  branches/literals/ADR/BL/BLX. The predecessor has no reference into the new
  range. The result contains only its three internal literal references.
- 122 independent artifact/source/owner mutations are rejected, including
  every byte in the installed range and reordered clears with identical
  final values. Another 57 negative controls exercise the reference scanner.
  Total: **179**. The builder's separate self-check rejects 41 mutations.
- No emulator, supplied save, live IRQ scheduling, hardware timing, or game
  service was executed. Bounded instruction effects use the documented
  retained callee contracts.

## Reproduction

Run from the repository, using an unused output directory. Replace `-a` with
`-b` for the second build and verification.

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/build_shoot_initializer_prefix.py `
  build/stage-priority-routing-20261023-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-prefix-20261026-a/current-candidate.gba `
  --manifest build/shoot-initializer-prefix-20261026-a/manifest.json

& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/verify_shoot_initializer_prefix.py `
  build/stage-priority-routing-20261023-a/current-candidate.gba `
  build/shoot-initializer-prefix-20261026-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-prefix-20261026-a/verification.json
```

## Next bounded contract and open gates

The next source unit is `71D1..7394`, represented by the resident player phase
`085C1000`. A disconnected ordered composition can call this prefix followed
by that phase, retaining zero `r11` inside its own preserved register frame.
Before implementing that composition, review and guard the current player
phase, its now-updated resource pointers, and auxiliary reuse
`085C1300 -> 085BC244` against their actual source/native consumers.

Its preconditions are the existing three valid object handles at
`030048A0`, `0300489C`, `03004D3C` and the other character ID in `0..14`.
The inherited case-5 cleanup only releases pool-0 list objects; the two
players and auxiliary use pools 3, 4, 5 as recorded in
`records/shoot-scene-object-pools.md`. This bounded survival proof does not
authorize arbitrary scene entry or prove an entire new transition lifetime.

Full initializer `085C7800`, external scene/controller callers, source SRAM
`1000:3CD8/3CDA`, terminal interrupted-DI behavior, camera lifetime, and the
remaining initializer/tail ordering remain open. The native manager is not
an allocator for the three existing player/auxiliary objects. No external
hook or complete Shoot claim is made by this layer.
