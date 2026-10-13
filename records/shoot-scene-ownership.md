# Shoot scene task ownership

Recorded 2026-10-13. This is a bounded source/native lifecycle proof, separate
from the frozen v51 ROM layer graph. No new scene caller is installed by this
work. No emulator, runtime execution, or save access was used.

The root review also compared every GBA evidence range below against exact v51
`726DA3D80AD498232F043B659A8268D312B2368FF542B497BFD16C12EE2B7284`.
All match the retail source except the existing four-byte stage-setup mapping hook
at raw `377B18`. The bootstrap callback restoration/retirement at `377B54..377BB8`
is unchanged. This compatibility check does not prove arbitrary task-list state.

## Result and exact boundary

The retail task lifecycle supplies a concrete way to keep the known pause and
other scene capture paths out of Shoot's palette interval. It is conditional
on normal battle entry and one active transition owner. It does **not** make
an arbitrary call to the initializer safe.

The common native scene root at `0833FC28` replaces the input task and the
battle task before allocating its scene. Source `71F0:0000` does the same.
The input callback used for source case 5 has no pause dispatch, and the
battle replacement removes the normal match-end scene producers.

| Handle | Source scene callback | Native scene callback | Normal callback restored later |
| --- | --- | --- | --- |
| `1000:03DE` / `03004510` | first `4090:0769`, then case 5 `4090:07D6` | first `08374EFC`, then `08374FAC` | `4090:07FA` / `08374FF4` |
| `1000:03E0` / `03004514` | `4090:0B8B` | `0837354C` | `4090:0D0B` / `083735BC` |

Native replacements occur at `0833FCA0`, `0833FCC4`, and `0833FCFC` through
`08011E7C`. That helper only stores the supplied callback at `task+0`.
The scheduler at `08011DCC..08011DD8` reads that field and calls the current
callback before continuing its task-list traversal. The scene input callback
`08374FAC..08374FE0` has one callee, `08353B48`, which only clears three byte
counters. Its remaining stores clear `0300482A` and copy input halfwords into
`0300451C/1E`. It does not invoke either pause entry call.

The normal battle producer at `083736B0` passes `03004529 & 7 == 0`, requires
mode word `03004502 == 2`, and takes the second player's nonpositive HP path.
It calls the scene root with argument 5 and returns through `083738D4`.
The root changes that battle task to `0837354C`, whose bounded body contains
none of the four normal battle calls to the scene root. This prevents the
same normal battle callback from repeatedly allocating the transition.

## Source capture through task retirement

Source case 5 selects Shoot's `71F0:0EEA` only when stage is not 11 and either
difficulty is 3, or difficulty is nonzero and progression word `0068` bit
`0400` is clear. These are equality tests on the original byte values. The
other case-5 branch chooses `0653`; neither condition may be discarded by a
future native entry adapter.

The analyzer decodes the entire `0EEA..15A9` lifecycle and checks all thirteen
current-task callback assignments and all twelve initial writes to its
`+42` phase counter:

`0EEA → 0F67 → 0FC3 → 1043 → 10DD → 11F7 → 1267 → 12C6 → 1331 → 139C → 13F4 → 1434 → 1486 → 1540`.

The `0F67`, `1043`, and `11F7` entries also execute by immediate fallthrough
in the invocation that installs them. Counts describe callback executions;
they do not justify adding an extra frame between those phases.

- `1043` calls the complete snapshot at `1073`, then performs the destructive
  black fill at `1082`. The temporary `+42=100` write at `1069` is overwritten
  with 6 at `10B1` before installing `10DD`.
- `10DD` waits on presentation events. Its final path enters the 32-call
  `11F7` white prelude immediately. At the end it invokes the source audio
  reset `4FFF:50F2` and the ordered initializer `4090:7168` at `1243`.
- `1267` executes 32 alternating half-palette decrements. It then initializes
  `12C6` to 150; after decrement to 130, the source attempts sound D2/type 2
  if its sound command slot is available.
- `1331` executes 32 alternating half-palette restores from the saved target.
  The last restore precedes the player flag change at `1378` and installation
  of `139C`. The mirror dependency ends here.
- Later event and HP-count phases retain both scene task callbacks. Only at
  `1574` and `158A` does the source restore normal input and battle callbacks.
  It then retires its own current task at `15A0` through `4FFF:0A32`.

The native task-state base is `task+18`, compared with source `task+10`.
Native `08012030` retrieves the current task from `0300133C` and calls
`08011BE4`; the latter clears task status at `+10`, decrements the live count,
and unlinks the node. The existing match-start sequence already uses this
restore-then-retire pattern at `08377B54..08377BB8`.

## Known owners, and what the proof does not establish

All aligned words in the exact USA input were checked for direct ARM B/BL
encodings to the named roots and for exact literals to the two task handles.
This is a finite reference population, not an exhaustive indirect-reference
proof.

- The only direct calls to pause capture `08375360` are `08375298` and
  `083752CC`, inside the full input callback replaced above.
- All five calls to common capture `0833FDC0` are in the retail common-scene
  family: `08340110`, `083403BC`, `08340728`, `08340C18`, `08340EC0`.
  A new Shoot scene must replace the selected existing scene, not coexist
  with it.
- Four of the six calls to scene root `0833FC28` occur in normal battle
  callback `083735BC`. The remaining two are pause-exit case 1 at
  `0837574C` and a separate startup/cutscene case 3 at `08378510`.
  Those require the explicit no-other-live-owner entry invariant; this
  record does not infer their absence from a palette flag.
- The bootstrap mirror write at `08377928` belongs to a start sequence that
  restores both normal callbacks and retires its task at `08377BB0`.
  A normal completed startup is an entry precondition, not a proof for
  arbitrary task-list contents.

`08011AC4` allocates a free task and inserts it by priority. It **does not**
deduplicate equal priorities. Input priority is `0F00`, scene priority `0FF0`,
and battle-update priority `6000`; these are ordering facts, not a lock.
Display word `03D4` bit 2 is still not a pause guard.

The smallest identified native connection point is the existing case-5
scene allocation at `0833FD18`. Its callback literal at `0833FDB4` currently
selects `0834059C`. A future complete adapter must preserve the source
case-5 branch conditions, install the translated `0EEA` scene in that one
allocation, retain both scene callbacks until the source exit, and retire
the scene. Calling `7168` alone or adding a second `0FF0` task does not meet
the ownership contract. No such connection was made here.

Remaining content gates include the full scene presentation/event callbacks,
ordered initializer with resource-backed constructors, the remaining lower
controller families, exact sound reset/scheduling, and the final restoration
and task-retirement adapter. Resident rules, palette operations, and resource
adapters do not satisfy these gates by themselves.

## Reproduction

`tools/analyze_shoot_scene_ownership.py` checks sixteen fixed source/native
evidence ranges, decoded ABI and timer/phase contracts, and seven semantic
mutation negatives without executing either ISA. Negatives cover wrong input
and battle callbacks, missing retirement, a bypassed pause gate, wrong source
restoration, wrong fade count/parity, and a source task that fails to retire.

Run from the repository:

```powershell
py -3 tools/analyze_shoot_scene_ownership.py `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  --output build/shoot-rules-20261013/scene-ownership.json
```

Report SHA-256:
`5F9323F4641873B03A6187EFF37FF3F1C559E46D028F0CA2887EF2E938ECA291`.
The 1.0 WSC input is identity-checked for the shared project profile; the
specific lifecycle evidence in this report comes from 1.5 WSC and USA GBA.
