# Shoot initializer front through source 73E2 (2026-10-26)

The existing disconnected entry `08629800` now performs the proven prefix,
player binding, OBJ-slot-5 palette load, and the exact `0660` halfword clear.
It covers source `4090:7168..73E2` with the end excluded. The next instruction,
`73E2: mov word ptr es:[3CD8],0`, is the first unresolved SRAM gate and is not
implemented by this layer. No external scene/controller entry is added.

## Frozen artifacts

- Builder: `tools/build_shoot_initializer_front.py`.
- Independent verifier: `tools/verify_shoot_initializer_front.py`, SHA-256
  `39652942A0E480C7B08016F7E2B8CC93046A1163F29572490096AA3A9A3244CD`.
- Exact predecessor: `build/shoot-initializer-player-chain-20261026-a/current-candidate.gba`,
  SHA-256 `2C9C96129EBECF30FCB915E077899CE91FBA979F4AC44C027EE39F4C9A8C4BC7`.
- Outputs: `build/shoot-initializer-front-20261026-a` and `-b`.
- `current-candidate.gba` SHA-256:
  `CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7`.
- `manifest.json` SHA-256:
  `10F1C6A0CC75C74EA8FD526A31BBB14373E11A26A00B0C73217027F134CCCDE0`.
- Independently produced `verification.json` files in a/b both pass and have
  SHA-256 `471C31326FEE5FDCD2BD7841FB227082EE38D8CAB782AD6EA967C27C7C9C881F`.
- Both ROM and builder manifest match between a/b. Comparison report
  `build/shoot-initializer-front-20261026-comparison.json` SHA-256:
  `3C0E60EDA815824EAEBC9330EE226F87228A233AD757150AA39A16111D225A9D`.

The result-language candidate is not a dependency. Earlier frozen prefix and
player-chain artifacts/builders are preserved. Main-pipeline integration is
the coordinating task's separate responsibility.

## Consolidated continuation contract

The newly covered source bytes `[747C94,747CE2)` are 78 bytes / 24 x86
instructions, SHA-256
`D3BB949DFAC1F1281974822C5A60CEB156FF8BA65226FBFC5E0386CAD32BE2E9`.

| Source interval | Native representation |
|---|---|
| `7394..73A9` | Call existing `085C1700` to load the slot-5 palette |
| `73A9..73D6` | Retain the already-installed source-identical P0 resources and their dynamic renderer consumers; no new initialization call |
| `73D6..73E2` | Call existing `085C4400` to clear only native halfword `030048A4` |
| `73E2..73F0` | Unresolved `ES1000:3CD8/3CDA`; not crossed |

`085C1700` passes native entry-stack arguments
`[5,0,0,0,085DB740]` to `080132EC`. The source P2 at `3D7A90` inverses
exactly from its native 40-byte representation. The actual loader writes
15 halfwords to `050002A2..050002BE`, retaining color zero at `050002A0`.
Its entire 14-instruction adapter and local literal remain unchanged.

The two P0 preloads resolve to `3D44E0` (tile identity `006D`) and `3D0CA0`
(`0137`). Their existing native P0 headers are `085DB300/085DB400`, and
later constructor adapters `085C4500/085C4600` preserve those identities
and their actual P1/P0/P2 argument roles. Existing lower callbacks already
call these adapters at `085CC3F8` and `085CC278`, respectively. Calling the
constructors during this initializer interval would create effects absent
from the source interval and is not done.

Both P0 flags are `0008`. The descriptor-index mask `0002` is clear, so their P1 word2
values do not index multiple descriptors: each uses its sole descriptor 0.
Independent checks reverse all 768 and 1,568 tile bytes, all 8 and 18 layouts,
and 106 bounded layout tile reads. All 15/20 actual P1 items select valid
layouts; their command, A/B and per-item tail data also match the source.

The actual native constructor stores resource pointers at presentation
`+44/+48/+4C` and tile identity at `+14`. P1 flags zero OR P0 flags eight
select dynamic draw entry `03000204`. Native startup at `08000160..19C`
copies 0x180 bytes from `08012C58` to `03000200`; the callable entry skips
the copied push because the dispatcher has already saved the same frame.
The complete copied extent and return/literals are retained, not only a
prefix ending before the final `BX LR`.

The draw routine reads P0 through presentation `+48`, chooses descriptor 0,
and copies 32-byte layout tiles into `02000000 + dynamic_index*32`. OAM uses
that same dynamic index. The bounded routine never reads presentation `+14`
to select a fixed tile destination. Thus source preload availability is
represented by the immutable resident resources and their actual native
consumer; no fixed-VRAM upload, new renderer, or claim of identical upload
timing is introduced.

## Exact 0660 owner and first hard gate

Source `73D6` loads ES=`1000`; `73DB` clears only `ES:0660`, ending at
`73E2`. The second indexed source reader at raw `766ECD..766EEE` selects
ES=`1000` and reaches this base without an intervening call or segment
reassignment. The native producer `08352B44` and indexed readers
`08352DCC/08355EF0` obtain exactly `030048A4` from literals at raw
`352CC8/3530A4/355FE4`. Their current instructions match the retail input.

The first source indexed-reader family also has an alternate ES-reselection
path. Its initial ES=`1000` assignment alone is not evidence that every path
retains that segment. The unambiguous second reader is the source-domain
anchor; the first/native indexed counterpart provides bounded corroboration.
No blanket all-path ES claim is made.

The existing `085C4400` leaf is six instructions plus one literal. It writes
one halfword to `030048A4`, preserving the adjacent halfword and all other
history fields. It is not a four/eight-byte blanket reset.

The omitted source instructions at raw `747CE2` and `747CE9` clear linear
addresses `13CD8/13CDA`. Ordinary fighter HP globals use source segment
`0C00`, linear `FCD8/FCDA`, and cannot substitute for these SRAM addresses.
Existing SRAM work remains `UNRESOLVED_OBSERVER`; record-layout exclusions
and unsuccessful searches do not make these writes dead.

## Exact write and stack

Only `[629810,629820)` changes:

```text
before: E8BD4800 E12FFF1E FFFFFFFF FFFFFFFF
after:  EBFE5FBA EBFE6AF9 E8BD4800 E12FFF1E
```

The first 16 bytes at `629800` remain unchanged. The entry grows from
24 to 32 bytes by replacing its old return with the two calls and moving
that same return eight bytes later. The new reservation `[629818,629820)`
was entirely FF, with no all-alignment/mirrored pointer or ARM/Thumb
branch/literal/ADR reference before the write. Full inverse restores the
entire exact predecessor; only 15 of the 16 declared bytes differ.

The call order is `08629700 -> 085C1000 -> 085C1700 -> 085C4400`. Every callee
preserves `r0-r12`, LR and SP. The existing entry saves only `r11,LR`, keeps
`r11=0` inside its frame, and permits flags to change. Its stack allocation
remains eight bytes, with no new wrapper or nested entry frame. The slot-5
adapter/arguments/leaf use 56+20+16=92 bytes beneath that frame, and the
0660 leaf uses 56. These are bounded local requirements, not a maximum for
the whole scene or proof of a live caller's available stack.

Builder self-checks reject 39 mutations, including all changed instruction
bytes, writes outside the range, changed dependencies, occupied extension,
source clear widths/order and the unresolved hard-gate instructions.

The separately authored final-artifact verifier imports no builder or
analyzer. It checks the actual 24 source instructions, all 47 instructions
of the P2 consumer and its palette inverse, the clean second ES1000 reader
and native counterparts, both static P0 populations and all 35 actual P1
layout selections, later constructors/callers, and the complete renderer
copy with startup/dispatch. Its 256 ABI/order cases pass. It rejects 36
artifact/semantic mutations and 58 reference-scanner controls: **94** total.
Both independent runs confirm the full inverse and unchanged first 16 bytes.

## Reproduction and limits

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/build_shoot_initializer_front.py `
  build/shoot-initializer-player-chain-20261026-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-front-20261026-a/current-candidate.gba `
  --manifest build/shoot-initializer-front-20261026-a/manifest.json

& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/verify_shoot_initializer_front.py `
  build/shoot-initializer-player-chain-20261026-a/current-candidate.gba `
  build/shoot-initializer-front-20261026-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-front-20261026-a/verification.json
```

Use `-b` for the second unused output directory. Existing object validity,
renderer startup, native stack, and exclusive scene/display ownership remain
preconditions. The retained player's intermediate-store timing contract is
unchanged. Full initializer `085C7800`, external route, SRAM observer/storage,
terminal DI, camera lifetime and later initializer phases remain open.
No emulator, supplied save, game service, or runtime transition was executed.
