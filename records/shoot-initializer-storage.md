# Shoot initializer storage through source 73F0 (2026-11-03)

The disconnected entry `08629800` now includes the two ordered source stores
at `4090:73E2` and `73E9`. On initialized, functional native storage it reaches
source boundary `73F0`, with the end excluded. It remains disconnected from
the scene/controller, and the remainder of the full initializer is absent.

This adopts block 25 of the existing native EEPROM service for the distinct
source SRAM words. It does not clear the ordinary regeneration timers at
`030048AC/AE`, add a generic storage helper, or allocate persistent RAM.

## Frozen artifacts

- Builder: `tools/build_shoot_initializer_storage.py`, SHA-256
  `4F684C3CF5ED2E24F2F87C307412AAE0D0105EEE0886CFFD0F41E82D35D58C9E`.
- Exact predecessor: `build/shoot-initializer-front-20261026-a/current-candidate.gba`,
  SHA-256 `CB926019A7289762D5B5539A7994B522AD8A3B73D12A70A92337D47761FB58C7`.
- Outputs: `build/shoot-initializer-storage-20261103-a` and `-b`.
- Both `current-candidate.gba` files have SHA-256
  `66DA1AC3CC4FED2DF12C6A2C85430E735AA99C4934C967950B058D5D22F5ADFF`.
- Both `manifest.json` files have SHA-256
  `CFAE7F95E58F7BD2E4968AFAF9D13B0CF1E0EBD873D23151596248CAE40A3F5F`.
- Comparison: `build/shoot-initializer-storage-20261103-comparison.json`,
  SHA-256 `36DD9DAF69528C77F4DC7CD8877CFB16CC2C11CDB3EF9B32983C1281C469C45A`.
- Pre-write contract: `build/shoot-initializer-storage-contract-20261103.json`,
  SHA-256 `CA4947B6EC5DD205304C9F00C298FF8DD6ED5362653F491E4CFADB773D6CFF3E`.
  Independent pre-write review approved the exact 26 words and clarified
  that the new storage coordinates name the native API buffer, not serialized
  save-file byte order. The executable contract did not change.

The separate final-artifact verifier was completed and independently rerun
on 2026-11-05. `tools/verify_shoot_initializer_storage.py` checks 4,096
encoded ABI/RMW/error-path cases, 2,048 source bank aliases, 186 negative
controls and the full inverse. Its report
`build/shoot-initializer-storage-independent-20261105.json` has SHA-256
`BC75F6EACF9E9320463CC8436A731E7405F4DE15959882CA59B71DC32C90333E`,
identical to the previous two independent reports. The checker does not
import the builder or read its manifest. This is static artifact/model
verification; no physical EEPROM or reachable Shoot scene was executed.

## Source identity and native owner

The exact source footer at raw `7FFFF0` is
`EAFC06FF4F0001003000080204003E44`. Code `02` at raw `7FFFFB` selects 32 KiB
SRAM. In the standard retail SRAM mapping the backing coordinate is
`((linear & FFFF) | (C1 << 16)) & 7FFF`. Thus every C1 value maps
`13CD8..13CDB` and `1BCD8..1BCDB` to the same backing bytes `3CD8..3CDB`.
The builder checks all 2,048 combinations of C1, aperture alias and byte.

The primary implementation used to resolve the geometry and address rule is
Beetle WonderSwan revision `4b01295838ea89e3f1355bbe4cb5cf98aa6108cd`:
[header decoder](https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/libretro.c)
and [SRAM read/write mapping](https://github.com/libretro/beetle-wswan-libretro/blob/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd/mednafen/wswan/wswan-memory.c).
This is a source-derived cartridge model, not a new hardware execution test.
It removes C1 dependence for this image; it does not prove a source observer
set, a fresh-save value, or a source boot reset of these words.

The [distinct-state owner proof](shoot-distinct-state-owner.md) supplies the
bounded native ownership argument: selected capacity is 64 eight-byte blocks,
the actual native record loops use only blocks `0..24`, and all thirteen
additional finite MMIO-pattern candidates have positive data owners. The
existing computed-alias limit is retained, without demanding an unbounded
whole-program exclusion before using this owner.

| Source identity | Adopted native API identity |
|---|---|
| `1000:3CD8` | Block 25, buffer halfword at `+0` |
| `1000:3CDA` | Block 25, buffer halfword at `+2` |
| No newly assigned source identity | Buffer bytes `+4..+7` retained |

Labels `C8..CF` in the earlier review mean eight-byte **API record
coordinates**. The native reader packs incoming bits into buffer halfwords
`+6,+4,+2,+0`, and the writer serializes its words in the corresponding reverse
order. No identity with raw save-file byte order is claimed or needed here.
No save file was opened to infer this mapping.

Each source store has its own read/modify/write. First the reader at
`0837DB60` fills an eight-byte stack buffer; only halfword `+0` is cleared,
then `0837DB54` writes and verifies the block. The second operation rereads
the actual block, clears only halfword `+2`, and uses the same writer. Each
submitted block preserves the other six bytes from its corresponding read.
In particular, the second operation does not assume that the first committed.

## Failure policy and lifetime

Normal equivalence requires initialized, functional EEPROM and exclusive
main-task use of its existing DMA3/timer-2 service. A nonzero read result skips
only that corresponding write, avoiding an uninitialized-buffer write. The
writer retains its native limit of three write/verify attempts. The entry
then restores the existing scene ABI, including the incoming `r0`; it adds
neither a retry callback nor an unbounded software retry loop.

The source has no commit-status branch: its two instructions are plain MOV
stores, and caller raw `773143` proceeds directly to its timer/callback update.
Native record writer `0801FC5C` stops its block loop on error and propagates
`r0`; wrapper `0801FBD0` also propagates it. Ordinary retail callers such as
`0808B390`, `080C07C8`, `080C0ED0` and `0833EE04` restore their incoming `r0`
without inspecting the status. The two writes at `0808B378/0808B390` likewise
have no intervening status test. Those actual callers justify the bounded
backend limitation; the wrapper alone would not.

The current Options-language callers at `08633640/0863383C` do explicitly
test status and maintain their own error state. They remain byte-identical.
The Shoot layer does not impose or remove that separate feature's policy.

Failed-device intermediate or final data equivalence is not claimed. Native
DMA completion and timer IRQ availability remain service preconditions;
three attempts is not a guarantee that arbitrary broken hardware terminates.
There is no source evidence requiring a new commit-confirmed scene state.

The cartridge owner persists independently of task retirement. Every future
translated source observer must use this same identity and its required
lifetime; the current layer does not silently remap unknown observers or
declare the stores dead. Existing ordinary saves/reset transfers do not touch
block 25. No initial zero value, migration or valid-data tag is invented.

## Exact code, ownership and stack

Only raw `[629818,629880)` changes: 104 declared bytes, 103 actually different.
The 96-byte extension `[629820,629880)` was FF. The first 24 entry bytes and
all existing phase calls remain unchanged. Restoring this single range
recovers the entire exact CB926 predecessor.

The 26 approved words are:

```text
E92D100F E24DD008 E3A00019 E1A0100D EBF550CC E3500000 1A000004
E3A00000 E1CD00B0 E3A00019 E1A0100D EBF550C2 E3A00019 E1A0100D
EBF550C2 E3500000 1A000004 E3A00000 E1CD00B2 E3A00019 E1A0100D
EBF550B8 E28DD008 E8BD100F E8BD4800 E12FFF1E
```

The payload SHA-256 is
`95AC158B5F5E711177A6390384F0FFCA735D4F91FE176ADBB9496BAD4DB4E36A`.
Cleanup is `08629870` (release buffer), `08629874` (restore scratch),
`08629878` (restore original r11/LR) and `0862987C` (BX LR).

The conservative extension scan finds exactly two apparent Thumb ADRs.
Positive ARM instruction ownership resolves both: `08629510:EAEAA1D8` is
the priority helper's B to `080D1C78`, and `08629620:EBE7A493` is the
waterfall initializer's BL to `08012874`. The actual complete ARM bodies,
both manager callers and waterfall callback pointer are guarded. Their
Thumb-looking targets `08629874/08629870` are not real data references.
All other pointer/ARM/Thumb patterns in the finite scan are absent.

The preserved ABI is `r0-r12,LR,SP`; flags may change. The original frame uses
eight bytes, the added scratch save twenty, and the block eight: 36 bytes
total, with four-byte stack alignment. The native services preserve r4-r11;
timer start saves/restores its temporary r8/r9 use. The inspected synchronous
storage paths require 204 bytes for a direct read, 256 for write/timer start,
and 240 for verification/read/DMA, including the entry's 36 bytes. These do
not bound asynchronous IRQ stack, a live caller, or all earlier scene phases.

Builder checks cover 144 ABI/RMW cases, including read failures, write status
values, synthetic partial failed writes, and fidelity to the second actual
read. They reject 136 mutations, including all output bytes, dependency and
source changes, occupied extension bytes, and an unaligned mirrored pointer.

## Reproduction

```powershell
& 'C:\Users\김기호\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -Xutf8 tools/build_shoot_initializer_storage.py `
  build/shoot-initializer-front-20261026-a/current-candidate.gba `
  'C:\Users\김기호\Downloads\JUS\Digimon - Battle Spirit (USA).gba' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit (Japan) (En,Ja).wsc' `
  'C:\Users\김기호\Downloads\JUS\Digimon Tamers - Battle Spirit Ver 1.5.wsc' `
  build/shoot-initializer-storage-20261103-a/current-candidate.gba `
  --manifest build/shoot-initializer-storage-20261103-a/manifest.json
```

Use a fresh output directory; existing outputs are deliberately rejected.
Change `-a` to `-b` for the independent build invocation. No game, emulator,
physical EEPROM operation, supplied save or external scene route was run.
The source tail from `73F0`, full initializer entry, observer integration,
terminal IRQ/camera lifetime and runtime verification remain open.
