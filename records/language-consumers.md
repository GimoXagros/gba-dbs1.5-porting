# Native language and Options consumers

Read-only investigation, 2026-10-16. Three original ROMs are SHA-256 pinned
by `tools/analyze_language_consumers.py`; the inspected candidate is the frozen
callback-6 parity output `A559CC981736E376EEEF6D4097D93EC8965CFCE26FF23A5A269D4D049D4F2949`.
No ROM, font, save, or running emulator was changed. The supplied save was never
opened. These findings identify the next implementation boundary; four working
languages are not claimed.

## Source language behavior

Commercial WSC 1.0 has 26 exact `IN AL,CD; AND AL,1` sequences, all in its
code region. Their full population is in the report. WSC 1.5 has no occurrence
of that exact four-byte sequence anywhere in its ROM. More strongly, the paired
Options branches positively replace the read with zero:

| Purpose | WSC 1.0 raw | WSC 1.5 raw | Actual paired behavior |
| --- | --- | --- | --- |
| Options graphics branch | `3B4299` | `775679` | Old reads/masks `CD`; new executes two `XOR AX,AX` before the same zero comparison |
| Options task constructor | `3B4438` | `775816` | Same replacement; zero path calls the Japanese constructor |
| Record-error text branch | `3C5BD2` | `786202` | Same replacement before `OR AX,AX`/zero branch |

The WSC 1.0 language read is not evidence for an existing cartridge language
menu. The [Mednafen documentation](https://mednafen.github.io/documentation/wswan.html)
describes a Japanese/English emulator setting affecting Battle Spirit. The
[primary memory implementation](https://raw.githubusercontent.com/libretro/beetle-wswan-libretro/master/mednafen/wswan/wswan-memory.c)
returns the configured language in the low bit of the relevant port range,
after handling EEPROM ports separately. The positive ROM pair above establishes
the difference relevant to this port. Apparent `OUT CD` byte patterns elsewhere
in both ROMs lie outside these inspected code regions and are not classified as
executed writes.

USA GBA Options retains the two branches but forces English: ARM words at
`080C15F4` and `080C1824` are `E3B00001` (`MOVS r0,#1`), followed by a zero
comparison. An exact aligned-pattern scan also finds `080895A4`, `08089A88`,
`08089B98`, and `080BB44C`. Those four are additional investigation sites,
not a complete language-consumer inventory or an instruction to patch all six.

## Actual mode, input, and task lifetime

The main mode is a halfword at `03002310`. The mode table starts at raw `15B70`
with 12-byte rows. Row 14 has initializer `080C15C4` and constructor `080C17B0`.
The mode-3 transition row at raw `15CD7` is exactly `04 04 0E 02 13`, connecting
the third title choice to Options. The actual title resource includes
`PRESS START`, `1P BATTLE`, `2P BATTLE`, `OPTIONS`, and `D-ARK`.

`080C17B0` chooses Japanese constructor `080C1894` or English constructor
`080C2564`; both are still present. Its load of EEPROM record `+64` at
`080C17B8` is immediately overridden by `MOV r2,#0` at `080C17BC`. That value
is not an existing language option.

The input callback is `080C3234`. Its actual state base is `03004738`:
flags at `+0`, buttons at `+2`, current row at `+6`, old row at `+8`, and
relayout flag at `+E`. Button masks are up `1`, down `4`, left `8`, right `2`,
confirm `40`, and cancel `80`. Input sources are `03001306` and `0300130A`.

| Consumer | Original word / behavior |
| --- | --- |
| `080C32B8` | `E3A02004`: upward wrap to row 4 |
| `080C32C4` | `E3520004`: downward maximum row 4 |
| `080C32FC` | `E3580004`: confirm exits only from row 4 |
| `080C3354` | Existing exit callback; waits on retirement state `0300473C` |
| raw `C33F4` | Expected retirement bitmap `000001FB` |
| `080C38B8` / `080C3910` | Time reads/writes halfword `03002320`, domain 0..2 |
| `080C3A68` / `080C3AC0` | Level reads/writes byte `0300231F`, domain 0..2 |
| `08015930` / `08015934` | Cold initialization sets Time and Level to 1 |

The current five rows are Time, Level, Sound Test, Erase Data, and Return.
There is no language row. A sixth row requires an actual display task,
selection/value handling, coordinate reflow, and retirement accounting in
addition to the cursor constants. The existing Options exit does not call the
record writer; a RAM-only selection would therefore not establish persistence.

## Decoded native graphics and finite asset budget

These are P0/P1 native sprite resources, not encoded text strings requiring
a new text renderer. All referenced layouts and every tile reference were
parsed against the real atlas. Static P0 flag `+0E=8` selects the single
preloaded descriptor. The resource previews show first event frames in
grayscale; they are not emulator screenshots.

| Resource | P0 raw | P1 raw | P2 raw | Tiles / bytes | Events / layouts | Maximum parts in one frame |
| --- | --- | --- | --- | --- | --- | --- |
| Japanese Options | `09F980` | `0A02E8` | `0A05B8` | 50 / 1600 | 12 / 32 | 20 |
| English Options | `0A05E0` | `0A0D68` | `0A1038` | 34 / 1088 | 12 / 32 | 20 |
| Title labels | `08FD08` | `08FC58` | `090878` | 77 / 2464 | 5 / 5 | 26 |

Both Options P1 files have the same event and frame structure. Events 0/2/4/6/7
are the five row labels; 1 is the time values, 3 the difficulty values, 5 the
digits, 8 arrows, 9 the animated head, 10 a colon, and 11 the erase confirmation.
The first English frames read `TIME`, `90`, `LEVEL`, `EASY`, `SOUND TEST`, `0`,
`ERASE DATA`, `RETURN`, arrow, head, colon, `NO`. Their Japanese counterparts
are retained in the USA ROM, including `しあいじかん`, `むずかしさ`,
`かんたん`, `サウンドテスト`, `データをけす`, `もどる`, and `いいえ`.
These readings were checked against the decoded atlas at nearest-neighbor
magnification. Event 11's first frame is `いいえ` (No), not `ふつう` (Normal);
the Korean draft for that frame is therefore `아니요`.

The 20-part bound is per resource frame. It does not prove a complete screen's
OAM total, nor that four atlases can all be active simultaneously. A new Options
resource should select one language's atlas, while preserving native event and
presentation contracts. Before adding glyphs, close the combined live-task OAM
count, actual preload VRAM ownership, and the sixth row's vertical layout.
The report supplies every frame's parts and tile indices for that calculation.

`Galmuri11.ttf` under the local JUS project is a supplied candidate for Korean.
It has not been adopted, measured, or rasterized in this investigation. A font
filename alone does not establish 8x8-cell fit. Digicode assets still require
the user's chart pixels and Japanese-reading mapping; the native Japanese
assets above do not substitute for that chart.

## Native record, preservation, and proposed language owner

The actual native RAM record begins at `03001120`. Payload bytes `00..BF`
participate in the checksum; `C0..C3` store its four-byte sum; `C4..C7` are
transferred tail bytes outside the sum. Writer `0801FC5C` and reader
`0801FCA8` transfer exactly 25 eight-byte blocks. Checksum `0801FD0C` sums
exactly `C0` unsigned bytes. These facts independently agree with
`records/shoot-eeprom-storage.md`.

`0801F894` reads the record, checks only the first eight signature bytes, and
resets on mismatch or an explicit reset request. Reset clears `C0` bytes and
copies 16 bytes from raw `1F9D4`:

```text
44 49 4D 50 53 20 56 65 72 30 2E 37 32 20 20 20
 D  I  M  P  S     V  e  r  0  .  7  2
```

The final space at record `+0F` (`0300112F`) is a concrete candidate for a
tagged language byte, e.g. `A0..A3`, with legacy `20` or an invalid tag interpreted
as English. Under that proposal the first 15 header bytes remain exactly
`44494D505320566572302E37322020`, and all existing record fields at `+10` onward
retain their locations. The language byte would already be covered by the
native checksum and normal block transfer. This allocation is **not adopted**
by the present read-only report.

The full-ROM encoded-reference inventory finds 25 byte-aligned pointers into
the commercial `C8`-byte record and 26 in this candidate. The sole additional
candidate pattern is raw `4F82A1` pointing to record `+10`; it is unaligned and
is recorded as data, not assumed to execute. None points directly into header
`+01..0F`. All 17 aligned ARM literal loads of the record base are enumerated
and classified in the report. Apart from first-eight signature comparison and
bulk initialization/checksum/transfers, their observed uses begin at `+10`.
The normalizer `0801FA98` does not assign semantics to header `+08..0F`.

This is a finite encoded-reference and inspected-consumer proof, not a claim
that arbitrary computed aliases are impossible. Independent review should
endorse the new byte owner before a patch is emitted. The separate main
configuration byte `0300231F` is Level and must never be reused as language.

The native write path returns zero in `r0` on success and nonzero on failure.
A language change needs a deliberate commit point and existing native error
handling, preserving that status and normal caller ABI. On reset, invalid
record, or legacy header, load/default behavior must be defined. Saving only
on a later unrelated progress event would not meet a fresh-session language
persistence requirement.

## Concrete next implementation boundary

1. Independently approve the bounded `record+0F` ownership and add explicit
   load/default/reset/commit behavior around the existing record APIs.
2. Add a sixth Language row using the native task/presentation system, update
   the three cursor/Return consumers, and account for task retirement.
3. Close whole-screen OAM, atlas VRAM, and row-coordinate budgets. Produce
   one selected native P0/P1 resource per language with exact event contracts.
4. Replace the two Options constants with four-way dispatch, then inventory
   and connect title, error, result, and gameplay text consumers separately.
5. Verify switching and fresh-data persistence in invisible root-owned runs,
   including invalid language tags, write errors, missing glyphs, and overflow.

The smallest immediate implementation gap is the new language row/resource
and explicit commit path. The existing two-branch assets and checksum structure
are identified; an existing two-choice menu or completed four-language renderer
must not be inferred from them.

## Reproduction

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' `
  tools/analyze_language_consumers.py `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/opening-callback6-parity-20261016/current-candidate.gba `
  build/language-consumers-20261016/analysis.json `
  --render-directory build/language-consumers-20261016
```

Add `--all-frames` to render every event frame and its complete sprite bounds.
The default first-frame preview remains unchanged for historical reproduction.
The optional preview path uses Pillow. The read-only analyzer itself needs only
the Python standard library. It records full input hashes, preserved native
slices, exact guarded words, complete source-pattern and record-pointer
populations, all P1 frames, and all P0 tile references. Later candidates may be
analyzed only if every inspected native range and contract remains unchanged.
