# Selection palette changes follow the actual fighter, 2026-10-21

The palette-only path at `08083178..0808322C` reads current and old cursors
from `03004738+4/+6`. It takes this path when their low bytes agree but their
palette high bytes differ. It then masked the current cursor at `080831C0`
and immediately scaled it by32 to index the canonical fighter resource table.
The cursor is a list position: clean-mode positions11/12 mean fighters13/14.
The direct lookup therefore selected fighters11/12's palettes instead.

The original three roster consumers explicitly read the list. This fourth
logical consumer instead used the cursor as an ID, so it was outside that
literal-list inventory. It is not the cause of the separately proved VS
overflow, whose failing natural-input sequence contained no palette changes.

`tools/build_selection_palette_index_repair.py` replaces only the original
`AND r1,r1,#FF` at raw `0831C0` with a branch. The exact 56-byte bridge at
`628240..628278` masks the cursor, reads existing unlock byte `03002329`,
selects the established immutable roster view at `08628000`, and loads the
actual fighter ID into r1. It returns to the original `LSLS r1,r1,#5` at
`080831C4`; the unchanged table lookup and both palette branches then use
that fighter's primary/alternate palette.

The bridge saves/restores r0 and r8 with a balanced eight-byte stack frame.
It changes only r1, preserves every incoming condition flag and LR, and makes
no calls or new persistent RAM allocation. The original r4 selection-state
owner remains intact. There are no preexisting encoded pointers or ARM
branches directly into the hook/continuation; their native fallthrough is
preserved. The new bridge is FF in the fixed predecessor and has no prior
encoded pointer, ARM branch, or immediate PC-relative access into it.

| Artifact | SHA-256 |
| --- | --- |
| Predecessor | `99EFB070C3DC604040B4F67B70DB9D2099186C8401A3F8E9CDE981567AC3EFD1` |
| `build/selection-palette-index-repair-20261021/current-candidate.gba` | `AAD4D471696955AC2DB07DD112CE349AACC3CF57C32C2C0D33906769E43EBEFF` |
| `build/selection-palette-index-repair-20261021/manifest.json` | `D05D3E374A20E2025347AC1174E03A2FA685C238C239916FE751B213EAB10E1A` |
| `build/selection-palette-index-repair-20261021/verification.json` | `D699F79E826696454DD9E614A9C8B67193EFCE52692399DC5D61E1A899D4D2C1` |

The layer changes59 bytes. The separate verifier imports no builder, decodes
all twelve bridge instructions and fifteen actual native consumer instructions,
resolves both PC-relative literals, and checks7,168 lookups across all256
unlock bytes and both live palette variants. Twelve damaging mutations are
rejected; the complete inverse changes only the declared hook/bridge.

The root-owned natural-input run in
`build/runtime-id14-palette-switch-20261021` pressed Down to clean-mode
cursor12, then Right at63 seconds. Its capture manifest SHA-256 is
`DE0546CB9882E5C860AC1449F9424F77BB0AEF10BEC77289707F70D5E55F453D`.
An independent read of the manifest and all six memory-region files verified
their identities, requested stop `S02`, no asynchronous fault, 106 enabled
OAM entries, and exact native copied-renderer bytes.

The final state is mode4 with cursor `010C`. Canonical fighter14's alternate
palette `084A1368` supplies all15 visible colors at hardware `05000202`.
The corresponding primary palette, and both palettes for fighters11..13,
do not match those colors. The live handle at `03004728` remains `02010360`
through every captured Down/Right input. Its P1/P0 pointers are the actual
fighter14 row's `086184A0`/`08420AC0`. Its presentation retains the original
P2 pointer, as the native palette-only path loads the alternate colors
directly. This is expected native behavior, not a stale character resource.

The independent report is
`build/selection-palette-index-repair-20261021/runtime-verification.json`,
SHA-256 `57C7A70B4924B1F4FFC604B1974E7F61B6015BACD77E9B7D6FD7B824C910B6CC`.
The run remained in selection and did not press battle confirmation. It
establishes this menu consumer, not full battle or visual parity. The
established ordinary roster policy is unchanged; the separate source
alternate-mode policy is not implemented by this layer. No save was opened
and no emulator was launched by this workstream.
