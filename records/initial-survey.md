# Initial survey

## Scope

- Target base: USA retail GBA release of *Digimon: Battle Spirit*.
- Reference content: Japan retail WonderSwan Color release of *Digimon Tamers: Battle Spirit Ver. 1.5*.
- Intended direction: retain the GBA engine and reproduce selected 1.5 content on GBA.
- The source ROMs are read-only local inputs and are not stored in this project.

## Confirmed inputs

| ID | Platform | Size | CRC32 | SHA-1 | SHA-256 |
|---|---:|---:|---|---|---|
| `gba-usa-retail` | GBA | 4,194,304 | `CEEF2008` | `2BA954A54DD34B2B450D9EF718EB8A0F570B6549` | `996DE33330AC729D10D761D1901E7A335191C9503B0470569E8F294ACF6618ED` |
| `wsc-jpn-kor-10-retail` | WSC | 4,194,304 | `C927BFCB` | `757E92177385A14D979227EDEE1CB544B4C56BD6` | `58220B9C050C3BF29B4953885C9576BE103EA8E00A7BCB96CCA18607E19E9735` |
| `wsc-jpn-15-retail` | WSC | 8,388,608 | `6CAAD4A2` | `3F39FF494A3D8DD9D55A2E7CF86B47F1C8E8A156` | `C415F227ED9A277F6553B4EC03CA16CE4D0058D1C1104889D90BD88071D76FD7` |

The GBA digest matches the known No-Intro entry. The WSC digests match the
MAME software-list dumps for cartridges `SWJ-BANC1A / SWJ-BANC24` (original)
and `SWJ-BANC30` (Ver. 1.5).

## Confirmed structure

- The GBA image has a standard header, title `DIGIMON BTSP`, game code `A8SE`,
  and maker code `B2`.
- The WSC image uses the standard 10-byte footer, identifies Bandai (`0x01`),
  cartridge ID `0x30`, 8 MiB ROM code `0x08`, and 32 KiB SRAM code `0x02`.
- The original WSC image also has a valid footer and checksum. It identifies
  Bandai (`0x01`), cartridge ID `0x1A`, 4 MiB ROM code `0x06`, and 32 KiB SRAM
  code `0x02`. Its `En,Ja` filename is consistent with the retail cartridge's
  built-in bilingual data and does not indicate a fan translation.
- The WSC 16-bit additive checksum is stored little-endian and matches the ROM.
- Large WSC sprite blocks are raw 4bpp planar tiles. Converting each tile to
  GBA packed 4bpp produces exact, byte-for-byte matches in the GBA ROM:
  - WSC `0x1B0000` -> GBA `0x2DD720`, 2,026 contiguous tiles / 64,832 bytes.
  - WSC `0x290000` -> GBA `0x2ED460`, 1,477 contiguous tiles / 47,264 bytes.
- WSC BGR444 palette entries also convert exactly to GBA BGR555 entries. One
  confirmed mapping is WSC `0x43FDD0` -> GBA `0x020088` (also duplicated at
  `0x0D0D70`).
- A GBA `(byte length, ROM pointer)` descriptor table immediately precedes the
  first matched sprite block. Its first entry is `(0x460, 0x082DD720)` and the
  following entries describe contiguous, tile-aligned chunks.
- The WSC CPU code is V30MZ/80186-family machine code; the GBA startup and game
  code are ARM7TDMI. Assets can be transformed, but executable code cannot be
  transplanted.

## Active hypotheses

| Risk ID | Hypothesis | Current state | Next discriminator |
|---|---|---|---|
| `R-CODE-01` | WSC game logic cannot be transplanted as machine code. | Confirmed by incompatible V30MZ vs ARM7TDMI ISAs; semantic reimplementation is required. | Identify the smallest 1.5-only mechanic and its GBA integration point. |
| `R-ASSET-01` | Character art can be converted independently of code. | Confirmed for large raw 4bpp tile blocks and palettes. | Identify the complete boundaries and metadata of each 1.5-only character set. |
| `R-GBA-01` | The GBA engine has reusable character/stage descriptor tables. | Partially confirmed for sprite chunks. | Trace one roster entry through animation, collision, selection, and move data. |
| `R-SPACE-01` | Expanding the 4 MiB GBA ROM can supply enough storage. | Plausible but not sufficient. | Confirm all address calculations and loader assumptions before any expansion. |
| `R-AUDIO-01` | WSC audio can be copied directly. | Rejected. | Choose reconstruction, conversion, or reuse of GBA audio per asset. |

## Unknowns blocking a port claim

- Exact GBA character and stage table layouts.
- Compression and packing formats used outside the confirmed raw tile blocks.
- Whether 1.5-only moves fit the existing GBA scripting/animation model.
- Runtime RAM, VRAM, object, and per-frame CPU budgets for added content.
- Save-data changes needed for the expanded roster and unlock state.

## Current decision

Proceed conditionally with a vertical proof of concept. Do not claim a port or
hardware compatibility until one added asset travels through the final GBA
storage, load, render, gameplay, and hardware-test path.

The first proof of concept replaces only the 0x460-byte tile payload addressed
by the first confirmed GBA sprite descriptor. It is deliberately a reversible
graphics-path probe, not a roster or gameplay port.
